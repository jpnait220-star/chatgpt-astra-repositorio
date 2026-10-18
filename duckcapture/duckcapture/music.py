from __future__ import annotations
import random
import re
from pathlib import Path
from urllib.parse import urlparse
from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QPainter, QColor, QPixmap, QPainterPath, QDesktopServices
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFileDialog,
    QListWidget,
    QSlider,
    QLineEdit,
    QCheckBox,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from .widgets import Page, Tip, card, label, button


class Vinyl(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(175, 175)
        self.angle = 0
        self.cover = QPixmap()
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.rotate)

    def rotate(self):
        self.angle = (self.angle + 1.2) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(87, 87)
        p.rotate(self.angle)
        p.setBrush(QColor("#090b10"))
        p.setPen(QColor("#353b47"))
        p.drawEllipse(-80, -80, 160, 160)
        for r in range(34, 78, 6):
            p.drawEllipse(-r, -r, r * 2, r * 2)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#ead06d"))
        p.drawEllipse(-32, -32, 64, 64)
        if not self.cover.isNull():
            path = QPainterPath()
            path.addEllipse(-31, -31, 62, 62)
            p.setClipPath(path)
            p.drawPixmap(-31, -31, 62, 62, self.cover)
            p.setClipping(False)
        p.setBrush(QColor("#11151b"))
        p.drawEllipse(-4, -4, 8, 8)
        p.end()


