"""
Comprehensive tests for user profile (me) API endpoints.

Tests user profile information, activity tracking, and data isolation.
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
class TestMeAPI:
    """Test user profile endpoints"""

    async def test_get_profile(self):
        """Test getting user profile"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            response = await client.get(
                "/v1/me/profile",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "email" in data
            assert "created_at" in data
            assert data["email"] == auth_data["user"]["email"]

    async def test_update_profile(self):
        """Test updating user profile"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            update_data = {
                "display_name": "Updated Name",
                "preferences": {
                    "theme": "dark",
                    "notifications": True
                }
            }

            response = await client.put(
                "/v1/me/profile",
                json=update_data,
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["display_name"] == "Updated Name"

    async def test_get_activity(self):
        """Test getting user activity"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            response = await client.get(
                "/v1/me/activity",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert "recent_tasks" in data
            assert "total_tasks" in data
            assert "last_login" in data

    async def test_get_statistics(self):
        """Test getting user statistics"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            response = await client.get(
                "/v1/me/statistics",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert "total_devices" in data
            assert "total_tasks" in data
            assert "success_rate" in data

    async def test_unauthorized_access(self):
        """Test unauthorized access to profile endpoints"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            endpoints = [
                ("GET", "/v1/me/profile"),
                ("PUT", "/v1/me/profile"),
                ("GET", "/v1/me/activity"),
                ("GET", "/v1/me/statistics"),
            ]

            for method, url in endpoints:
                response = await client.request(method, url)
                assert response.status_code == 401