"""F11 while saving: keep the real FFmpeg replay alive across source changes."""
import threading
import time
import ctypes
from types import SimpleNamespace

import numpy as np

from duckcapture import capture
from duckcapture.capture import CaptureEngine
from duckcapture.config import Settings
from duckcapture.frame_pacer import SourceFramePacer
from duckcapture.media import Media


def wait_for(predicate, engine, timeout=10):
    end = time.monotonic() + timeout
    while not predicate():
        assert engine.error is None, engine.error
        assert time.monotonic() < end, 'Capture did not recover'
        time.sleep(.02)


class MovingSource:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.handlers = {}
        self.stopped = threading.Event()
        self.thread = None

    def event(self, callback):
        self.handlers[callback.__name__] = callback
        return callback

    def start_free_threaded(self):
        def run():
            index = 0
            while not self.stopped.is_set():
                color = [8, index % 180 + 20, 230, 255] if 'monitor_index' in self.kwargs else [230, index % 180 + 20, 8, 255]
                frame = np.tile(np.array([[color]], dtype=np.uint8), (90, 160, 1))
                self.handlers['on_frame_arrived'](SimpleNamespace(frame_buffer=frame, timespan=round((index + 1) * 10_000_000 / 30)), self)
                index += 1
                self.stopped.wait(1 / 30)
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()
        return self

    def stop(self):
        self.stopped.set()
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join(timeout=2)

    def is_finished(self):
        return self.stopped.is_set()


def test_timestamp_epoch_reset_accepts_new_frames_immediately():
    pacer = SourceFramePacer(60)
    assert pacer.allow(900)
    assert pacer.allow(900 + 1/60)
    assert pacer.allow(.01)
    assert sum(pacer.allow(.01 + i/60) for i in range(1, 61)) == 60


