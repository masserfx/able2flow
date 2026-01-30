"""Tests for advanced features: SLA, Events, AI."""

import pytest


class TestSLAAPI:
    """Test suite for /api/sla endpoints."""

    def test_sla_report(self, client):
        """Test SLA report generation."""
        response = client.get("/api/sla/report?hours=24")
        assert response.status_code == 200

        data = response.json()
        assert "sla_target" in data
        assert "monitors" in data
        assert "incident_metrics" in data
        assert "overall_sla_compliance" in data

    def test_health_score(self, client):
        """Test health score calculation."""
        response = client.get("/api/sla/health-score")
        assert response.status_code == 200

        data = response.json()
        assert "score" in data
        assert "status" in data
        assert 0 <= data["score"] <= 100
        assert data["status"] in ["excellent", "good", "degraded", "critical"]

    def test_mtta_calculation(self, client):
        """Test MTTA (Mean Time To Acknowledge) endpoint."""
        response = client.get("/api/sla/incidents/mtta")
        assert response.status_code == 200

        data = response.json()
        assert "period_hours" in data
        assert "sla_target_minutes" in data

    def test_mttr_calculation(self, client):
        """Test MTTR (Mean Time To Recovery) endpoint."""
        response = client.get("/api/sla/incidents/mttr")
        assert response.status_code == 200

        data = response.json()
        assert "period_hours" in data
        assert "sla_target_hours" in data


class TestEventsAPI:
    """Test suite for /api/events endpoints."""

    def test_activity_feed(self, client):
        """Test activity feed."""
        # Create some activity
        client.post("/api/tasks", json={"title": "Feed Test"})

        response = client.get("/api/events/feed")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        if data:
            assert "entity_type" in data[0]
            assert "action" in data[0]
            assert "summary" in data[0]

    def test_entity_history(self, client):
        """Test entity history retrieval."""
        # Create and update a task
        create_resp = client.post("/api/tasks", json={"title": "History Test"})
        task_id = create_resp.json()["id"]
        client.put(f"/api/tasks/{task_id}", json={"title": "Updated"})

        response = client.get(f"/api/events/task/{task_id}/history")
        assert response.status_code == 200

        data = response.json()
        assert data["entity_type"] == "task"
        assert data["entity_id"] == task_id
        assert data["event_count"] >= 2  # create + update

    def test_time_travel_state_at(self, client):
        """Test time-travel state reconstruction."""
        # Create a task
        create_resp = client.post("/api/tasks", json={"title": "Time Travel"})
        task_id = create_resp.json()["id"]

        # Get history to find timestamp
        history = client.get(f"/api/events/task/{task_id}/history").json()
        timestamp = history["events"][0]["timestamp"]

        # Time travel
        response = client.get(
            f"/api/events/task/{task_id}/state-at",
            params={"timestamp": timestamp}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["state"]["title"] == "Time Travel"

    def test_event_replay(self, client):
        """Test event replay functionality."""
        # Create and modify task
        create_resp = client.post("/api/tasks", json={"title": "Replay Test"})
        task_id = create_resp.json()["id"]
        client.put(f"/api/tasks/{task_id}", json={"title": "Replayed"})

        response = client.get(f"/api/events/task/{task_id}/replay")
        assert response.status_code == 200

        data = response.json()
        assert data["replayed_events"] >= 2
        assert data["final_state"]["title"] == "Replayed"


class TestAIAPI:
    """Test suite for /api/ai endpoints."""

    def test_runbook_suggestion(self, client):
        """Test runbook suggestion for incidents."""
        # Create incident
        create_resp = client.post("/api/incidents", json={
            "title": "Connection timeout error",
            "severity": "critical"
        })
        incident_id = create_resp.json()["id"]

        response = client.get(f"/api/ai/incidents/{incident_id}/runbook")
        assert response.status_code == 200

        data = response.json()
        assert "suggested_runbook" in data
        assert "steps" in data["suggested_runbook"]

    def test_incident_analysis_fallback(self, client):
        """Test incident analysis with fallback (no API key)."""
        # Create incident
        create_resp = client.post("/api/incidents", json={
            "title": "Test incident",
            "severity": "warning"
        })
        incident_id = create_resp.json()["id"]

        response = client.post(f"/api/ai/incidents/{incident_id}/analyze")
        assert response.status_code == 200

        data = response.json()
        # Should return fallback analysis
        assert "severity_suggestion" in data
        assert "recommended_actions" in data

    def test_auto_triage(self, client):
        """Test auto-triage endpoint."""
        # Create incident
        create_resp = client.post("/api/incidents", json={
            "title": "Auto triage test",
            "severity": "warning"
        })
        incident_id = create_resp.json()["id"]

        response = client.post(f"/api/ai/incidents/{incident_id}/auto-triage")
        assert response.status_code == 200

        data = response.json()
        assert "analysis" in data
        assert "runbook" in data
        assert "auto_updated" in data
