"""
Comprehensive tests for Devices endpoints.
Tests all device endpoints with various scenarios including edge cases and error conditions.
"""

import os
import uuid
import pytest
import httpx
from datetime import datetime, timezone
from typing import Tuple


BASE_URL = os.getenv("BASE_URL", "http://0.0.0.0:8000")


async def create_user_and_get_token(client: httpx.AsyncClient) -> Tuple[str, str]:
    """Helper function to create a user and return access token and user email."""
    email = f"device_test_{uuid.uuid4().hex[:12]}@test.com"
    password = "SecurePassword123!"

    # Signup
    await client.post("/v1/auth/signup", json={"email": email, "password": password})

    # Login
    login_response = await client.post(
        "/v1/auth/login", json={"email": email, "password": password}
    )

    access_token = login_response.json()["access_token"]
    return access_token, email


class TestDeviceEnrollment:
    """Test device enrollment endpoint."""

    @pytest.mark.asyncio
    async def test_enroll_device_success(self):
        """Test successful device enrollment."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)

            device_data = {
                "device_name": "Test Device",
                "platform": "linux",
                "capabilities": {"fs": True, "network": True},
                "idempotency_key": uuid.uuid4().hex,
            }

            response = await client.post(
                "/v1/devices/enroll",
                headers={"Authorization": f"Bearer {access_token}"},
                json=device_data,
            )

            assert response.status_code == 201
            data = response.json()

            # Verify response structure
            assert "device_id" in data
            assert "device_token" in data
            assert "wss_url" in data
            assert "kid" in data
            assert "expires_at" in data

            # Verify data types
            assert isinstance(data["device_id"], str)
            assert isinstance(data["device_token"], str)
            assert isinstance(data["wss_url"], str)
            assert isinstance(data["kid"], str)

            # Verify expires_at is a valid datetime string
            expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
            assert expires_at > datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_enroll_device_idempotency(self):
        """Test device enrollment idempotency."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)

            device_data = {
                "device_name": "Idempotent Device",
                "platform": "windows",
                "capabilities": {"screen": True},
                "idempotency_key": uuid.uuid4().hex,
            }

            # First enrollment
            response1 = await client.post(
                "/v1/devices/enroll",
                headers={"Authorization": f"Bearer {access_token}"},
                json=device_data,
            )
            assert response1.status_code == 201
            device_id_1 = response1.json()["device_id"]

            # Second enrollment with same idempotency key
            response2 = await client.post(
                "/v1/devices/enroll",
                headers={"Authorization": f"Bearer {access_token}"},
                json=device_data,
            )
            assert response2.status_code == 201
            device_id_2 = response2.json()["device_id"]

            # Should return the same device
            assert device_id_1 == device_id_2

    @pytest.mark.asyncio
    async def test_enroll_device_without_idempotency_key(self):
        """Test device enrollment without idempotency key."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)

            device_data = {
                "device_name": "No Idempotency Device",
                "platform": "macos",
                "capabilities": {},
            }

            response = await client.post(
                "/v1/devices/enroll",
                headers={"Authorization": f"Bearer {access_token}"},
                json=device_data,
            )

            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_enroll_device_unauthorized(self):
        """Test device enrollment without authentication."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            device_data = {
                "device_name": "Unauthorized Device",
                "platform": "linux",
                "capabilities": {},
            }

            response = await client.post("/v1/devices/enroll", json=device_data)
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_enroll_device_invalid_data(self):
        """Test device enrollment with invalid data."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)

            # Missing required fields
            response1 = await client.post(
                "/v1/devices/enroll",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"platform": "linux"},  # Missing device_name
            )
            assert response1.status_code == 422

            # Empty device name
            response2 = await client.post(
                "/v1/devices/enroll",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"device_name": "", "platform": "linux"},
            )
            assert response2.status_code == 422


class TestDeviceTokenRefresh:
    """Test device token refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_device_token_success(self):
        """Test successful device token refresh."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)

            # First enroll a device
            device_data = {
                "device_name": "Refresh Test Device",
                "platform": "linux",
                "capabilities": {"test": True},
            }

            enroll_response = await client.post(
                "/v1/devices/enroll",
                headers={"Authorization": f"Bearer {access_token}"},
                json=device_data,
            )
            assert enroll_response.status_code == 201
            device_id = enroll_response.json()["device_id"]
            original_token = enroll_response.json()["device_token"]

            # Refresh the token
            refresh_response = await client.post(
                "/v1/devices/token/refresh",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"device_id": device_id},
            )

            assert refresh_response.status_code == 200
            data = refresh_response.json()

            # Verify response structure
            assert "device_id" in data
            assert "device_token" in data
            assert "wss_url" in data
            assert "kid" in data
            assert "expires_at" in data

            # Verify device_id matches
            assert data["device_id"] == device_id

            # Verify new token is different
            assert data["device_token"] != original_token

    @pytest.mark.asyncio
    async def test_refresh_device_token_nonexistent_device(self):
        """Test refresh token for non-existent device."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)

            fake_device_id = str(uuid.uuid4())

            response = await client.post(
                "/v1/devices/token/refresh",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"device_id": fake_device_id},
            )

            assert response.status_code == 404
            assert "Device not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_device_token_unauthorized(self):
        """Test refresh token without authentication."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            response = await client.post(
                "/v1/devices/token/refresh", json={"device_id": str(uuid.uuid4())}
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_device_token_other_users_device(self):
        """Test refresh token for another user's device."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create first user and device
            access_token1, _ = await create_user_and_get_token(client)

            enroll_response = await client.post(
                "/v1/devices/enroll",
                headers={"Authorization": f"Bearer {access_token1}"},
                json={"device_name": "User1 Device", "platform": "linux"},
            )
            device_id = enroll_response.json()["device_id"]

            # Create second user
            access_token2, _ = await create_user_and_get_token(client)

            # Try to refresh first user's device with second user's token
            response = await client.post(
                "/v1/devices/token/refresh",
                headers={"Authorization": f"Bearer {access_token2}"},
                json={"device_id": device_id},
            )

            assert response.status_code == 404
            assert "Device not found" in response.json()["detail"]


