"""Gamification service for ANT HILL - points calculation and leaderboard."""

import math
from datetime import datetime, timedelta
from typing import Optional

from database import get_db


def calculate_points(estimated_minutes: int) -> int:
    """Calculate points from estimated minutes (1 bod = 10 minut)."""
    return max(1, math.ceil(estimated_minutes / 10))


def calculate_bonus_points(
    task_id: int,
    actual_seconds: int,
    estimated_minutes: int,
    due_date: Optional[str],
    completed_at: str,
    priority: str,
) -> int:
    """Calculate bonus points based on efficiency and priority."""
    bonus = 0
    estimated_seconds = estimated_minutes * 60

    # Bonus 1: Completed faster than estimate (+20%)
    if estimated_seconds > 0 and actual_seconds < estimated_seconds * 0.8:
        base_points = calculate_points(estimated_minutes)
        bonus += int(base_points * 0.2)

    # Bonus 2: Completed before deadline (+10%)
    if due_date and completed_at:
        try:
            due_dt = datetime.fromisoformat(due_date)
            completed_dt = datetime.fromisoformat(completed_at)
            if completed_dt < due_dt:
                base_points = calculate_points(estimated_minutes)
                bonus += int(base_points * 0.1)
        except (ValueError, TypeError):
            pass

    # Bonus 3: High priority tasks (+5 bodů)
    if priority == "critical":
        bonus += 5
    elif priority == "high":
        bonus += 3

    return bonus


def award_points_for_task(task_id: int, user_id: str) -> dict:
    """Award points to user when task is completed."""
    with get_db() as conn:
        # Get task details
        task = conn.execute(
            """SELECT estimated_minutes, time_spent_seconds, due_date,
                      completed_at, priority, title, points
               FROM tasks WHERE id = ?""",
            (task_id,),
        ).fetchone()

        if not task:
            raise ValueError(f"Task {task_id} not found")

        estimated_minutes = task["estimated_minutes"] or 0
        time_spent = task["time_spent_seconds"] or 0
        due_date = task["due_date"]
        completed_at = task["completed_at"]
        priority = task["priority"] or "medium"
        title = task["title"]
        base_points = task["points"] or calculate_points(estimated_minutes)

        # Calculate bonus
        bonus = calculate_bonus_points(
            task_id, time_spent, estimated_minutes, due_date, completed_at, priority
        )
        total_points = base_points + bonus

        # Get user name for notification
        user = conn.execute(
            "SELECT name FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        user_name = user["name"] if user else "Unknown"

        # Update user_points for all periods
        now = datetime.now()
        periods = [
            ("daily", now.date(), now.date() + timedelta(days=1)),
            (
                "weekly",
                now.date() - timedelta(days=now.weekday()),
                now.date() - timedelta(days=now.weekday()) + timedelta(days=7),
            ),
            (
                "monthly",
                now.date().replace(day=1),
                (now.date().replace(day=1) + timedelta(days=32)).replace(day=1),
            ),
            ("all_time", datetime(2000, 1, 1).date(), datetime(2099, 12, 31).date()),
        ]

        for period_type, period_start, period_end in periods:
            conn.execute(
                """INSERT INTO user_points
                   (user_id, period_type, period_start, period_end, points_earned, tasks_completed, bonus_points)
                   VALUES (?, ?, ?, ?, ?, 1, ?)
                   ON CONFLICT(user_id, period_type, period_start) DO UPDATE SET
                       points_earned = points_earned + excluded.points_earned,
                       tasks_completed = tasks_completed + 1,
                       bonus_points = bonus_points + excluded.bonus_points,
                       updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, period_type, period_start, period_end, base_points, bonus),
            )

        # Create notification
        conn.execute(
            """INSERT INTO notifications
               (user_id, notification_type, title, message, related_task_id)
               VALUES (NULL, 'points_awarded', ?, ?, ?)""",
            (
                f"💎 {user_name} získal {total_points} bodů!",
                f"Dokončil task: {title}",
                task_id,
            ),
        )

        conn.commit()

        return {
            "base_points": base_points,
            "bonus_points": bonus,
            "total_points": total_points,
        }


def get_leaderboard(period_type: str = "weekly", limit: int = 10) -> list[dict]:
    """Get leaderboard for specified period."""
    with get_db() as conn:
        # Get current period bounds
        now = datetime.now()
        if period_type == "weekly":
            period_start = now.date() - timedelta(days=now.weekday())
        elif period_type == "monthly":
            period_start = now.date().replace(day=1)
        elif period_type == "all_time":
            period_start = datetime(2000, 1, 1).date()
        else:  # daily
            period_start = now.date()

        # Query leaderboard with user info
        rows = conn.execute(
            """SELECT
                   up.user_id,
                   u.name as user_name,
                   u.email as user_email,
                   u.avatar_url,
                   up.points_earned,
                   up.tasks_completed,
                   up.bonus_points,
                   (up.points_earned + up.bonus_points) as total_points
               FROM user_points up
               JOIN users u ON up.user_id = u.id
               WHERE up.period_type = ? AND up.period_start = ?
               ORDER BY total_points DESC
               LIMIT ?""",
            (period_type, period_start, limit),
        ).fetchall()

        return [
            {
                "rank": idx + 1,
                "user_id": row["user_id"],
                "user_name": row["user_name"],
                "user_email": row["user_email"],
                "avatar_url": row["avatar_url"],
                "points_earned": row["points_earned"],
                "tasks_completed": row["tasks_completed"],
                "bonus_points": row["bonus_points"],
                "total_points": row["total_points"],
            }
            for idx, row in enumerate(rows)
        ]


def get_user_stats(user_id: str) -> dict:
    """Get statistics for a specific user."""
    with get_db() as conn:
        # Get all-time stats
        all_time = conn.execute(
            """SELECT points_earned, tasks_completed, bonus_points
               FROM user_points
               WHERE user_id = ? AND period_type = 'all_time'
               LIMIT 1""",
            (user_id,),
        ).fetchone()

        if not all_time:
            return {
                "total_points": 0,
                "tasks_completed": 0,
                "avg_points_per_task": 0,
                "efficiency_ratio": 0,
            }

        total_points = all_time["points_earned"] + all_time["bonus_points"]
        tasks = all_time["tasks_completed"]

        # Calculate efficiency (sum of time_spent vs estimated)
        efficiency = conn.execute(
            """SELECT
                   SUM(estimated_minutes * 60) as total_estimated,
                   SUM(time_spent_seconds) as total_spent
               FROM tasks
               WHERE assigned_to = ? AND completed = 1 AND estimated_minutes IS NOT NULL""",
            (user_id,),
        ).fetchone()

        efficiency_ratio = 1.0
        if efficiency and efficiency["total_spent"] and efficiency["total_estimated"]:
            efficiency_ratio = (
                efficiency["total_estimated"] / efficiency["total_spent"]
            )

        return {
            "total_points": total_points,
            "tasks_completed": tasks,
            "avg_points_per_task": round(total_points / tasks, 1) if tasks > 0 else 0,
            "efficiency_ratio": round(efficiency_ratio, 2),
        }
