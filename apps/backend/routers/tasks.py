"""Tasks router for Able2Flow API."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import get_db
from services import audit_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    column_id: int | None = None
    position: int | None = None
    priority: str = "medium"
    due_date: str | None = None
    project_id: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    completed: bool | None = None
    column_id: int | None = None
    position: int | None = None
    priority: str | None = None
    due_date: str | None = None


class TaskMove(BaseModel):
    column_id: int
    position: int


class Task(BaseModel):
    id: int
    title: str
    description: str | None
    completed: bool
    column_id: int | None
    project_id: int | None
    position: int
    priority: str
    due_date: str | None
    created_at: str
    archived: bool
    # ANT HILL fields
    assigned_to: str | None = None
    assigned_at: str | None = None
    estimated_minutes: int | None = None
    points: int | None = None
    time_spent_seconds: int | None = None
    completed_at: str | None = None
    claimed_from_marketplace: bool = False


def _safe_get(row, key, default=None):
    """Safely get a value from sqlite3.Row (which lacks .get())."""
    return row[key] if key in row.keys() else default


def row_to_task(row) -> dict:
    """Convert database row to task dict."""
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "completed": bool(row["completed"]),
        "column_id": row["column_id"],
        "project_id": row["project_id"],
        "position": row["position"] or 0,
        "priority": row["priority"] or "medium",
        "due_date": row["due_date"],
        "archived": bool(row["archived"]) if "archived" in row.keys() else False,
        "created_at": row["created_at"],
        # ANT HILL fields
        "assigned_to": _safe_get(row, "assigned_to"),
        "assigned_at": _safe_get(row, "assigned_at"),
        "estimated_minutes": _safe_get(row, "estimated_minutes"),
        "points": _safe_get(row, "points"),
        "time_spent_seconds": _safe_get(row, "time_spent_seconds"),
        "completed_at": _safe_get(row, "completed_at"),
        "claimed_from_marketplace": bool(_safe_get(row, "claimed_from_marketplace", 0)),
    }


@router.get("", response_model=list[Task])
def list_tasks(column_id: int | None = None, project_id: int | None = None) -> list[dict]:
    """Get all tasks, optionally filtered by column and/or project."""
    with get_db() as conn:
        conditions = []
        params = []

        if column_id is not None:
            conditions.append("column_id = ?")
            params.append(column_id)

        if project_id is not None:
            conditions.append("project_id = ?")
            params.append(project_id)

        if conditions:
            where_clause = " AND ".join(conditions)
            order = "ORDER BY position" if column_id is not None else "ORDER BY created_at DESC"
            cursor = conn.execute(
                f"SELECT * FROM tasks WHERE {where_clause} {order}",
                params,
            )
        else:
            cursor = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC")
        return [row_to_task(row) for row in cursor.fetchall()]


@router.get("/marketplace", response_model=list[Task])
def get_marketplace_tasks(project_id: int | None = None):
    """Get all unassigned tasks (marketplace)."""
    with get_db() as conn:
        conditions = ["assigned_to IS NULL", "archived = 0"]
        params = []

        if project_id is not None:
            conditions.append("project_id = ?")
            params.append(project_id)

        where_clause = " AND ".join(conditions)
        cursor = conn.execute(
            f"""SELECT * FROM tasks
                WHERE {where_clause}
                ORDER BY points DESC, created_at ASC""",
            params,
        )

        return [row_to_task(row) for row in cursor.fetchall()]


@router.get("/{task_id}", response_model=Task)
def get_task(task_id: int) -> dict:
    """Get a single task by ID."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        return row_to_task(row)


