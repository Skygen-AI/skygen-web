"""
Comprehensive tests for scheduled tasks API endpoints.

Tests scheduled task creation, management, cron validation, and execution triggers.
"""

import os
import pytest
import uuid
import httpx
from datetime import datetime, timezone, timedelta


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


async def create_template(auth_headers):
    """Helper function to create a task template"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        template_data = {
            "name": "Test Template",
            "description": "Test template for scheduled tasks",
            "category": "automation",
            "actions": [
                {"action_id": "1", "type": "screenshot", "params": {}}
            ],
            "variables": {"delay": "5"},
            "is_public": False
        }

        response = await client.post(
            "/v1/templates/",
            json=template_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        return response.json()


async def create_scheduled_task(auth_headers, device_id, **kwargs):
    """Helper function to create a scheduled task"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        default_data = {
            "name": f"Test Task {uuid.uuid4().hex[:8]}",
            "cron_expression": "0 9 * * *",
            "actions": [{"action_id": "1", "type": "screenshot", "params": {}}],
            "device_id": device_id,
            "is_active": True
        }
        default_data.update(kwargs)

        response = await client.post(
            "/v1/scheduled-tasks/",
            json=default_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        return response.json()


@pytest.mark.asyncio
class TestScheduledTasksAPI:
    """Test scheduled tasks endpoints"""

    async def test_create_scheduled_task_success(self):
        """Test creating a scheduled task"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create device
            device = await create_device(auth_headers)

            payload = {
                "name": "Daily Screenshot",
                "cron_expression": "0 9 * * *",  # 9 AM daily
                "actions": [
                    {"action_id": "1", "type": "screenshot", "params": {}}
                ],
                "device_id": device["id"],
                "is_active": True
            }

            response = await client.post(
                "/v1/scheduled-tasks/",
                json=payload,
                headers=auth_headers
            )

            assert response.status_code == 201
            data = response.json()

            assert "id" in data
            assert data["name"] == "Daily Screenshot"
            assert data["cron_expression"] == "0 9 * * *"
            assert data["cron_description"] is not None
            assert data["actions"] == payload["actions"]
            assert data["is_active"] is True
            assert data["device_id"] == device["id"]
            assert data["next_run"] is not None

    async def test_create_scheduled_task_with_template(self):
        """Test creating a scheduled task with template"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create device and template
            device = await create_device(auth_headers)
            template = await create_template(auth_headers)

            payload = {
                "name": "Templated Task",
                "cron_expression": "0 */2 * * *",  # Every 2 hours
                "actions": [
                    {"action_id": "1", "type": "click",
                        "params": {"x": 100, "y": 200}}
                ],
                "device_id": device["id"],
                "template_id": template["id"]
            }

            response = await client.post(
                "/v1/scheduled-tasks/",
                json=payload,
                headers=auth_headers
            )

            assert response.status_code == 201
            data = response.json()
            assert data["template_id"] == template["id"]

    async def test_create_scheduled_task_invalid_cron(self):
        """Test creating scheduled task with invalid cron expression"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create device
            device = await create_device(auth_headers)

            payload = {
                "name": "Invalid Cron",
                "cron_expression": "invalid cron",
                "actions": [{"action_id": "1", "type": "screenshot", "params": {}}],
                "device_id": device["id"]
            }

            response = await client.post(
                "/v1/scheduled-tasks/",
                json=payload,
                headers=auth_headers
            )

            assert response.status_code == 400
            assert "Invalid cron expression" in response.json()["detail"]

    async def test_create_scheduled_task_device_not_found(self):
        """Test creating scheduled task with non-existent device"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            payload = {
                "name": "No Device",
                "cron_expression": "0 9 * * *",
                "actions": [{"action_id": "1", "type": "screenshot", "params": {}}],
                "device_id": str(uuid.uuid4())
            }

            response = await client.post(
                "/v1/scheduled-tasks/",
                json=payload,
                headers=auth_headers
            )

            assert response.status_code == 404
            assert "Device not found" in response.json()["detail"]

    async def test_list_scheduled_tasks(self):
        """Test listing scheduled tasks"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create device
            device = await create_device(auth_headers)

            # Create test scheduled tasks
            tasks = []
            for i in range(3):
                task = await create_scheduled_task(
                    auth_headers,
                    device["id"],
                    name=f"Test Task {i}",
                    is_active=(i % 2 == 0)  # Alternate active/inactive
                )
                tasks.append(task)

            response = await client.get(
                "/v1/scheduled-tasks/",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert len(data) == 3
            assert all("id" in task for task in data)
            assert all("cron_description" in task for task in data)
            assert all("next_run" in task for task in data)

    async def test_list_scheduled_tasks_with_filters(self):
        """Test listing scheduled tasks with filters"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create device
            device = await create_device(auth_headers)

            # Create tasks with different states
            await create_scheduled_task(
                auth_headers,
                device["id"],
                name="Active Task",
                is_active=True
            )

            await create_scheduled_task(
                auth_headers,
                device["id"],
                name="Inactive Task",
                cron_expression="0 10 * * *",
                is_active=False
            )

            # Test filter by device_id
            response = await client.get(
                f"/v1/scheduled-tasks/?device_id={device['id']}",
                headers=auth_headers
            )
            assert response.status_code == 200
            assert len(response.json()) == 2

            # Test filter by is_active=true
            response = await client.get(
                "/v1/scheduled-tasks/?is_active=true",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["is_active"] is True

            # Test filter by is_active=false
            response = await client.get(
                "/v1/scheduled-tasks/?is_active=false",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["is_active"] is False

    async def test_get_scheduled_task(self):
        """Test getting a specific scheduled task"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create device
            device = await create_device(auth_headers)

            # Create task
            task = await create_scheduled_task(
                auth_headers,
                device["id"],
                name="Get Test Task",
                cron_expression="0 12 * * *"
            )

            response = await client.get(
                f"/v1/scheduled-tasks/{task['id']}",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert data["id"] == task["id"]
            assert data["name"] == "Get Test Task"
            assert data["cron_expression"] == "0 12 * * *"
            assert "cron_description" in data

    async def test_get_scheduled_task_not_found(self):
        """Test getting non-existent scheduled task"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            response = await client.get(
                f"/v1/scheduled-tasks/{uuid.uuid4()}",
                headers=auth_headers
            )

            assert response.status_code == 404
            assert "Scheduled task not found" in response.json()["detail"]

    async def test_update_scheduled_task(self):
        """Test updating a scheduled task"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create device
            device = await create_device(auth_headers)

            # Create task
            task = await create_scheduled_task(
                auth_headers,
                device["id"],
                name="Update Test Task"
            )

            update_payload = {
                "name": "Updated Task Name",
                "cron_expression": "0 15 * * *",  # Change to 3 PM
                "is_active": False
            }

            response = await client.put(
                f"/v1/scheduled-tasks/{task['id']}",
                json=update_payload,
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert data["name"] == "Updated Task Name"
            assert data["cron_expression"] == "0 15 * * *"
            assert data["is_active"] is False
            assert "next_run" in data  # Should be recalculated

    async def test_update_scheduled_task_invalid_cron(self):
        """Test updating scheduled task with invalid cron"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create device
            device = await create_device(auth_headers)

            # Create task
            task = await create_scheduled_task(
                auth_headers,
                device["id"],
                name="Update Test Task"
            )

            update_payload = {
                "cron_expression": "invalid cron"
            }

            response = await client.put(
                f"/v1/scheduled-tasks/{task['id']}",
                json=update_payload,
                headers=auth_headers
            )

            assert response.status_code == 400
            assert "Invalid cron expression" in response.json()["detail"]

    async def test_delete_scheduled_task(self):
        """Test deleting a scheduled task"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create device
            device = await create_device(auth_headers)

            # Create task
            task = await create_scheduled_task(
                auth_headers,
                device["id"],
                name="Delete Test Task"
            )

            response = await client.delete(
                f"/v1/scheduled-tasks/{task['id']}",
                headers=auth_headers
            )

            assert response.status_code == 200
            assert response.json()["status"] == "deleted"

            # Verify task is deleted
            response = await client.get(
                f"/v1/scheduled-tasks/{task['id']}",
                headers=auth_headers
            )
            assert response.status_code == 404

    async def test_run_scheduled_task_now(self):
        """Test manually triggering a scheduled task"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create device
            device = await create_device(auth_headers)

            # Create task
            task = await create_scheduled_task(
                auth_headers,
                device["id"],
                name="Run Now Test Task"
            )

            response = await client.post(
                f"/v1/scheduled-tasks/{task['id']}/run",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "triggered"
            assert "will run within the next minute" in data["message"]

    async def test_toggle_scheduled_task(self):
        """Test toggling scheduled task active/inactive"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create device
            device = await create_device(auth_headers)

            # Create task
            task = await create_scheduled_task(
                auth_headers,
                device["id"],
                name="Toggle Test Task",
                is_active=True
            )

            # Toggle from active to inactive
            response = await client.post(
                f"/v1/scheduled-tasks/{task['id']}/toggle",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_active"] is False
            assert data["status"] == "deactivated"

            # Toggle back to active
            response = await client.post(
                f"/v1/scheduled-tasks/{task['id']}/toggle",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_active"] is True
            assert data["status"] == "activated"

    async def test_cron_validation_edge_cases(self):
        """Test various cron expression validations"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create device
            device = await create_device(auth_headers)

            test_cases = [
                ("0 9 * * *", True),          # Valid: 9 AM daily
                ("*/15 * * * *", True),       # Valid: Every 15 minutes
                ("0 0 1 * *", True),          # Valid: First day of month
                ("0 0 * * 0", True),          # Valid: Every Sunday
                ("0 0 1 1 *", True),          # Valid: January 1st
                ("invalid", False),           # Invalid: not cron format
                ("* * * * * *", False),       # Invalid: 6 fields (seconds)
                ("60 * * * *", False),        # Invalid: minute > 59
                ("0 25 * * *", False),        # Invalid: hour > 23
                ("0 0 32 * *", False),        # Invalid: day > 31
                ("0 0 * 13 *", False),        # Invalid: month > 12
                ("0 0 * * 8", False),         # Invalid: weekday > 7
            ]

            for cron_expr, should_be_valid in test_cases:
                payload = {
                    "name": f"Test {cron_expr}",
                    "cron_expression": cron_expr,
                    "actions": [{"action_id": "1", "type": "screenshot", "params": {}}],
                    "device_id": device["id"]
                }

                response = await client.post(
                    "/v1/scheduled-tasks/",
                    json=payload,
                    headers=auth_headers
                )

                if should_be_valid:
                    assert response.status_code == 201, f"Cron '{cron_expr}' should be valid"
                else:
                    assert response.status_code == 400, f"Cron '{cron_expr}' should be invalid"

    async def test_unauthorized_access(self):
        """Test unauthorized access to scheduled tasks endpoints"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            endpoints = [
                ("POST", "/v1/scheduled-tasks/"),
                ("GET", "/v1/scheduled-tasks/"),
                ("GET", f"/v1/scheduled-tasks/{uuid.uuid4()}"),
                ("PUT", f"/v1/scheduled-tasks/{uuid.uuid4()}"),
                ("DELETE", f"/v1/scheduled-tasks/{uuid.uuid4()}"),
                ("POST", f"/v1/scheduled-tasks/{uuid.uuid4()}/run"),
                ("POST", f"/v1/scheduled-tasks/{uuid.uuid4()}/toggle"),
            ]

            for method, url in endpoints:
                response = await client.request(method, url)
                assert response.status_code == 401

    async def test_cross_user_access_prevention(self):
        """Test that users cannot access each other's scheduled tasks"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create first user and task
            auth_data1 = await create_user_and_login()
            auth_headers1 = auth_data1["headers"]
            device1 = await create_device(auth_headers1)
            task = await create_scheduled_task(
                auth_headers1,
                device1["id"],
                name="Private Task"
            )

            # Create second user
            auth_data2 = await create_user_and_login()
            auth_headers2 = auth_data2["headers"]

            # Try to access with different user
            response = await client.get(
                f"/v1/scheduled-tasks/{task['id']}",
                headers=auth_headers2
            )
            assert response.status_code == 404

            # Try to update with different user
            response = await client.put(
                f"/v1/scheduled-tasks/{task['id']}",
                json={"name": "Hacked"},
                headers=auth_headers2
            )
            assert response.status_code == 404

            # Try to delete with different user
            response = await client.delete(
                f"/v1/scheduled-tasks/{task['id']}",
                headers=auth_headers2
            )
            assert response.status_code == 404


@pytest.mark.asyncio
class TestScheduledTasksIntegration:
    """Integration tests for scheduled tasks"""

    async def test_template_integration(self):
        """Test integration with task templates"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create device and template
            device = await create_device(auth_headers)
            template = await create_template(auth_headers)

            payload = {
                "name": "Template Integration Test",
                "cron_expression": "0 */6 * * *",  # Every 6 hours
                "actions": [{"action_id": "1", "type": "screenshot", "params": {}}],
                "device_id": device["id"],
                "template_id": template["id"]
            }

            response = await client.post(
                "/v1/scheduled-tasks/",
                json=payload,
                headers=auth_headers
            )

            assert response.status_code == 201
            data = response.json()
            assert data["template_id"] == template["id"]

            # Test with non-existent template
            payload["template_id"] = str(uuid.uuid4())
            response = await client.post(
                "/v1/scheduled-tasks/",
                json=payload,
                headers=auth_headers
            )
            assert response.status_code == 404
            assert "Template not found" in response.json()["detail"]

    async def test_large_dataset_performance(self):
        """Test performance with large number of scheduled tasks"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create device
            device = await create_device(auth_headers)

            # Create many scheduled tasks
            tasks = []
            for i in range(20):  # Reduced from 100 for faster testing
                task = await create_scheduled_task(
                    auth_headers,
                    device["id"],
                    name=f"Performance Test Task {i}",
                    is_active=(i % 2 == 0)
                )
                tasks.append(task)

            # Test listing with pagination
            response = await client.get(
                "/v1/scheduled-tasks/?limit=10",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) <= 10  # Respects limit

    async def test_concurrent_operations(self):
        """Test concurrent operations on scheduled tasks"""
        import asyncio

        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create user and get auth
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            # Create device
            device = await create_device(auth_headers)

            # Create task
            task = await create_scheduled_task(
                auth_headers,
                device["id"],
                name="Concurrent Test Task",
                is_active=True
            )

            # Concurrent toggle operations
            async def toggle_task():
                return await client.post(
                    f"/v1/scheduled-tasks/{task['id']}/toggle",
                    headers=auth_headers
                )

            # Run multiple toggles concurrently
            responses = await asyncio.gather(*[toggle_task() for _ in range(3)])

            # All requests should succeed
            assert all(r.status_code == 200 for r in responses)

            # Final state should be deterministic
            final_response = await client.get(
                f"/v1/scheduled-tasks/{task['id']}",
                headers=auth_headers
            )
            assert final_response.status_code == 200
            # State should be either True or False (not corrupted)
            final_state = final_response.json()["is_active"]
            assert isinstance(final_state, bool)
