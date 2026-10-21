"""Prevent raw ffprobe timeouts from leaking into DuckCapture's clip saving."""
from __future__ import annotations
import subprocess
import json
import time
from pathlib import Path
import pytest
from duckcapture.media import Media, MediaError
from duckcapture.capture import CaptureEngine
from duckcapture.config import Settings


def test_ffprobe_timeout_becomes_friendly_media_error(monkeypatch, tmp_path):
    media = Media()
    monkeypatch.setattr(media, "require", lambda: None)
    media.ffprobe = "ffprobe.exe"
    def timeout(*args, **kwargs):
        assert "-count_packets" in args[0]
        assert "-count_frames" not in args[0]
        raise subprocess.TimeoutExpired(args[0], 5)
    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(MediaError, match="ocupado"):
        media.decoded_duration(tmp_path / "segment.mkv", 30)


def test_closed_segments_are_preferred_over_live_probe(tmp_path, monkeypatch):
    engine = CaptureEngine(Media())
    engine.settings = Settings(fps=30)
    engine.session = tmp_path
    first = tmp_path / "frame-000000000.mkv"
    second = tmp_path / "frame-000000001.mkv"
    first.write_bytes(b"complete-0")
    second.write_bytes(b"complete-1")
    monkeypatch.setattr(engine, "_segments", lambda: [
        (first, 0.0, 2.0), (second, 2.0, 4.0),
    ])
    monkeypatch.setattr(engine.media, "decoded_duration", lambda *args: pytest.fail("No live probing needed"))
    result = engine._freeze_replay(.5, 3.7, tmp_path)
    assert len(result) == 2
    assert (tmp_path / "part0.mkv").read_bytes() == b"complete-0"
    assert (tmp_path / "part1.mkv").read_bytes() == b"complete-1"
    engine.pool.shutdown(wait=True)


def test_probe_invalid_tail_is_controlled_error(tmp_path):
    media = Media()
    if not media.ffprobe:
        pytest.skip("ffprobe unavailable")
    p = tmp_path / "part0.mkv"
    p.write_bytes(b"not a valid matroska file")
    with pytest.raises(MediaError):
        media.decoded_duration(p, 30)


def test_thumbnail_is_created_atomically(tmp_path):
    media = Media()
    if not (media.ffprobe and media.ffmpeg):
        pytest.skip("ffmpeg not installed")
    video = tmp_path / "clip.mp4"
    media.run(["-y", "-f", "lavfi", "-i", "color=c=blue:s=160x90:r=30", "-t", "2", "-c:v", "libx264", str(video)], timeout=30)
    image = tmp_path / "thumbnail.png"
    media.thumbnail(video, image)
    assert image.stat().st_size > 100
    assert not (tmp_path / "thumbnail.partial.png").exists()
