"""Columns router for Kanban board."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import get_db
from services import audit_service

router = APIRouter(prefix="/api/columns", tags=["columns"])


class ColumnCreate(BaseModel):
    name: str
    position: int | None = None
    color: str = "#3b82f6"
    board_id: int = 1
    project_id: int | None = None


class ColumnUpdate(BaseModel):
    name: str | None = None
    position: int | None = None
    color: str | None = None


class Column(BaseModel):
    id: int
    board_id: int
    name: str
    position: int
    color: str
    created_at: str


def row_to_column(row) -> dict:
    """Convert database row to column dict."""
    return {
        "id": row["id"],
        "board_id": row["board_id"],
        "name": row["name"],
        "position": row["position"],
        "color": row["color"],
        "created_at": row["created_at"],
    }


@router.get("", response_model=list[Column])
def list_columns(board_id: int = 1, project_id: int | None = None) -> list[dict]:
    """Get all columns for a board, optionally filtered by project."""
    with get_db() as conn:
        if project_id is not None:
            cursor = conn.execute(
                "SELECT * FROM columns WHERE board_id = ? AND project_id = ? ORDER BY position",
                (board_id, project_id),
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM columns WHERE board_id = ? ORDER BY position",
                (board_id,),
            )
        return [row_to_column(row) for row in cursor.fetchall()]


@router.get("/{column_id}", response_model=Column)
def get_column(column_id: int) -> dict:
    """Get a single column by ID."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM columns WHERE id = ?", (column_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Column not found")
        return row_to_column(row)


@router.post("", response_model=Column)
def create_column(column: ColumnCreate) -> dict:
    """Create a new column."""
    with get_db() as conn:
        position = column.position
        if position is None:
            cursor = conn.execute(
                "SELECT MAX(position) as max_pos FROM columns WHERE board_id = ?",
                (column.board_id,),
            )
            row = cursor.fetchone()
            position = (row["max_pos"] or 0) + 1

        cursor = conn.execute(
            """
            INSERT INTO columns (board_id, name, position, color)
            VALUES (?, ?, ?, ?)
            """,
            (column.board_id, column.name, position, column.color),
        )
        conn.commit()
        column_id = cursor.lastrowid

        cursor = conn.execute("SELECT * FROM columns WHERE id = ?", (column_id,))
        row = cursor.fetchone()
        result = row_to_column(row)

        audit_service.log_action("column", column_id, "create", new_value=result)

        return result


@router.put("/{column_id}", response_model=Column)
def update_column(column_id: int, column: ColumnUpdate) -> dict:
    """Update an existing column."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM columns WHERE id = ?", (column_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Column not found")

        old_value = row_to_column(existing)

        updates = []
        values = []

        for field in ["name", "position", "color"]:
            value = getattr(column, field)
            if value is not None:
                updates.append(f"{field} = ?")
                values.append(value)

        if updates:
            values.append(column_id)
            conn.execute(
                f"UPDATE columns SET {', '.join(updates)} WHERE id = ?",
                values,
            )
            conn.commit()

        cursor = conn.execute("SELECT * FROM columns WHERE id = ?", (column_id,))
        row = cursor.fetchone()
        result = row_to_column(row)

        audit_service.log_action("column", column_id, "update", old_value=old_value, new_value=result)

        return result


@router.delete("/{column_id}")
def delete_column(column_id: int) -> dict:
    """Delete a column (tasks in this column will have column_id set to NULL)."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM columns WHERE id = ?", (column_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Column not found")

        old_value = row_to_column(existing)

        # Set tasks in this column to NULL
        conn.execute("UPDATE tasks SET column_id = NULL WHERE column_id = ?", (column_id,))
        conn.execute("DELETE FROM columns WHERE id = ?", (column_id,))
        conn.commit()

        audit_service.log_action("column", column_id, "delete", old_value=old_value)

        return {"message": "Column deleted"}
