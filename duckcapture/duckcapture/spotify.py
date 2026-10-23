"""Spotify-only embedded browser. Site playback follows Spotify's licensing and DRM rules."""
from __future__ import annotations

import re
from urllib.parse import urlparse
from PySide6.QtCore import QUrl, Signal, Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame
from .widgets import label, button
from .fold_hover import add_fold_hover

START_URL = "https://open.spotify.com/intl-pt/"
ALLOWED_HOSTS = frozenset((
    "open.spotify.com", "spotify.com", "www.spotify.com",
    "accounts.spotify.com", "login.spotify.com", "auth.spotify.com", "spotify.link",
))


def embed_url(value):
    """Validate an official Spotify content link or URI for preview playback."""
    value = value.strip()
    uri = re.fullmatch(
        r"spotify:(playlist|track|album|artist|episode|show):([A-Za-z0-9]{22})", value
    )
    if uri:
        value = f"https://open.spotify.com/{uri[1]}/{uri[2]}"
    parsed = urlparse(value)
    match = re.fullmatch(
        r"/(?:intl-[a-z]{2}/)?(?:embed/)?(playlist|track|album|artist|episode|show)/([A-Za-z0-9]{22})/?",
        parsed.path,
    )
    if parsed.scheme != "https" or parsed.netloc != "open.spotify.com" or not match:
        raise ValueError("Use um link HTTPS de música, álbum ou playlist em open.spotify.com.")
    return f"https://open.spotify.com/embed/{match[1]}/{match[2]}?theme=0"


def browser_url(raw: str) -> str:
    """Accept only Spotify destinations; no arbitrary in-app browser sites."""
    value = raw.strip()
    if not value:
        return START_URL
    uri = re.fullmatch(
        r"spotify:(playlist|track|album|artist|episode|show):([A-Za-z0-9]{22})", value
    )
    if uri:
        value = f"https://open.spotify.com/{uri[1]}/{uri[2]}"
    elif not "://" in value:
        value = "https://" + value
    parsed = urlparse(value)
    if (
        parsed.scheme != "https" or
        (parsed.hostname or "").lower() not in ALLOWED_HOSTS or
        parsed.username or parsed.password or parsed.port or
        not parsed.hostname
    ):
        raise ValueError("Este navegador abre apenas endereços oficiais do Spotify (open.spotify.com ou spotify.com).")
    return value


class SpotifyDisc(QWidget):
    """A decorative disc shared with the local-player visual language.

    The official Spotify webpage owns playback; the disc never pretends it can
    bypass account requirements or DRM restrictions.
    """
    def __init__(self):
        super().__init__()
        self.setFixedSize(106, 106)
        self.setToolTip("Representação visual; controle a reprodução no Spotify abaixo")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        area = QRectF(4, 4, self.width()-8, self.height()-8)
        painter.setBrush(QColor("#07080a"))
        painter.setPen(QPen(QColor("#33363e"), 1))
        painter.drawEllipse(area)
        for offset in (11, 19, 27):
            painter.setPen(QPen(QColor("#262930"), 1))
            painter.drawEllipse(area.adjusted(offset, offset, -offset, -offset))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#e9edf2"))
        painter.drawEllipse(QRectF(34, 34, 38, 38))
        painter.setBrush(QColor("#060709"))
        painter.drawEllipse(QRectF(49, 49, 8, 8))
        painter.end()


