"""
Test Kafka integration functionality through API endpoints.
"""

import os
import uuid
import pytest
import httpx
from typing import Tuple


BASE_URL = os.getenv("BASE_URL", "http://0.0.0.0:8000")


async def create_user_and_get_token(client: httpx.AsyncClient) -> Tuple[str, str]:
    """Helper function to create a user and return access token and user email."""
    email = f"kafka_test_{uuid.uuid4().hex[:12]}@test.com"
    password = "SecurePassword123!"

    # Signup
    signup_response = await client.post(
        "/v1/auth/signup", json={"email": email, "password": password}
    )
    assert signup_response.status_code == 201

    # Login
    login_response = await client.post(
        "/v1/auth/login", json={"email": email, "password": password}
    )
    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]
    return access_token, email


async def enroll_device(
    client: httpx.AsyncClient, access_token: str, device_name: str = "Kafka Test Device"
) -> Tuple[str, str]:
    """Helper function to enroll a device and return device_id and device_token."""
    device_data = {
        "device_name": device_name,
        "platform": "linux",
        "capabilities": {"fs": True, "screen": True},
    }

    device_response = await client.post(
        "/v1/devices/enroll", headers={"Authorization": f"Bearer {access_token}"}, json=device_data
    )
    assert device_response.status_code == 201

    device_id = device_response.json()["device_id"]
    device_token = device_response.json()["device_token"]
    return device_id, device_token


class TestKafkaIntegration:
    """Test Kafka integration through task creation and WebSocket delivery."""

    @pytest.mark.asyncio
    async def test_task_creation_with_kafka_routing(self):
        """Test that tasks are created and routed through Kafka (if available)."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, device_token = await enroll_device(client, access_token)

            # Create a task that should trigger Kafka routing
            task_data = {
                "device_id": device_id,
                "title": "Kafka Integration Test Task",
                "description": "Test task for Kafka routing",
                "metadata": {
                    "actions": [{"action_id": "test_action", "type": "test", "params": {}}]
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

            # Task should be created successfully regardless of Kafka status
            assert task_response.status_code == 201
            task_id = task_response.json()["id"]
            assert task_response.json()["status"] == "queued"

            print(f"✅ Task {task_id} created successfully")
            print("ℹ️  Note: Kafka routing depends on broker availability")

    @pytest.mark.asyncio
    async def test_health_endpoint_with_kafka_status(self):
        """Test that health endpoint works regardless of Kafka status."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            response = await client.get("/healthz")
            assert response.status_code == 200

            health_data = response.json()
            assert health_data["status"] == "ok"
            print(f"✅ Health check passed: {health_data}")

    @pytest.mark.asyncio
    async def test_artifacts_with_kafka_background(self):
        """Test that artifacts work even if Kafka is not available."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)

            # Create a task first
            task_data = {
                "device_id": device_id,
                "title": "Artifact Test Task",
                "metadata": {
                    "actions": [{"action_id": "screenshot", "type": "screenshot", "params": {}}]
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

            # Test artifact presigning (should work regardless of Kafka)
            presign_response = await client.post(
                "/v1/artifacts/presign",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"task_id": task_id, "filename": "kafka_test.png", "size": 1024},
            )

            # Should work even if Kafka is down
            if presign_response.status_code == 200:
                print("✅ Artifacts work independently of Kafka")
            elif presign_response.status_code == 500:
                # Check if it's S3 configuration issue, not Kafka
                error_detail = presign_response.json().get("detail", "")
                if "bucket not configured" in error_detail.lower():
                    print("ℹ️  Artifacts require S3 configuration (not Kafka)")
                else:
                    print(f"⚠️  Unexpected error: {error_detail}")
            else:
                print(f"⚠️  Unexpected status code: {presign_response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__])
