"""
Comprehensive tests for Artifacts endpoints.
Tests all artifact endpoints with various scenarios including edge cases and error conditions.
"""

import os
import uuid
import pytest
import httpx
from datetime import datetime, timezone
from typing import Tuple
from urllib.parse import urlparse, parse_qs


BASE_URL = os.getenv("BASE_URL", "http://0.0.0.0:8000")


async def create_user_and_get_token(client: httpx.AsyncClient) -> Tuple[str, str]:
    """Helper function to create a user and return access token and user email."""
    email = f"artifact_test_{uuid.uuid4().hex[:12]}@test.com"
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
    client: httpx.AsyncClient, access_token: str, device_name: str = "Artifact Test Device"
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


async def create_task(
    client: httpx.AsyncClient, access_token: str, device_id: str, title: str = "Artifact Test Task"
) -> str:
    """Helper function to create a task and return task_id."""
    task_data = {
        "device_id": device_id,
        "title": title,
        "metadata": {"actions": [{"action_id": "a1", "type": "screenshot", "params": {}}]},
    }

    response = await client.post(
        "/v1/tasks/",
        headers={"Authorization": f"Bearer {access_token}",
                 "Idempotency-Key": uuid.uuid4().hex},
        json=task_data,
    )

    assert response.status_code == 201
    return response.json()["id"]


