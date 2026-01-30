"""Google Calendar integration service."""

import os
from datetime import datetime, timedelta
from typing import Optional
import httpx

from database import get_db
from auth.token_service import TokenService

# Clerk configuration
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

        # First try to get token from Clerk
        clerk_token = await self._get_clerk_google_token()
        if clerk_token:
            self._access_token = clerk_token
            return self._access_token

        # Fallback to local token storage
        token_data = TokenService.get_token(self.user_id, "google")
        if not token_data:
            return None

        # Check if token is expired
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
            print(f"[CalendarService] No CLERK_SECRET_KEY")
            return None

        print(f"[CalendarService] Fetching token for user: {self.user_id}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"https://api.clerk.com/v1/users/{self.user_id}/oauth_access_tokens/oauth_google",
                    headers={
                        "Authorization": f"Bearer {CLERK_SECRET_KEY}",
                        "Content-Type": "application/json",
                    }
                )

                print(f"[CalendarService] Clerk response status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        token = data[0].get("token")
                        print(f"[CalendarService] Got token: {token[:30] if token else 'None'}...")
                        return token
                print(f"[CalendarService] No token found in response")
                return None
            except Exception as e:
                print(f"[CalendarService] Error: {e}")
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
            print(f"[CalendarService] _make_request: No access token!")
            return None

        url = f"{self.CALENDAR_API_BASE}{endpoint}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        print(f"[CalendarService] _make_request: {method} {endpoint}")

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

                print(f"[CalendarService] Response status: {response.status_code}")

                if response.status_code in [200, 201]:
                    return response.json() if response.content else {}

                print(f"[CalendarService] Error response: {response.text[:200]}")
                return None
            except Exception as e:
                print(f"[CalendarService] Request exception: {e}")
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

    async def sync_task_to_calendar(
        self,
        task_id: int,
        calendar_id: str = "primary",
        force_update: bool = False,
    ) -> Optional[dict]:
        """Sync a task's due date to Google Calendar. Updates existing event or creates new."""
        print(f"[CalendarService] sync_task_to_calendar: task_id={task_id}, force_update={force_update}")

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            task = cursor.fetchone()

            if not task:
                print(f"[CalendarService] Task {task_id} not found")
                return None

            task_dict = dict(task)
            due_date = task_dict.get("due_date")
            title = task_dict.get("title", "")
            description = task_dict.get("description", "") or ""
            is_completed = task_dict.get("completed", 0) == 1
            existing_event_id = task_dict.get("google_event_id")

            print(f"[CalendarService] Task: {title}, due_date={due_date}, completed={is_completed}")

            # If task is completed and has event, delete the event
            if is_completed and existing_event_id:
                print(f"[CalendarService] Task completed - deleting event {existing_event_id}")
                await self.delete_event(existing_event_id, calendar_id)
                cursor.execute(
                    "UPDATE tasks SET google_event_id = NULL WHERE id = ?",
                    (task_id,)
                )
                conn.commit()
                return {"id": existing_event_id, "status": "deleted"}

            if not due_date:
                print(f"[CalendarService] Task {task_id} has no due_date")
                # If had event but no due_date now, delete the event
                if existing_event_id:
                    print(f"[CalendarService] Deleting event {existing_event_id} (no due_date)")
                    await self.delete_event(existing_event_id, calendar_id)
                    cursor.execute(
                        "UPDATE tasks SET google_event_id = NULL WHERE id = ?",
                        (task_id,)
                    )
                    conn.commit()
                return None

            # Parse due date - treat as local time (Europe/Prague)
            if isinstance(due_date, str):
                due_datetime = datetime.fromisoformat(due_date.replace("Z", ""))
            else:
                due_datetime = due_date

            end_datetime = due_datetime + timedelta(hours=1)

            # Check if task already has an event - UPDATE it
            if existing_event_id:
                print(f"[CalendarService] Updating existing event {existing_event_id}")
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
                    print(f"[CalendarService] Event {existing_event_id} updated")
                    return {"id": existing_event_id, "status": "updated"}
                else:
                    print(f"[CalendarService] Failed to update event, creating new")
                    # Event might have been deleted, create new one
                    existing_event_id = None

            # Create new calendar event
            print(f"[CalendarService] Creating event for: {title} at {due_datetime}")
            result = await self.create_event(
                summary=f"[Task] {title}",
                start=due_datetime,
                description=description,
                calendar_id=calendar_id,
            )
            print(f"[CalendarService] Create event result: {result}")

            # Save event_id to task
            if result and "id" in result:
                cursor.execute(
                    "UPDATE tasks SET google_event_id = ? WHERE id = ?",
                    (result["id"], task_id)
                )
                conn.commit()
                print(f"[CalendarService] Saved event_id {result['id']} to task {task_id}")

            return result

    async def sync_all_tasks(
        self,
        project_id: Optional[int] = None,
        calendar_id: str = "primary",
    ) -> dict:
        """Sync all tasks with due dates to calendar (create new or update existing)."""
        print(f"[CalendarService] sync_all_tasks: project_id={project_id}")

        with get_db() as conn:
            cursor = conn.cursor()

            # Get all tasks (not just with due_date) to handle deletions too
            if project_id:
                cursor.execute(
                    "SELECT * FROM tasks WHERE project_id = ?",
                    (project_id,)
                )
            else:
                cursor.execute("SELECT * FROM tasks")

            tasks = cursor.fetchall()
            print(f"[CalendarService] Found {len(tasks)} tasks")

            created = 0
            updated = 0
            deleted = 0
            failed = 0

            for task in tasks:
                print(f"[CalendarService] Processing task {task['id']}: {task['title']}")
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
                    # No due_date or other issue - not a failure for tasks without due_date
                    if task["due_date"]:
                        failed += 1

            print(f"[CalendarService] Sync complete: {created} created, {updated} updated, {deleted} deleted, {failed} failed")

            return {
                "synced": created,
                "updated": updated,
                "deleted": deleted,
                "failed": failed,
                "total": len(tasks),
            }

    async def get_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
    ) -> Optional[dict]:
        """Get a single calendar event by ID."""
        return await self._make_request("GET", f"/calendars/{calendar_id}/events/{event_id}")

    def _get_done_column_id(self, cursor, task_project_id: int) -> Optional[int]:
        """Get the 'Done' column ID for a project."""
        # Try to find column named 'Done' for this project
        cursor.execute(
            "SELECT id FROM columns WHERE project_id = ? AND name = 'Done' ORDER BY position DESC LIMIT 1",
            (task_project_id,)
        )
        row = cursor.fetchone()
        if row:
            return row["id"]

        # Fallback: get the last column (highest position) for this project
        cursor.execute(
            "SELECT id FROM columns WHERE project_id = ? ORDER BY position DESC LIMIT 1",
            (task_project_id,)
        )
        row = cursor.fetchone()
        return row["id"] if row else None

    async def sync_from_calendar(
        self,
        project_id: Optional[int] = None,
        calendar_id: str = "primary",
    ) -> dict:
        """
        Sync from Google Calendar back to tasks.
        - If event deleted/cancelled: mark task as completed and move to Done column
        - If event exists: sync description changes back to task
        """
        print(f"[CalendarService] sync_from_calendar: project_id={project_id}")

        with get_db() as conn:
            cursor = conn.cursor()

            # Get tasks that have google_event_id
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
            print(f"[CalendarService] Found {len(tasks)} tasks with google_event_id")

            completed_count = 0
            updated_count = 0
            checked_count = 0

            for task in tasks:
                task_dict = dict(task)
                event_id = task_dict["google_event_id"]
                task_project_id = task_dict.get("project_id", 1)
                task_id = task_dict["id"]
                is_already_completed = task_dict.get("completed", 0) == 1
                print(f"[CalendarService] Checking event {event_id} for task {task_id}")

                # Try to get the event from Google Calendar
                event = await self.get_event(event_id, calendar_id)

                should_complete = False
                if event is None:
                    if not is_already_completed:
                        print(f"[CalendarService] Event {event_id} not found - marking task {task_id} as completed")
                        should_complete = True
                elif event.get("status") == "cancelled":
                    if not is_already_completed:
                        print(f"[CalendarService] Event {event_id} cancelled - marking task {task_id} as completed")
                        should_complete = True
                else:
                    # Event exists - sync changes (description, title) back to task
                    event_description = event.get("description", "")
                    event_summary = event.get("summary", "")

                    # Remove [Task] prefix from summary if present
                    if event_summary.startswith("[Task] "):
                        event_summary = event_summary[7:]

                    current_description = task_dict.get("description") or ""
                    current_title = task_dict.get("title") or ""

                    updates = []
                    params = []

                    # Check if description changed
                    if event_description != current_description:
                        updates.append("description = ?")
                        params.append(event_description)
                        print(f"[CalendarService] Updating description for task {task_id}")

                    # Check if title changed (only if not prefixed)
                    if event_summary and event_summary != current_title:
                        updates.append("title = ?")
                        params.append(event_summary)
                        print(f"[CalendarService] Updating title for task {task_id}: {event_summary}")

                    if updates:
                        params.append(task_id)
                        cursor.execute(
                            f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?",
                            params
                        )
                        conn.commit()
                        updated_count += 1

                if should_complete:
                    # Get Done column for this task's project
                    done_column_id = self._get_done_column_id(cursor, task_project_id)
                    print(f"[CalendarService] Moving task {task_id} to Done column {done_column_id}")

                    # Shift existing tasks in Done column down (increment position)
                    if done_column_id:
                        cursor.execute(
                            "UPDATE tasks SET position = position + 1 WHERE column_id = ?",
                            (done_column_id,)
                        )

                    # Mark as completed, move to Done column, position 0 (top)
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

            print(f"[CalendarService] Sync from calendar complete: {completed_count} completed, {updated_count} updated, {checked_count} checked")

            return {
                "completed": completed_count,
                "updated": updated_count,
                "checked": checked_count,
            }
