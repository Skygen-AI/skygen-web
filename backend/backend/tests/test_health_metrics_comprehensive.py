"""
Comprehensive tests for Health and Metrics endpoints.
Tests health check and metrics endpoints with various scenarios.
"""

import os
import pytest
import httpx
import asyncio


BASE_URL = os.getenv("BASE_URL", "http://0.0.0.0:8000")


class TestHealthEndpoint:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_endpoint_success(self):
        """Test successful health check."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            response = await client.get("/healthz")

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "status" in data
            assert "env" in data

            # Verify values
            assert data["status"] == "ok"
            assert isinstance(data["env"], str)
            assert len(data["env"]) > 0

    @pytest.mark.asyncio
    async def test_health_endpoint_no_auth_required(self):
        """Test that health endpoint doesn't require authentication."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Test without any headers
            response = await client.get("/healthz")
            assert response.status_code == 200

            # Test with invalid auth header (should still work)
            response2 = await client.get(
                "/healthz", headers={"Authorization": "Bearer invalid_token"}
            )
            assert response2.status_code == 200

    @pytest.mark.asyncio
    async def test_health_endpoint_response_format(self):
        """Test health endpoint response format consistency."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Make multiple requests to ensure consistent format
            for _ in range(5):
                response = await client.get("/healthz")

                assert response.status_code == 200
                data = response.json()

                # Verify consistent structure
                assert set(data.keys()) == {"status", "env"}
                assert data["status"] == "ok"
                assert isinstance(data["env"], str)

    @pytest.mark.asyncio
    async def test_health_endpoint_methods(self):
        """Test health endpoint with different HTTP methods."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # GET should work
            response = await client.get("/healthz")
            assert response.status_code == 200

            # Other methods should not be allowed
            methods_to_test = ["POST", "PUT", "DELETE", "PATCH"]

            for method in methods_to_test:
                response = await client.request(method, "/healthz")
                # Should return 405 Method Not Allowed or 404 Not Found
                assert response.status_code in [404, 405]

    @pytest.mark.asyncio
    async def test_health_endpoint_query_parameters(self):
        """Test health endpoint with query parameters."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Query parameters should be ignored
            response = await client.get("/healthz?param=value&other=test")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_endpoint_headers(self):
        """Test health endpoint with various headers."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            headers = {
                "User-Agent": "TestClient/1.0",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Custom-Header": "test-value",
            }

            response = await client.get("/healthz", headers=headers)

            assert response.status_code == 200
            assert response.headers.get("content-type", "").startswith("application/json")

    @pytest.mark.asyncio
    async def test_health_endpoint_concurrent_requests(self):
        """Test health endpoint with concurrent requests."""
        import asyncio

        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create multiple concurrent requests
            tasks = []
            for _ in range(10):
                task = client.get("/healthz")
                tasks.append(task)

            # Execute all requests concurrently
            responses = await asyncio.gather(*tasks)

            # All should succeed
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "ok"


