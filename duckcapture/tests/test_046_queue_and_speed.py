"""0.4.6: F8 queues jobs, stable snapshots and fast same-volume copies."""
import json
import os
import sys
import types
from pathlib import Path

import pytest

# Offline/Linux test runners may not have Qt. Only the Windows-window adapter
# is irrelevant for a pre-generated FFmpeg segment test.
try:
    import PySide6.QtCore  # noqa: F401
except ModuleNotFoundError:
    if "duckcapture.windows" not in sys.modules:
        mock_windows = types.ModuleType("duckcapture.windows")
        mock_windows.window_exists = lambda hwnd: True
        mock_windows.window_minimized = lambda hwnd: False
        sys.modules["duckcapture.windows"] = mock_windows

from duckcapture.capture import CaptureEngine
from duckcapture.config import Settings
from duckcapture.media import Media


def test_two_quick_saves_export_in_order_without_rejecting(tmp_path):
    media = Media()
    if not (media.ffmpeg and media.ffprobe):
        pytest.skip("FFmpeg not available")
    engine = CaptureEngine(media)
    session = tmp_path / "buffer"
    session.mkdir()
    engine.session = session
    engine.settings = Settings(
        fps=30, duration=15, clips_dir=str(tmp_path / "clips"),
        system_audio=False, hud_enabled=False,
    )
    engine.output_size = (160, 90)
    engine.encoder = "libx264"
    engine.epoch = 0.0
    engine.frames = 8 * 30
    engine.active = True
    media.run([
        "-y", "-f", "lavfi", "-i", "color=c=blue:s=160x90:r=30",
        "-t", "8", "-c:v", "libx264", "-preset", "ultrafast",
        "-g", "60", "-bf", "0", "-force_key_frames",
        "expr:gte(t,n_forced*2)", "-f", "segment", "-segment_time",
        "2", "-reset_timestamps", "1", "-segment_list",
        str(session / "segments.csv"), "-segment_list_type", "csv",
        str(session / "frame-%09d.mkv"),
    ])
    try:
        first = engine.save_clip()
        second = engine.save_clip()
        assert engine.pending >= 1
        assert engine.pinning
        paths = [first.result(timeout=30), second.result(timeout=30)]
        assert paths[0] != paths[1]
        assert all(path.is_file() for path in paths)
        assert all(abs(media.probe(path).duration - 8) < 0.1 for path in paths)
        assert engine.pending == 0
        assert not engine.pinning
        events = list(engine.events.queue)
        assert sum(name == "queued" for name, _ in events) == 2
        assert sum(name == "saved" for name, _ in events) == 2
        assert all(json.loads(path.with_suffix(".json").read_text())["fps"] == 30 for path in paths)
    finally:
        engine.shutdown()


def test_frozen_segment_can_be_reused_without_copy(tmp_path, monkeypatch):
    src = tmp_path / "src.mkv"
    src.write_bytes(b"test fake frozen segment")
    dest = tmp_path / "dest.mkv"
    CaptureEngine._snapshot_segment(src, dest)
    assert dest.read_bytes() == src.read_bytes()
    if os.name != "nt":
        assert src.stat().st_ino == dest.stat().st_ino
    src.unlink()
    assert dest.read_bytes() == b"test fake frozen segment"

    src2 = tmp_path / "src2.mkv"
    src2.write_bytes(b"fallback copy")
    dest2 = tmp_path / "dest2.mkv"
    def no_link(*args, **kwargs):
        raise PermissionError("link not supported")
    monkeypatch.setattr(os, "link", no_link)
    CaptureEngine._snapshot_segment(src2, dest2)
    assert dest2.read_bytes() == b"fallback copy"


def test_queue_has_backpressure_and_keeps_old_buffer_pinned(tmp_path, monkeypatch):
    engine = CaptureEngine(Media())
    engine.settings = Settings(fps=30, duration=15, clips_dir=str(tmp_path / "clips"), system_audio=False)
    engine.session = tmp_path / "buffer"
    engine.session.mkdir()
    engine.frames = 30
    engine.active = True
    engine.epoch = 0.0
    class NeverStartPool:
        def submit(self, *args, **kwargs):
            return object()
        def shutdown(self, wait=True):
            pass
    engine.pool.shutdown(wait=True)
    engine.pool = NeverStartPool()
    for n in range(engine.MAX_PENDING_CLIPS):
        engine.save_clip()
    assert engine.pending == engine.MAX_PENDING_CLIPS
    assert engine._snapshots_pending == engine.MAX_PENDING_CLIPS
    assert engine.pinning
    with pytest.raises(RuntimeError, match="Fila cheia"):
        engine.save_clip()
    assert engine.pending == engine.MAX_PENDING_CLIPS
    engine.shutdown()
