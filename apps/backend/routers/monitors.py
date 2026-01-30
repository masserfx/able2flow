"""Monitors router for health checks."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import get_db
from services import audit_service
from services.monitor_service import monitor_service

router = APIRouter(prefix="/api/monitors", tags=["monitors"])


class MonitorCreate(BaseModel):
    name: str
    url: str
    check_interval: int = 60


class MonitorUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    check_interval: int | None = None


class Monitor(BaseModel):
    id: int
    name: str
    url: str
    check_interval: int
    last_status: str
    last_check: str | None
    created_at: str


def row_to_monitor(row) -> dict:
    """Convert database row to monitor dict."""
    return {
        "id": row["id"],
        "name": row["name"],
        "url": row["url"],
        "check_interval": row["check_interval"],
        "last_status": row["last_status"],
        "last_check": row["last_check"],
        "created_at": row["created_at"],
    }


@router.get("", response_model=list[Monitor])
def list_monitors() -> list[dict]:
    """Get all monitors."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM monitors ORDER BY name")
        return [row_to_monitor(row) for row in cursor.fetchall()]


@router.get("/{monitor_id}", response_model=Monitor)
def get_monitor(monitor_id: int) -> dict:
    """Get a single monitor by ID."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM monitors WHERE id = ?", (monitor_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Monitor not found")
        return row_to_monitor(row)


@router.post("", response_model=Monitor)
def create_monitor(monitor: MonitorCreate) -> dict:
    """Create a new monitor."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO monitors (name, url, check_interval)
            VALUES (?, ?, ?)
            """,
            (monitor.name, monitor.url, monitor.check_interval),
        )
        conn.commit()
        monitor_id = cursor.lastrowid

        cursor = conn.execute("SELECT * FROM monitors WHERE id = ?", (monitor_id,))
        row = cursor.fetchone()
        result = row_to_monitor(row)

        audit_service.log_action("monitor", monitor_id, "create", new_value=result)

        return result


@router.put("/{monitor_id}", response_model=Monitor)
def update_monitor(monitor_id: int, monitor: MonitorUpdate) -> dict:
    """Update an existing monitor."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM monitors WHERE id = ?", (monitor_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Monitor not found")

        old_value = row_to_monitor(existing)

        updates = []
        values = []

        for field in ["name", "url", "check_interval"]:
            value = getattr(monitor, field)
            if value is not None:
                updates.append(f"{field} = ?")
                values.append(value)

        if updates:
            values.append(monitor_id)
            conn.execute(
                f"UPDATE monitors SET {', '.join(updates)} WHERE id = ?",
                values,
            )
            conn.commit()

        cursor = conn.execute("SELECT * FROM monitors WHERE id = ?", (monitor_id,))
        row = cursor.fetchone()
        result = row_to_monitor(row)

        audit_service.log_action("monitor", monitor_id, "update", old_value=old_value, new_value=result)

        return result


@router.delete("/{monitor_id}")
def delete_monitor(monitor_id: int) -> dict:
    """Delete a monitor."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM monitors WHERE id = ?", (monitor_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Monitor not found")

        old_value = row_to_monitor(existing)

        conn.execute("DELETE FROM metrics WHERE monitor_id = ?", (monitor_id,))
        conn.execute("DELETE FROM incidents WHERE monitor_id = ?", (monitor_id,))
        conn.execute("DELETE FROM monitors WHERE id = ?", (monitor_id,))
        conn.commit()

        audit_service.log_action("monitor", monitor_id, "delete", old_value=old_value)

        return {"message": "Monitor deleted"}


@router.post("/{monitor_id}/check")
async def check_monitor(monitor_id: int) -> dict:
    """Run a health check for a monitor immediately."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM monitors WHERE id = ?", (monitor_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Monitor not found")

    result = await monitor_service.check_monitor(monitor_id)
    return result


@router.get("/{monitor_id}/metrics")
def get_monitor_metrics(monitor_id: int, limit: int = 100) -> list[dict]:
    """Get metrics for a monitor."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM monitors WHERE id = ?", (monitor_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Monitor not found")

        cursor = conn.execute(
            """
            SELECT * FROM metrics
            WHERE monitor_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (monitor_id, limit),
        )
        return [
            {
                "id": row["id"],
                "monitor_id": row["monitor_id"],
                "response_time_ms": row["response_time_ms"],
                "status_code": row["status_code"],
                "is_up": bool(row["is_up"]),
                "timestamp": row["timestamp"],
            }
            for row in cursor.fetchall()
        ]
