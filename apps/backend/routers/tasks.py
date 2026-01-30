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
        "created_at": row["created_at"],
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

        if task.completed is not None:
            updates.append("completed = ?")
            values.append(int(task.completed))

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
