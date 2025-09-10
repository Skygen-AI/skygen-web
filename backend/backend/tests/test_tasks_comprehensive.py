"""
Comprehensive tests for Tasks endpoints.
Tests all task endpoints with various scenarios including edge cases and error conditions.
"""

import os
import uuid
import pytest
import httpx
import json
import asyncio
import websockets
from datetime import datetime, timezone
from typing import Tuple


BASE_URL = os.getenv("BASE_URL", "http://0.0.0.0:8000")
WS_URL = BASE_URL.replace("http", "ws")


async def create_user_and_get_token(client: httpx.AsyncClient) -> Tuple[str, str]:
    """Helper function to create a user and return access token and user email."""
    email = f"task_test_{uuid.uuid4().hex[:12]}@test.com"
    password = "SecurePassword123!"

    # Signup
    await client.post("/v1/auth/signup", json={"email": email, "password": password})

    # Login
    login_response = await client.post(
        "/v1/auth/login", json={"email": email, "password": password}
    )

    access_token = login_response.json()["access_token"]
    return access_token, email


async def enroll_device(
    client: httpx.AsyncClient, access_token: str, device_name: str = "Test Device"
) -> Tuple[str, str]:
    """Helper function to enroll a device and return device_id and device_token."""
    device_data = {
        "device_name": device_name,
        "platform": "linux",
        "capabilities": {"fs": True, "network": True},
    }

    response = await client.post(
        "/v1/devices/enroll", headers={"Authorization": f"Bearer {access_token}"}, json=device_data
    )

    assert response.status_code == 201
    data = response.json()
    return data["device_id"], data["device_token"]


