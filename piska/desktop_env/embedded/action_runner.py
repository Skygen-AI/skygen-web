from __future__ import annotations

import random
from typing import Any, Dict

import pyautogui  # type: ignore


KEYBOARD_KEYS = set(pyautogui.KEYBOARD_KEYS)


def execute_action(action: Dict[str, Any]) -> None:
    if action in ["WAIT", "FAIL", "DONE"]:
        return

    action_type = action["action_type"]
    parameters = action.get("parameters") or {
        k: v for k, v in action.items() if k != "action_type"
    }

    move_mode = random.choice(
        [
            pyautogui.easeInQuad,
            pyautogui.easeOutQuad,
            pyautogui.easeInOutQuad,
            pyautogui.easeInBounce,
            pyautogui.easeInElastic,
        ]
    )
    duration = random.uniform(0.5, 1)

    if action_type == "MOVE_TO":
        if not parameters:
            pyautogui.moveTo()
        elif "x" in parameters and "y" in parameters:
            x = parameters["x"]
            y = parameters["y"]
            pyautogui.moveTo(x, y, duration, move_mode)
        else:
            raise Exception(f"Unknown parameters: {parameters}")

    elif action_type == "CLICK":
        if not parameters:
            pyautogui.click()
        elif "button" in parameters and "x" in parameters and "y" in parameters:
            button = parameters["button"]
            x = parameters["x"]
            y = parameters["y"]
            if "num_clicks" in parameters:
                num_clicks = parameters["num_clicks"]
                pyautogui.click(button=button, x=x, y=y, clicks=num_clicks)
            else:
                pyautogui.click(button=button, x=x, y=y)
        elif "button" in parameters and "x" not in parameters and "y" not in parameters:
            button = parameters["button"]
            if "num_clicks" in parameters:
                num_clicks = parameters["num_clicks"]
                pyautogui.click(button=button, clicks=num_clicks)
            else:
                pyautogui.click(button=button)
        elif "button" not in parameters and "x" in parameters and "y" in parameters:
            x = parameters["x"]
            y = parameters["y"]
            if "num_clicks" in parameters:
                num_clicks = parameters["num_clicks"]
                pyautogui.click(x=x, y=y, clicks=num_clicks)
            else:
                pyautogui.click(x=x, y=y)
        else:
            raise Exception(f"Unknown parameters: {parameters}")

    elif action_type == "MOUSE_DOWN":
        if not parameters:
            pyautogui.mouseDown()
        elif "button" in parameters:
            button = parameters["button"]
            pyautogui.mouseDown(button=button)
        else:
            raise Exception(f"Unknown parameters: {parameters}")

    elif action_type == "MOUSE_UP":
        if not parameters:
            pyautogui.mouseUp()
        elif "button" in parameters:
            button = parameters["button"]
            pyautogui.mouseUp(button=button)
        else:
            raise Exception(f"Unknown parameters: {parameters}")

    elif action_type == "RIGHT_CLICK":
        if not parameters:
            pyautogui.rightClick()
        elif "x" in parameters and "y" in parameters:
            x = parameters["x"]
            y = parameters["y"]
            pyautogui.rightClick(x=x, y=y)
        else:
            raise Exception(f"Unknown parameters: {parameters}")

    elif action_type == "DOUBLE_CLICK":
        if not parameters:
            pyautogui.doubleClick()
        elif "x" in parameters and "y" in parameters:
            x = parameters["x"]
            y = parameters["y"]
            pyautogui.doubleClick(x=x, y=y)
        else:
            raise Exception(f"Unknown parameters: {parameters}")

    elif action_type == "DRAG_TO":
        if "x" in parameters and "y" in parameters:
            x = parameters["x"]
            y = parameters["y"]
            pyautogui.dragTo(x, y, duration=1.0, button="left")

    elif action_type == "SCROLL":
        if "dx" in parameters and "dy" in parameters:
            dx = parameters["dx"]
            dy = parameters["dy"]
            pyautogui.hscroll(dx)
            pyautogui.vscroll(dy)
        elif "dx" in parameters and "dy" not in parameters:
            dx = parameters["dx"]
            pyautogui.hscroll(dx)
        elif "dx" not in parameters and "dy" in parameters:
            dy = parameters["dy"]
            pyautogui.vscroll(dy)
        else:
            raise Exception(f"Unknown parameters: {parameters}")

    elif action_type == "TYPING":
        if "text" not in parameters:
            raise Exception(f"Unknown parameters: {parameters}")
        text = parameters["text"]
        pyautogui.typewrite(text)

    elif action_type == "PRESS":
        if "key" not in parameters:
            raise Exception(f"Unknown parameters: {parameters}")
        key = parameters["key"]
        if key.lower() not in KEYBOARD_KEYS:
            raise Exception(f"Key must be one of {KEYBOARD_KEYS}")
        pyautogui.press(key)

    elif action_type == "KEY_DOWN":
        if "key" not in parameters:
            raise Exception(f"Unknown parameters: {parameters}")
        key = parameters["key"]
        if key.lower() not in KEYBOARD_KEYS:
            raise Exception(f"Key must be one of {KEYBOARD_KEYS}")
        pyautogui.keyDown(key)

    elif action_type == "KEY_UP":
        if "key" not in parameters:
            raise Exception(f"Unknown parameters: {parameters}")
        key = parameters["key"]
        if key.lower() not in KEYBOARD_KEYS:
            raise Exception(f"Key must be one of {KEYBOARD_KEYS}")
        pyautogui.keyUp(key)

    elif action_type == "HOTKEY":
        keys = parameters.get("keys") if isinstance(parameters, dict) else None
        if not isinstance(keys, list) or len(keys) < 2:
            raise Exception("HOTKEY action requires a List of at least two keys.")
        for key in keys:
            if key.lower() not in KEYBOARD_KEYS:
                raise Exception(f"Key '{key}' is not a valid keyboard key.")
        pyautogui.hotkey(*keys)

    elif action_type in ["WAIT", "FAIL", "DONE"]:
        return
    else:
        raise Exception(f"Unknown action type: {action_type}")
