"""
Comprehensive tests for approval system API endpoints.

Tests approval workflow, risk assessment, and automatic cancellation.
"""

import os
import pytest
import uuid
import httpx


BASE_URL = os.getenv("BASE_URL", "http://0.0.0.0:8000")


async def create_user_and_login():
    """Helper function to create a user and get auth headers"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        email = f"test_{uuid.uuid4().hex[:12]}@test.com"
        password = "SecurePassword123!"
        
        signup_response = await client.post(
            "/v1/auth/signup", json={"email": email, "password": password}
        )
        assert signup_response.status_code == 201
        user_data = signup_response.json()
        
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


@pytest.mark.asyncio
class TestApprovalsAPI:
    """Test approval system endpoints"""

    async def test_create_approval_request(self):
        """Test creating an approval request"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]
            
            payload = {
                "task_name": "High Risk Task",
                "actions": [
                    {"action_id": "1", "type": "file_delete", "params": {"path": "/important/file"}}
                ],
                "reason": "Need to clean up old files",
                "risk_level": "high"
            }

            response = await client.post(
                "/v1/approvals/",
                json=payload,
                headers=auth_headers
            )

            assert response.status_code == 201
            data = response.json()
            assert "id" in data
            assert data["status"] == "pending"
            assert data["risk_level"] == "high"

    async def test_list_approval_requests(self):
        """Test listing approval requests"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]

            response = await client.get(
                "/v1/approvals/",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    async def test_approve_request(self):
        """Test approving a request"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]
            
            # Create approval request first
            payload = {
                "task_name": "Test Task",
                "actions": [{"action_id": "1", "type": "screenshot", "params": {}}],
                "reason": "Testing",
                "risk_level": "low"
            }

            create_response = await client.post(
                "/v1/approvals/",
                json=payload,
                headers=auth_headers
            )
            approval_id = create_response.json()["id"]

            # Approve the request
            response = await client.post(
                f"/v1/approvals/{approval_id}/approve",
                json={"comment": "Approved for testing"},
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "approved"

    async def test_reject_request(self):
        """Test rejecting a request"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            auth_data = await create_user_and_login()
            auth_headers = auth_data["headers"]
            
            # Create approval request first
            payload = {
                "task_name": "Test Task",
                "actions": [{"action_id": "1", "type": "screenshot", "params": {}}],
                "reason": "Testing",
                "risk_level": "medium"
            }

            create_response = await client.post(
                "/v1/approvals/",
                json=payload,
                headers=auth_headers
            )
            approval_id = create_response.json()["id"]

            # Reject the request
            response = await client.post(
                f"/v1/approvals/{approval_id}/reject",
                json={"comment": "Too risky"},
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "rejected"

    async def test_unauthorized_access(self):
        """Test unauthorized access to approval endpoints"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            endpoints = [
                ("GET", "/v1/approvals/"),
                ("POST", "/v1/approvals/"),
                ("POST", f"/v1/approvals/{uuid.uuid4()}/approve"),
                ("POST", f"/v1/approvals/{uuid.uuid4()}/reject"),
            ]

            for method, url in endpoints:
                response = await client.request(method, url)
                assert response.status_code == 401