"""
Comprehensive tests for admin API endpoints.

Tests admin-only functionality for system monitoring and management.
"""

import os
import pytest
import uuid
import httpx


BASE_URL = os.getenv("BASE_URL", "http://0.0.0.0:8000")


async def create_user_and_login(is_admin=False):
    """Helper function to create a user and get auth headers"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        email = f"test_{uuid.uuid4().hex[:12]}@test.com"
        if is_admin:
            email = f"admin_{uuid.uuid4().hex[:12]}@test.com"
        password = "SecurePassword123!"

        # Create user
        signup_response = await client.post(
            "/v1/auth/signup", json={"email": email, "password": password}
        )
        assert signup_response.status_code == 201
        user_data = signup_response.json()

        # Promote to admin if requested
        if is_admin:
            promote_response = await client.post(
                f"/v1/admin/users/{user_data['id']}/promote"
            )
            assert promote_response.status_code == 200

        # Login to get token
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


async def create_device(auth_headers):
    """Helper function to create a device"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        device_data = {
            "name": f"Test Device {uuid.uuid4().hex[:8]}",
            "device_type": "desktop",
            "os_type": "windows"
        }

        response = await client.post(
            "/v1/devices/",
            json=device_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        return response.json()


async def create_task(auth_headers, device_id):
    """Helper function to create a task"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        task_data = {
            "name": f"Test Task {uuid.uuid4().hex[:8]}",
            "actions": [
                {"action_id": "1", "type": "screenshot", "params": {}}
            ],
            "device_id": device_id
        }

        response = await client.post(
            "/v1/tasks/",
            json=task_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        return response.json()


@pytest.mark.asyncio
class TestAdminUsersAPI:
    """Test admin user management endpoints"""

    async def test_list_all_users_as_admin(self):
        """Test listing all users as admin"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create admin user
            admin_data = await create_user_and_login(is_admin=True)
            admin_headers = admin_data["headers"]

            # Create some regular users
            for _ in range(3):
                await create_user_and_login()

            response = await client.get(
                "/v1/admin/users",
                headers=admin_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert isinstance(data, list)
            assert len(data) >= 4  # At least admin + 3 users

            # Verify user data structure
            for user in data:
                assert "id" in user
                assert "email" in user
                assert "is_active" in user
                assert "created_at" in user

    async def test_list_users_unauthorized(self):
        """Test that non-admin users cannot list all users"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create regular user
            user_data = await create_user_and_login()
            user_headers = user_data["headers"]

            response = await client.get(
                "/v1/admin/users",
                headers=user_headers
            )

            assert response.status_code == 403
            assert "admin" in response.json()["detail"].lower()

    async def test_get_user_details_as_admin(self):
        """Test getting specific user details as admin"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create admin user
            admin_data = await create_user_and_login(is_admin=True)
            admin_headers = admin_data["headers"]

            # Create regular user
            user_data = await create_user_and_login()
            user_id = user_data["user"]["id"]

            response = await client.get(
                f"/v1/admin/users/{user_id}",
                headers=admin_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert data["id"] == user_id
            assert "email" in data
            assert "is_active" in data
            assert "created_at" in data

    async def test_deactivate_user_as_admin(self):
        """Test deactivating a user as admin"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create admin user
            admin_data = await create_user_and_login(is_admin=True)
            admin_headers = admin_data["headers"]

            # Create regular user
            user_data = await create_user_and_login()
            user_id = user_data["user"]["id"]

            response = await client.post(
                f"/v1/admin/users/{user_id}/deactivate",
                headers=admin_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "deactivated"


@pytest.mark.asyncio
class TestAdminSystemAPI:
    """Test admin system monitoring endpoints"""

    async def test_system_statistics(self):
        """Test getting system statistics"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create admin user
            admin_data = await create_user_and_login(is_admin=True)
            admin_headers = admin_data["headers"]

            response = await client.get(
                "/v1/admin/system/statistics",
                headers=admin_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert "total_users" in data
            assert "active_users" in data
            assert "total_devices" in data
            assert "total_tasks" in data

    async def test_system_health(self):
        """Test getting system health status"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create admin user
            admin_data = await create_user_and_login(is_admin=True)
            admin_headers = admin_data["headers"]

            response = await client.get(
                "/v1/admin/system/health",
                headers=admin_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert "database_status" in data
            assert "overall_health" in data

    async def test_unauthorized_admin_access(self):
        """Test that admin endpoints require authentication"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            admin_endpoints = [
                "/v1/admin/users",
                "/v1/admin/system/statistics",
                "/v1/admin/system/health",
            ]

            for endpoint in admin_endpoints:
                response = await client.get(endpoint)
                assert response.status_code == 401
