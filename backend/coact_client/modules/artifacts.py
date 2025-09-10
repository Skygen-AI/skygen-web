"""
Artifact upload module

Handles uploading files, screenshots, and other artifacts to the server.
"""

import asyncio
import logging
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional
import aiohttp

from coact_client.config.settings import settings
from coact_client.core.auth import auth_client

logger = logging.getLogger(__name__)


class ArtifactError(Exception):
    """Artifact upload errors"""
    pass


class ArtifactUploader:
    """Artifact upload handler"""
    
    def __init__(self):
        self.api_url = settings.server.api_url
        self.timeout = settings.server.timeout
        self.max_file_size = settings.security.max_file_size_mb * 1024 * 1024
        self.allowed_extensions = set(settings.security.allowed_file_extensions)
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
            timeout = aiohttp.ClientTimeout(total=self.timeout * 2)  # Upload timeout is longer
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"User-Agent": f"Coact-Client/{settings.app_version}"}
            )
    
    async def close(self) -> None:
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def upload_artifact(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Upload artifact file"""
        filepath = action.get("filepath")
        task_id = action.get("task_id")
        
        if not filepath:
            raise ArtifactError("No filepath provided")
        if not task_id:
            raise ArtifactError("No task_id provided")
        
        filepath = Path(filepath)
        if not filepath.exists():
            raise ArtifactError(f"File not found: {filepath}")
        
        # Validate file
        self._validate_file(filepath)
        
        try:
            # Get presigned upload URL
            presign_data = await self._get_presigned_url(task_id, filepath)
            
            # Upload file
            upload_result = await self._upload_to_storage(filepath, presign_data)
            
            logger.info(f"Artifact uploaded successfully: {filepath.name}")
            
            return {
                "success": True,
                "filepath": str(filepath),
                "filename": filepath.name,
                "size_bytes": filepath.stat().st_size,
                "upload_url": upload_result.get("upload_url"),
                "public_url": upload_result.get("public_url"),
                "s3_url": upload_result.get("s3_url")
            }
            
        except Exception as e:
            logger.error(f"Artifact upload failed: {e}")
            raise ArtifactError(f"Upload failed: {e}")
    
    def _validate_file(self, filepath: Path) -> None:
        """Validate file for upload"""
        # Check file size
        file_size = filepath.stat().st_size
        if file_size > self.max_file_size:
            raise ArtifactError(f"File too large: {file_size} bytes (max: {self.max_file_size})")
        
        # Check file extension
        if self.allowed_extensions:
            extension = filepath.suffix.lower()
            if extension not in self.allowed_extensions:
                raise ArtifactError(f"File type not allowed: {extension}")
        
        # Basic security checks
        filename = filepath.name.lower()
        dangerous_extensions = {".exe", ".bat", ".sh", ".ps1", ".vbs", ".scr", ".com", ".pif"}
        if any(filename.endswith(ext) for ext in dangerous_extensions):
            raise ArtifactError(f"Dangerous file type: {filename}")
    
    async def _get_presigned_url(self, task_id: str, filepath: Path) -> Dict[str, Any]:
        """Get presigned upload URL from server"""
        await auth_client.ensure_valid_tokens()
        if not auth_client.is_authenticated():
            raise ArtifactError("Authentication required")
        
        await self._ensure_session()
        
        url = f"{self.api_url}/v1/artifacts/presign"
        headers = {"Authorization": auth_client.get_auth_header()}
        
        data = {
            "task_id": task_id,
            "filename": filepath.name,
            "size": filepath.stat().st_size
        }
        
        async with self._session.post(url, json=data, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise ArtifactError(f"Failed to get presigned URL: {error_text}")
    
    async def _upload_to_storage(self, filepath: Path, presign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upload file to storage using presigned URL"""
        upload_url = presign_data.get("upload_url")
        if not upload_url:
            raise ArtifactError("No upload URL provided")
        
        # Determine content type
        content_type = mimetypes.guess_type(filepath)[0] or "application/octet-stream"
        
        # Prepare upload data
        headers = {
            "Content-Type": content_type,
            "Content-Length": str(filepath.stat().st_size)
        }
        
        # Add any additional fields from presign response
        fields = presign_data.get("fields", {})
        if fields:
            # For S3-style uploads with form fields
            data = aiohttp.FormData()
            for key, value in fields.items():
                data.add_field(key, value)
            
            # Add file
            data.add_field(
                "file",
                filepath.open("rb"),
                filename=filepath.name,
                content_type=content_type
            )
            
            # Upload using POST with form data
            async with self._session.post(upload_url, data=data) as response:
                if response.status in (200, 201, 204):
                    return {
                        "success": True,
                        "upload_url": upload_url,
                        "public_url": presign_data.get("public_url"),
                        "s3_url": presign_data.get("s3_url")
                    }
                else:
                    error_text = await response.text()
                    raise ArtifactError(f"Storage upload failed: {error_text}")
        else:
            # Direct PUT upload
            with filepath.open("rb") as f:
                async with self._session.put(upload_url, data=f, headers=headers) as response:
                    if response.status in (200, 201, 204):
                        return {
                            "success": True,
                            "upload_url": upload_url,
                            "public_url": presign_data.get("public_url"),
                            "s3_url": presign_data.get("s3_url")
                        }
                    else:
                        error_text = await response.text()
                        raise ArtifactError(f"Storage upload failed: {error_text}")
    
    async def upload_screenshot(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Upload screenshot artifact"""
        # Take screenshot first if not provided
        if "filepath" not in action:
            from coact_client.modules.screen import screen_module
            screenshot_result = await screen_module.take_screenshot(action)
            action["filepath"] = screenshot_result["filepath"]
        
        # Upload the screenshot
        return await self.upload_artifact(action)
    
    async def upload_log_file(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Upload log file artifact"""
        log_type = action.get("log_type", "application")
        
        if log_type == "application":
            # Upload main application log
            log_file = settings.get_log_file()
        else:
            # Custom log file path
            log_file = Path(action.get("filepath", ""))
        
        if not log_file.exists():
            raise ArtifactError(f"Log file not found: {log_file}")
        
        # Create action for upload
        upload_action = action.copy()
        upload_action["filepath"] = str(log_file)
        
        return await self.upload_artifact(upload_action)
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get artifact uploader configuration"""
        return {
            "max_file_size_mb": settings.security.max_file_size_mb,
            "allowed_extensions": list(self.allowed_extensions),
            "api_url": self.api_url,
            "timeout": self.timeout
        }


# Global artifact uploader instance
artifact_uploader = ArtifactUploader()