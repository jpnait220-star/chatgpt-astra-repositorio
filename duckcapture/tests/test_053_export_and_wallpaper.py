"""Exercise decoded exports, display transitions and visible wallpaper pixels."""

import json
import threading
import time
from pathlib import Path

import numpy as np
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from duckcapture import capture
from duckcapture.capture import CaptureEngine
from duckcapture.config import Settings
from duckcapture.media import Media
from duckcapture.wallpaper import VideoBackground
from test_051_f11_recovery import MovingSource, wait_for

APP = QApplication.instance() or QApplication([])


class TracedMedia(Media):
    def __init__(self):
        super().__init__()
        self.exports = []

    def run(self, args, **kwargs):
        if kwargs.get("cwd"):
            self.exports.append(list(map(str, args)))
        return super().run(args, **kwargs)


def pixels(media, path, at):
    raw = media.run(
        [
            "-ss",
            str(at),
            "-i",
            path,
            "-frames:v",
            "1",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "pipe:1",
        ]
    ).stdout
    assert raw
    return np.frombuffer(raw, dtype=np.uint8)


def test_copy_export_seeks_between_keyframes_without_reencoding_or_freezing(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("DUCKCAPTURE_DATA", str(tmp_path / "data"))
    media = TracedMedia()
    engine = CaptureEngine(media)
    engine.session = tmp_path / "session"
    engine.session.mkdir()
    source = engine.session / "frame-000000000.mkv"
    media.run(
        [
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=s=160x90:r=30",
            "-t",
            "4",
            "-c:v",
            "libx264",
            "-g",
            "60",
            "-bf",
            "0",
            "-threads",
            "2",
            source,
        ]
    )
    (engine.session / "segments.csv").write_text(f"{source.name},0,4\n")
    engine.output_size = (160, 90)
    engine.encoder = "h264_amf"  # Export must not touch this GPU encoder.
    settings = Settings(fps=30, clips_dir=str(tmp_path / "clips"), clip_end_sound=True)
    engine.active = True
    try:
        output = engine._save_clip(
            37 / 30, 97 / 30, [], settings, engine.session, 0, None
        )
        info = media.probe(output)
        assert info.audio and abs(info.duration - 2) < 0.05
        assert np.array_equal(pixels(media, source, 37 / 30), pixels(media, output, 0))
        assert np.array_equal(
            pixels(media, source, 96 / 30), pixels(media, output, 59 / 30)
        )
        assert not np.array_equal(pixels(media, output, 0), pixels(media, output, 1.5))
        assert all(args[args.index("-c:v") + 1] == "copy" for args in media.exports)
        assert (
            json.loads(output.with_suffix(".json").read_text())["video_export"]
            == "copy"
        )
    finally:
        engine.active = False
        engine.shutdown()


def test_hud_export_uses_cpu_while_gpu_replay_remains_active(tmp_path, monkeypatch):
    monkeypatch.setenv("DUCKCAPTURE_DATA", str(tmp_path / "data"))
    media = TracedMedia()
    engine = CaptureEngine(media)
    engine.session = tmp_path / "session"
    engine.session.mkdir()
    source = engine.session / "frame-000000000.mkv"
    media.run(
        [
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=s=160x90:r=30",
            "-t",
            "2",
            "-c:v",
            "libx264",
            "-g",
            "60",
            "-bf",
            "0",
            "-threads",
            "2",
            source,
        ]
    )
    (engine.session / "segments.csv").write_text(f"{source.name},0,2\n")
    engine.encoder = "h264_amf"
    engine.output_size = (160, 90)
    settings = Settings(
        fps=30,
        clips_dir=str(tmp_path / "clips"),
        clip_end_sound=False,
        hud_enabled=True,
        hud=[dict(kind="timer", x=0.1, y=0.1)],
    )
    engine.active = True
    try:
        output = engine._save_clip(0, 1.5, [], settings, engine.session, 0, None)
        assert media.probe(output).duration >= 1.49
        export = media.exports[-1]
        assert export[export.index("-c:v") + 1] == "libx264"
        assert "-readrate" in export
        assert not np.array_equal(pixels(media, output, 0), pixels(media, output, 1))
    finally:
        engine.active = False
        engine.shutdown()


def test_requested_clip_keeps_motion_when_f11_temporarily_destroys_window(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("DUCKCAPTURE_DATA", str(tmp_path / "data"))
    exists, mode, current = [True], [None], [123]
    monkeypatch.setattr(capture, "monitor_for_fullscreen", lambda *a: mode[0])
    monkeypatch.setattr(
        capture,
        "replacement_window",
        lambda hwnd, pid, **kw: current[0]
        if exists[0] and hwnd != current[0]
        else None,
    )
    media = TracedMedia()
    engine = CaptureEngine(
        media, source_factory=MovingSource, window_exists_fn=lambda _: exists[0]
    )
    try:
        engine.start(
            123,
            Settings(
                fps=30,
                duration=2,
                encoder="libx264",
                system_audio=False,
                clip_end_sound=False,
                clips_dir=str(tmp_path / "clips"),
            ),
        )
        wait_for(lambda: engine.active and engine.elapsed > 3.3, engine)
        future = engine.save_clip()
        exists[0] = False
        time.sleep(0.4)
        current[0], mode[0], exists[0] = 234, 1, True
        wait_for(
            lambda: engine.hwnd == 234
            and engine.capture_mode == "monitor"
            and engine.received.is_set(),
            engine,
        )
        output = future.result(timeout=15)
        assert engine.active and not engine.error
        # This is the clip requested BEFORE F11, not merely the next clip.
        assert (
            np.abs(
                pixels(media, output, 0).astype(float) - pixels(media, output, 1.8)
            ).mean()
            > 8
        )
        assert abs(media.probe(output).duration - 2) < 0.1
    finally:
        engine.shutdown()


def test_source_supervision_runs_even_without_encoder_loop(monkeypatch):
    from test_048_fullscreen_smooth import FakeSource

    mode = [None]
    monkeypatch.setattr(capture, "monitor_for_fullscreen", lambda *a: mode[0])
    monkeypatch.setattr(capture, "replacement_window", lambda *a, **kw: None)
    engine = CaptureEngine(Media(), source_factory=FakeSource)
    engine.settings, engine.hwnd = Settings(), 123
    engine._open_source()
    engine.source_watch = threading.Thread(target=engine._watch_source)
    engine.source_watch.start()
    try:
        mode[0] = 1
        deadline = time.monotonic() + 3
        while engine.capture_mode != "monitor" and time.monotonic() < deadline:
            time.sleep(0.02)
        assert engine.capture_mode == "monitor"
    finally:
        engine.done.set()
        engine.source_watch.join(3)
        if engine.restart_thread:
            engine.restart_thread.join(3)
        if engine.control:
            engine.control.stop()
        engine.shutdown()


def test_alt_tab_does_not_recreate_fullscreen_source(monkeypatch):
    engine = CaptureEngine(Media())
    engine.settings, engine.hwnd, engine.capture_mode, engine.monitor_index = (
        Settings(),
        123,
        "monitor",
        1,
    )
    monkeypatch.setattr(capture, "is_target_foreground", lambda *a: False)
    monkeypatch.setattr(capture, "monitor_for_fullscreen", lambda *a: None)
    assert not engine._detect_fullscreen(force=True)
    assert engine.capture_mode == "monitor" and engine.monitor_index == 1
    engine.shutdown()


def test_wallpaper_shows_poster_when_paused_then_decodes_normalized_video(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("DUCKCAPTURE_DATA", str(tmp_path / "data"))
    media = Media()
    source = tmp_path / "wallpaper.mkv"
    # FFV1 would bypass 0.5.2 normalization just because it is <=1080p/30 FPS.
    media.run(
        [
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=lime:s=320x180:r=30",
            "-t",
            "1",
            "-c:v",
            "ffv1",
            source,
        ]
    )
    before = source.read_bytes()
    bg = VideoBackground()
    bg.resize(400, 240)
    bg.dim = 35
    bg.show()
    try:
        bg.set_video(str(source))
        until = time.monotonic() + 10
        while bg.frame.isNull() and time.monotonic() < until:
            QTest.qWait(20)
        assert bg.blocked and not bg.frame.isNull()
        assert bg.grab().toImage().pixelColor(200, 120).green() > 100
        assert bg.job is None  # No full transcode while replay/motion blocks animation.
        bg.set_blocked(False)
        until = time.monotonic() + 15
        while bg.last_frame == 0 and time.monotonic() < until:
            QTest.qWait(20)
        assert bg.last_frame > 0 and bg.prepared_path != str(source)
        assert Path(bg.prepared_path).suffix == ".mp4" and source.read_bytes() == before
    finally:
        bg.shutdown()
        bg.close()
        bg.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
