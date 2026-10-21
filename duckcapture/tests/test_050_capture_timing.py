"""F11 uses one-based monitor indices; native timestamps survive callback jitter."""
import ctypes
import time
from types import SimpleNamespace
import numpy as np
from duckcapture import fullscreen, capture
from duckcapture.capture import CaptureEngine
from duckcapture.config import Settings
from duckcapture.media import Media
from duckcapture.frame_pacer import SourceFramePacer, FrameWaiter
from test_048_fullscreen_smooth import FakeSource


def test_native_monitor_indices_start_at_one(monkeypatch):
    bounds = (0, 0, 1920, 1080)
    def monitor_info(handle, pointer):
        info = ctypes.cast(pointer, ctypes.POINTER(fullscreen.MonitorInfo)).contents
        info.rcMonitor.left, info.rcMonitor.top, info.rcMonitor.right, info.rcMonitor.bottom = bounds
        return True
    def window_rect(hwnd, pointer):
        rect = ctypes.cast(pointer, ctypes.POINTER(fullscreen.wintypes.RECT)).contents
        rect.left, rect.top, rect.right, rect.bottom = bounds
        return True
    def enumerate_monitors(hdc, rect, callback, data):
        for handle in [100, 200]:
            callback(handle, None, None, 0)
        return True
    monkeypatch.setattr(fullscreen, 'IS_WINDOWS', True)
    monkeypatch.setattr(fullscreen, 'is_target_foreground', lambda *_: True)
    monkeypatch.setattr(ctypes, 'WINFUNCTYPE', ctypes.CFUNCTYPE, raising=False)
    api = SimpleNamespace(IsWindow=lambda *_: True, MonitorFromWindow=lambda hwnd, *_: hwnd,
                          GetMonitorInfoW=monitor_info, GetWindowRect=window_rect,
                          EnumDisplayMonitors=enumerate_monitors)
    monkeypatch.setattr(fullscreen, '_user32', api, raising=False)
    assert fullscreen.monitor_for_fullscreen(100) == 1
    assert fullscreen.monitor_for_fullscreen(200) == 2
    monkeypatch.setattr(fullscreen, 'is_target_foreground', lambda *_: False)
    assert fullscreen.monitor_for_fullscreen(100) is None


def test_native_frame_time_keeps_60_fps_despite_python_callback_jitter(monkeypatch):
    engine = CaptureEngine(Media(), source_factory=FakeSource)
    engine.settings = Settings(fps=60)
    engine.hwnd, engine.target_pid = 123, 456
    engine._open_source()
    rng = np.random.default_rng(77)
    arrivals = np.cumsum(1/60+rng.uniform(-.010, .010, 600))
    now = [1000.]
    monkeypatch.setattr(capture.time, 'monotonic', lambda: now[0])
    delivered = 0
    try:
        for i, timestamp in enumerate(arrivals):
            now[0] = 1000+timestamp
            native = SimpleNamespace(frame_buffer=np.full((4, 4, 4), i % 255, dtype=np.uint8), timespan=round((i/60+1)*10_000_000))
            before = engine.latest
            engine.source.events['on_frame_arrived'](native, engine.control)
            delivered += engine.latest is not before
        assert delivered == 600
    finally:
        engine.shutdown()


def test_jittery_source_is_sampled_nearest_deadline():
    rng = np.random.default_rng(77)
    samples = np.cumsum(1/60 + rng.uniform(-.003, .003, 600))
    pacer = SourceFramePacer(60)
    assert sum(pacer.allow(t) for t in samples) / samples[-1] > 59


def test_frame_buffer_keeps_its_owner_and_resizes_once():
    engine = CaptureEngine(Media())
    engine.settings = Settings()
    source = np.full((108, 192, 4), 100, dtype=np.uint8)
    try:
        payload = engine._frame_payload(source, 640, 360, 96, 54)
        assert len(payload) == 96*54*4
        assert isinstance(payload, memoryview)
        assert np.asarray(payload).mean() == 100
        assert engine._frame_payload(source, 640, 360, 96, 54) is payload
        assert len(engine._frame_payload(source, 640, 360, 48, 27)) == 48*27*4
    finally:
        engine.shutdown()


def test_frame_waiter_cancellation_returns_without_delay():
    import threading
    stopped = threading.Event()
    stopped.set()
    waiter = FrameWaiter()
    try:
        before = time.monotonic()
        waiter.wait(.05, stopped)
        assert time.monotonic()-before < .04
    finally:
        waiter.close()
