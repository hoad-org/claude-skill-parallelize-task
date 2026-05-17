"""
Load Tests for Parallelizer Deployment
Tests performance under load and stress
"""

import asyncio
import time
import pytest
import httpx
from statistics import mean

BASE_URL = "http://localhost:8000"


@pytest.fixture
async def http_client():
    """Create HTTP client for testing"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        yield client


class TestConcurrentLoad:
    """Test behavior under concurrent load"""

    @pytest.mark.asyncio
    async def test_10_concurrent_requests(self, http_client):
        """Test 10 concurrent health checks"""
        tasks = [http_client.get("/health") for _ in range(10)]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successes
        successes = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 200)
        assert successes >= 9  # Allow 1 failure out of 10

    @pytest.mark.asyncio
    async def test_50_concurrent_requests(self, http_client):
        """Test 50 concurrent requests"""
        tasks = [http_client.get("/health") for _ in range(50)]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        successes = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 200)
        success_rate = successes / 50
        assert success_rate >= 0.90  # Allow 10% failure rate

    @pytest.mark.asyncio
    async def test_100_concurrent_requests(self, http_client):
        """Test 100 concurrent requests"""
        tasks = [http_client.get("/health") for _ in range(100)]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        successes = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 200)
        success_rate = successes / 100
        assert success_rate >= 0.85  # Allow 15% failure rate at high concurrency


class TestLatencyUnderLoad:
    """Test latency characteristics under load"""

    @pytest.mark.asyncio
    async def test_health_latency_single(self, http_client):
        """Test single health check latency"""
        times = []

        for _ in range(10):
            start = time.time()
            response = await http_client.get("/health")
            elapsed = time.time() - start

            assert response.status_code == 200
            times.append(elapsed)

        avg_time = mean(times)
        max_time = max(times)

        assert avg_time < 0.5  # Average under 500ms
        assert max_time < 1.0  # Max under 1 second

    @pytest.mark.asyncio
    async def test_health_latency_concurrent(self, http_client):
        """Test latency under concurrent load"""

        async def timed_request():
            start = time.time()
            response = await http_client.get("/health")
            elapsed = time.time() - start
            return elapsed, response.status_code == 200

        # Run 50 concurrent requests
        tasks = [timed_request() for _ in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        times = [t for t, success in results if isinstance(t, float) and success]

        if times:
            avg_time = mean(times)
            p95_time = sorted(times)[int(len(times) * 0.95)]

            # Under concurrent load, latency may increase
            assert avg_time < 2.0  # Average under 2 seconds
            assert p95_time < 3.0  # 95th percentile under 3 seconds

    @pytest.mark.asyncio
    async def test_metrics_latency(self, http_client):
        """Test metrics endpoint latency"""
        times = []

        for _ in range(5):
            start = time.time()
            response = await http_client.get("/metrics")
            elapsed = time.time() - start

            assert response.status_code == 200
            times.append(elapsed)

        avg_time = mean(times)

        # Metrics may be larger, allow more time
        assert avg_time < 2.0

    @pytest.mark.asyncio
    async def test_api_latency(self, http_client):
        """Test API endpoint latency"""
        times = []

        for _ in range(5):
            start = time.time()
            response = await http_client.get("/api/v1/status")
            elapsed = time.time() - start

            # Endpoint may not exist
            if response.status_code == 200:
                times.append(elapsed)

        if times:
            avg_time = mean(times)
            assert avg_time < 1.0


class TestThroughput:
    """Test maximum throughput"""

    @pytest.mark.asyncio
    async def test_requests_per_second(self, http_client):
        """Test requests per second capacity"""
        start_time = time.time()
        request_count = 0
        successful_requests = 0

        # Run for up to 10 seconds or 1000 requests
        while time.time() - start_time < 10 and request_count < 1000:
            response = await http_client.get("/health")
            request_count += 1

            if response.status_code == 200:
                successful_requests += 1

        elapsed = time.time() - start_time
        rps = request_count / elapsed

        # Should handle at least 10 requests per second
        assert rps >= 10
        assert successful_requests / request_count >= 0.95

    @pytest.mark.asyncio
    async def test_throughput_with_concurrency(self, http_client):
        """Test throughput with concurrent requests"""
        start_time = time.time()
        request_count = 0
        successful_requests = 0

        # 20 concurrent requests, repeated 5 times
        for _ in range(5):
            tasks = [http_client.get("/health") for _ in range(20)]

            responses = await asyncio.gather(*tasks, return_exceptions=True)
            request_count += 20

            for response in responses:
                if isinstance(response, httpx.Response) and response.status_code == 200:
                    successful_requests += 1

        elapsed = time.time() - start_time
        rps = request_count / elapsed

        assert rps >= 20
        assert successful_requests / request_count >= 0.95


class TestSustainability:
    """Test sustained load over time"""

    @pytest.mark.asyncio
    async def test_sustained_load_30_seconds(self, http_client):
        """Test sustained load for 30 seconds"""
        start_time = time.time()
        request_count = 0
        successful_requests = 0
        failures = []

        while time.time() - start_time < 30:
            try:
                response = await http_client.get("/health", timeout=5.0)
                request_count += 1

                if response.status_code == 200:
                    successful_requests += 1
                else:
                    failures.append(response.status_code)
            except Exception as e:
                request_count += 1
                failures.append(str(e))

            # Small delay between requests
            await asyncio.sleep(0.01)

        _elapsed = time.time() - start_time
        success_rate = successful_requests / request_count if request_count > 0 else 0

        assert success_rate >= 0.95
        assert request_count > 50  # Should make at least 50 requests in 30 seconds

    @pytest.mark.asyncio
    async def test_no_memory_leak_pattern(self, http_client):
        """Test for patterns indicating memory leaks"""
        # Make requests and check response times don't degrade
        times = []

        for i in range(100):
            start = time.time()
            response = await http_client.get("/health")
            elapsed = time.time() - start

            if response.status_code == 200:
                times.append((i, elapsed))

            if i % 25 == 24:
                await asyncio.sleep(0.1)

        # Check if response times increase significantly over time
        if len(times) > 10:
            first_half = [t for i, t in times[: len(times) // 2]]
            second_half = [t for i, t in times[len(times) // 2 :]]

            avg_first = mean(first_half)
            avg_second = mean(second_half)

            # Second half shouldn't be more than 2x slower
            assert avg_second <= avg_first * 2


class TestErrorRates:
    """Test error behavior under load"""

    @pytest.mark.asyncio
    async def test_error_rate_under_light_load(self, http_client):
        """Test error rate with 10 concurrent requests"""
        tasks = [http_client.get("/health") for _ in range(10)]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        successful = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 200)
        error_rate = 1 - (successful / len(responses))

        assert error_rate < 0.05  # Less than 5% error rate

    @pytest.mark.asyncio
    async def test_error_rate_under_heavy_load(self, http_client):
        """Test error rate with 200 concurrent requests"""
        tasks = [http_client.get("/health") for _ in range(200)]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        successful = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 200)
        error_rate = 1 - (successful / len(responses))

        # Higher error rate acceptable at heavy load, but should stay reasonable
        assert error_rate < 0.20  # Less than 20% error rate

    @pytest.mark.asyncio
    async def test_timeout_handling(self, http_client):
        """Test timeout handling under load"""
        # Set very short timeout
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=0.1) as timeout_client:
            tasks = [timeout_client.get("/health") for _ in range(20)]

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Should either succeed or timeout gracefully
            for response in responses:
                if isinstance(response, httpx.Response):
                    assert response.status_code in [200]
                # Exceptions are acceptable (timeouts)


class TestResourceUsage:
    """Test resource usage patterns"""

    @pytest.mark.asyncio
    async def test_response_size(self, http_client):
        """Test response sizes are reasonable"""
        response = await http_client.get("/health")
        assert response.status_code == 200

        size_kb = len(response.content) / 1024
        assert size_kb < 10  # Health endpoint should be under 10KB

    @pytest.mark.asyncio
    async def test_metrics_response_size(self, http_client):
        """Test metrics response size"""
        response = await http_client.get("/metrics")
        assert response.status_code == 200

        size_kb = len(response.content) / 1024
        assert size_kb < 100  # Metrics may be larger, but should stay under 100KB


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
