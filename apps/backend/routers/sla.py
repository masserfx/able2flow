"""SLA reporting router."""

from fastapi import APIRouter, HTTPException

from database import get_db
from services.sla_service import sla_service

router = APIRouter(prefix="/api/sla", tags=["sla"])


@router.get("/report")
def get_sla_report(hours: int = 720) -> dict:
    """Get comprehensive SLA compliance report.

    Args:
        hours: Period to analyze (default 720 = 30 days)

    Returns:
        Complete SLA report with uptime, response times, MTTA, MTTR
    """
    return sla_service.generate_sla_report(hours=hours)


@router.get("/monitors/{monitor_id}/uptime")
def get_monitor_uptime(monitor_id: int, hours: int = 24) -> dict:
    """Get uptime statistics for a specific monitor."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM monitors WHERE id = ?", (monitor_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Monitor not found")

    return sla_service.calculate_uptime(monitor_id, hours)


@router.get("/monitors/{monitor_id}/response-times")
def get_response_time_percentiles(monitor_id: int, hours: int = 24) -> dict:
    """Get response time percentiles for a specific monitor."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM monitors WHERE id = ?", (monitor_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Monitor not found")

    return sla_service.calculate_response_time_percentiles(monitor_id, hours)


@router.get("/incidents/mtta")
def get_mtta(hours: int = 720) -> dict:
    """Get Mean Time To Acknowledge (MTTA) statistics."""
    return sla_service.calculate_mtta(hours)


@router.get("/incidents/mttr")
def get_mttr(hours: int = 720) -> dict:
    """Get Mean Time To Recovery (MTTR) statistics."""
    return sla_service.calculate_mttr(hours)


@router.get("/health-score")
def get_health_score() -> dict:
    """Get overall system health score (0-100).

    Combines multiple metrics into a single score.
    """
    # Get SLA data
    report = sla_service.generate_sla_report(hours=24)

    score = 100
    issues = []

    # Uptime impact (max -40 points)
    for m in report["monitors"]:
        uptime = m["uptime"]["uptime_percentage"]
        if uptime < 99.9:
            penalty = min(40, (99.9 - uptime) * 10)
            score -= penalty
            issues.append(f"{m.get('name', 'Monitor')} uptime: {uptime}%")

    # Response time impact (max -20 points)
    for m in report["monitors"]:
        p95 = m["response_time"].get("p95_ms")
        if p95 and p95 > 500:
            penalty = min(20, (p95 - 500) / 100)
            score -= penalty
            issues.append(f"High p95 response time: {p95}ms")

    # MTTA impact (max -20 points)
    mtta = report["incident_metrics"]["mtta"].get("mtta_minutes")
    if mtta and mtta > 15:
        penalty = min(20, (mtta - 15) / 5)
        score -= penalty
        issues.append(f"High MTTA: {mtta:.1f}min")

    # MTTR impact (max -20 points)
    mttr_hours = report["incident_metrics"]["mttr"].get("mttr_hours")
    if mttr_hours and mttr_hours > 4:
        penalty = min(20, (mttr_hours - 4) * 5)
        score -= penalty
        issues.append(f"High MTTR: {mttr_hours:.1f}h")

    score = max(0, round(score))

    if score >= 90:
        status = "excellent"
        color = "green"
    elif score >= 70:
        status = "good"
        color = "yellow"
    elif score >= 50:
        status = "degraded"
        color = "orange"
    else:
        status = "critical"
        color = "red"

    return {
        "score": score,
        "status": status,
        "color": color,
        "issues": issues,
        "period": "24h",
    }
