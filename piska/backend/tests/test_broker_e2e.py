import os
import uuid
import asyncio
import json
import pytest
import httpx
import websockets


BASE_URL = os.getenv("BASE_URL", "http://0.0.0.0:8000")
WS_URL = BASE_URL.replace("http", "ws")


@pytest.mark.asyncio
async def test_broker_worker_delivery_and_presign():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
        email = f"bk_{uuid.uuid4().hex[:10]}@t.com"
        password = "Password1!"
        # Signup/login
        await client.post("/v1/auth/signup", json={"email": email, "password": password})
        r = await client.post("/v1/auth/login", json={"email": email, "password": password})
        access = r.json()["access_token"]
        # Enroll device
        r = await client.post(
            "/v1/devices/enroll",
            headers={"Authorization": f"Bearer {access}"},
            json={"device_name": "W", "platform": "linux", "capabilities": {}},
        )
        assert r.status_code == 201, r.text
        device_id = r.json()["device_id"]
        device_token = r.json()["device_token"]

    # Simulated agent WS
    uri = f"{WS_URL}/v1/ws/agent?token={device_token}"
    async with websockets.connect(uri) as ws:
        # Create task with actions
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
            actions = [{"action_id": "a1", "type": "noop", "params": {}}]
            payload = {"device_id": device_id, "title": "T",
                       "metadata": {"actions": actions}}
            r = await client.post(
                "/v1/tasks/",
                headers={"Authorization": f"Bearer {access}",
                         "Idempotency-Key": uuid.uuid4().hex},
                json=payload,
            )
            assert r.status_code == 201, r.text
            task_id = r.json()["id"]

        # Expect server->device delivery via broker/worker
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        data = json.loads(msg)
        assert data["type"] == "task.exec"
        assert data["task_id"] == task_id

        # Presign artifact
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
            pr = await client.post(
                "/v1/artifacts/presign",
                headers={"Authorization": f"Bearer {access}"},
                json={"task_id": task_id, "filename": "x.bin", "size": 1},
            )
            assert pr.status_code == 200, pr.text
            s3_url = pr.json()["s3_url"]

        # Send task result back
        result = {
            "type": "task.result",
            "task_id": task_id,
            "results": [{"action_id": "a1", "status": "done", "s3_url": s3_url}],
            "timestamp": "2025-01-01T00:00:00Z",
            "signature": "",
        }
        await ws.send(json.dumps(result))
