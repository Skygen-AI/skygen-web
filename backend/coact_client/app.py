"""
Main Coact Client Application

Coordinates all components and handles the main application lifecycle.
"""

import asyncio
import logging
import signal
import sys
from typing import Dict, Any

from coact_client.config.settings import settings
from coact_client.utils.logging import setup_logging, performance_monitor
from coact_client.core.auth import auth_client
from coact_client.core.device import device_manager
from coact_client.core.websocket import websocket_client
from coact_client.core.tasks import task_engine
from coact_client.modules.screen import screen_module
from coact_client.modules.shell import shell_module
from coact_client.modules.artifacts import artifact_uploader
from coact_client.modules.desktop_env import desktop_env_module
from coact_client.modules.embedded_desktop_env import embedded_desktop_env_module

logger = logging.getLogger(__name__)


class CoactClient:
    """Main Coact Client application"""

    def __init__(self):
        self.running = False
        self.shutdown_event = asyncio.Event()
        self._startup_complete = False

        # Register signal handlers
        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, _):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        if self.running:
            asyncio.create_task(self.shutdown())

    async def initialize(self) -> None:
        """Initialize application components"""
        logger.info("Initializing Coact Client...")

        with performance_monitor.time_operation("app_initialization"):
            # Setup logging
            setup_logging()

            # Register task action handlers
            self._register_action_handlers()

            # Set task completion callback
            task_engine.on_task_completed = self._on_task_completed

            # Set WebSocket event handlers
            websocket_client.on_connect = self._on_websocket_connect
            websocket_client.on_disconnect = self._on_websocket_disconnect
            websocket_client.on_message = self._on_websocket_message
            websocket_client.on_error = self._on_websocket_error

        logger.info("Application initialized successfully")
        self._startup_complete = True

    def _register_action_handlers(self) -> None:
        """Register handlers for different action types"""
        # Screen actions
        task_engine.register_action_handler(
            "screenshot", screen_module.take_screenshot)
        task_engine.register_action_handler(
            "screenshot_upload", screen_module.take_screenshot_and_upload)
        task_engine.register_action_handler("click", screen_module.click)
        task_engine.register_action_handler("type", screen_module.type_text)
        task_engine.register_action_handler("scroll", screen_module.scroll)
        task_engine.register_action_handler("key", screen_module.press_key)
        task_engine.register_action_handler(
            "move_mouse", screen_module.move_mouse)
        task_engine.register_action_handler(
            "screen_info", screen_module.get_screen_info)

        # Shell actions
        task_engine.register_action_handler(
            "shell", shell_module.execute_command)
        task_engine.register_action_handler(
            "system_info", shell_module.get_system_info)

        # Artifact actions
        task_engine.register_action_handler(
            "upload_artifact", artifact_uploader.upload_artifact)
        task_engine.register_action_handler(
            "upload_screenshot", artifact_uploader.upload_screenshot)
        task_engine.register_action_handler(
            "upload_log", artifact_uploader.upload_log_file)

        # Desktop Environment actions (VM-based)
        task_engine.register_action_handler(
            "desktop_env_init", desktop_env_module.initialize)
        task_engine.register_action_handler(
            "desktop_env_reset", desktop_env_module.reset_environment)
        task_engine.register_action_handler(
            "desktop_env_action", desktop_env_module.execute_action)
        task_engine.register_action_handler(
            "desktop_env_screenshot", desktop_env_module.take_screenshot)
        task_engine.register_action_handler(
            "desktop_env_a11y", desktop_env_module.get_accessibility_tree)
        task_engine.register_action_handler(
            "desktop_env_evaluate", desktop_env_module.evaluate_task)
        task_engine.register_action_handler(
            "desktop_env_info", desktop_env_module.get_vm_info)
        task_engine.register_action_handler(
            "desktop_env_task", desktop_env_module.execute_complex_task)

        # Embedded Desktop Environment actions (direct system control)
        task_engine.register_action_handler(
            "embedded_desktop_init", embedded_desktop_env_module.initialize)
        task_engine.register_action_handler(
            "embedded_desktop_screenshot", embedded_desktop_env_module.take_screenshot)
        task_engine.register_action_handler(
            "embedded_desktop_a11y", embedded_desktop_env_module.get_accessibility_tree)
        task_engine.register_action_handler(
            "embedded_desktop_type", embedded_desktop_env_module.type_text)
        task_engine.register_action_handler(
            "embedded_desktop_command", embedded_desktop_env_module.execute_command)
        task_engine.register_action_handler(
            "embedded_desktop_python", embedded_desktop_env_module.run_python_code)
        task_engine.register_action_handler(
            "embedded_desktop_open", embedded_desktop_env_module.open_file_or_app)
        task_engine.register_action_handler(
            "embedded_desktop_activate", embedded_desktop_env_module.activate_window)
        task_engine.register_action_handler(
            "embedded_desktop_info", embedded_desktop_env_module.get_system_info)
        task_engine.register_action_handler(
            "embedded_desktop_action", embedded_desktop_env_module.execute_action)
        task_engine.register_action_handler(
            "embedded_desktop_task", embedded_desktop_env_module.execute_complex_task)
        task_engine.register_action_handler(
            "embedded_desktop_terminal", embedded_desktop_env_module.get_terminal_output)

        logger.info(
            f"Registered {len(task_engine.get_supported_actions())} action handlers")

    async def authenticate(self, email: str, password: str) -> bool:
        """Authenticate user"""
        logger.info(f"Authenticating user: {email}")

        try:
            async with auth_client:
                await auth_client.login(email, password)

            logger.info("Authentication successful")
            return True

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    async def enroll_device(self, force: bool = False) -> bool:
        """Enroll device with server"""
        logger.info("Enrolling device...")

        try:
            async with device_manager:
                device_info = await device_manager.enroll_device(force_reenroll=force)

            logger.info(f"Device enrolled: {device_info.device_id}")
            return True

        except Exception as e:
            logger.error(f"Device enrollment failed: {e}")
            return False

    async def start(self) -> None:
        """Start the client application"""
        if self.running:
            return

        logger.info("Starting Coact Client...")
        self.running = True

        try:
            # Ensure authentication
            if not auth_client.is_authenticated():
                logger.error("Not authenticated - cannot start client")
                return

            # Ensure device enrollment - try to auto-enroll if not enrolled
            if not device_manager.is_enrolled():
                logger.info(
                    "Device not enrolled - attempting auto-enrollment...")
                try:
                    await device_manager.enroll_device()
                    logger.info("Device auto-enrolled successfully")
                except Exception as e:
                    logger.error(f"Device auto-enrollment failed: {e}")
                    logger.error(
                        "Cannot start client without device enrollment")
                    return

            # Connect WebSocket
            await websocket_client.connect()

            # Wait for shutdown signal
            await self.shutdown_event.wait()

        except Exception as e:
            logger.error(f"Application error: {e}")
            raise
        finally:
            self.running = False

    async def shutdown(self) -> None:
        """Shutdown the client application"""
        if not self.running:
            return

        logger.info("Shutting down Coact Client...")

        with performance_monitor.time_operation("app_shutdown"):
            try:
                # Cancel active tasks
                active_tasks = task_engine.get_active_tasks()
                if active_tasks:
                    logger.info(f"Cancelling {len(active_tasks)} active tasks")
                    for task_id in active_tasks:
                        await task_engine.cancel_task(task_id)

                # Disconnect WebSocket
                if websocket_client.is_connected():
                    await websocket_client.disconnect()

                # Close desktop environments
                await desktop_env_module.close()
                await embedded_desktop_env_module.close()

                # Close HTTP sessions
                await auth_client.close()
                await device_manager.close()
                await artifact_uploader.close()

            except Exception as e:
                logger.error(f"Error during shutdown: {e}")

        self.running = False
        self.shutdown_event.set()
        logger.info("Shutdown complete")

    async def _on_websocket_connect(self) -> None:
        """Handle WebSocket connection established"""
        logger.info("WebSocket connected - client is now online")

        # Log connection metrics
        performance_monitor.record_metric("websocket_connected", 1)

    async def _on_websocket_disconnect(self) -> None:
        """Handle WebSocket disconnection"""
        logger.warning("WebSocket disconnected - client is now offline")

        # Log disconnection metrics
        performance_monitor.record_metric("websocket_disconnected", 1)

    async def _on_websocket_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming WebSocket message"""
        message_type = message.get("type")

        logger.debug(f"Received WebSocket message: {message_type}")

        # Log message metrics
        performance_monitor.record_metric(
            f"message_received_{message_type}", 1)

        try:
            if message_type == "task.exec":
                # Handle task execution
                await task_engine.process_task(message)

            elif message_type == "ping":
                # Respond to server ping
                await websocket_client.send_message({"type": "pong"})

            else:
                logger.debug(f"Unhandled message type: {message_type}")

        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

    async def _on_websocket_error(self, error: Exception) -> None:
        """Handle WebSocket error"""
        logger.error(f"WebSocket error: {error}")

        # Log error metrics
        performance_monitor.record_metric("websocket_error", 1)

    async def _on_task_completed(self, task_execution) -> None:
        """Handle task completion"""
        task_id = task_execution.task_id
        status = task_execution.status

        logger.info(f"Task {task_id} completed with status: {status.value}")

        # Log task metrics
        performance_monitor.record_metric(f"task_completed_{status.value}", 1)

        # Send result to server
        try:
            await websocket_client.send_task_result(
                task_id=task_id,
                results=[r.to_dict() for r in task_execution.results],
                status=status.value
            )
        except Exception as e:
            logger.error(f"Failed to send task result: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get application status"""
        return {
            "running": self.running,
            "startup_complete": self._startup_complete,
            "authenticated": auth_client.is_authenticated(),
            "device_enrolled": device_manager.is_enrolled(),
            "websocket_connected": websocket_client.is_connected(),
            "websocket_state": websocket_client.get_state().value,
            "active_tasks": len(task_engine.get_active_tasks()),
            "supported_actions": task_engine.get_supported_actions(),
            "version": settings.app_version,
            "environment": settings.environment,
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return performance_monitor.get_metrics()


# Global application instance
app = CoactClient()