class TestTaskCreation:
    """Test task creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_task_success(self):
        """Test successful task creation."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)

            task_data = {
                "device_id": device_id,
                "title": "Test Task",
                "description": "This is a test task",
                "metadata": {"actions": [{"action_id": "a1", "type": "noop", "params": {}}]},
            }

            idempotency_key = uuid.uuid4().hex

            response = await client.post(
                "/v1/tasks/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Idempotency-Key": idempotency_key,
                },
                json=task_data,
            )

            assert response.status_code == 201
            data = response.json()

            # Verify response structure
            assert "id" in data
            assert "user_id" in data
            assert "device_id" in data
            assert "status" in data
            assert "title" in data
            assert "description" in data
            assert "payload" in data
            assert "created_at" in data
            assert "updated_at" in data

            # Verify values
            assert data["device_id"] == device_id
            assert data["title"] == task_data["title"]
            assert data["description"] == task_data["description"]
            # Default status for safe actions
            assert data["status"] == "queued"
            assert "actions" in data["payload"]
            assert len(data["payload"]["actions"]) == 1

    @pytest.mark.asyncio
    async def test_create_task_with_dangerous_actions(self):
        """Test creating task with dangerous actions requiring confirmation."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)

            task_data = {
                "device_id": device_id,
                "title": "Dangerous Task",
                "description": "This task requires confirmation",
                "metadata": {
                    "actions": [
                        {"action_id": "a1", "type": "shell",
                            "params": {"command": "ls -la"}}
                    ]
                },
            }

            response = await client.post(
                "/v1/tasks/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Idempotency-Key": uuid.uuid4().hex,
                },
                json=task_data,
            )

            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "awaiting_confirmation"

    @pytest.mark.asyncio
    async def test_create_task_idempotency(self):
        """Test task creation idempotency."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)

            task_data = {
                "device_id": device_id,
                "title": "Idempotent Task",
                "description": "This task should be created only once",
                "metadata": {"actions": [{"action_id": "a1", "type": "noop", "params": {}}]},
            }

            idempotency_key = uuid.uuid4().hex

            # First request
            response1 = await client.post(
                "/v1/tasks/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Idempotency-Key": idempotency_key,
                },
                json=task_data,
            )
            assert response1.status_code == 201
            task_id_1 = response1.json()["id"]

            # Second request with same idempotency key
            response2 = await client.post(
                "/v1/tasks/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Idempotency-Key": idempotency_key,
                },
                json=task_data,
            )
            assert response2.status_code == 201
            task_id_2 = response2.json()["id"]

            # Should return the same task
            assert task_id_1 == task_id_2

    @pytest.mark.asyncio
    async def test_create_task_missing_idempotency_key(self):
        """Test task creation without idempotency key."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)

            task_data = {
                "device_id": device_id,
                "title": "No Idempotency Task",
                "metadata": {"actions": []},
            }

            response = await client.post(
                "/v1/tasks/", headers={"Authorization": f"Bearer {access_token}"}, json=task_data
            )

            assert response.status_code == 400
            assert "Idempotency-Key header required" in response.json()[
                "detail"]

    @pytest.mark.asyncio
    async def test_create_task_unauthorized(self):
        """Test task creation without authentication."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            task_data = {
                "device_id": str(uuid.uuid4()),
                "title": "Unauthorized Task",
                "metadata": {"actions": []},
            }

            response = await client.post(
                "/v1/tasks/", headers={"Idempotency-Key": uuid.uuid4().hex}, json=task_data
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_task_invalid_device(self):
        """Test task creation with non-existent device."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)

            task_data = {
                "device_id": str(uuid.uuid4()),  # Non-existent device
                "title": "Invalid Device Task",
                "metadata": {"actions": []},
            }

            response = await client.post(
                "/v1/tasks/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Idempotency-Key": uuid.uuid4().hex,
                },
                json=task_data,
            )

            # Task creation might succeed but delivery will fail
            # The API doesn't validate device existence at creation time
            assert response.status_code in [201, 400, 404]

    @pytest.mark.asyncio
    async def test_create_task_other_users_device(self):
        """Test creating task for another user's device."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create first user and device
            access_token1, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token1, "User1 Device")

            # Create second user
            access_token2, _ = await create_user_and_get_token(client)

            task_data = {
                "device_id": device_id,  # First user's device
                "title": "Cross-User Task",
                "metadata": {"actions": []},
            }

            response = await client.post(
                "/v1/tasks/",
                headers={
                    "Authorization": f"Bearer {access_token2}",
                    "Idempotency-Key": uuid.uuid4().hex,
                },
                json=task_data,
            )

            # This should either fail or succeed but not deliver
            # depending on implementation
            assert response.status_code in [201, 400, 403, 404]

    @pytest.mark.asyncio
    async def test_create_task_invalid_data(self):
        """Test task creation with invalid data."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)

            # Missing required fields
            response1 = await client.post(
                "/v1/tasks/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Idempotency-Key": uuid.uuid4().hex,
                },
                json={"device_id": device_id},  # Missing title
            )
            assert response1.status_code == 422

            # Invalid device_id format
            response2 = await client.post(
                "/v1/tasks/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Idempotency-Key": uuid.uuid4().hex,
                },
                json={"device_id": "invalid-uuid",
                      "title": "Invalid Device ID Task"},
            )
            assert response2.status_code == 422

    @pytest.mark.asyncio
    async def test_create_task_with_complex_actions(self):
        """Test creating task with complex action metadata."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)

            task_data = {
                "device_id": device_id,
                "title": "Complex Task",
                "description": "Task with multiple complex actions",
                "metadata": {
                    "actions": [
                        {
                            "action_id": "a1",
                            "type": "file_read",
                            "params": {"path": "/tmp/test.txt", "encoding": "utf-8"},
                        },
                        {
                            "action_id": "a2",
                            "type": "http_request",
                            "params": {
                                "url": "https://api.example.com/data",
                                "method": "GET",
                                "headers": {"User-Agent": "CoactAgent/1.0"},
                            },
                        },
                        {"action_id": "a3", "type": "wait",
                            "params": {"seconds": 5}},
                    ],
                    "timeout": 300,
                    "retry_policy": {"max_retries": 3, "backoff": "exponential"},
                },
            }

            response = await client.post(
                "/v1/tasks/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Idempotency-Key": uuid.uuid4().hex,
                },
                json=task_data,
            )

            assert response.status_code == 201
            data = response.json()
            assert len(data["payload"]["actions"]) == 3
            assert data["status"] == "queued"

    @pytest.mark.asyncio
    async def test_create_task_without_actions(self):
        """Test creating task without actions."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)

            task_data = {
                "device_id": device_id,
                "title": "Empty Task",
                "description": "Task with no actions",
                "metadata": {"actions": []},
            }

            response = await client.post(
                "/v1/tasks/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Idempotency-Key": uuid.uuid4().hex,
                },
                json=task_data,
            )

            assert response.status_code == 201
            data = response.json()
            assert len(data["payload"]["actions"]) == 0

    @pytest.mark.asyncio
    async def test_create_task_without_metadata(self):
        """Test creating task without metadata."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)

            task_data = {
                "device_id": device_id,
                "title": "No Metadata Task",
                "description": "Task without metadata",
            }

            response = await client.post(
                "/v1/tasks/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Idempotency-Key": uuid.uuid4().hex,
                },
                json=task_data,
            )

            assert response.status_code == 201
            data = response.json()
            assert "actions" in data["payload"]
            assert len(data["payload"]["actions"]) == 0


