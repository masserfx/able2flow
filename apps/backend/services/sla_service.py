"""SLA (Service Level Agreement) tracking and reporting."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from database import get_db


@dataclass
class SLATarget:
    """SLA target configuration."""

    name: str
    uptime_target: float  # e.g., 99.9
    response_time_p95_ms: int  # e.g., 500
    incident_response_minutes: int  # e.g., 15
    incident_resolution_hours: int  # e.g., 4


# Default SLA targets (could be configurable per monitor)
DEFAULT_SLA = SLATarget(
    name="Standard",
    uptime_target=99.9,
    response_time_p95_ms=500,
    incident_response_minutes=15,
    incident_resolution_hours=4,
)


class SLAService:
    """Service for SLA tracking and compliance reporting."""

    def __init__(self, sla_target: SLATarget = DEFAULT_SLA):
        self.sla = sla_target

    def calculate_uptime(
        self, monitor_id: int, hours: int = 24
    ) -> dict[str, Any]:
        """Calculate uptime percentage for a monitor."""
        with get_db() as conn:
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN is_up = 1 THEN 1 ELSE 0 END) as up_count
                FROM metrics
                WHERE monitor_id = ?
                AND timestamp > datetime('now', ?)
                """,
                (monitor_id, f"-{hours} hours"),
            )
            row = cursor.fetchone()

            total = row["total"] or 0
            up_count = row["up_count"] or 0

            if total == 0:
                uptime = 100.0
            else:
                uptime = round((up_count / total) * 100, 4)

            return {
                "monitor_id": monitor_id,
                "period_hours": hours,
                "total_checks": total,
                "successful_checks": up_count,
                "failed_checks": total - up_count,
                "uptime_percentage": uptime,
                "sla_target": self.sla.uptime_target,
                "sla_met": uptime >= self.sla.uptime_target,
                "sla_breach_margin": round(uptime - self.sla.uptime_target, 4),
            }

    def calculate_response_time_percentiles(
        self, monitor_id: int, hours: int = 24
    ) -> dict[str, Any]:
        """Calculate response time percentiles (p50, p95, p99)."""
        with get_db() as conn:
            cursor = conn.execute(
                """
                SELECT response_time_ms
                FROM metrics
                WHERE monitor_id = ?
                AND timestamp > datetime('now', ?)
                AND is_up = 1
                AND response_time_ms IS NOT NULL
                ORDER BY response_time_ms
                """,
                (monitor_id, f"-{hours} hours"),
            )
            times = [row["response_time_ms"] for row in cursor.fetchall()]

            if not times:
                return {
                    "monitor_id": monitor_id,
                    "period_hours": hours,
                    "sample_count": 0,
                    "p50_ms": None,
                    "p95_ms": None,
                    "p99_ms": None,
                    "sla_target_p95_ms": self.sla.response_time_p95_ms,
                    "sla_met": None,
                }

            def percentile(data: list[int], p: float) -> int:
                idx = int(len(data) * p / 100)
                return data[min(idx, len(data) - 1)]

            p50 = percentile(times, 50)
            p95 = percentile(times, 95)
            p99 = percentile(times, 99)

            return {
                "monitor_id": monitor_id,
                "period_hours": hours,
                "sample_count": len(times),
                "min_ms": min(times),
                "max_ms": max(times),
                "avg_ms": round(sum(times) / len(times)),
                "p50_ms": p50,
                "p95_ms": p95,
                "p99_ms": p99,
                "sla_target_p95_ms": self.sla.response_time_p95_ms,
                "sla_met": p95 <= self.sla.response_time_p95_ms,
            }

    def calculate_mttr(self, hours: int = 720) -> dict[str, Any]:
        """Calculate Mean Time To Recovery (MTTR) for incidents."""
        with get_db() as conn:
            cursor = conn.execute(
                """
                SELECT
                    started_at,
                    resolved_at,
                    (julianday(resolved_at) - julianday(started_at)) * 24 * 60 as resolution_minutes
                FROM incidents
                WHERE status = 'resolved'
                AND resolved_at IS NOT NULL
                AND started_at > datetime('now', ?)
                """,
                (f"-{hours} hours",),
            )
            incidents = cursor.fetchall()

            if not incidents:
                return {
                    "period_hours": hours,
                    "resolved_incidents": 0,
                    "mttr_minutes": None,
                    "sla_target_hours": self.sla.incident_resolution_hours,
                    "sla_met": None,
                }

            resolution_times = [row["resolution_minutes"] for row in incidents]
            mttr = sum(resolution_times) / len(resolution_times)

            breaches = sum(
                1
                for t in resolution_times
                if t > self.sla.incident_resolution_hours * 60
            )

            return {
                "period_hours": hours,
                "resolved_incidents": len(incidents),
                "mttr_minutes": round(mttr, 1),
                "mttr_hours": round(mttr / 60, 2),
                "min_resolution_minutes": round(min(resolution_times), 1),
                "max_resolution_minutes": round(max(resolution_times), 1),
                "sla_target_hours": self.sla.incident_resolution_hours,
                "sla_breaches": breaches,
                "sla_met": breaches == 0,
            }

    def calculate_mtta(self, hours: int = 720) -> dict[str, Any]:
        """Calculate Mean Time To Acknowledge (MTTA) for incidents."""
        with get_db() as conn:
            cursor = conn.execute(
                """
                SELECT
                    started_at,
                    acknowledged_at,
                    (julianday(acknowledged_at) - julianday(started_at)) * 24 * 60 as ack_minutes
                FROM incidents
                WHERE acknowledged_at IS NOT NULL
                AND started_at > datetime('now', ?)
                """,
                (f"-{hours} hours",),
            )
            incidents = cursor.fetchall()

            if not incidents:
                return {
                    "period_hours": hours,
                    "acknowledged_incidents": 0,
                    "mtta_minutes": None,
                    "sla_target_minutes": self.sla.incident_response_minutes,
                    "sla_met": None,
                }

            ack_times = [row["ack_minutes"] for row in incidents]
            mtta = sum(ack_times) / len(ack_times)

            breaches = sum(
                1 for t in ack_times if t > self.sla.incident_response_minutes
            )

            return {
                "period_hours": hours,
                "acknowledged_incidents": len(incidents),
                "mtta_minutes": round(mtta, 1),
                "min_ack_minutes": round(min(ack_times), 1),
                "max_ack_minutes": round(max(ack_times), 1),
                "sla_target_minutes": self.sla.incident_response_minutes,
                "sla_breaches": breaches,
                "sla_met": breaches == 0,
            }

    def generate_sla_report(
        self, monitor_id: int | None = None, hours: int = 720
    ) -> dict[str, Any]:
        """Generate comprehensive SLA compliance report."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "period_hours": hours,
            "period_days": hours // 24,
            "sla_target": {
                "name": self.sla.name,
                "uptime": f"{self.sla.uptime_target}%",
                "response_time_p95": f"{self.sla.response_time_p95_ms}ms",
                "incident_response": f"{self.sla.incident_response_minutes}min",
                "incident_resolution": f"{self.sla.incident_resolution_hours}h",
            },
            "incident_metrics": {
                "mtta": self.calculate_mtta(hours),
                "mttr": self.calculate_mttr(hours),
            },
        }

        if monitor_id:
            report["monitors"] = [
                {
                    "uptime": self.calculate_uptime(monitor_id, hours),
                    "response_time": self.calculate_response_time_percentiles(
                        monitor_id, hours
                    ),
                }
            ]
        else:
            # All monitors
            with get_db() as conn:
                cursor = conn.execute("SELECT id, name FROM monitors")
                monitors = cursor.fetchall()

            report["monitors"] = [
                {
                    "id": m["id"],
                    "name": m["name"],
                    "uptime": self.calculate_uptime(m["id"], hours),
                    "response_time": self.calculate_response_time_percentiles(
                        m["id"], hours
                    ),
                }
                for m in monitors
            ]

        # Calculate overall SLA compliance
        all_met = True
        for m in report["monitors"]:
            if not m["uptime"].get("sla_met", True):
                all_met = False
            if m["response_time"].get("sla_met") is False:
                all_met = False

        if report["incident_metrics"]["mtta"].get("sla_met") is False:
            all_met = False
        if report["incident_metrics"]["mttr"].get("sla_met") is False:
            all_met = False

        report["overall_sla_compliance"] = all_met

        return report


# Global instance
sla_service = SLAService()