class MusicPage(Page):
    trackChanged = Signal(str)

    def __init__(self, settings, save, notify):
        super().__init__(
            "Sua trilha sonora.", "Músicas locais, um disco girando e zero upload."
        )
        self.settings = settings
        self.save = save
        self.notify = notify
        self.paths = []
        self.index = -1
        self.current_title = ""
        self.history = []
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.audio.setVolume(0.5)
        frame = card()
        row = QHBoxLayout(frame)
        row.setContentsMargins(22, 20, 22, 20)
        self.vinyl = Vinyl()
        row.addWidget(self.vinyl)
        info = QVBoxLayout()
        info.addWidget(label("MUSICDUCK MIX", "eyebrow"))
        self.title = label("Escolha sua primeira música", "subheading")
        info.addWidget(self.title)
        self.position = QSlider(Qt.Orientation.Horizontal)
        self.position.setRange(0, 0)
        self.position.sliderMoved.connect(self.player.setPosition)
        info.addWidget(self.position)
        controls = QHBoxLayout()
        controls.addWidget(button("Anterior", self.previous))
        self.play_button = button("Reproduzir", self.toggle, True)
        controls.addWidget(self.play_button)
        controls.addWidget(button("Próxima", self.next))
        info.addLayout(controls)
        options = QHBoxLayout()
        self.shuffle = QCheckBox("Aleatório")
        self.repeat = QCheckBox("Repetir")
        options.addWidget(self.shuffle)
        options.addWidget(self.repeat)
        volume = QSlider(Qt.Orientation.Horizontal)
        volume.setRange(0, 100)
        volume.setValue(50)
        volume.valueChanged.connect(lambda value: self.audio.setVolume(value / 100))
        options.addWidget(label("Volume", "muted"))
        options.addWidget(volume)
        info.addLayout(options)
        row.addLayout(info, 1)
        self.body.addWidget(frame)
        folderrow = QHBoxLayout()
        self.folder = label(settings.music_dir, "muted", True)
        folderrow.addWidget(self.folder, 1)
        folderrow.addWidget(button("Escolher pasta", self.choose_folder))
        folderrow.addWidget(button("Atualizar", self.scan))
        self.body.addLayout(folderrow)
        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(lambda item: self.play(self.list.row(item)))
        self.body.addWidget(self.list, 1)
        spotify = QHBoxLayout()
        self.spotify = QLineEdit(settings.spotify)
        self.spotify.setPlaceholderText("https://open.spotify.com/playlist/…")
        spotify.addWidget(self.spotify, 1)
        spotify.addWidget(button("Abrir no Spotify", self.open_spotify))
        self.body.addLayout(spotify)
        self.body.addWidget(
            label(
                "Spotify abre no serviço oficial. Esta versão não importa nem baixa as faixas da playlist.",
                "tiny",
                True,
            )
        )
        self.tip = Tip(
            "MusicDuck",
            "Coloque MP3, WAV, FLAC, OGG ou M4A na sua pasta. O áudio do sistema também pode incluir a música nos clipes.",
        )
        self.body.addWidget(self.tip)
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(lambda v: self.position.setMaximum(v))
        self.player.playbackStateChanged.connect(self.state_changed)
        self.player.mediaStatusChanged.connect(self.status_changed)
        self.player.errorOccurred.connect(
            lambda *_: self.notify("Erro de reprodução: " + self.player.errorString())
        )
        self.scan()
        self.watch = QTimer(self)
        self.watch.setInterval(10000)
        self.watch.timeout.connect(self.scan)
        self.watch.start()

    def scan(self):
        folder = Path(self.settings.music_dir).expanduser()
        try:
            folder.mkdir(parents=True, exist_ok=True)
            paths = sorted(
                p
                for p in folder.iterdir()
                if p.suffix.lower() in (".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac")
            )
        except OSError as error:
            self.notify(str(error))
            return
        if paths == self.paths:
            return
        previous = self.paths[self.index] if 0 <= self.index < len(self.paths) else None
        self.paths = paths
        self.list.clear()
        self.list.addItems([p.stem for p in paths])
        self.index = paths.index(previous) if previous in paths else -1
        if self.index >= 0:
            self.list.setCurrentRow(self.index)

    def choose_folder(self):
        path = QFileDialog.getExistingDirectory(
            self, "Pasta de músicas", self.settings.music_dir
        )
        if path:
            self.settings.music_dir = path
            self.folder.setText(path)
            self.save()
            self.scan()

    def play(self, index):
        if not 0 <= index < len(self.paths):
            return
        self.index = index
        path = self.paths[index]
        title = path.stem
        self.vinyl.cover = QPixmap()
        try:
            from mutagen import File

            tags = File(path, easy=True)
            if tags and tags.get("title"):
                title = str(tags["title"][0])
            media = File(path)
            if media and media.tags:
                for key, value in media.tags.items():
                    if str(key).startswith("APIC"):
                        self.vinyl.cover.loadFromData(value.data)
                        break
                    if str(key) == "covr":
                        self.vinyl.cover.loadFromData(bytes(value[0]))
                        break
        except Exception:
            pass
        self.current_title = title
        self.title.setText(title)
        self.trackChanged.emit(title)
        self.list.setCurrentRow(index)
        self.player.setSource(QUrl.fromLocalFile(str(path.resolve())))
        self.player.play()

    def toggle(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        elif self.index < 0:
            self.play(0)
        else:
            self.player.play()

    def next(self):
        if not self.paths:
            return
        if self.index >= 0:
            self.history.append(self.index)
        choices = [i for i in range(len(self.paths)) if i != self.index]
        self.play(
            random.choice(choices)
            if self.shuffle.isChecked() and choices
            else (self.index + 1) % len(self.paths)
        )

    def previous(self):
        self.play(self.history.pop() if self.history else max(0, self.index - 1))

    def update_position(self, value):
        if not self.position.isSliderDown():
            self.position.setValue(value)

    def state_changed(self, state):
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.play_button.setText("Pausar" if playing else "Reproduzir")
        if playing:
            self.vinyl.timer.start()
            self.trackChanged.emit(self.current_title)
        else:
            self.vinyl.timer.stop()
            self.trackChanged.emit(
                "Pausado · " + self.current_title if self.current_title else ""
            )

    def status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.repeat.isChecked():
                self.player.setPosition(0)
                self.player.play()
            elif self.shuffle.isChecked() or self.index + 1 < len(self.paths):
                self.next()

    def open_spotify(self):
        url = self.spotify.text().strip()
        parsed = urlparse(url)
        if (
            parsed.scheme != "https"
            or parsed.netloc != "open.spotify.com"
            or not re.fullmatch(r"/playlist/[A-Za-z0-9]+/?", parsed.path)
        ):
            self.notify("Use o link HTTPS de uma playlist em open.spotify.com.")
            return
        self.settings.spotify = url
        self.save()
        QDesktopServices.openUrl(QUrl(url))
