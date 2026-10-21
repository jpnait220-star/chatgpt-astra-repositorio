from __future__ import annotations
import ctypes
import os
from collections import deque
from ctypes import wintypes
try:
    from PySide6.QtCore import QAbstractNativeEventFilter
except ModuleNotFoundError:
    # Hotkeys are only attached to a Qt application on Windows. Let the
    # platform-independent replay engine run its offline tests without Qt.
    class QAbstractNativeEventFilter:
        pass

KEYS = {
    "W": 0x57,
    "A": 0x41,
    "S": 0x53,
    "D": 0x44,
    "SPACE": 0x20,
    "SHIFT": 0x10,
    "CTRL": 0x11,
}
IS_WINDOWS = os.name == "nt"
if IS_WINDOWS:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD),
    ]
    user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
    user32.GetAsyncKeyState.restype = ctypes.c_short


def window_exists(hwnd):
    return bool(IS_WINDOWS and user32.IsWindow(hwnd))


def window_minimized(hwnd):
    return bool(IS_WINDOWS and user32.IsIconic(hwnd))


def list_windows():
    if not IS_WINDOWS:
        return []
    result = []
    callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @callback
    def each(hwnd, _):
        length = user32.GetWindowTextLengthW(hwnd)
        if user32.IsWindowVisible(hwnd) and length:
            name = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, name, length + 1)
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            if (
                pid.value != os.getpid()
                and rect.right > rect.left
                and rect.bottom > rect.top
            ):
                result.append((int(hwnd), name.value))
        return True

    user32.EnumWindows(each, 0)
    return sorted(result, key=lambda x: x[1].casefold())


def parse_hotkey(value):
    parts = value.upper().replace("CONTROL", "CTRL").split("+")
    mod = 0x4000
    for prefix in parts[:-1]:
        if prefix not in ("CTRL", "ALT", "SHIFT"):
            raise ValueError(
                "Use Ctrl, Alt ou Shift com F1–F24, uma letra ou um número."
            )
        mod |= {"CTRL": 2, "ALT": 1, "SHIFT": 4}[prefix]
    key = parts[-1]
    if key.startswith("F") and key[1:].isdigit() and 1 <= int(key[1:]) <= 24:
        vk = 0x70 + int(key[1:]) - 1
    elif len(key) == 1 and key.isascii() and key.isalnum():
        vk = ord(key)
    else:
        raise ValueError("Atalho inválido. Exemplos: F8, Ctrl+F8 ou Ctrl+Shift+C.")
    return mod, vk


class Hotkeys(QAbstractNativeEventFilter):
    def __init__(self):
        super().__init__()
        self.callbacks = {}
        self.serial = 200

    def update(self, mapping):
        parsed = [parse_hotkey(key) for key in mapping]
        if len(set(parsed)) != len(parsed):
            raise ValueError("Os atalhos de clipe e print precisam ser diferentes.")
        if not IS_WINDOWS:
            return
        fresh = {}
        # Unregister old bindings and roll back if a new shortcut is unavailable.
        previous = list(self.callbacks.values())
        self.clear()
        try:
            for (key, callback), (mod, vk) in zip(mapping.items(), parsed):
                self.serial += 1
                if not user32.RegisterHotKey(None, self.serial, mod, vk):
                    raise ValueError(
                        f"O atalho {key} já está em uso por outro aplicativo."
                    )
                fresh[self.serial] = (key, callback)
        except Exception:
            for id in fresh:
                user32.UnregisterHotKey(None, id)
            for key, callback in previous:
                self.serial += 1
                mod, vk = parse_hotkey(key)
                if user32.RegisterHotKey(None, self.serial, mod, vk):
                    self.callbacks[self.serial] = (key, callback)
            raise
        self.callbacks = fresh

    def clear(self):
        if IS_WINDOWS:
            for id in self.callbacks:
                user32.UnregisterHotKey(None, id)
        self.callbacks = {}

    def nativeEventFilter(self, event_type, message):
        if IS_WINDOWS and bytes(event_type) in (
            b"windows_generic_MSG",
            b"windows_dispatcher_MSG",
        ):
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == 0x312 and int(msg.wParam) in self.callbacks:
                self.callbacks[int(msg.wParam)][1]()
                return True, 0
        return False, 0


class InputSampler:
    def __init__(self):
        self.previous = set()
        self.clicks = deque()

    def reset(self):
        self.previous.clear()
        self.clicks.clear()

    def sample(self, hwnd, t, music=""):
        result = dict(
            t=t, keys=[], buttons=[], cursor=[0.5, 0.5], cps=0, click=False, music=music
        )
        if not IS_WINDOWS or user32.GetForegroundWindow() != hwnd:
            self.previous = set()
            return result
        result["keys"] = [
            key for key, code in KEYS.items() if user32.GetAsyncKeyState(code) & 0x8000
        ]
        buttons = {
            name
            for name, code in [("L", 1), ("R", 2), ("M", 4)]
            if user32.GetAsyncKeyState(code) & 0x8000
        }
        new = buttons - self.previous
        if new:
            self.clicks.extend([t] * len(new))
            result["click"] = True
        self.previous = buttons
        while self.clicks and self.clicks[0] < t - 1:
            self.clicks.popleft()
        result["cps"] = len(self.clicks)
        result["buttons"] = sorted(buttons)
        point = wintypes.POINT()
        rect = wintypes.RECT()
        if user32.GetCursorPos(ctypes.byref(point)) and user32.GetWindowRect(
            hwnd, ctypes.byref(rect)
        ):
            result["cursor"] = [
                max(0, min(1, (point.x - rect.left) / max(1, rect.right - rect.left))),
                max(0, min(1, (point.y - rect.top) / max(1, rect.bottom - rect.top))),
            ]
        return result