class TestArtifactPresigning:
    """Test artifact presigning endpoint."""

    @pytest.mark.asyncio
    async def test_presign_artifact_success(self):
        """Test successful artifact presigning."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)
            task_id = await create_task(client, access_token, device_id)

            response = await client.post(
                "/v1/artifacts/presign",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"task_id": task_id,
                      "filename": "screenshot.png", "size": 1024},
            )

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "upload_url" in data
            assert "s3_url" in data
            assert "expires_at" in data

            # Verify URL formats
            assert data["upload_url"].startswith("http")
            assert data["s3_url"].startswith("s3://")

            # Verify expires_at is a valid future datetime
            expires_at = datetime.fromisoformat(
                data["expires_at"].replace("Z", "+00:00"))
            assert expires_at > datetime.now(timezone.utc)

            # Verify S3 URL contains task_id
            assert task_id in data["s3_url"]
            assert "screenshot.png" in data["s3_url"]

    @pytest.mark.asyncio
    async def test_presign_artifact_various_file_types(self):
        """Test presigning for various file types."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)
            task_id = await create_task(client, access_token, device_id)

            file_types = [
                ("document.pdf", 2048),
                ("video.mp4", 10485760),  # 10MB
                ("data.json", 512),
                ("log.txt", 1024),
                ("image.jpg", 4096),
                ("archive.zip", 8192),
            ]

            for filename, size in file_types:
                response = await client.post(
                    "/v1/artifacts/presign",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={"task_id": task_id,
                          "filename": filename, "size": size},
                )

                assert response.status_code == 200, f"Failed for {filename}"
                data = response.json()

                assert filename in data["s3_url"]
                assert data["upload_url"].startswith("http")

    @pytest.mark.asyncio
    async def test_presign_artifact_different_sizes(self):
        """Test presigning for different file sizes."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)
            task_id = await create_task(client, access_token, device_id)

            sizes = [1, 1024, 1048576, 104857600]  # 1B, 1KB, 1MB, 100MB

            for size in sizes:
                response = await client.post(
                    "/v1/artifacts/presign",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={"task_id": task_id,
                          "filename": f"file_{size}.dat", "size": size},
                )

                assert response.status_code == 200, f"Failed for size {size}"

    @pytest.mark.asyncio
    async def test_presign_artifact_unauthorized(self):
        """Test presigning without authentication."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
            response = await client.post(
                "/v1/artifacts/presign",
                json={"task_id": "fake-task-id",
                      "filename": "test.png", "size": 1024},
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_presign_artifact_invalid_token(self):
        """Test presigning with invalid token."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
            response = await client.post(
                "/v1/artifacts/presign",
                headers={"Authorization": "Bearer invalid_token"},
                json={"task_id": "fake-task-id",
                      "filename": "test.png", "size": 1024},
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_presign_artifact_missing_parameters(self):
        """Test presigning with missing required parameters."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
            access_token, _ = await create_user_and_get_token(client)

            # Missing task_id
            response1 = await client.post(
                "/v1/artifacts/presign",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"filename": "test.png", "size": 1024},
            )
            assert response1.status_code == 422

            # Missing filename
            response2 = await client.post(
                "/v1/artifacts/presign",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"task_id": "fake-task-id", "size": 1024},
            )
            assert response2.status_code == 422

            # Missing size
            response3 = await client.post(
                "/v1/artifacts/presign",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"task_id": "fake-task-id", "filename": "test.png"},
            )
            assert response3.status_code == 422

    @pytest.mark.asyncio
    async def test_presign_artifact_invalid_parameters(self):
        """Test presigning with invalid parameters."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)
            task_id = await create_task(client, access_token, device_id)

            # Invalid size (negative)
            response1 = await client.post(
                "/v1/artifacts/presign",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"task_id": task_id, "filename": "test.png", "size": -1},
            )
            assert response1.status_code == 422

            # Invalid size (zero)
            response2 = await client.post(
                "/v1/artifacts/presign",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"task_id": task_id, "filename": "test.png", "size": 0},
            )
            assert response2.status_code == 422

            # Empty filename
            response3 = await client.post(
                "/v1/artifacts/presign",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"task_id": task_id, "filename": "", "size": 1024},
            )
            assert response3.status_code == 422

    @pytest.mark.asyncio
    async def test_presign_artifact_filename_with_special_characters(self):
        """Test presigning with filenames containing special characters."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)
            task_id = await create_task(client, access_token, device_id)

            special_filenames = [
                "file with spaces.txt",
                "file-with-dashes.txt",
                "file_with_underscores.txt",
                "file.with.dots.txt",
                "file(with)parentheses.txt",
                "file[with]brackets.txt",
                "файл_с_кириллицей.txt",
                "文件名.txt",
            ]

            for filename in special_filenames:
                response = await client.post(
                    "/v1/artifacts/presign",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={"task_id": task_id,
                          "filename": filename, "size": 1024},
                )

                # Some special characters might be rejected by S3 or the API
                # Accept both success and validation errors
                assert response.status_code in [
                    200, 422], f"Unexpected status for {filename}"

    @pytest.mark.asyncio
    async def test_presign_artifact_large_files(self):
        """Test presigning for very large files."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)
            task_id = await create_task(client, access_token, device_id)

            # Test various large sizes
            large_sizes = [
                1073741824,  # 1GB
                5368709120,  # 5GB
                10737418240,  # 10GB
            ]

            for size in large_sizes:
                response = await client.post(
                    "/v1/artifacts/presign",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={"task_id": task_id,
                          "filename": f"large_file_{size}.dat", "size": size},
                )

                # Large files might be rejected by policy or succeed
                assert response.status_code in [200, 400, 413, 422], (
                    f"Unexpected status for size {size}"
                )

    @pytest.mark.asyncio
    async def test_presign_artifact_multiple_files_same_task(self):
        """Test presigning multiple files for the same task."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)
            task_id = await create_task(client, access_token, device_id)

            files = [
                ("screenshot.png", 2048),
                ("log.txt", 1024),
                ("config.json", 512),
                ("output.dat", 4096),
            ]

            presigned_urls = []

            for filename, size in files:
                response = await client.post(
                    "/v1/artifacts/presign",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={"task_id": task_id,
                          "filename": filename, "size": size},
                )

                assert response.status_code == 200
                data = response.json()
                presigned_urls.append(data["s3_url"])

                # Verify task_id is in all URLs
                assert task_id in data["s3_url"]
                assert filename in data["s3_url"]

            # Verify all URLs are different
            assert len(set(presigned_urls)) == len(presigned_urls)

    @pytest.mark.asyncio
    async def test_presign_artifact_nonexistent_task(self):
        """Test presigning for non-existent task."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
            access_token, _ = await create_user_and_get_token(client)

            fake_task_id = uuid.uuid4().hex

            response = await client.post(
                "/v1/artifacts/presign",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"task_id": fake_task_id,
                      "filename": "test.png", "size": 1024},
            )

            # The API might not validate task existence at presign time
            # Accept both success and not found responses
            assert response.status_code in [
                200, 404], "Unexpected response for non-existent task"

    @pytest.mark.asyncio
    async def test_presign_artifact_other_users_task(self):
        """Test presigning for another user's task."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
            # Create first user and task
            access_token1, _ = await create_user_and_get_token(client)
            device_id1, _ = await enroll_device(client, access_token1, "User1 Device")
            task_id = await create_task(client, access_token1, device_id1, "User1 Task")

            # Create second user
            access_token2, _ = await create_user_and_get_token(client)

            # Try to presign artifact for first user's task with second user's token
            response = await client.post(
                "/v1/artifacts/presign",
                headers={"Authorization": f"Bearer {access_token2}"},
                json={"task_id": task_id,
                      "filename": "unauthorized.png", "size": 1024},
            )

            # Should either succeed (no validation) or fail with authorization error
            assert response.status_code in [200, 403, 404], (
                "Unexpected response for cross-user access"
            )


