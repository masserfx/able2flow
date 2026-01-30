"""Google Calendar integration endpoints."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
from auth.clerk_middleware import ClerkUser
from services.integrations import CalendarService

router = APIRouter(prefix="/api/integrations/calendar", tags=["Calendar"])


class CreateEventRequest(BaseModel):
    """Request to create a calendar event."""
    summary: str
    start: datetime
    end: Optional[datetime] = None
    description: Optional[str] = None
    calendar_id: str = "primary"


class SyncTaskRequest(BaseModel):
    """Request to sync a task to calendar."""
    task_id: int
    calendar_id: str = "primary"


class SyncAllTasksRequest(BaseModel):
    """Request to sync all tasks to calendar."""
    project_id: Optional[int] = None
    calendar_id: str = "primary"


@router.get("/calendars")
async def list_calendars(user: ClerkUser = Depends(get_current_user)) -> dict:
    """List user's Google Calendars."""
    service = CalendarService(user.user_id)
    calendars = await service.list_calendars()

    return {
        "calendars": calendars,
    }


@router.get("/events")
async def get_events(
    calendar_id: str = "primary",
    days: int = 30,
    max_results: int = 100,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Get calendar events."""
    service = CalendarService(user.user_id)

    time_min = datetime.now()
    time_max = datetime.now()
    from datetime import timedelta
    time_max = time_min + timedelta(days=days)

    events = await service.get_events(
        calendar_id=calendar_id,
        time_min=time_min,
        time_max=time_max,
        max_results=max_results,
    )

    return {
        "events": events,
        "calendar_id": calendar_id,
    }


@router.post("/events")
async def create_event(
    request: CreateEventRequest,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Create a calendar event."""
    service = CalendarService(user.user_id)

    event = await service.create_event(
        summary=request.summary,
        start=request.start,
        end=request.end,
        description=request.description,
        calendar_id=request.calendar_id,
    )

    if not event:
        raise HTTPException(status_code=400, detail="Failed to create event")

    return {
        "status": "success",
        "event": event,
    }


@router.post("/sync/task")
async def sync_task_to_calendar(
    request: SyncTaskRequest,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Sync a single task to Google Calendar."""
    service = CalendarService(user.user_id)

    event = await service.sync_task_to_calendar(
        task_id=request.task_id,
        calendar_id=request.calendar_id,
    )

    if not event:
        raise HTTPException(
            status_code=400,
            detail="Failed to sync task. Make sure the task has a due date."
        )

    return {
        "status": "success",
        "event": event,
    }


@router.post("/sync/all")
async def sync_all_tasks(
    request: SyncAllTasksRequest,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """Sync all tasks with due dates to Google Calendar."""
    service = CalendarService(user.user_id)

    result = await service.sync_all_tasks(
        project_id=request.project_id,
        calendar_id=request.calendar_id,
    )

    return {
        "status": "success",
        "synced": result["synced"],
        "failed": result["failed"],
        "total": result["total"],
    }


@router.post("/sync/from-calendar")
async def sync_from_calendar(
    request: SyncAllTasksRequest,
    user: ClerkUser = Depends(get_current_user)
) -> dict:
    """
    Sync from Google Calendar back to tasks.
    If an event was deleted in Calendar, mark the task as completed.
    """
    service = CalendarService(user.user_id)

    result = await service.sync_from_calendar(
        project_id=request.project_id,
        calendar_id=request.calendar_id,
    )

    return {
        "status": "success",
        "completed": result["completed"],
        "checked": result["checked"],
    }