class TestDeviceRevocation:
    """Test device revocation endpoint."""

    @pytest.mark.asyncio
    async def test_revoke_device_success(self):
        """Test successful device revocation."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)

            # Enroll a device
            enroll_response = await client.post(
                "/v1/devices/enroll",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"device_name": "Revoke Test Device", "platform": "linux"},
            )
            device_id = enroll_response.json()["device_id"]

            # Revoke the device
            revoke_response = await client.post(
                f"/v1/devices/{device_id}/revoke",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            assert revoke_response.status_code == 200
            data = revoke_response.json()

            assert "device_id" in data
            assert "revoked_count" in data
            assert data["device_id"] == device_id
            assert isinstance(data["revoked_count"], int)
            assert data["revoked_count"] >= 0

    @pytest.mark.asyncio
    async def test_revoke_device_nonexistent(self):
        """Test revoking non-existent device."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)

            fake_device_id = str(uuid.uuid4())

            response = await client.post(
                f"/v1/devices/{fake_device_id}/revoke",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            assert response.status_code == 404
            assert "Device not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_revoke_device_unauthorized(self):
        """Test revoking device without authentication."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            fake_device_id = str(uuid.uuid4())

            response = await client.post(f"/v1/devices/{fake_device_id}/revoke")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_revoke_other_users_device(self):
        """Test revoking another user's device."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create first user and device
            access_token1, _ = await create_user_and_get_token(client)

            enroll_response = await client.post(
                "/v1/devices/enroll",
                headers={"Authorization": f"Bearer {access_token1}"},
                json={"device_name": "User1 Device", "platform": "linux"},
            )
            device_id = enroll_response.json()["device_id"]

            # Create second user
            access_token2, _ = await create_user_and_get_token(client)

            # Try to revoke first user's device with second user's token
            response = await client.post(
                f"/v1/devices/{device_id}/revoke",
                headers={"Authorization": f"Bearer {access_token2}"},
            )

            assert response.status_code == 404
            assert "Device not found" in response.json()["detail"]


class TestDevicesList:
    """Test devices list endpoint."""

    @pytest.mark.asyncio
    async def test_list_devices_empty(self):
        """Test listing devices when user has no devices."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)

            response = await client.get(
                "/v1/devices/", headers={"Authorization": f"Bearer {access_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0

    @pytest.mark.asyncio
    async def test_list_devices_with_devices(self):
        """Test listing devices when user has devices."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)

            # Enroll multiple devices
            device_names = ["Device 1", "Device 2", "Device 3"]
            device_ids = []

            for name in device_names:
                enroll_response = await client.post(
                    "/v1/devices/enroll",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={"device_name": name, "platform": "linux"},
                )
                device_ids.append(enroll_response.json()["device_id"])

            # List devices
            response = await client.get(
                "/v1/devices/", headers={"Authorization": f"Bearer {access_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 3

            # Verify device structure
            for device in data:
                assert "id" in device
                assert "device_name" in device
                assert "platform" in device
                assert "capabilities" in device
                assert "connection_status" in device
                assert "presence" in device  # Default include_presence=True

                assert device["id"] in device_ids
                assert device["device_name"] in device_names
                assert device["platform"] == "linux"

    @pytest.mark.asyncio
    async def test_list_devices_without_presence(self):
        """Test listing devices without presence information."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)

            # Enroll a device
            await client.post(
                "/v1/devices/enroll",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"device_name": "Test Device", "platform": "linux"},
            )

            # List devices without presence
            response = await client.get(
                "/v1/devices/?include_presence=false",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1

            device = data[0]
            assert "presence" not in device
            assert "id" in device
            assert "device_name" in device

    @pytest.mark.asyncio
    async def test_list_devices_unauthorized(self):
        """Test listing devices without authentication."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            response = await client.get("/v1/devices/")
            assert response.status_code == 401


class TestDeviceGet:
    """Test individual device get endpoint."""

    @pytest.mark.asyncio
    async def test_get_device_success(self):
        """Test getting individual device details."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)

            # Enroll a device
            device_data = {
                "device_name": "Get Test Device",
                "platform": "windows",
                "capabilities": {"test": True, "screen": False},
            }

            enroll_response = await client.post(
                "/v1/devices/enroll",
                headers={"Authorization": f"Bearer {access_token}"},
                json=device_data,
            )
            device_id = enroll_response.json()["device_id"]

            # Get device details
            response = await client.get(
                f"/v1/devices/{device_id}", headers={"Authorization": f"Bearer {access_token}"}
            )

            assert response.status_code == 200
            data = response.json()

            # Verify device structure
            assert "id" in data
            assert "device_name" in data
            assert "platform" in data
            assert "capabilities" in data
            assert "connection_status" in data
            assert "presence" in data

            # Verify values
            assert data["id"] == device_id
            assert data["device_name"] == device_data["device_name"]
            assert data["platform"] == device_data["platform"]
            assert data["capabilities"] == device_data["capabilities"]

    @pytest.mark.asyncio
    async def test_get_device_nonexistent(self):
        """Test getting non-existent device."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)

            fake_device_id = str(uuid.uuid4())

            response = await client.get(
                f"/v1/devices/{fake_device_id}", headers={"Authorization": f"Bearer {access_token}"}
            )

            assert response.status_code == 404
            assert "Device not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_device_unauthorized(self):
        """Test getting device without authentication."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            fake_device_id = str(uuid.uuid4())

            response = await client.get(f"/v1/devices/{fake_device_id}")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_other_users_device(self):
        """Test getting another user's device."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Create first user and device
            access_token1, _ = await create_user_and_get_token(client)

            enroll_response = await client.post(
                "/v1/devices/enroll",
                headers={"Authorization": f"Bearer {access_token1}"},
                json={"device_name": "User1 Device", "platform": "linux"},
            )
            device_id = enroll_response.json()["device_id"]

            # Create second user
            access_token2, _ = await create_user_and_get_token(client)

            # Try to get first user's device with second user's token
            response = await client.get(
                f"/v1/devices/{device_id}", headers={"Authorization": f"Bearer {access_token2}"}
            )

            assert response.status_code == 404
            assert "Device not found" in response.json()["detail"]


class TestDevicesIntegration:
    """Integration tests for device management workflow."""

    @pytest.mark.asyncio
    async def test_complete_device_lifecycle(self):
        """Test complete device lifecycle: enroll -> list -> get -> refresh -> revoke."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)

            # 1. Enroll device
            device_data = {
                "device_name": "Lifecycle Test Device",
                "platform": "linux",
                "capabilities": {"fs": True, "network": True},
            }

            enroll_response = await client.post(
                "/v1/devices/enroll",
                headers={"Authorization": f"Bearer {access_token}"},
                json=device_data,
            )
            assert enroll_response.status_code == 201
            device_id = enroll_response.json()["device_id"]

            # 2. List devices (should include our device)
            list_response = await client.get(
                "/v1/devices/", headers={"Authorization": f"Bearer {access_token}"}
            )
            assert list_response.status_code == 200
            devices = list_response.json()
            assert len(devices) >= 1
            assert any(d["id"] == device_id for d in devices)

            # 3. Get specific device
            get_response = await client.get(
                f"/v1/devices/{device_id}", headers={"Authorization": f"Bearer {access_token}"}
            )
            assert get_response.status_code == 200
            device_details = get_response.json()
            assert device_details["id"] == device_id
            assert device_details["device_name"] == device_data["device_name"]

            # 4. Refresh device token
            refresh_response = await client.post(
                "/v1/devices/token/refresh",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"device_id": device_id},
            )
            assert refresh_response.status_code == 200
            assert refresh_response.json()["device_id"] == device_id

            # 5. Revoke device
            revoke_response = await client.post(
                f"/v1/devices/{device_id}/revoke",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert revoke_response.status_code == 200
            assert revoke_response.json()["device_id"] == device_id

    @pytest.mark.asyncio
    async def test_multiple_devices_per_user(self):
        """Test that users can have multiple devices."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            access_token, _ = await create_user_and_get_token(client)

            # Enroll multiple devices with different platforms
            platforms = ["linux", "windows", "macos", "android", "ios"]
            device_ids = []

            for i, platform in enumerate(platforms):
                enroll_response = await client.post(
                    "/v1/devices/enroll",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={
                        "device_name": f"Device {i + 1}",
                        "platform": platform,
                        "capabilities": {"platform_specific": True},
                    },
                )
                assert enroll_response.status_code == 201
                device_ids.append(enroll_response.json()["device_id"])

            # List all devices
            list_response = await client.get(
                "/v1/devices/", headers={"Authorization": f"Bearer {access_token}"}
            )
            assert list_response.status_code == 200
            devices = list_response.json()
            assert len(devices) == len(platforms)

            # Verify all devices are present and have correct platforms
            returned_device_ids = [d["id"] for d in devices]
            returned_platforms = [d["platform"] for d in devices]

            for device_id in device_ids:
                assert device_id in returned_device_ids

            for platform in platforms:
                assert platform in returned_platforms
