"""Time tracking service for ANT HILL."""

from datetime import datetime
from typing import Optional

from database import get_db


def start_time_tracking(task_id: int, user_id: str) -> dict:
    """Start time tracking for a task."""
    with get_db() as conn:
        # Verify task exists and is assigned to user
        task = conn.execute(
            "SELECT assigned_to FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()

        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Stop any active time logs for this user
        conn.execute(
            """UPDATE time_logs
               SET ended_at = CURRENT_TIMESTAMP,
                   duration_seconds = CAST((julianday(CURRENT_TIMESTAMP) - julianday(started_at)) * 86400 AS INTEGER),
                   is_active = 0
               WHERE user_id = ? AND is_active = 1""",
            (user_id,),
        )

        # Create new time log
        cursor = conn.execute(
            """INSERT INTO time_logs (task_id, user_id, started_at)
               VALUES (?, ?, CURRENT_TIMESTAMP)""",
            (task_id, user_id),
        )

        log_id = cursor.lastrowid

        # Get the created log
        log = conn.execute(
            """SELECT id, task_id, user_id, started_at, ended_at, duration_seconds, is_active
               FROM time_logs WHERE id = ?""",
            (log_id,),
        ).fetchone()

        conn.commit()

        return dict(log)


def stop_time_tracking(log_id: int, user_id: str) -> dict:
    """Stop time tracking."""
    with get_db() as conn:
        # Get the log
        log = conn.execute(
            "SELECT task_id, started_at FROM time_logs WHERE id = ? AND user_id = ?",
            (log_id, user_id),
        ).fetchone()

        if not log:
            raise ValueError(f"Time log {log_id} not found or not owned by user")

        # Calculate duration
        started_at = datetime.fromisoformat(log["started_at"])
        ended_at = datetime.now()
        duration_seconds = int((ended_at - started_at).total_seconds())

        # Update log
        conn.execute(
            """UPDATE time_logs
               SET ended_at = ?,
                   duration_seconds = ?,
                   is_active = 0
               WHERE id = ?""",
            (ended_at.isoformat(), duration_seconds, log_id),
        )

        # Update task time_spent_seconds
        conn.execute(
            """UPDATE tasks
               SET time_spent_seconds = time_spent_seconds + ?
               WHERE id = ?""",
            (duration_seconds, log["task_id"]),
        )

        conn.commit()

        # Return updated log
        updated_log = conn.execute(
            """SELECT id, task_id, user_id, started_at, ended_at, duration_seconds, is_active
               FROM time_logs WHERE id = ?""",
            (log_id,),
        ).fetchone()

        return dict(updated_log)


def get_active_time_log(user_id: str) -> Optional[dict]:
    """Get active time log for user."""
    with get_db() as conn:
        log = conn.execute(
            """SELECT id, task_id, user_id, started_at, ended_at, duration_seconds, is_active
               FROM time_logs
               WHERE user_id = ? AND is_active = 1
               LIMIT 1""",
            (user_id,),
        ).fetchone()

        return dict(log) if log else None


def get_task_time_logs(task_id: int) -> list[dict]:
    """Get all time logs for a task."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT tl.id, tl.task_id, tl.user_id, u.name as user_name,
                      tl.started_at, tl.ended_at, tl.duration_seconds, tl.is_active
               FROM time_logs tl
               LEFT JOIN users u ON tl.user_id = u.id
               WHERE tl.task_id = ?
               ORDER BY tl.started_at DESC""",
            (task_id,),
        ).fetchall()

        return [dict(row) for row in rows]


def get_task_time_summary(task_id: int) -> dict:
    """Get time summary for a task."""
    with get_db() as conn:
        task = conn.execute(
            """SELECT estimated_minutes, time_spent_seconds
               FROM tasks WHERE id = ?""",
            (task_id,),
        ).fetchone()

        if not task:
            raise ValueError(f"Task {task_id} not found")

        estimated_seconds = (task["estimated_minutes"] or 0) * 60
        actual_seconds = task["time_spent_seconds"] or 0

        efficiency_ratio = 0
        if actual_seconds > 0 and estimated_seconds > 0:
            efficiency_ratio = estimated_seconds / actual_seconds

        return {
            "estimated_seconds": estimated_seconds,
            "actual_seconds": actual_seconds,
            "efficiency_ratio": round(efficiency_ratio, 2),
            "over_estimate": actual_seconds > estimated_seconds,
            "variance_seconds": actual_seconds - estimated_seconds,
        }
