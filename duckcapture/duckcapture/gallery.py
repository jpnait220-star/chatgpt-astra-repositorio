"""Local clip library; thumbnails are generated one at a time, only when visible."""

import hashlib
import time
import logging
from pathlib import Path
from PySide6.QtCore import (
    Qt,
    QSize,
    QTimer,
    QObject,
    Signal,
    QRunnable,
    QThreadPool,
    QUrl,
)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QDialog,
    QSlider,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from .config import data_dir
from .widgets import Page, label, button
from .visuals import icon
from .fold_hover import add_fold_hover


class ThumbnailSignals(QObject):
    ready = Signal(str, str)


class Thumbnail(QRunnable):
    def __init__(self, media, source, target):
        super().__init__()
        self.media, self.source, self.target = media, source, target
        self.signals = ThumbnailSignals()

    def run(self):
        try:
            self.media.thumbnail(self.source, self.target)
            result = str(self.target)
        except Exception as error:
            logging.warning("Miniatura indisponível para %s: %s", self.source, error)
            result = ""
        self.signals.ready.emit(self.source, result)


class ClipViewer(QDialog):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(Path(path).name)
        self.resize(960, 620)
        layout = QVBoxLayout(self)
        self.player = None
        if Path(path).suffix.lower() == ".png":
            from .visuals import MascotLabel

            layout.addWidget(MascotLabel(QPixmap(path), 240), 1)
        else:
            video = QVideoWidget()
            video.setMinimumSize(480, 270)
            layout.addWidget(video, 1)
            self.player = QMediaPlayer(self)
            self.audio = QAudioOutput(self)
            self.audio.setVolume(0.65)
            self.player.setAudioOutput(self.audio)
            self.player.setVideoOutput(video)
            seek = QSlider(Qt.Orientation.Horizontal)
            seek.sliderMoved.connect(self.player.setPosition)
            self.player.positionChanged.connect(
                lambda position: seek.setValue(position)
                if not seek.isSliderDown()
                else None
            )
            self.player.durationChanged.connect(
                lambda duration: seek.setRange(0, duration)
            )
            layout.addWidget(seek)
            self.play_button = button("Pausar", self.toggle, True)
            layout.addWidget(self.play_button)
            self.player.playbackStateChanged.connect(
                lambda state: self.play_button.setText(
                    "Pausar"
                    if state == QMediaPlayer.PlaybackState.PlayingState
                    else "Reproduzir"
                )
            )
            error = label("", "muted", True)
            layout.addWidget(error)
            self.player.errorOccurred.connect(
                lambda *_: error.setText(self.player.errorString())
            )
            self.player.setSource(QUrl.fromLocalFile(str(Path(path).resolve())))
            self.player.play()
        layout.addWidget(button("Fechar", self.accept))
        self.finished.connect(lambda _: self.player.stop() if self.player else None)

    def toggle(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()


class GalleryPage(Page):
    def __init__(self, media, edit, open_folder, notify, busy):
        super().__init__(
            "Todos os seus clipes.",
            "Reveja, encontre e edite. Seus momentos ficam neste computador.",
        )
        self.media, self.edit, self.notify, self.busy = media, edit, notify, busy
        self.snapshot = []
        self.items = {}
        self.thumbnails = {}
        self.attempted = set()
        self.failed_at = {}
        self.task = None
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar pelo nome do arquivo…")
        self.search.textChanged.connect(self.filter)
        row.addWidget(self.search, 1)
        self.kind = QComboBox()
        self.kind.addItems(["Todos", "Clipes", "Prints"])
        self.kind.currentIndexChanged.connect(self.filter)
        row.addWidget(self.kind)
        row.addWidget(button("Abrir pasta", open_folder))
        self.body.addLayout(row)
        self.count = label("", "eyebrow")
        self.body.addWidget(self.count)
        self.list = QListWidget()
        self.list.setViewMode(QListWidget.ViewMode.IconMode)
        self.list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list.setMovement(QListWidget.Movement.Static)
        self.list.setIconSize(QSize(204, 114))
        self.list.setGridSize(QSize(230, 184))
        self.list.setSpacing(7)
        self.list.setMinimumHeight(290)
        self.list.setWordWrap(True)
        self.list.setUniformItemSizes(True)
        self.list.itemDoubleClicked.connect(self.open_selected)
        add_fold_hover(self.list, item_view=self.list)
        self.body.addWidget(self.list, 1)
        self.empty = label(
            "Nenhum clipe ainda. Inicie a captura e use Salvar últimos segundos.",
            "muted",
            True,
        )
        self.body.addWidget(self.empty)
        actions = QHBoxLayout()
        actions.addWidget(button("Reproduzir / ver", self.open_selected, True))
        actions.addWidget(button("Editar selecionado", self.edit_selected))
        actions.addWidget(button("Criar link", self.share_selected))
        actions.addStretch()
        self.body.addLayout(actions)
        self.timer = QTimer(self)
        self.timer.setInterval(400)
        self.timer.timeout.connect(self.next_thumbnail)
        self.timer.start()

    def share_selected(self):
        path = self.selected()
        if not path or not Path(path).is_file():
            self.notify("Selecione um clipe para criar o link.")
            return
        if Path(path).suffix.lower() != '.mp4':
            self.notify("Selecione um clipe MP4. Prints não são enviados por este botão.")
            return
        from .sharing import ShareDialog
        dialog = ShareDialog(path, self)
        dialog.exec()
        dialog.deleteLater()

    def refresh(self, snapshot):
        selected = self.selected()
        self.snapshot = snapshot
        current_keys = {(path, mtime) for path, _, mtime in snapshot}
        self.attempted.intersection_update(current_keys)
        self.failed_at = {key: value for key, value in self.failed_at.items() if key in current_keys}
        self.list.clear()
        self.items.clear()
        for path, size, mtime in snapshot:
            name = Path(path).name
            item = QListWidgetItem(
                f"{name}\n{size / 1024**2:.1f} MB · {time.strftime('%d/%m %H:%M', time.localtime(mtime))}"
            )
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setToolTip(name)
            item.setSizeHint(QSize(224, 178))
            item.setIcon(
                self.thumbnails.get(
                    (path, mtime),
                    icon("image" if Path(path).suffix.lower() == ".png" else "play"),
                )
            )
            self.list.addItem(item)
            self.items[path] = item
            if path == selected:
                self.list.setCurrentItem(item)
        self.filter()

    def filter(self, *_):
        query = self.search.text().casefold().strip()
        kind = self.kind.currentIndex()
        count = 0
        for path, item in self.items.items():
            picture = Path(path).suffix.lower() == ".png"
            visible = query in Path(path).name.casefold() and (
                kind == 0 or (kind == 2) == picture
            )
            item.setHidden(not visible)
            count += visible
        self.count.setText(
            f"{count} DE {len(self.snapshot)} ARQUIVOS · MAIS RECENTES PRIMEIRO"
        )
        self.empty.setVisible(count == 0)
        self.empty.setText(
            "Nenhum resultado para essa busca."
            if self.snapshot
            else "Nenhum clipe ainda. Inicie a captura e use Salvar últimos segundos."
        )

    def selected(self):
        item = self.list.currentItem()
        return (
            item.data(Qt.ItemDataRole.UserRole)
            if item and not item.isHidden()
            else None
        )

    def open_selected(self, *_):
        path = self.selected()
        if not path:
            self.notify("Selecione um clipe ou print.")
            return
        ClipViewer(path, self).exec()

    def edit_selected(self):
        path = self.selected()
        if path and Path(path).suffix.lower() != ".png":
            self.edit(path)
        else:
            self.notify("Selecione um vídeo para editar.")

    def next_thumbnail(self):
        if not self.isVisible() or self.task or self.busy():
            return
        viewport = self.list.viewport().rect()
        for path, size, mtime in self.snapshot:
            key = (path, mtime)
            item = self.items[path]
            if (
                (key in self.attempted and key not in self.failed_at)
                or (key in self.failed_at and time.monotonic() - self.failed_at[key] < 30)
                or item.isHidden()
                or not viewport.intersects(self.list.visualItemRect(item))
            ):
                continue
            self.attempted.add(key)
            if Path(path).suffix.lower() == ".png":
                self.thumbnail_ready(path, path, key)
                return
            cache = data_dir() / "thumbnails"
            cache.mkdir(exist_ok=True)
            target = cache / (
                hashlib.sha256(f"{path}|{size}|{mtime}".encode()).hexdigest() + ".png"
            )
            if target.exists():
                self.thumbnail_ready(path, str(target), key)
            else:
                self.task = Thumbnail(self.media, path, target)
                self.task.signals.ready.connect(
                    lambda source, result, k=key: self.thumbnail_ready(
                        source, result, k
                    )
                )
                self.pool.start(self.task)
            return

    def thumbnail_ready(self, path, target, key):
        self.task = None
        if not target:
            self.failed_at[key] = time.monotonic()
            # Do not retry while the current capture is busy.
            return
        self.failed_at.pop(key, None)
        if target:
            pixmap = QPixmap(target)
            if not pixmap.isNull():
                thumbnail = QIcon(
                    pixmap.scaled(
                        204,
                        114,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                self.thumbnails[key] = thumbnail
                if path in self.items:
                    self.items[path].setIcon(thumbnail)
