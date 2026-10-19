import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtMultimedia import QMediaPlayer
from duckcapture.config import Settings
from duckcapture.app import MainWindow
from duckcapture.hud_editor import HudItem

if not QApplication.instance():
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
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
    assert window.stack.count() == 7
    assert not window.engine.active
    assert window.library.count() == 1 and window.library.item(0).data(256) is None
    for i in range(7):
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
    QTest.qWait(250)
    window.grab().save(str(out / "duckcapture-inicio.png"))
    window.navigate(3)
    QTest.qWait(250)
    window.grab().save(str(out / "duckcapture-hud.png"))
    window.navigate(2)
    QTest.qWait(250)
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


def test_gallery_has_all_clips_and_searches_beyond_old_limit(tmp_path, monkeypatch):
    monkeypatch.setenv("DUCKCAPTURE_DATA", str(tmp_path / "data"))
    clips = tmp_path / "clips"
    clips.mkdir()
    # Listing fixture only; these files are never presented as playable clips.
    for i in range(125):
        (clips / f"Momento-{i:03d}.mp4").touch()
    (clips / "Print.png").touch()
    window = MainWindow(
        Settings(clips_dir=str(clips), music_dir=str(tmp_path / "music"))
    )
    try:
        assert window.gallery.list.count() == 126
        window.gallery.search.setText("Momento-124")
        visible = [
            item for item in window.gallery.items.values() if not item.isHidden()
        ]
        assert len(visible) == 1 and "124" in visible[0].text()
        window.gallery.search.clear()
        window.gallery.kind.setCurrentIndex(2)
        assert sum(not item.isHidden() for item in window.gallery.items.values()) == 1
        window.navigate(6)
        assert window.nav[6].isChecked()
        assert sum(button.isChecked() for button in window.nav.values()) == 1
    finally:
        window.close()
        APP.processEvents()


def test_capture_failure_stays_visible_after_stopped_and_can_be_copied(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("DUCKCAPTURE_DATA", str(tmp_path / "data"))
    window = MainWindow(
        Settings(clips_dir=str(tmp_path / "clips"), music_dir=str(tmp_path / "music"))
    )
    try:
        window.engine.error = "Nenhum quadro recebido."
        window.engine.events.put(("capture_error", window.engine.error))
        window.engine.events.put(("stopped", "Captura parada."))
        window.tick()
        assert "FALHA" in window.status_label.text()
        assert not window.capture_error.isHidden()
        assert "Nenhum quadro" in window.capture_error.text()
        assert window.start_button.isEnabled() and not window.clip_button.isEnabled()
        assert window.progress.value() == 0 and window.progress.maximum() > 0
        window.copy_capture_error()
        assert "Nenhum quadro recebido" in APP.clipboard().text()
        window.toggle_motion(False)
        assert Settings.load().motion is False and APP.property("duckMotion") is False
    finally:
        window.close()
        APP.processEvents()


def test_gallery_generates_thumbnail_and_opens_real_video(tmp_path, monkeypatch):
    from duckcapture.gallery import ClipViewer
    from duckcapture.media import Media

    monkeypatch.setenv("DUCKCAPTURE_DATA", str(tmp_path / "data"))
    clips = tmp_path / "clips"
    clips.mkdir()
    media = Media()
    path = clips / "teste.mp4"
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
            str(path),
        ]
    )
    window = MainWindow(
        Settings(clips_dir=str(clips), music_dir=str(tmp_path / "music"))
    )
    window.show()
    try:
        window.navigate(6)
        for _ in range(150):
            if window.gallery.thumbnails:
                break
            QTest.qWait(20)
        assert window.gallery.thumbnails
        assert any((tmp_path / "data/thumbnails").glob("*.png"))
        viewer = ClipViewer(str(path), window)
        viewer.show()
        for _ in range(100):
            if viewer.player.hasVideo():
                break
            QTest.qWait(20)
        assert viewer.player.hasVideo()
        viewer.accept()
        assert viewer.player.playbackState() == QMediaPlayer.PlaybackState.StoppedState
    finally:
        window.close()
        APP.processEvents()


def test_visual_picker_selects_window_and_releases_thumbnails():
    from duckcapture.window_picker import WindowPicker

    previews = []

    class Thumbnail:
        def __init__(self, destination, source):
            self.source = source
            self.closed = False
            previews.append(self)

        def update(self, *args):
            pass

        def close(self):
            self.closed = True

    picker = WindowPicker(
        windows=[(i, f"Janela {i}") for i in range(8)], thumbnail_factory=Thumbnail
    )
    picker.show()
    APP.processEvents()
    assert len(picker.previews) == 6
    picker.turn(1)
    assert all(p.closed for p in previews[:6])
    assert len(picker.previews) == 2
    picker.choose(7, "Janela 7")
    assert picker.selected == (7, "Janela 7")
    assert all(p.closed for p in previews)
    APP.processEvents()


def test_saved_sounds_and_icon_expansion(tmp_path, monkeypatch):
    from duckcapture import sounds
    from duckcapture.visuals import ExpandButton

    calls = []

    class Effect:
        def __init__(self, parent):
            pass

        def setVolume(self, value):
            assert 0 < value < 0.5

        def setSource(self, url):
            self.name = Path(url.toLocalFile()).name
            assert Path(url.toLocalFile()).is_file()

        def stop(self):
            pass

        def play(self):
            calls.append(self.name)

    monkeypatch.setattr(sounds, "QSoundEffect", Effect)
    settings = Settings()
    player = sounds.CaptureSounds(None, settings)
    player.saved("Clipe.mp4")
    player.saved("Print.png")
    settings.notification_sounds = False
    player.saved("silenciado.mp4")
    assert calls == ["clip.wav", "print.wav"]
    APP.setProperty("duckMotion", True)
    control = ExpandButton("HUD", "hud", 160)
    control.show()
    QTest.qWait(20)
    assert control.width() == 50 and not control.icon().isNull()
    QTest.mouseClick(control, Qt.MouseButton.LeftButton)
    QTest.qWait(250)
    assert control.isChecked() and control.width() == 160
    control.close()
