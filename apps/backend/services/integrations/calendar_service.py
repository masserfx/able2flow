"""Google Calendar integration service."""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional
import httpx

from database import get_db
from auth.token_service import TokenService

logger = logging.getLogger(__name__)

CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")


class CalendarService:
    """Service for Google Calendar operations."""

    CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"

    def __init__(self, user_id: str):
        self.user_id = user_id
        self._access_token: Optional[str] = None

    async def _get_access_token(self) -> Optional[str]:
        """Get valid access token from Clerk or local storage."""
        if self._access_token:
            return self._access_token

        clerk_token = await self._get_clerk_google_token()
        if clerk_token:
            self._access_token = clerk_token
            return self._access_token

        token_data = TokenService.get_token(self.user_id, "google")
        if not token_data:
            return None

        if TokenService.is_token_expired(self.user_id, "google"):
            refreshed = TokenService.refresh_google_token(self.user_id)
            if not refreshed:
                return None
            token_data = TokenService.get_token(self.user_id, "google")

        self._access_token = token_data.get("access_token")
        return self._access_token

    async def _get_clerk_google_token(self) -> Optional[str]:
        """Get Google OAuth token from Clerk Backend API."""
        if not CLERK_SECRET_KEY:
            logger.warning("CLERK_SECRET_KEY not configured")
            return None

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"https://api.clerk.com/v1/users/{self.user_id}/oauth_access_tokens/oauth_google",
                    headers={
                        "Authorization": f"Bearer {CLERK_SECRET_KEY}",
                        "Content-Type": "application/json",
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        return data[0].get("token")
                return None
            except Exception as e:
                logger.error("Failed to get Clerk token: %s", str(e))
                return None

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
    ) -> Optional[dict]:
        """Make authenticated request to Calendar API."""
        access_token = await self._get_access_token()
        if not access_token:
            logger.warning("No access token available")
            return None

        url = f"{self.CALENDAR_API_BASE}{endpoint}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            try:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    return None

                if response.status_code in [200, 201]:
                    return response.json() if response.content else {}

                logger.warning("Calendar API error: %d", response.status_code)
                return None
            except Exception as e:
                logger.error("Calendar API request failed: %s", str(e))
                return None

    async def list_calendars(self) -> list:
        """List user's calendars."""
        result = await self._make_request("GET", "/users/me/calendarList")
        if result:
            return result.get("items", [])
        return []

    async def get_events(
        self,
        calendar_id: str = "primary",
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 100,
    ) -> list:
        """Get calendar events."""
        if not time_min:
            time_min = datetime.now()
        if not time_max:
            time_max = time_min + timedelta(days=30)

        params = (
            f"?timeMin={time_min.isoformat()}Z"
            f"&timeMax={time_max.isoformat()}Z"
            f"&maxResults={max_results}"
            f"&orderBy=startTime"
            f"&singleEvents=true"
        )

        result = await self._make_request("GET", f"/calendars/{calendar_id}/events{params}")
        if result:
            return result.get("items", [])
        return []

    async def create_event(
        self,
        summary: str,
        start: datetime,
        end: Optional[datetime] = None,
        description: Optional[str] = None,
        calendar_id: str = "primary",
        timezone: str = "Europe/Prague",
    ) -> Optional[dict]:
        """Create a calendar event."""
        if not end:
            end = start + timedelta(hours=1)

        event_data = {
            "summary": summary,
            "description": description or "",
            "start": {
                "dateTime": start.isoformat(),
                "timeZone": timezone,
            },
            "end": {
                "dateTime": end.isoformat(),
                "timeZone": timezone,
            },
        }

        return await self._make_request("POST", f"/calendars/{calendar_id}/events", event_data)

    async def update_event(
        self,
        event_id: str,
        updates: dict,
        calendar_id: str = "primary",
    ) -> Optional[dict]:
        """Update a calendar event."""
        return await self._make_request("PUT", f"/calendars/{calendar_id}/events/{event_id}", updates)

    async def delete_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
    ) -> bool:
        """Delete a calendar event."""
        result = await self._make_request("DELETE", f"/calendars/{calendar_id}/events/{event_id}")
        return result is not None

    async def get_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
    ) -> Optional[dict]:
        """Get a single calendar event by ID."""
        return await self._make_request("GET", f"/calendars/{calendar_id}/events/{event_id}")

    def _get_done_column_id(self, cursor, task_project_id: int) -> Optional[int]:
        """Get the 'Done' column ID for a project."""
        cursor.execute(
            "SELECT id FROM columns WHERE project_id = ? AND name = 'Done' ORDER BY position DESC LIMIT 1",
            (task_project_id,)
        )
        row = cursor.fetchone()
        if row:
            return row["id"]

        cursor.execute(
            "SELECT id FROM columns WHERE project_id = ? ORDER BY position DESC LIMIT 1",
            (task_project_id,)
        )
        row = cursor.fetchone()
        return row["id"] if row else None

    async def sync_task_to_calendar(
        self,
        task_id: int,
        calendar_id: str = "primary",
        force_update: bool = False,
    ) -> Optional[dict]:
        """Sync a task's due date to Google Calendar."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            task = cursor.fetchone()

            if not task:
                return None

            task_dict = dict(task)
            due_date = task_dict.get("due_date")
            title = task_dict.get("title", "")
            description = task_dict.get("description", "") or ""
            is_completed = task_dict.get("completed", 0) == 1
            existing_event_id = task_dict.get("google_event_id")

            if is_completed and existing_event_id:
                await self.delete_event(existing_event_id, calendar_id)
                cursor.execute(
                    "UPDATE tasks SET google_event_id = NULL WHERE id = ?",
                    (task_id,)
                )
                conn.commit()
                return {"id": existing_event_id, "status": "deleted"}

            if not due_date:
                if existing_event_id:
                    await self.delete_event(existing_event_id, calendar_id)
                    cursor.execute(
                        "UPDATE tasks SET google_event_id = NULL WHERE id = ?",
                        (task_id,)
                    )
                    conn.commit()
                return None

            if isinstance(due_date, str):
                due_datetime = datetime.fromisoformat(due_date.replace("Z", ""))
            else:
                due_datetime = due_date

            end_datetime = due_datetime + timedelta(hours=1)

            if existing_event_id:
                updates = {
                    "summary": f"[Task] {title}",
                    "description": description,
                    "start": {
                        "dateTime": due_datetime.isoformat(),
                        "timeZone": "Europe/Prague",
                    },
                    "end": {
                        "dateTime": end_datetime.isoformat(),
                        "timeZone": "Europe/Prague",
                    },
                }
                result = await self.update_event(existing_event_id, updates, calendar_id)
                if result:
                    return {"id": existing_event_id, "status": "updated"}
                existing_event_id = None

            result = await self.create_event(
                summary=f"[Task] {title}",
                start=due_datetime,
                description=description,
                calendar_id=calendar_id,
            )

            if result and "id" in result:
                cursor.execute(
                    "UPDATE tasks SET google_event_id = ? WHERE id = ?",
                    (result["id"], task_id)
                )
                conn.commit()

            return result

    async def sync_all_tasks(
        self,
        project_id: Optional[int] = None,
        calendar_id: str = "primary",
    ) -> dict:
        """Sync all tasks with due dates to calendar."""
        with get_db() as conn:
            cursor = conn.cursor()

            if project_id:
                cursor.execute(
                    "SELECT * FROM tasks WHERE project_id = ?",
                    (project_id,)
                )
            else:
                cursor.execute("SELECT * FROM tasks")

            tasks = cursor.fetchall()

            created = 0
            updated = 0
            deleted = 0
            failed = 0

            for task in tasks:
                result = await self.sync_task_to_calendar(task["id"], calendar_id)
                if result:
                    status = result.get("status", "created")
                    if status == "updated":
                        updated += 1
                    elif status == "deleted":
                        deleted += 1
                    else:
                        created += 1
                else:
                    if task["due_date"]:
                        failed += 1

            return {
                "synced": created,
                "updated": updated,
                "deleted": deleted,
                "failed": failed,
                "total": len(tasks),
            }

    async def sync_from_calendar(
        self,
        project_id: Optional[int] = None,
        calendar_id: str = "primary",
    ) -> dict:
        """Sync from Google Calendar back to tasks."""
        with get_db() as conn:
            cursor = conn.cursor()

            if project_id:
                cursor.execute(
                    "SELECT * FROM tasks WHERE google_event_id IS NOT NULL AND project_id = ?",
                    (project_id,)
                )
            else:
                cursor.execute(
                    "SELECT * FROM tasks WHERE google_event_id IS NOT NULL"
                )

            tasks = cursor.fetchall()

            completed_count = 0
            updated_count = 0
            checked_count = 0

            for task in tasks:
                task_dict = dict(task)
                event_id = task_dict["google_event_id"]
                task_project_id = task_dict.get("project_id", 1)
                task_id = task_dict["id"]
                is_already_completed = task_dict.get("completed", 0) == 1

                event = await self.get_event(event_id, calendar_id)

                should_complete = False
                if event is None:
                    if not is_already_completed:
                        should_complete = True
                elif event.get("status") == "cancelled":
                    if not is_already_completed:
                        should_complete = True
                else:
                    event_description = event.get("description", "")
                    event_summary = event.get("summary", "")

                    if event_summary.startswith("[Task] "):
                        event_summary = event_summary[7:]

                    current_description = task_dict.get("description") or ""
                    current_title = task_dict.get("title") or ""

                    updates = []
                    params = []

                    if event_description != current_description:
                        updates.append("description = ?")
                        params.append(event_description)

                    if event_summary and event_summary != current_title:
                        updates.append("title = ?")
                        params.append(event_summary)

                    if updates:
                        params.append(task_id)
                        cursor.execute(
                            f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?",
                            params
                        )
                        conn.commit()
                        updated_count += 1

                if should_complete:
                    done_column_id = self._get_done_column_id(cursor, task_project_id)

                    if done_column_id:
                        cursor.execute(
                            "UPDATE tasks SET position = position + 1 WHERE column_id = ?",
                            (done_column_id,)
                        )

                    if done_column_id:
                        cursor.execute(
                            "UPDATE tasks SET completed = 1, column_id = ?, position = 0 WHERE id = ?",
                            (done_column_id, task_id)
                        )
                    else:
                        cursor.execute(
                            "UPDATE tasks SET completed = 1 WHERE id = ?",
                            (task_id,)
                        )
                    conn.commit()
                    completed_count += 1

                checked_count += 1

            return {
                "completed": completed_count,
                "updated": updated_count,
                "checked": checked_count,
            }
