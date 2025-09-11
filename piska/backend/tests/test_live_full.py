import os
import uuid
from datetime import datetime, timezone
import pytest
import httpx


BASE_URL = os.getenv("BASE_URL", "http://0.0.0.0:8000")


# type: ignore[name-defined]
async def signup_login(client: httpx.AsyncClient):
    email = f"l_{uuid.uuid4().hex[:12]}@t.com"
    password = "Password1!"
    await client.post("/v1/auth/signup", json={"email": email, "password": password})
    r = await client.post("/v1/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


@pytest.mark.asyncio
async def test_live_all_flows():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        access = await signup_login(client)

        idem = uuid.uuid4().hex
        payload = {
            "device_name": "A",
            "platform": "linux",
            "capabilities": {},
            "idempotency_key": idem,
        }
        r1 = await client.post(
            "/v1/devices/enroll", headers={"Authorization": f"Bearer {access}"}, json=payload
        )
        r2 = await client.post(
            "/v1/devices/enroll", headers={"Authorization": f"Bearer {access}"}, json=payload
        )
        assert r1.status_code == 201 and r2.status_code == 201
        assert r1.json()["device_id"] == r2.json()["device_id"]

        device_id = r1.json()["device_id"]
        r = await client.post(
            "/v1/devices/token/refresh",
            headers={"Authorization": f"Bearer {access}"},
            json={"device_id": device_id},
        )
        assert r.status_code == 200
        exp = datetime.fromisoformat(r.json()["expires_at"].replace("Z", "+00:00"))
        assert exp > datetime.now(timezone.utc)

        r = await client.post(
            f"/v1/devices/{device_id}/revoke", headers={"Authorization": f"Bearer {access}"}
        )
        assert r.status_code == 200
