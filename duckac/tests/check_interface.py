"""Real Tk smoke test. Run with a display; never injects OS mouse input."""
import os
import sys
import tempfile
import tkinter as tk
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import duckac
from duckac_engine import AutoClickController,ClickSettings,VK_SHIFT

class PreviewBackend:
    def __init__(self):self.keys=set()
    def key_down(self,key):return key in self.keys
    def target_focused(self,_):return False
    def inventory_context(self):return False
    def click(self,_):raise AssertionError('GUI check must never inject clicks')

with tempfile.TemporaryDirectory() as temp, patch.object(duckac,'SETTINGS_PATH',Path(temp)/'settings.json'):
    root=tk.Tk()
    callback_errors=[]
    root.report_callback_exception=lambda *error:callback_errors.append(error)
    backend=PreviewBackend()
    engine=AutoClickController(backend,ClickSettings(cps=25))
    with patch.object(engine, "start"):
        app=duckac.DuckApp(root,engine)
    root.report_callback_exception=lambda *error:callback_errors.append(error)
    engine._heartbeat = None  # Deterministic engine clock for synthetic keys.
    root.update()
    assert not root.overrideredirect()
    assert (root.winfo_width(),root.winfo_height())==(duckac.W,duckac.H)
    # Hit-test actual vector controls instead of invoking all their methods directly.
    def click(x,y):
        app.canvas.event_generate('<Button-1>',x=x,y=y)
        app.canvas.event_generate('<ButtonRelease-1>',x=x,y=y)
        root.update()
    click(55,195)
    assert engine.settings.cps==24
    click(335,247)
    assert engine.settings.cps==25
    click(145,400)
    assert engine.settings.mouse_button=='middle'
    click(220,400)
    assert engine.settings.mouse_button=='right'
    click(410,400)
    assert app.capture
    backend.keys={VK_SHIFT,ord('R')}
    engine._tick(1000)
    assert not engine.status().enabled
    app.canvas.focus_force()
    root.update()
    app.canvas.event_generate('<KeyPress-i>')
    root.update()
    assert engine.settings.hotkey=='I'
    assert not app.capture
    assert duckac.load_settings().hotkey=='I'
    backend.keys={ord('I')}
    engine._tick(1000.01)
    assert not engine.status().enabled
    backend.keys.clear();engine._tick(1000.02)
    backend.keys={VK_SHIFT,ord('R')};engine._tick(1000.03)
    assert not engine.status().enabled
    backend.keys={ord('I')};engine._tick(1000.04)
    assert engine.status().enabled
    backend.keys.clear();engine._tick(1000.05)
    backend.keys={ord('I')};engine._tick(1000.06)
    assert not engine.status().enabled
    backend.keys.clear()
    click(80,466)
    assert not engine.settings.inventory_pause
    click(80,466)
    assert engine.settings.inventory_pause
    click(130,550)
    assert engine.status().enabled
    click(412,550)
    assert not engine.status().enabled
    # Drag outside the slider, including over caption buttons.
    for destination in ((534,23),(490,23),(-100,247),(700,247)):
        app.canvas.event_generate('<Button-1>',x=150,y=247)
        for x in range(40,336,7):
            app.canvas.event_generate('<B1-Motion>',x=x,y=247)
            root.update()
        app.canvas.event_generate('<B1-Motion>',x=destination[0],y=destination[1])
        app.canvas.event_generate('<Button-1>',x=destination[0],y=destination[1])
        app.canvas.event_generate('<ButtonRelease-1>',x=destination[0],y=destination[1])
        root.update()
        assert not app.closed and not app.minimized and root.winfo_exists()
        assert 1<=engine.settings.cps<=25
    # Releasing a different control over X must not close the app.
    app.canvas.event_generate('<Button-1>',x=55,y=195)
    app.canvas.event_generate('<ButtonRelease-1>',x=534,y=23)
    root.update()
    assert not app.closed
    # All canvas text stays within the panel bounds.
    app.hover=None;app.render();root.update()
    for item in app.canvas.find_all():
        if app.canvas.type(item)=='text':
            x0,y0,x1,y1=app.canvas.bbox(item)
            assert 0<=x0<x1<=duckac.W and 0<=y0<y1<=duckac.H, app.canvas.itemcget(item,'text')
    if '--screenshot' in sys.argv:
        from PIL import ImageGrab
        root.geometry('+20+20');root.update()
        ImageGrab.grab(bbox=(root.winfo_rootx(),root.winfo_rooty(),root.winfo_rootx()+duckac.W,root.winfo_rooty()+duckac.H),**({'xdisplay':root.winfo_screen()} if os.name!='nt' else {})).save(
            Path(__file__).resolve().parents[1]/'PREVIA.png')
    # Tester receives real Tk event callbacks independently of the engine.
    click(440,466)
    tester=app.tester
    assert tester is not None
    root.update()
    for _ in range(7):tester.area.event_generate('<ButtonRelease-1>',x=220,y=80)
    for _ in range(3):tester.area.event_generate('<ButtonRelease-3>',x=220,y=80)
    for _ in range(4):tester.area.event_generate('<ButtonRelease-2>',x=220,y=80)
    root.update()
    assert tester.meter.total==14
    assert engine.status().total_clicks==0
    root.after(120,root.quit)
    root.mainloop()
    assert tester.area.itemcget(tester.total_text,'text')=='Recebidos aqui: 14'
    tester.reset()
    assert tester.meter.total==0
    tester.close()
    assert app.tester is None
    # Test the title bar's minimize/restore code path. Xorg has no WM, so
    # Windows taskbar behavior remains a Windows-only manual check.
    app.minimize()
    root.deiconify();root.update()
    app.restore_window(SimpleNamespace(widget=root))
    root.update()
    assert not root.overrideredirect()
    # Dragging uses only the header and preserves internal positions.
    app.mouse_click(SimpleNamespace(x=200,y=22,x_root=220,y_root=42))
    app.mouse_drag(SimpleNamespace(x_root=270,y_root=92))
    app.mouse_release(None)
    assert app.window_drag is None
    app.close()
    assert not callback_errors,callback_errors
print('GUI OK: dark header, layout, vector controls, hotkey I, old shortcut ignored, CPS receiver, close/restore')
