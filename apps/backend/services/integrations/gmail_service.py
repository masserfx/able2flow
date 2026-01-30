"""Gmail integration service."""

import base64
from email.mime.text import MIMEText
from typing import Optional
import httpx

from database import get_db
from auth.token_service import TokenService


class GmailService:
    """Service for Gmail operations."""

    GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"

    def __init__(self, user_id: str):
        self.user_id = user_id
        self._access_token: Optional[str] = None

    async def _get_access_token(self) -> Optional[str]:
        """Get valid access token, refreshing if necessary."""
        if self._access_token:
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

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
    ) -> Optional[dict]:
        """Make authenticated request to Gmail API."""
        access_token = await self._get_access_token()
        if not access_token:
            return None

        url = f"{self.GMAIL_API_BASE}{endpoint}"
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
                else:
                    return None

                if response.status_code in [200, 201]:
                    return response.json() if response.content else {}
                return None
            except Exception:
                return None

    async def list_messages(
        self,
        query: Optional[str] = None,
        max_results: int = 10,
    ) -> list:
        """List Gmail messages."""
        endpoint = f"/users/me/messages?maxResults={max_results}"
        if query:
            endpoint += f"&q={query}"

        result = await self._make_request("GET", endpoint)
        if result:
            return result.get("messages", [])
        return []

    async def get_message(self, message_id: str) -> Optional[dict]:
        """Get a specific message."""
        return await self._make_request("GET", f"/users/me/messages/{message_id}")

    async def get_message_content(self, message_id: str) -> Optional[dict]:
        """Get message with full content parsed."""
        message = await self.get_message(message_id)
        if not message:
            return None

        # Parse headers
        headers = {}
        for header in message.get("payload", {}).get("headers", []):
            headers[header["name"].lower()] = header["value"]

        # Parse body
        body = ""
        payload = message.get("payload", {})

        if "body" in payload and payload["body"].get("data"):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
        elif "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                    break

        return {
            "id": message_id,
            "subject": headers.get("subject", ""),
            "from": headers.get("from", ""),
            "to": headers.get("to", ""),
            "date": headers.get("date", ""),
            "body": body,
            "snippet": message.get("snippet", ""),
        }

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
    ) -> Optional[dict]:
        """Send an email."""
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        return await self._make_request(
            "POST",
            "/users/me/messages/send",
            {"raw": raw}
        )

    async def create_task_from_email(self, message_id: str, project_id: int = 1) -> Optional[dict]:
        """Create a task from an email message."""
        message = await self.get_message_content(message_id)
        if not message:
            return None

        with get_db() as conn:
            cursor = conn.cursor()

            # Get default column (To Do)
            cursor.execute(
                "SELECT id FROM columns WHERE name = 'To Do' AND project_id = ?",
                (project_id,)
            )
            column = cursor.fetchone()
            column_id = column["id"] if column else None

            # Create task
            title = f"[Email] {message['subject']}"
            description = f"""From: {message['from']}
Date: {message['date']}

{message['body'][:1000]}{'...' if len(message['body']) > 1000 else ''}
"""

            cursor.execute("""
                INSERT INTO tasks (title, description, column_id, project_id, priority)
                VALUES (?, ?, ?, ?, ?)
            """, (title, description, column_id, project_id, "medium"))

            task_id = cursor.lastrowid
            conn.commit()

            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            task = cursor.fetchone()

            return dict(task) if task else None

    async def send_incident_notification(
        self,
        to: str,
        incident: dict,
    ) -> Optional[dict]:
        """Send email notification about an incident."""
        subject = f"[Able2Flow] Incident Alert: {incident.get('title', 'Unknown')}"

        body = f"""An incident has been reported in Able2Flow.

Incident Details:
- Title: {incident.get('title', 'Unknown')}
- Severity: {incident.get('severity', 'Unknown')}
- Status: {incident.get('status', 'Unknown')}
- Started At: {incident.get('started_at', 'Unknown')}

Please log in to Able2Flow to view more details and take action.

---
This is an automated notification from Able2Flow.
"""
        return await self.send_email(to, subject, body)

    async def send_task_notification(
        self,
        to: str,
        task: dict,
        event_type: str = "updated",
    ) -> Optional[dict]:
        """Send email notification about a task change."""
        subject = f"[Able2Flow] Task {event_type}: {task.get('title', 'Unknown')}"

        body = f"""A task has been {event_type} in Able2Flow.

Task Details:
- Title: {task.get('title', 'Unknown')}
- Priority: {task.get('priority', 'medium')}
- Due Date: {task.get('due_date', 'Not set')}
- Description: {task.get('description', 'No description')}

---
This is an automated notification from Able2Flow.
"""
        return await self.send_email(to, subject, body)

    async def send_daily_digest(
        self,
        to: str,
        project_id: Optional[int] = None,
    ) -> Optional[dict]:
        """Send daily digest email with task and incident summary."""
        with get_db() as conn:
            cursor = conn.cursor()

            # Get task stats
            if project_id:
                cursor.execute("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed,
                        SUM(CASE WHEN due_date < date('now') AND completed = 0 THEN 1 ELSE 0 END) as overdue
                    FROM tasks WHERE project_id = ?
                """, (project_id,))
            else:
                cursor.execute("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed,
                        SUM(CASE WHEN due_date < date('now') AND completed = 0 THEN 1 ELSE 0 END) as overdue
                    FROM tasks
                """)
            task_stats = dict(cursor.fetchone())

            # Get open incidents
            if project_id:
                cursor.execute(
                    "SELECT COUNT(*) as count FROM incidents WHERE status = 'open' AND project_id = ?",
                    (project_id,)
                )
            else:
                cursor.execute("SELECT COUNT(*) as count FROM incidents WHERE status = 'open'")
            open_incidents = cursor.fetchone()["count"]

        subject = "[Able2Flow] Daily Digest"

        body = f"""Good morning! Here's your daily summary from Able2Flow.

Task Summary:
- Total Tasks: {task_stats['total']}
- Completed: {task_stats['completed']}
- Overdue: {task_stats['overdue']}

Incident Summary:
- Open Incidents: {open_incidents}

Have a productive day!

---
This is an automated notification from Able2Flow.
"""
        return await self.send_email(to, subject, body)
