import pytest
from duckcapture.spotify import embed_url


@pytest.mark.parametrize(
    "url",
    [
        "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=123",
        "https://open.spotify.com/intl-pt/playlist/37i9dQZF1DXcBWIGoYBM5M/",
        "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M",
        "https://open.spotify.com/embed/playlist/37i9dQZF1DXcBWIGoYBM5M?theme=0",
    ],
)
def test_canonical_official_embed(url):
    assert (
        embed_url(url)
        == "https://open.spotify.com/embed/playlist/37i9dQZF1DXcBWIGoYBM5M?theme=0"
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
        "https://open.spotify.com.evil.example/playlist/37i9dQZF1DXcBWIGoYBM5M",
        "https://open.spotify.com@evil.example/playlist/37i9dQZF1DXcBWIGoYBM5M",
        "file:///playlist/37i9dQZF1DXcBWIGoYBM5M",
        "https://open.spotify.com/playlist/invalid",
    ],
)
def test_invalid_playlist_links(url):
    with pytest.raises(ValueError, match="open.spotify.com"):
        embed_url(url)


def test_embedded_player_lifecycle_without_external_browser(monkeypatch):
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt, QUrl, QEvent
    from PySide6.QtTest import QTest

    if not QApplication.instance():
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication.instance() or QApplication([])
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from duckcapture.spotify import SpotifyPanel

    requested = []
    monkeypatch.setattr(
        QWebEngineView, "setUrl", lambda self, url: requested.append(url.toString())
    )
    panel = SpotifyPanel()
    assert panel.view is None  # No browser is created at app startup.
    panel.load("spotify:playlist:37i9dQZF1DXcBWIGoYBM5M")
    assert requested == [embed_url("spotify:playlist:37i9dQZF1DXcBWIGoYBM5M")]
    # Test Chromium rendering with controlled HTML, without a Spotify request.
    # Allow the setHtml data navigation only in this test's page subclass.
    monkeypatch.setattr(
        type(panel.view.page()), "acceptNavigationRequest", lambda *args: True
    )
    panel.view.setHtml(
        '<html><body><p id="check">player interno</p></body></html>',
        QUrl("https://open.spotify.com/"),
    )
    loaded = []
    panel.view.loadFinished.connect(loaded.append)
    for _ in range(150):
        if loaded:
            break
        QTest.qWait(20)
    assert loaded and loaded[-1]
    result = []
    panel.view.page().runJavaScript(
        'document.querySelector("#check").textContent', result.append
    )
    for _ in range(100):
        if result:
            break
        QTest.qWait(20)
    assert result == ["player interno"]
    panel.close_player()
    app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()
    assert panel.view is None and panel.profile is None
    panel.close()
