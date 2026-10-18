from __future__ import annotations
import copy
from pathlib import Path
from PySide6.QtCore import Qt, QUrl, QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QFileDialog,
    QListWidget,
    QDoubleSpinBox,
    QSlider,
    QLineEdit,
    QComboBox,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from .widgets import Page, Tip, label, button
from .media import EditPart


class Task(QThread):
    result = Signal(object)
    failed = Signal(str)

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self.fn = fn

    def run(self):
        try:
            self.result.emit(self.fn())
        except Exception as error:
            self.failed.emit(str(error))


class EditorPage(Page):
    exported = Signal(str)

    def __init__(self, media, settings, notify):
        super().__init__(
            "O momento, do seu jeito.",
            "Corte, divida, junte e exporte. O arquivo original fica intacto.",
        )
        self.media = media
        self.settings = settings
        self.notify = notify
        self.parts = []
        self.undo = []
        self.loading = False
        self.task = None
        top = QHBoxLayout()
        top.addWidget(button("+ Importar vídeo", self.import_video))
        top.addWidget(button("Dividir aqui", self.split))
        top.addWidget(button("Desfazer", self.revert))
        top.addStretch()
        self.export_button = button("Exportar MP4", self.export, True)
        top.addWidget(self.export_button)
        self.body.addLayout(top)
        middle = QHBoxLayout()
        self.video = QVideoWidget()
        self.video.setMinimumSize(380, 210)
        middle.addWidget(self.video, 3)
        self.list = QListWidget()
        self.list.setMinimumWidth(180)
        self.list.currentRowChanged.connect(self.select)
        middle.addWidget(self.list, 1)
        self.body.addLayout(middle, 1)
        playback = QHBoxLayout()
        playback.addWidget(button("Reproduzir / Pausar", self.toggle))
        self.position = QSlider(Qt.Orientation.Horizontal)
        self.position.sliderMoved.connect(self.seek)
        playback.addWidget(self.position, 1)
        self.position_label = label("00:00 / 00:00", "muted")
        playback.addWidget(self.position_label)
        self.body.addLayout(playback)
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setVolume(1)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video)
        self.player.mediaStatusChanged.connect(self.media_ready)
        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(lambda d: self.position.setMaximum(d))
        self.player.errorOccurred.connect(
            lambda *_: notify("Prévia de vídeo: " + self.player.errorString())
        )
        row = QHBoxLayout()
        self.start = QDoubleSpinBox()
        self.start.setRange(0, 86400)
        self.start.setSuffix(" s")
        self.end = QDoubleSpinBox()
        self.end.setRange(0.01, 86400)
        self.end.setSuffix(" s")
        self.speed = QDoubleSpinBox()
        self.speed.setRange(0.25, 4)
        self.speed.setSingleStep(0.25)
        self.speed.setValue(1)
        self.speed.setSuffix("×")
        self.volume = QDoubleSpinBox()
        self.volume.setRange(0, 2)
        self.volume.setSingleStep(0.1)
        self.volume.setValue(1)
        self.zoom = QDoubleSpinBox()
        self.zoom.setRange(1, 3)
        self.zoom.setSingleStep(0.1)
        self.zoom.setValue(1)
        for title, control in [
            ("Início", self.start),
            ("Fim", self.end),
            ("Velocidade", self.speed),
            ("Volume", self.volume),
            ("Zoom", self.zoom),
        ]:
            row.addWidget(label(title, "muted"))
            row.addWidget(control)
            control.editingFinished.connect(self.commit)
        self.body.addLayout(row)
        row = QHBoxLayout()
        self.text = QLineEdit()
        self.text.setPlaceholderText("Texto sobre o vídeo")
        self.text.editingFinished.connect(self.commit)
        row.addWidget(self.text, 1)
        self.effect = QComboBox()
        self.effect.addItems(["Original", "Preto e branco", "Quente", "Contraste"])
        self.effect.currentTextChanged.connect(self.commit)
        row.addWidget(self.effect)
        row.addWidget(button("Sticker…", self.sticker))
        row.addWidget(button("Sem sticker", self.no_sticker))
        self.body.addLayout(row)
        order = QHBoxLayout()
        order.addWidget(button("Mover ↑", lambda: self.move(-1)))
        order.addWidget(button("Mover ↓", lambda: self.move(1)))
        order.addWidget(button("Remover trecho", self.remove))
        order.addStretch()
        self.body.addLayout(order)
        self.body.addWidget(
            label(
                "A prévia reproduz o trecho original. Texto, filtros, sticker e zoom são aplicados na exportação.",
                "tiny",
                True,
            )
        )
        self.tip = Tip(
            "EditDuck",
            "Use a barra para escolher o ponto e “Dividir aqui”. Ajuste início e fim de cada trecho; a lista define a ordem do vídeo final.",
        )
        self.body.addWidget(self.tip)

    def current(self):
        i = self.list.currentRow()
        return self.parts[i] if 0 <= i < len(self.parts) else None

    def remember(self):
        self.undo.append(copy.deepcopy(self.parts))
        self.undo = self.undo[-40:]

    def import_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar vídeo",
            self.settings.clips_dir,
            "Vídeos (*.mp4 *.mkv *.mov *.webm *.avi)",
        )
        if path:
            self.load(path)

    def load(self, path):
        try:
            info = self.media.probe(path)
            self.remember()
            self.parts.append(EditPart(str(Path(path).resolve()), 0, info.duration))
            self.render(len(self.parts) - 1)
        except Exception as error:
            self.notify(str(error))

    def render(self, index=0):
        self.list.blockSignals(True)
        self.list.clear()
        for i, p in enumerate(self.parts):
            self.list.addItem(
                f"{i + 1:02}  {Path(p.path).name}\n{p.start:.2f}–{p.end:.2f}s · {p.speed:g}×"
            )
        self.list.blockSignals(False)
        if self.parts:
            self.list.setCurrentRow(max(0, min(index, len(self.parts) - 1)))
        else:
            self.player.stop()
            self.player.setSource(QUrl())

    def select(self, index):
        if not 0 <= index < len(self.parts):
            return
        self.loading = True
        p = self.parts[index]
        self.start.setValue(p.start)
        self.end.setValue(p.end)
        self.speed.setValue(p.speed)
        self.volume.setValue(p.volume)
        self.zoom.setValue(p.zoom)
        self.text.setText(p.text)
        self.effect.setCurrentText(p.effect)
        self.player.setSource(QUrl.fromLocalFile(p.path))
        self.player.setPlaybackRate(p.speed)
        self.audio.setVolume(min(1, p.volume))
        self.player.setPosition(round(p.start * 1000))
        self.loading = False

    def commit(self, *_):
        p = self.current()
        if self.loading or p is None:
            return
        values = dict(
            start=self.start.value(),
            end=self.end.value(),
            speed=self.speed.value(),
            volume=self.volume.value(),
            zoom=self.zoom.value(),
            text=self.text.text(),
            effect=self.effect.currentText(),
        )
        if all(getattr(p, k) == v for k, v in values.items()):
            return
        self.remember()
        for key, value in values.items():
            setattr(p, key, value)
        self.player.setPlaybackRate(p.speed)
        self.audio.setVolume(min(1, p.volume))
        row = self.list.currentRow()
        self.list.item(row).setText(
            f"{row + 1:02}  {Path(p.path).name}\n{p.start:.2f}–{p.end:.2f}s · {p.speed:g}×"
        )

    def media_ready(self, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia and self.current():
            self.player.setPosition(round(self.current().start * 1000))

    def seek(self, milliseconds):
        self.player.setPosition(milliseconds)

    def position_changed(self, milliseconds):
        if not self.position.isSliderDown():
            self.position.setValue(milliseconds)
        t = milliseconds // 1000
        total = self.player.duration() // 1000
        self.position_label.setText(
            f"{t // 60:02}:{t % 60:02} / {total // 60:02}:{total % 60:02}"
        )
        p = self.current()
        if (
            p
            and self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
            and milliseconds >= p.end * 1000
        ):
            self.player.pause()

    def toggle(self):
        p = self.current()
        if not p:
            return
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            if not p.start * 1000 <= self.player.position() < p.end * 1000:
                self.player.setPosition(round(p.start * 1000))
            self.player.play()

    def split(self):
        p = self.current()
        point = self.player.position() / 1000
        if not p or not p.start + 0.05 < point < p.end - 0.05:
            self.notify("Escolha um ponto dentro do trecho para dividir.")
            return
        self.remember()
        index = self.list.currentRow()
        second = copy.deepcopy(p)
        p.end = point
        second.start = point
        self.parts.insert(index + 1, second)
        self.render(index)

    def sticker(self):
        p = self.current()
        if not p:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Escolher sticker", "", "Imagens (*.png *.jpg *.webp)"
        )
        if path:
            self.remember()
            p.sticker = path
            self.notify(
                "Sticker adicionado ao trecho. Ele aparece no canto superior direito na exportação."
            )

    def no_sticker(self):
        p = self.current()
        if p:
            self.remember()
            p.sticker = ""

    def remove(self):
        i = self.list.currentRow()
        if i >= 0:
            self.remember()
            self.parts.pop(i)
            self.render(i)

    def move(self, delta):
        i = self.list.currentRow()
        j = i + delta
        if 0 <= j < len(self.parts):
            self.remember()
            self.parts[i], self.parts[j] = self.parts[j], self.parts[i]
            self.render(j)

    def revert(self):
        if self.undo:
            self.parts = self.undo.pop()
            self.render()

    def export(self):
        if self.task and self.task.isRunning():
            return
        self.commit()
        if not self.parts:
            self.notify("Importe um vídeo primeiro.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar como",
            str(Path(self.settings.clips_dir) / "Editado.mp4"),
            "Vídeo MP4 (*.mp4)",
        )
        if not path:
            return
        output = Path(path).with_suffix(".mp4")
        parts = copy.deepcopy(self.parts)
        self.player.pause()
        self.export_button.setEnabled(False)
        self.export_button.setText("Exportando…")

        def work():
            return self.media.export(
                parts,
                output,
                self.media.encoder(self.settings.encoder),
                self.settings.fps,
                self.settings.quality,
            )

        self.task = Task(work, self)
        self.task.result.connect(
            lambda p: (
                self.exported.emit(str(p)),
                self.notify("Vídeo exportado: " + str(p)),
            )
        )
        self.task.failed.connect(self.notify)
        self.task.finished.connect(self.export_done)
        self.task.start()

    def export_done(self):
        self.export_button.setEnabled(True)
        self.export_button.setText("Exportar MP4")
