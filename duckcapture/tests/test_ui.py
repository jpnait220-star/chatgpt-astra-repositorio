import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtMultimedia import QMediaPlayer
from duckcapture.config import Settings
from duckcapture.app import MainWindow
from duckcapture.hud_editor import HudItem

APP = QApplication.instance() or QApplication([])


def test_application_navigation_hud_persistence_and_no_fake_capture(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("DUCKCAPTURE_DATA", str(tmp_path / "data"))
    settings = Settings(
        clips_dir=str(tmp_path / "clips"), music_dir=str(tmp_path / "music")
    )
    window = MainWindow(settings)
    window.resize(1360, 930)
    window.show()
    APP.processEvents()
    assert window.stack.count() == 6
    assert not window.engine.active
    assert window.library.count() == 1 and window.library.item(0).data(256) is None
    for i in range(6):
        window.navigate(i)
        APP.processEvents()
    window.hud.kind.setCurrentIndex(window.hud.kind.findData("timer"))
    window.hud.add()
    item = next(
        i
        for i in window.hud.scene.items()
        if isinstance(i, HudItem) and i.model["kind"] == "timer"
    )
    item.setPos(300, 100)
    window.save_settings()
    assert abs(Settings.load().hud[-1]["x"] - 300 / 960) < 0.001
    window.settings.clip_key = "Ctrl+F8"
    window.settings.screenshot_key = "Ctrl+F9"
    window.save_settings()
    window.refresh_library(True)
    assert Settings.load().clip_key == "Ctrl+F8"
    out = Path(__file__).resolve().parents[1] / "artifacts"
    out.mkdir(exist_ok=True)
    window.navigate(0)
    APP.processEvents()
    window.grab().save(str(out / "duckcapture-inicio.png"))
    window.navigate(3)
    APP.processEvents()
    window.grab().save(str(out / "duckcapture-hud.png"))
    window.navigate(2)
    APP.processEvents()
    window.grab().save(str(out / "duckcapture-editor.png"))
    window.close()
    APP.processEvents()


def test_editor_actions_and_music_folder(tmp_path, monkeypatch):
    from duckcapture.media import Media

    monkeypatch.setenv("DUCKCAPTURE_DATA", str(tmp_path / "data"))
    media = Media()
    source = tmp_path / "clip.mp4"
    media.run(
        [
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=160x90:r=30",
            "-t",
            "2",
            "-c:v",
            "libx264",
            "-threads",
            "2",
            str(source),
        ]
    )
    music = tmp_path / "music"
    music.mkdir()
    media.run(
        [
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440",
            "-t",
            "1",
            str(music / "minha-musica.wav"),
        ]
    )
    window = MainWindow(
        Settings(clips_dir=str(tmp_path / "clips"), music_dir=str(music))
    )
    window.editor.load(source)
    APP.processEvents()
    assert len(window.editor.parts) == 1
    for _ in range(100):
        if window.editor.player.mediaStatus() == QMediaPlayer.MediaStatus.LoadedMedia:
            break
        QTest.qWait(20)
    assert window.editor.player.hasVideo()
    window.editor.player.setPosition(1000)
    window.editor.split()
    assert len(window.editor.parts) == 2
    assert window.editor.parts[0].end == 1 and window.editor.parts[1].start == 1
    window.editor.revert()
    assert len(window.editor.parts) == 1
    window.editor.text.setText("Meu clipe")
    window.editor.commit()
    assert window.editor.parts[0].text == "Meu clipe"
    window.editor.revert()
    assert window.editor.parts[0].text == ""
    assert (
        window.music.list.count() == 1
        and window.music.paths[0].name == "minha-musica.wav"
    )
    window.music.spotify.setText("https://example.com/playlist/123")
    window.music.open_spotify()
    assert window.settings.spotify == "" and "open.spotify.com" in window.last_toast
    window.close()
    APP.processEvents()
