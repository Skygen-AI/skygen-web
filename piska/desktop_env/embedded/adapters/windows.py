from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pyautogui  # type: ignore

from ..os_adapter import OSAdapter


class WindowsAdapter(OSAdapter):
    def get_platform(self) -> str:
        return platform.system()

    def get_screen_size(self) -> Tuple[int, int]:
        import ctypes  # type: ignore

        user32 = ctypes.windll.user32
        return int(user32.GetSystemMetrics(0)), int(user32.GetSystemMetrics(1))

    def get_cursor_position(self) -> Tuple[int, int]:
        pos = pyautogui.position()
        return int(pos.x), int(pos.y)

    def capture_screenshot(self) -> bytes:
        from PIL import ImageGrab
        from io import BytesIO

        img = ImageGrab.grab(bbox=None, include_layered_windows=True)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def get_accessibility_tree(self) -> str:
        # Lightweight stub; full UIA via pywinauto is large and slow for embedded minimal
        return "<desktop/>"

    def open_file_or_app(self, path_or_app: str) -> str:
        p = Path(os.path.expandvars(os.path.expanduser(path_or_app)))
        if p.exists():
            os.startfile(p)  # type: ignore[attr-defined]
            return "opened"
        import subprocess

        subprocess.Popen([path_or_app])
        return "launched"

    def activate_window(
        self, title: str, strict: bool = False, by_class: bool = False
    ) -> bool:
        try:
            import pygetwindow as gw  # type: ignore

            if by_class:
                return False
            windows: List[gw.Window] = gw.getWindowsWithTitle(title)
            if not windows:
                return False
            if strict:
                for w in windows:
                    if w.title == title:
                        w.activate()
                        return True
                return False
            else:
                windows[0].activate()
                return True
        except Exception:
            return False

    def close_window(
        self, title: str, strict: bool = False, by_class: bool = False
    ) -> bool:
        try:
            import pygetwindow as gw  # type: ignore

            if by_class:
                return False
            windows: List[gw.Window] = gw.getWindowsWithTitle(title)
            if not windows:
                return False
            if strict:
                for w in windows:
                    if w.title == title:
                        w.close()
                        return True
                return False
            else:
                windows[0].close()
                return True
        except Exception:
            return False

    def type_text(self, text: str, interval: float = 0.0) -> None:
        pyautogui.typewrite(text, interval=interval)

    def list_directory_tree(self, path: str) -> Dict[str, Any]:
        def _list_dir_contents(directory: str) -> Dict[str, Any]:
            tree: Dict[str, Any] = {
                "type": "directory",
                "name": os.path.basename(directory),
                "children": [],
            }
            try:
                for entry in os.listdir(directory):
                    full_path = os.path.join(directory, entry)
                    if os.path.isdir(full_path):
                        tree["children"].append(_list_dir_contents(full_path))
                    else:
                        tree["children"].append({"type": "file", "name": entry})
            except OSError as e:
                tree = {"error": str(e)}
            return tree

        start_path = os.path.expandvars(os.path.expanduser(path))
        if not os.path.isdir(start_path):
            return {"error": "not a directory"}
        return _list_dir_contents(start_path)

    def read_file_bytes(self, file_path: str) -> bytes:
        p = Path(os.path.expandvars(os.path.expanduser(file_path)))
        with open(p, "rb") as f:
            return f.read()

    def write_file_bytes(self, file_path: str, data: bytes) -> None:
        p = Path(os.path.expandvars(os.path.expanduser(file_path)))
        if p.parent:
            p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as f:
            f.write(data)

    def get_wallpaper(self) -> Optional[bytes]:
        return None

    def change_wallpaper(self, file_path: str) -> bool:
        try:
            import ctypes  # type: ignore

            p = Path(os.path.expandvars(os.path.expanduser(file_path)))
            ctypes.windll.user32.SystemParametersInfoW(20, 0, str(p), 3)
            return True
        except Exception:
            return False

    def execute_command(
        self, command: Union[str, List[str]], shell: bool = False, timeout: int = 120
    ) -> Dict[str, Any]:
        import shlex
        import subprocess

        cmd: List[str] | str
        if isinstance(command, str) and not shell:
            cmd = shlex.split(command)
        else:
            cmd = command  # type: ignore[assignment]
        if not shell and isinstance(cmd, list):
            for i, arg in enumerate(cmd):
                if isinstance(arg, str) and arg.startswith("~/"):
                    cmd[i] = os.path.expanduser(arg)
        try:
            flags = 0
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=shell,
                text=True,
                timeout=timeout,
                creationflags=flags,
            )
            return {
                "status": "success",
                "output": result.stdout,
                "error": result.stderr,
                "returncode": result.returncode,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def execute_command_with_verification(
        self, command, shell, verification, max_wait_time=10, check_interval=1.0
    ):
        res = self.execute_command(command, shell)
        res.update({"verification": "skipped"})
        return res

    def run_python(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        import uuid
        import subprocess

        tmp = f"%TEMP%/python_exec_{uuid.uuid4().hex}.py"
        tmp = os.path.expandvars(tmp)
        try:
            with open(tmp, "w") as f:
                f.write(code)
            result = subprocess.run(
                ["py", tmp],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
            )
            return {
                "status": "success" if result.returncode == 0 else "error",
                "message": (
                    result.stdout + ("\n" + result.stderr if result.stderr else "")
                )
                if result.stdout or result.stderr
                else "",
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "Execution timeout",
                "error": "TimeoutExpired",
            }
        except Exception as e:
            return {"status": "error", "message": f"Execution error: {e}"}
        finally:
            try:
                os.remove(tmp)
            except Exception:
                pass

    def run_bash_script(
        self, script: str, timeout: int = 100, working_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        return {
            "status": "error",
            "output": "bash not supported natively on Windows in this adapter",
            "error": "",
            "returncode": -1,
        }

    def get_terminal_output(self) -> Optional[str]:
        return None
