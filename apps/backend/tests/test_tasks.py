"""Tests for tasks API."""

import pytest


class TestTasksAPI:
    """Test suite for /api/tasks endpoints."""

    def test_list_tasks_empty(self, client):
        """Test listing tasks when database is empty."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        """Test creating a new task."""
        task_data = {
            "title": "Test Task",
            "description": "Test description",
            "column_id": 1,
            "priority": "high"
        }
        response = client.post("/api/tasks", json=task_data)
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == "Test Task"
        assert data["description"] == "Test description"
        assert data["column_id"] == 1
        assert data["priority"] == "high"
        assert data["completed"] is False
        assert "id" in data

    def test_get_task(self, client):
        """Test getting a single task."""
        # Create task first
        create_response = client.post("/api/tasks", json={"title": "Get Test"})
        task_id = create_response.json()["id"]

        # Get task
        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Get Test"

    def test_get_task_not_found(self, client):
        """Test getting non-existent task."""
        response = client.get("/api/tasks/9999")
        assert response.status_code == 404

    def test_update_task(self, client):
        """Test updating a task."""
        # Create task
        create_response = client.post("/api/tasks", json={"title": "Original"})
        task_id = create_response.json()["id"]

        # Update task
        response = client.put(f"/api/tasks/{task_id}", json={
            "title": "Updated",
            "completed": True
        })
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == "Updated"
        assert data["completed"] is True

    def test_delete_task(self, client):
        """Test deleting a task."""
        # Create task
        create_response = client.post("/api/tasks", json={"title": "To Delete"})
        task_id = create_response.json()["id"]

        # Delete task
        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200

        # Verify deleted
        get_response = client.get(f"/api/tasks/{task_id}")
        assert get_response.status_code == 404

    def test_move_task(self, client):
        """Test moving a task between columns."""
        # Create task in column 1
        create_response = client.post("/api/tasks", json={
            "title": "Movable Task",
            "column_id": 1
        })
        task_id = create_response.json()["id"]

        # Move to column 2
        response = client.put(f"/api/tasks/{task_id}/move", json={
            "column_id": 2,
            "position": 0
        })
        assert response.status_code == 200
        assert response.json()["column_id"] == 2
        assert response.json()["position"] == 0


class TestColumnsAPI:
    """Test suite for /api/columns endpoints."""

    def test_list_columns(self, client):
        """Test listing columns."""
        response = client.get("/api/columns")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 3  # Pre-seeded columns
        assert data[0]["name"] == "To Do"

    def test_create_column(self, client):
        """Test creating a new column."""
        response = client.post("/api/columns", json={
            "name": "Review",
            "color": "#8b5cf6"
        })
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Review"
        assert data["color"] == "#8b5cf6"


class TestIncidentsAPI:
    """Test suite for /api/incidents endpoints."""

    def test_create_incident(self, client):
        """Test creating an incident."""
        response = client.post("/api/incidents", json={
            "title": "Server down",
            "severity": "critical"
        })
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == "Server down"
        assert data["severity"] == "critical"
        assert data["status"] == "open"

    def test_acknowledge_incident(self, client):
        """Test acknowledging an incident."""
        # Create incident
        create_response = client.post("/api/incidents", json={
            "title": "Test incident"
        })
        incident_id = create_response.json()["id"]

        # Acknowledge
        response = client.post(f"/api/incidents/{incident_id}/acknowledge")
        assert response.status_code == 200
        assert response.json()["status"] == "acknowledged"
        assert response.json()["acknowledged_at"] is not None

    def test_resolve_incident(self, client):
        """Test resolving an incident."""
        # Create incident
        create_response = client.post("/api/incidents", json={
            "title": "Test incident"
        })
        incident_id = create_response.json()["id"]

        # Resolve
        response = client.post(f"/api/incidents/{incident_id}/resolve")
        assert response.status_code == 200
        assert response.json()["status"] == "resolved"
        assert response.json()["resolved_at"] is not None

    def test_list_open_incidents(self, client):
        """Test listing only open incidents."""
        # Create and resolve one incident
        create1 = client.post("/api/incidents", json={"title": "Resolved"})
        client.post(f"/api/incidents/{create1.json()['id']}/resolve")

        # Create open incident
        client.post("/api/incidents", json={"title": "Open"})

        # List open only
        response = client.get("/api/incidents/open")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Open"


class TestDashboardAPI:
    """Test suite for /api/dashboard endpoint."""

    def test_dashboard_empty(self, client):
        """Test dashboard with empty data."""
        response = client.get("/api/dashboard")
        assert response.status_code == 200

        data = response.json()
        assert "tasks" in data
        assert "monitoring" in data
        assert "activity" in data
        assert data["tasks"]["total"] == 0

    def test_dashboard_with_data(self, client):
        """Test dashboard with some data."""
        # Create tasks
        client.post("/api/tasks", json={"title": "Task 1", "column_id": 1})
        client.post("/api/tasks", json={"title": "Task 2", "column_id": 1})
        task3 = client.post("/api/tasks", json={"title": "Task 3", "column_id": 3})
        client.put(f"/api/tasks/{task3.json()['id']}", json={"completed": True})

        response = client.get("/api/dashboard")
        data = response.json()

        assert data["tasks"]["total"] == 3
        assert data["tasks"]["completed"] == 1
        assert data["tasks"]["pending"] == 2


class TestAuditAPI:
    """Test suite for /api/audit endpoint."""

    def test_audit_log_records_actions(self, client):
        """Test that actions are recorded in audit log."""
        # Create a task
        create_response = client.post("/api/tasks", json={"title": "Audited Task"})
        task_id = create_response.json()["id"]

        # Update it
        client.put(f"/api/tasks/{task_id}", json={"title": "Updated"})

        # Delete it
        client.delete(f"/api/tasks/{task_id}")

        # Check audit log
        response = client.get("/api/audit")
        assert response.status_code == 200

        data = response.json()
        assert len(data) >= 3  # create, update, delete

        actions = [log["action"] for log in data]
        assert "create" in actions
        assert "update" in actions
        assert "delete" in actions
