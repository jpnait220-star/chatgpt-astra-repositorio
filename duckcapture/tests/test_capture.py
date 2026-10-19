import json
import wave
from collections import deque
import numpy as np
import pytest
from PIL import Image
from duckcapture.audio import AudioRing
from duckcapture.capture import CaptureEngine
from duckcapture.config import Settings
from duckcapture.media import Media
from duckcapture import windows


def test_audio_snapshot_survives_ring_eviction_and_keeps_timing(tmp_path):
    ring = AudioRing()
    pcm = np.full((48000, 2), 12000, dtype="<i2").tobytes()
    ring.chunks.append((10, pcm))
    frozen = ring.snapshot(9.5, 11.5)
    ring.chunks.clear()
    path = tmp_path / "sound.wav"
    frozen.write(path, 9.5, 11.5)
    with wave.open(str(path), "rb") as stream:
        assert stream.getnframes() == 96000 and stream.getnchannels() == 2
        data = np.frombuffer(stream.readframes(96000), dtype="<i2").reshape(-1, 2)
    assert not data[:24000].any() and not data[72000:].any()
    assert np.all(data[24000:72000] == 12000)


def test_retention_and_screenshots(tmp_path):
    engine = CaptureEngine(Media())
    engine.settings = Settings(duration=15, fps=30, clips_dir=str(tmp_path / "clips"))
    engine.session = tmp_path / "session"
    engine.session.mkdir()
    engine.frames = 35 * 30
    old = engine.session / "old.mkv"
    recent = engine.session / "recent.mkv"
    old.write_bytes(b"old")
    recent.write_bytes(b"recent")
    (engine.session / "segments.csv").write_text("old.mkv,0,2\nrecent.mkv,20,22\n")
    engine.samples = deque([dict(t=1), dict(t=30)])
    engine.pinning = True
    engine._prune()
    assert old.exists()
    engine.pinning = False
    engine._prune()
    assert not old.exists() and recent.exists()
    assert len(engine.samples) == 1
    with pytest.raises(RuntimeError):
        engine.screenshot()
    engine.active = True
    engine.latest = np.tile(
        np.array([[[7, 13, 240, 255]]], dtype=np.uint8), (10, 20, 1)
    )
    image = Image.open(engine.screenshot())
    assert image.size == (20, 10)
    assert image.getpixel((0, 0)) == (240, 13, 7)
    engine.active = False
    engine.shutdown()


def test_hotkeys_restore_previous_binding_when_new_key_conflicts(monkeypatch):
    class API:
        def __init__(self):
            self.registered = {}
            self.fail_vk = None

        def RegisterHotKey(self, hwnd, id, mod, vk):
            if vk == self.fail_vk:
                return 0
            self.registered[id] = (mod, vk)
            return 1

        def UnregisterHotKey(self, hwnd, id):
            self.registered.pop(id, None)
            return 1

    api = API()
    monkeypatch.setattr(windows, "IS_WINDOWS", True)
    monkeypatch.setattr(windows, "user32", api, raising=False)
    hotkeys = windows.Hotkeys()
    callback = lambda: None
    hotkeys.update({"F8": callback, "F9": callback})
    api.fail_vk = windows.parse_hotkey("F11")[1]
    with pytest.raises(ValueError):
        hotkeys.update({"F10": callback, "F11": callback})
    assert {key for key, _ in hotkeys.callbacks.values()} == {"F8", "F9"}
    assert len(api.registered) == 2
    hotkeys.clear()
    assert not api.registered