def test_save_then_f11_with_live_old_handle_keeps_motion_and_exports(tmp_path, monkeypatch):
    monkeypatch.setenv('DUCKCAPTURE_DATA', str(tmp_path / 'data'))
    mode, current = [None], [123]
    monkeypatch.setattr(capture, 'monitor_for_fullscreen', lambda *args: mode[0])
    monkeypatch.setattr(capture, 'is_target_foreground', lambda *args: True)
    monkeypatch.setattr(capture, 'replacement_window', lambda hwnd, pid, **kwargs: current[0] if hwnd != current[0] else None)
    media = Media()
    engine = CaptureEngine(media, source_factory=MovingSource, window_exists_fn=lambda _: True)
    try:
        engine.start(123, Settings(fps=30, encoder='libx264', system_audio=False, clip_end_sound=False, clips_dir=str(tmp_path / 'clips')))
        wait_for(lambda: engine.active and engine.elapsed >= 1.1, engine)
        session = engine.session
        first = engine.save_clip()
        assert engine.pending == 1
        mode[0], current[0] = 1, 234
        wait_for(lambda: engine.capture_mode == 'monitor' and engine.hwnd == 234 and engine.latest[0, 0, 2] == 230, engine)
        before = engine.latest.copy()
        wait_for(lambda: engine.elapsed >= 4.5, engine)
        assert not np.array_equal(before, engine.latest)
        second = engine.save_clip()
        first_path, second_path = first.result(timeout=15), second.result(timeout=15)
        assert engine.session == session and engine.active and not engine.error
        assert media.probe(first_path).duration >= 1
        duration = media.probe(second_path).duration
        frames = []
        for position in [duration - .8, duration - .2]:
            raw = media.run(['-ss', str(position), '-i', second_path, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1']).stdout
            frames.append(np.frombuffer(raw, dtype=np.uint8).reshape(90, 160, 3))
        assert frames[0][45, 80, 0] > 180  # Fullscreen source, not the old blue frame.
        assert np.abs(frames[0].astype(float) - frames[1]).mean() > 2
        mode[0] = None
        wait_for(lambda: engine.capture_mode == 'window' and engine.latest[0, 0, 0] == 230, engine)
        assert engine.session == session and engine.active
    finally:
        engine.shutdown()


def test_new_source_gets_grace_period_before_reconnect(monkeypatch):
    from test_048_fullscreen_smooth import FakeSource
    monkeypatch.setattr(capture, 'replacement_window', lambda *a, **k: None)
    monkeypatch.setattr(capture, 'monitor_for_fullscreen', lambda *a: None)
    engine = CaptureEngine(Media(), source_factory=FakeSource)
    engine.settings = Settings()
    engine.hwnd = 123
    engine.last_frame_at = time.monotonic() - 20
    try:
        engine._open_source()
        source = engine.control
        engine._maintain_source()
        assert engine.control is source and engine.restart_thread is None
        engine.last_source_attempt -= 3
        engine._maintain_source()
        assert engine.restart_thread is not None
        engine.restart_thread.join(timeout=3)
        assert engine.control is not source
    finally:
        engine.done.set()
        engine.control.stop()
        engine.shutdown()


def test_slow_native_stop_does_not_block_replacement_capture():
    from test_048_fullscreen_smooth import FakeSource
    release = threading.Event()
    engine = CaptureEngine(Media(), source_factory=FakeSource)
    engine.settings = Settings()
    engine.hwnd = 123
    engine._open_source()
    old = engine.control
    old.stop = lambda: release.wait(5)
    try:
        start = time.monotonic()
        engine._open_source()
        assert time.monotonic() - start < 1
        assert engine.control is not old
        engine.control.frame(42)
        assert engine.latest[0, 0, 0] == 42
    finally:
        release.set()
        for thread in engine.retired_sources:
            thread.join(timeout=2)
        engine.done.set()
        engine.control.stop()
        engine.shutdown()


def test_live_replacement_only_follows_unowned_same_class_game_window(monkeypatch):
    from duckcapture import fullscreen
    current_class, owner, pid = ['GLFW30'], [0], [456]
    def window_rect(hwnd, pointer):
        rect = ctypes.cast(pointer, ctypes.POINTER(fullscreen.wintypes.RECT)).contents
        rect.left, rect.top, rect.right, rect.bottom = 0, 0, 1920, 1080
        return True
    def class_name(hwnd, buffer, size):
        buffer.value = 'GLFW30' if hwnd == 123 else current_class[0]
        return len(buffer.value)
    api = SimpleNamespace(GetForegroundWindow=lambda: 234, IsWindowVisible=lambda _: True,
                          GetWindowRect=window_rect, GetClassNameW=class_name, GetWindow=lambda *_: owner[0])
    monkeypatch.setattr(fullscreen, 'IS_WINDOWS', True)
    monkeypatch.setattr(fullscreen, '_user32', api, raising=False)
    monkeypatch.setattr(fullscreen, 'process_id', lambda _: pid[0])
    assert fullscreen.replacement_window(123, 456, live=True) == 234
    current_class[0] = '#32770'
    assert fullscreen.replacement_window(123, 456, live=True) is None
    current_class[0], owner[0] = 'GLFW30', 123
    assert fullscreen.replacement_window(123, 456, live=True) is None
    owner[0], pid[0] = 0, 999
    assert fullscreen.replacement_window(123, 456, live=True) is None


def test_in_flight_old_frame_cannot_replace_new_source_pixels():
    from test_048_fullscreen_smooth import FakeSource
    engine = CaptureEngine(Media(), source_factory=FakeSource)
    engine.settings = Settings()
    engine.hwnd = 123
    engine._open_source()
    old = engine.source
    class DelayedCopy:
        def copy(self):
            engine._open_source()
            engine.control.frame(77)
            return np.full((30, 30, 4), 13, dtype=np.uint8)
    try:
        old.events['on_frame_arrived'](SimpleNamespace(frame_buffer=DelayedCopy()), old)
        assert engine.latest[0, 0, 0] == 77
        assert all(frame[0, 0, 0] == 77 for frame in engine.frame_queue)
    finally:
        engine.done.set()
        engine.control.stop()
        engine.shutdown()
