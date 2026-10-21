"""Windows fullscreen checks for an opt-in, foreground-only F11 fallback.

This module imports on Linux as well so the replay can be unit-tested without
Win32 or PySide6. Monitor capture must NEVER copy the desktop when the selected
application is not the active foreground process.
"""
from __future__ import annotations

import ctypes
import os
from ctypes import wintypes

IS_WINDOWS = os.name == "nt"
if IS_WINDOWS:
    _user32 = ctypes.WinDLL("user32", use_last_error=True)
    _user32.GetForegroundWindow.restype = wintypes.HWND
    _user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    _user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    _user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    _user32.GetWindowRect.restype = wintypes.BOOL
    _user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
    _user32.MonitorFromWindow.restype = wintypes.HANDLE
    _user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    _user32.IsWindowVisible.argtypes = [wintypes.HWND]
    _user32.IsWindow.argtypes = [wintypes.HWND]


class MonitorInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]


def process_id(hwnd):
    if not IS_WINDOWS or not hwnd:
        return None
    pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(int(hwnd), ctypes.byref(pid))
    return pid.value or None


def is_target_foreground(hwnd, pid=None):
    """Allow monitor pixels only while the selected application has focus."""
    if not IS_WINDOWS:
        return True  # Synthetic captures run under Linux tests.
    focused = _user32.GetForegroundWindow()
    if not focused:
        return False
    original_pid = pid or process_id(hwnd)
    return bool(original_pid and process_id(focused) == original_pid)


def monitor_for_fullscreen(hwnd, pid=None):
    """Return the library’s one-based monitor index only for a focused fullscreen game window."""
    if not IS_WINDOWS or not is_target_foreground(hwnd, pid):
        return None
    if not _user32.IsWindow(hwnd):
        return None
    monitor = _user32.MonitorFromWindow(hwnd, 2)  # MONITOR_DEFAULTTONEAREST
    if not monitor:
        return None
    info = MonitorInfo()
    info.cbSize = ctypes.sizeof(MonitorInfo)
    _user32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MonitorInfo)]
    _user32.GetMonitorInfoW.restype = wintypes.BOOL
    bounds = wintypes.RECT()
    if not _user32.GetMonitorInfoW(monitor, ctypes.byref(info)) or not _user32.GetWindowRect(hwnd, ctypes.byref(bounds)):
        return None
    mr = info.rcMonitor
    # Windows can add an invisible 7-8px resize border around a borderless window.
    tolerance = 16
    if any((abs(a - b) > tolerance for a, b in zip(
        (bounds.left, bounds.top, bounds.right, bounds.bottom),
        (mr.left, mr.top, mr.right, mr.bottom),
    ))):
        return None
    # windows-capture 2.0.1 Monitor::from_index is ONE-based over EnumDisplayMonitors.
    indices = []
    callback_type = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HANDLE, wintypes.HDC,
        ctypes.POINTER(wintypes.RECT), wintypes.LPARAM,
    )

    @callback_type
    def callback(current, _hdc, _rect, _data):
        indices.append(int(current))
        return True

    _user32.EnumDisplayMonitors(None, None, callback, 0)
    try:
        return indices.index(int(monitor)) + 1
    except ValueError:
        return None


def replacement_window(hwnd, pid):
    """Find a new visible game HWND if F11 recreated the previous one."""
    if not IS_WINDOWS or not pid:
        return None
    current = int(_user32.GetForegroundWindow() or 0)
    if current and current != hwnd and process_id(current) == pid:
        return current
    candidates = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def callback(candidate, _data):
        if (int(candidate) != hwnd and process_id(candidate) == pid
                and _user32.IsWindowVisible(candidate)):
            bounds = wintypes.RECT()
            if _user32.GetWindowRect(candidate, ctypes.byref(bounds)) and (bounds.right - bounds.left) >= 100 and (bounds.bottom - bounds.top) >= 100:
                candidates.append(int(candidate))
        return True

    _user32.EnumWindows(callback, 0)
    return candidates[0] if candidates else None
