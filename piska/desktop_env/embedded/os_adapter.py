from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union


class OSAdapter(ABC):
    """Abstract interface for OS-specific desktop automation.

    Implementations should map the core actions needed by an embedded agent
    without exposing any HTTP/REST server. All methods run locally in-process.
    """

    # --- System info ---
    @abstractmethod
    def get_platform(self) -> str:
        pass

    # --- Screen & cursor ---
    @abstractmethod
    def get_screen_size(self) -> Tuple[int, int]:
        pass

    @abstractmethod
    def get_cursor_position(self) -> Tuple[int, int]:
        pass

    @abstractmethod
    def capture_screenshot(self) -> bytes:
        """Return screenshot PNG bytes (preferably including cursor if feasible)."""
        pass

    # --- Accessibility ---
    @abstractmethod
    def get_accessibility_tree(self) -> str:
        """Return accessibility tree as XML string."""
        pass

    # --- Apps & windows ---
    @abstractmethod
    def open_file_or_app(self, path_or_app: str) -> str:
        pass

    @abstractmethod
    def activate_window(
        self, title: str, strict: bool = False, by_class: bool = False
    ) -> bool:
        pass

    @abstractmethod
    def close_window(
        self, title: str, strict: bool = False, by_class: bool = False
    ) -> bool:
        pass

    # --- Input ---
    @abstractmethod
    def type_text(self, text: str, interval: float = 0.0) -> None:
        pass

    # --- Filesystem ---
    @abstractmethod
    def list_directory_tree(self, path: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def read_file_bytes(self, file_path: str) -> bytes:
        pass

    @abstractmethod
    def write_file_bytes(self, file_path: str, data: bytes) -> None:
        pass

    # --- Wallpaper ---
    @abstractmethod
    def get_wallpaper(self) -> Optional[bytes]:
        pass

    @abstractmethod
    def change_wallpaper(self, file_path: str) -> bool:
        pass

    # --- Commands ---
    @abstractmethod
    def execute_command(
        self, command: Union[str, List[str]], shell: bool = False, timeout: int = 120
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def execute_command_with_verification(
        self,
        command: Union[str, List[str]],
        shell: bool,
        verification: Dict[str, Any],
        max_wait_time: int = 10,
        check_interval: float = 1.0,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def run_python(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        pass

    @abstractmethod
    def run_bash_script(
        self, script: str, timeout: int = 100, working_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        pass

    # --- Utilities ---
    @abstractmethod
    def get_terminal_output(self) -> Optional[str]:
        pass