@router.post("", response_model=Task)
def create_task(task: TaskCreate) -> dict:
    """Create a new task."""
    with get_db() as conn:
        # Determine project_id from column if not provided
        project_id = task.project_id
        if project_id is None and task.column_id is not None:
            cursor = conn.execute(
                "SELECT project_id FROM columns WHERE id = ?",
                (task.column_id,),
            )
            col_row = cursor.fetchone()
            if col_row:
                project_id = col_row["project_id"]

        # Default to project 1 if still None
        if project_id is None:
            project_id = 1

        # Get max position in column
        position = task.position
        if position is None and task.column_id is not None:
            cursor = conn.execute(
                "SELECT MAX(position) as max_pos FROM tasks WHERE column_id = ?",
                (task.column_id,),
            )
            row = cursor.fetchone()
            position = (row["max_pos"] or 0) + 1

        cursor = conn.execute(
            """
            INSERT INTO tasks (title, description, column_id, project_id, position, priority, due_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (task.title, task.description, task.column_id, project_id, position or 0, task.priority, task.due_date),
        )
        conn.commit()
        task_id = cursor.lastrowid

        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        result = row_to_task(row)

        audit_service.log_action("task", task_id, "create", new_value=result)

        return result


@router.put("/{task_id}", response_model=Task)
def update_task(task_id: int, task: TaskUpdate) -> dict:
    """Update an existing task."""
    from datetime import datetime
    from services.gamification_service import award_points_for_task

    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Task not found")

        old_value = row_to_task(existing)

        updates = []
        values = []

        for field in ["title", "description", "column_id", "position", "priority", "due_date"]:
            value = getattr(task, field)
            if value is not None:
                updates.append(f"{field} = ?")
                values.append(value)

        # Track if task is being completed
        is_completing = task.completed is True and not existing["completed"]

        if task.completed is not None:
            updates.append("completed = ?")
            values.append(int(task.completed))

            # Set completed_at timestamp if completing
            if is_completing:
                updates.append("completed_at = ?")
                values.append(datetime.now().isoformat())

        if updates:
            values.append(task_id)
            conn.execute(
                f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?",
                values,
            )
            conn.commit()

        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        result = row_to_task(row)

        audit_service.log_action("task", task_id, "update", old_value=old_value, new_value=result)

        # Award points if task was completed
        if is_completing and existing["assigned_to"]:
            try:
                points_info = award_points_for_task(task_id, existing["assigned_to"])
                result["points_awarded"] = points_info
            except Exception as e:
                # Log error but don't fail the update
                import logging
                logging.error(f"Failed to award points for task {task_id}: {e}")

        return result


@router.put("/{task_id}/move", response_model=Task)
def move_task(task_id: int, move: TaskMove) -> dict:
    """Move a task to a different column/position (drag & drop)."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Task not found")

        old_value = row_to_task(existing)
        old_column = existing["column_id"]
        old_position = existing["position"]

        # Update positions in old column (shift up)
        if old_column is not None:
            conn.execute(
                """
                UPDATE tasks SET position = position - 1
                WHERE column_id = ? AND position > ?
                """,
                (old_column, old_position),
            )

        # Update positions in new column (shift down)
        conn.execute(
            """
            UPDATE tasks SET position = position + 1
            WHERE column_id = ? AND position >= ?
            """,
            (move.column_id, move.position),
        )

        # Move the task
        conn.execute(
            """
            UPDATE tasks SET column_id = ?, position = ?
            WHERE id = ?
            """,
            (move.column_id, move.position, task_id),
        )
        conn.commit()

        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        result = row_to_task(row)

        audit_service.log_action("task", task_id, "move", old_value=old_value, new_value=result)

        return result


@router.delete("/{task_id}")
def delete_task(task_id: int) -> dict:
    """Delete a task."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Task not found")

        old_value = row_to_task(existing)

        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()

        audit_service.log_action("task", task_id, "delete", old_value=old_value)

        return {"message": "Task deleted"}

@router.post("/{task_id}/duplicate", response_model=Task)
def duplicate_task(task_id: int) -> dict:
    """Duplicate a task with all its properties."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Task not found")

        # Get max position in same column for placement
        cursor = conn.execute(
            "SELECT MAX(position) as max_pos FROM tasks WHERE column_id = ?",
            (existing["column_id"],),
        )
        row = cursor.fetchone()
        new_position = (row["max_pos"] or 0) + 1

        # Create duplicate with "(Copy)" suffix
        cursor = conn.execute(
            """
            INSERT INTO tasks (title, description, column_id, project_id, position, priority, due_date, completed, archived)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"{existing['title']} (Copy)",
                existing["description"],
                existing["column_id"],
                existing["project_id"],
                new_position,
                existing["priority"],
                existing["due_date"],
                0,  # Reset completed status
                0,  # Not archived
            ),
        )
        conn.commit()
        new_task_id = cursor.lastrowid

        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (new_task_id,))
        row = cursor.fetchone()
        result = row_to_task(row)

        audit_service.log_action("task", new_task_id, "duplicate", old_value={"source_id": task_id})

        return result


@router.put("/{task_id}/archive", response_model=Task)
def archive_task(task_id: int) -> dict:
    """Archive or unarchive a task."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Task not found")

        old_value = row_to_task(existing)
        new_archived = 0 if existing["archived"] else 1

        conn.execute(
            "UPDATE tasks SET archived = ? WHERE id = ?",
            (new_archived, task_id),
        )
        conn.commit()

        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        result = row_to_task(row)

        audit_service.log_action("task", task_id, "archive" if new_archived else "unarchive", old_value=old_value, new_value=result)

        return result


