import gc
import time
from types import SimpleNamespace
import numpy as np
import pytest
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtGui import QImage, QColor
from PySide6.QtMultimedia import QVideoFrame
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from duckcapture.media import Media
from duckcapture.media_jobs import MediaJob, share_plan
from duckcapture.capture import CaptureEngine
from duckcapture.hud import write_hud
from duckcapture.hud_art import artwork
from duckcapture.wallpaper import VideoBackground

APP = QApplication.instance() or QApplication([])


def finish(job):
    errors = []
    job.failed.connect(errors.append)
    job.start()
    deadline = time.monotonic() + 60
    while job.isRunning() and time.monotonic() < deadline:
        QTest.qWait(20)
    assert not job.isRunning()
    APP.processEvents()
    assert not errors, errors
    return job.result


def test_owned_native_frames_are_retained_without_full_resolution_copy():
    Frame = type("Frame", (), {"__module__": "windows_capture"})
    owner = np.full((1080, 1920, 4), 77, dtype=np.uint8)
    frame = Frame()
    frame.frame_buffer = owner.view()
    retained = CaptureEngine._retain_frame(frame)
    assert retained is frame.frame_buffer
    del owner, frame
    gc.collect()
    assert retained[1000, 1800, 2] == 77
    external = np.zeros((4, 4, 4), dtype=np.uint8)
    copied = CaptureEngine._retain_frame(SimpleNamespace(frame_buffer=external))
    external[:] = 255
    assert not copied.any()


def test_yuv_pipe_uses_62_percent_less_data_and_preserves_colors():
    cv2 = pytest.importorskip("cv2")
    engine = CaptureEngine(Media())
    engine.pipe_format = "yuv420p"
    source = np.full((180, 320, 4), [18, 100, 220, 255], dtype=np.uint8)
    payload = engine._frame_payload(source, 320, 180, 320, 180)
    assert len(payload) == 320 * 180 * 3 // 2
    assert len(payload) / (320 * 180 * 4) == 0.375
    restored = cv2.cvtColor(
        np.frombuffer(payload, dtype=np.uint8).reshape(270, 320),
        cv2.COLOR_YUV2BGRA_I420,
    )
    assert np.abs(restored.astype(float) - source).mean() < 2
    engine.shutdown()


