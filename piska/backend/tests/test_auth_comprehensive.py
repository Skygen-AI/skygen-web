"""
Comprehensive tests for Authentication endpoints.
Tests all auth endpoints with various scenarios including edge cases and error conditions.
"""

import os
import uuid
import pytest
import httpx


BASE_URL = os.getenv("BASE_URL", "http://0.0.0.0:8000")


class TestAuthSignup:
    """Test signup endpoint with various scenarios."""

    @pytest.mark.asyncio
    async def test_signup_success(self):
        """Test successful user signup."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            email = f"signup_{uuid.uuid4().hex[:12]}@test.com"
            password = "SecurePassword123!"

            response = await client.post(
                "/v1/auth/signup", json={"email": email, "password": password}
            )

            assert response.status_code == 201
            data = response.json()
            assert "id" in data
            assert data["email"] == email
            assert "password" not in data  # Ensure password is not returned

    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self):
        """Test signup with already existing email."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            email = f"dup_{uuid.uuid4().hex[:12]}@test.com"
            password = "SecurePassword123!"

            # First signup
            response1 = await client.post(
                "/v1/auth/signup", json={"email": email, "password": password}
            )
            assert response1.status_code == 201

            # Second signup with same email
            response2 = await client.post(
                "/v1/auth/signup", json={"email": email, "password": password}
            )
            assert response2.status_code == 409
            assert "already in use" in response2.json()["detail"]

    @pytest.mark.asyncio
    async def test_signup_invalid_email(self):
        """Test signup with invalid email format."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            response = await client.post(
                "/v1/auth/signup", json={"email": "invalid-email", "password": "SecurePassword123!"}
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_signup_weak_password(self):
        """Test signup with password that's too short."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            email = f"weak_{uuid.uuid4().hex[:12]}@test.com"

            response = await client.post(
                "/v1/auth/signup",
                json={
                    "email": email,
                    "password": "123",  # Too short
                },
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_signup_missing_fields(self):
        """Test signup with missing required fields."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Missing password
            response1 = await client.post(
                "/v1/auth/signup", json={"email": f"missing_{uuid.uuid4().hex[:12]}@test.com"}
            )
            assert response1.status_code == 422

            # Missing email
            response2 = await client.post(
                "/v1/auth/signup", json={"password": "SecurePassword123!"}
            )
            assert response2.status_code == 422


class TestAuthLogin:
    """Test login endpoint with various scenarios."""

    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            email = f"login_{uuid.uuid4().hex[:12]}@test.com"
            password = "SecurePassword123!"

            # Create user first
            signup_response = await client.post(
                "/v1/auth/signup", json={"email": email, "password": password}
            )
            assert signup_response.status_code == 201

            # Login
            login_response = await client.post(
                "/v1/auth/login", json={"email": email, "password": password}
            )

            assert login_response.status_code == 200
            data = login_response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"

            # Verify tokens are not empty
            assert len(data["access_token"]) > 0
            assert len(data["refresh_token"]) > 0

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            email = f"invalid_{uuid.uuid4().hex[:12]}@test.com"
            password = "SecurePassword123!"

            # Create user first
            await client.post("/v1/auth/signup", json={"email": email, "password": password})

            # Login with wrong password
            response = await client.post(
                "/v1/auth/login", json={"email": email, "password": "WrongPassword123!"}
            )

            assert response.status_code == 401
            assert "Invalid credentials" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self):
        """Test login with non-existent user."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            response = await client.post(
                "/v1/auth/login",
                json={
                    "email": f"nonexistent_{uuid.uuid4().hex[:12]}@test.com",
                    "password": "SecurePassword123!",
                },
            )

            assert response.status_code == 401
            assert "Invalid credentials" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_missing_fields(self):
        """Test login with missing required fields."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Missing password
            response1 = await client.post(
                "/v1/auth/login", json={"email": f"missing_{uuid.uuid4().hex[:12]}@test.com"}
            )
            assert response1.status_code == 422

            # Missing email
            response2 = await client.post("/v1/auth/login", json={"password": "SecurePassword123!"})
            assert response2.status_code == 422

    @pytest.mark.asyncio
    async def test_login_rate_limiting(self):
        """Test rate limiting on login endpoint."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            email = f"ratelimit_{uuid.uuid4().hex[:12]}@test.com"

            # Try multiple failed login attempts quickly
            # Note: This test might be flaky depending on rate limit settings
            for i in range(10):
                response = await client.post(
                    "/v1/auth/login", json={"email": email, "password": "WrongPassword123!"}
                )
                # After several attempts, we should get rate limited or account locked
                if response.status_code == 429:
                    assert "Too many login attempts" in response.json()["detail"]
                    break
                elif response.status_code == 423:
                    assert "Account temporarily locked" in response.json()["detail"]
                    break
                assert response.status_code == 401


