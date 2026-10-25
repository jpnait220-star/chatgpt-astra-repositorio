"""Frozen installation smoke test. Never sends mouse input or reads user settings."""
import json
import threading
import traceback
from pathlib import Path


def check_installation(output):
    import tkinter as tk
    import duckac
    from duckac_engine import AutoClickController, ClickSettings

    class Backend:
        def key_down(self, key): return False
        def target_focused(self, minecraft): return False
        def inventory_context(self): return False
        def click(self, button): raise AssertionError('Diagnostics must not send input')

    root = engine = None
    report = {'ok': False}
    try:
        duckac.SETTINGS_PATH = Path(output).with_suffix('.settings.json')
        root = tk.Tk()
        engine = AutoClickController(Backend(), ClickSettings(mouse_button='middle'))
        app = duckac.DuckApp(root, engine)
        errors = []
        root.report_callback_exception = lambda *args: errors.append(str(args))
        app.open_tester()
        root.after(200, app.close)
        root.mainloop()
        assert not errors, errors
        assert not engine._thread.is_alive()
        assert not engine.status().enabled
        assert not any(t.name == 'DuckAC-Input' and t.is_alive() for t in threading.enumerate())
        report.update(ok=True, middle=True, assets=True, worker_stopped=True)
    except Exception:
        report['error'] = traceback.format_exc()
    finally:
        if engine:
            engine.stop()
        if root:
            try:
                root.destroy()
            except tk.TclError:
                pass
        Path(output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if report['ok'] else 1
