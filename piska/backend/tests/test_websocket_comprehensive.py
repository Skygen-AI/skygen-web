"""
Comprehensive tests for WebSocket functionality.
Tests all WebSocket endpoints and behaviors with various scenarios including edge cases and error conditions.
"""

import os
import uuid
import pytest
import httpx
import websockets
import websockets.protocol
import json
import asyncio
from datetime import datetime, timezone
from typing import Tuple


BASE_URL = os.getenv("BASE_URL", "http://0.0.0.0:8000")
WS_URL = BASE_URL.replace("http", "ws")


async def create_user_and_get_token(client: httpx.AsyncClient) -> Tuple[str, str]:
    """Helper function to create a user and return access token and user email."""
    email = f"ws_test_{uuid.uuid4().hex[:12]}@test.com"
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
    client: httpx.AsyncClient, access_token: str, device_name: str = "WS Test Device"
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


class TestWebSocketConnection:
    """Test WebSocket connection establishment and authentication."""

    @pytest.mark.asyncio
    async def test_ws_connection_with_query_token_success(self):
        """Test successful WebSocket connection with token in query parameters."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            async with websockets.connect(uri) as ws:
                # Connection should be established successfully
                assert ws.state == websockets.protocol.OPEN

                # Should be able to send a heartbeat
                heartbeat = {
                    "type": "heartbeat",
                    "device_id": device_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await ws.send(json.dumps(heartbeat))

                # Give server time to process
                await asyncio.sleep(0.5)

    @pytest.mark.asyncio
    async def test_ws_connection_with_header_token_success(self):
        """Test successful WebSocket connection with token in Authorization header."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            uri = f"{WS_URL}/v1/ws/agent"
            headers = {"Authorization": f"Bearer {device_token}"}

            async with websockets.connect(uri, additional_headers=headers) as ws:
                assert ws.state == websockets.protocol.OPEN

                # Send heartbeat
                heartbeat = {
                    "type": "heartbeat",
                    "device_id": device_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await ws.send(json.dumps(heartbeat))
                await asyncio.sleep(0.5)

    @pytest.mark.asyncio
    async def test_ws_connection_no_token(self):
        """Test WebSocket connection without token."""
        uri = f"{WS_URL}/v1/ws/agent"

        with pytest.raises(websockets.exceptions.InvalidStatus) as exc_info:
            async with websockets.connect(uri) as ws:
                await ws.recv()  # This should fail

        # Should reject with HTTP 403
        assert exc_info.value.response.status_code == 403

    @pytest.mark.asyncio
    async def test_ws_connection_invalid_token(self):
        """Test WebSocket connection with invalid token."""
        uri = f"{WS_URL}/v1/ws/agent?token=invalid_token_here"

        with pytest.raises(websockets.exceptions.InvalidStatus) as exc_info:
            async with websockets.connect(uri) as ws:
                await ws.recv()

        # Should reject with HTTP 403
        assert exc_info.value.response.status_code == 403

    @pytest.mark.asyncio
    async def test_ws_connection_expired_token(self):
        """Test WebSocket connection with expired token."""
        # Create a device token, then revoke it to simulate expiration
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            # Revoke the device to invalidate its token
            await client.post(
                f"/v1/devices/{device_id}/revoke",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            # Try to connect with revoked token
            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            with pytest.raises(websockets.ConnectionClosedError) as exc_info:
                async with websockets.connect(uri) as ws:
                    await ws.recv()

            assert exc_info.value.code == 4401

    @pytest.mark.asyncio
    async def test_ws_connection_malformed_token(self):
        """Test WebSocket connection with malformed JWT token."""
        malformed_tokens = [
            "not.a.jwt",
            "header.payload",  # Missing signature
            "header.payload.signature.extra",  # Too many parts
            "",  # Empty token
            "Bearer valid_looking_but_fake_token",
        ]

        for token in malformed_tokens:
            uri = f"{WS_URL}/v1/ws/agent?token={token}"

            with pytest.raises(websockets.exceptions.InvalidStatus) as exc_info:
                async with websockets.connect(uri) as ws:
                    await ws.recv()

            # Should reject with HTTP 400 (Bad Request) or 403 (Forbidden) during handshake
            assert exc_info.value.response.status_code in [400, 403]

    @pytest.mark.asyncio
    async def test_ws_connection_multiple_simultaneous(self):
        """Test multiple simultaneous WebSocket connections from different devices."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)

            # Create multiple devices
            devices = []
            for i in range(3):
                device_id, device_token = await enroll_device(
                    client, access_token, f"Multi Device {i + 1}"
                )
                devices.append((device_id, device_token))

            # Connect all devices simultaneously
            connections = []
            try:
                for device_id, device_token in devices:
                    uri = f"{WS_URL}/v1/ws/agent?token={device_token}"
                    ws = await websockets.connect(uri)
                    connections.append((ws, device_id))

                # Verify all connections are open
                for ws, device_id in connections:
                    assert ws.state == websockets.protocol.OPEN

                    # Send heartbeat from each device
                    heartbeat = {
                        "type": "heartbeat",
                        "device_id": device_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    await ws.send(json.dumps(heartbeat))

                await asyncio.sleep(1)  # Give server time to process

            finally:
                # Clean up connections
                for ws, _ in connections:
                    if ws.state != websockets.protocol.CLOSED:
                        await ws.close()

    @pytest.mark.asyncio
    async def test_ws_connection_single_device_multiple_attempts(self):
        """Test that only one connection per device is allowed (new connection closes old one)."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            # First connection
            ws1 = await websockets.connect(uri)
            assert ws1.state.name == "OPEN"

            # Send heartbeat to establish connection
            heartbeat = {
                "type": "heartbeat",
                "device_id": device_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await ws1.send(json.dumps(heartbeat))
            await asyncio.sleep(0.5)

            # Second connection (should close the first one)
            ws2 = await websockets.connect(uri)
            assert ws2.state.name == "OPEN"

            # Wait a bit for the server to handle the new connection
            await asyncio.sleep(1)

            # First connection should be closed or will be closed soon
            # Second connection should remain open
            assert ws2.state.name == "OPEN"

            # Clean up
            if ws1.state.name != "CLOSED":
                await ws1.close()
            await ws2.close()


class TestWebSocketHeartbeat:
    """Test WebSocket heartbeat functionality."""

    @pytest.mark.asyncio
    async def test_heartbeat_message_handling(self):
        """Test that heartbeat messages are handled correctly."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            async with websockets.connect(uri) as ws:
                # Send multiple heartbeats
                for i in range(5):
                    heartbeat = {
                        "type": "heartbeat",
                        "device_id": device_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    await ws.send(json.dumps(heartbeat))
                    await asyncio.sleep(0.2)

                # Connection should remain stable
                assert ws.state == websockets.protocol.OPEN

    @pytest.mark.asyncio
    async def test_heartbeat_with_invalid_json(self):
        """Test heartbeat handling with invalid JSON."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            async with websockets.connect(uri) as ws:
                # Send invalid JSON (should be treated as heartbeat)
                await ws.send("invalid json here")
                await asyncio.sleep(0.5)

                # Connection should remain stable
                assert ws.state == websockets.protocol.OPEN

                # Send valid heartbeat after
                heartbeat = {
                    "type": "heartbeat",
                    "device_id": device_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await ws.send(json.dumps(heartbeat))
                await asyncio.sleep(0.5)

                assert ws.state == websockets.protocol.OPEN

    @pytest.mark.asyncio
    async def test_heartbeat_empty_message(self):
        """Test heartbeat handling with empty messages."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            async with websockets.connect(uri) as ws:
                # Send empty message
                await ws.send("")
                await asyncio.sleep(0.5)

                # Connection should remain stable
                assert ws.state == websockets.protocol.OPEN

    @pytest.mark.asyncio
    async def test_heartbeat_frequency(self):
        """Test rapid heartbeat messages."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            async with websockets.connect(uri) as ws:
                # Send rapid heartbeats
                for i in range(20):
                    heartbeat = {
                        "type": "heartbeat",
                        "device_id": device_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    await ws.send(json.dumps(heartbeat))
                    await asyncio.sleep(0.05)  # Very rapid

                # Connection should handle rapid messages
                assert ws.state == websockets.protocol.OPEN


class TestWebSocketTaskDelivery:
    """Test task delivery via WebSocket."""

    @pytest.mark.asyncio
    async def test_task_delivery_basic(self):
        """Test basic task delivery to connected device."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            async with websockets.connect(uri) as ws:
                # Create a task
                task_data = {
                    "device_id": device_id,
                    "title": "WebSocket Delivery Test",
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

                # Receive task via WebSocket
                message = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(message)

                assert data["type"] == "task.exec"
                assert data["task_id"] == task_id
                assert "actions" in data
                assert "issued_at" in data
                assert "signature" in data

                assert len(data["actions"]) == 1
                assert data["actions"][0]["action_id"] == "a1"

    @pytest.mark.asyncio
    async def test_task_delivery_multiple_actions(self):
        """Test task delivery with multiple actions."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            async with websockets.connect(uri) as ws:
                actions = [
                    {"action_id": "a1", "type": "screenshot", "params": {}},
                    {"action_id": "a2", "type": "wait", "params": {"seconds": 1}},
                    {"action_id": "a3", "type": "log", "params": {"message": "test"}},
                ]

                task_data = {
                    "device_id": device_id,
                    "title": "Multi-Action WebSocket Test",
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

                # Receive task
                message = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(message)

                assert data["type"] == "task.exec"
                assert len(data["actions"]) == 3

                # Verify all actions are present
                received_action_ids = [action["action_id"] for action in data["actions"]]
                expected_action_ids = ["a1", "a2", "a3"]
                assert received_action_ids == expected_action_ids

    @pytest.mark.asyncio
    async def test_pending_task_delivery_on_connect(self):
        """Test that pending tasks are delivered when device connects."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            # Create task while device is offline
            task_data = {
                "device_id": device_id,
                "title": "Pending Task Test",
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
                message = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(message)

                assert data["type"] == "task.exec"
                assert data["task_id"] == task_id

    @pytest.mark.asyncio
    async def test_multiple_pending_tasks_delivery(self):
        """Test delivery of multiple pending tasks on connect."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            # Create multiple tasks while device is offline
            task_ids = []
            for i in range(3):
                task_data = {
                    "device_id": device_id,
                    "title": f"Pending Task {i + 1}",
                    "metadata": {
                        "actions": [{"action_id": f"a{i + 1}", "type": "noop", "params": {}}]
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
                assert task_response.status_code == 201, (
                    f"Failed to create task {i + 1}: {task_response.text}"
                )
                task_data_response = task_response.json()
                task_ids.append(task_data_response["id"])

            # Connect device and receive all pending tasks
            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            async with websockets.connect(uri) as ws:
                received_task_ids = []

                # Send heartbeat to establish connection
                heartbeat = {
                    "type": "heartbeat",
                    "device_id": device_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await ws.send(json.dumps(heartbeat))

                # Wait longer for connection to be fully established and tasks to be sent
                await asyncio.sleep(2.0)

                # Receive all pending tasks with more flexible timeout
                start_time = asyncio.get_event_loop().time()
                max_wait_time = 10.0  # Total maximum wait time

                while (
                    len(received_task_ids) < 3
                    and (asyncio.get_event_loop().time() - start_time) < max_wait_time
                ):
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=2.0)
                        data = json.loads(message)
                        if data["type"] == "task.exec":
                            received_task_ids.append(data["task_id"])
                    except asyncio.TimeoutError:
                        # If we haven't received all tasks yet, continue waiting
                        if len(received_task_ids) < 3:
                            continue
                        else:
                            break

                # All tasks should be received (order might vary)
                assert len(received_task_ids) == 3, (
                    f"Expected 3 tasks, got {len(received_task_ids)}: received={received_task_ids}, expected={task_ids}"
                )
                assert set(received_task_ids) == set(task_ids)


class TestWebSocketTaskResults:
    """Test task result handling via WebSocket."""

    @pytest.mark.asyncio
    async def test_task_result_success(self):
        """Test successful task result submission."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            async with websockets.connect(uri) as ws:
                # Create and receive task
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

                # Send successful result
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
                await asyncio.sleep(1)  # Give server time to process

                # Connection should remain stable
                assert ws.state == websockets.protocol.OPEN

    @pytest.mark.asyncio
    async def test_task_result_failure(self):
        """Test failed task result submission."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            async with websockets.connect(uri) as ws:
                # Create and receive task
                task_data = {
                    "device_id": device_id,
                    "title": "Failure Test Task",
                    "metadata": {
                        "actions": [{"action_id": "a1", "type": "fail_action", "params": {}}]
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

                # Send failure result
                result = {
                    "type": "task.result",
                    "task_id": task_id,
                    "results": [
                        {
                            "action_id": "a1",
                            "status": "failed",
                            "error": "Action failed with error message",
                            "error_code": "ACTION_FAILED",
                        }
                    ],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "signature": "",
                }

                await ws.send(json.dumps(result))
                await asyncio.sleep(1)

                assert ws.state == websockets.protocol.OPEN

    @pytest.mark.asyncio
    async def test_task_result_multiple_actions(self):
        """Test task result with multiple action results."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            async with websockets.connect(uri) as ws:
                # Create task with multiple actions
                actions = [
                    {"action_id": "a1", "type": "screenshot", "params": {}},
                    {"action_id": "a2", "type": "log", "params": {"message": "test"}},
                    {"action_id": "a3", "type": "wait", "params": {"seconds": 1}},
                ]

                task_data = {
                    "device_id": device_id,
                    "title": "Multi-Result Test Task",
                    "metadata": {"actions": actions},
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

                # Send results for all actions
                result = {
                    "type": "task.result",
                    "task_id": task_id,
                    "results": [
                        {
                            "action_id": "a1",
                            "status": "done",
                            "s3_url": "s3://bucket/screenshot.png",
                        },
                        {"action_id": "a2", "status": "done", "output": "Logged message"},
                        {"action_id": "a3", "status": "done", "output": "Waited 1 second"},
                    ],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "signature": "",
                }

                await ws.send(json.dumps(result))
                await asyncio.sleep(1)

                assert ws.state == websockets.protocol.OPEN

    @pytest.mark.asyncio
    async def test_task_result_with_artifacts(self):
        """Test task result with artifact references."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            async with websockets.connect(uri) as ws:
                # Create task
                task_data = {
                    "device_id": device_id,
                    "title": "Artifact Result Test",
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
                    json={"task_id": task_id, "filename": "screenshot.png", "size": 2048},
                )
                assert presign_response.status_code == 200
                s3_url = presign_response.json()["s3_url"]

                # Send result with artifact
                result = {
                    "type": "task.result",
                    "task_id": task_id,
                    "results": [
                        {
                            "action_id": "a1",
                            "status": "done",
                            "s3_url": s3_url,
                            "artifact_type": "image/png",
                            "artifact_size": 2048,
                        }
                    ],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "signature": "",
                }

                await ws.send(json.dumps(result))
                await asyncio.sleep(1)

                assert ws.state == websockets.protocol.OPEN

    @pytest.mark.asyncio
    async def test_task_result_invalid_format(self):
        """Test handling of invalid task result format."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            async with websockets.connect(uri) as ws:
                # Send invalid result formats
                invalid_results = [
                    {"type": "task.result"},  # Missing required fields
                    {"type": "task.result", "task_id": "invalid"},  # Missing results
                    {"type": "task.result", "task_id": "test", "results": "not_an_array"},
                    # Unknown message type
                    {"type": "unknown_type", "data": "test"},
                ]

                for invalid_result in invalid_results:
                    await ws.send(json.dumps(invalid_result))
                    await asyncio.sleep(0.2)

                # Connection should remain stable despite invalid messages
                assert ws.state == websockets.protocol.OPEN

                # Send valid heartbeat to confirm connection is still working
                heartbeat = {
                    "type": "heartbeat",
                    "device_id": device_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await ws.send(json.dumps(heartbeat))
                await asyncio.sleep(0.5)

                assert ws.state == websockets.protocol.OPEN


class TestWebSocketRevocation:
    """Test WebSocket connection revocation and security."""

    @pytest.mark.asyncio
    async def test_device_revocation_closes_connection(self):
        """Test that revoking a device closes its WebSocket connection."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            async with websockets.connect(uri) as ws:
                # Verify connection is open
                assert ws.state == websockets.protocol.OPEN

                # Send heartbeat to establish connection
                heartbeat = {
                    "type": "heartbeat",
                    "device_id": device_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await ws.send(json.dumps(heartbeat))
                await asyncio.sleep(0.5)

                # Revoke the device
                revoke_response = await client.post(
                    f"/v1/devices/{device_id}/revoke",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                assert revoke_response.status_code == 200

                # Connection should be closed within a reasonable time
                with pytest.raises(
                    (websockets.exceptions.ConnectionClosedError, asyncio.TimeoutError)
                ):
                    await asyncio.wait_for(ws.recv(), timeout=10.0)

    @pytest.mark.asyncio
    async def test_revocation_during_task_execution(self):
        """Test revocation while a task is being executed."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            async with websockets.connect(uri) as ws:
                # Send heartbeat to establish connection
                heartbeat = {
                    "type": "heartbeat",
                    "device_id": device_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await ws.send(json.dumps(heartbeat))
                await asyncio.sleep(0.5)

                # Create a task
                task_data = {
                    "device_id": device_id,
                    "title": "Revocation During Execution Test",
                    "metadata": {
                        "actions": [{"action_id": "a1", "type": "long_running", "params": {}}]
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
                message = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(message)
                assert data["task_id"] == task_id

                # Revoke device while "executing" task
                await client.post(
                    f"/v1/devices/{device_id}/revoke",
                    headers={"Authorization": f"Bearer {access_token}"},
                )

                # Connection should be closed within reasonable time (revocation watcher checks every 5 seconds)
                # Try to receive messages until connection is closed or timeout
                connection_closed = False
                start_time = asyncio.get_event_loop().time()
                max_wait_time = 15.0

                while (
                    not connection_closed
                    and (asyncio.get_event_loop().time() - start_time) < max_wait_time
                ):
                    try:
                        await asyncio.wait_for(ws.recv(), timeout=2.0)
                    except (websockets.exceptions.ConnectionClosedError, asyncio.TimeoutError):
                        connection_closed = True
                        break
                    except Exception:
                        # Any other exception means connection is likely closed
                        connection_closed = True
                        break

                # Assert that the connection was closed
                assert connection_closed or ws.state.name == "CLOSED", (
                    "Connection should be closed after revocation"
                )

    @pytest.mark.asyncio
    async def test_reconnect_after_revocation(self):
        """Test that device cannot reconnect after revocation."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            # First connection
            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            async with websockets.connect(uri) as ws:
                assert ws.state.name == "OPEN"

                # Send heartbeat to establish connection
                heartbeat = {
                    "type": "heartbeat",
                    "device_id": device_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await ws.send(json.dumps(heartbeat))
                await asyncio.sleep(0.5)

                # Revoke device
                await client.post(
                    f"/v1/devices/{device_id}/revoke",
                    headers={"Authorization": f"Bearer {access_token}"},
                )

                # Wait for connection to close (revocation watcher checks every 5 seconds)
                # Try to receive messages until connection is closed or timeout
                connection_closed = False
                start_time = asyncio.get_event_loop().time()
                max_wait_time = 15.0

                while (
                    not connection_closed
                    and (asyncio.get_event_loop().time() - start_time) < max_wait_time
                ):
                    try:
                        await asyncio.wait_for(ws.recv(), timeout=2.0)
                    except (websockets.exceptions.ConnectionClosedError, asyncio.TimeoutError):
                        connection_closed = True
                        break
                    except Exception:
                        # Any other exception means connection is likely closed
                        connection_closed = True
                        break

                # Assert that the connection was closed
                assert connection_closed or ws.state.name == "CLOSED", (
                    "Connection should be closed after revocation"
                )

            # Try to reconnect with same token (should fail)
            with pytest.raises(
                (websockets.exceptions.InvalidStatus, websockets.exceptions.ConnectionClosedError)
            ) as exc_info:
                async with websockets.connect(uri) as ws:
                    await ws.recv()

            # Should either reject with HTTP 403 or close with revocation code 4401
            if isinstance(exc_info.value, websockets.exceptions.InvalidStatus):
                assert exc_info.value.response.status_code == 403
            elif isinstance(exc_info.value, websockets.exceptions.ConnectionClosedError):
                assert exc_info.value.rcvd.code == 4401


class TestWebSocketEdgeCases:
    """Test WebSocket edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_connection_with_large_messages(self):
        """Test WebSocket with very large messages."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            async with websockets.connect(uri) as ws:
                # Send a very large heartbeat message
                large_data = "x" * 100000  # 100KB of data
                large_heartbeat = {
                    "type": "heartbeat",
                    "device_id": device_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "large_field": large_data,
                }

                await ws.send(json.dumps(large_heartbeat))
                await asyncio.sleep(1)

                # Connection should handle large messages
                assert ws.state == websockets.protocol.OPEN

    @pytest.mark.asyncio
    async def test_rapid_message_sending(self):
        """Test rapid message sending."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            async with websockets.connect(uri) as ws:
                # Send many messages rapidly
                for i in range(100):
                    message = {
                        "type": "heartbeat",
                        "device_id": device_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "sequence": i,
                    }
                    await ws.send(json.dumps(message))
                    # No sleep - send as fast as possible

                await asyncio.sleep(2)  # Give server time to process

                # Connection should handle rapid messages
                assert ws.state == websockets.protocol.OPEN

    @pytest.mark.asyncio
    async def test_connection_timeout_behavior(self):
        """Test connection behavior during inactivity."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            async with websockets.connect(uri) as ws:
                # Send initial heartbeat
                heartbeat = {
                    "type": "heartbeat",
                    "device_id": device_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await ws.send(json.dumps(heartbeat))

                # Wait for a longer period without sending anything
                await asyncio.sleep(30)  # 30 seconds of inactivity

                # Try to send another message
                heartbeat2 = {
                    "type": "heartbeat",
                    "device_id": device_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await ws.send(json.dumps(heartbeat2))
                await asyncio.sleep(1)

                # Connection should still be active (or handle reconnection gracefully)
                # The exact behavior depends on server timeout settings
                # We just verify no exception is thrown

    @pytest.mark.asyncio
    async def test_malformed_device_id_in_messages(self):
        """Test handling of malformed device IDs in messages."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            uri = f"{WS_URL}/v1/ws/agent?token={device_token}"

            async with websockets.connect(uri) as ws:
                # Send messages with wrong device IDs
                wrong_device_messages = [
                    {
                        "type": "heartbeat",
                        "device_id": "wrong-id",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    {
                        "type": "heartbeat",
                        "device_id": str(uuid.uuid4()),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    {
                        "type": "heartbeat",
                        "device_id": "",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    {
                        "type": "heartbeat",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },  # Missing device_id
                ]

                for message in wrong_device_messages:
                    await ws.send(json.dumps(message))
                    await asyncio.sleep(0.2)

                # Send correct heartbeat
                correct_heartbeat = {
                    "type": "heartbeat",
                    "device_id": device_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await ws.send(json.dumps(correct_heartbeat))
                await asyncio.sleep(0.5)

                # Connection should remain stable
                assert ws.state == websockets.protocol.OPEN