def test_large_share_copy_fits_budget_preserves_duration_audio_original(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("DUCKCAPTURE_DATA", str(tmp_path / "data"))
    media = Media()
    source = tmp_path / "original.mp4"
    media.run(
        [
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=s=640x360:r=30",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=550:sample_rate=48000",
            "-t",
            "3",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "0",
            "-threads",
            "2",
            "-c:a",
            "aac",
            source,
        ]
    )
    before = source.read_bytes()
    limit = 150000
    assert len(before) > limit
    job = MediaJob(source, "share", limit=limit)
    output = finish(job)
    from pathlib import Path

    assert 0 < Path(output).stat().st_size <= limit
    info = media.probe(output)
    assert info.audio and abs(info.duration - 3) < 0.1 and abs(info.fps - 30) < 0.1
    assert source.read_bytes() == before and Path(output) != source


def test_wallpaper_cache_preserves_display_detail_and_caps_decode_rate(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("DUCKCAPTURE_DATA", str(tmp_path / "data"))
    media = Media()
    source = tmp_path / "large.mp4"
    media.run(
        [
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=3840x2160:r=30",
            "-t",
            "0.5",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-threads",
            "2",
            source,
        ]
    )
    result = finish(MediaJob(source, "wallpaper", size=(1920, 1080)))
    info = media.probe(result)
    assert (info.width, info.height) == (1920, 1080) and info.fps == 24
    assert finish(MediaJob(source, "wallpaper", size=(1920, 1080))) == result


def test_wallpaper_30fps_delivery_is_not_halved_to_15fps():
    background = VideoBackground()
    background.show()
    background.set_blocked(False)
    image = QImage(1920, 1080, QImage.Format.Format_RGB32)
    image.fill(QColor("red"))
    for i in range(60):
        frame = QVideoFrame(image)
        frame.setStartTime(round(i / 30 * 1_000_000))
        background.receive_frame(frame)
    assert 47 <= background.pacer.accepted <= 49
    assert background.frame.width() == 1920
    background.shutdown()
    background.close()


def test_hud_uses_actual_music_state_custom_colors_and_compacts_identical_input(
    tmp_path,
):
    model = dict(
        kind="music", x=0.05, y=0.05, scale=1, opacity=1, accent_color="#ff3366"
    )
    state = dict(
        music="Minha música",
        music_artist="Artista real",
        music_position=60,
        music_duration=120,
        music_playing=True,
    )
    parts = artwork(model, state)
    assert any(p.get("text") == "Minha música" for p in parts)
    assert any(p.get("text") == "Artista real" for p in parts)
    assert any(p.get("text") == "01:00 / 02:00" for p in parts)
    assert any(p["color"] == "#ff3366" for p in parts)
    mouse = artwork(dict(kind="mouse", accent_color="#ff3366"), dict(buttons=["L"]))
    assert any(any(command[0] == "C" for command in p.get("path", [])) for p in mouse)
    assert any(p["color"] == "#ff3366" for p in mouse)
    path = tmp_path / "keys.ass"
    write_hud(
        path,
        [dict(kind="keyboard", x=0.1, y=0.1, scale=1)],
        [
            dict(t=i / 30, keys=["W"], cursor=[i / 300, 0], music="track")
            for i in range(300)
        ],
        1280,
        720,
        10,
        60,
    )
    assert path.read_text(encoding="utf-8-sig").count("Dialogue:") < 20


def test_share_plan_covers_all_gpu_vendors_without_changing_source_fps():
    info = SimpleNamespace(duration=120, fps=60, audio=True)
    bitrate, fps, height = share_plan(info, 200_000_000)
    assert 10000 < bitrate < 14000 and fps == 60 and height == 1080


def test_cancel_preparation_cleans_up_without_publishing(tmp_path, monkeypatch):
    monkeypatch.setenv("DUCKCAPTURE_DATA", str(tmp_path / "data"))
    media = Media()
    source = tmp_path / "video.mp4"
    media.run(
        [
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=s=320x180:r=30",
            "-t",
            "1",
            "-c:v",
            "libx264",
            "-threads",
            "2",
            source,
        ]
    )
    job = MediaJob(source, "share", limit=100000)
    published = []
    job.succeeded.connect(published.append)
    job.cancel()
    job.start()
    assert job.wait(5000)
    APP.processEvents()
    assert not published and not job.result
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_hud_timer_advances_even_without_input_samples(tmp_path):
    path = tmp_path / "timer.ass"
    write_hud(path, [dict(kind="timer", x=0.1, y=0.1)], [], 1280, 720, 3.5, 60)
    content = path.read_text(encoding="utf-8-sig")
    assert all(f"00:0{second}" in content for second in range(4))
    assert "0:00:03.00,0:00:03.50" in content


def test_spotify_timeline_failure_keeps_track_and_controls():
    import asyncio
    from duckcapture.spotify_desktop import query_session

    class Session:
        source_app_user_model_id = "Spotify.exe"

        async def try_get_media_properties_async(self):
            return SimpleNamespace(title="Minha música", artist="Artista")

        def get_playback_info(self):
            return SimpleNamespace(
                playback_status=4,
                controls=SimpleNamespace(
                    is_play_pause_toggle_enabled=True,
                    is_next_enabled=True,
                    is_previous_enabled=True,
                ),
            )

        def get_timeline_properties(self):
            raise OSError("timeline changing")

    result = asyncio.run(
        query_session(SimpleNamespace(get_sessions=lambda: [Session()]))
    )
    assert result["connected"] and result["playing"] and result["toggle"]
    assert result["title"] == "Minha música" and result["duration"] == 0


def test_music_card_hover_paints_and_returns_slowly():
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QPainter
    from PySide6.QtWidgets import QGraphicsScene
    from duckcapture.hud_editor import HudItem

    item = HudItem(dict(kind="music", x=0, y=0), lambda: None)
    scene = QGraphicsScene()
    scene.addItem(item)

    def render():
        image = QImage(300, 100, QImage.Format.Format_ARGB32)
        image.fill(QColor("black"))
        p = QPainter(image)
        try:
            item.paint(p, None, None)
        finally:
            p.end()
        return image

    flat = render()
    item._fold_pointer = QPointF(0, 0)
    item._fold_changed(1)
    assert render() != flat
    APP.setProperty("duckMotion", True)
    item._fold_to(0)
    assert item._fold_anim.duration() == 650
    item._fold_anim.stop()
    scene.clear()
    scene.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
