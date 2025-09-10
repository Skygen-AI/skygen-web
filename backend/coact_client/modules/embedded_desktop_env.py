"""
Embedded Desktop Environment Control Module

Integrates with local EmbeddedDesktopEnv to provide direct desktop automation 
capabilities on the current system (macOS/Linux/Windows).
"""

from coact_client.config.settings import settings
import asyncio
import logging
import tempfile
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import base64
from datetime import datetime
import sys
import os

# Add the local desktop_env to path
sys.path.insert(0, os.path.join(
    os.path.dirname(__file__), '..', '..', 'desktop_env'))


logger = logging.getLogger(__name__)

try:
    # Import directly from the embedded module to avoid importing the problematic desktop_env.py
    from desktop_env.embedded import EmbeddedDesktopEnv
    HAS_EMBEDDED_DESKTOP_ENV = True
    logger.info("✅ Local EmbeddedDesktopEnv loaded successfully")
except ImportError as e:
    HAS_EMBEDDED_DESKTOP_ENV = False
    logger.warning(f"❌ Local EmbeddedDesktopEnv not available: {e}")


class EmbeddedDesktopEnvError(Exception):
    """Embedded desktop environment specific errors"""
    pass


class EmbeddedDesktopEnvModule:
    """Embedded Desktop Environment Control Module

    This module provides direct desktop automation capabilities using the local
    EmbeddedDesktopEnv which works directly on the current system without VM overhead.
    """

    def __init__(self, platform_key: Optional[str] = None):
        """Initialize Embedded Desktop Environment Module

        Args:
            platform_key: Platform identifier (Darwin, Linux, Windows) 
                         If None, auto-detects current platform
        """
        self.platform_key = platform_key

        # Environment settings
        self.cache_dir = settings.cache_dir / "embedded_desktop_env"
        self.cache_dir.mkdir(exist_ok=True)

        # Environment instance
        self._env: Optional[EmbeddedDesktopEnv] = None
        self._initialized = False

        if not HAS_EMBEDDED_DESKTOP_ENV:
            logger.warning(
                "EmbeddedDesktopEnv not available - module will have limited functionality")

    async def initialize(self) -> Dict[str, Any]:
        """Initialize the embedded desktop environment"""
        if not HAS_EMBEDDED_DESKTOP_ENV:
            raise EmbeddedDesktopEnvError("EmbeddedDesktopEnv not available")

        try:
            # Initialize in background thread to avoid blocking
            def _init_env():
                self._env = EmbeddedDesktopEnv(platform_key=self.platform_key)
                self._initialized = True
                platform = self._env.platform()
                screen_size = self._env.screen_size()
                logger.info(
                    f"EmbeddedDesktopEnv initialized for {platform}, screen: {screen_size}")
                return platform, screen_size

            platform, screen_size = await asyncio.get_event_loop().run_in_executor(None, _init_env)

            return {
                "success": True,
                "platform": platform,
                "screen_size": screen_size,
                "platform_key": self.platform_key,
                "direct_control": True,
                "vm_required": False
            }

        except Exception as e:
            logger.error(
                f"Failed to initialize embedded desktop environment: {e}")
            raise EmbeddedDesktopEnvError(f"Initialization failed: {e}")

    async def take_screenshot(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Take a screenshot of the current desktop"""
        if not self._env:
            await self.initialize()

        try:
            # Extract parameters from action - they can be in 'parameters' field or directly in action
            parameters = action.get("parameters", {})
            include_base64 = parameters.get(
                "include_base64") or action.get("include_base64", False)

            def _get_screenshot():
                return self._env.screenshot_png_bytes()

            screenshot_bytes = await asyncio.get_event_loop().run_in_executor(None, _get_screenshot)

            # Save screenshot
            timestamp = int(datetime.utcnow().timestamp())
            screenshot_path = self.cache_dir / f"screenshot_{timestamp}.png"

            with open(screenshot_path, 'wb') as f:
                f.write(screenshot_bytes)

            # Get image dimensions (approximate from bytes length)
            # For more accurate dimensions, we could use PIL, but for now estimate
            estimated_size = len(screenshot_bytes)

            result = {
                "success": True,
                "screenshot_path": str(screenshot_path),
                "screenshot_size": estimated_size,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Include base64 if requested
            if include_base64:
                result["base64"] = base64.b64encode(screenshot_bytes).decode()

            logger.info(
                f"Screenshot taken: {screenshot_path} ({estimated_size} bytes)")

            # Try to upload to MinIO if task_id is available
            task_id = action.get("task_id")
            if task_id:
                try:
                    from coact_client.modules.artifacts import artifact_uploader
                    upload_result = await artifact_uploader.upload_artifact({
                        "filepath": str(screenshot_path),
                        "task_id": task_id
                    })
                    result.update({
                        "uploaded_to_minio": True,
                        "minio_url": upload_result.get("public_url"),
                        "s3_url": upload_result.get("s3_url")
                    })
                    logger.info(
                        f"Screenshot uploaded to MinIO: {upload_result.get('public_url')}")
                except Exception as e:
                    logger.warning(
                        f"Failed to upload screenshot to MinIO: {e}")
                    result["uploaded_to_minio"] = False
            else:
                result["uploaded_to_minio"] = False
                logger.info("No task_id provided, skipping MinIO upload")

            return result

        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            raise EmbeddedDesktopEnvError(f"Screenshot failed: {e}")

    async def get_accessibility_tree(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Get accessibility tree of the current desktop"""
        if not self._env:
            await self.initialize()

        try:
            def _get_tree():
                return self._env.a11y_tree_xml()

            tree_xml = await asyncio.get_event_loop().run_in_executor(None, _get_tree)

            return {
                "success": True,
                "accessibility_tree": tree_xml,
                "format": "xml",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get accessibility tree: {e}")
            raise EmbeddedDesktopEnvError(f"Accessibility tree failed: {e}")

    async def type_text(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Type text using keyboard"""
        if not self._env:
            await self.initialize()

        try:
            text = action.get("text", "")
            interval = action.get("interval", 0.1)

            if not text:
                raise EmbeddedDesktopEnvError("No text provided")

            def _type_text():
                self._env.type_text(text, interval=interval)

            await asyncio.get_event_loop().run_in_executor(None, _type_text)

            logger.info(
                f"Typed text: '{text[:50]}{'...' if len(text) > 50 else ''}'")

            return {
                "success": True,
                "text": text,
                "length": len(text),
                "interval": interval,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Type text failed: {e}")
            raise EmbeddedDesktopEnvError(f"Type text failed: {e}")

    async def execute_command(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system command"""
        if not self._env:
            await self.initialize()

        try:
            # Extract parameters from action - they can be in 'parameters' field or directly in action
            parameters = action.get("parameters", {})
            command = parameters.get("command") or action.get("command", "")
            shell = parameters.get("shell") or action.get("shell", False)
            timeout = parameters.get("timeout") or action.get("timeout", 120)

            if not command:
                raise EmbeddedDesktopEnvError("No command provided")

            def _execute_command():
                return self._env.exec(command, shell=shell, timeout=timeout)

            result = await asyncio.get_event_loop().run_in_executor(None, _execute_command)

            logger.info(
                f"Executed command: {command[:100]}{'...' if len(command) > 100 else ''}")

            return {
                "success": True,
                "command": command,
                "result": result,
                "shell": shell,
                "timeout": timeout,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise EmbeddedDesktopEnvError(f"Command execution failed: {e}")

    async def run_python_code(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Python code"""
        logger.info(f"🔍 run_python_code called with action: {action}")

        if not self._env:
            await self.initialize()

        try:
            # Debug: log the action structure
            logger.info(f"Python action received: {action}")

            # Extract parameters from action - they can be in 'parameters' field or directly in action
            parameters = action.get("parameters", {})
            code = parameters.get("code") or action.get("code", "")
            timeout = parameters.get("timeout") or action.get("timeout", 30)

            logger.info(f"Extracted code: '{code}', parameters: {parameters}")

            if not code:
                raise EmbeddedDesktopEnvError("No code provided")

            def _run_python():
                return self._env.run_python(code, timeout=timeout)

            result = await asyncio.get_event_loop().run_in_executor(None, _run_python)

            logger.info(f"Executed Python code: {len(code)} characters")

            return {
                "success": True,
                "code": code,
                "result": result,
                "timeout": timeout,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Python code execution failed: {e}")
            raise EmbeddedDesktopEnvError(f"Python code execution failed: {e}")

    async def open_file_or_app(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Open file or application"""
        if not self._env:
            await self.initialize()

        try:
            path_or_app = action.get("path_or_app", "")

            if not path_or_app:
                raise EmbeddedDesktopEnvError("No path or app provided")

            def _open():
                return self._env.open_file_or_app(path_or_app)

            result = await asyncio.get_event_loop().run_in_executor(None, _open)

            logger.info(f"Opened: {path_or_app}")

            return {
                "success": True,
                "path_or_app": path_or_app,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(
                f"Failed to open {action.get('path_or_app', '')}: {e}")
            raise EmbeddedDesktopEnvError(f"Open failed: {e}")

    async def activate_window(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Activate window by title"""
        if not self._env:
            await self.initialize()

        try:
            title = action.get("title", "")
            strict = action.get("strict", False)
            by_class = action.get("by_class", False)

            if not title:
                raise EmbeddedDesktopEnvError("No window title provided")

            def _activate():
                return self._env.activate_window(title, strict=strict, by_class=by_class)

            success = await asyncio.get_event_loop().run_in_executor(None, _activate)

            logger.info(
                f"Window activation {'succeeded' if success else 'failed'}: {title}")

            return {
                "success": success,
                "title": title,
                "strict": strict,
                "by_class": by_class,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Window activation failed: {e}")
            raise EmbeddedDesktopEnvError(f"Window activation failed: {e}")

    async def get_system_info(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Get system information"""
        if not self._env:
            await self.initialize()

        try:
            def _get_info():
                platform = self._env.platform()
                screen_size = self._env.screen_size()
                cursor_position = self._env.cursor_position()
                return platform, screen_size, cursor_position

            platform, screen_size, cursor_position = await asyncio.get_event_loop().run_in_executor(None, _get_info)

            return {
                "success": True,
                "platform": platform,
                "screen_size": screen_size,
                "cursor_position": cursor_position,
                "direct_control": True,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            raise EmbeddedDesktopEnvError(f"System info failed: {e}")

    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a generic action using the embedded desktop env action runner"""
        if not self._env:
            await self.initialize()

        try:
            def _execute_action():
                return self._env.execute_action(action)

            result = await asyncio.get_event_loop().run_in_executor(None, _execute_action)

            logger.info(f"Executed action: {action.get('type', 'unknown')}")

            return {
                "success": True,
                "action": action,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            raise EmbeddedDesktopEnvError(f"Action execution failed: {e}")

    async def execute_complex_task(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a complex task with multiple steps"""
        # Extract parameters from action - they can be in 'parameters' field or directly in action
        parameters = action.get("parameters", {})
        actions = parameters.get("actions") or action.get("actions", [])

        if not actions:
            raise EmbeddedDesktopEnvError(
                "No actions provided for complex task")

        results = []

        try:
            for i, single_action in enumerate(actions):
                logger.info(f"Executing step {i+1}/{len(actions)}")

                # Determine action type and route to appropriate method
                action_type = single_action.get("type", "").lower()

                if action_type == "screenshot":
                    result = await self.take_screenshot(single_action)
                elif action_type == "type" or action_type == "type_text":
                    result = await self.type_text(single_action)
                elif action_type == "command" or action_type == "exec":
                    result = await self.execute_command(single_action)
                elif action_type == "python" or action_type == "run_python":
                    result = await self.run_python_code(single_action)
                elif action_type == "open":
                    result = await self.open_file_or_app(single_action)
                elif action_type == "activate_window":
                    result = await self.activate_window(single_action)
                else:
                    # Try generic action execution
                    result = await self.execute_action(single_action)

                results.append(result)

                # Add delay between actions if specified
                delay = single_action.get("delay", 0)
                if delay > 0:
                    await asyncio.sleep(delay)

            return {
                "success": True,
                "total_steps": len(results),
                "action_results": results,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Complex task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "completed_steps": len(results),
                "action_results": results,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def get_terminal_output(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Get terminal output"""
        if not self._env:
            await self.initialize()

        try:
            def _get_terminal_output():
                return self._env.get_terminal_output()

            output = await asyncio.get_event_loop().run_in_executor(None, _get_terminal_output)

            return {
                "success": True,
                "terminal_output": output,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get terminal output: {e}")
            raise EmbeddedDesktopEnvError(f"Terminal output failed: {e}")

    async def close(self) -> None:
        """Close the embedded desktop environment"""
        if self._env:
            try:
                # EmbeddedDesktopEnv doesn't need explicit cleanup
                logger.info("EmbeddedDesktopEnv closed")

            except Exception as e:
                logger.error(
                    f"Error closing embedded desktop environment: {e}")
            finally:
                self._env = None
                self._initialized = False


# Global embedded desktop environment module instance
embedded_desktop_env_module = EmbeddedDesktopEnvModule()