class TestAuthRefresh:
    """Test refresh token endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_success(self):
        """Test successful token refresh."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            email = f"refresh_{uuid.uuid4().hex[:12]}@test.com"
            password = "SecurePassword123!"

            # Create user and login
            await client.post("/v1/auth/signup", json={"email": email, "password": password})

            login_response = await client.post(
                "/v1/auth/login", json={"email": email, "password": password}
            )
            assert login_response.status_code == 200

            refresh_token = login_response.json()["refresh_token"]

            # Use refresh token
            refresh_response = await client.post("/v1/auth/refresh", json={"token": refresh_token})

            assert refresh_response.status_code == 200
            data = refresh_response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"

            # Verify new tokens are different from original
            assert data["access_token"] != login_response.json()["access_token"]
            assert data["refresh_token"] != refresh_token

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self):
        """Test refresh with invalid token."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            response = await client.post(
                "/v1/auth/refresh", json={"token": "invalid_refresh_token"}
            )

            assert response.status_code == 401
            assert "Invalid refresh token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_used_token(self):
        """Test refresh with already used token (token rotation)."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            email = f"used_token_{uuid.uuid4().hex[:12]}@test.com"
            password = "SecurePassword123!"

            # Create user and login
            await client.post("/v1/auth/signup", json={"email": email, "password": password})

            login_response = await client.post(
                "/v1/auth/login", json={"email": email, "password": password}
            )
            refresh_token = login_response.json()["refresh_token"]

            # Use refresh token first time
            first_refresh = await client.post("/v1/auth/refresh", json={"token": refresh_token})
            assert first_refresh.status_code == 200

            # Try to use same token again (should fail due to rotation)
            second_refresh = await client.post("/v1/auth/refresh", json={"token": refresh_token})
            assert second_refresh.status_code == 401
            assert "Invalid refresh token" in second_refresh.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_missing_token(self):
        """Test refresh with missing token."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            response = await client.post("/v1/auth/refresh", json={})
            assert response.status_code == 422


class TestAuthIntegration:
    """Integration tests for auth flow."""

    @pytest.mark.asyncio
    async def test_complete_auth_flow(self):
        """Test complete authentication flow: signup -> login -> refresh -> use access token."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            email = f"flow_{uuid.uuid4().hex[:12]}@test.com"
            password = "SecurePassword123!"

            # 1. Signup
            signup_response = await client.post(
                "/v1/auth/signup", json={"email": email, "password": password}
            )
            assert signup_response.status_code == 201
            user_id = signup_response.json()["id"]

            # 2. Login
            login_response = await client.post(
                "/v1/auth/login", json={"email": email, "password": password}
            )
            assert login_response.status_code == 200

            access_token = login_response.json()["access_token"]
            refresh_token = login_response.json()["refresh_token"]

            # 3. Use access token (test with devices list endpoint)
            devices_response = await client.get(
                "/v1/devices/", headers={"Authorization": f"Bearer {access_token}"}
            )
            assert devices_response.status_code == 200
            assert isinstance(devices_response.json(), list)

            # 4. Refresh token
            refresh_response = await client.post("/v1/auth/refresh", json={"token": refresh_token})
            assert refresh_response.status_code == 200

            new_access_token = refresh_response.json()["access_token"]

            # 5. Use new access token
            devices_response2 = await client.get(
                "/v1/devices/", headers={"Authorization": f"Bearer {new_access_token}"}
            )
            assert devices_response2.status_code == 200

    @pytest.mark.asyncio
    async def test_access_token_validation(self):
        """Test access token validation on protected endpoints."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # Test without token
            response1 = await client.get("/v1/devices/")
            assert response1.status_code == 401

            # Test with invalid token
            response2 = await client.get(
                "/v1/devices/", headers={"Authorization": "Bearer invalid_token"}
            )
            assert response2.status_code == 401

            # Test with malformed authorization header
            response3 = await client.get(
                "/v1/devices/", headers={"Authorization": "invalid_format"}
            )
            assert response3.status_code == 401
