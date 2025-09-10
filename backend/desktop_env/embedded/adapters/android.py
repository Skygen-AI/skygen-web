from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union

from ..os_adapter import OSAdapter


class AndroidAdapter(OSAdapter):
    """Placeholder adapter to enable future Android support via ADB.

    Methods are stubbed and should be implemented with ADB (e.g., screencap,
    input text, dumpsys accessibility, am start, etc.).
    """

    def get_platform(self) -> str:
        return "Android"

    def get_screen_size(self) -> Tuple[int, int]:
        return (0, 0)

    def get_cursor_position(self) -> Tuple[int, int]:
        return (0, 0)

    def capture_screenshot(self) -> bytes:
        return b""

    def get_accessibility_tree(self) -> str:
        return "<hierarchy/>"

    def open_file_or_app(self, path_or_app: str) -> str:
        return "not_implemented"

    def activate_window(
        self, title: str, strict: bool = False, by_class: bool = False
    ) -> bool:
        return False

    def close_window(
        self, title: str, strict: bool = False, by_class: bool = False
    ) -> bool:
        return False

    def type_text(self, text: str, interval: float = 0.0) -> None:
        return None

    def list_directory_tree(self, path: str) -> Dict[str, Any]:
        return {"error": "not_implemented"}

    def read_file_bytes(self, file_path: str) -> bytes:
        return b""

    def write_file_bytes(self, file_path: str, data: bytes) -> None:
        return None

    def get_wallpaper(self) -> Optional[bytes]:
        return None

    def change_wallpaper(self, file_path: str) -> bool:
        return False

    def execute_command(
        self, command: Union[str, List[str]], shell: bool = False, timeout: int = 120
    ) -> Dict[str, Any]:
        return {"status": "error", "message": "not_implemented"}

    def execute_command_with_verification(
        self, command, shell, verification, max_wait_time=10, check_interval=1.0
    ):
        return {"status": "error", "message": "not_implemented"}

    def run_python(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        return {"status": "error", "message": "not_implemented"}

    def run_bash_script(
        self, script: str, timeout: int = 100, working_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        return {
            "status": "error",
            "output": "not_implemented",
            "error": "",
            "returncode": -1,
        }

    def get_terminal_output(self) -> Optional[str]:
        return None
