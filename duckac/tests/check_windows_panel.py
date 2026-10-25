"""Real HWND/cursor guard check on CI Windows; SendInput is disabled."""
import ctypes
import os
import sys
import tempfile
import tkinter as tk
from ctypes import wintypes as wt
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import duckac
from duckac_engine import AutoClickController, ClickSettings, WindowsBackend

if os.name != 'nt':
    print('Windows cursor/handle check skipped on this OS')
    raise SystemExit(0)

with tempfile.TemporaryDirectory() as temp, patch.object(duckac, 'SETTINGS_PATH', Path(temp)/'settings.json'):
    root = tk.Tk()
    backend = WindowsBackend()
    engine = AutoClickController(backend, ClickSettings())
    old = wt.POINT()
    backend.u.GetCursorPos(ctypes.byref(old))
    backend.u.SetCursorPos.argtypes = (ctypes.c_int, ctypes.c_int)
    try:
        with patch.object(engine, 'start'), patch.object(backend, '_send', side_effect=AssertionError('No OS clicks allowed')):
            app = duckac.DuckApp(root, engine)
            root.geometry('+50+50')
            root.update()
            for restore in (False, True):
                if restore:
                    app.minimize()
                    root.deiconify()
                    root.update()
                root.lift()
                root.focus_force()
                root.update()
                for x in (40, 150, 335):
                    assert backend.u.SetCursorPos(root.winfo_rootx()+x, root.winfo_rooty()+247)
                    root.update()
                    assert backend.pointer_over_panel(), ('panel guard', restore, x)
                    assert not backend.click('left', 0)
                app.canvas.event_generate('<Button-1>', x=150, y=247)
                app.canvas.event_generate('<B1-Motion>', x=534, y=23)
                app.canvas.event_generate('<ButtonRelease-1>', x=534, y=23)
                root.update()
                assert not app.closed and not app.minimized
            app.close()
    finally:
        backend.close()
        backend.u.SetCursorPos(old.x, old.y)
        try:
            root.destroy()
        except tk.TclError:
            pass
print('Windows OK: native pointer guard, restore, slider drag; no OS clicks sent')
