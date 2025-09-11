import os
import uuid
import asyncio
import pytest
import httpx
import websockets


BASE_URL = os.getenv("BASE_URL", "http://0.0.0.0:8000")
WS_URL = BASE_URL.replace("http", "ws")


@pytest.mark.asyncio
async def test_live_ws_revocation():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        email = f"w_{uuid.uuid4().hex[:12]}@t.com"
        password = "Password1!"
        await client.post("/v1/auth/signup", json={"email": email, "password": password})
        r = await client.post("/v1/auth/login", json={"email": email, "password": password})
        access = r.json()["access_token"]
        r = await client.post(
            "/v1/devices/enroll",
            headers={"Authorization": f"Bearer {access}"},
            json={"device_name": "ws", "platform": "linux", "capabilities": {}},
        )
        assert r.status_code == 201
        device_id = r.json()["device_id"]
        token = r.json()["device_token"]

    uri = f"{WS_URL}/v1/ws/agent?token={token}"
    async with websockets.connect(uri) as ws:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            rr = await client.post(
                f"/v1/devices/{device_id}/revoke", headers={"Authorization": f"Bearer {access}"}
            )
            assert rr.status_code == 200
        # give server time to close
        with pytest.raises(Exception):
            await asyncio.wait_for(ws.recv(), timeout=2)
