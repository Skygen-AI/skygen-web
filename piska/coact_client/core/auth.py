"""
Authentication module for Coact Client

Handles user authentication, token management, and secure credential storage.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
import aiohttp

from coact_client.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class Tokens:
    """Authentication tokens"""
    access_token: str
    refresh_token: str
    expires_at: datetime
    token_type: str = "bearer"

    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """Check if access token is expired (with buffer)"""
        if not self.expires_at:
            return True
        return datetime.now(timezone.utc) >= self.expires_at - timedelta(seconds=buffer_seconds)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data["expires_at"] = self.expires_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tokens":
        """Create from dictionary"""
        data = data.copy()
        if isinstance(data["expires_at"], str):
            data["expires_at"] = datetime.fromisoformat(data["expires_at"])
        return cls(**data)


class CredentialStorage:
    """Secure credential storage using encryption"""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.key_path = storage_path.parent / ".key"
        self._fernet: Optional[Fernet] = None

    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key"""
        if self.key_path.exists():
            return self.key_path.read_bytes()
        else:
            key = Fernet.generate_key()
            self.key_path.write_bytes(key)
            self.key_path.chmod(0o600)  # Read/write for owner only
            return key

    def _get_fernet(self) -> Fernet:
        """Get Fernet instance"""
        if self._fernet is None:
            key = self._get_or_create_key()
            self._fernet = Fernet(key)
        return self._fernet

    def save_credentials(self, email: str, tokens: Tokens) -> None:
        """Save encrypted credentials"""
        data = {
            "email": email,
            "tokens": tokens.to_dict(),
            "saved_at": datetime.now(timezone.utc).isoformat()
        }

        encrypted_data = self._get_fernet().encrypt(json.dumps(data).encode())
        self.storage_path.write_bytes(encrypted_data)
        self.storage_path.chmod(0o600)

        logger.info("Credentials saved securely")

    def load_credentials(self) -> Optional[tuple[str, Tokens]]:
        """Load and decrypt credentials"""
        if not self.storage_path.exists():
            return None

        try:
            encrypted_data = self.storage_path.read_bytes()
            decrypted_data = self._get_fernet().decrypt(encrypted_data)
            data = json.loads(decrypted_data.decode())

            email = data["email"]
            tokens = Tokens.from_dict(data["tokens"])

            logger.info("Credentials loaded successfully")
            return email, tokens

        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return None

    def clear_credentials(self) -> None:
        """Remove stored credentials"""
        if self.storage_path.exists():
            self.storage_path.unlink()
        logger.info("Credentials cleared")


class AuthenticationError(Exception):
    """Authentication related errors"""
    pass


