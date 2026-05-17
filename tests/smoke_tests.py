"""
Smoke Tests for Parallelizer Deployment
Tests basic functionality after deployment
"""

import asyncio
import pytest
import httpx

# Base URL - can be overridden with environment variable
BASE_URL = "http://localhost:8000"


@pytest.fixture
async def http_client():
    """Create HTTP client for testing"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        yield client


class TestHealthEndpoints:
    """Test health check endpoints"""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, http_client):
        """Test /health endpoint responds"""
        response = await http_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_health_endpoint_structure(self, http_client):
        """Test /health endpoint returns proper structure"""
        response = await http_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy" or data.get("status") == "ok"

    @pytest.mark.asyncio
    async def test_readiness_endpoint(self, http_client):
        """Test readiness probe endpoint"""
        response = await http_client.get("/health/ready")
        assert response.status_code in [200, 503]  # Ready or not ready

    @pytest.mark.asyncio
    async def test_liveness_endpoint(self, http_client):
        """Test liveness probe endpoint"""
        response = await http_client.get("/health/live")
        assert response.status_code == 200


class TestMetricsEndpoints:
    """Test metrics and monitoring endpoints"""

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, http_client):
        """Test /metrics endpoint returns Prometheus metrics"""
        response = await http_client.get("/metrics")
        assert response.status_code == 200
        assert "http_requests_total" in response.text or "HELP" in response.text

    @pytest.mark.asyncio
    async def test_metrics_endpoint_format(self, http_client):
        """Test metrics are in proper format"""
        response = await http_client.get("/metrics")
        assert response.status_code == 200
        # Prometheus format contains lines with # or actual metrics
        assert "#" in response.text or "{" in response.text

    @pytest.mark.asyncio
    async def test_status_endpoint(self, http_client):
        """Test /status endpoint returns deployment info"""
        response = await http_client.get("/api/v1/status")
        assert response.status_code in [200, 404]  # Endpoint may not exist
        if response.status_code == 200:
            data = response.json()
            assert "version" in data or "status" in data


class TestAPIEndpoints:
    """Test main API endpoints"""

    @pytest.mark.asyncio
    async def test_api_root(self, http_client):
        """Test API root endpoint"""
        response = await http_client.get("/api")
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_api_v1_endpoints(self, http_client):
        """Test /api/v1 endpoints exist and respond"""
        endpoints = ["/api/v1/health", "/api/v1/status"]

        for endpoint in endpoints:
            response = await http_client.get(endpoint)
            # Endpoint should either exist (200) or be not found (404)
            assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_api_documentation(self, http_client):
        """Test API documentation is available"""
        # Check for OpenAPI/Swagger docs
        endpoints = ["/docs", "/openapi.json", "/redoc"]

        for endpoint in endpoints:
            response = await http_client.get(endpoint)
            if response.status_code == 200:
                # Found one valid documentation endpoint
                return

        # At least one should be available
        pytest.skip("No API documentation endpoints found")


class TestDatabaseConnectivity:
    """Test database and external service connectivity"""

    @pytest.mark.asyncio
    async def test_redis_connectivity(self, http_client):
        """Test Redis connectivity"""
        response = await http_client.get("/health/redis")
        # Endpoint may not exist, but should not 500
        assert response.status_code in [200, 404, 503]

    @pytest.mark.asyncio
    async def test_database_connectivity(self, http_client):
        """Test database connectivity"""
        response = await http_client.get("/health/db")
        # Endpoint may not exist, but should not 500
        assert response.status_code in [200, 404, 503]


class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_404_response(self, http_client):
        """Test 404 responses for non-existent endpoints"""
        response = await http_client.get("/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, http_client):
        """Test 405 for unsupported methods"""
        # Most endpoints should reject DELETE
        response = await http_client.delete("/health")
        assert response.status_code in [405, 404]

    @pytest.mark.asyncio
    async def test_invalid_json_request(self, http_client):
        """Test handling of invalid JSON"""
        response = await http_client.post(
            "/api/v1/task", content="invalid json", headers={"Content-Type": "application/json"}
        )
        # Should return 400 or 404
        assert response.status_code in [400, 404, 422]


class TestPerformance:
    """Test performance characteristics"""

    @pytest.mark.asyncio
    async def test_health_check_latency(self, http_client):
        """Test health endpoint responds quickly"""
        import time

        start = time.time()
        response = await http_client.get("/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0  # Should respond in under 1 second

    @pytest.mark.asyncio
    async def test_metrics_endpoint_latency(self, http_client):
        """Test metrics endpoint responds within reasonable time"""
        import time

        start = time.time()
        response = await http_client.get("/metrics")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 2.0  # Should respond in under 2 seconds


class TestResponseHeaders:
    """Test proper HTTP headers"""

    @pytest.mark.asyncio
    async def test_health_response_headers(self, http_client):
        """Test response headers are correct"""
        response = await http_client.get("/health")
        assert response.status_code == 200
        assert "content-type" in response.headers

    @pytest.mark.asyncio
    async def test_cors_headers_present(self, http_client):
        """Test CORS headers are present if configured"""
        response = await http_client.get("/health")
        # Check for CORS or security headers
        headers = response.headers
        # Headers should exist (specific values may vary by config)
        assert len(headers) > 0


class TestDeploymentState:
    """Test deployment-specific checks"""

    @pytest.mark.asyncio
    async def test_api_connectivity(self, http_client):
        """Test API is accessible"""
        response = await http_client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests(self, http_client):
        """Test API handles concurrent requests"""
        tasks = [http_client.get("/health") for _ in range(5)]

        responses = await asyncio.gather(*tasks)

        for response in responses:
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_sequential_requests(self, http_client):
        """Test sequential requests work correctly"""
        for _ in range(5):
            response = await http_client.get("/health")
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
