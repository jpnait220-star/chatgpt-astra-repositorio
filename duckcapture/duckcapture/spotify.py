"""Spotify's public player, loaded on request inside Qt; no API keys or downloads."""

import re
from urllib.parse import urlparse
from PySide6.QtCore import QUrl, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from .widgets import label, button


def embed_url(value):
    value = value.strip()
    if value.startswith("spotify:playlist:"):
        value = "https://open.spotify.com/playlist/" + value.removeprefix(
            "spotify:playlist:"
        )
    parsed = urlparse(value)
    match = re.fullmatch(
        r"/(?:intl-[a-z]{2}/)?(?:embed/)?playlist/([A-Za-z0-9]{22})/?", parsed.path
    )
    if parsed.scheme != "https" or parsed.netloc != "open.spotify.com" or not match:
        raise ValueError(
            "Use o link HTTPS de uma playlist em open.spotify.com (Compartilhar → Copiar link)."
        )
    return f"https://open.spotify.com/embed/playlist/{match[1]}?theme=0"


class SpotifyPanel(QWidget):
    opened = Signal()

    def __init__(self):
        super().__init__()
        self.view = None
        self.profile = None
        self.url = ""
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.message = label(
            "Spotify dentro do DuckCapture. Cole uma playlist e clique em Carregar player.",
            "muted",
            True,
        )
        self.layout_.addWidget(self.message)
        self.layout_.addWidget(
            label(
                "Conta gratuita: o player oficial pode reproduzir apenas prévias de 30 segundos. Faixas completas dependem das permissões do Spotify e do suporte do player. Músicas locais tocam completas.",
                "tiny",
                True,
            )
        )
        actions = QHBoxLayout()
        self.reload_button = button("Recarregar player", self.reload)
        self.close_button = button("Fechar player", self.close_player)
        actions.addWidget(self.reload_button)
        actions.addWidget(self.close_button)
        actions.addStretch()
        self.layout_.addLayout(actions)
        self.reload_button.hide()
        self.close_button.hide()

    def load(self, value):
        self.url = embed_url(value)
        if self.view is None:
            # Lazy import avoids a Chromium process while only clipping or
            # listening to local music. Keep Qt's sandbox and TLS defaults.
            from PySide6.QtWebEngineWidgets import QWebEngineView
            from PySide6.QtWebEngineCore import (
                QWebEnginePage,
                QWebEngineProfile,
                QWebEngineSettings,
            )

            panel = self

            class PlayerPage(QWebEnginePage):
                def acceptNavigationRequest(self, url, kind, main_frame):
                    if main_frame and url.scheme() != "https":
                        return False
                    if main_frame and url.host() not in (
                        "open.spotify.com",
                        "accounts.spotify.com",
                    ):
                        panel.message.setText(
                            "Este link não faz parte do player. Use os controles da playlist abaixo."
                        )
                        return False
                    return True

            self.profile = QWebEngineProfile(
                self
            )  # Ephemeral, no stored account session.
            self.profile.downloadRequested.connect(lambda request: request.cancel())
            self.view = QWebEngineView(self)
            page = PlayerPage(self.profile, self.view)
            self.view.setPage(page)
            page.newWindowRequested.connect(
                lambda _: self.message.setText(
                    "Esse controle tenta abrir outra janela. A reprodução disponível nesta versão usa os botões da playlist abaixo."
                )
            )
            page.featurePermissionRequested.connect(
                lambda origin, feature: page.setFeaturePermission(
                    origin,
                    feature,
                    QWebEnginePage.PermissionPolicy.PermissionDeniedByUser,
                )
            )
            self.view.settings().setAttribute(
                QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, True
            )
            self.view.setMinimumHeight(390)
            self.view.loadFinished.connect(self.loaded)
            self.layout_.insertWidget(1, self.view)
        self.message.setText(
            "Carregando player oficial… Depois clique em reproduzir na playlist."
        )
        self.reload_button.show()
        self.close_button.show()
        self.opened.emit()
        self.view.setUrl(QUrl(self.url))

    def loaded(self, ok):
        self.message.setText(
            "Player oficial do Spotify · use os controles abaixo para ouvir."
            if ok
            else "O Spotify não carregou. Confira sua conexão e tente Recarregar player. O serviço pode bloquear players incorporados."
        )

    def reload(self):
        if self.url:
            self.load(self.url)

    def close_player(self):
        if self.view:
            view, profile = self.view, self.profile
            self.view = self.profile = None
            view.stop()
            view.page().setAudioMuted(True)
            self.layout_.removeWidget(view)
            view.hide()
            # The profile must outlive its page.
            view.destroyed.connect(profile.deleteLater)
            view.deleteLater()
        self.reload_button.hide()
        self.close_button.hide()
        self.message.setText(
            "Player fechado. Carregue a playlist para ouvir novamente."
        )
