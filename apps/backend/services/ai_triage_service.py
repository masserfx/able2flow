"""AI-powered incident triage using Claude API."""

import os
from datetime import datetime
from typing import Any

import httpx

from database import get_db


class AITriageService:
    """Service for AI-powered incident analysis and recommendations."""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = "claude-3-haiku-20240307"  # Fast & cheap for triage
        self.base_url = "https://api.anthropic.com/v1/messages"

    async def analyze_incident(self, incident_id: int) -> dict[str, Any]:
        """Analyze incident and provide AI recommendations.

        Returns:
            - severity_suggestion: Recommended severity level
            - root_cause_hypothesis: Possible root causes
            - recommended_actions: Step-by-step remediation
            - similar_incidents: Related past incidents
            - estimated_impact: Business impact assessment
        """
        # Gather context
        context = await self._gather_incident_context(incident_id)

        if not self.api_key:
            return self._fallback_analysis(context)

        prompt = self._build_analysis_prompt(context)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 1024,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()
                return self._parse_ai_response(result, context)
        except Exception as e:
            return {
                "error": str(e),
                "fallback": True,
                **self._fallback_analysis(context),
            }

    async def _gather_incident_context(self, incident_id: int) -> dict[str, Any]:
        """Gather all relevant context for incident analysis."""
        with get_db() as conn:
            # Get incident details
            cursor = conn.execute(
                "SELECT * FROM incidents WHERE id = ?", (incident_id,)
            )
            incident = dict(cursor.fetchone())

            # Get monitor info if linked
            monitor = None
            if incident.get("monitor_id"):
                cursor = conn.execute(
                    "SELECT * FROM monitors WHERE id = ?",
                    (incident["monitor_id"],),
                )
                row = cursor.fetchone()
                if row:
                    monitor = dict(row)

            # Get recent metrics for the monitor
            metrics = []
            if monitor:
                cursor = conn.execute(
                    """
                    SELECT * FROM metrics
                    WHERE monitor_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 10
                    """,
                    (monitor["id"],),
                )
                metrics = [dict(row) for row in cursor.fetchall()]

            # Get similar past incidents
            cursor = conn.execute(
                """
                SELECT * FROM incidents
                WHERE id != ? AND status = 'resolved'
                ORDER BY started_at DESC
                LIMIT 5
                """,
                (incident_id,),
            )
            past_incidents = [dict(row) for row in cursor.fetchall()]

            # Get recent audit log
            cursor = conn.execute(
                """
                SELECT * FROM audit_log
                WHERE timestamp > datetime('now', '-1 hour')
                ORDER BY timestamp DESC
                LIMIT 20
                """,
            )
            recent_changes = [dict(row) for row in cursor.fetchall()]

        return {
            "incident": incident,
            "monitor": monitor,
            "recent_metrics": metrics,
            "past_incidents": past_incidents,
            "recent_changes": recent_changes,
        }

    def _build_analysis_prompt(self, context: dict[str, Any]) -> str:
        """Build prompt for AI analysis."""
        incident = context["incident"]
        monitor = context.get("monitor")
        metrics = context.get("recent_metrics", [])

        prompt = f"""You are an expert SRE analyzing an incident. Provide actionable insights.

INCIDENT:
- Title: {incident['title']}
- Severity: {incident['severity']}
- Status: {incident['status']}
- Started: {incident['started_at']}

"""
        if monitor:
            prompt += f"""AFFECTED SERVICE:
- Name: {monitor['name']}
- URL: {monitor['url']}
- Last Status: {monitor['last_status']}

"""

        if metrics:
            prompt += "RECENT METRICS:\n"
            for m in metrics[:5]:
                status = "UP" if m.get("is_up") else "DOWN"
                prompt += f"- {m['timestamp']}: {status}, {m.get('response_time_ms', 'N/A')}ms, HTTP {m.get('status_code', 'N/A')}\n"
            prompt += "\n"

        prompt += """Analyze this incident and respond in JSON format:
{
    "severity_suggestion": "critical|warning|info",
    "confidence": 0.0-1.0,
    "root_cause_hypothesis": ["possible cause 1", "possible cause 2"],
    "recommended_actions": ["action 1", "action 2", "action 3"],
    "estimated_impact": "description of business impact",
    "runbook_suggestion": "link or name of relevant runbook if known"
}

Be concise and actionable."""

        return prompt

    def _parse_ai_response(
        self, response: dict, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Parse AI response and enrich with metadata."""
        import json

        try:
            content = response["content"][0]["text"]
            # Try to extract JSON from response
            if "{" in content and "}" in content:
                json_start = content.index("{")
                json_end = content.rindex("}") + 1
                analysis = json.loads(content[json_start:json_end])
            else:
                analysis = {"raw_response": content}
        except (json.JSONDecodeError, KeyError, IndexError):
            analysis = {"raw_response": response}

        return {
            "ai_powered": True,
            "model": self.model,
            "analyzed_at": datetime.now().isoformat(),
            "incident_id": context["incident"]["id"],
            **analysis,
        }

    def _fallback_analysis(self, context: dict[str, Any]) -> dict[str, Any]:
        """Rule-based fallback when AI is unavailable."""
        incident = context["incident"]
        metrics = context.get("recent_metrics", [])

        # Simple heuristics
        severity = incident.get("severity", "warning")
        actions = ["Check service logs", "Verify network connectivity"]

        if metrics:
            down_count = sum(1 for m in metrics if not m.get("is_up"))
            if down_count > 3:
                severity = "critical"
                actions.insert(0, "Service has multiple failures - escalate immediately")

        return {
            "ai_powered": False,
            "severity_suggestion": severity,
            "confidence": 0.5,
            "root_cause_hypothesis": [
                "Service unreachable",
                "Network issues",
                "Resource exhaustion",
            ],
            "recommended_actions": actions,
            "estimated_impact": "Unknown - manual assessment required",
            "analyzed_at": datetime.now().isoformat(),
            "incident_id": incident["id"],
        }

    async def suggest_runbook(self, incident_id: int) -> dict[str, Any]:
        """Suggest or generate a runbook for the incident type."""
        context = await self._gather_incident_context(incident_id)
        incident = context["incident"]

        # Pre-defined runbooks based on incident patterns
        runbooks = {
            "timeout": {
                "name": "Service Timeout Runbook",
                "steps": [
                    "1. Check service health endpoint directly",
                    "2. Review recent deployments in audit log",
                    "3. Check resource utilization (CPU, memory)",
                    "4. Review application logs for errors",
                    "5. If persists > 5min, restart service",
                    "6. If restart fails, rollback last deployment",
                ],
            },
            "connection": {
                "name": "Connection Failure Runbook",
                "steps": [
                    "1. Verify DNS resolution",
                    "2. Check firewall rules",
                    "3. Test network path with traceroute",
                    "4. Verify SSL certificate validity",
                    "5. Check load balancer health",
                ],
            },
            "default": {
                "name": "General Incident Runbook",
                "steps": [
                    "1. Acknowledge incident",
                    "2. Assess impact scope",
                    "3. Check monitoring dashboard",
                    "4. Review recent changes in audit log",
                    "5. Engage relevant team if needed",
                    "6. Document findings",
                ],
            },
        }

        title_lower = incident["title"].lower()
        if "timeout" in title_lower:
            runbook = runbooks["timeout"]
        elif "connection" in title_lower or "refused" in title_lower:
            runbook = runbooks["connection"]
        else:
            runbook = runbooks["default"]

        return {
            "incident_id": incident_id,
            "suggested_runbook": runbook,
            "auto_generated": True,
        }


# Global instance
ai_triage = AITriageService()
