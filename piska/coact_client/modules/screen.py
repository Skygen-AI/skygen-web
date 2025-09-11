"""
Screen capture and interaction module

Handles screenshot taking, mouse clicks, and keyboard input.
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import base64
from io import BytesIO

try:
    import pyautogui
    import PIL.Image
    HAS_GUI_LIBS = True
except ImportError:
    HAS_GUI_LIBS = False

from coact_client.config.settings import settings

logger = logging.getLogger(__name__)

# Disable pyautogui failsafe for production use
if HAS_GUI_LIBS:
    pyautogui.FAILSAFE = False


class ScreenError(Exception):
    """Screen interaction errors"""
    pass


class ScreenModule:
    """Screen capture and interaction module"""

    def __init__(self):
        self.screenshot_dir = settings.cache_dir / "screenshots"
        self.screenshot_dir.mkdir(exist_ok=True)

        if not HAS_GUI_LIBS:
            logger.warning(
                "GUI libraries not available - screen actions will be limited")

    async def take_screenshot(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Take a screenshot"""
        if not HAS_GUI_LIBS:
            raise ScreenError("GUI libraries not available")

        try:
            # Take screenshot in background thread to avoid blocking
            screenshot = await asyncio.get_event_loop().run_in_executor(
                None, pyautogui.screenshot
            )

            # Get screenshot parameters
            region = action.get("region")  # [x, y, width, height]
            quality = action.get("quality", 85)
            format_type = action.get("format", "PNG").upper()

            # Crop if region specified
            if region and len(region) >= 4:
                x, y, width, height = region
                screenshot = screenshot.crop((x, y, x + width, y + height))

            # Convert to bytes
            img_buffer = BytesIO()
            if format_type == "JPEG":
                screenshot = screenshot.convert("RGB")
                screenshot.save(img_buffer, format="JPEG",
                                quality=quality, optimize=True)
            else:
                screenshot.save(img_buffer, format="PNG", optimize=True)

            img_bytes = img_buffer.getvalue()

            # Save to file for potential upload
            timestamp = int(asyncio.get_event_loop().time())
            filename = f"screenshot_{timestamp}.{format_type.lower()}"
            filepath = self.screenshot_dir / filename

            filepath.write_bytes(img_bytes)

            # Get image info
            width, height = screenshot.size
            file_size = len(img_bytes)

            logger.info(
                f"Screenshot taken: {width}x{height}, {file_size} bytes")

            return {
                "success": True,
                "filepath": str(filepath),
                "filename": filename,
                "width": width,
                "height": height,
                "size_bytes": file_size,
                "format": format_type,
                "base64": base64.b64encode(img_bytes).decode() if action.get("include_base64") else None
            }

        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            raise ScreenError(f"Screenshot failed: {e}")

    async def click(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Perform mouse click"""
        if not HAS_GUI_LIBS:
            raise ScreenError("GUI libraries not available")

        try:
            # Get click parameters
            coordinates = action.get("coordinates", [0, 0])
            if len(coordinates) < 2:
                raise ScreenError("Invalid coordinates")

            x, y = coordinates[0], coordinates[1]
            button = action.get("button", "left").lower()
            clicks = action.get("clicks", 1)
            interval = action.get("interval", 0.1)
            duration = action.get("duration", 0.0)

            # Validate coordinates
            screen_width, screen_height = pyautogui.size()
            if not (0 <= x <= screen_width and 0 <= y <= screen_height):
                raise ScreenError(
                    f"Coordinates ({x}, {y}) out of screen bounds")

            # Perform click in background thread
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: pyautogui.click(
                    x=x, y=y,
                    clicks=clicks,
                    interval=interval,
                    button=button,
                    duration=duration
                )
            )

            logger.info(f"Clicked at ({x}, {y}) with {button} button")

            return {
                "success": True,
                "coordinates": [x, y],
                "button": button,
                "clicks": clicks
            }

        except Exception as e:
            logger.error(f"Click failed: {e}")
            raise ScreenError(f"Click failed: {e}")

    async def type_text(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Type text using keyboard"""
        if not HAS_GUI_LIBS:
            raise ScreenError("GUI libraries not available")

        try:
            text = action.get("text", "")
            if not text:
                raise ScreenError("No text provided")

            interval = action.get("interval", 0.01)

            # Type text in background thread
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: pyautogui.typewrite(text, interval=interval)
            )

            logger.info(
                f"Typed text: '{text[:50]}{'...' if len(text) > 50 else ''}'")

            return {
                "success": True,
                "text": text,
                "length": len(text)
            }

        except Exception as e:
            logger.error(f"Type text failed: {e}")
            raise ScreenError(f"Type text failed: {e}")

    async def scroll(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Scroll the mouse wheel"""
        if not HAS_GUI_LIBS:
            raise ScreenError("GUI libraries not available")

        try:
            clicks = action.get("clicks", 3)
            x = action.get("x")
            y = action.get("y")

            # Scroll in background thread
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: pyautogui.scroll(clicks=clicks, x=x, y=y)
            )

            logger.info(f"Scrolled {clicks} clicks at ({x}, {y})")

            return {
                "success": True,
                "clicks": clicks,
                "position": [x, y] if x is not None and y is not None else None
            }

        except Exception as e:
            logger.error(f"Scroll failed: {e}")
            raise ScreenError(f"Scroll failed: {e}")

    async def press_key(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Press keyboard keys"""
        if not HAS_GUI_LIBS:
            raise ScreenError("GUI libraries not available")

        try:
            keys = action.get("keys")
            if not keys:
                raise ScreenError("No keys provided")

            # Handle both single key and key combinations
            if isinstance(keys, str):
                keys = [keys]

            # Press keys in background thread
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: pyautogui.hotkey(
                    *keys) if len(keys) > 1 else pyautogui.press(keys[0])
            )

            logger.info(f"Pressed keys: {keys}")

            return {
                "success": True,
                "keys": keys
            }

        except Exception as e:
            logger.error(f"Press key failed: {e}")
            raise ScreenError(f"Press key failed: {e}")

    async def move_mouse(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Move mouse cursor"""
        if not HAS_GUI_LIBS:
            raise ScreenError("GUI libraries not available")

        try:
            coordinates = action.get("coordinates", [0, 0])
            if len(coordinates) < 2:
                raise ScreenError("Invalid coordinates")

            x, y = coordinates[0], coordinates[1]
            duration = action.get("duration", 0.5)

            # Validate coordinates
            screen_width, screen_height = pyautogui.size()
            if not (0 <= x <= screen_width and 0 <= y <= screen_height):
                raise ScreenError(
                    f"Coordinates ({x}, {y}) out of screen bounds")

            # Move mouse in background thread
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: pyautogui.moveTo(x, y, duration=duration)
            )

            logger.info(f"Moved mouse to ({x}, {y})")

            return {
                "success": True,
                "coordinates": [x, y],
                "duration": duration
            }

        except Exception as e:
            logger.error(f"Move mouse failed: {e}")
            raise ScreenError(f"Move mouse failed: {e}")

    async def get_screen_info(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Get screen information"""
        if not HAS_GUI_LIBS:
            return {
                "success": False,
                "error": "GUI libraries not available"
            }

        try:
            # Get screen size
            screen_width, screen_height = pyautogui.size()

            # Get current mouse position
            mouse_x, mouse_y = pyautogui.position()

            return {
                "success": True,
                "screen_size": [screen_width, screen_height],
                "mouse_position": [mouse_x, mouse_y],
                "gui_available": True
            }

        except Exception as e:
            logger.error(f"Get screen info failed: {e}")
            raise ScreenError(f"Get screen info failed: {e}")

    async def take_screenshot_and_upload(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Take screenshot and upload to MinIO"""
        if not HAS_GUI_LIBS:
            raise ScreenError("GUI libraries not available")

        try:
            # First take the screenshot
            screenshot_result = await self.take_screenshot(action)

            if not screenshot_result.get("success"):
                return screenshot_result

            # Now upload to MinIO using artifact uploader
            from coact_client.modules.artifacts import artifact_uploader

            upload_action = {
                "filepath": screenshot_result["filepath"],
                "task_id": action.get("task_id"),
                "filename": screenshot_result["filename"]
            }

            async with artifact_uploader:
                upload_result = await artifact_uploader.upload_artifact(upload_action)

            # Combine results
            result = screenshot_result.copy()
            result.update({
                "upload_success": upload_result.get("success", False),
                "upload_url": upload_result.get("upload_url"),
                "public_url": upload_result.get("public_url"),
                "s3_url": upload_result.get("s3_url")
            })

            logger.info(
                f"Screenshot taken and uploaded: {screenshot_result['filename']}")

            return result

        except Exception as e:
            logger.error(f"Screenshot and upload failed: {e}")
            raise ScreenError(f"Screenshot and upload failed: {e}")


# Global screen module instance
screen_module = ScreenModule()
