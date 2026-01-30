"""AI-powered features router."""

from fastapi import APIRouter, HTTPException, Query

from database import get_db
from services.ai_triage_service import ai_triage
from services import audit_service

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/incidents/{incident_id}/analyze")
async def analyze_incident(
    incident_id: int,
    lang: str = Query("en", description="Response language: 'en' or 'cs'")
) -> dict:
    """AI-powered incident analysis.

    Returns severity suggestion, root cause hypothesis,
    recommended actions, and impact assessment.

    Query params:
        lang: Response language ('en' for English, 'cs' for Czech)
    """
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM incidents WHERE id = ?", (incident_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Incident not found")

    analysis = await ai_triage.analyze_incident(incident_id, language=lang)

    # Log AI analysis action
    audit_service.log_action(
        "incident",
        incident_id,
        "ai_analyze",
        new_value={"analysis_result": analysis.get("severity_suggestion")},
    )

    return analysis


@router.get("/incidents/{incident_id}/runbook")
async def get_runbook_suggestion(incident_id: int) -> dict:
    """Get suggested runbook for incident type."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM incidents WHERE id = ?", (incident_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Incident not found")

    return await ai_triage.suggest_runbook(incident_id)


@router.post("/incidents/{incident_id}/auto-triage")
async def auto_triage_incident(
    incident_id: int,
    lang: str = Query("en", description="Response language: 'en' or 'cs'")
) -> dict:
    """Automatically triage incident using AI.

    Analyzes incident, suggests severity, and optionally
    updates incident with AI recommendations.

    Query params:
        lang: Response language ('en' for English, 'cs' for Czech)
    """
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM incidents WHERE id = ?", (incident_id,)
        )
        incident = cursor.fetchone()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")

        old_value = dict(incident)

    # Get AI analysis
    analysis = await ai_triage.analyze_incident(incident_id, language=lang)
    runbook = await ai_triage.suggest_runbook(incident_id)

    # Auto-update severity if AI is confident
    updated = False
    if analysis.get("confidence", 0) >= 0.8:
        suggested_severity = analysis.get("severity_suggestion")
        if suggested_severity and suggested_severity != incident["severity"]:
            with get_db() as conn:
                conn.execute(
                    "UPDATE incidents SET severity = ? WHERE id = ?",
                    (suggested_severity, incident_id),
                )
                conn.commit()
                updated = True

                audit_service.log_action(
                    "incident",
                    incident_id,
                    "ai_auto_triage",
                    old_value=old_value,
                    new_value={"severity": suggested_severity},
                )

    return {
        "incident_id": incident_id,
        "analysis": analysis,
        "runbook": runbook,
        "auto_updated": updated,
        "message": "Severity updated by AI" if updated else "Analysis complete",
    }
