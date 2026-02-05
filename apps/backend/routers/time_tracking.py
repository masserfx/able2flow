"""Time Tracking API for ANT HILL."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.time_tracking_service import (
    get_active_time_log,
    get_task_time_logs,
    get_task_time_summary,
    start_time_tracking,
    stop_time_tracking,
)

router = APIRouter(prefix="/api/time-tracking", tags=["time-tracking"])


class TimeLogStart(BaseModel):
    """Request to start time tracking."""

    task_id: int
    user_id: str  # TODO: Replace with auth dependency


class TimeLogStop(BaseModel):
    """Request to stop time tracking."""

    log_id: int
    user_id: str  # TODO: Replace with auth dependency


class TimeLogResponse(BaseModel):
    """Time log response."""

    id: int
    task_id: int
    user_id: str
    started_at: str
    ended_at: str | None
    duration_seconds: int | None
    is_active: int


class TimeLogWithUser(BaseModel):
    """Time log with user info."""

    id: int
    task_id: int
    user_id: str
    user_name: str | None
    started_at: str
    ended_at: str | None
    duration_seconds: int | None
    is_active: int


class TimeSummary(BaseModel):
    """Time summary for a task."""

    estimated_seconds: int
    actual_seconds: int
    efficiency_ratio: float
    over_estimate: bool
    variance_seconds: int


@router.post("/start", response_model=TimeLogResponse)
async def start_tracking(data: TimeLogStart):
    """Start time tracking for a task."""
    try:
        log = start_time_tracking(data.task_id, data.user_id)
        return log
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop", response_model=TimeLogResponse)
async def stop_tracking(data: TimeLogStop):
    """Stop time tracking."""
    try:
        log = stop_time_tracking(data.log_id, data.user_id)
        return log
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active", response_model=TimeLogResponse | None)
async def get_active(user_id: str):
    """Get currently active time log for user."""
    try:
        log = get_active_time_log(user_id)
        return log
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}/logs", response_model=list[TimeLogWithUser])
async def get_task_logs(task_id: int):
    """Get all time logs for a task."""
    try:
        logs = get_task_time_logs(task_id)
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}/summary", response_model=TimeSummary)
async def get_task_summary(task_id: int):
    """Get time summary for a task."""
    try:
        summary = get_task_time_summary(task_id)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
