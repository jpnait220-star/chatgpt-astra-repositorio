"""Small Windows-only helpers; importing the GUI remains portable for tests."""
import ctypes
import os


class SingleInstance:
    def __init__(self):
        self.handle = None
        self.already_running = False
        if os.name == 'nt':
            from ctypes import wintypes as wt
            self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            self.kernel.CreateMutexW.argtypes = (ctypes.c_void_p, wt.BOOL, wt.LPCWSTR)
            self.kernel.CreateMutexW.restype = wt.HANDLE
            self.kernel.CloseHandle.argtypes = (wt.HANDLE,)
            self.handle = self.kernel.CreateMutexW(None, False, 'Local\\DuckAC.SingleInstance.V8')
            if not self.handle:
                raise ctypes.WinError(ctypes.get_last_error())
            self.already_running = ctypes.get_last_error() == 183

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def enable_dpi_awareness():
    if os.name == 'nt':
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()


def show_in_taskbar(root):
    """Frameless window keeps its own taskbar/Alt+Tab entry."""
    if os.name != 'nt':
        return
    from ctypes import wintypes as wt
    user = ctypes.windll.user32
    user.GetAncestor.argtypes = (wt.HWND, wt.UINT)
    user.GetAncestor.restype = wt.HWND
    hwnd = user.GetAncestor(root.winfo_id(), 2)
    get = user.GetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p) == 8 else user.GetWindowLongW
    set_ = user.SetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p) == 8 else user.SetWindowLongW
    get.argtypes = (wt.HWND, ctypes.c_int)
    get.restype = ctypes.c_ssize_t
    set_.argtypes = (wt.HWND, ctypes.c_int, ctypes.c_ssize_t)
    set_.restype = ctypes.c_ssize_t
    style = get(hwnd, -20)
    set_(hwnd, -20, (style | 0x40000) & ~0x80)  # APPWINDOW, not TOOLWINDOW
    user.SetWindowPos.argtypes = (wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int,
                                  ctypes.c_int, ctypes.c_int, wt.UINT)
    user.SetWindowPos(hwnd, None, 0, 0, 0, 0, 0x37)  # frame changed; no resize/activate
