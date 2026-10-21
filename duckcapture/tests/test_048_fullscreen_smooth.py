"""0.4.8: F11 monitor fallback is focus-gated and frames are buffered."""
import sys
import types
import time
from types import SimpleNamespace
import numpy as np
import pytest

try:
    import PySide6.QtCore
except ModuleNotFoundError:
    if "duckcapture.windows" not in sys.modules:
        mod = types.ModuleType("duckcapture.windows")
        mod.window_exists = lambda hwnd: True
        mod.window_minimized = lambda hwnd: False
        sys.modules["duckcapture.windows"] = mod

from duckcapture import capture
from duckcapture.capture import CaptureEngine
from duckcapture.config import Settings
from duckcapture.frame_pacer import SourceFramePacer
from duckcapture.media import Media

class FakeSource:
    sources = []
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.events = {}
        self.stopped = False
        self.sources.append(self)
    def event(self, cb):
        self.events[cb.__name__] = cb
        return cb
    def start_free_threaded(self):
        return self
    def is_finished(self):
        return self.stopped
    def stop(self):
        self.stopped = True
    def frame(self, value):
        pixels = np.full((30, 30, 4), value, dtype=np.uint8)
        self.events["on_frame_arrived"](SimpleNamespace(frame_buffer=pixels), self)


def test_f11_switches_to_selected_monitor_and_back(monkeypatch):
    FakeSource.sources.clear()
    focus = [True]
    fullscreen_idx = [1]
    monkeypatch.setattr(capture, "monitor_for_fullscreen", lambda hwnd, pid: fullscreen_idx[0])
    monkeypatch.setattr(capture, "is_target_foreground", lambda hwnd, pid: focus[0])
    engine = CaptureEngine(Media(), source_factory=FakeSource)
    engine.settings = Settings(fps=60, fullscreen_compatibility=True)
    engine.hwnd = 987
    engine.target_pid = 222
    engine._detect_fullscreen(force=True)
    assert engine.capture_mode == "monitor"
    engine._open_source()
    monitor = FakeSource.sources[-1]
    assert monitor.kwargs.get("monitor_index") == 1 and "window_hwnd" not in monitor.kwargs
    focus[0] = False
    monitor.frame(10)
    assert engine.latest is None and not engine.frame_queue, "Must not capture other apps on Alt+Tab"
    focus[0] = True
    time.sleep(0.019)
    monitor.frame(12)
    assert engine.latest[0, 0, 0] == 12
    fullscreen_idx[0] = None
    engine._detect_fullscreen(force=True)
    engine._open_source()
    window = FakeSource.sources[-1]
    assert window.kwargs.get("window_hwnd") == 987 and "monitor_index" not in window.kwargs
    # An old monitor callback must remain focus-gated even during reconnect.
    focus[0] = False
    monitor.frame(22)
    assert engine.latest[0, 0, 0] == 12
    engine.done.set()
    engine.control.stop()


def test_disable_fullscreen_fallback(monkeypatch):
    engine = CaptureEngine(Media(), source_factory=FakeSource)
    engine.settings = Settings(fullscreen_compatibility=False)
    engine.hwnd = 123
    monkeypatch.setattr(capture, "monitor_for_fullscreen", lambda *args: 0)
    assert not engine._detect_fullscreen(force=True)
    assert engine.capture_mode == "window"
    engine.shutdown()


def test_jitter_queue_returns_distinct_frames_in_order():
    engine = CaptureEngine(Media(), source_factory=FakeSource)
    with engine.lock:
        engine.frame_queue.extend([np.full((1, 1, 4), i, dtype=np.uint8) for i in (1, 2, 3)])
        engine.latest = engine.frame_queue[-1]
    taken = []
    for _ in range(4):
        with engine.lock:
            item = engine.frame_queue.popleft() if engine.frame_queue else engine.latest
        taken.append(int(item[0, 0, 0]))
    assert taken == [1, 2, 3, 3]
    engine.shutdown()


def test_low_fps_source_keeps_all_frames():
    pacer = SourceFramePacer(60)
    assert sum(pacer.allow(i / 40) for i in range(400)) == 400


def test_live_f11_change_reconnects_without_stopping_replay(monkeypatch):
    focus = [True]
    fullscreen_idx = [None]
    monkeypatch.setattr(capture, "monitor_for_fullscreen", lambda *a: fullscreen_idx[0])
    monkeypatch.setattr(capture, "is_target_foreground", lambda *a: focus[0])
    engine = CaptureEngine(Media(), source_factory=FakeSource)
    engine.settings = Settings(fullscreen_compatibility=True)
    engine.hwnd = 323
    engine.target_pid = 220
    engine._open_source()
    first_source = engine.control
    fullscreen_idx[0] = 0
    engine._maintain_source()
    engine.restart_thread.join(timeout=3)
    assert engine.control is not first_source
    assert engine.control.kwargs.get("monitor_index") == 0
    assert first_source.stopped
    assert engine.capture_mode == "monitor"
    engine.done.set()
    engine.control.stop()
