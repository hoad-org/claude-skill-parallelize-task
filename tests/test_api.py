"""Tests for FastAPI REST API endpoints.

Tests cover:
- Health check endpoints
- Workflow CRUD operations
- Analysis endpoints
- Decision generation
- Execution endpoints
- Monitoring endpoints
- Performance endpoints
- Error handling
"""

import pytest
from datetime import datetime

from fastapi.testclient import TestClient
from parallelizer_skill.api import create_app
from parallelizer_skill.models import Task, TaskPriority


@pytest.fixture
def client():
    """Create FastAPI test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_task():
    """Create a sample task."""
    return Task(
        id="task1",
        name="Test Task",
        description="A test task",
        estimated_duration=5.0,
        parallelizable=True,
        priority=TaskPriority.NORMAL,
        max_concurrent=1,
    )


@pytest.fixture
def sample_workflow_data(sample_task):
    """Create sample workflow data."""
    return {
        "name": "Test Workflow",
        "description": "A test workflow",
        "tasks": [sample_task.model_dump()],
        "dependencies": [],
        "metadata": {"test": True},
    }


# ============================================================================
# Health & Status Tests
# ============================================================================


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "uptime_seconds" in data
        assert data["version"] == "1.1.0"

    def test_detailed_health(self, client):
        """Test detailed health check."""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "components" in data
        assert "active_workflows" in data
        assert "memory_usage_mb" in data
        assert "cpu_usage_percent" in data

    def test_health_timestamp(self, client):
        """Test health check includes timestamp."""
        response = client.get("/health")
        data = response.json()
        assert "timestamp" in data
        # Verify timestamp is ISO format
        datetime.fromisoformat(data["timestamp"])


# ============================================================================
# Workflow CRUD Tests
# ============================================================================


class TestWorkflowEndpoints:
    """Tests for workflow CRUD endpoints."""

    def test_create_workflow(self, client, sample_workflow_data):
        """Test creating a new workflow."""
        response = client.post("/workflows", json=sample_workflow_data)
        assert response.status_code == 200
        data = response.json()
        assert "workflow_id" in data
        assert data["status"] == "created"

    def test_list_workflows(self, client, sample_workflow_data):
        """Test listing workflows."""
        # Create a workflow first
        client.post("/workflows", json=sample_workflow_data)

        # List workflows
        response = client.get("/workflows")
        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_list_workflows_with_pagination(self, client, sample_workflow_data):
        """Test listing workflows with pagination."""
        # Create multiple workflows
        for i in range(5):
            data = sample_workflow_data.copy()
            data["name"] = f"Workflow {i}"
            client.post("/workflows", json=data)

        # Test pagination
        response = client.get("/workflows?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["workflows"]) <= 2
        assert data["limit"] == 2
        assert data["offset"] == 0

    def test_get_workflow(self, client, sample_workflow_data):
        """Test getting a workflow."""
        # Create a workflow
        create_response = client.post("/workflows", json=sample_workflow_data)
        workflow_id = create_response.json()["workflow_id"]

        # Get the workflow
        response = client.get(f"/workflows/{workflow_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == workflow_id
        assert data["name"] == sample_workflow_data["name"]

    def test_get_nonexistent_workflow(self, client):
        """Test getting a nonexistent workflow."""
        response = client.get("/workflows/nonexistent-id")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_delete_workflow(self, client, sample_workflow_data):
        """Test deleting a workflow."""
        # Create a workflow
        create_response = client.post("/workflows", json=sample_workflow_data)
        workflow_id = create_response.json()["workflow_id"]

        # Delete it
        response = client.delete(f"/workflows/{workflow_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

        # Verify it's deleted
        response = client.get(f"/workflows/{workflow_id}")
        assert response.status_code == 404

    def test_delete_nonexistent_workflow(self, client):
        """Test deleting a nonexistent workflow."""
        response = client.delete("/workflows/nonexistent-id")
        assert response.status_code == 404


# ============================================================================
# Analysis Tests
# ============================================================================


class TestAnalysisEndpoints:
    """Tests for analysis endpoints."""

    def test_analyze_workflow(self, client, sample_workflow_data):
        """Test analyzing a workflow."""
        # Create a workflow
        create_response = client.post("/workflows", json=sample_workflow_data)
        workflow_id = create_response.json()["workflow_id"]

        # Analyze it
        response = client.post("/analyze", json={"workflow_id": workflow_id})
        assert response.status_code == 200
        data = response.json()
        assert "analysis_id" in data
        assert data["status"] == "completed"

    def test_analyze_nonexistent_workflow(self, client):
        """Test analyzing a nonexistent workflow."""
        response = client.post("/analyze", json={"workflow_id": "nonexistent"})
        assert response.status_code == 404

    def test_get_analysis(self, client, sample_workflow_data):
        """Test getting analysis results."""
        # Create and analyze a workflow
        create_response = client.post("/workflows", json=sample_workflow_data)
        workflow_id = create_response.json()["workflow_id"]

        analyze_response = client.post("/analyze", json={"workflow_id": workflow_id})
        analysis_id = analyze_response.json()["analysis_id"]

        # Get the analysis
        response = client.get(f"/analyze/{analysis_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_id"] == analysis_id
        assert data["workflow_id"] == workflow_id
        assert "total_tasks" in data
        assert "complexity_scores" in data

    def test_get_nonexistent_analysis(self, client):
        """Test getting a nonexistent analysis."""
        response = client.get("/analyze/nonexistent-id")
        assert response.status_code == 404


# ============================================================================
# Decision Tests
# ============================================================================


class TestDecisionEndpoints:
    """Tests for decision generation endpoints."""

    def test_generate_decision(self, client, sample_workflow_data):
        """Test generating a decision."""
        # Create and analyze a workflow
        create_response = client.post("/workflows", json=sample_workflow_data)
        workflow_id = create_response.json()["workflow_id"]

        analyze_response = client.post("/analyze", json={"workflow_id": workflow_id})
        analysis_id = analyze_response.json()["analysis_id"]

        # Generate decision
        response = client.post("/decide", json={"analysis_id": analysis_id})
        assert response.status_code == 200
        data = response.json()
        assert "decision_id" in data
        assert data["status"] == "completed"

    def test_generate_decision_nonexistent_analysis(self, client):
        """Test generating decision for nonexistent analysis."""
        response = client.post("/decide", json={"analysis_id": "nonexistent"})
        assert response.status_code == 404

    def test_get_decision(self, client, sample_workflow_data):
        """Test getting decision results."""
        # Create, analyze, and generate decision
        create_response = client.post("/workflows", json=sample_workflow_data)
        workflow_id = create_response.json()["workflow_id"]

        analyze_response = client.post("/analyze", json={"workflow_id": workflow_id})
        analysis_id = analyze_response.json()["analysis_id"]

        decide_response = client.post("/decide", json={"analysis_id": analysis_id})
        decision_id = decide_response.json()["decision_id"]

        # Get decision
        response = client.get(f"/decide/{decision_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == decision_id
        assert "efficiency_gain" in data
        assert "critical_path" in data


# ============================================================================
# Execution Tests
# ============================================================================


class TestExecutionEndpoints:
    """Tests for execution endpoints."""

    def test_execute_workflow(self, client, sample_workflow_data):
        """Test executing a workflow."""
        # Create a workflow
        create_response = client.post("/workflows", json=sample_workflow_data)
        workflow_id = create_response.json()["workflow_id"]

        # Execute it
        response = client.post("/execute", json={"workflow_id": workflow_id})
        assert response.status_code == 200
        data = response.json()
        assert "execution_id" in data
        assert data["status"] == "running"

    def test_execute_nonexistent_workflow(self, client):
        """Test executing a nonexistent workflow."""
        response = client.post("/execute", json={"workflow_id": "nonexistent"})
        assert response.status_code == 404

    def test_get_execution_status(self, client, sample_workflow_data):
        """Test getting execution status."""
        # Create and execute a workflow
        create_response = client.post("/workflows", json=sample_workflow_data)
        workflow_id = create_response.json()["workflow_id"]

        exec_response = client.post("/execute", json={"workflow_id": workflow_id})
        execution_id = exec_response.json()["execution_id"]

        # Get status
        response = client.get(f"/execute/{execution_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["execution_id"] == execution_id
        assert "status" in data
        assert "tasks_completed" in data

    def test_get_execution_metrics(self, client, sample_workflow_data):
        """Test getting execution metrics."""
        # Create and execute a workflow
        create_response = client.post("/workflows", json=sample_workflow_data)
        workflow_id = create_response.json()["workflow_id"]

        exec_response = client.post("/execute", json={"workflow_id": workflow_id})
        execution_id = exec_response.json()["execution_id"]

        # Get metrics
        response = client.get(f"/execute/{execution_id}/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["execution_id"] == execution_id
        assert "duration_seconds" in data
        assert "tasks_completed" in data


# ============================================================================
# Monitoring Tests
# ============================================================================


class TestMonitoringEndpoints:
    """Tests for monitoring endpoints."""

    def test_get_metrics(self, client, sample_workflow_data):
        """Test getting metrics."""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "workflows_total" in data
        assert "workflows_active" in data
        assert "tasks_completed_total" in data
        assert "cache_hit_rate" in data

    def test_get_alerts(self, client):
        """Test getting alerts."""
        response = client.get("/alerts")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "alerts" in data

    def test_get_alerts_with_limit(self, client):
        """Test getting alerts with limit."""
        response = client.get("/alerts?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["alerts"]) <= 5


# ============================================================================
# Performance Tests
# ============================================================================


class TestPerformanceEndpoints:
    """Tests for performance endpoints."""

    def test_get_performance_stats(self, client):
        """Test getting performance statistics."""
        response = client.get("/performance/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_workflows" in data
        assert "total_tasks" in data
        assert "average_task_duration" in data
        assert "parallelization_success_rate" in data

    def test_get_cache_stats(self, client):
        """Test getting cache statistics."""
        response = client.get("/performance/cache")
        assert response.status_code == 200
        data = response.json()
        assert "total_caches" in data
        assert "cache_hits" in data
        assert "cache_misses" in data
        assert "hit_rate" in data


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegrationWorkflow:
    """Integration tests for complete workflow."""

    def test_full_workflow_pipeline(self, client, sample_workflow_data):
        """Test complete workflow pipeline."""
        # 1. Create workflow
        create_response = client.post("/workflows", json=sample_workflow_data)
        assert create_response.status_code == 200
        workflow_id = create_response.json()["workflow_id"]

        # 2. Get workflow
        get_response = client.get(f"/workflows/{workflow_id}")
        assert get_response.status_code == 200

        # 3. Analyze workflow
        analyze_response = client.post("/analyze", json={"workflow_id": workflow_id})
        assert analyze_response.status_code == 200
        analysis_id = analyze_response.json()["analysis_id"]

        # 4. Generate decision
        decide_response = client.post("/decide", json={"analysis_id": analysis_id})
        assert decide_response.status_code == 200
        decision_id = decide_response.json()["decision_id"]

        # 5. Execute workflow
        exec_response = client.post("/execute", json={"workflow_id": workflow_id, "plan_id": decision_id})
        assert exec_response.status_code == 200
        execution_id = exec_response.json()["execution_id"]

        # 6. Get execution status
        status_response = client.get(f"/execute/{execution_id}")
        assert status_response.status_code == 200

        # 7. Get metrics
        metrics_response = client.get("/metrics")
        assert metrics_response.status_code == 200
        assert metrics_response.json()["workflows_total"] >= 1

    def test_health_check_consistency(self, client, sample_workflow_data):
        """Test that health checks are consistent."""
        # Get health before and after creating workflows
        health1 = client.get("/health/detailed").json()
        health1["active_workflows"]

        # Create a workflow
        client.post("/workflows", json=sample_workflow_data)

        # Check health again
        health2 = client.get("/health/detailed").json()

        # Status should remain healthy
        assert health1["overall_status"] == "healthy"
        assert health2["overall_status"] == "healthy"


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_json(self, client):
        """Test handling of invalid JSON."""
        response = client.post(
            "/workflows",
            content="invalid json",
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        """Test handling of missing required fields."""
        response = client.post("/workflows", json={"description": "Missing name"})
        assert response.status_code == 422

    def test_404_response_format(self, client):
        """Test that 404 responses have proper format."""
        response = client.get("/workflows/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "timestamp" in data

    def test_method_not_allowed(self, client):
        """Test method not allowed."""
        response = client.post("/health")
        assert response.status_code == 405


# ============================================================================
# Endpoint Coverage Tests
# ============================================================================


class TestEndpointCoverage:
    """Tests to ensure all endpoints are accessible."""

    def test_openapi_schema(self, client):
        """Test OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "paths" in data
        assert "components" in data

    def test_swagger_ui(self, client):
        """Test Swagger UI is available."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()

    def test_redoc(self, client):
        """Test ReDoc is available."""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_all_endpoints_exist(self, client):
        """Test that all documented endpoints exist."""
        endpoints = [
            ("/health", "GET"),
            ("/health/detailed", "GET"),
            ("/workflows", "GET"),
            ("/workflows", "POST"),
            ("/metrics", "GET"),
            ("/alerts", "GET"),
            ("/performance/stats", "GET"),
            ("/performance/cache", "GET"),
        ]

        for path, method in endpoints:
            if method == "GET":
                response = client.get(path)
                assert response.status_code in [200, 422], f"Failed for GET {path}"
            elif method == "POST":
                response = client.post(path, json={})
                # POST without proper data should give 422 or 200
                assert response.status_code in [200, 422], f"Failed for POST {path}"
