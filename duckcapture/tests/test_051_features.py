import json
import threading
import time
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import pytest
from PySide6.QtCore import QEvent, QUrl, QCoreApplication
from PySide6.QtGui import QImage, QColor
from PySide6.QtMultimedia import QMediaPlayer, QVideoFrame
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton, QComboBox, QWidget, QVBoxLayout

from duckcapture.clip_sound import mix_clip_chime
from duckcapture.fold_hover import install_interactive_motion
from duckcapture.sharing import ShareDialog, valid_clip_url, MAX_UPLOAD
from duckcapture.wallpaper import VideoBackground

APP = QApplication.instance() or QApplication([])


def wait_until(predicate, timeout=5000):
    end = time.monotonic() + timeout / 1000
    while not predicate() and time.monotonic() < end:
        QTest.qWait(20)
    assert predicate()


@pytest.mark.parametrize('existing', [True, False])
def test_chime_is_in_tail_and_preserves_duration_and_game_audio(tmp_path, existing):
    path = tmp_path / 'audio.wav'
    original = np.full((48000 * 3, 2), 12000, dtype='<i2')
    if existing:
        with wave.open(str(path), 'wb') as stream:
            stream.setparams((2, 2, 48000, 0, 'NONE', 'not compressed'))
            stream.writeframes(original.tobytes())
    mix_clip_chime(path, 3, .82)
    with wave.open(str(path), 'rb') as stream:
        assert stream.getnframes() == 144000
        data = np.frombuffer(stream.readframes(144000), dtype='<i2').reshape(-1, 2)
    assert np.array_equal(data[:48000], original[:48000] if existing else np.zeros_like(original[:48000]))
    assert np.std(data[96000:136000]) > 500
    assert np.abs(data.astype(np.int32)).max() <= 32000
    assert np.all(data[-3000:] == (12000 if existing else 0))


def test_very_short_replay_still_has_faded_chime(tmp_path):
    path = tmp_path / 'short.wav'
    mix_clip_chime(path, .05, 1)
    with wave.open(str(path), 'rb') as stream:
        samples = np.frombuffer(stream.readframes(stream.getnframes()), dtype='<i2')
        assert stream.getnframes() == 2400
    assert samples.any() and not samples[-400:].any()


def test_dynamic_clickable_controls_return_slowly_without_changing_geometry():
    install_interactive_motion()
    APP.setProperty('duckMotion', True)
    window = QWidget()
    layout = QVBoxLayout(window)
    controls = [QPushButton('Novo botão'), QComboBox()]
    controls[1].addItems(['720p', '1080p'])
    for item in controls:
        layout.addWidget(item)
    window.show()
    APP.processEvents()
    for item in controls:
        controller = item._duck_fold_overlay
        geometry = item.geometry()
        controller.switch(True)
        QTest.qWait(240)
        controller.switch(False)
        QTest.qWait(250)
        assert controller.opacity > .1
        QTest.qWait(450)
        assert controller.opacity == 0
        assert item.geometry() == geometry
    window.close()


def test_wallpaper_accepts_frames_only_when_active_and_mutes_audio():
    background = VideoBackground()
    background.resize(400, 260)
    background.show()
    background.set_blocked(False)
    image = QImage(160, 90, QImage.Format.Format_RGB32)
    image.fill(QColor('red'))
    background.receive_frame(QVideoFrame(image))
    assert not background.frame.isNull()
    last = background.frame
    background.set_blocked(True)
    image.fill(QColor('blue'))
    background.receive_frame(QVideoFrame(image))
    assert background.frame == last
    assert background.audio.isMuted()
    assert background.player.loops() == QMediaPlayer.Loops.Infinite
    background.set_video('')
    assert background.frame.isNull() and background.player.source() == QUrl()
    background.close()


@pytest.fixture
def upload_server(monkeypatch):
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            requests.append(self.rfile.read(int(self.headers['Content-Length'])))
            body = self.server.response
            self.send_response(200)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *_):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.response = b'https://files.catbox.moe/abc123.mp4'
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setattr('duckcapture.sharing.UPLOAD_URL', f'http://127.0.0.1:{server.server_port}/api')
    yield server, requests
    server.shutdown()
    server.server_close()
    thread.join()


def test_sharing_is_explicit_streamed_and_reuses_link(tmp_path, monkeypatch, upload_server):
    monkeypatch.setenv('DUCKCAPTURE_DATA', str(tmp_path / 'data'))
    path = tmp_path / 'private filename.mp4'
    path.write_bytes(b'example synthetic media bytes')
    server, requests = upload_server
    dialog = ShareDialog(path)
    dialog.show()
    QTest.qWait(50)
    assert requests == []  # Opening the dialog must never publish a clip.
    dialog.start()
    wait_until(lambda: dialog.reply is None)
    assert len(requests) == 1
    assert b'name="reqtype"' in requests[0] and b'fileupload' in requests[0]
    assert b'name="fileToUpload"; filename="DuckCapture.mp4"' in requests[0]
    assert path.read_bytes() in requests[0] and b'private filename' not in requests[0]
    assert valid_clip_url(dialog.link.text())
    dialog.copy_link()
    assert QApplication.clipboard().text() == dialog.link.text()
    assert json.loads((tmp_path / 'data/shared-clips.json').read_text())
    dialog.reject()
    repeated = ShareDialog(path)
    assert repeated.link.text() == dialog.link.text()
    assert not repeated.send.isEnabled()
    repeated.reject()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_upload_rejects_oversize_and_untrusted_response(tmp_path, monkeypatch, upload_server):
    monkeypatch.setenv('DUCKCAPTURE_DATA', str(tmp_path / 'data'))
    path = tmp_path / 'large.mp4'
    with path.open('wb') as stream:
        stream.truncate(MAX_UPLOAD + 1)
    server, requests = upload_server
    dialog = ShareDialog(path)
    dialog.start()
    assert not requests and '200 MB' in dialog.status.text()
    path.write_bytes(b'synthetic')
    server.response = b'https://files.catbox.moe.evil.example/a.mp4'
    dialog.start()
    wait_until(lambda: dialog.reply is None)
    assert not dialog.link.text() and not dialog.copy.isEnabled()
    assert 'Não foi possível' in dialog.status.text()
    dialog.reject()


def test_upload_cancel_aborts_request(tmp_path, monkeypatch, upload_server):
    monkeypatch.setenv('DUCKCAPTURE_DATA', str(tmp_path / 'data'))
    path = tmp_path / 'clip.mp4'
    path.write_bytes(b'synthetic')
    dialog = ShareDialog(path)
    dialog.start()
    dialog.reject()
    assert dialog.reply is None
    assert not dialog.idle.isActive() and not dialog.deadline.isActive()
