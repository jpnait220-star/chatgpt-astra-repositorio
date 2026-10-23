"""Clock-based frame selection for variable-refresh window capture.

Windows Graphics Capture can deliver e.g. 75, 90, 100 or 144 FPS. Dropping
all callbacks closer than a fixed interval to the LAST accepted callback
creates aliasing: a 90 FPS game sampled with a fixed 60 FPS minimum interval
ends up with only 45 distinct FPS. Track the ideal *next* sample deadline
instead, and distribute accepted frames over the input timeline.
"""
from __future__ import annotations
import math


class SourceFramePacer:
    def __init__(self, fps: float):
        if not math.isfinite(fps) or fps <= 0:
            raise ValueError("A meta de FPS deve ser maior que zero")
        self.interval = 1.0 / fps
        self.next_due: float | None = None
        self.last_timestamp: float | None = None
        self.accepted = 0
        self.skipped = 0

    def allow(self, now: float) -> bool:
        """Return True for the source frame nearest the output sampling deadline.

        For a slow game accept every available frame; for a fast game select at
        the requested output rate *on average* (not every Nth frame). After a
        long pause reset phase so the callback never attempts a catch-up burst.
        """
        # A recreated WGC frame pool can restart its timestamp epoch after F11.
        # Do not reject every new frame until the old epoch is reached again.
        if self.last_timestamp is not None and now < self.last_timestamp - self.interval:
            self.next_due = None
        self.last_timestamp = now
        if self.next_due is None:
            self.next_due = now + self.interval
        elif now + self.interval * .5 < self.next_due:
            self.skipped += 1
            return False
        elif now - self.next_due >= self.interval:
            self.next_due = now + self.interval
        else:
            self.next_due += self.interval
        self.accepted += 1
        return True


class FrameWaiter:
    """High-resolution Windows waits without busy-spinning or global timer changes."""
    def __init__(self):
        self.handle = None
        import os
        if os.name != 'nt':
            return
        import ctypes
        from ctypes import wintypes
        self.ctypes = ctypes
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.CreateWaitableTimerExW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        self.kernel.CreateWaitableTimerExW.restype = wintypes.HANDLE
        self.kernel.SetWaitableTimer.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_longlong), wintypes.LONG, ctypes.c_void_p, ctypes.c_void_p, wintypes.BOOL]
        self.kernel.SetWaitableTimer.restype = wintypes.BOOL
        self.kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel.WaitForSingleObject.restype = wintypes.DWORD
        self.kernel.CancelWaitableTimer.argtypes = [wintypes.HANDLE]
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        # Windows 10 1803+; unsupported systems use the cancellable Event fallback.
        self.handle = self.kernel.CreateWaitableTimerExW(None, None, 2, 0x100002)

    def wait(self, seconds, cancelled):
        if seconds <= 0 or cancelled.is_set():
            return
        seconds = min(seconds, .05)
        if self.handle:
            due = self.ctypes.c_longlong(-max(1, round(seconds * 10_000_000)))
            if self.kernel.SetWaitableTimer(self.handle, self.ctypes.byref(due), 0, None, None, False):
                self.kernel.WaitForSingleObject(self.handle, math.ceil(seconds*1000)+50)
                return
        cancelled.wait(seconds)

    def close(self):
        if self.handle:
            self.kernel.CancelWaitableTimer(self.handle)
            self.kernel.CloseHandle(self.handle)
            self.handle = None