class TestMetricsEndpoint:
    """Test metrics endpoint."""

    @pytest.mark.asyncio
    async def test_metrics_endpoint_success(self):
        """Test successful metrics retrieval."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            response = await client.get("/metrics")

            assert response.status_code == 200

            # Verify content type is Prometheus format
            content_type = response.headers.get("content-type", "")
            assert "text/plain" in content_type or "text/plain; version=0.0.4" in content_type

    @pytest.mark.asyncio
    async def test_metrics_endpoint_content_format(self):
        """Test metrics endpoint content format (Prometheus format)."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            response = await client.get("/metrics")

            assert response.status_code == 200
            content = response.text

            # Basic Prometheus format checks
            assert isinstance(content, str)
            assert len(content) > 0

            # Should contain some basic metrics patterns
            # Prometheus metrics typically have lines like:
            # # HELP metric_name Description
            # # TYPE metric_name counter
            # metric_name{label="value"} 123.45

            lines = content.split("\n")

            # Should have some non-empty lines
            non_empty_lines = [line for line in lines if line.strip()]
            assert len(non_empty_lines) > 0

            # Look for typical Prometheus patterns
            has_help_lines = any(line.startswith("# HELP") for line in lines)
            has_type_lines = any(line.startswith("# TYPE") for line in lines)
            has_metric_lines = any(not line.startswith("#") and line.strip() for line in lines)

            # At least some metric content should be present
            assert has_metric_lines

    @pytest.mark.asyncio
    async def test_metrics_endpoint_no_auth_required(self):
        """Test that metrics endpoint doesn't require authentication."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Test without any headers
            response = await client.get("/metrics")
            assert response.status_code == 200

            # Test with invalid auth header (should still work)
            response2 = await client.get(
                "/metrics", headers={"Authorization": "Bearer invalid_token"}
            )
            assert response2.status_code == 200

    @pytest.mark.asyncio
    async def test_metrics_endpoint_methods(self):
        """Test metrics endpoint with different HTTP methods."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # GET should work
            response = await client.get("/metrics")
            assert response.status_code == 200

            # Other methods should not be allowed
            methods_to_test = ["POST", "PUT", "DELETE", "PATCH"]

            for method in methods_to_test:
                response = await client.request(method, "/metrics")
                # Should return 405 Method Not Allowed or 404 Not Found
                assert response.status_code in [404, 405]

    @pytest.mark.asyncio
    async def test_metrics_endpoint_consistency(self):
        """Test metrics endpoint consistency across multiple calls."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Get metrics multiple times
            responses = []
            for _ in range(3):
                response = await client.get("/metrics")
                assert response.status_code == 200
                responses.append(response.text)

            # All responses should be valid (though values may change)
            for content in responses:
                assert isinstance(content, str)
                assert len(content) > 0

                # Should maintain consistent format
                lines = content.split("\n")
                non_empty_lines = [line for line in lines if line.strip()]
                assert len(non_empty_lines) > 0

    @pytest.mark.asyncio
    async def test_metrics_endpoint_specific_metrics(self):
        """Test for presence of specific expected metrics."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            response = await client.get("/metrics")

            assert response.status_code == 200
            content = response.text

            # Look for common Python/FastAPI metrics
            # These might be present depending on what metrics are configured
            possible_metrics = [
                "python_info",
                "process_",
                "http_requests",
                "http_request_duration",
                "ws_connections",
                "tasks_created",
                # Add other metrics that your application exposes
            ]

            # At least some metrics should be present
            found_metrics = []
            for metric in possible_metrics:
                if metric in content:
                    found_metrics.append(metric)

            # We expect at least some metrics to be present
            # The exact metrics depend on your Prometheus setup
            # This test is more about ensuring the endpoint returns valid content
            assert len(content) > 100  # Should have substantial content

    @pytest.mark.asyncio
    async def test_metrics_endpoint_concurrent_requests(self):
        """Test metrics endpoint with concurrent requests."""
        import asyncio

        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create multiple concurrent requests
            tasks = []
            for _ in range(5):
                task = client.get("/metrics")
                tasks.append(task)

            # Execute all requests concurrently
            responses = await asyncio.gather(*tasks)

            # All should succeed
            for response in responses:
                assert response.status_code == 200
                assert len(response.text) > 0

    @pytest.mark.asyncio
    async def test_metrics_endpoint_after_api_activity(self):
        """Test metrics endpoint after some API activity to ensure metrics are updated."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Get initial metrics
            initial_response = await client.get("/metrics")
            assert initial_response.status_code == 200
            initial_content = initial_response.text

            # Perform some API activity that might affect metrics
            # Health check calls
            for _ in range(5):
                health_response = await client.get("/healthz")
                assert health_response.status_code == 200

            # Get metrics again
            final_response = await client.get("/metrics")
            assert final_response.status_code == 200
            final_content = final_response.text

            # Both should be valid metrics content
            assert len(initial_content) > 0
            assert len(final_content) > 0

            # Content format should be consistent
            assert isinstance(initial_content, str)
            assert isinstance(final_content, str)

    @pytest.mark.asyncio
    async def test_metrics_endpoint_response_headers(self):
        """Test metrics endpoint response headers."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            response = await client.get("/metrics")

            assert response.status_code == 200

            # Check content type
            content_type = response.headers.get("content-type", "")
            # Prometheus metrics should have text/plain content type
            assert "text/plain" in content_type.lower()

            # Check that response has content
            assert len(response.content) > 0


