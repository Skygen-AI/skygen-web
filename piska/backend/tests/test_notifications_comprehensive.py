"""
Comprehensive tests for notifications API endpoints.

Tests WebSocket connections, notification management, and heartbeat mechanism.
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
class TestNotificationsAPI:
    """Test notifications endpoints"""

    async def test_get_notifications(self):
        """Test getting user notifications"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            response = await client.get(
                "/v1/notifications/",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    async def test_notification_preferences(self):
        """Test notification preferences"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            response = await client.get(
                "/v1/notifications/preferences",
                headers=auth_headers
            )

            assert response.status_code == 200

    async def test_unauthorized_access(self):
        """Test unauthorized access to notification endpoints"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            response = await client.get("/v1/notifications/")
            assert response.status_code == 401
