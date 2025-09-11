from __future__ import annotations

import os
import platform
import re
import shlex
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import AppKit  # type: ignore
import ApplicationServices  # type: ignore
import Quartz  # type: ignore
import pyautogui  # type: ignore
import pyperclip

from ..os_adapter import OSAdapter


class MacOSAdapter(OSAdapter):
    def get_platform(self) -> str:
        return platform.system()

    def get_screen_size(self) -> Tuple[int, int]:
        main_display = Quartz.CGMainDisplayID()
        width = Quartz.CGDisplayPixelsWide(main_display)
        height = Quartz.CGDisplayPixelsHigh(main_display)
        return int(width), int(height)

    def get_cursor_position(self) -> Tuple[int, int]:
        pos = pyautogui.position()
        return int(pos.x), int(pos.y)

    def capture_screenshot(self) -> bytes:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            subprocess.run(["screencapture", "-C", tmp_path], check=True)
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def get_accessibility_tree(self) -> str:
        # Minimal port of macOS branch from the existing Flask server
        reserved_keys = {
            "AXEnabled": "st",
            "AXFocused": "st",
            "AXFullScreen": "st",
            "AXTitle": "attr",
            "AXChildrenInNavigationOrder": "attr",
            "AXChildren": "attr",
            "AXFrame": "attr",
            "AXRole": "role",
            "AXHelp": "attr",
            "AXRoleDescription": "role",
            "AXSubrole": "role",
            "AXURL": "attr",
            "AXValue": "val",
            "AXDescription": "attr",
            "AXDOMIdentifier": "attr",
            "AXSelected": "st",
            "AXInvalid": "st",
            "AXRows": "attr",
            "AXColumns": "attr",
        }

        import lxml.etree  # type: ignore

        _ns = {
            "st": "https://accessibility.macos.example.org/ns/state",
            "attr": "https://accessibility.macos.example.org/ns/attributes",
            "cp": "https://accessibility.macos.example.org/ns/component",
            "doc": "https://accessibility.macos.example.org/ns/document",
            "txt": "https://accessibility.macos.example.org/ns/text",
            "val": "https://accessibility.macos.example.org/ns/value",
            "act": "https://accessibility.macos.example.org/ns/action",
            "role": "https://accessibility.macos.example.org/ns/role",
        }

        def _create_axui_node(
            node, nodes: set = None, depth: int = 0, bbox: tuple = None
        ):
            nodes = nodes or set()
            if node in nodes:
                return
            nodes.add(node)

            attribute_dict: Dict[str, Any] = {}

            if depth == 0:
                bbox = (
                    node["kCGWindowBounds"]["X"],
                    node["kCGWindowBounds"]["Y"],
                    node["kCGWindowBounds"]["X"] + node["kCGWindowBounds"]["Width"],
                    node["kCGWindowBounds"]["Y"] + node["kCGWindowBounds"]["Height"],
                )
                app_ref = ApplicationServices.AXUIElementCreateApplication(
                    node["kCGWindowOwnerPID"]
                )

                attribute_dict["name"] = node["kCGWindowOwnerName"]
                if attribute_dict["name"] != "Dock":
                    error_code, app_wins_ref = (
                        ApplicationServices.AXUIElementCopyAttributeValue(
                            app_ref, "AXWindows", None
                        )
                    )
                    if error_code:
                        return
                else:
                    app_wins_ref = [app_ref]
                node = app_wins_ref[0]

            error_code, attr_names = ApplicationServices.AXUIElementCopyAttributeNames(
                node, None
            )
            if error_code:
                return

            value = None
            role: Optional[str] = None
            text: Optional[str] = None

            if "AXFrame" in attr_names:
                error_code, attr_val = (
                    ApplicationServices.AXUIElementCopyAttributeValue(
                        node, "AXFrame", None
                    )
                )
                rep = repr(attr_val)
                x_value = re.search(r"x:(-?[\d.]+)", rep)
                y_value = re.search(r"y:(-?[\d.]+)", rep)
                w_value = re.search(r"w:(-?[\d.]+)", rep)
                h_value = re.search(r"h:(-?[\d.]+)", rep)
                type_value = re.search(r"type\s?=\s?(\w+)", rep)
                value = {
                    "x": float(x_value.group(1)) if x_value else None,
                    "y": float(y_value.group(1)) if y_value else None,
                    "w": float(w_value.group(1)) if w_value else None,
                    "h": float(h_value.group(1)) if h_value else None,
                    "type": type_value.group(1) if type_value else None,
                }

                if not any(v is None for v in value.values()):
                    x_min = max(bbox[0], value["x"])  # type: ignore[index]
                    # type: ignore[index]
                    x_max = min(bbox[2], value["x"] + value["w"])
                    y_min = max(bbox[1], value["y"])  # type: ignore[index]
                    # type: ignore[index]
                    y_max = min(bbox[3], value["y"] + value["h"])
                    if x_min > x_max or y_min > y_max:
                        return

            for attr_name, ns_key in reserved_keys.items():
                if attr_name not in attr_names:
                    continue
                if value and attr_name == "AXFrame":
                    bb = value
                    if not any(v is None for v in bb.values()):
                        attribute_dict[f"{{{_ns['cp']}}}screencoord"] = (
                            f"({int(bb['x'])}, {int(bb['y'])})"
                        )
                        attribute_dict[f"{{{_ns['cp']}}}size"] = (
                            f"({int(bb['w'])}, {int(bb['h'])})"
                        )
                    continue
                error_code, attr_val = (
                    ApplicationServices.AXUIElementCopyAttributeValue(
                        node, attr_name, None
                    )
                )
                full_attr_name = f"{{{_ns[ns_key]}}}{attr_name}"
                if attr_name == "AXValue" and not text:
                    text = str(attr_val)
                    continue
                if attr_name == "AXRoleDescription":
                    role = attr_val
                    continue
                if not isinstance(
                    attr_val, ApplicationServices.AXUIElementRef
                ) and not isinstance(attr_val, (AppKit.NSArray, list)):
                    if attr_val is not None:
                        attribute_dict[full_attr_name] = str(attr_val)

            node_role_name = role.lower().replace(" ", "_") if role else "unknown_role"
            xml_node = lxml.etree.Element(
                node_role_name, attrib=attribute_dict, nsmap=_ns
            )
            if text is not None and len(text) > 0:
                xml_node.text = text

            future_children = []
            for attr_name, ns_key in reserved_keys.items():
                if attr_name not in attr_names:
                    continue
                error_code, attr_val = (
                    ApplicationServices.AXUIElementCopyAttributeValue(
                        node, attr_name, None
                    )
                )
                if isinstance(attr_val, ApplicationServices.AXUIElementRef):
                    child = _create_axui_node(attr_val, nodes, depth + 1, bbox)
                    if child is not None:
                        xml_node.append(child)
                elif isinstance(attr_val, (AppKit.NSArray, list)):
                    for child in attr_val:
                        ch = _create_axui_node(child, nodes, depth + 1, bbox)
                        if ch is not None:
                            xml_node.append(ch)
            return xml_node

        xml_root = Quartz.CGWindowListCopyWindowInfo(
            (
                Quartz.kCGWindowListExcludeDesktopElements
                | Quartz.kCGWindowListOptionOnScreenOnly
            ),
            Quartz.kCGNullWindowID,
        )
        xml_node = lxml.etree.Element(
            "desktop",
            nsmap={
                "st": "https://accessibility.macos.example.org/ns/state",
                "attr": "https://accessibility.macos.example.org/ns/attributes",
                "cp": "https://accessibility.macos.example.org/ns/component",
                "doc": "https://accessibility.macos.example.org/ns/document",
                "txt": "https://accessibility.macos.example.org/ns/text",
                "val": "https://accessibility.macos.example.org/ns/value",
                "act": "https://accessibility.macos.example.org/ns/action",
                "role": "https://accessibility.macos.example.org/ns/role",
            },
        )
        foreground_windows = [
            win
            for win in xml_root
            if win.get("kCGWindowLayer") == 0
            and win.get("kCGWindowOwnerName") != "Window Server"
        ]
        dock_info = [
            win
            for win in Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionAll, Quartz.kCGNullWindowID
            )
            if win.get("kCGWindowName", None) == "Dock"
        ]
        for wnd in foreground_windows + dock_info:
            tree = _create_axui_node(wnd, None, 0)
            if tree is not None:
                xml_node.append(tree)
        return str(lxml.etree.tostring(xml_node, encoding="unicode"))

    def open_file_or_app(self, path_or_app: str) -> str:
        p = Path(os.path.expandvars(os.path.expanduser(path_or_app)))
        if p.exists():
            subprocess.Popen(["open", str(p)])
            return "opened"
        subprocess.Popen([path_or_app])
        return "launched"

    def _get_macos_windows(self) -> List[Dict[str, Any]]:
        windows = []
        window_list = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListExcludeDesktopElements
            | Quartz.kCGWindowListOptionOnScreenOnly,
            Quartz.kCGNullWindowID,
        )
        for window in window_list:
            if window.get("kCGWindowName") and window.get("kCGWindowOwnerName"):
                windows.append(
                    {
                        "title": window["kCGWindowName"],
                        "owner": window["kCGWindowOwnerName"],
                        "pid": window["kCGWindowOwnerPID"],
                        "window_id": window["kCGWindowNumber"],
                        "bounds": window.get("kCGWindowBounds", {}),
                    }
                )
        return windows

    def _activate_window_macos(self, window_name: str, strict: bool = False) -> bool:
        windows = self._get_macos_windows()
        target = None
        for window in windows:
            if strict:
                if window["title"] == window_name:
                    target = window
                    break
            else:
                if window_name.lower() in window["title"].lower():
                    target = window
                    break
        if not target:
            return False
        app = AppKit.NSWorkspace.sharedWorkspace().runningApplications()
        for running_app in app:
            if running_app.processIdentifier() == target["pid"]:
                running_app.activateWithOptions_(
                    AppKit.NSApplicationActivateIgnoringOtherApps
                )
                return True
        return False

    def _close_window_applescript(self, window_name: str, strict: bool = False) -> bool:
        if strict:
            script = f'''
            tell application "System Events"
                set allApps to application processes
                repeat with appProc in allApps
                    try
                        set windowList to windows of appProc
                        repeat with win in windowList
                            if name of win is "{window_name}" then
                                click button 1 of win
                                return "success"
                            end if
                        end repeat
                    end try
                end repeat
            end tell
            return "not found"
            '''
        else:
            script = f'''
            tell application "System Events"
                set allApps to application processes
                repeat with appProc in allApps
                    try
                        set windowList to windows of appProc
                        repeat with win in windowList
                            if name of win contains "{window_name}" then
                                click button 1 of win
                                return "success"
                            end if
                        end repeat
                    end try
                end repeat
            end tell
            return "not found"
            '''
        try:
            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip() == "success"
        except Exception:
            return False

    def activate_window(
        self, title: str, strict: bool = False, by_class: bool = False
    ) -> bool:
        if by_class:
            return False
        return self._activate_window_macos(title, strict)

    def close_window(
        self, title: str, strict: bool = False, by_class: bool = False
    ) -> bool:
        if by_class:
            return False
        return self._close_window_applescript(title, strict)

    def type_text(self, text: str, interval: float = 0.1) -> None:
        pyperclip.copy(text)

        with pyautogui.hold("command"):
            time.sleep(interval)
            pyautogui.press(["v"])

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
        script = """
        tell application "System Events" to tell every desktop to get picture
        """
        proc = subprocess.Popen(
            ["osascript", "-e", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output, error = proc.communicate()
        if error:
            return None
        path = output.strip().decode("utf-8").split(",")[0].strip()
        try:
            with open(path, "rb") as f:
                return f.read()
        except Exception:
            return None

    def change_wallpaper(self, file_path: str) -> bool:
        p = Path(os.path.expandvars(os.path.expanduser(file_path)))
        if not p.exists():
            return False
        try:
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    f'tell application "Finder" to set desktop picture to POSIX file "{str(p)}"',
                ],
                check=True,
            )
            return True
        except Exception:
            return False

    def execute_command(
        self, command: Union[str, List[str]], shell: bool = False, timeout: int = 120
    ) -> Dict[str, Any]:
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
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=shell,
                text=True,
                timeout=timeout,
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
        self,
        command: Union[str, List[str]],
        shell: bool,
        verification: Dict[str, Any],
        max_wait_time: int = 10,
        check_interval: float = 1.0,
    ) -> Dict[str, Any]:
        result = self.execute_command(command, shell=shell)
        if not verification:
            return result

        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            verification_passed = True

            if "window_exists" in verification:
                window_name = verification["window_exists"]
                windows = self._get_macos_windows()
                window_found = any(
                    window_name.lower() in w["title"].lower() for w in windows
                )
                if not window_found:
                    verification_passed = False

            if "command_success" in verification:
                verify_cmd = verification["command_success"]
                try:
                    verify_result = subprocess.run(
                        verify_cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if verify_result.returncode != 0:
                        verification_passed = False
                except Exception:
                    verification_passed = False

            if verification_passed:
                result.update(
                    {
                        "verification": "passed",
                        "wait_time": time.time() - start_time,
                    }
                )
                return result
            time.sleep(check_interval)

        result.update(
            {
                "verification": "failed",
                "wait_time": max_wait_time,
            }
        )
        result["status"] = "verification_failed"
        return result

    def run_python(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        import uuid

        tmp = f"/tmp/python_exec_{uuid.uuid4().hex}.py"
        try:
            with open(tmp, "w") as f:
                f.write(code)
            result = subprocess.run(
                ["/usr/bin/python3", tmp],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
            )
            message = (
                (result.stdout + ("\n" + result.stderr if result.stderr else ""))
                if (result.stdout or result.stderr)
                else ""
            )
            return {
                "status": "success" if result.returncode == 0 else "error",
                "message": message,
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
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sh", delete=False
        ) as tmp_file:
            if "#!/bin/bash" not in script:
                script = "#!/bin/bash\n\n" + script
            tmp_file.write(script)
            tmp_path = tmp_file.name
        try:
            os.chmod(tmp_path, 0o755)
            result = subprocess.run(
                ["/bin/bash", tmp_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout,
                cwd=working_dir,
            )
            return {
                "status": "success" if result.returncode == 0 else "error",
                "output": result.stdout,
                "error": "",
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "output": f"Script execution timed out after {timeout} seconds",
                "error": "",
                "returncode": -1,
            }
        except Exception as e:
            return {
                "status": "error",
                "output": f"Failed to execute script: {e}",
                "error": "",
                "returncode": -1,
            }
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def get_terminal_output(self) -> Optional[str]:
        script = """
        tell application "Terminal"
            if (count of windows) > 0 then
                set frontWindow to front window
                set tabCount to count of tabs of frontWindow
                if tabCount > 0 then
                    set currentTab to selected tab of frontWindow
                    return contents of currentTab
                end if
            end if
        end tell
        return ""
        """
        try:
            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None
