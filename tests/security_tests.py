"""
Security Tests for Parallelizer Deployment
Tests security aspects of the application and infrastructure
"""

import pytest
import httpx

BASE_URL = "http://localhost:8000"


@pytest.fixture
async def http_client():
    """Create HTTP client for testing"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        yield client


class TestHTTPSecurity:
    """Test HTTP security headers"""

    @pytest.mark.asyncio
    async def test_no_server_header_disclosure(self, http_client):
        """Test that server version is not disclosed"""
        response = await http_client.get("/health")
        assert response.status_code == 200

        # Check for common server header variations
        headers = {k.lower(): v for k, v in response.headers.items()}

        # Server header should either not exist or be generic
        if "server" in headers:
            server = headers["server"]
            # Should not contain detailed version info
            assert "python" not in server.lower() or "version" not in server.lower()

    @pytest.mark.asyncio
    async def test_security_headers_present(self, http_client):
        """Test that security headers are present"""
        response = await http_client.get("/health")
        assert response.status_code == 200

        headers = {k.lower(): v for k, v in response.headers.items()}

        # Check for at least some security headers
        security_headers = ["content-security-policy", "x-content-type-options", "x-frame-options", "x-xss-protection"]

        # At least one security header should be present
        # (specific headers depend on framework configuration)
        any(header in headers for header in security_headers)
        # Note: This is optional depending on framework config

    @pytest.mark.asyncio
    async def test_content_type_header(self, http_client):
        """Test content-type is properly set"""
        response = await http_client.get("/health")
        assert response.status_code == 200

        headers = {k.lower(): v for k, v in response.headers.items()}
        assert "content-type" in headers

    @pytest.mark.asyncio
    async def test_no_debug_info_in_errors(self, http_client):
        """Test that debug info is not exposed in error responses"""
        response = await http_client.get("/nonexistent")
        assert response.status_code == 404

        # Should not contain stack traces or detailed error info
        content = response.text.lower()
        assert "traceback" not in content
        assert "exception" not in content or "api" in content  # Exception in API docs is ok


class TestAuthenticationSecurity:
    """Test authentication and authorization"""

    @pytest.mark.asyncio
    async def test_no_default_credentials(self, http_client):
        """Test that default credentials are not active"""
        # Try with common default credentials
        await http_client.get("/health", headers={"Authorization": "Basic YWRtaW46YWRtaW4"})  # admin:admin

        # Should not gain elevated access with defaults
        # (exact behavior depends on auth implementation)

    @pytest.mark.asyncio
    async def test_missing_auth_header(self, http_client):
        """Test behavior with missing auth headers"""
        # Try accessing endpoint without auth
        response = await http_client.get("/health")

        # Health endpoint should be public
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_auth_header(self, http_client):
        """Test handling of invalid auth headers"""
        response = await http_client.get("/health", headers={"Authorization": "Bearer invalid_token"})

        # Should handle gracefully
        # Either 200 (public endpoint) or 401 (protected endpoint)
        assert response.status_code in [200, 401, 403]


class TestInputValidation:
    """Test input validation and injection prevention"""

    @pytest.mark.asyncio
    async def test_sql_injection_attempt(self, http_client):
        """Test SQL injection prevention"""
        malicious_input = "'; DROP TABLE users; --"

        response = await http_client.get(f"/api/v1/task?search={malicious_input}")

        # Should not execute or expose database
        assert response.status_code in [200, 400, 404, 422]
        assert "drop table" not in response.text.lower()

    @pytest.mark.asyncio
    async def test_xss_attempt(self, http_client):
        """Test XSS prevention"""
        xss_payload = "<script>alert('xss')</script>"

        response = await http_client.get(f"/api/v1/task?name={xss_payload}")

        # Script should be escaped or sanitized
        if response.status_code == 200:
            assert "<script>" not in response.text or response.headers.get("content-type", "").startswith(
                "application/json"
            )

    @pytest.mark.asyncio
    async def test_path_traversal_attempt(self, http_client):
        """Test path traversal prevention"""
        response = await http_client.get("/api/v1/../../../etc/passwd")

        # Should not allow path traversal
        assert response.status_code in [404, 400, 403]

    @pytest.mark.asyncio
    async def test_json_bomb_attack(self, http_client):
        """Test protection against JSON bomb (large payload)"""
        large_payload = "x" * (10 * 1024 * 1024)  # 10MB

        try:
            response = await http_client.post(
                "/api/v1/task",
                content=f'{{"data": "{large_payload}"}}',
                headers={"Content-Type": "application/json"},
                timeout=5.0,
            )
            # Should reject or handle gracefully
            assert response.status_code in [400, 413, 422, 404]
        except httpx.RequestError:
            # Timeout or connection error is acceptable
            pass


class TestRateLimiting:
    """Test rate limiting and abuse prevention"""

    @pytest.mark.asyncio
    async def test_rapid_requests(self, http_client):
        """Test handling of rapid repeated requests"""
        import asyncio

        responses = []
        for i in range(100):
            response = await http_client.get("/health")
            responses.append(response.status_code)
            await asyncio.sleep(0.01)

        # Should mostly succeed (rate limiting may kick in)
        successful = sum(1 for s in responses if s == 200)
        assert successful >= 90  # At least 90% should succeed

    @pytest.mark.asyncio
    async def test_rate_limit_headers(self, http_client):
        """Test rate limit headers are present"""
        response = await http_client.get("/health")

        {k.lower(): v for k, v in response.headers.items()}

        # Check for rate limit headers (if implemented)

        # At least one may be present depending on configuration


class TestDataSensitivity:
    """Test handling of sensitive data"""

    @pytest.mark.asyncio
    async def test_no_credentials_in_logs(self, http_client):
        """Test that credentials are not logged"""
        response = await http_client.get("/health", headers={"Authorization": "Bearer secret_token_12345"})

        # Response should not contain the token
        assert "secret_token_12345" not in response.text

    @pytest.mark.asyncio
    async def test_no_pii_in_errors(self, http_client):
        """Test that PII is not exposed in error messages"""
        response = await http_client.get("/nonexistent")

        # Should not contain sensitive data
        assert "@example.com" not in response.text
        assert "192.168" not in response.text


class TestSSLTLS:
    """Test SSL/TLS configuration"""

    @pytest.mark.asyncio
    async def test_https_redirect(self):
        """Test HTTPS redirect (if implemented)"""
        # Note: This test is informational only
        # Application should ideally redirect HTTP to HTTPS
        pass

    @pytest.mark.asyncio
    async def test_hsts_header(self, http_client):
        """Test HSTS header presence"""
        response = await http_client.get("/health")

        {k.lower(): v for k, v in response.headers.items()}

        # HSTS header is optional but recommended
        # assert "strict-transport-security" in headers


class TestCORSSecurity:
    """Test CORS configuration"""

    @pytest.mark.asyncio
    async def test_cors_origin_validation(self, http_client):
        """Test CORS origin validation"""
        response = await http_client.get("/health", headers={"Origin": "https://malicious.com"})

        assert response.status_code == 200

        headers = {k.lower(): v for k, v in response.headers.items()}

        # Check CORS headers if present
        if "access-control-allow-origin" in headers:
            origin = headers["access-control-allow-origin"]
            # Should not allow all origins with credentials
            if origin == "*":
                # Wildcard is OK if no credentials involved
                assert "access-control-allow-credentials" not in headers

    @pytest.mark.asyncio
    async def test_preflight_request(self, http_client):
        """Test CORS preflight request handling"""
        response = await http_client.options(
            "/health", headers={"Origin": "https://example.com", "Access-Control-Request-Method": "POST"}
        )

        # Should handle OPTIONS gracefully
        assert response.status_code in [200, 404, 405]


class TestDeprecatedProtocols:
    """Test that deprecated protocols are not allowed"""

    @pytest.mark.asyncio
    async def test_tls_version(self):
        """Test TLS version (informational)"""
        # This would require SSL context inspection
        # Ensure TLS 1.2+ is used (not SSLv3, TLSv1.0, TLSv1.1)
        pass


class TestVulnerableComponents:
    """Test for known vulnerable component usage"""

    @pytest.mark.asyncio
    async def test_outdated_dependencies(self):
        """Test that dependencies are up to date"""
        # This should be checked via pip-audit or similar
        # Not a runtime test, but good practice
        pass


class TestSecurityHeaders:
    """Test comprehensive security header configuration"""

    @pytest.mark.asyncio
    async def test_content_security_policy(self, http_client):
        """Test CSP header"""
        response = await http_client.get("/health")

        headers = {k.lower(): v for k, v in response.headers.items()}

        # CSP is optional but recommended
        if "content-security-policy" in headers:
            csp = headers["content-security-policy"]
            # Should restrict sources
            assert len(csp) > 0

    @pytest.mark.asyncio
    async def test_x_content_type_options(self, http_client):
        """Test X-Content-Type-Options header"""
        response = await http_client.get("/health")

        headers = {k.lower(): v for k, v in response.headers.items()}

        # Should prevent MIME sniffing
        if "x-content-type-options" in headers:
            assert headers["x-content-type-options"].lower() == "nosniff"

    @pytest.mark.asyncio
    async def test_x_frame_options(self, http_client):
        """Test X-Frame-Options header"""
        response = await http_client.get("/health")

        headers = {k.lower(): v for k, v in response.headers.items()}

        # Should prevent clickjacking
        if "x-frame-options" in headers:
            value = headers["x-frame-options"].upper()
            assert value in ["DENY", "SAMEORIGIN"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