class AuthClient:
    """Authentication client for Coact API"""

    def __init__(self):
        self.api_url = settings.server["api_url"]
        self.timeout = settings.server["timeout"]
        self.storage = CredentialStorage(settings.get_credentials_file())
        self._session: Optional[aiohttp.ClientSession] = None
        self._current_tokens: Optional[Tokens] = None
        self._current_email: Optional[str] = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def _ensure_session(self) -> None:
        """Ensure HTTP session exists"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"User-Agent": f"Coact-Client/{settings.app_version}"}
            )

    async def close(self) -> None:
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def signup(self, email: str, password: str, auto_login: bool = True) -> bool:
        """Register new user account"""
        await self._ensure_session()

        url = f"{self.api_url}/v1/auth/signup"
        data = {"email": email, "password": password}

        try:
            async with self._session.post(url, json=data) as response:
                if response.status == 201:
                    result = await response.json()
                    logger.info(
                        f"User registered successfully: {result.get('email')}")

                    # Автоматически логинимся после успешной регистрации
                    if auto_login:
                        try:
                            await self.login(email, password, save_credentials=True, auto_enroll_device=True)
                            logger.info(
                                "Auto-login and device enrollment completed after signup")
                        except Exception as e:
                            logger.warning(
                                f"Auto-login after signup failed: {e}")

                    return True
                else:
                    error_text = await response.text()
                    raise AuthenticationError(f"Signup failed: {error_text}")

        except aiohttp.ClientError as e:
            logger.error(f"Network error during signup: {e}")
            raise AuthenticationError(f"Network error: {e}")

    async def login(self, email: str, password: str, save_credentials: bool = True, auto_enroll_device: bool = True) -> Tokens:
        """Authenticate user and get tokens"""
        await self._ensure_session()

        url = f"{self.api_url}/v1/auth/login"
        data = {"email": email, "password": password}

        try:
            async with self._session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()

                    # Calculate token expiration (assuming 1 hour for access token)
                    expires_at = datetime.now(
                        timezone.utc) + timedelta(hours=1)

                    tokens = Tokens(
                        access_token=result["access_token"],
                        refresh_token=result["refresh_token"],
                        expires_at=expires_at,
                        token_type=result.get("token_type", "bearer")
                    )

                    self._current_tokens = tokens
                    self._current_email = email

                    if save_credentials:
                        self.storage.save_credentials(email, tokens)

                    logger.info(f"User authenticated successfully: {email}")

                    # Автоматически регистрируем устройство после успешного логина
                    if auto_enroll_device:
                        try:
                            from coact_client.core.device import device_manager
                            await device_manager.enroll_device()
                            logger.info(
                                "Device auto-enrolled successfully after login")
                        except Exception as e:
                            logger.warning(
                                f"Auto device enrollment failed, but login successful: {e}")

                    return tokens

                else:
                    error_text = await response.text()
                    raise AuthenticationError(f"Login failed: {error_text}")

        except aiohttp.ClientError as e:
            logger.error(f"Network error during login: {e}")
            raise AuthenticationError(f"Network error: {e}")

    async def refresh_tokens(self, refresh_token: str) -> Tokens:
        """Refresh access token"""
        await self._ensure_session()

        url = f"{self.api_url}/v1/auth/refresh"
        data = {"token": refresh_token}

        try:
            async with self._session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()

                    expires_at = datetime.now(
                        timezone.utc) + timedelta(hours=1)

                    tokens = Tokens(
                        access_token=result["access_token"],
                        refresh_token=result["refresh_token"],
                        expires_at=expires_at,
                        token_type=result.get("token_type", "bearer")
                    )

                    self._current_tokens = tokens

                    # Save updated tokens
                    if self._current_email:
                        self.storage.save_credentials(
                            self._current_email, tokens)

                    logger.info("Tokens refreshed successfully")
                    return tokens

                else:
                    error_text = await response.text()
                    raise AuthenticationError(
                        f"Token refresh failed: {error_text}")

        except aiohttp.ClientError as e:
            logger.error(f"Network error during token refresh: {e}")
            raise AuthenticationError(f"Network error: {e}")

    async def ensure_valid_tokens(self) -> Optional[Tokens]:
        """Ensure we have valid tokens, refresh if needed"""
        # Try to load from storage if not in memory
        if self._current_tokens is None:
            credentials = self.storage.load_credentials()
            if credentials:
                self._current_email, self._current_tokens = credentials

        if self._current_tokens is None:
            return None

        # Check if tokens need refreshing
        if self._current_tokens.is_expired():
            try:
                self._current_tokens = await self.refresh_tokens(self._current_tokens.refresh_token)
            except AuthenticationError as e:
                logger.error(f"Failed to refresh tokens: {e}")
                self._current_tokens = None
                self._current_email = None
                return None

        return self._current_tokens

    def get_auth_header(self) -> Optional[str]:
        """Get authorization header value"""
        if self._current_tokens:
            return f"{self._current_tokens.token_type} {self._current_tokens.access_token}"
        return None

    async def logout(self) -> None:
        """Logout user and clear credentials"""
        self._current_tokens = None
        self._current_email = None
        self.storage.clear_credentials()
        logger.info("User logged out")

    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        return self._current_tokens is not None and not self._current_tokens.is_expired()

    def get_current_email(self) -> Optional[str]:
        """Get current authenticated user email"""
        return self._current_email


# Global auth client instance
auth_client = AuthClient()
