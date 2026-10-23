import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import json
import pytest
from duckcapture.media import Media, EditPart, MediaError
from duckcapture.capture import CaptureEngine
from duckcapture.config import Settings
from duckcapture.hud import write_hud, preset, escape
from duckcapture.windows import parse_hotkey


@pytest.fixture
def media():
    media = Media()
    media.require()
    return media


@pytest.fixture
def source(media, tmp_path):
    path = tmp_path / "vídeo d'entrada.mp4"
    media.run(
        [
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=320x180:rate=30",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000",
            "-t",
            "4",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-threads",
            "2",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(path),
        ]
    )
    return path


def test_editor_trims_splits_joins_speed_volume_text_and_preserves_source(
    media, source, tmp_path
):
    before = source.read_bytes()
    parts = [
        EditPart(
            str(source), 0.5, 1.5, 2, 0.5, "Olá {Users} \\ teste", "Preto e branco", 1.2
        ),
        EditPart(str(source), 2, 3, 1, 0),
    ]
    output = media.export(parts, tmp_path / "resultado.mp4", fps=30)
    info = media.probe(output)
    assert abs(info.duration - 1.5) < 0.12
    assert info.width == 320 and info.height == 180 and info.audio
    assert source.read_bytes() == before
    with pytest.raises(MediaError):
        media.export(parts, output)


def test_quarter_speed_silent_video_and_sticker(media, tmp_path):
    from PIL import Image

    source = tmp_path / "silent.mp4"
    media.run(
        [
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=160x90:r=30",
            "-t",
            "1",
            "-c:v",
            "libx264",
            "-threads",
            "2",
            str(source),
        ]
    )
    sticker = tmp_path / "sticker.png"
    Image.new("RGBA", (30, 30), "yellow").save(sticker)
    output = media.export(
        [EditPart(str(source), 0, 0.5, 0.25, 1, sticker=str(sticker))],
        tmp_path / "slow.mp4",
    )
    info = media.probe(output)
    assert abs(info.duration - 2) < 0.15
    assert info.audio


def test_replay_exports_requested_last_seconds_with_real_ffmpeg(media, tmp_path):
    engine = CaptureEngine(media)
    engine.settings = Settings(
        duration=15,
        fps=30,
        quality="Equilibrado",
        clips_dir=str(tmp_path / "clips"),
        hud_enabled=True,
        hud=preset("Minimal"),
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
            "testsrc2=size=320x180:rate=30",
            "-t",
            "8",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-threads",
            "2",
            "-g",
            "60",
            "-bf",
            "0",
            "-force_key_frames",
            "expr:gte(t,n_forced*2)",
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
            str(engine.session / "frame-%09d.mkv"),
        ]
    )
    engine.settings.clip_folder()
    output = engine._save_clip(2, 7, [], engine.settings, engine.session, 0, None)
    assert abs(media.probe(output).duration - 5) < 0.1
    assert json.loads(output.with_suffix(".json").read_text())["duration"] == 5
    assert engine.pending == 0
    engine.shutdown()


def test_hud_burns_real_keys_and_images(media, tmp_path):
    ass = tmp_path / "hud.ass"
    write_hud(
        ass,
        [dict(item,accent_color='#ffdf58') for item in preset()],
        [dict(t=0, keys=["W"], buttons=["L"], cursor=[0.5, 0.5], click=True, cps=1)],
        960,
        540,
        1,
        30,
    )
    assert "W" in ass.read_text(encoding="utf-8-sig")
    out = tmp_path / "hud.mp4"
    media.run(
        [
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=960x540:r=30",
            "-t",
            "1",
            "-vf",
            "subtitles=hud.ass",
            "-c:v",
            "libx264",
            "-threads",
            "2",
            str(out),
        ],
        cwd=tmp_path,
    )
    shot = tmp_path / "frame.png"
    media.run(["-y", "-i", str(out), "-frames:v", "1", str(shot)])
    from PIL import Image
    import numpy as np

    pixels = np.asarray(Image.open(shot).convert("RGB"))
    assert (
        (pixels[:, :, 0] > 170) & (pixels[:, :, 1] > 130) & (pixels[:, :, 2] < 150)
    ).sum() > 50


def test_constraints_and_safe_hotkeys(media, source, tmp_path):
    with pytest.raises(MediaError):
        media.export([EditPart(str(source), 3, 2)], tmp_path / "invalid.mp4")
    assert parse_hotkey("Ctrl+Shift+F8")[1] == 0x77
    assert parse_hotkey("F9")[1] == 0x78
    with pytest.raises(ValueError):
        parse_hotkey("Alt+F99")
    assert "{" not in escape("{\\pos(0,0)}")


def test_auto_encoder_checks_actual_size_quality_and_fps_before_fallback(monkeypatch):
    from duckcapture.media import Media, MediaError

    media = Media()
    calls = []

    def probe(args, **kwargs):
        calls.append(args)
        if args[args.index("-c:v") + 1] != "libx264":
            raise MediaError("GPU incompatível com o perfil")

    monkeypatch.setattr(media, "run", probe)
    assert media.encoder("Automático", (1920, 1080), "Full", 60) == "libx264"
    assert len(calls) == 4
    assert all("color=s=1920x1080:r=60" in call for call in calls)
    assert "16" in calls[-1] and "120" in calls[-1]
    calls.clear()
    assert media.encoder("Automático", (1920, 1080), "Full", 60) == "libx264"
    assert not calls  # Identical configurations can reuse the successful probe.
    assert media.encoder("Automático", (2560, 1440), "Full", 60) == "libx264"
    assert len(calls) == 4