class SpotifyPanel(QWidget):
    opened = Signal()
    trackChanged = Signal(str)

    def __init__(self):
        super().__init__()
        from .spotify_desktop import SpotifyDesktop
        from .visuals import icon
        self.view = self.profile = None
        self.url = ''
        self.desktop_state = {}
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(14)
        self.desktop = SpotifyDesktop(self)
        self.desktop.changed.connect(self.desktop_changed)
        self.desktop.busyChanged.connect(self.busy_changed)
        header = QFrame()
        header.setObjectName('card')
        body = QVBoxLayout(header)
        body.setContentsMargins(20, 18, 20, 18)
        record = QHBoxLayout()
        record.addWidget(SpotifyDisc())
        titles = QVBoxLayout()
        titles.addWidget(label('SPOTIFY / CONECTADO AO SEU PC', 'eyebrow'))
        self.disc_title = label('Sua música, no seu ritmo.', 'subheading', True)
        titles.addWidget(self.disc_title)
        self.artist = label('Conecte o aplicativo Spotify do Windows.', 'muted', True)
        titles.addWidget(self.artist)
        record.addLayout(titles, 1)
        body.addLayout(record)
        controls = QHBoxLayout()
        self.transport = {}
        for command, text, symbol in [('previous', 'Anterior', 'previous'), ('toggle', 'Reproduzir', 'play'), ('next', 'Próxima', 'next')]:
            control = button(text, lambda checked=False, cmd=command: self.command(cmd))
            control.setIcon(icon(symbol))
            control.setEnabled(False)
            self.transport[command] = control
            controls.addWidget(control)
        controls.addStretch()
        body.addLayout(controls)
        body.addWidget(label('O Spotify instalado toca a música; você controla por aqui. Funciona com conta gratuita e Premium, conforme as regras da sua conta.', 'tiny', True))
        self.layout_.addWidget(header)
        add_fold_hover(header)
        connection = QHBoxLayout()
        connection.addWidget(button('Abrir Spotify no PC', self.open_external, True))
        connection.addWidget(button('Conectar / atualizar', lambda: self.desktop.refresh()))
        self.layout_.addLayout(connection)
        self.message = label('Abra uma faixa no Spotify do Windows e clique em Conectar.', 'muted', True)
        self.layout_.addWidget(self.message)
        self.browser_message = label('Sem o Spotify instalado? Cole um link acima para abrir a prévia oficial.', 'tiny', True)
        self.layout_.addWidget(self.browser_message)
        from PySide6.QtCore import QTimer
        self.load_timeout = QTimer(self)
        self.load_timeout.setSingleShot(True)
        self.load_timeout.setInterval(18000)
        self.load_timeout.timeout.connect(self.browser_timed_out)

    def command(self, command):
        self.opened.emit()
        if self.view:
            self.view.page().setAudioMuted(True)
        self.desktop.refresh(command)

    def busy_changed(self, busy):
        for name, control in self.transport.items():
            control.setEnabled(not busy and bool(self.desktop_state.get(name, False)))

    def desktop_changed(self, state):
        import time
        self.desktop_updated_at = time.monotonic()
        from .visuals import icon
        self.desktop_state = state
        self.disc_title.setText(state.get('title', 'Conecte seu Spotify'))
        self.artist.setText(state.get('artist', 'Spotify para Windows'))
        self.message.setText(state.get('message', 'Reproduzindo no Spotify.' if state.get('playing') else 'Conectado. Use os controles acima.'))
        playing = state.get('playing', False)
        self.transport['toggle'].setText('Pausar' if playing else 'Reproduzir')
        self.transport['toggle'].setIcon(icon('pause' if playing else 'play'))
        self.busy_changed(False)
        self.trackChanged.emit(state.get('title', '') if playing else '')

    def open_external(self):
        from PySide6.QtGui import QDesktopServices
        if self.view:
            self.view.page().setAudioMuted(True)
        destination = 'spotify:'
        if self.url:
            match = re.search(r'/embed/(track|album|playlist|artist|show|episode)/([A-Za-z0-9]{22})', self.url)
            if match:
                destination = f'spotify:{match[1]}:{match[2]}'
        if QDesktopServices.openUrl(QUrl(destination)):
            self.opened.emit()
            self.message.setText('Toque uma música no Spotify. Os controles aparecem aqui ao conectar.')
            self.desktop.set_active(True)
        else:
            self.message.setText('Spotify não encontrado. Instale o aplicativo oficial do Spotify para Windows ou use a prévia por link.')

    def set_browser_active(self, active):
        self.desktop.set_active(active)
        if self.view:
            self.view.page().setAudioMuted(not active)

    def load(self, value):
        # Embeds are supported previews. The full website is not a playback SDK.
        self.url = embed_url(value)
        if self.view is None:
            from PySide6.QtWebEngineWidgets import QWebEngineView
            from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
            panel = self

            class SpotifyPage(QWebEnginePage):
                def acceptNavigationRequest(self, url, kind, main_frame):
                    if main_frame and (url.scheme() != 'https' or url.host().lower() not in ALLOWED_HOSTS):
                        panel.browser_message.setText('Esse link não pertence ao Spotify.')
                        return False
                    return super().acceptNavigationRequest(url, kind, main_frame)

            # Qt owns this profile for the application lifetime. Previews do not
            # need persistent login, and destroying a profile during Chromium's
            # asynchronous page teardown can crash later UI events.
            self.profile = QWebEngineProfile.defaultProfile()
            if not self.profile.property('duckPreviewConfigured'):
                self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
                self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
                self.profile.downloadRequested.connect(lambda request: request.cancel())
                self.profile.setProperty('duckPreviewConfigured', True)
            self.view = QWebEngineView(self)
            page = SpotifyPage(self.profile, self.view)
            page.setBackgroundColor(QColor('#08090c'))
            self.view.setPage(page)
            page.featurePermissionRequested.connect(lambda origin, feature: page.setFeaturePermission(origin, feature, QWebEnginePage.PermissionPolicy.PermissionDeniedByUser))
            self.view.settings().setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, True)
            self.view.setMinimumHeight(352)
            self.view.setMaximumHeight(380)
            self.view.loadFinished.connect(self.loaded)
            page.recentlyAudibleChanged.connect(self.audio_state_changed)
            self.layout_.addWidget(self.view)
        self.opened.emit()
        self.view.show()
        self.view.page().setAudioMuted(False)
        self.browser_message.setText('Carregando a prévia oficial…')
        self.load_timeout.start()
        self.view.setUrl(QUrl(self.url))

    def loaded(self, ok):
        self.load_timeout.stop()
        self.browser_message.setText('Prévia carregada. Pressione Reproduzir no player. Faixas completas: use o Spotify do PC acima.' if ok else 'Não foi possível carregar a prévia. Confira sua conexão ou use o Spotify do PC.')

    def browser_timed_out(self):
        if self.view:
            self.view.stop()
            self.view.hide()
        self.browser_message.setText('A prévia não respondeu a tempo. Tente o link novamente ou use o Spotify do PC acima.')

    def audio_state_changed(self, audible):
        if audible:
            self.load_timeout.stop()
            self.browser_message.setText('Reproduzindo a prévia oficial do Spotify.')

    def close_player(self):
        self.load_timeout.stop()
        self.desktop.set_active(False)
        if self.view:
            view = self.view
            self.view = self.profile = None
            view.stop()
            view.page().setAudioMuted(True)
            self.layout_.removeWidget(view)
            view.hide()
            view.deleteLater()

    def shutdown(self):
        self.close_player()
        self.desktop.shutdown()
