"""Incidents router for incident management."""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import get_db
from services import audit_service

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


class IncidentCreate(BaseModel):
    monitor_id: int | None = None
    title: str
    severity: str = "warning"
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
        "started_at": row["started_at"],
        "acknowledged_at": row["acknowledged_at"],
        "resolved_at": row["resolved_at"],
    }


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
            INSERT INTO incidents (monitor_id, title, severity, started_at)
            VALUES (?, ?, ?, ?)
            """,
            (incident.monitor_id, incident.title, incident.severity, datetime.now().isoformat()),
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
