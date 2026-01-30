"""Dashboard router for analytics summary."""

from fastapi import APIRouter

from database import get_db
from services import audit_service
from services.monitor_service import get_monitor_stats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard(project_id: int | None = None) -> dict:
    """Get dashboard summary with all key metrics, optionally filtered by project."""
    with get_db() as conn:
        # Build project filter
        project_filter = ""
        project_params: tuple = ()
        if project_id is not None:
            project_filter = " WHERE project_id = ?"
            project_params = (project_id,)

        # Task statistics
        cursor = conn.execute(f"SELECT COUNT(*) as total FROM tasks{project_filter}", project_params)
        total_tasks = cursor.fetchone()["total"]

        task_completed_filter = " WHERE completed = 1" if project_id is None else " WHERE completed = 1 AND project_id = ?"
        cursor = conn.execute(f"SELECT COUNT(*) as completed FROM tasks{task_completed_filter}", project_params)
        completed_tasks = cursor.fetchone()["completed"]

        task_priority_filter = " WHERE completed = 0" if project_id is None else " WHERE completed = 0 AND project_id = ?"
        cursor = conn.execute(
            f"""
            SELECT priority, COUNT(*) as count
            FROM tasks
            {task_priority_filter}
            GROUP BY priority
            """,
            project_params,
        )
        tasks_by_priority = {row["priority"]: row["count"] for row in cursor.fetchall()}

        # Tasks by column
        if project_id is not None:
            cursor = conn.execute(
                """
                SELECT c.name as column_name, COUNT(t.id) as count
                FROM columns c
                LEFT JOIN tasks t ON t.column_id = c.id AND t.project_id = ?
                WHERE c.project_id = ?
                GROUP BY c.id, c.name
                ORDER BY c.position
                """,
                (project_id, project_id),
            )
        else:
            cursor = conn.execute(
                """
                SELECT c.name as column_name, COUNT(t.id) as count
                FROM columns c
                LEFT JOIN tasks t ON t.column_id = c.id
                GROUP BY c.id, c.name
                ORDER BY c.position
                """
            )
        tasks_by_column = {row["column_name"]: row["count"] for row in cursor.fetchall()}

        # Overdue tasks
        overdue_filter = " WHERE due_date < date('now') AND completed = 0" if project_id is None else " WHERE due_date < date('now') AND completed = 0 AND project_id = ?"
        cursor = conn.execute(
            f"""
            SELECT COUNT(*) as overdue
            FROM tasks
            {overdue_filter}
            """,
            project_params,
        )
        overdue_tasks = cursor.fetchone()["overdue"]

    # Monitoring stats
    monitor_stats = get_monitor_stats(project_id=project_id)

    # Audit stats
    audit_stats = audit_service.get_audit_stats()

    return {
        "tasks": {
            "total": total_tasks,
            "completed": completed_tasks,
            "pending": total_tasks - completed_tasks,
            "completion_rate": round((completed_tasks / total_tasks) * 100, 1) if total_tasks > 0 else 0,
            "by_priority": tasks_by_priority,
            "by_column": tasks_by_column,
            "overdue": overdue_tasks,
        },
        "monitoring": monitor_stats,
        "activity": {
            "total_actions": audit_stats["total_actions"],
            "recent_24h": audit_stats["recent_24h"],
        },
    }


@router.get("/tasks")
def get_task_stats() -> dict:
    """Get detailed task statistics."""
    with get_db() as conn:
        cursor = conn.execute("SELECT COUNT(*) as total FROM tasks")
        total = cursor.fetchone()["total"]

        cursor = conn.execute("SELECT COUNT(*) as completed FROM tasks WHERE completed = 1")
        completed = cursor.fetchone()["completed"]

        cursor = conn.execute(
            """
            SELECT priority, COUNT(*) as count
            FROM tasks
            GROUP BY priority
            """
        )
        by_priority = {row["priority"]: row["count"] for row in cursor.fetchall()}

        cursor = conn.execute(
            """
            SELECT date(created_at) as date, COUNT(*) as count
            FROM tasks
            WHERE created_at > date('now', '-7 days')
            GROUP BY date(created_at)
            ORDER BY date
            """
        )
        created_last_7_days = [
            {"date": row["date"], "count": row["count"]}
            for row in cursor.fetchall()
        ]

    return {
        "total": total,
        "completed": completed,
        "pending": total - completed,
        "by_priority": by_priority,
        "created_last_7_days": created_last_7_days,
    }


@router.get("/monitoring")
def get_monitoring_stats() -> dict:
    """Get detailed monitoring statistics."""
    return get_monitor_stats()