def test_replay_fractional_trim_audio_and_image_overlay(tmp_path):
    media = Media()
    engine = CaptureEngine(media)
    sticker = tmp_path / "image.png"
    Image.new("RGB", (20, 20), (255, 0, 0)).save(sticker)
    engine.settings = Settings(
        fps=30,
        clips_dir=str(tmp_path / "clips"),
        hud_enabled=True,
        hud=[dict(kind="image", path=str(sticker), x=0.1, y=0.1, scale=1, opacity=1)],
    )
    engine.session = tmp_path / "buffer"
    engine.session.mkdir()
    engine.output_size = (320, 180)
    engine.encoder = "libx264"
    engine.pending = 1
    media.run(
        [
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=320x180:r=30",
            "-t",
            "8",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-g",
            "60",
            "-bf",
            "0",
            "-f",
            "segment",
            "-segment_time",
            "2",
            "-reset_timestamps",
            "1",
            "-segment_list",
            str(engine.session / "segments.csv"),
            "-segment_list_type",
            "csv",
            str(engine.session / "frame-%03d.mkv"),
        ]
    )
    sound = AudioRing()
    sound.chunks.append((0, np.full((48000 * 8, 2), 6000, dtype="<i2").tobytes()))
    output = engine._save_clip(2.3, 6.7, [], engine.settings, engine.session, 0, sound)
    info = media.probe(output)
    assert info.audio and abs(info.duration - 4.4) < 0.1
    frame = tmp_path / "frame.png"
    media.run(["-y", "-i", str(output), "-frames:v", "1", str(frame)])
    pixels = np.asarray(Image.open(frame).convert("RGB"))
    assert pixels[35, 50, 0] > 200 and pixels[35, 50, 2] < 70
    pcm = media.run(
        [
            "-i",
            str(output),
            "-map",
            "0:a:0",
            "-f",
            "s16le",
            "-ac",
            "2",
            "-ar",
            "48000",
            "pipe:1",
        ]
    ).stdout
    assert np.abs(np.frombuffer(pcm, dtype="<i2").astype(float)).mean() > 4000
    assert json.loads(output.with_suffix(".json").read_text())[
        "duration"
    ] == pytest.approx(4.4)
    engine.shutdown()


class SyntheticWindow:
    """Test-only WGC boundary; the writer and encoder remain real."""

    def __init__(self, **kwargs):
        self.handlers = {}
        self.stopped = False

    def event(self, handler):
        self.handlers[handler.__name__] = handler
        return handler

    def start_free_threaded(self):
        from types import SimpleNamespace

        pixels = np.tile(np.array([[[230, 30, 8, 255]]], dtype=np.uint8), (90, 160, 1))
        self.handlers["on_frame_arrived"](SimpleNamespace(frame_buffer=pixels), self)
        return self

    def is_finished(self):
        return self.stopped

    def wait(self):
        pass

    def stop(self):
        self.stopped = True


def wait_for(predicate, engine, timeout=10):
    import time

    deadline = time.monotonic() + timeout
    while not predicate():
        assert not engine.error, engine.error
        assert time.monotonic() < deadline, "Capture did not reach the expected state"
        time.sleep(0.025)


def test_live_writer_saves_real_clip_despite_audio_start_failure(tmp_path, monkeypatch):
    from duckcapture import capture

    class UnavailableAudio:
        def start(self):
            raise RuntimeError("Dispositivo desconectado")

        def stop(self):
            pass

    monkeypatch.setenv("DUCKCAPTURE_DATA", str(tmp_path / "data"))
    monkeypatch.setattr(capture, "AudioRing", UnavailableAudio)
    media = Media()
    engine = CaptureEngine(media, source_factory=SyntheticWindow)
    settings = Settings(
        fps=30,
        duration=15,
        encoder="libx264",
        system_audio=True,
        clips_dir=str(tmp_path / "clips"),
    )
    try:
        engine.start(123, settings)
        wait_for(lambda: engine.active and engine.elapsed >= 2.3, engine)
        output = engine.save_clip().result(timeout=12)
        info = media.probe(output)
        assert not info.audio
        assert 2.2 <= info.duration <= 3.0
        assert info.width == 160 and info.height == 90
        events = list(engine.events.queue)
        assert sum(kind == "started" for kind, _ in events) == 1
        assert any(
            kind == "warning" and "SEM ÁUDIO" in message for kind, message in events
        )
        assert not any(kind == "capture_error" for kind, _ in events)
        engine.stop()
        engine.thread.join(timeout=5)
        assert not engine.thread.is_alive() and not engine.active
        settings.system_audio = False
        engine.start(123, settings)
        wait_for(lambda: engine.active, engine)
        assert engine.audio is None and not engine.audio_warning
        assert engine.elapsed < 1
    finally:
        engine.shutdown()


