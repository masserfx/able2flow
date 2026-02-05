"""Gamification API - Leaderboards and Points."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.gamification_service import (
    calculate_points,
    get_leaderboard,
    get_user_stats,
)

router = APIRouter(prefix="/api/leaderboard", tags=["gamification"])


class LeaderboardEntry(BaseModel):
    """Leaderboard entry model."""

    rank: int
    user_id: str
    user_name: str
    user_email: str
    avatar_url: str | None
    points_earned: int
    tasks_completed: int
    bonus_points: int
    total_points: int


class UserStats(BaseModel):
    """User statistics model."""

    total_points: int
    tasks_completed: int
    avg_points_per_task: float
    efficiency_ratio: float


@router.get("/weekly", response_model=list[LeaderboardEntry])
async def get_weekly_leaderboard(limit: int = 10):
    """Get TOP performers for current week."""
    try:
        return get_leaderboard("weekly", limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monthly", response_model=list[LeaderboardEntry])
async def get_monthly_leaderboard(limit: int = 10):
    """Get TOP performers for current month."""
    try:
        return get_leaderboard("monthly", limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily", response_model=list[LeaderboardEntry])
async def get_daily_leaderboard(limit: int = 10):
    """Get TOP performers for today."""
    try:
        return get_leaderboard("daily", limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all-time", response_model=list[LeaderboardEntry])
async def get_alltime_leaderboard(limit: int = 10):
    """Get all-time TOP performers."""
    try:
        return get_leaderboard("all_time", limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}", response_model=UserStats)
async def get_user_statistics(user_id: str):
    """Get statistics for specific user."""
    try:
        return get_user_stats(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calculate-points")
async def calculate_task_points(estimated_minutes: int):
    """Calculate how many points a task would be worth."""
    return {"estimated_minutes": estimated_minutes, "points": calculate_points(estimated_minutes)}