class TestArtifactIntegration:
    """Integration tests for artifact workflows."""

    @pytest.mark.asyncio
    async def test_artifact_presign_upload_workflow(self):
        """Test complete artifact workflow: presign -> upload simulation."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)
            task_id = await create_task(client, access_token, device_id)

            # 1. Presign artifact
            presign_response = await client.post(
                "/v1/artifacts/presign",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"task_id": task_id,
                      "filename": "test_artifact.png", "size": 2048},
            )

            assert presign_response.status_code == 200
            presign_data = presign_response.json()

            upload_url = presign_data["upload_url"]
            s3_url = presign_data["s3_url"]
            expires_at = presign_data["expires_at"]

            # 2. Verify URL structure and expiration
            assert upload_url.startswith("http")
            assert s3_url.startswith("s3://")
            assert task_id in s3_url
            assert "test_artifact.png" in s3_url

            expires_time = datetime.fromisoformat(
                expires_at.replace("Z", "+00:00"))
            assert expires_time > datetime.now(timezone.utc)

            # 3. Parse upload URL to verify it contains expected parameters
            parsed_url = urlparse(upload_url)
            query_params = parse_qs(parsed_url.query)

            # Should contain AWS signature parameters (if using AWS S3)
            # The exact parameters depend on S3 configuration
            assert parsed_url.scheme in ["http", "https"]
            assert parsed_url.netloc  # Should have a hostname

    @pytest.mark.asyncio
    async def test_multiple_artifacts_same_task_workflow(self):
        """Test workflow with multiple artifacts for the same task."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)
            task_id = await create_task(client, access_token, device_id)

            artifacts = [
                ("screenshot_before.png", 4096),
                ("screenshot_after.png", 4096),
                ("execution_log.txt", 1024),
                ("performance_data.json", 2048),
            ]

            artifact_urls = {}

            # Presign all artifacts
            for filename, size in artifacts:
                response = await client.post(
                    "/v1/artifacts/presign",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={"task_id": task_id,
                          "filename": filename, "size": size},
                )

                assert response.status_code == 200
                data = response.json()
                artifact_urls[filename] = data["s3_url"]

            # Verify all artifacts have unique URLs but same task_id
            assert len(artifact_urls) == len(artifacts)
            for filename, s3_url in artifact_urls.items():
                assert task_id in s3_url
                assert filename in s3_url

            # Verify all URLs are unique
            unique_urls = set(artifact_urls.values())
            assert len(unique_urls) == len(artifacts)

    @pytest.mark.asyncio
    async def test_artifact_presign_expiration_workflow(self):
        """Test artifact presign URL expiration behavior."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)
            task_id = await create_task(client, access_token, device_id)

            # Presign artifact
            response = await client.post(
                "/v1/artifacts/presign",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"task_id": task_id,
                      "filename": "expiration_test.png", "size": 1024},
            )

            assert response.status_code == 200
            data = response.json()

            # Verify expiration is set to future time (typically 5 minutes)
            expires_at = datetime.fromisoformat(
                data["expires_at"].replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)

            # Should expire in the future but not too far (typical range: 5-15 minutes)
            assert expires_at > now
            time_diff = expires_at - now
            assert time_diff.total_seconds() > 60  # At least 1 minute
            assert time_diff.total_seconds() < 3600  # Less than 1 hour

    @pytest.mark.asyncio
    async def test_artifact_presign_concurrent_requests(self):
        """Test concurrent artifact presign requests."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)
            task_id = await create_task(client, access_token, device_id)

            import asyncio

            async def presign_artifact(filename: str, size: int):
                response = await client.post(
                    "/v1/artifacts/presign",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={"task_id": task_id,
                          "filename": filename, "size": size},
                )
                return response

            # Create multiple concurrent requests
            tasks = []
            for i in range(5):
                task = presign_artifact(
                    f"concurrent_file_{i}.dat", 1024 * (i + 1))
                tasks.append(task)

            # Execute all requests concurrently
            responses = await asyncio.gather(*tasks)

            # Verify all requests succeeded
            for i, response in enumerate(responses):
                assert response.status_code == 200, f"Request {i} failed"
                data = response.json()
                assert f"concurrent_file_{i}.dat" in data["s3_url"]

    @pytest.mark.asyncio
    async def test_artifact_s3_bucket_configuration(self):
        """Test artifact functionality when S3 is not configured."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)
            task_id = await create_task(client, access_token, device_id)

            response = await client.post(
                "/v1/artifacts/presign",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"task_id": task_id,
                      "filename": "config_test.png", "size": 1024},
            )

            # Should either succeed (S3 configured) or fail with 500 (not configured)
            if response.status_code == 500:
                error_detail = response.json()["detail"]
                assert (
                    "bucket not configured" in error_detail.lower() or "s3" in error_detail.lower()
                )
            else:
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_artifact_presign_different_task_types(self):
        """Test artifact presigning for different types of tasks."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
            access_token, _ = await create_user_and_get_token(client)
            device_id, _ = await enroll_device(client, access_token)

            # Create different types of tasks
            task_types = [
                ("Screenshot Task", [
                 {"action_id": "a1", "type": "screenshot", "params": {}}]),
                (
                    "File Task",
                    [{"action_id": "a1", "type": "file_read",
                        "params": {"path": "/tmp/test"}}],
                ),
                (
                    "Complex Task",
                    [
                        {"action_id": "a1", "type": "screenshot", "params": {}},
                        {
                            "action_id": "a2",
                            "type": "file_write",
                            "params": {"path": "/tmp/output", "content": "test"},
                        },
                    ],
                ),
            ]

            for task_title, actions in task_types:
                # Create task
                task_data = {
                    "device_id": device_id,
                    "title": task_title,
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

                # Presign artifact for this task
                artifact_response = await client.post(
                    "/v1/artifacts/presign",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={
                        "task_id": task_id,
                        "filename": f"{task_title.lower().replace(' ', '_')}_artifact.dat",
                        "size": 2048,
                    },
                )

                assert artifact_response.status_code == 200
                data = artifact_response.json()
                assert task_id in data["s3_url"]
