"""Gmail integration endpoints."""

from typing import Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
from auth.clerk_middleware import ClerkUser
from services.integrations import GmailService

router = APIRouter(prefix="/api/integrations/gmail", tags=["Gmail"])


class SendEmailRequest(BaseModel):
    """Request to send an email."""
    to: str
    subject: str
    body: str


class CreateTaskFromEmailRequest(BaseModel):
    """Request to create a task from an email."""
    message_id: str
    project_id: int = 1


class SendNotificationRequest(BaseModel):
    """Request to send notification email."""
    to: str
    incident_id: Optional[int] = None
    task_id: Optional[int] = None
    event_type: str = "updated"


@router.get("/messages")
async def list_messages(
    query: Optional[str] = None,
    max_results: int = 10,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """List recent Gmail messages."""
    service = GmailService(user.user_id)

    messages = await service.list_messages(query=query, max_results=max_results)

    return {
        "messages": messages,
        "count": len(messages),
    }


@router.get("/messages/{message_id}")
async def get_message(
    message_id: str,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Get a specific email message with content."""
    service = GmailService(user.user_id)

    message = await service.get_message_content(message_id)

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    return {
        "message": message,
    }


@router.post("/send")
async def send_email(
    request: SendEmailRequest,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Send an email."""
    service = GmailService(user.user_id)

    result = await service.send_email(
        to=request.to,
        subject=request.subject,
        body=request.body,
    )

    if not result:
        raise HTTPException(status_code=400, detail="Failed to send email")

    return {
        "status": "success",
        "message_id": result.get("id"),
    }


@router.post("/create-task-from-email")
async def create_task_from_email(
    request: CreateTaskFromEmailRequest,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Create a task from an email message."""
    service = GmailService(user.user_id)

    task = await service.create_task_from_email(
        message_id=request.message_id,
        project_id=request.project_id,
    )

    if not task:
        raise HTTPException(status_code=400, detail="Failed to create task from email")

    return {
        "status": "success",
        "task": task,
    }


@router.post("/send-notification")
async def send_notification(
    request: SendNotificationRequest,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Send notification email about incident or task."""
    service = GmailService(user.user_id)

    from database import get_db

    if request.incident_id:
        # Get incident
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM incidents WHERE id = ?", (request.incident_id,))
            incident = cursor.fetchone()

            if not incident:
                raise HTTPException(status_code=404, detail="Incident not found")

            result = await service.send_incident_notification(
                to=request.to,
                incident=dict(incident),
            )

    elif request.task_id:
        # Get task
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (request.task_id,))
            task = cursor.fetchone()

            if not task:
                raise HTTPException(status_code=404, detail="Task not found")

            result = await service.send_task_notification(
                to=request.to,
                task=dict(task),
                event_type=request.event_type,
            )
    else:
        raise HTTPException(status_code=400, detail="Must provide incident_id or task_id")

    if not result:
        raise HTTPException(status_code=400, detail="Failed to send notification")

    return {
        "status": "success",
        "message_id": result.get("id"),
    }


@router.post("/daily-digest")
async def send_daily_digest(
    to: str,
    project_id: Optional[int] = None,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Send daily digest email."""
    service = GmailService(user.user_id)

    result = await service.send_daily_digest(
        to=to,
        project_id=project_id,
    )

    if not result:
        raise HTTPException(status_code=400, detail="Failed to send digest")

    return {
        "status": "success",
        "message_id": result.get("id"),
    }