# ============================================================================
# ANT HILL - Marketplace and Assignment
# ============================================================================


class TaskAssignment(BaseModel):
    """Task assignment request."""

    user_id: str  # TODO: Replace with auth dependency


class TaskEstimate(BaseModel):
    """Set task estimate."""

    estimated_minutes: int


@router.post("/{task_id}/assign-to-me", response_model=Task)
def assign_task_to_me(task_id: int, data: TaskAssignment):
    """Self-assign task from marketplace."""
    from datetime import datetime

    with get_db() as conn:
        # Get task
        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Task not found")

        # Check if already assigned
        if existing["assigned_to"]:
            raise HTTPException(status_code=409, detail="Task already assigned")

        old_value = row_to_task(existing)

        # Assign task
        conn.execute(
            """UPDATE tasks
               SET assigned_to = ?,
                   assigned_at = ?,
                   claimed_from_marketplace = 1
               WHERE id = ?""",
            (data.user_id, datetime.now().isoformat(), task_id),
        )
        conn.commit()

        # Get user name for notification
        user = conn.execute(
            "SELECT name FROM users WHERE id = ?", (data.user_id,)
        ).fetchone()
        user_name = user["name"] if user else "Unknown"

        # Create notification
        conn.execute(
            """INSERT INTO notifications
               (user_id, notification_type, title, message, related_task_id)
               VALUES (NULL, 'task_claimed', ?, ?, ?)""",
            (
                f"🎯 {user_name} si vzal task!",
                f"Task '{existing['title']}' byl přiřazen",
                task_id,
            ),
        )
        conn.commit()

        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        result = row_to_task(row)

        audit_service.log_action("task", task_id, "assign", old_value=old_value, new_value=result)

        return result


@router.post("/{task_id}/release")
def release_task(task_id: int, data: TaskAssignment):
    """Release task back to marketplace."""
    with get_db() as conn:
        # Get task
        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Task not found")

        # Verify ownership
        if existing["assigned_to"] != data.user_id:
            raise HTTPException(status_code=403, detail="Not assigned to you")

        old_value = row_to_task(existing)

        # Stop any active time logs
        conn.execute(
            """UPDATE time_logs
               SET ended_at = CURRENT_TIMESTAMP,
                   duration_seconds = CAST((julianday(CURRENT_TIMESTAMP) - julianday(started_at)) * 86400 AS INTEGER),
                   is_active = 0
               WHERE task_id = ? AND user_id = ? AND is_active = 1""",
            (task_id, data.user_id),
        )

        # Release task
        conn.execute(
            """UPDATE tasks
               SET assigned_to = NULL,
                   assigned_at = NULL
               WHERE id = ?""",
            (task_id,),
        )
        conn.commit()

        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        result = row_to_task(row)

        audit_service.log_action("task", task_id, "release", old_value=old_value, new_value=result)

        return {"message": "Task released", "task": result}


@router.put("/{task_id}/estimate", response_model=Task)
def set_task_estimate(task_id: int, data: TaskEstimate):
    """Set time estimate and calculate points."""
    import math

    with get_db() as conn:
        # Get task
        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Task not found")

        old_value = row_to_task(existing)

        # Calculate points (1 bod = 10 minut)
        points = max(1, math.ceil(data.estimated_minutes / 10))

        # Update task
        conn.execute(
            """UPDATE tasks
               SET estimated_minutes = ?,
                   points = ?
               WHERE id = ?""",
            (data.estimated_minutes, points, task_id),
        )
        conn.commit()

        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        result = row_to_task(row)

        audit_service.log_action("task", task_id, "set_estimate", old_value=old_value, new_value=result)

        return result