def test_native_start_failure_is_reported_without_false_started(tmp_path, monkeypatch):
    class FailedWindow(SyntheticWindow):
        def start_free_threaded(self):
            self.stopped = True
            return self

        def wait(self):
            raise RuntimeError("WGC: acesso à janela negado")

    monkeypatch.setenv("DUCKCAPTURE_DATA", str(tmp_path / "data"))
    engine = CaptureEngine(Media(), source_factory=FailedWindow)
    try:
        engine.start(123, Settings(system_audio=False))
        engine.thread.join(timeout=2)
        assert not engine.thread.is_alive()
        events = list(engine.events.queue)
        assert any(
            kind == "capture_error" and "acesso à janela" in message
            for kind, message in events
        )
        assert not any(kind == "started" for kind, _ in events)
        assert not engine.active and not engine.starting
    finally:
        engine.shutdown()


def test_cancel_before_first_frame_is_not_reported_as_error(tmp_path, monkeypatch):
    class WaitingWindow(SyntheticWindow):
        def start_free_threaded(self):
            return self

    monkeypatch.setenv("DUCKCAPTURE_DATA", str(tmp_path / "data"))
    engine = CaptureEngine(Media(), source_factory=WaitingWindow)
    try:
        engine.start(123, Settings(system_audio=False))
        engine.stop()
        engine.thread.join(timeout=2)
        assert not engine.thread.is_alive() and engine.error is None
        assert all(
            kind not in ("capture_error", "started") for kind, _ in engine.events.queue
        )
    finally:
        engine.shutdown()


def test_runtime_encoder_error_contains_ffmpeg_diagnostic(tmp_path, monkeypatch):
    class BrokenEncoder(Media):
        def encoder(self, *args, **kwargs):
            return "libx264"

        def encoding(self, *args):
            return ["-c:v", "encoder_does_not_exist"]

    monkeypatch.setenv("DUCKCAPTURE_DATA", str(tmp_path / "data"))
    engine = CaptureEngine(BrokenEncoder(), source_factory=SyntheticWindow)
    try:
        engine.start(123, Settings(system_audio=False))
        engine.thread.join(timeout=6)
        assert not engine.thread.is_alive()
        assert engine.error and "encoder_does_not_exist" in engine.error
        assert (tmp_path / "data/last-encoder.log").is_file()
        assert any(kind == "capture_error" for kind, _ in engine.events.queue)
    finally:
        engine.shutdown()


def test_audio_com_is_balanced_for_repeated_workers_and_record_failure(monkeypatch):
    import ctypes
    import sys
    from types import SimpleNamespace
    from duckcapture import audio

    calls = []

    class Function:
        def __init__(self, name):
            self.name = name

        def __call__(self, *args):
            calls.append(self.name)
            return 0

    dll = SimpleNamespace(
        CoInitializeEx=Function("initialize"), CoUninitialize=Function("release")
    )
    monkeypatch.setattr(ctypes, "WinDLL", lambda _: dll, raising=False)
    monkeypatch.setattr(audio, "os", SimpleNamespace(name="nt"))
    current = [None]
    fail = [False]

    class Recorder:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def record(self, **kwargs):
            assert not current[0].ready.is_set()
            if fail[0]:
                raise RuntimeError("Falha na primeira amostra")
            current[0].done.set()
            return np.zeros((960, 2))

    mic = SimpleNamespace(recorder=lambda **kwargs: Recorder())
    monkeypatch.setitem(
        sys.modules,
        "soundcard",
        SimpleNamespace(
            default_speaker=lambda: SimpleNamespace(id="speaker"),
            get_microphone=lambda **kwargs: mic,
        ),
    )
    for failure in (False, False, True):
        ring = AudioRing()
        current[0], fail[0] = ring, failure
        ring._run()
        assert ring.ready.is_set()
        assert bool(ring.error) == failure
        assert bool(ring.chunks) != failure
    assert calls == ["initialize", "release"] * 3
    assert dll.CoUninitialize.restype is None
