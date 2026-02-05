"""Incidents router for incident management."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from database import get_db
from services import audit_service
from services.ai_triage_service import ai_triage


INCIDENT_TEMPLATES = [
    {
        "id": "db-slow",
        "name": "Database Slow Query",
        "title": "Database response time > 5s",
        "severity": "critical",
        "description": "Database queries taking longer than 5s. Check slow query log and index usage."
    },
    {
        "id": "api-timeout",
        "name": "API Timeout",
        "title": "API endpoint timeout",
        "severity": "critical",
        "description": "External API not responding within timeout threshold (10s)."
    },
    {
        "id": "high-cpu",
        "name": "High CPU Usage",
        "title": "CPU usage above 80%",
        "severity": "warning",
        "description": "Server CPU usage sustained above 80% for 5+ minutes."
    },
    {
        "id": "disk-space",
        "name": "Low Disk Space",
        "title": "Disk space < 10%",
        "severity": "warning",
        "description": "Available disk space below 10%. Consider cleanup or expansion."
    },
    {
        "id": "ssl-expiry",
        "name": "SSL Certificate Expiring",
        "title": "SSL certificate expires in <30 days",
        "severity": "warning",
        "description": "SSL certificate nearing expiration. Renew before expiry date."
    }
]

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


class IncidentCreate(BaseModel):
    monitor_id: int | None = None
    title: str
    severity: str = "warning"
    description: str | None = None
    project_id: int | None = None


class IncidentUpdate(BaseModel):
    title: str | None = None
    status: str | None = None
    severity: str | None = None


class Incident(BaseModel):
    id: int
    monitor_id: int | None
    title: str
    status: str
    severity: str
    description: str | None
    started_at: str
    acknowledged_at: str | None
    resolved_at: str | None


def row_to_incident(row) -> dict:
    """Convert database row to incident dict."""
    return {
        "id": row["id"],
        "monitor_id": row["monitor_id"],
        "title": row["title"],
        "status": row["status"],
        "severity": row["severity"],
        "description": row["description"] if "description" in row.keys() else None,
        "started_at": row["started_at"],
        "acknowledged_at": row["acknowledged_at"],
        "resolved_at": row["resolved_at"],
    }



@router.get("/templates")
def get_incident_templates() -> dict:
    """Get list of incident templates for quick creation."""
    return {"templates": INCIDENT_TEMPLATES}


@router.get("", response_model=list[Incident])
def list_incidents(status: str | None = None, project_id: int | None = None) -> list[dict]:
    """Get all incidents, optionally filtered by status and/or project."""
    with get_db() as conn:
        conditions = []
        params = []

        if status:
            conditions.append("status = ?")
            params.append(status)

        if project_id is not None:
            conditions.append("project_id = ?")
            params.append(project_id)

        if conditions:
            where_clause = " AND ".join(conditions)
            cursor = conn.execute(
                f"SELECT * FROM incidents WHERE {where_clause} ORDER BY started_at DESC",
                params,
            )
        else:
            cursor = conn.execute("SELECT * FROM incidents ORDER BY started_at DESC")
        return [row_to_incident(row) for row in cursor.fetchall()]


@router.get("/open", response_model=list[Incident])
def list_open_incidents(project_id: int | None = None) -> list[dict]:
    """Get all open (non-resolved) incidents, optionally filtered by project."""
    with get_db() as conn:
        if project_id is not None:
            cursor = conn.execute(
                "SELECT * FROM incidents WHERE status != 'resolved' AND project_id = ? ORDER BY started_at DESC",
                (project_id,),
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM incidents WHERE status != 'resolved' ORDER BY started_at DESC"
            )
        return [row_to_incident(row) for row in cursor.fetchall()]


@router.get("/{incident_id}", response_model=Incident)
def get_incident(incident_id: int) -> dict:
    """Get a single incident by ID."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Incident not found")
        return row_to_incident(row)


@router.post("", response_model=Incident)
def create_incident(incident: IncidentCreate) -> dict:
    """Create a new incident manually."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO incidents (monitor_id, title, severity, description, started_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (incident.monitor_id, incident.title, incident.severity, incident.description, datetime.now().isoformat()),
        )
        conn.commit()
        incident_id = cursor.lastrowid

        cursor = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        row = cursor.fetchone()
        result = row_to_incident(row)

        audit_service.log_action("incident", incident_id, "create", new_value=result)

        return result


@router.put("/{incident_id}", response_model=Incident)
def update_incident(incident_id: int, incident: IncidentUpdate) -> dict:
    """Update an existing incident."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Incident not found")

        old_value = row_to_incident(existing)

        updates = []
        values = []

        for field in ["title", "status", "severity"]:
            value = getattr(incident, field)
            if value is not None:
                updates.append(f"{field} = ?")
                values.append(value)

        if updates:
            values.append(incident_id)
            conn.execute(
                f"UPDATE incidents SET {', '.join(updates)} WHERE id = ?",
                values,
            )
            conn.commit()

        cursor = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        row = cursor.fetchone()
        result = row_to_incident(row)

        audit_service.log_action("incident", incident_id, "update", old_value=old_value, new_value=result)

        return result


