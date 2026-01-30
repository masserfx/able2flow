"""Projects router for project management."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import get_db
from services import audit_service

router = APIRouter(prefix="/api/projects", tags=["projects"])

DEFAULT_COLUMNS = [
    ("Backlog", 0, "#6b7280"),
    ("To Do", 1, "#3b82f6"),
    ("In Progress", 2, "#f59e0b"),
    ("Done", 3, "#10b981"),
]


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    color: str | None = "#7aa2f7"


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None


class Project(BaseModel):
    id: int
    name: str
    description: str | None
    color: str
    created_at: str


def row_to_project(row) -> dict:
    """Convert database row to project dict."""
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "color": row["color"],
        "created_at": row["created_at"],
    }


@router.get("", response_model=list[Project])
def list_projects() -> list[dict]:
    """Get all projects."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM projects ORDER BY created_at DESC")
        return [row_to_project(row) for row in cursor.fetchall()]


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: int) -> dict:
    """Get a single project by ID."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")
        return row_to_project(row)


@router.post("", response_model=Project)
def create_project(project: ProjectCreate) -> dict:
    """Create a new project with default columns."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO projects (name, description, color)
            VALUES (?, ?, ?)
            """,
            (project.name, project.description, project.color),
        )
        conn.commit()
        project_id = cursor.lastrowid

        # Create default columns for this project
        for name, position, color in DEFAULT_COLUMNS:
            conn.execute(
                """
                INSERT INTO columns (project_id, board_id, name, position, color)
                VALUES (?, ?, ?, ?, ?)
                """,
                (project_id, project_id, name, position, color),
            )
        conn.commit()

        cursor = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        result = row_to_project(row)

        audit_service.log_action("project", project_id, "create", new_value=result)

        return result


@router.put("/{project_id}", response_model=Project)
def update_project(project_id: int, project: ProjectUpdate) -> dict:
    """Update an existing project."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Project not found")

        old_value = row_to_project(existing)

        updates = []
        values = []

        for field in ["name", "description", "color"]:
            value = getattr(project, field)
            if value is not None:
                updates.append(f"{field} = ?")
                values.append(value)

        if updates:
            values.append(project_id)
            conn.execute(
                f"UPDATE projects SET {', '.join(updates)} WHERE id = ?",
                values,
            )
            conn.commit()

        cursor = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        result = row_to_project(row)

        audit_service.log_action("project", project_id, "update", old_value=old_value, new_value=result)

        return result


@router.delete("/{project_id}")
def delete_project(project_id: int) -> dict:
    """Delete a project and all related data (columns, tasks)."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Project not found")

        old_value = row_to_project(existing)

        # Cascade delete: tasks -> columns -> project
        conn.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
        conn.execute("DELETE FROM columns WHERE project_id = ?", (project_id,))
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()

        audit_service.log_action("project", project_id, "delete", old_value=old_value)

        return {"message": "Project deleted"}
