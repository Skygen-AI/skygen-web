"""
Device management module

Handles device enrollment, token management, and device information.
"""

import json
import uuid
import platform
import psutil
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

import aiohttp

from coact_client.config.settings import settings
from coact_client.core.auth import auth_client, AuthenticationError

logger = logging.getLogger(__name__)


@dataclass
class DeviceInfo:
    """Device information"""
    device_id: str
    device_name: str
    platform: str
    capabilities: Dict[str, Any]
    device_token: str
    wss_url: str
    kid: str
    expires_at: datetime
    enrolled_at: datetime
    
    def is_token_expired(self, buffer_seconds: int = 300) -> bool:
        """Check if device token is expired"""
        return datetime.now(timezone.utc) >= self.expires_at - timedelta(seconds=buffer_seconds)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data["expires_at"] = self.expires_at.isoformat()
        data["enrolled_at"] = self.enrolled_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceInfo":
        """Create from dictionary"""
        data = data.copy()
        for field in ["expires_at", "enrolled_at"]:
            if isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])
        return cls(**data)


class DeviceError(Exception):
    """Device related errors"""
    pass


class DeviceManager:
    """Device enrollment and management"""
    
    def __init__(self):
        self.api_url = settings.server.api_url
        self.timeout = settings.server.timeout
        self.device_file = settings.data_dir / "device.json"
        self._device_info: Optional[DeviceInfo] = None
        self._session: Optional[aiohttp.ClientSession] = None
    
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
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get detailed system information"""
        try:
            cpu_info = {
                "count": psutil.cpu_count(),
                "count_logical": psutil.cpu_count(logical=True),
                "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            }
            
            memory_info = psutil.virtual_memory()._asdict()
            disk_info = psutil.disk_usage('/')._asdict()
            
            return {
                "hostname": platform.node(),
                "platform": platform.platform(),
                "architecture": platform.architecture()[0],
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "cpu": cpu_info,
                "memory": memory_info,
                "disk": disk_info,
                "screen_resolution": self._get_screen_resolution(),
                "installed_software": self._get_installed_software(),
            }
        except Exception as e:
            logger.warning(f"Could not gather complete system info: {e}")
            return {
                "hostname": platform.node(),
                "platform": platform.platform(),
                "error": str(e)
            }
    
    def _get_screen_resolution(self) -> Optional[Dict[str, int]]:
        """Get screen resolution"""
        try:
            import pyautogui
            width, height = pyautogui.size()
            return {"width": width, "height": height}
        except Exception:
            return None
    
    def _get_installed_software(self) -> Dict[str, bool]:
        """Check for commonly used software"""
        software_check = {}
        
        # Check for common applications
        try:
            import subprocess
            import shutil
            
            apps_to_check = [
                "chrome", "firefox", "safari", "edge",
                "vscode", "code", "sublime", "atom",
                "docker", "git", "node", "python", "java"
            ]
            
            for app in apps_to_check:
                software_check[app] = shutil.which(app) is not None
                
        except Exception:
            pass
        
        return software_check
    
    async def enroll_device(self, force_reenroll: bool = False) -> DeviceInfo:
        """Enroll this device with the server"""
        # Check if already enrolled and valid
        if not force_reenroll:
            existing_device = self.load_device_info()
            if existing_device and not existing_device.is_token_expired():
                logger.info(f"Device already enrolled: {existing_device.device_id}")
                self._device_info = existing_device
                return existing_device
        
        # Ensure we have valid authentication
        await auth_client.ensure_valid_tokens()
        if not auth_client.is_authenticated():
            raise DeviceError("Authentication required for device enrollment")
        
        await self._ensure_session()
        
        # Prepare enrollment data
        system_info = self._get_system_info()
        device_name = settings.device.name or f"{system_info.get('hostname', 'unknown')}-{platform.system().lower()}"
        
        capabilities = settings.device.capabilities.copy()
        capabilities.update({
            "system_info": system_info,
            "max_concurrent_tasks": settings.device.max_concurrent_tasks,
            "client_version": settings.app_version,
        })
        
        enrollment_data = {
            "device_name": device_name,
            "platform": settings.device.platform,
            "capabilities": capabilities,
            "idempotency_key": str(uuid.uuid4())
        }
        
        # Enroll device
        url = f"{self.api_url}/v1/devices/enroll"
        headers = {"Authorization": auth_client.get_auth_header()}
        
        try:
            async with self._session.post(url, json=enrollment_data, headers=headers) as response:
                if response.status == 201:
                    result = await response.json()
                    
                    device_info = DeviceInfo(
                        device_id=result["device_id"],
                        device_name=device_name,
                        platform=settings.device.platform,
                        capabilities=capabilities,
                        device_token=result["device_token"],
                        wss_url=result["wss_url"],
                        kid=result["kid"],
                        expires_at=datetime.fromisoformat(result["expires_at"]),
                        enrolled_at=datetime.now(timezone.utc)
                    )
                    
                    self._device_info = device_info
                    self.save_device_info(device_info)
                    
                    logger.info(f"Device enrolled successfully: {device_info.device_id}")
                    return device_info
                    
                else:
                    error_text = await response.text()
                    raise DeviceError(f"Device enrollment failed: {error_text}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error during device enrollment: {e}")
            raise DeviceError(f"Network error: {e}")
    
    async def refresh_device_token(self) -> DeviceInfo:
        """Refresh device token"""
        if not self._device_info:
            raise DeviceError("No device information available")
        
        await auth_client.ensure_valid_tokens()
        if not auth_client.is_authenticated():
            raise DeviceError("Authentication required for token refresh")
        
        await self._ensure_session()
        
        url = f"{self.api_url}/v1/devices/token/refresh"
        headers = {"Authorization": auth_client.get_auth_header()}
        data = {"device_id": self._device_info.device_id}
        
        try:
            async with self._session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Update device info with new token
                    self._device_info.device_token = result["device_token"]
                    self._device_info.expires_at = datetime.fromisoformat(result["expires_at"])
                    self._device_info.kid = result["kid"]
                    
                    self.save_device_info(self._device_info)
                    
                    logger.info("Device token refreshed successfully")
                    return self._device_info
                    
                else:
                    error_text = await response.text()
                    raise DeviceError(f"Token refresh failed: {error_text}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error during token refresh: {e}")
            raise DeviceError(f"Network error: {e}")
    
    async def ensure_valid_device(self) -> Optional[DeviceInfo]:
        """Ensure device is enrolled and has valid token"""
        # Load device info if not in memory
        if self._device_info is None:
            self._device_info = self.load_device_info()
        
        if self._device_info is None:
            return None
        
        # Check if token needs refreshing
        if self._device_info.is_token_expired():
            try:
                self._device_info = await self.refresh_device_token()
            except DeviceError as e:
                logger.error(f"Failed to refresh device token: {e}")
                return None
        
        return self._device_info
    
    async def revoke_device(self) -> bool:
        """Revoke this device"""
        if not self._device_info:
            logger.warning("No device to revoke")
            return False
        
        await auth_client.ensure_valid_tokens()
        if not auth_client.is_authenticated():
            raise DeviceError("Authentication required for device revocation")
        
        await self._ensure_session()
        
        url = f"{self.api_url}/v1/devices/{self._device_info.device_id}/revoke"
        headers = {"Authorization": auth_client.get_auth_header()}
        
        try:
            async with self._session.post(url, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Device revoked: {result.get('revoked_count')} tokens revoked")
                    
                    self.clear_device_info()
                    return True
                    
                else:
                    error_text = await response.text()
                    raise DeviceError(f"Device revocation failed: {error_text}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error during device revocation: {e}")
            raise DeviceError(f"Network error: {e}")
    
    def save_device_info(self, device_info: DeviceInfo) -> None:
        """Save device information to file"""
        try:
            self.device_file.write_text(json.dumps(device_info.to_dict(), indent=2))
            self.device_file.chmod(0o600)  # Read/write for owner only
            logger.debug("Device information saved")
        except Exception as e:
            logger.error(f"Failed to save device information: {e}")
    
    def load_device_info(self) -> Optional[DeviceInfo]:
        """Load device information from file"""
        if not self.device_file.exists():
            return None
        
        try:
            data = json.loads(self.device_file.read_text())
            device_info = DeviceInfo.from_dict(data)
            logger.debug("Device information loaded")
            return device_info
        except Exception as e:
            logger.error(f"Failed to load device information: {e}")
            return None
    
    def clear_device_info(self) -> None:
        """Clear device information"""
        if self.device_file.exists():
            self.device_file.unlink()
        self._device_info = None
        logger.info("Device information cleared")
    
    def is_enrolled(self) -> bool:
        """Check if device is enrolled"""
        if self._device_info is None:
            self._device_info = self.load_device_info()
        return self._device_info is not None and not self._device_info.is_token_expired()
    
    def get_device_info(self) -> Optional[DeviceInfo]:
        """Get current device information"""
        if self._device_info is None:
            self._device_info = self.load_device_info()
        return self._device_info


# Global device manager instance
device_manager = DeviceManager()