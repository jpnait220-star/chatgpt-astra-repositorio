from __future__ import annotations
import copy
from pathlib import Path
from PySide6.QtCore import Qt, QUrl, QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QTabWidget,
    QWidget,
    QAbstractItemView,
    QStackedWidget,
    QFileDialog,
    QListWidget,
    QDoubleSpinBox,
    QSlider,
    QLineEdit,
    QComboBox,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from .widgets import Page, Tip, label, button, card
from .timeline import TrimTimeline
from .visuals import icon
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
        self.durations = {}
        top = QHBoxLayout()
        top.addWidget(button("Importar vídeo", self.import_video))
        top.addWidget(button("Desfazer", self.revert))
        top.addStretch()
        self.export_button = button("Exportar MP4", self.export, True)
        top.addWidget(self.export_button)
        self.body.addLayout(top)

        studio = QHBoxLayout()
        studio.setSpacing(16)
        preview = card()
        preview_body = QVBoxLayout(preview)
        preview_body.setContentsMargins(16, 16, 16, 16)
        preview_body.addWidget(label("01 / PRÉVIA", "eyebrow"))
        self.video = QVideoWidget()
        self.video.setMinimumSize(300, 195)
        self.preview_stack = QStackedWidget()
        empty = QWidget()
        empty_body = QVBoxLayout(empty)
        empty_body.addStretch()
        empty_icon = label("")
        empty_icon.setPixmap(icon("editor").pixmap(42, 42))
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_body.addWidget(empty_icon)
        empty_title = label("Seu próximo clipe começa aqui", "subheading", True)
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_body.addWidget(empty_title)
        empty_hint = label("Importe um vídeo ou escolha um clipe na biblioteca.", "muted", True)
        empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_body.addWidget(empty_hint)
        empty_body.addStretch()
        self.preview_stack.addWidget(empty)
        self.preview_stack.addWidget(self.video)
        preview_body.addWidget(self.preview_stack, 1)
        playback = QHBoxLayout()
        self.play_button = button("Reproduzir", self.toggle)
        self.play_button.setIcon(icon("play"))
        playback.addWidget(self.play_button)
        self.position = QSlider(Qt.Orientation.Horizontal)
        self.position.sliderMoved.connect(self.seek)
        playback.addWidget(self.position, 1)
        self.position_label = label("00:00 / 00:00", "muted")
        playback.addWidget(self.position_label)
        preview_body.addLayout(playback)
        preview_body.addWidget(label("Arraste as pontas para definir o corte", "tiny"))
        self.timeline = TrimTimeline()
        self.timeline.trimmed.connect(self.trimmed)
        self.timeline.seeked.connect(self.seek)
        preview_body.addWidget(self.timeline)
        preview_body.addWidget(label("Texto, filtro, imagem e zoom aparecem no arquivo exportado.", "tiny", True))
        studio.addWidget(preview, 3)

        inspector = card()
        inspector.setMinimumWidth(248)
        inspector.setMaximumWidth(330)
        inspection = QVBoxLayout(inspector)
        inspection.setContentsMargins(16, 16, 16, 16)
        inspection.addWidget(label("02 / AJUSTES DO TRECHO", "eyebrow"))
        self.selected_title = label("Nenhum trecho selecionado", "muted", True)
        inspection.addWidget(self.selected_title)
        self.inspector_tabs = QTabWidget()
        cut, look = QWidget(), QWidget()
        self.inspector_tabs.addTab(cut, "Corte e som")
        self.inspector_tabs.addTab(look, "Aparência")
        inspection.addWidget(self.inspector_tabs)
        cut_form, look_form = QFormLayout(cut), QFormLayout(look)
        for form in (cut_form, look_form):
            form.setContentsMargins(0, 10, 0, 0)
            form.setSpacing(12)
            form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        cut_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        self.start, self.end = QDoubleSpinBox(), QDoubleSpinBox()
        self.start.setRange(0, 86400)
        self.end.setRange(.01, 86400)
        for control in (self.start, self.end):
            control.setSuffix(" s")
            control.setDecimals(2)
            control.setSingleStep(.1)
        self.speed, self.volume, self.zoom = QDoubleSpinBox(), QDoubleSpinBox(), QDoubleSpinBox()
        self.speed.setRange(.25, 4)
        self.speed.setSingleStep(.25)
        self.speed.setSuffix(" ×")
        self.volume.setRange(0, 2)
        self.volume.setSingleStep(.1)
        self.volume.setSuffix(" ×")
        self.zoom.setRange(1, 3)
        self.zoom.setSingleStep(.1)
        self.zoom.setSuffix(" ×")
        for control in (self.speed, self.volume, self.zoom):
            control.setValue(1)
        for title, control in [("Início", self.start), ("Fim", self.end), ("Velocidade", self.speed), ("Volume", self.volume)]:
            cut_form.addRow(title, control)
        look_form.addRow("Zoom", self.zoom)
        for control in (self.start, self.end, self.speed, self.volume, self.zoom):
            control.editingFinished.connect(self.commit)
        self.text = QLineEdit()
        self.text.setPlaceholderText("Uma legenda para esse momento")
        self.text.editingFinished.connect(self.commit)
        look_form.addRow("Texto no vídeo", self.text)
        self.effect = QComboBox()
        self.effect.addItems(["Original", "Preto e branco", "Quente", "Contraste"])
        self.effect.currentTextChanged.connect(self.commit)
        look_form.addRow("Filtro", self.effect)
        look_form.addRow(button("Adicionar imagem", self.sticker))
        look_form.addRow(button("Remover imagem", self.no_sticker))
        inspection.addStretch()
        studio.addWidget(inspector, 2)
        self.body.addLayout(studio, 1)

        sequence = card()
        sequence_body = QVBoxLayout(sequence)
        sequence_body.setContentsMargins(16, 14, 16, 14)
        order = QHBoxLayout()
        order.addWidget(label("03 / SEQUÊNCIA", "eyebrow"))
        order.addStretch()
        order.addWidget(button("Dividir aqui", self.split))
        order.addWidget(button("Anterior", lambda: self.move(-1)))
        order.addWidget(button("Próximo", lambda: self.move(1)))
        order.addWidget(button("Remover", self.remove))
        sequence_body.addLayout(order)
        self.list = QListWidget()
        self.list.setFlow(QListWidget.Flow.LeftToRight)
        self.list.setWrapping(False)
        self.list.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list.setFixedHeight(94)
        self.list.currentRowChanged.connect(self.select)
        sequence_body.addWidget(self.list)
        self.body.addWidget(sequence)
        self.tip = Tip("EditDuck", "Importe um vídeo, escolha o trecho e ajuste as pontas do corte. Organize a sequência e exporte seu clipe.")
        self.body.addWidget(self.tip)
        self.inspector_tabs.setEnabled(False)
        self.export_button.setEnabled(False)
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setVolume(1)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video)
        self.player.mediaStatusChanged.connect(self.media_ready)
        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(self.duration_changed)
        self.player.playbackStateChanged.connect(self.play_state_changed)
        self.player.errorOccurred.connect(lambda *_: notify("Prévia de vídeo: " + self.player.errorString()))

    def duration_changed(self, duration):
        self.position.setMaximum(duration)
        part = self.current()
        if part:
            total = self.durations.get(part.path, duration / 1000)
            self.timeline.set_range(total, part.start, part.end)

    def play_state_changed(self, state):
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.play_button.setText("Pausar" if playing else "Reproduzir")
        self.play_button.setIcon(icon("pause" if playing else "play"))

    def trimmed(self, start, end):
        self.start.setValue(start)
        self.end.setValue(end)
        self.commit()
        self.seek(round(self.start.value()*1000))

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
            absolute = str(Path(path).resolve())
            self.durations[absolute] = info.duration
            self.parts.append(EditPart(absolute, 0, info.duration))
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
        self.inspector_tabs.setEnabled(bool(self.parts))
        self.export_button.setEnabled(bool(self.parts) and not (self.task and self.task.isRunning()))
        if self.parts:
            self.list.setCurrentRow(max(0, min(index, len(self.parts) - 1)))
        else:
            self.player.stop()
            self.player.setSource(QUrl())
            self.preview_stack.setCurrentIndex(0)
            self.selected_title.setText("Nenhum trecho selecionado")
            self.timeline.set_range(0, 0, 0)

    def select(self, index):
        if not 0 <= index < len(self.parts):
            return
        self.loading = True
        self.preview_stack.setCurrentIndex(1)
        p = self.parts[index]
        self.selected_title.setText(f"{index+1:02} / {Path(p.path).name}")
        self.timeline.set_range(self.durations.get(p.path, p.end), p.start, p.end)
        self.start.setMaximum(max(0, self.durations.get(p.path, 86400) - .05))
        self.end.setMaximum(self.durations.get(p.path, 86400))
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
        if self.start.value() >= self.end.value():
            self.start.setValue(p.start)
            self.end.setValue(p.end)
            self.notify("O início precisa ficar antes do fim do trecho.")
            self.timeline.set_range(self.durations.get(p.path, p.end), p.start, p.end)
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
        self.timeline.set_range(self.durations.get(p.path, p.end), p.start, p.end)
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
        self.timeline.set_position(milliseconds)
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
