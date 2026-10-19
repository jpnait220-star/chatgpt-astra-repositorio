"""Spotify's public player, loaded on request inside Qt; no API keys or downloads."""

import re
from urllib.parse import urlparse
from PySide6.QtCore import QUrl, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from .widgets import label, button


def embed_url(value):
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
        raise ValueError(
            "Use um link HTTPS de música, álbum ou playlist em open.spotify.com (Compartilhar → Copiar link)."
        )
    return f"https://open.spotify.com/embed/{match[1]}/{match[2]}?theme=0"


class SpotifyPanel(QWidget):
    opened = Signal()

    def __init__(self):
        super().__init__()
        self.view = None
        self.profile = None
        self.url = ""
        self.resolve_reply = None
        self.network = None
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.message = label(
            "Spotify dentro do DuckCapture. Cole um link de música, álbum ou playlist e clique em Ouvir no app.",
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
        parsed = urlparse(value.strip())
        if (
            parsed.scheme == "https"
            and parsed.netloc == "spotify.link"
            and re.fullmatch(r"/[A-Za-z0-9_-]+/?", parsed.path)
        ):
            self.resolve_short(QUrl(value.strip()))
            return
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
            "Carregando player oficial… Depois clique em reproduzir nos controles abaixo."
        )
        self.reload_button.show()
        self.close_button.show()
        self.opened.emit()
        self.view.setUrl(QUrl(self.url))

    def resolve_short(self, url, hops=0):
        from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest

        if hops >= 5:
            self.message.setText(
                "Esse link redirecionou muitas vezes. Copie o endereço completo de open.spotify.com."
            )
            return
        if self.resolve_reply:
            old, self.resolve_reply = self.resolve_reply, None
            old.abort()
        if self.network is None:
            self.network = QNetworkAccessManager(self)
        self.message.setText("Abrindo o link compartilhado do Spotify…")
        request = QNetworkRequest(url)
        request.setTransferTimeout(8000)
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.ManualRedirectPolicy,
        )
        reply = self.network.head(request)
        self.resolve_reply = reply

        def finished():
            reply.deleteLater()
            if self.resolve_reply is not reply:
                return
            self.resolve_reply = None
            location = reply.attribute(
                QNetworkRequest.Attribute.RedirectionTargetAttribute
            )
            if location:
                target = url.resolved(location)
                try:
                    canonical = embed_url(target.toString())
                except ValueError:
                    if (
                        target.scheme() == "https"
                        and target.host() == "spotify.link"
                        and not target.userName()
                        and not target.port() > 0
                    ):
                        self.resolve_short(target, hops + 1)
                        return
                else:
                    self.load(canonical)
                    return
            self.message.setText(
                "Não foi possível abrir o link curto. Confira a conexão ou copie o endereço completo de open.spotify.com."
            )

        reply.finished.connect(finished)

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
        if self.resolve_reply:
            reply, self.resolve_reply = self.resolve_reply, None
            reply.abort()
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
