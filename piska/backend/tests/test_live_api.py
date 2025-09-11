import os
import uuid
import pytest
import httpx


BASE_URL = os.getenv("BASE_URL", "http://0.0.0.0:8000")


@pytest.mark.asyncio
async def test_live_auth_and_enroll():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        email = f"u_{uuid.uuid4().hex[:12]}@t.com"
        password = "Password1!"

        r = await client.post("/v1/auth/signup", json={"email": email, "password": password})
        assert r.status_code in (201, 409)

        r = await client.post("/v1/auth/login", json={"email": email, "password": password})
        assert r.status_code == 200
        access = r.json()["access_token"]

        idem = uuid.uuid4().hex
        payload = {
            "device_name": "LiveHost",
            "platform": "linux",
            "capabilities": {"fs": True},
            "idempotency_key": idem,
        }
        r1 = await client.post(
            "/v1/devices/enroll", headers={"Authorization": f"Bearer {access}"}, json=payload
        )
        assert r1.status_code == 201, r1.text
        d1 = r1.json()

        r2 = await client.post(
            "/v1/devices/enroll", headers={"Authorization": f"Bearer {access}"}, json=payload
        )
        assert r2.status_code == 201, r2.text
        d2 = r2.json()
        assert d1["device_id"] == d2["device_id"]


@pytest.mark.asyncio
async def test_live_device_token_refresh_and_revoke():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        email = f"u_{uuid.uuid4().hex[:12]}@t.com"
        password = "Password1!"
        await client.post("/v1/auth/signup", json={"email": email, "password": password})
        r = await client.post("/v1/auth/login", json={"email": email, "password": password})
        access = r.json()["access_token"]

        p = {"device_name": "LiveB", "platform": "linux", "capabilities": {}}
        r = await client.post(
            "/v1/devices/enroll", headers={"Authorization": f"Bearer {access}"}, json=p
        )
        assert r.status_code == 201
        device_id = r.json()["device_id"]

        r = await client.post(
            "/v1/devices/token/refresh",
            headers={"Authorization": f"Bearer {access}"},
            json={"device_id": device_id},
        )
        assert r.status_code == 200

        r = await client.post(
            f"/v1/devices/{device_id}/revoke", headers={"Authorization": f"Bearer {access}"}
        )
        assert r.status_code == 200
