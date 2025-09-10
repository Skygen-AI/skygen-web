"""
Comprehensive tests for analytics API endpoints.

Tests performance analytics, device analytics, action performance, trends, and insights.
"""

import os
import pytest
import uuid
import httpx
from datetime import datetime, timedelta


BASE_URL = os.getenv("BASE_URL", "http://0.0.0.0:8000")


async def create_user_and_login():
    """Helper function to create a user and get auth headers"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        email = f"test_{uuid.uuid4().hex[:12]}@test.com"
        password = "SecurePassword123!"

        # Create user
        signup_response = await client.post(
            "/v1/auth/signup", json={"email": email, "password": password}
        )
        assert signup_response.status_code == 201
        user_data = signup_response.json()

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
            "title": f"Test Task {uuid.uuid4().hex[:8]}",
            "description": "Test task for analytics",
            "device_id": device_id,
            "metadata": {"test": True}
        }

        # Add required idempotency key
        headers = {**auth_headers, "Idempotency-Key": str(uuid.uuid4())}

        response = await client.post(
            "/v1/tasks/",
            json=task_data,
            headers=headers
        )
        assert response.status_code == 201
        return response.json()


@pytest.mark.asyncio
class TestAnalyticsAPI:
    """Test analytics endpoints"""

    async def test_get_performance_analytics(self):
        """Test getting performance analytics"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create some data for analytics
            device = await create_device(auth_headers)
            for _ in range(3):
                await create_task(auth_headers, device["id"])

            response = await client.get(
                "/v1/analytics/performance",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert "total_tasks" in data
            assert "success_rate" in data
            assert "average_execution_time" in data
            assert "tasks_per_day" in data

    async def test_get_device_analytics(self):
        """Test getting device analytics"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create devices
            devices = []
            for _ in range(3):
                device = await create_device(auth_headers)
                devices.append(device)

            response = await client.get(
                "/v1/analytics/devices",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert "total_devices" in data
            assert "online_devices" in data
            assert "device_types" in data
            assert "platform_distribution" in data

    async def test_get_action_analytics(self):
        """Test getting action analytics"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create device and tasks with different actions
            device = await create_device(auth_headers)

            # Create tasks with different action types
            action_types = ["screenshot", "click", "type_text"]
            for action_type in action_types:
                task_data = {
                    "title": f"Task with {action_type}",
                    "description": f"Test task with {action_type} action",
                    "device_id": device["id"],
                    "metadata": {"action_type": action_type}
                }

                # Add required idempotency key
                headers = {**auth_headers,
                           "Idempotency-Key": str(uuid.uuid4())}

                response = await client.post(
                    "/v1/tasks/",
                    json=task_data,
                    headers=headers
                )
                assert response.status_code == 201

            response = await client.get(
                "/v1/analytics/actions",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert "action_counts" in data
            assert "most_used_actions" in data
            assert "action_success_rates" in data

    async def test_get_trends_analytics(self):
        """Test getting trends analytics"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            response = await client.get(
                "/v1/analytics/trends",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert "daily_tasks" in data
            assert "weekly_tasks" in data
            assert "growth_rate" in data

    async def test_get_insights_analytics(self):
        """Test getting insights analytics"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            response = await client.get(
                "/v1/analytics/insights",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert "recommendations" in data
            assert "optimization_tips" in data
            assert "usage_patterns" in data

    async def test_analytics_with_date_filters(self):
        """Test analytics with date range filters"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create device and task
            device = await create_device(auth_headers)
            await create_task(auth_headers, device["id"])

            # Test with date filters
            start_date = (datetime.now() - timedelta(days=7)).isoformat()
            end_date = datetime.now().isoformat()

            response = await client.get(
                f"/v1/analytics/performance?start_date={start_date}&end_date={end_date}",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert "total_tasks" in data

    async def test_device_specific_analytics(self):
        """Test analytics for specific device"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create device and tasks
            device = await create_device(auth_headers)
            for _ in range(2):
                await create_task(auth_headers, device["id"])

            response = await client.get(
                f"/v1/analytics/devices/{device['id']}",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert "device_id" in data
            assert "total_tasks" in data
            assert "success_rate" in data
            assert "average_execution_time" in data

    async def test_analytics_export(self):
        """Test exporting analytics data"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            response = await client.get(
                "/v1/analytics/export?format=json",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert "performance" in data
            assert "devices" in data
            assert "actions" in data
            assert "export_timestamp" in data

    async def test_real_time_analytics(self):
        """Test real-time analytics endpoint"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            response = await client.get(
                "/v1/analytics/real-time",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert "active_tasks" in data
            assert "online_devices" in data
            assert "current_load" in data
            assert "last_updated" in data

    async def test_analytics_unauthorized(self):
        """Test that analytics endpoints require authentication"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            endpoints = [
                "/v1/analytics/performance",
                "/v1/analytics/devices",
                "/v1/analytics/actions",
                "/v1/analytics/trends",
                "/v1/analytics/insights",
                "/v1/analytics/real-time",
            ]

            for endpoint in endpoints:
                response = await client.get(endpoint)
                assert response.status_code == 401

    async def test_analytics_cross_user_isolation(self):
        """Test that users only see their own analytics data"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create first user and data
            auth_data1 = await create_user_and_login()
            auth_headers1 = auth_data1["headers"]
            device1 = await create_device(auth_headers1)
            await create_task(auth_headers1, device1["id"])

            # Create second user
            auth_data2 = await create_user_and_login()
            auth_headers2 = auth_data2["headers"]

            # Get analytics for first user
            response1 = await client.get(
                "/v1/analytics/performance",
                headers=auth_headers1
            )
            assert response1.status_code == 200
            data1 = response1.json()

            # Get analytics for second user
            response2 = await client.get(
                "/v1/analytics/performance",
                headers=auth_headers2
            )
            assert response2.status_code == 200
            data2 = response2.json()

            # Second user should have no tasks
            assert data2["total_tasks"] == 0
            assert data1["total_tasks"] >= 1


@pytest.mark.asyncio
class TestAnalyticsIntegration:
    """Integration tests for analytics"""

    async def test_comprehensive_analytics_flow(self):
        """Test complete analytics workflow"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create multiple devices
            devices = []
            for _ in range(3):
                device = await create_device(auth_headers)
                devices.append(device)

            # Create tasks across devices
            tasks = []
            for device in devices:
                for _ in range(2):
                    task = await create_task(auth_headers, device["id"])
                    tasks.append(task)

            # Get comprehensive analytics
            analytics_endpoints = [
                "/v1/analytics/performance",
                "/v1/analytics/devices",
                "/v1/analytics/actions",
                "/v1/analytics/trends",
                "/v1/analytics/insights"
            ]

            for endpoint in analytics_endpoints:
                response = await client.get(endpoint, headers=auth_headers)
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, dict)

    async def test_analytics_performance_under_load(self):
        """Test analytics performance with larger dataset"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create devices and tasks
            device = await create_device(auth_headers)

            # Create multiple tasks
            for _ in range(10):
                await create_task(auth_headers, device["id"])

            # Test analytics performance
            response = await client.get(
                "/v1/analytics/performance",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_tasks"] >= 10

    async def test_analytics_data_consistency(self):
        """Test analytics data consistency across endpoints"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create device and tasks
            device = await create_device(auth_headers)
            task_count = 5

            for _ in range(task_count):
                await create_task(auth_headers, device["id"])

            # Get performance analytics
            perf_response = await client.get(
                "/v1/analytics/performance",
                headers=auth_headers
            )
            assert perf_response.status_code == 200
            perf_data = perf_response.json()

            # Get device analytics
            device_response = await client.get(
                "/v1/analytics/devices",
                headers=auth_headers
            )
            assert device_response.status_code == 200
            device_data = device_response.json()

            # Data should be consistent
            assert perf_data["total_tasks"] >= task_count
            assert device_data["total_devices"] >= 1
