"""Slack integration service."""

import os
from typing import Optional
import httpx

from database import get_db
from auth.token_service import TokenService


class SlackService:
    """Service for Slack operations."""

    SLACK_API_BASE = "https://slack.com/api"

    def __init__(self, user_id: Optional[str] = None):
        self.user_id = user_id
        self._bot_token = os.getenv("SLACK_BOT_TOKEN", "")
        self._access_token: Optional[str] = None

    async def _get_access_token(self) -> Optional[str]:
        """Get access token - either user token or bot token."""
        # Prefer user token if user_id is set
        if self.user_id:
            token_data = TokenService.get_token(self.user_id, "slack")
            if token_data:
                return token_data.get("access_token")

        # Fallback to bot token
        return self._bot_token if self._bot_token else None

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
    ) -> Optional[dict]:
        """Make authenticated request to Slack API."""
        access_token = await self._get_access_token()
        if not access_token:
            return None

        url = f"{self.SLACK_API_BASE}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            try:
                if method == "GET":
                    response = await client.get(url, headers=headers, params=data)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data)
                else:
                    return None

                result = response.json()
                if result.get("ok"):
                    return result
                return None
            except Exception:
                return None

    async def list_channels(self) -> list:
        """List available Slack channels."""
        result = await self._make_request("GET", "conversations.list", {"types": "public_channel,private_channel"})
        if result:
            return result.get("channels", [])
        return []

    async def send_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[list] = None,
    ) -> Optional[dict]:
        """Send a message to a Slack channel."""
        data = {
            "channel": channel,
            "text": text,
        }
        if blocks:
            data["blocks"] = blocks

        return await self._make_request("POST", "chat.postMessage", data)

    async def send_incident_notification(
        self,
        channel: str,
        incident: dict,
    ) -> Optional[dict]:
        """Send formatted incident notification to Slack."""
        severity_emoji = {
            "critical": ":rotating_light:",
            "warning": ":warning:",
            "info": ":information_source:",
        }
        status_color = {
            "open": "#dc2626",
            "acknowledged": "#f59e0b",
            "resolved": "#10b981",
        }

        emoji = severity_emoji.get(incident.get("severity", "info"), ":bell:")
        color = status_color.get(incident.get("status", "open"), "#6b7280")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Incident: {incident.get('title', 'Unknown')}",
                    "emoji": True,
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{incident.get('severity', 'Unknown').upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{incident.get('status', 'Unknown').upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Started At:*\n{incident.get('started_at', 'Unknown')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*ID:*\n#{incident.get('id', 'N/A')}"
                    },
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Acknowledge",
                            "emoji": True,
                        },
                        "value": f"ack_{incident.get('id')}",
                        "action_id": "acknowledge_incident",
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View in Able2Flow",
                            "emoji": True,
                        },
                        "url": f"http://localhost:5173/incidents",
                        "action_id": "view_incident",
                    },
                ]
            },
        ]

        text = f"{emoji} Incident Alert: {incident.get('title')} ({incident.get('severity')})"

        return await self.send_message(channel, text, blocks)

    async def send_task_notification(
        self,
        channel: str,
        task: dict,
        event_type: str = "created",
    ) -> Optional[dict]:
        """Send task notification to Slack."""
        priority_emoji = {
            "high": ":red_circle:",
            "medium": ":yellow_circle:",
            "low": ":white_circle:",
        }

        emoji = priority_emoji.get(task.get("priority", "medium"), ":blue_circle:")

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *Task {event_type}:* {task.get('title', 'Unknown')}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Priority:*\n{task.get('priority', 'medium')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Due Date:*\n{task.get('due_date', 'Not set')}"
                    },
                ]
            },
        ]

        if task.get("description"):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{task['description'][:200]}{'...' if len(task.get('description', '')) > 200 else ''}"
                }
            })

        text = f"Task {event_type}: {task.get('title')}"

        return await self.send_message(channel, text, blocks)

    async def handle_slash_command(self, command_data: dict) -> dict:
        """Handle Slack slash command."""
        command = command_data.get("command", "")
        text = command_data.get("text", "").strip()
        user_id = command_data.get("user_id", "")

        if command == "/able2flow":
            parts = text.split(" ", 1)
            action = parts[0].lower() if parts else "help"
            args = parts[1] if len(parts) > 1 else ""

            if action == "create":
                return await self._handle_create_task(args, user_id)
            elif action == "list":
                return await self._handle_list_tasks()
            elif action == "incidents":
                return await self._handle_list_incidents()
            else:
                return self._get_help_response()

        return {"text": "Unknown command"}

    async def _handle_create_task(self, title: str, slack_user_id: str) -> dict:
        """Create a task from slash command."""
        if not title:
            return {"text": "Please provide a task title: `/able2flow create [task title]`"}

        with get_db() as conn:
            cursor = conn.cursor()

            # Get default column
            cursor.execute("SELECT id FROM columns WHERE name = 'To Do' AND project_id = 1")
            column = cursor.fetchone()
            column_id = column["id"] if column else None

            cursor.execute("""
                INSERT INTO tasks (title, column_id, project_id, priority)
                VALUES (?, ?, 1, 'medium')
            """, (title, column_id))

            task_id = cursor.lastrowid
            conn.commit()

        return {
            "response_type": "in_channel",
            "text": f":white_check_mark: Task created: *{title}* (ID: #{task_id})"
        }

    async def _handle_list_tasks(self) -> dict:
        """List recent tasks."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.*, c.name as column_name
                FROM tasks t
                LEFT JOIN columns c ON t.column_id = c.id
                WHERE t.completed = 0
                ORDER BY t.created_at DESC
                LIMIT 5
            """)
            tasks = cursor.fetchall()

        if not tasks:
            return {"text": "No open tasks found."}

        task_list = "\n".join([
            f"• *{t['title']}* ({t['column_name'] or 'No column'}) - {t['priority']}"
            for t in tasks
        ])

        return {
            "response_type": "ephemeral",
            "text": f"*Recent Tasks:*\n{task_list}"
        }

    async def _handle_list_incidents(self) -> dict:
        """List open incidents."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM incidents
                WHERE status = 'open'
                ORDER BY started_at DESC
                LIMIT 5
            """)
            incidents = cursor.fetchall()

        if not incidents:
            return {"text": ":white_check_mark: No open incidents!"}

        incident_list = "\n".join([
            f"• :{'rotating_light' if i['severity'] == 'critical' else 'warning' if i['severity'] == 'warning' else 'information_source'}: *{i['title']}* ({i['severity']})"
            for i in incidents
        ])

        return {
            "response_type": "ephemeral",
            "text": f"*Open Incidents:*\n{incident_list}"
        }

    def _get_help_response(self) -> dict:
        """Get help response for slash command."""
        return {
            "response_type": "ephemeral",
            "text": """*Able2Flow Slack Commands:*

• `/able2flow create [task title]` - Create a new task
• `/able2flow list` - List recent tasks
• `/able2flow incidents` - List open incidents
• `/able2flow help` - Show this help message"""
        }

    async def unfurl_link(self, url: str) -> Optional[dict]:
        """Generate unfurl data for Able2Flow links."""
        # Parse URL to determine type
        if "/tasks/" in url:
            return await self._unfurl_task(url)
        elif "/incidents/" in url:
            return await self._unfurl_incident(url)
        return None

    async def _unfurl_task(self, url: str) -> Optional[dict]:
        """Generate unfurl for task link."""
        # Extract task ID from URL
        try:
            task_id = int(url.split("/tasks/")[-1].split("/")[0].split("?")[0])
        except (ValueError, IndexError):
            return None

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            task = cursor.fetchone()

            if not task:
                return None

            task_dict = dict(task)

        return {
            "title": task_dict["title"],
            "text": task_dict.get("description", "")[:200],
            "color": "#3b82f6",
            "fields": [
                {"title": "Priority", "value": task_dict.get("priority", "medium"), "short": True},
                {"title": "Due Date", "value": task_dict.get("due_date", "Not set"), "short": True},
            ],
        }

    async def _unfurl_incident(self, url: str) -> Optional[dict]:
        """Generate unfurl for incident link."""
        try:
            incident_id = int(url.split("/incidents/")[-1].split("/")[0].split("?")[0])
        except (ValueError, IndexError):
            return None

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
            incident = cursor.fetchone()

            if not incident:
                return None

            incident_dict = dict(incident)

        severity_color = {
            "critical": "#dc2626",
            "warning": "#f59e0b",
            "info": "#3b82f6",
        }

        return {
            "title": f"Incident: {incident_dict['title']}",
            "text": f"Status: {incident_dict['status']}",
            "color": severity_color.get(incident_dict.get("severity", "info"), "#6b7280"),
            "fields": [
                {"title": "Severity", "value": incident_dict.get("severity", "unknown"), "short": True},
                {"title": "Status", "value": incident_dict.get("status", "unknown"), "short": True},
            ],
        }
