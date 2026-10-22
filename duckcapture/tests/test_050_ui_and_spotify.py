"""Interaction regression checks for the new editor, fold and Spotify bridge."""
import asyncio
from pathlib import Path
from types import SimpleNamespace
import wave
import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtWidgets import QApplication, QLabel, QFrame
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
from duckcapture.config import Settings
from duckcapture.app import MainWindow
from duckcapture.color_picker import ColorDialog
from duckcapture.fold_hover import fold_transform, add_fold_hover
from duckcapture.rounded import RoundScrollBar
from duckcapture.spotify_desktop import query_session

if not QApplication.instance():
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
APP = QApplication.instance() or QApplication([])


def test_pointed_corner_deforms_and_reduced_motion_is_identity():
    APP.setProperty('duckMotion', True)
    rect = QRectF(0, 0, 210, 160)
    for corner, opposite in [(rect.topLeft(), rect.bottomRight()), (rect.topRight(), rect.bottomLeft()), (rect.bottomRight(), rect.topLeft()), (rect.bottomLeft(), rect.topRight())]:
        transform = fold_transform(rect, corner, 1)
        assert not transform.isIdentity()
        assert (transform.map(corner)-corner).manhattanLength() > (transform.map(opposite)-opposite).manhattanLength()*2
        assert rect.contains(transform.map(corner))
    APP.setProperty('duckMotion', False)
    assert fold_transform(rect, QPointF(1, 1), 1).isIdentity()
    APP.setProperty('duckMotion', True)


def test_fold_changes_actual_widget_pixels_without_moving_click_target():
    widget = QFrame()
    widget.setStyleSheet('background: #283242; border: 2px solid white; border-radius:16px;')
    widget.resize(210, 160)
    widget.show()
    control = add_fold_hover(widget)
    APP.processEvents()
    control.reset()
    before = widget.grab().toImage()
    control.pointer = QPointF(2, 2)
    control.on_opacity(1.)
    after = widget.grab().toImage()
    assert before != after
    assert widget.size().width() == 210
    widget.close()


def test_rounded_color_input_validation_and_cancel():
    picker = ColorDialog(QColor('#cdbdff'))
    picker.show()
    APP.processEvents()
    assert picker.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    picker.hex_edited('#ZZZZZZ')
    assert not picker.confirm.isEnabled()
    picker.hex_edited('#123abc')
    assert picker.color.name() == '#123abc' and picker.confirm.isEnabled()
    picker.reject()
    assert picker.result() == 0


def test_navigation_interrupts_fades_and_editor_rejects_inverted_trim(tmp_path, monkeypatch):
    monkeypatch.setenv('DUCKCAPTURE_DATA', str(tmp_path / 'data'))
    window = MainWindow(Settings(clips_dir=str(tmp_path/'clips'), music_dir=str(tmp_path/'music')))
    window.show()
    try:
        for index in [1, 5, 6, 0, 1, 0]:
            window.navigate(index)
            APP.processEvents()
        QTest.qWait(450)
        overlays = window.stack.findChildren(QLabel, options=Qt.FindChildOption.FindDirectChildrenOnly)
        assert not any(overlay.isVisible() for overlay in overlays)
        assert isinstance(window.stack.currentWidget().verticalScrollBar(), RoundScrollBar)
        from duckcapture.media import EditPart
        part = EditPart(str(tmp_path/'fixture.mp4'), 2, 7)
        window.editor.parts = [part]
        window.editor.durations[part.path] = 10
        window.editor.render()
        window.editor.start.setValue(8)
        window.editor.end.setValue(3)
        window.editor.commit()
        assert (part.start, part.end) == (2, 7)
        window.editor.trimmed(3, 6)
        assert (part.start, part.end) == (3, 6)
        window.editor.revert()
        assert (window.editor.parts[0].start, window.editor.parts[0].end) == (2, 7)
    finally:
        window.close()
        APP.processEvents()


def test_spotify_targets_only_official_desktop_and_honors_controls():
    calls = []
    class Session:
        source_app_user_model_id = 'Spotify.exe'
        async def try_get_media_properties_async(self):
            return SimpleNamespace(title='Faixa de teste', artist='Artista')
        async def try_toggle_play_pause_async(self):
            calls.append('toggle')
            return True
        def get_playback_info(self):
            return SimpleNamespace(playback_status=4, controls=SimpleNamespace(is_play_pause_toggle_enabled=True, is_next_enabled=False, is_previous_enabled=True))
    browser = SimpleNamespace(source_app_user_model_id='chrome.exe')
    manager = SimpleNamespace(get_sessions=lambda: [browser, Session()])
    result = asyncio.run(query_session(manager, 'toggle'))
    assert calls == ['toggle']
    assert result['playing'] and result['title'] == 'Faixa de teste'
    assert result['toggle'] and not result['next']
    assert not asyncio.run(query_session(SimpleNamespace(get_sessions=lambda: [browser])))['connected']


def test_chime_is_longer_stereo_and_has_headroom():
    with wave.open(str(Path(__file__).resolve().parents[1]/'duckcapture/assets/clip.wav'), 'rb') as source:
        assert source.getnchannels() == 2
        assert 1 <= source.getnframes()/source.getframerate() <= 1.2
        samples = np.frombuffer(source.readframes(source.getnframes()), dtype='<i2').astype(float)/32768
    assert .8 < np.max(np.abs(samples)) < .95
    assert .1 < np.sqrt(np.mean(samples**2)) < .4
    assert abs(samples[0]) < .001 and abs(samples[-1]) < .001
