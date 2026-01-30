"""Monitoring service for health checks and incident management."""

import asyncio
from datetime import datetime
from typing import Any

import httpx

from database import get_db
from services import audit_service


class MonitorService:
    """Service for running health checks and managing incidents."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self._running = False
        self._task: asyncio.Task | None = None

    async def check_monitor(self, monitor_id: int) -> dict[str, Any]:
        """Run a health check for a single monitor.

        Args:
            monitor_id: ID of the monitor to check

        Returns:
            Dict with check results
        """
        with get_db() as conn:
            cursor = conn.execute(
                "SELECT * FROM monitors WHERE id = ?", (monitor_id,)
            )
            monitor = cursor.fetchone()
            if not monitor:
                raise ValueError(f"Monitor {monitor_id} not found")

            url = monitor["url"]
            name = monitor["name"]

        start_time = datetime.now()
        is_up = False
        status_code = 0
        response_time_ms = 0
        error_message = None

        try:
            response = await self.client.get(url)
            status_code = response.status_code
            is_up = 200 <= status_code < 400
            response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        except httpx.TimeoutException:
            error_message = "Timeout"
        except httpx.ConnectError:
            error_message = "Connection failed"
        except Exception as e:
            error_message = str(e)

        # Save metrics
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO metrics (monitor_id, response_time_ms, status_code, is_up, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (monitor_id, response_time_ms, status_code, int(is_up), datetime.now().isoformat()),
            )

            # Update monitor status
            new_status = "up" if is_up else "down"
            conn.execute(
                """
                UPDATE monitors SET last_status = ?, last_check = ?
                WHERE id = ?
                """,
                (new_status, datetime.now().isoformat(), monitor_id),
            )
            conn.commit()

        # Handle incidents
        await self._handle_incident(monitor_id, name, is_up, error_message)

        return {
            "monitor_id": monitor_id,
            "is_up": is_up,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "error": error_message,
            "checked_at": datetime.now().isoformat(),
        }

    async def _handle_incident(
        self, monitor_id: int, name: str, is_up: bool, error_message: str | None
    ) -> None:
        """Create or resolve incidents based on check results."""
        with get_db() as conn:
            # Check for open incident
            cursor = conn.execute(
                """
                SELECT * FROM incidents
                WHERE monitor_id = ? AND status != 'resolved'
                ORDER BY started_at DESC LIMIT 1
                """,
                (monitor_id,),
            )
            open_incident = cursor.fetchone()

            if not is_up and not open_incident:
                # Create new incident
                title = f"{name} is down"
                if error_message:
                    title += f": {error_message}"

                cursor = conn.execute(
                    """
                    INSERT INTO incidents (monitor_id, title, status, severity, started_at)
                    VALUES (?, ?, 'open', 'critical', ?)
                    """,
                    (monitor_id, title, datetime.now().isoformat()),
                )
                conn.commit()
                incident_id = cursor.lastrowid

                audit_service.log_action(
                    "incident",
                    incident_id,
                    "create",
                    new_value={"monitor_id": monitor_id, "title": title, "status": "open"},
                )

            elif is_up and open_incident:
                # Resolve existing incident
                conn.execute(
                    """
                    UPDATE incidents SET status = 'resolved', resolved_at = ?
                    WHERE id = ?
                    """,
                    (datetime.now().isoformat(), open_incident["id"]),
                )
                conn.commit()

                audit_service.log_action(
                    "incident",
                    open_incident["id"],
                    "resolve",
                    old_value={"status": open_incident["status"]},
                    new_value={"status": "resolved"},
                )

    async def check_all_monitors(self) -> list[dict[str, Any]]:
        """Run health checks for all monitors.

        Returns:
            List of check results
        """
        with get_db() as conn:
            cursor = conn.execute("SELECT id FROM monitors")
            monitor_ids = [row["id"] for row in cursor.fetchall()]

        results = []
        for monitor_id in monitor_ids:
            try:
                result = await self.check_monitor(monitor_id)
                results.append(result)
            except Exception as e:
                results.append({"monitor_id": monitor_id, "error": str(e)})

        return results

    async def start_background_checks(self) -> None:
        """Start background health check loop."""
        self._running = True
        while self._running:
            await self.check_all_monitors()
            await asyncio.sleep(30)  # Check every 30 seconds

    def stop_background_checks(self) -> None:
        """Stop background health check loop."""
        self._running = False
        if self._task:
            self._task.cancel()

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()


# Global instance
monitor_service = MonitorService()


def get_monitor_stats(project_id: int | None = None) -> dict[str, Any]:
    """Get monitoring statistics, optionally filtered by project."""
    with get_db() as conn:
        # Build project filter
        project_filter = ""
        project_params: tuple = ()
        if project_id is not None:
            project_filter = " WHERE project_id = ?"
            project_params = (project_id,)

        # Total monitors
        cursor = conn.execute(f"SELECT COUNT(*) as total FROM monitors{project_filter}", project_params)
        total_monitors = cursor.fetchone()["total"]

        # Monitors by status
        cursor = conn.execute(
            f"""
            SELECT last_status, COUNT(*) as count
            FROM monitors
            {project_filter}
            GROUP BY last_status
            """,
            project_params,
        )
        by_status = {row["last_status"]: row["count"] for row in cursor.fetchall()}

        # Open incidents
        if project_id is not None:
            cursor = conn.execute(
                """
                SELECT COUNT(*) as count
                FROM incidents
                WHERE status != 'resolved' AND project_id = ?
                """,
                (project_id,),
            )
        else:
            cursor = conn.execute(
                """
                SELECT COUNT(*) as count
                FROM incidents
                WHERE status != 'resolved'
                """
            )
        open_incidents = cursor.fetchone()["count"]

        # Average response time (last hour) - filter by monitors in project
        if project_id is not None:
            cursor = conn.execute(
                """
                SELECT AVG(m.response_time_ms) as avg_time
                FROM metrics m
                JOIN monitors mon ON m.monitor_id = mon.id
                WHERE m.timestamp > datetime('now', '-1 hour') AND m.is_up = 1 AND mon.project_id = ?
                """,
                (project_id,),
            )
        else:
            cursor = conn.execute(
                """
                SELECT AVG(response_time_ms) as avg_time
                FROM metrics
                WHERE timestamp > datetime('now', '-1 hour') AND is_up = 1
                """
            )
        row = cursor.fetchone()
        avg_response_time = round(row["avg_time"]) if row["avg_time"] else 0

        # Uptime percentage (last 24h)
        if project_id is not None:
            cursor = conn.execute(
                """
                SELECT
                    SUM(CASE WHEN m.is_up = 1 THEN 1 ELSE 0 END) as up_count,
                    COUNT(*) as total
                FROM metrics m
                JOIN monitors mon ON m.monitor_id = mon.id
                WHERE m.timestamp > datetime('now', '-24 hours') AND mon.project_id = ?
                """,
                (project_id,),
            )
        else:
            cursor = conn.execute(
                """
                SELECT
                    SUM(CASE WHEN is_up = 1 THEN 1 ELSE 0 END) as up_count,
                    COUNT(*) as total
                FROM metrics
                WHERE timestamp > datetime('now', '-24 hours')
                """
            )
        row = cursor.fetchone()
        uptime = round((row["up_count"] / row["total"]) * 100, 2) if row["total"] > 0 else 100

        return {
            "total_monitors": total_monitors,
            "by_status": by_status,
            "open_incidents": open_incidents,
            "avg_response_time_ms": avg_response_time,
            "uptime_24h": uptime,
        }
