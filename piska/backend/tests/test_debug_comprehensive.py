"""
Comprehensive tests for debug API endpoints.

Tests debugging functionality, system monitoring, and diagnostics.
"""

import os
import pytest
import uuid
import httpx


BASE_URL = os.getenv("BASE_URL", "http://0.0.0.0:8000")


async def create_user_and_login():
    """Helper function to create a user and get auth headers"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        email = f"test_{uuid.uuid4().hex[:12]}@test.com"
        password = "SecurePassword123!"

        signup_response = await client.post(
            "/v1/auth/signup", json={"email": email, "password": password}
        )
        assert signup_response.status_code == 201
        user_data = signup_response.json()

        login_response = await client.post(
            "/v1/auth/login", json={"email": email, "password": password}
        )
        assert login_response.status_code == 200
        token_data = login_response.json()

        return {
            "user": user_data,
            "headers": {"Authorization": f"Bearer {token_data['access_token']}"},
            "token": token_data['access_token']
        }


@pytest.mark.asyncio
class TestDebugAPI:
    """Test debug endpoints"""

    async def test_system_info(self):
        """Test getting system information"""
        auth_data = await create_user_and_login()
        auth_headers = auth_data["headers"]

        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            response = await client.get(
                "/v1/debug/system-info",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert "python_version" in data
            assert "platform" in data
            assert "memory_usage" in data

    async def test_database_status(self):
        """Test database status check"""
        auth_data = await create_user_and_login()
        auth_headers = auth_data["headers"]

        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            response = await client.get(
                "/v1/debug/database-status",
                headers=auth_headers
            )

            if response.status_code != 200:
                print(f"Response status: {response.status_code}")
                print(f"Response content: {response.text}")

            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "connection_pool" in data

    async def test_logs(self):
        """Test getting application logs"""
        auth_data = await create_user_and_login()
        auth_headers = auth_data["headers"]

        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            response = await client.get(
                "/v1/debug/logs?limit=10",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    async def test_unauthorized_access(self):
        """Test unauthorized access to debug endpoints"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            endpoints = [
                "/v1/debug/system-info",
                "/v1/debug/database-status",
                "/v1/debug/logs",
            ]

            for endpoint in endpoints:
                response = await client.get(endpoint)
                assert response.status_code == 401
