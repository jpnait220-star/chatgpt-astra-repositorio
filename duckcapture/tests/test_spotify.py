"""Spotify URL restrictions and minimal native-browser lifetime."""
import pytest
from duckcapture.spotify import embed_url, browser_url


@pytest.mark.parametrize("value", [
    "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=123",
    "https://open.spotify.com/intl-pt/playlist/37i9dQZF1DXcBWIGoYBM5M/",
    "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M",
])
def test_embed_helper_legacy(value):
    assert embed_url(value) == "https://open.spotify.com/embed/playlist/37i9dQZF1DXcBWIGoYBM5M?theme=0"


def test_spotify_browser_accepts_official_hosts():
    assert browser_url("spotify.com") == "https://spotify.com"
    assert browser_url("https://open.spotify.com/intl-pt/") == "https://open.spotify.com/intl-pt/"
    assert browser_url("") == "https://open.spotify.com/intl-pt/"
    assert browser_url("spotify:track:37i9dQZF1DXcBWIGoYBM5M") == "https://open.spotify.com/track/37i9dQZF1DXcBWIGoYBM5M"


@pytest.mark.parametrize("value", [
    "https://google.com",
    "http://open.spotify.com",
    "https://open.spotify.com.evil.example",
    "file:///etc/passwd",
])
def test_spotify_browser_rejects_other_sites(value):
    with pytest.raises(ValueError):
        browser_url(value)


def test_browser_lifecycle_without_network(monkeypatch, tmp_path):
    monkeypatch.setenv("DUCKCAPTURE_DATA", str(tmp_path))
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    if not QApplication.instance():
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication.instance() or QApplication([])
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from duckcapture.spotify import SpotifyPanel
    requested = []
    monkeypatch.setattr(QWebEngineView, "setUrl", lambda self, value: requested.append(value.toString()))
    panel = SpotifyPanel()
    assert panel.view is None
    panel.load("https://open.spotify.com/track/37i9dQZF1DXcBWIGoYBM5M")
    assert requested == ["https://open.spotify.com/embed/track/37i9dQZF1DXcBWIGoYBM5M?theme=0"]
    assert panel.load_timeout.isActive()
    panel.browser_timed_out()
    assert panel.view.isHidden()
    assert "não respondeu" in panel.browser_message.text()
    panel.shutdown()
    from PySide6.QtCore import QCoreApplication, QEvent
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()
    assert panel.view is None