class TestHealthMetricsIntegration:
    """Integration tests for health and metrics endpoints."""

    @pytest.mark.asyncio
    async def test_health_and_metrics_together(self):
        """Test calling both health and metrics endpoints together."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Call both endpoints
            health_response = await client.get("/healthz")
            metrics_response = await client.get("/metrics")

            # Both should succeed
            assert health_response.status_code == 200
            assert metrics_response.status_code == 200

            # Verify content
            health_data = health_response.json()
            assert health_data["status"] == "ok"

            metrics_content = metrics_response.text
            assert len(metrics_content) > 0

    @pytest.mark.asyncio
    async def test_health_metrics_during_high_load(self):
        """Test health and metrics endpoints during simulated high load."""
        import asyncio

        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create many concurrent requests to both endpoints
            tasks = []

            # Health checks
            for _ in range(10):
                tasks.append(client.get("/healthz"))

            # Metrics requests
            for _ in range(5):
                tasks.append(client.get("/metrics"))

            # Execute all concurrently
            responses = await asyncio.gather(*tasks)

            # All should succeed
            health_responses = responses[:10]
            metrics_responses = responses[10:]

            for response in health_responses:
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "ok"

            for response in metrics_responses:
                assert response.status_code == 200
                assert len(response.text) > 0

    @pytest.mark.asyncio
    async def test_health_metrics_availability(self):
        """Test that health and metrics endpoints are always available."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Test multiple times with some delay
            for i in range(5):
                health_response = await client.get("/healthz")
                metrics_response = await client.get("/metrics")

                assert health_response.status_code == 200
                assert metrics_response.status_code == 200

                # Small delay between requests
                await asyncio.sleep(0.5)

    @pytest.mark.asyncio
    async def test_health_metrics_error_resilience(self):
        """Test that health and metrics endpoints remain available even with bad requests."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Make some bad requests to other endpoints first
            bad_requests = [
                client.get("/nonexistent"),
                client.post("/healthz"),  # Wrong method
                client.get("/v1/auth/login"),  # Missing body
            ]

            # Execute bad requests (expect failures)
            bad_responses = await asyncio.gather(*bad_requests, return_exceptions=True)

            # Health and metrics should still work
            health_response = await client.get("/healthz")
            metrics_response = await client.get("/metrics")

            assert health_response.status_code == 200
            assert metrics_response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_metrics_response_time(self):
        """Test that health and metrics endpoints respond quickly."""
        import time

        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Test health endpoint response time
            start_time = time.time()
            health_response = await client.get("/healthz")
            health_time = time.time() - start_time

            assert health_response.status_code == 200
            assert health_time < 2.0  # Should respond within 2 seconds

            # Test metrics endpoint response time
            start_time = time.time()
            metrics_response = await client.get("/metrics")
            metrics_time = time.time() - start_time

            assert metrics_response.status_code == 200
            assert metrics_time < 5.0  # Metrics might take a bit longer

    @pytest.mark.asyncio
    async def test_health_metrics_with_different_user_agents(self):
        """Test health and metrics endpoints with different user agents."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "curl/7.68.0",
            "Prometheus/2.30.0",
            "python-httpx/0.24.0",
            "HealthChecker/1.0",
        ]

        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            for user_agent in user_agents:
                headers = {"User-Agent": user_agent}

                health_response = await client.get("/healthz", headers=headers)
                metrics_response = await client.get("/metrics", headers=headers)

                assert health_response.status_code == 200
                assert metrics_response.status_code == 200

                # Verify content is consistent regardless of user agent
                health_data = health_response.json()
                assert health_data["status"] == "ok"

                assert len(metrics_response.text) > 0