@router.post("/{incident_id}/acknowledge", response_model=Incident)
def acknowledge_incident(incident_id: int) -> dict:
    """Acknowledge an incident."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Incident not found")

        if existing["status"] == "resolved":
            raise HTTPException(status_code=400, detail="Cannot acknowledge resolved incident")

        old_value = row_to_incident(existing)

        conn.execute(
            """
            UPDATE incidents SET status = 'acknowledged', acknowledged_at = ?
            WHERE id = ?
            """,
            (datetime.now().isoformat(), incident_id),
        )
        conn.commit()

        cursor = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        row = cursor.fetchone()
        result = row_to_incident(row)

        audit_service.log_action("incident", incident_id, "acknowledge", old_value=old_value, new_value=result)

        return result


@router.post("/{incident_id}/resolve", response_model=Incident)
def resolve_incident(incident_id: int) -> dict:
    """Resolve an incident."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Incident not found")

        old_value = row_to_incident(existing)

        conn.execute(
            """
            UPDATE incidents SET status = 'resolved', resolved_at = ?
            WHERE id = ?
            """,
            (datetime.now().isoformat(), incident_id),
        )
        conn.commit()

        cursor = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        row = cursor.fetchone()
        result = row_to_incident(row)

        audit_service.log_action("incident", incident_id, "resolve", old_value=old_value, new_value=result)

        return result


class CreateTaskFromIncident(BaseModel):
    project_id: int
    column_id: Optional[int] = None
    use_ai_suggestion: bool = True


@router.get("/{incident_id}/suggest-task")
async def suggest_task_from_incident(
    incident_id: int,
    lang: str = Query("en", description="Response language: 'en' or 'cs'")
) -> dict:
    """Get AI-suggested task details based on incident.

    Returns suggested title, description, and priority for a follow-up task.
    """
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        incident = cursor.fetchone()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")

        # Get project_id from monitor if available
        suggested_project_id = None
        if incident["monitor_id"]:
            cursor = conn.execute(
                "SELECT project_id FROM monitors WHERE id = ?",
                (incident["monitor_id"],)
            )
            monitor = cursor.fetchone()
            if monitor:
                suggested_project_id = monitor["project_id"]

    suggestion = await ai_triage.suggest_task_from_incident(incident_id, language=lang)
    suggestion["suggested_project_id"] = suggested_project_id

    return suggestion


@router.post("/{incident_id}/create-task")
async def create_task_from_incident(
    incident_id: int,
    data: CreateTaskFromIncident,
    lang: str = Query("en", description="Response language: 'en' or 'cs'")
) -> dict:
    """Create a follow-up task from an incident.

    Optionally uses AI to generate task title and description.
    """
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        incident = cursor.fetchone()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")

        # Verify project exists
        cursor = conn.execute("SELECT id FROM projects WHERE id = ?", (data.project_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")

        # Get or determine column_id
        column_id = data.column_id
        if not column_id:
            # Use first column of the project (usually "Backlog" or "To Do")
            cursor = conn.execute(
                "SELECT id FROM columns WHERE project_id = ? ORDER BY position LIMIT 1",
                (data.project_id,)
            )
            first_col = cursor.fetchone()
            if first_col:
                column_id = first_col["id"]
            else:
                raise HTTPException(status_code=400, detail="Project has no columns")

        # Get task suggestion
        if data.use_ai_suggestion:
            suggestion = await ai_triage.suggest_task_from_incident(incident_id, language=lang)
            title = suggestion["title"]
            description = suggestion["description"]
            priority = suggestion.get("priority", "medium")
        else:
            title = f"Follow-up: {incident['title'][:50]}"
            description = f"Created from incident #{incident_id}\n\nOriginal incident: {incident['title']}"
            priority = "high" if incident["severity"] == "critical" else "medium"

        # Create the task
        cursor = conn.execute(
            """
            INSERT INTO tasks (title, description, column_id, project_id, priority, source_incident_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (title, description, column_id, data.project_id, priority, incident_id, datetime.now().isoformat()),
        )
        conn.commit()
        task_id = cursor.lastrowid

        # Get created task
        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = dict(cursor.fetchone())

        audit_service.log_action(
            "task",
            task_id,
            "create",
            new_value={**task, "source": f"incident_{incident_id}"}
        )

        return {
            "task": task,
            "incident_id": incident_id,
            "ai_generated": data.use_ai_suggestion,
            "message": "Task created successfully"
        }
