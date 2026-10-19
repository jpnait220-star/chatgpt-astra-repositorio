from __future__ import annotations
import logging
import queue
import shutil
import sys
import time
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QUrl, QLockFile, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QDesktopServices, QPixmap, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QStackedWidget,
    QScrollArea,
    QComboBox,
    QFileDialog,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QSystemTrayIcon,
    QMenu,
    QKeySequenceEdit,
    QLabel,
    QGraphicsOpacityEffect,
)
from .config import Settings, data_dir, DURATIONS, FPS, PROFILES
from .widgets import STYLE, Page, Tip, card, label, button, mascot, CHARACTERS
from .visuals import MascotLabel, icon as vector_icon, motion_enabled
from .gallery import GalleryPage, ClipViewer
from . import __version__
from .media import Media
from .capture import CaptureEngine
from .windows import IS_WINDOWS, list_windows, Hotkeys, InputSampler
from .music import MusicPage
from .hud_editor import HudEditor
from .editor import EditorPage


class MainWindow(QMainWindow):
    def __init__(self, settings=None):
        super().__init__()
        self.settings = settings or Settings.load()
        QApplication.instance().setProperty("duckMotion", self.settings.motion)
        self.fade_overlay = None
        self.media = Media(self.settings.ffmpeg_dir)
        self.engine = CaptureEngine(self.media)
        self.setWindowTitle("DuckCapture")
        screen = QApplication.primaryScreen().availableGeometry()
        self.setMinimumSize(1000, 640)
        self.resize(min(1360, screen.width() - 40), min(930, screen.height() - 60))
        self.setWindowIcon(QIcon(mascot("Duck", 128)))
        self.setStyleSheet(STYLE)
        self.music_title = ""
        self.file_snapshot = []
        self.inputs = InputSampler()
        self.hud_sampling = False
        self.last_toast = ""
        shell = QWidget()
        shell.setObjectName("shell")
        self.setCentralWidget(shell)
        row = QHBoxLayout(shell)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(235)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(19, 27, 19, 23)
        nav.setSpacing(10)
        brand = QHBoxLayout()
        icon = MascotLabel(mascot("Duck", 80), 44)
        icon.setFixedSize(44, 44)
        brand.addWidget(icon)
        brand.addWidget(label("DuckCapture", "brand"))
        nav.addLayout(brand)
        nav.addWidget(label("SEU MOMENTO MERECE FICAR.", "tiny"))
        nav.addSpacing(31)
        self.stack = QStackedWidget()
        self.nav = {}
        for index, symbol, title in [
            (0, "home", "Início"),
            (1, "capture", "Capturar"),
            (6, "library", "Todos os clipes"),
            (2, "editor", "Editor"),
            (3, "hud", "HUD"),
            (4, "music", "Música"),
            (5, "settings", "Configurações"),
        ]:
            b = button(title, lambda checked=False, i=index: self.navigate(i))
            b.setIcon(vector_icon(symbol))
            b.setObjectName("nav")
            b.setCheckable(True)
            nav.addWidget(b)
            self.nav[index] = b
        nav.addStretch()
        nav.addWidget(label("LOCAL. PRIVADO. SEU.", "eyebrow"))
        nav.addWidget(
            label(
                "Seus clipes ficam no PC.\nSpotify conecta ao serviço ao carregar o player.",
                "muted",
                True,
            )
        )
        nav.addSpacing(15)
        nav.addWidget(button("Conhecer a turma", self.show_mascots))
        nav.addWidget(label(f"DUCKCAPTURE     {__version__} · ALPHA", "tiny"))
        row.addWidget(sidebar)
        row.addWidget(self.stack, 1)
        self.home = self.home_page()
        self.capture = self.capture_page()
        self.editor = EditorPage(self.media, self.settings, self.notify)
        self.hud = HudEditor(self.settings, self.save_settings, self.notify)
        self.music = MusicPage(self.settings, self.save_settings, self.notify)
        self.preferences = self.settings_page()
        self.gallery = GalleryPage(
            self.media,
            self.edit_path,
            self.open_clips,
            self.notify,
            lambda: self.engine.active or self.engine.starting,
        )

        for page in [
            self.home,
            self.capture,
            self.editor,
            self.hud,
            self.music,
            self.preferences,
            self.gallery,
        ]:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(page)
            self.stack.addWidget(scroll)
        self.music.trackChanged.connect(self.set_music)
        self.editor.exported.connect(lambda _: self.refresh_library(True))
        self.hotkeys = Hotkeys()
        QApplication.instance().installNativeEventFilter(self.hotkeys)
        try:
            self.bind_hotkeys()
        except ValueError as error:
            self.notify(str(error))
        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self.input_timer = QTimer(self)
        self.input_timer.setInterval(33)
        self.input_timer.timeout.connect(self.sample_inputs)
        self.library_timer = QTimer(self)
        self.library_timer.setInterval(5000)
        self.library_timer.timeout.connect(self.refresh_library)
        self.library_timer.start()
        self.tray = QSystemTrayIcon(self.windowIcon(), self)
        self.tray.setToolTip("DuckCapture — captura parada")
        menu = QMenu()
        menu.addAction("Abrir DuckCapture", self.show_normal)
        menu.addAction("Salvar clipe", self.save_clip)
        menu.addAction("Tirar print", self.screenshot)
        menu.addAction("Parar captura", self.stop_capture)
        menu.addSeparator()
        menu.addAction("Sair", self.close)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda reason: self.show_normal()
            if reason == QSystemTrayIcon.ActivationReason.DoubleClick
            else None
        )
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()
        self.refresh_library(True)
        self.navigate(0)
        self.apply_tips()
        self.statusBar().showMessage("Pronto. Escolha uma janela e inicie a captura.")
        self._preview_tick = 0

    def home_page(self):
        page = Page(
            "Se passou na tela, pode virar história.",
            "Leve como um pato, rápido como um clique.",
        )
        self.status_label = label("○  CAPTURA PARADA", "eyebrow")
        page.body.addWidget(self.status_label)
        hero = card()
        hero.setObjectName("hero")
        row = QHBoxLayout(hero)
        row.setContentsMargins(30, 22, 25, 22)
        text = QVBoxLayout()
        text.addWidget(label("UM CLIQUE. UM BOM MOMENTO.", "eyebrow"))
        text.addWidget(label("Pronto para\ncapturar?", "heroTitle"))
        text.addWidget(
            label(
                "Seu replay fica esperando por você.\nAperte o atalho e guarde o que acabou de acontecer.",
                "muted",
                True,
            )
        )
        text.addSpacing(12)
        actions = QHBoxLayout()
        self.home_start = button("Iniciar captura  →", self.start_capture, True)
        actions.addWidget(self.home_start)
        actions.addWidget(button("Escolher janela", lambda: self.navigate(1)))
        text.addLayout(actions)
        row.addLayout(text, 3)
        art = MascotLabel(mascot("Duck", 420), 190)
        art.setMaximumWidth(300)
        row.addWidget(art, 2)
        page.body.addWidget(hero)
        stats = QHBoxLayout()
        self.summary = {}
        for key, title in [
            ("key", "ATALHO DO CLIPE"),
            ("duration", "REPLAY"),
            ("quality", "QUALIDADE"),
            ("fps", "QUADROS POR SEGUNDO"),
        ]:
            frame = card()
            col = QVBoxLayout(frame)
            col.setContentsMargins(18, 17, 18, 17)
            col.addWidget(label(title, "tiny"))
            value = label("—", "value")
            col.addWidget(value)
            self.summary[key] = value
            stats.addWidget(frame)
        page.body.addLayout(stats)
        header = QHBoxLayout()
        header.addWidget(label("Seus últimos momentos", "subheading"))
        header.addStretch()
        header.addWidget(button("Todos os clipes", lambda: self.navigate(6), True))
        header.addWidget(
            button("Importar no editor", lambda: self.editor.import_video())
        )
        page.body.addLayout(header)
        self.library = QListWidget()
        self.library.setMinimumHeight(150)
        self.library.itemDoubleClicked.connect(self.open_item)
        page.body.addWidget(self.library, 1)
        controls = QHBoxLayout()
        controls.addWidget(button("Editar selecionado", self.edit_item))
        controls.addWidget(button("Reproduzir / abrir", self.open_item))
        controls.addStretch()
        self.total_label = label("Nenhum clipe salvo ainda", "tiny")
        controls.addWidget(self.total_label)
        page.body.addLayout(controls)
        self.home_tip = Tip(
            "GuardDuck",
            "Seus clipes ficam no computador. Você escolhe o que capturar e quando começar.",
        )
        page.body.addWidget(self.home_tip)
        return page

    def capture_page(self):
        page = Page(
            "Escolha o que merece ficar.",
            "Selecione uma janela. O replay só começa quando você clicar em Iniciar captura.",
        )
        self.capture_error = label("", "captureError", True)
        self.capture_error.setTextFormat(Qt.TextFormat.PlainText)
        self.capture_error.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        page.body.addWidget(self.capture_error)
        self.capture_error.hide()
        self.copy_error = button("Copiar diagnóstico", self.copy_capture_error)
        page.body.addWidget(self.copy_error)
        self.copy_error.hide()
        frame = card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 22, 24, 22)
        row = QHBoxLayout()
        row.addWidget(label("JANELA SELECIONADA", "eyebrow"))
        row.addStretch()
        self.refresh_button = button("Atualizar janelas", self.refresh_windows)
        row.addWidget(self.refresh_button)
        layout.addLayout(row)
        self.windows = QComboBox()
        self.windows.setMinimumHeight(45)
        layout.addWidget(self.windows)
        grid = QGridLayout()
        self.duration = QComboBox()
        for seconds in DURATIONS:
            self.duration.addItem(
                {
                    15: "15 segundos",
                    30: "30 segundos",
                    60: "1 minuto",
                    90: "1 min e 30 s",
                    120: "2 minutos",
                }[seconds],
                seconds,
            )
        self.duration.setCurrentIndex(DURATIONS.index(self.settings.duration))
        self.fps = QComboBox()
        self.fps.addItems([str(fps) for fps in FPS])
        self.fps.setCurrentText(str(self.settings.fps))
        self.quality = QComboBox()
        self.quality.addItems(PROFILES)
        self.quality.setCurrentText(self.settings.quality)
        for i, (title, control) in enumerate(
            [
                ("Duração do replay", self.duration),
                ("Qualidade", self.quality),
                ("FPS desejados", self.fps),
            ]
        ):
            grid.addWidget(label(title, "muted"), 0, i)
            grid.addWidget(control, 1, i)
        layout.addLayout(grid)
        self.system_audio = QCheckBox(
            "Capturar áudio do sistema (inclui outras aplicações)"
        )
        self.system_audio.setChecked(self.settings.system_audio)
        layout.addWidget(self.system_audio)
        self.cursor = QCheckBox("Mostrar cursor na captura")
        self.cursor.setChecked(self.settings.cursor)
        layout.addWidget(self.cursor)
        self.capture_note = label(
            "Windows Graphics Capture · melhor resultado com jogos em janela sem bordas. Janelas minimizadas ou conteúdo protegido podem não fornecer quadros.",
            "tiny",
            True,
        )
        layout.addWidget(self.capture_note)
        row = QHBoxLayout()
        self.start_button = button("Iniciar captura", self.start_capture, True)
        self.stop_button = button("Parar", self.stop_capture)
        self.stop_button.setEnabled(False)
        self.clip_button = button("Salvar últimos segundos", self.save_clip)
        self.clip_button.setEnabled(False)
        self.print_button = button("Tirar print", self.screenshot)
        self.print_button.setEnabled(False)
        for b in [
            self.start_button,
            self.stop_button,
            self.clip_button,
            self.print_button,
        ]:
            row.addWidget(b)
        layout.addLayout(row)
        page.body.addWidget(frame)
        self.progress = QProgressBar()
        self.progress.setRange(0, self.settings.duration)
        self.progress.setValue(0)
        self.progress.setFormat("Buffer preenchido: %v s")
        page.body.addWidget(self.progress)
        self.engine_label = label("Nenhuma janela sendo capturada.", "muted", True)
        page.body.addWidget(self.engine_label)
        self.preview = QLabel("A prévia aparece aqui após iniciar.")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(200)
        self.preview.setMaximumHeight(280)
        self.preview.setStyleSheet(
            "background:#080b10;border:1px solid #2a303b;border-radius:10px;color:#707d91;"
        )
        page.body.addWidget(self.preview, 1)
        self.capture_tip = Tip(
            "SpeedDuck",
            "Comece com 30 ou 60 FPS. Full preserva a resolução da janela com compressão de alta qualidade; FPS altos exigem mais GPU, memória e disco.",
        )
        page.body.addWidget(self.capture_tip)
        for combo in [self.duration, self.fps, self.quality]:
            combo.currentIndexChanged.connect(self.capture_settings)
        self.system_audio.toggled.connect(self.capture_settings)
        self.cursor.toggled.connect(self.capture_settings)
        self.refresh_windows()
        return page

    def settings_page(self):
        page = Page(
            "No seu ritmo.",
            "Atalhos, desempenho e pastas. Nada de assinatura ou conta.",
        )
        frame = card()
        layout = QGridLayout(frame)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)
        self.clip_key = QKeySequenceEdit(QKeySequence(self.settings.clip_key))
        self.print_key = QKeySequenceEdit(QKeySequence(self.settings.screenshot_key))
        layout.addWidget(label("Salvar replay", "muted"), 0, 0)
        layout.addWidget(self.clip_key, 0, 1)
        layout.addWidget(label("Tirar screenshot", "muted"), 1, 0)
        layout.addWidget(self.print_key, 1, 1)
        layout.addWidget(button("Aplicar atalhos", self.apply_hotkeys), 2, 1)
        self.encoder = QComboBox()
        self.encoder.addItems(
            ["Automático", "h264_nvenc", "h264_qsv", "h264_amf", "libx264"]
        )
        self.encoder.setCurrentText(self.settings.encoder)
        self.encoder.currentTextChanged.connect(self.set_encoder)
        layout.addWidget(label("Codificador de vídeo", "muted"), 3, 0)
        layout.addWidget(self.encoder, 3, 1)
        self.tip_check = QCheckBox("Mostrar dicas dos mascotes")
        self.tip_check.setChecked(self.settings.tips)
        self.tip_check.toggled.connect(self.toggle_tips)
        layout.addWidget(self.tip_check, 4, 0, 1, 2)
        layout.addWidget(label("Pasta de clipes", "muted"), 5, 0)
        self.clips_path = label(self.settings.clips_dir, "muted", True)
        layout.addWidget(self.clips_path, 5, 1)
        layout.addWidget(button("Escolher pasta", self.choose_clips), 6, 1)
        layout.addWidget(label("FFmpeg e ffprobe", "muted"), 7, 0)
        self.ffmpeg_label = label(self.media.ffmpeg or "Não encontrado", "tiny", True)
        layout.addWidget(self.ffmpeg_label, 7, 1)
        layout.addWidget(button("Selecionar pasta do FFmpeg", self.choose_ffmpeg), 8, 1)
        self.motion_check = QCheckBox("Animações suaves e brilho acompanhando o mouse")
        self.motion_check.setChecked(self.settings.motion)
        self.motion_check.toggled.connect(self.toggle_motion)
        layout.addWidget(self.motion_check, 9, 0, 1, 2)
        page.body.addWidget(frame)
        row = QHBoxLayout()
        row.addWidget(
            button(
                "Abrir dados e logs",
                lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(data_dir()))),
            )
        )
        row.addWidget(button("Limpar replay temporário", self.clean_buffer))
        row.addWidget(button("Minimizar para a bandeja", self.to_tray))
        row.addStretch()
        page.body.addLayout(row)
        self.settings_tip = Tip(
            "ProfDuck",
            "O primeiro uso precisa de Python 3.12, dependências e FFmpeg. Depois disso, captura, editor e músicas locais funcionam sem conexão.",
        )
        page.body.addWidget(self.settings_tip)
        page.body.addStretch()
        return page

    def save_settings(self):
        try:
            self.settings.save()
        except OSError as error:
            self.notify("Não foi possível salvar as configurações: " + str(error))
        if hasattr(self, "summary"):
            values = dict(
                key=self.settings.clip_key,
                duration=f"{self.settings.duration}s",
                quality=self.settings.quality,
                fps=str(self.settings.fps),
            )
            for key, value in values.items():
                self.summary[key].setText(value)

    def capture_settings(self, *_):
        self.settings.duration = self.duration.currentData()
        self.settings.fps = int(self.fps.currentText())
        self.settings.quality = self.quality.currentText()
        self.settings.system_audio = self.system_audio.isChecked()
        self.settings.cursor = self.cursor.isChecked()
        self.save_settings()

    def set_encoder(self, value):
        self.settings.encoder = value
        self.save_settings()

    def refresh_windows(self):
        current = self.windows.currentData()
        self.windows.clear()
        if not IS_WINDOWS:
            self.windows.addItem("Seleção de janela disponível no Windows", None)
            return
        for hwnd, title in list_windows():
            self.windows.addItem(title, hwnd)
        if not self.windows.count():
            self.windows.addItem(
                "Nenhuma janela encontrada — abra seu jogo ou aplicativo", None
            )
        index = self.windows.findData(current)
        if index >= 0:
            self.windows.setCurrentIndex(index)

    def start_capture(self):
        if self.engine.active or self.engine.starting:
            self.navigate(1)
            return
        target = self.windows.currentData()
        if not target:
            self.navigate(1)
            self.notify(
                "Escolha uma janela aberta na página Capturar. A captura requer Windows."
            )
            return
        try:
            self.inputs.reset()
            self.capture_settings()
            self.capture_error.hide()
            self.copy_error.hide()
            self.preview.clear()
            self.preview.setText("Preparando a janela e o codificador…")
            self.navigate(1)
            self.engine.start(target, self.settings)
            self.progress.setRange(0, 0)
            self.engine_label.setText(
                "Aguardando o primeiro quadro. O replay ainda não começou."
            )
            self.status_label.setText("◌  PREPARANDO CAPTURA")
            self.set_capture_controls(True)
        except Exception as error:
            self.show_capture_error(str(error))

    def set_capture_controls(self, running):
        for control in [
            self.windows,
            self.refresh_button,
            self.duration,
            self.fps,
            self.quality,
            self.system_audio,
            self.cursor,
            self.encoder,
        ]:
            control.setEnabled(not running)
        self.start_button.setEnabled(not running)
        self.home_start.setText("Ver captura →" if running else "Iniciar captura →")
        self.home_start.setEnabled(True)
        self.stop_button.setText(
            "Cancelar preparação" if self.engine.starting else "Parar captura"
        )
        self.stop_button.setEnabled(running)
        self.clip_button.setEnabled(self.engine.active)
        self.print_button.setEnabled(self.engine.active)

    def stop_capture(self):
        self.engine.stop()
        self.stop_button.setEnabled(False)
        self.input_timer.stop()
        self.status_label.setText("◌  FINALIZANDO CAPTURA")

    def save_clip(self):
        try:
            self.engine.save_clip(self.settings)
        except Exception as error:
            self.notify(str(error))

    def screenshot(self):
        try:
            self.engine.screenshot()
        except Exception as error:
            self.notify(str(error))

    def tick(self):
        while True:
            try:
                kind, message = self.engine.events.get_nowait()
            except queue.Empty:
                break
            if kind == "started":
                self.status_label.setText(
                    "●  REPLAY ATIVO"
                    + (" · SEM ÁUDIO" if self.engine.audio_warning else "")
                )
                self.engine_label.setText(
                    message
                    + f" · Salve com {self.settings.clip_key} ou Salvar últimos segundos."
                )
                self.progress.setRange(0, self.engine.settings.duration)
                self.set_capture_controls(True)
                self.input_timer.start()
                self.tray.setToolTip("DuckCapture — gravando a janela selecionada")
            elif kind == "stopped":
                self.status_label.setText(
                    "FALHA NA CAPTURA" if self.engine.error else "○  CAPTURA PARADA"
                )
                self.progress.setRange(0, self.settings.duration)
                self.progress.setValue(0)
                if not self.engine.error:
                    self.engine_label.setText(message)
                self.set_capture_controls(False)
                self.input_timer.stop()
                self.tray.setToolTip("DuckCapture — captura parada")
            elif kind == "preparing":
                self.engine_label.setText(message)
            elif kind == "capture_error":
                self.show_capture_error(message)
            elif kind == "warning":
                self.show_capture_error(message, warning=True)
                if self.engine.active:
                    self.status_label.setText("●  REPLAY ATIVO · SEM ÁUDIO")
            elif kind == "saving":
                self.clip_button.setEnabled(False)
                self.notify(message)
            elif kind == "saved":
                self.refresh_library(True)
                self.notify("Salvo: " + Path(message).name)
                self.clip_button.setEnabled(self.engine.active)
            elif kind == "error":
                self.notify(message)
                self.clip_button.setEnabled(self.engine.active)
        if self.engine.active:
            self.progress.setMaximum(self.engine.settings.duration)
            self.progress.setValue(
                min(self.engine.settings.duration, int(self.engine.elapsed))
            )
            self._preview_tick += 1
            if self._preview_tick % 4 == 0 and self.stack.currentIndex() == 1:
                from PySide6.QtGui import QImage

                with self.engine.lock:
                    pixels = self.engine.latest
                if pixels is not None:
                    h, w = pixels.shape[:2]
                    image = QImage(
                        pixels.data,
                        w,
                        h,
                        pixels.strides[0],
                        QImage.Format.Format_ARGB32,
                    ).copy()
                    self.preview.setPixmap(
                        QPixmap.fromImage(image).scaled(
                            self.preview.size(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.FastTransformation,
                        )
                    )

    def sample_inputs(self):
        if self.engine.active and self.settings.hud_enabled:
            self.hud_sampling = True
            self.engine.sample(
                self.inputs.sample(
                    self.engine.hwnd, self.engine.elapsed, self.music_title
                )
            )
        elif self.engine.active and self.hud_sampling:
            # End a held key state when recording of HUD inputs is disabled.
            self.engine.sample(
                dict(keys=[], buttons=[], cursor=[0.5, 0.5], cps=0, music="")
            )
            self.hud_sampling = False

    def set_music(self, title):
        self.music_title = title

    def navigate(self, index):
        previous = self.stack.currentIndex()
        if self.fade_overlay:
            self.fade_animation.stop()
            self.fade_overlay.deleteLater()
            self.fade_overlay = None
        # Fade a static page snapshot, never attach opacity effects to native
        # video/web views. No animation or extra rendering while idle.
        snapshot = (
            self.stack.grab()
            if (
                self.isVisible()
                and motion_enabled()
                and previous != index
                and previous not in (2, 4)
                and index not in (2, 4)
            )
            else None
        )
        self.stack.setCurrentIndex(index)
        self.stack.currentWidget().verticalScrollBar().setValue(0)
        self.stack.currentWidget().horizontalScrollBar().setValue(0)
        for i, button_ in self.nav.items():
            button_.setChecked(i == index)
        if snapshot:
            overlay = QLabel(self.stack)
            overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            overlay.setPixmap(snapshot)
            overlay.setGeometry(self.stack.rect())
            effect = QGraphicsOpacityEffect(overlay)
            overlay.setGraphicsEffect(effect)
            self.fade_animation = QPropertyAnimation(effect, b"opacity", overlay)
            self.fade_animation.setDuration(190)
            self.fade_animation.setStartValue(1.0)
            self.fade_animation.setEndValue(0.0)
            self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.fade_animation.finished.connect(self.finish_fade)
            self.fade_overlay = overlay
            overlay.show()
            overlay.raise_()
            self.fade_animation.start()
        if index != 2 and hasattr(self, "editor"):
            self.editor.player.pause()
        self.save_settings()

    def finish_fade(self):
        if self.fade_overlay:
            self.fade_overlay.deleteLater()
            self.fade_overlay = None

    def show_capture_error(self, message, warning=False):
        self.capture_error.setText(
            ("AVISO DE ÁUDIO\n" if warning else "NÃO FOI POSSÍVEL MANTER A CAPTURA\n")
            + message
        )
        self.capture_error.show()
        self.copy_error.show()
        if not warning:
            self.status_label.setText("FALHA NA CAPTURA")
            self.engine_label.setText("Confira o diagnóstico acima e tente novamente.")
            self.progress.setRange(0, self.settings.duration)
            self.progress.setValue(0)
        self.notify(message)

    def copy_capture_error(self):
        text = f"DuckCapture {__version__}\n{self.capture_error.text()}\nCodificador: {self.settings.encoder} | {self.settings.fps} FPS | {self.settings.quality}"
        QApplication.clipboard().setText(text)
        self.notify("Diagnóstico copiado. Você pode colar a mensagem para pedir ajuda.")

    def notify(self, text):
        self.last_toast = text
        self.statusBar().showMessage(text, 16000)
        logging.info(text)
        if hasattr(self, "tray") and not self.isVisible():
            self.tray.showMessage(
                "DuckCapture", text, QSystemTrayIcon.MessageIcon.Information, 4500
            )

    def refresh_library(self, force=False):
        try:
            paths = sorted(
                (
                    p
                    for p in self.settings.clip_folder().iterdir()
                    if p.suffix.lower() in (".mp4", ".mkv", ".png")
                ),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            snapshot = [(str(p), p.stat().st_size, p.stat().st_mtime) for p in paths]
        except OSError as error:
            self.notify(str(error))
            return
        if not force and snapshot == self.file_snapshot:
            return
        self.file_snapshot = snapshot
        self.gallery.refresh(snapshot)
        self.library.clear()
        for path, size, mtime in snapshot[:12]:
            p = Path(path)
            item = QListWidgetItem(
                f"{p.name}\n{size / 1024**2:.1f} MB  ·  {time.strftime('%d/%m · %H:%M', time.localtime(mtime))}"
            )
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setIcon(vector_icon("image" if p.suffix.lower() == ".png" else "play"))
            self.library.addItem(item)
        if not snapshot:
            item = QListWidgetItem(
                "Seu primeiro clipe mora aqui.\nInicie a captura e aperte "
                + self.settings.clip_key
                + "."
            )
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.library.addItem(item)
        self.total_label.setText(
            f"{len(snapshot)} arquivos · {sum(s[1] for s in snapshot) / 1024**2:.1f} MB locais"
        )

    def selected_path(self):
        item = self.library.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def open_item(self, *_):
        path = self.selected_path()
        if path:
            ClipViewer(path, self).exec()

    def edit_item(self):
        path = self.selected_path()
        if not path or Path(path).suffix == ".png":
            self.notify("Selecione um vídeo da biblioteca para editar.")
            return
        self.edit_path(path)

    def edit_path(self, path):
        self.editor.load(path)
        self.navigate(2)

    def open_clips(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.settings.clip_folder())))

    def choose_clips(self):
        path = QFileDialog.getExistingDirectory(
            self, "Pasta dos clipes", self.settings.clips_dir
        )
        if path:
            self.settings.clips_dir = path
            self.clips_path.setText(path)
            self.save_settings()
            self.refresh_library(True)

    def choose_ffmpeg(self):
        if self.engine.active or self.engine.starting or self.engine.pending:
            self.notify(
                "Pare a captura e aguarde as exportações antes de trocar o FFmpeg."
            )
            return
        path = QFileDialog.getExistingDirectory(self, "Pasta com ffmpeg e ffprobe")
        if path:
            candidate = Media(path)
            try:
                candidate.require()
            except Exception as error:
                self.notify(str(error))
                return
            self.settings.ffmpeg_dir = path
            self.media = candidate
            self.engine.media = candidate
            self.editor.media = candidate
            self.gallery.media = candidate
            self.ffmpeg_label.setText(candidate.ffmpeg)
            self.save_settings()

    def bind_hotkeys(self):
        self.hotkeys.update(
            {
                self.settings.clip_key: self.save_clip,
                self.settings.screenshot_key: self.screenshot,
            }
        )

    def apply_hotkeys(self):
        old = (self.settings.clip_key, self.settings.screenshot_key)
        self.settings.clip_key = self.clip_key.keySequence().toString(
            QKeySequence.SequenceFormat.PortableText
        )
        self.settings.screenshot_key = self.print_key.keySequence().toString(
            QKeySequence.SequenceFormat.PortableText
        )
        try:
            if self.settings.clip_key == self.settings.screenshot_key:
                raise ValueError("Escolha atalhos diferentes para clipe e print.")
            self.bind_hotkeys()
            self.save_settings()
            self.refresh_library(True)
            self.notify(
                "Atalhos atualizados."
                if IS_WINDOWS
                else "Atalhos salvos; o registro global funciona no Windows."
            )
        except ValueError as error:
            self.settings.clip_key, self.settings.screenshot_key = old
            self.notify(str(error))

    def toggle_motion(self, value):
        self.settings.motion = value
        QApplication.instance().setProperty("duckMotion", value)
        if not value:
            self.music.vinyl.timer.stop()
            self.finish_fade()
        self.save_settings()

    def toggle_tips(self, value):
        self.settings.tips = value
        self.apply_tips()
        self.save_settings()

    def apply_tips(self):
        for tip in self.findChildren(Tip):
            tip.setVisible(self.settings.tips)

    def show_mascots(self):
        from PySide6.QtWidgets import QDialog

        dialog = QDialog(self)
        dialog.setWindowTitle("A turma DuckCapture")
        dialog.resize(650, 650)
        layout = QVBoxLayout(dialog)
        layout.addWidget(label("Uma turma. Muitos bons momentos.", "heading"))
        grid = QGridLayout()
        for i, name in enumerate(CHARACTERS):
            tile = QVBoxLayout()
            art = MascotLabel(mascot(name, 220), 130)
            art.setMaximumHeight(145)
            tile.addWidget(art)
            title = label(name, "tipName")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tile.addWidget(title)
            grid.addLayout(tile, i // 3, i % 3)
        layout.addLayout(grid)
        layout.addWidget(button("Fechar", dialog.accept, True))
        dialog.exec()

    def clean_buffer(self):
        if (
            self.engine.active
            or self.engine.starting
            or self.engine.pending
            or self.engine.thread
            and self.engine.thread.is_alive()
        ):
            self.notify(
                "Pare a captura e aguarde o salvamento dos clipes antes de limpar."
            )
            return
        root = data_dir() / "buffer"
        count = 0
        try:
            for folder in root.glob("replay-*"):
                if folder.is_dir() and not folder.is_symlink():
                    shutil.rmtree(folder)
                    count += 1
            self.notify(
                f"{count} pastas de replay temporário removidas. Seus clipes salvos foram preservados."
            )
        except OSError as error:
            self.notify(str(error))

    def to_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.notify("A bandeja do sistema não está disponível.")
            return
        self.hide()
        self.tray.showMessage(
            "DuckCapture",
            "O aplicativo continua aberto na bandeja. Clique duas vezes no patinho para voltar.",
        )

    def show_normal(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        if self.engine.pending or self.editor.task and self.editor.task.isRunning():
            self.notify("Aguarde a exportação terminar antes de sair.")
            event.ignore()
            return
        if self.engine.active or self.engine.starting:
            if (
                QMessageBox.question(
                    self,
                    "Parar captura?",
                    "Parar o replay e sair do DuckCapture? Os últimos segundos não salvos serão descartados.",
                )
                != QMessageBox.StandardButton.Yes
            ):
                event.ignore()
                return
        self.timer.stop()
        self.input_timer.stop()
        self.music.player.stop()
        self.music.spotify_panel.close_player()
        self.music.watch.stop()
        self.library_timer.stop()
        self.gallery.timer.stop()
        self.editor.player.stop()
        self.engine.shutdown()
        self.hotkeys.clear()
        self.tray.hide()
        self.save_settings()
        event.accept()


def main():
    QApplication.setApplicationName("DuckCapture")
    QApplication.setOrganizationName("DuckCapture")
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    lock = QLockFile(str(data_dir() / "application.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(0):
        QMessageBox.information(
            None,
            "DuckCapture",
            "O DuckCapture já está aberto. Procure o patinho na bandeja do Windows.",
        )
        return 0
    logging.basicConfig(
        filename=data_dir() / "duckcapture.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    try:
        window = MainWindow()
    except Exception as error:
        logging.exception("Erro ao iniciar")
        QMessageBox.critical(
            None,
            "DuckCapture",
            f"Não foi possível iniciar: {error}\nConsulte duckcapture.log na pasta de dados.",
        )
        return 1
    window.show()
    return app.exec()