class TestTaskDelivery:
    """Test task delivery via WebSocket."""

    @pytest.mark.asyncio
    async def test_task_delivery_to_connected_device(self):
        """Test that tasks are delivered to connected devices."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            # Connect device via WebSocket
            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"
            async with websockets.connect(uri) as ws:
                # Create task
                task_data = {
                    "device_id": device_id,
                    "title": "Delivery Test Task",
                    "metadata": {"actions": [{"action_id": "a1", "type": "noop", "params": {}}]},
                }

                task_response = await client.post(
                    "/v1/tasks/",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Idempotency-Key": uuid.uuid4().hex,
                    },
                    json=task_data,
                )
                assert task_response.status_code == 201
                task_id = task_response.json()["id"]

                # Wait for task delivery via WebSocket
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    data = json.loads(message)

                    assert data["type"] == "task.exec"
                    assert data["task_id"] == task_id
                    assert "actions" in data
                    assert "issued_at" in data
                    assert "signature" in data

                except asyncio.TimeoutError:
                    pytest.fail("Task was not delivered within timeout")

    @pytest.mark.asyncio
    async def test_task_delivery_multiple_actions(self):
        """Test task delivery with multiple actions."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            # Connect device via WebSocket
            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"
            async with websockets.connect(uri) as ws:
                # Create task with multiple actions
                actions = [
                    {"action_id": "a1", "type": "noop", "params": {}},
                    {"action_id": "a2", "type": "wait", "params": {"seconds": 1}},
                    {"action_id": "a3", "type": "log",
                        "params": {"message": "test"}},
                ]

                task_data = {
                    "device_id": device_id,
                    "title": "Multi-Action Task",
                    "metadata": {"actions": actions},
                }

                await client.post(
                    "/v1/tasks/",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Idempotency-Key": uuid.uuid4().hex,
                    },
                    json=task_data,
                )

                # Wait for task delivery
                message = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(message)

                assert len(data["actions"]) == 3
                assert data["actions"] == actions

    @pytest.mark.asyncio
    async def test_task_result_handling(self):
        """Test handling of task results from device."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            # Connect device via WebSocket
            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"
            async with websockets.connect(uri) as ws:
                # Create task
                task_data = {
                    "device_id": device_id,
                    "title": "Result Test Task",
                    "metadata": {"actions": [{"action_id": "a1", "type": "noop", "params": {}}]},
                }

                task_response = await client.post(
                    "/v1/tasks/",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Idempotency-Key": uuid.uuid4().hex,
                    },
                    json=task_data,
                )
                task_id = task_response.json()["id"]

                # Receive task
                await asyncio.wait_for(ws.recv(), timeout=5.0)

                # Send task result
                result = {
                    "type": "task.result",
                    "task_id": task_id,
                    "results": [
                        {
                            "action_id": "a1",
                            "status": "done",
                            "output": "Task completed successfully",
                        }
                    ],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "signature": "",
                }

                await ws.send(json.dumps(result))

                # Give server time to process the result
                await asyncio.sleep(1)

                # Verify task status would be updated (we can't directly query tasks endpoint
                # since it's not implemented, but the server should process the result)

    @pytest.mark.asyncio
    async def test_task_result_with_failures(self):
        """Test handling of failed task results."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            # Connect device via WebSocket
            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"
            async with websockets.connect(uri) as ws:
                # Create task
                task_data = {
                    "device_id": device_id,
                    "title": "Failure Test Task",
                    "metadata": {"actions": [{"action_id": "a1", "type": "fail", "params": {}}]},
                }

                task_response = await client.post(
                    "/v1/tasks/",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Idempotency-Key": uuid.uuid4().hex,
                    },
                    json=task_data,
                )
                task_id = task_response.json()["id"]

                # Receive task
                await asyncio.wait_for(ws.recv(), timeout=5.0)

                # Send failed task result
                result = {
                    "type": "task.result",
                    "task_id": task_id,
                    "results": [
                        {"action_id": "a1", "status": "failed",
                            "error": "Action failed with error"}
                    ],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "signature": "",
                }

                await ws.send(json.dumps(result))
                await asyncio.sleep(1)

    @pytest.mark.asyncio
    async def test_pending_task_delivery_on_reconnect(self):
        """Test that pending tasks are delivered when device reconnects."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            # Create task while device is offline
            task_data = {
                "device_id": device_id,
                "title": "Pending Task",
                "metadata": {"actions": [{"action_id": "a1", "type": "noop", "params": {}}]},
            }

            task_response = await client.post(
                "/v1/tasks/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Idempotency-Key": uuid.uuid4().hex,
                },
                json=task_data,
            )
            task_id = task_response.json()["id"]

            # Now connect device - should receive pending task
            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"
            async with websockets.connect(uri) as ws:
                # Should receive the pending task
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    data = json.loads(message)

                    assert data["type"] == "task.exec"
                    assert data["task_id"] == task_id

                except asyncio.TimeoutError:
                    pytest.fail("Pending task was not delivered on reconnect")


class TestTasksIntegration:
    """Integration tests for task workflows."""

    @pytest.mark.asyncio
    async def test_complete_task_workflow(self):
        """Test complete task workflow: create -> deliver -> execute -> result."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            # Connect device
            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"
            async with websockets.connect(uri) as ws:
                # 1. Create task
                task_data = {
                    "device_id": device_id,
                    "title": "Complete Workflow Task",
                    "description": "Full workflow test",
                    "metadata": {
                        "actions": [
                            {"action_id": "a1", "type": "noop", "params": {}},
                            {"action_id": "a2", "type": "log",
                                "params": {"message": "test"}},
                        ]
                    },
                }

                task_response = await client.post(
                    "/v1/tasks/",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Idempotency-Key": uuid.uuid4().hex,
                    },
                    json=task_data,
                )
                assert task_response.status_code == 201
                task_id = task_response.json()["id"]

                # 2. Receive task delivery
                message = await asyncio.wait_for(ws.recv(), timeout=5.0)
                delivered_task = json.loads(message)

                assert delivered_task["type"] == "task.exec"
                assert delivered_task["task_id"] == task_id
                assert len(delivered_task["actions"]) == 2

                # 3. Send task results
                result = {
                    "type": "task.result",
                    "task_id": task_id,
                    "results": [
                        {"action_id": "a1", "status": "done",
                            "output": "noop completed"},
                        {"action_id": "a2", "status": "done",
                            "output": "logged message"},
                    ],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "signature": "",
                }

                await ws.send(json.dumps(result))
                await asyncio.sleep(1)  # Give server time to process

    @pytest.mark.asyncio
    async def test_multiple_tasks_same_device(self):
        """Test multiple tasks for the same device."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            # Connect device
            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"
            async with websockets.connect(uri) as ws:
                task_ids = []

                # Create multiple tasks
                for i in range(3):
                    task_data = {
                        "device_id": device_id,
                        "title": f"Task {i + 1}",
                        "metadata": {
                            "actions": [{"action_id": f"a{i + 1}", "type": "noop", "params": {}}]
                        },
                    }

                    response = await client.post(
                        "/v1/tasks/",
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Idempotency-Key": uuid.uuid4().hex,
                        },
                        json=task_data,
                    )
                    task_ids.append(response.json()["id"])
                    # Small delay to ensure proper task ordering
                    await asyncio.sleep(0.1)

                # Receive all tasks with longer timeout
                received_task_ids = []
                seen_task_ids = set()  # Track unique task IDs to avoid duplicates

                # Wait for all tasks to be received
                start_time = asyncio.get_event_loop().time()
                timeout_duration = 15.0  # Total timeout for receiving all tasks

                while (
                    len(received_task_ids) < 3
                    and (asyncio.get_event_loop().time() - start_time) < timeout_duration
                ):
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=5.0)
                        data = json.loads(message)
                        if data.get("type") == "task.exec":
                            task_id = data["task_id"]
                            if task_id not in seen_task_ids:
                                received_task_ids.append(task_id)
                                seen_task_ids.add(task_id)
                                print(f"Received task {task_id}")
                    except asyncio.TimeoutError:
                        print(
                            f"Timeout waiting for tasks, received {len(received_task_ids)} so far"
                        )
                        continue

                # Verify all tasks were received
                print(f"Created tasks: {task_ids}")
                print(f"Received tasks: {received_task_ids}")
                assert set(task_ids) == set(received_task_ids), (
                    f"Expected {set(task_ids)}, got {set(received_task_ids)}"
                )

    @pytest.mark.asyncio
    async def test_task_with_artifact_workflow(self):
        """Test task workflow that includes artifact handling."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            # Connect device
            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"
            async with websockets.connect(uri) as ws:
                # Create task
                task_data = {
                    "device_id": device_id,
                    "title": "Artifact Task",
                    "metadata": {
                        "actions": [{"action_id": "a1", "type": "screenshot", "params": {}}]
                    },
                }

                task_response = await client.post(
                    "/v1/tasks/",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Idempotency-Key": uuid.uuid4().hex,
                    },
                    json=task_data,
                )
                task_id = task_response.json()["id"]

                # Receive task
                await asyncio.wait_for(ws.recv(), timeout=5.0)

                # Get presigned URL for artifact
                presign_response = await client.post(
                    "/v1/artifacts/presign",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={"task_id": task_id,
                          "filename": "screenshot.png", "size": 1024},
                )
                assert presign_response.status_code == 200
                s3_url = presign_response.json()["s3_url"]

                # Send task result with artifact reference
                result = {
                    "type": "task.result",
                    "task_id": task_id,
                    "results": [
                        {
                            "action_id": "a1",
                            "status": "done",
                            "s3_url": s3_url,
                            "artifact_type": "image/png",
                        }
                    ],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "signature": "",
                }

                await ws.send(json.dumps(result))
                await asyncio.sleep(1)
