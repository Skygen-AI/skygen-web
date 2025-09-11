from __future__ import annotations

import importlib
import platform
from typing import Dict, Type

from .os_adapter import OSAdapter
from .action_runner import execute_action as _execute_action


class OSRegistry:
    _registry: Dict[str, str] = {}

    @classmethod
    def register(cls, platform_key: str, adapter_path: str) -> None:
        cls._registry[platform_key.lower()] = adapter_path

    @classmethod
    def resolve(cls, platform_key: str) -> OSAdapter:
        key = platform_key.lower()
        if key not in cls._registry:
            raise RuntimeError(f"No OS adapter registered for {platform_key}")
        module_path, class_name = cls._registry[key].rsplit(".", 1)
        module = importlib.import_module(module_path)
        adapter_cls: Type[OSAdapter] = getattr(module, class_name)
        return adapter_cls()


class EmbeddedDesktopEnv:
    """Facade for embedded desktop control.

    Usage:
      env = EmbeddedDesktopEnv()
      env.screenshot_png_bytes()
    """

    def __init__(self, platform_key: str | None = None):
        if platform_key is None:
            platform_key = platform.system()
        # lazy default registrations
        # map platform names to adapter classes
        if not OSRegistry._registry:
            OSRegistry.register(
                "Darwin", "desktop_env.embedded.adapters.macos.MacOSAdapter"
            )
            OSRegistry.register(
                "Linux", "desktop_env.embedded.adapters.linux.LinuxAdapter"
            )
            OSRegistry.register(
                "Windows",
                "desktop_env.embedded.adapters.windows.WindowsAdapter",
            )
            OSRegistry.register(
                "Android",
                "desktop_env.embedded.adapters.android.AndroidAdapter",
            )
        self.adapter: OSAdapter = OSRegistry.resolve(platform_key)

    # short convenience proxies
    def screenshot_png_bytes(self) -> bytes:
        return self.adapter.capture_screenshot()

    def a11y_tree_xml(self) -> str:
        return self.adapter.get_accessibility_tree()

    def type_text(self, text: str, interval: float = 0.1) -> None:
        self.adapter.type_text(text, interval)

    def exec(self, command, shell=False, timeout=120):
        return self.adapter.execute_command(command, shell=shell, timeout=timeout)

    # full adapter surface proxies
    def platform(self) -> str:
        return self.adapter.get_platform()

    def screen_size(self) -> tuple[int, int]:
        return self.adapter.get_screen_size()

    def cursor_position(self) -> tuple[int, int]:
        return self.adapter.get_cursor_position()

    def open_file_or_app(self, path_or_app: str) -> str:
        return self.adapter.open_file_or_app(path_or_app)

    def activate_window(
        self, title: str, strict: bool = False, by_class: bool = False
    ) -> bool:
        return self.adapter.activate_window(title, strict=strict, by_class=by_class)

    def close_window(
        self, title: str, strict: bool = False, by_class: bool = False
    ) -> bool:
        return self.adapter.close_window(title, strict=strict, by_class=by_class)

    def list_directory_tree(self, path: str):
        return self.adapter.list_directory_tree(path)

    def read_file_bytes(self, file_path: str) -> bytes:
        return self.adapter.read_file_bytes(file_path)

    def write_file_bytes(self, file_path: str, data: bytes) -> None:
        self.adapter.write_file_bytes(file_path, data)

    def get_wallpaper(self):
        return self.adapter.get_wallpaper()

    def change_wallpaper(self, file_path: str) -> bool:
        return self.adapter.change_wallpaper(file_path)

    def execute_with_verification(
        self, command, shell, verification, max_wait_time=10, check_interval=1.0
    ):
        return self.adapter.execute_command_with_verification(
            command,
            shell,
            verification,
            max_wait_time=max_wait_time,
            check_interval=check_interval,
        )

    def run_python(self, code: str, timeout: int = 30):
        return self.adapter.run_python(code, timeout=timeout)

    def run_bash_script(
        self, script: str, timeout: int = 100, working_dir: str | None = None
    ):
        return self.adapter.run_bash_script(
            script, timeout=timeout, working_dir=working_dir
        )

    def get_terminal_output(self):
        return self.adapter.get_terminal_output()

    # high-level
    def execute_action(self, action):
        _execute_action(action)
