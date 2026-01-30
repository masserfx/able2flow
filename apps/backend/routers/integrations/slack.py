"""Slack integration endpoints."""

from typing import Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Request, Form

from auth import get_current_user, get_optional_user
from auth.clerk_middleware import ClerkUser
from services.integrations import SlackService

router = APIRouter(prefix="/api/integrations/slack", tags=["Slack"])


class SendMessageRequest(BaseModel):
    """Request to send a Slack message."""
    channel: str
    text: str


class NotifyIncidentRequest(BaseModel):
    """Request to notify about an incident."""
    channel: str
    incident_id: int


class NotifyTaskRequest(BaseModel):
    """Request to notify about a task."""
    channel: str
    task_id: int
    event_type: str = "created"


@router.get("/channels")
async def list_channels(user: ClerkUser = Depends(get_current_user)) -> dict:
    """List available Slack channels."""
    service = SlackService(user.user_id)
    channels = await service.list_channels()

    return {
        "channels": [
            {
                "id": ch.get("id"),
                "name": ch.get("name"),
                "is_private": ch.get("is_private", False),
            }
            for ch in channels
        ],
    }


@router.post("/message")
async def send_message(
    request: SendMessageRequest,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Send a message to a Slack channel."""
    service = SlackService(user.user_id)

    result = await service.send_message(
        channel=request.channel,
        text=request.text,
    )

    if not result:
        raise HTTPException(status_code=400, detail="Failed to send message")

    return {
        "status": "success",
        "channel": request.channel,
        "ts": result.get("ts"),
    }


@router.post("/notify/incident")
async def notify_incident(
    request: NotifyIncidentRequest,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Send incident notification to Slack."""
    from database import get_db

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incidents WHERE id = ?", (request.incident_id,))
        incident = cursor.fetchone()

        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")

    service = SlackService(user.user_id)

    result = await service.send_incident_notification(
        channel=request.channel,
        incident=dict(incident),
    )

    if not result:
        raise HTTPException(status_code=400, detail="Failed to send notification")

    return {
        "status": "success",
        "channel": request.channel,
        "ts": result.get("ts"),
    }


@router.post("/notify/task")
async def notify_task(
    request: NotifyTaskRequest,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Send task notification to Slack."""
    from database import get_db

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (request.task_id,))
        task = cursor.fetchone()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

    service = SlackService(user.user_id)

    result = await service.send_task_notification(
        channel=request.channel,
        task=dict(task),
        event_type=request.event_type,
    )

    if not result:
        raise HTTPException(status_code=400, detail="Failed to send notification")

    return {
        "status": "success",
        "channel": request.channel,
        "ts": result.get("ts"),
    }


@router.post("/commands")
async def handle_slack_command(
    request: Request,
    command: str = Form(...),
    text: str = Form(""),
    user_id: str = Form(...),
    channel_id: str = Form(...),
    response_url: str = Form(...),
) -> dict:
    """Handle Slack slash commands."""
    # Note: In production, verify the request signature
    service = SlackService()  # Use bot token for slash commands

    command_data = {
        "command": command,
        "text": text,
        "user_id": user_id,
        "channel_id": channel_id,
        "response_url": response_url,
    }

    response = await service.handle_slash_command(command_data)

    return response


@router.post("/events")
async def handle_slack_events(request: Request) -> dict:
    """Handle Slack events (webhooks)."""
    body = await request.json()

    # Handle URL verification challenge
    if body.get("type") == "url_verification":
        return {"challenge": body.get("challenge")}

    # Handle events
    event = body.get("event", {})
    event_type = event.get("type")

    if event_type == "link_shared":
        # Handle link unfurling
        service = SlackService()
        links = event.get("links", [])

        unfurls = {}
        for link in links:
            url = link.get("url", "")
            if "localhost:5173" in url or "able2flow" in url:
                unfurl_data = await service.unfurl_link(url)
                if unfurl_data:
                    unfurls[url] = unfurl_data

        # Would call chat.unfurl here with the unfurls data

    return {"status": "ok"}


@router.get("/unfurl")
async def preview_unfurl(
    url: str,
    user: Optional[ClerkUser] = Depends(get_optional_user)
) -> dict:
    """Preview unfurl data for a URL."""
    service = SlackService(user.user_id if user else None)

    unfurl = await service.unfurl_link(url)

    if not unfurl:
        raise HTTPException(status_code=404, detail="Unable to unfurl URL")

    return {
        "url": url,
        "unfurl": unfurl,
    }
