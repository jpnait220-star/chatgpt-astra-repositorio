from __future__ import annotations
import logging
import queue
import shutil
import sys
import time
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QUrl, QLockFile, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QDesktopServices, QPixmap, QKeySequence, QColor, QImage
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
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
    QSlider,
    QSystemTrayIcon,
    QMenu,
    QKeySequenceEdit,
    QLabel,
    QGraphicsOpacityEffect,
    QPushButton,
)
from .config import Settings, data_dir, DURATIONS, FPS, PROFILES, ROOT
from .widgets import STYLE, Page, Tip, card, label, button, mascot, CHARACTERS, BackdropCard
from .theme import PRESETS, theme_style, current_palette
from .visuals import (
    MascotLabel,
    icon as vector_icon,
    motion_enabled,
    ExpandButton,
    FadeNavButton,
)
from .window_picker import WindowPicker, WindowCombo
from .sounds import CaptureSounds
from .gallery import GalleryPage, ClipViewer
from . import __version__
from .media import Media
from .capture import CaptureEngine
from .windows import IS_WINDOWS, list_windows, Hotkeys, InputSampler
from .music import MusicPage
from .hud_editor import HudEditor
from .fold_hover import add_fold_hover, install_interactive_motion
from .wallpaper import VideoBackground
from .editor import EditorPage
from .color_picker import ColorDialog
from .typography import install_font
from .rounded import PopupRounder, install_rounded_controls


class MainWindow(QMainWindow):
    def __init__(self, settings=None):
        super().__init__()
        install_font()
        app = QApplication.instance()
        if not hasattr(app, '_duck_popup_rounder'):
            app._duck_popup_rounder = PopupRounder(app)
            app.installEventFilter(app._duck_popup_rounder)
        install_interactive_motion()
        self.settings = settings or Settings.load()
        QApplication.instance().setProperty("duckMotion", self.settings.motion)
        QApplication.instance().setProperty("duckAccent", self.settings.accent_color)
        self.fade_overlay = None
        self.media = Media(self.settings.ffmpeg_dir)
        self.engine = CaptureEngine(self.media)
        self.sounds = CaptureSounds(self, self.settings)
        self.setWindowTitle("DuckCapture")
        screen = QApplication.primaryScreen().availableGeometry()
        self.setMinimumSize(1000, 640)
        self.resize(min(1360, screen.width() - 40), min(930, screen.height() - 60))
        self.setWindowIcon(QIcon(str(ROOT / "assets" / "brand-icon.png")))
        self.apply_theme(update=False)
        self.music_title = ""
        self.file_snapshot = []
        self.inputs = InputSampler()
        self.hud_sampling = False
        self.last_toast = ""
        shell = VideoBackground()
        self.wallpaper = shell
        shell.dim = self.settings.wallpaper_dim
        shell.failed.connect(self.notify)
        shell.preparing.connect(self.notify)
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
        brand.setSpacing(11)
        logo = QLabel()
        logo.setObjectName("brandIcon")
        logo.setFixedSize(39, 39)
        logo.setPixmap(QPixmap(str(ROOT / "assets" / "brand-icon.png")).scaled(
            39, 39, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
        brand.addWidget(logo, 0, Qt.AlignmentFlag.AlignVCenter)
        brand.addWidget(label("DuckCapture", "brand"), 0, Qt.AlignmentFlag.AlignVCenter)
        nav.addLayout(brand)
        nav.addWidget(label("CAPTURE. EDITE. SALVE.", "tiny"))
        nav.addSpacing(19)
        nav.addWidget(label("SEU ESTÚDIO", "tiny"))
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
            b = ExpandButton(title, symbol, 196)
            b.clicked.connect(lambda checked=False, i=index: self.navigate(i))
            b.setObjectName("nav")
            b.setCheckable(True)
            nav.addWidget(b, 0, Qt.AlignmentFlag.AlignLeft)
            self.nav[index] = b
        nav.addStretch()
        nav.addWidget(label("SEUS MOMENTOS. SEU CONTROLE.", "eyebrow"))
        nav.addWidget(
            label(
                "Clipes ficam no PC. Só vão ao Catbox quando você escolhe criar um link.",
                "muted",
                True,
            )
        )
        nav.addSpacing(15)
        nav.addWidget(label(f"DUCKCAPTURE     {__version__} · ALPHA", "tiny"))
        row.addWidget(sidebar)
        workspace = QFrame()
        workspace.setObjectName("workspace")
        work_layout = QVBoxLayout(workspace)
        work_layout.setContentsMargins(0, 0, 0, 0)
        work_layout.setSpacing(0)
        self.history = []
        self.history_index = -1
        self.topbar = self.make_topbar()
        work_layout.addWidget(self.topbar)
        work_layout.addWidget(self.stack, 1)
        row.addWidget(workspace, 1)
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
            lambda: self.engine.active or self.engine.pending > 0 or self.engine.starting,
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
        install_rounded_controls(self)
        self.music.trackChanged.connect(self.set_music)
        self.editor.exported.connect(lambda _: self.refresh_library(True))
        self.hotkeys = Hotkeys()
        QApplication.instance().installNativeEventFilter(self.hotkeys)
        try:
            self.bind_hotkeys()
        except ValueError as error:
            self.notify(str(error))
        self.timer = QTimer(self)
        self.timer.setInterval(100)
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
        self._last_preview_source = None
        self._status_tick = 0
        self.wallpaper.set_video(self.settings.wallpaper_path)

    def make_topbar(self):
        bar = QFrame()
        bar.setObjectName("topbar")
        bar.setFixedHeight(68)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)
        self.back_button = FadeNavButton("←")
        self.forward_button = FadeNavButton("→")
        for b, cb, tooltip in [
            (self.back_button, self.go_back, "Voltar"),
            (self.forward_button, self.go_forward, "Avançar"),
        ]:
            b.setObjectName("topNav")
            b.setToolTip(tooltip)
            b.setFixedSize(36, 36)
            b.clicked.connect(cb)
            b.setEnabled(False)
            layout.addWidget(b, 0, Qt.AlignmentFlag.AlignVCenter)
        center = QHBoxLayout()
        center.setSpacing(8)
        gamepad = QLabel()
        gamepad.setPixmap(vector_icon("gamepad").pixmap(27, 27))
        gamepad.setToolTip("É aqui que começa a captura do seu jogo")
        center.addWidget(gamepad)
        self.top_status = label("◌  Esperando pelo jogo", "topStatus")
        center.addWidget(self.top_status)
        center.addSpacing(16)
        self.top_clip_key = label(self.settings.clip_key, "hotkeyTag")
        self.top_clip_key.setToolTip("Salvar clipe")
        clip_icon = QLabel()
        clip_icon.setPixmap(vector_icon("clip").pixmap(22, 22))
        clip_icon.setToolTip("Atalho para salvar clipe")
        center.addWidget(clip_icon)
        center.addWidget(self.top_clip_key)
        center.addWidget(label("Clipe", "topDescription"))
        center.addSpacing(8)
        self.top_print_key = label(self.settings.screenshot_key, "hotkeyTag")
        self.top_print_key.setToolTip("Tirar print")
        print_icon = QLabel()
        print_icon.setPixmap(vector_icon("camera").pixmap(22, 22))
        print_icon.setToolTip("Atalho para captura de tela")
        center.addWidget(print_icon)
        center.addWidget(self.top_print_key)
        center.addWidget(label("Print", "topDescription"))
        layout.addStretch(1)
        layout.addLayout(center)
        layout.addStretch(1)
        return bar

    def pulse_status(self):
        if not motion_enabled():
            return
        effect = self.top_status.graphicsEffect()
        if effect is None:
            effect = QGraphicsOpacityEffect(self.top_status)
            self.top_status.setGraphicsEffect(effect)
        if hasattr(self, "status_animation"):
            self.status_animation.stop()
        self.status_animation = QPropertyAnimation(effect, b"opacity", self)
        self.status_animation.setDuration(420)
        self.status_animation.setStartValue(.45)
        self.status_animation.setEndValue(1.0)
        self.status_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.status_animation.start()

    def go_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.navigate(self.history[self.history_index], record=False)

    def go_forward(self):
        if self.history_index + 1 < len(self.history):
            self.history_index += 1
            self.navigate(self.history[self.history_index], record=False)

    def apply_theme(self, update=True):
        QApplication.instance().setProperty("duckAccent", self.settings.accent_color)
        self.setStyleSheet(theme_style(STYLE, self.settings.accent_color))
        if update:
            self.update()
            for element in self.findChildren(QFrame) + self.findChildren(QPushButton):
                symbol = element.property("duckVectorIcon")
                if symbol:
                    tint = current_palette()['dark_text'] if element.objectName() == 'primary' else '#cbd4e6'
                    element.setIcon(vector_icon(symbol, tint))
                element.update()
            self.save_settings()

    def choose_accent(self):
        chosen = ColorDialog.getColor(QColor(self.settings.accent_color), self,
                                      "Escolha a cor do DuckCapture")
        if chosen.isValid():
            self.settings.accent_color = chosen.name()
            self.accent_options.blockSignals(True)
            self.accent_options.setCurrentIndex(self.accent_options.count()-1)
            self.accent_options.blockSignals(False)
            self.apply_theme()

    def select_accent(self, name):
        if name in PRESETS:
            self.settings.accent_color = PRESETS[name]
            self.apply_theme()
        elif name == "Personalizada…":
            self.choose_accent()

    def home_page(self):
        page = Page(
            "Se passou na tela, merece ficar.",
            "Captura rápida, biblioteca organizada e visual mais limpo.",
        )
        self.status_label = label("○  CAPTURA PARADA", "eyebrow")
        page.body.addWidget(self.status_label)
        hero = card()
        hero.setObjectName("hero")
        row = QHBoxLayout(hero)
        row.setContentsMargins(30, 24, 30, 24)
        row.setSpacing(18)
        text = QVBoxLayout()
        text.addWidget(label("DUCKCAPTURE STUDIO", "eyebrow"))
        text.addWidget(label("Replay instantâneo\nsem bagunça.", "heroTitle"))
        text.addWidget(
            label(
                "Escolha a janela, deixe o replay ativo e salve só quando acontecer algo bom.",
                "muted",
                True,
            )
        )
        text.addSpacing(12)
        actions = QHBoxLayout()
        self.home_start = button("Iniciar captura  →", self.start_capture, True)
        add_fold_hover(self.home_start)
        actions.addWidget(self.home_start)
        actions.addWidget(button("Escolher janela", lambda: self.navigate(1)))
        text.addLayout(actions)
        row.addLayout(text, 5)
        hero_art = QLabel()
        hero_art.setObjectName("heroDuck")
        hero_art.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_art.setMinimumSize(160, 190)
        hero_art.setMaximumWidth(255)
        hero_pix = QPixmap(str(ROOT / "assets" / "hero-duck.png"))
        if hero_pix.isNull():
            hero_pix = QPixmap(str(ROOT / "assets" / "brand-icon.png"))
        if not hero_pix.isNull():
            hero_art.setPixmap(hero_pix.scaled(
                215, 190, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
        row.addWidget(hero_art, 2, Qt.AlignmentFlag.AlignVCenter)
        page.body.addWidget(hero)
        section = QHBoxLayout()
        section.addWidget(label("ACESSO RÁPIDO", "eyebrow"))
        section.addStretch()
        section.addWidget(label("Estilo inspirado em apps de clipping", "tiny"))
        page.body.addLayout(section)
        cards = QHBoxLayout()
        cards.setSpacing(12)
        cards.addWidget(BackdropCard("jogos", "Captura", "Escolha um jogo ou app", lambda: self.navigate(1)), 1)
        cards.addWidget(BackdropCard("editor", "Editor", "Ajuste seus melhores momentos", lambda: self.navigate(2)), 1)
        cards.addWidget(BackdropCard("atalhos", "Config", "Qualidade, áudio e aparência", lambda: self.navigate(5)), 1)
        page.body.addLayout(cards)
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
            if key == "quality":
                value.setWordWrap(True)
                value.setStyleSheet("font-size:18px; font-weight:700;")
            self.summary[key] = value
            stats.addWidget(frame)
            add_fold_hover(frame)
        page.body.addLayout(stats)
        header = QHBoxLayout()
        header.addWidget(label("Seus últimos momentos", "subheading"))
        header.addStretch()
        header.addWidget(button("Todos os clipes", lambda: self.navigate(6), True))
        header.addWidget(button("Importar no editor", lambda: self.editor.import_video()))
        page.body.addLayout(header)
        self.library = QListWidget()
        self.library.setMinimumHeight(150)
        self.library.itemDoubleClicked.connect(self.open_item)
        add_fold_hover(self.library, item_view=self.library)
        page.body.addWidget(self.library, 1)
        controls = QHBoxLayout()
        controls.addWidget(button("Editar selecionado", self.edit_item))
        controls.addWidget(button("Reproduzir / abrir", self.open_item))
        controls.addStretch()
        self.total_label = label("Nenhum clipe salvo ainda", "tiny")
        controls.addWidget(self.total_label)
        page.body.addLayout(controls)
        return page

    def capture_page(self):
        page = Page(
            "Configure sua captura.",
            "Escolha a janela, qualidade, FPS, resolução, bitrate e áudio.",
        )
        self.capture_error = label("", "captureError", True)
        self.capture_error.setTextFormat(Qt.TextFormat.PlainText)
        self.capture_error.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
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
        self.refresh_button = button("Escolher janela", self.choose_window, True)
        row.addWidget(self.refresh_button)
        layout.addLayout(row)
        self.windows = WindowCombo()
        self.windows.chooseRequested.connect(self.choose_window)
        self.windows.setMinimumHeight(46)
        layout.addWidget(self.windows)
        grid = QGridLayout()
        self.duration = QComboBox()
        for seconds in DURATIONS:
            self.duration.addItem({15: "15 s", 30: "30 s", 60: "1 min", 90: "1 min 30 s", 120: "2 min"}[seconds], seconds)
        self.duration.setCurrentIndex(DURATIONS.index(self.settings.duration))
        self.fps = QComboBox()
        self.fps.addItems([str(fps) for fps in FPS])
        self.fps.setCurrentText(str(self.settings.fps))
        self.quality = QComboBox()
        self.quality.addItems(PROFILES)
        self.quality.setCurrentText(self.settings.quality)
        self.resolution = QComboBox()
        self.resolution.addItems(["720p", "1080p", "1440p", "4K", "Origem"])
        self.resolution.setCurrentText(getattr(self.settings, "resolution", "1080p"))
        self.bitrate = QComboBox()
        self.bitrate.addItems([f"{value} Mbps" for value in (8, 12, 16, 24, 40, 60, 80, 100)])
        self.bitrate.setCurrentText(f"{getattr(self.settings, 'bitrate_mbps', 16)} Mbps")
        controls = [
            ("Duração", self.duration),
            ("FPS", self.fps),
            ("Qualidade", self.quality),
            ("Resolução", self.resolution),
            ("Bitrate", self.bitrate),
        ]
        for i, (title, control) in enumerate(controls):
            grid.addWidget(label(title, "muted"), 0 if i < 3 else 2, i % 3)
            grid.addWidget(control, 1 if i < 3 else 3, i % 3)
        layout.addLayout(grid)
        audio_row = QGridLayout()
        self.audio_mode = QComboBox()
        self.audio_mode.addItems([
            "Som do PC (jogo, Discord, navegador)",
            "Sem áudio",
        ])
        self.audio_mode.setCurrentText(getattr(self.settings, "audio_mode", "Som do PC (jogo, Discord, navegador)"))
        self.mic_audio = QCheckBox("Microfone (em desenvolvimento)")
        self.mic_audio.setToolTip("A gravação do microfone será adicionada em uma atualização futura.")
        self.mic_audio.setEnabled(False)
        self.mic_audio.setChecked(getattr(self.settings, "microphone_audio", False))
        self.cursor = QCheckBox("Mostrar cursor na captura")
        self.cursor.setChecked(self.settings.cursor)
        audio_row.addWidget(label("Áudio", "muted"), 0, 0)
        audio_row.addWidget(self.audio_mode, 1, 0)
        audio_row.addWidget(self.mic_audio, 1, 1)
        audio_row.addWidget(self.cursor, 1, 2)
        layout.addLayout(audio_row)
        self.f11_mode = QCheckBox("Compatibilidade F11: capturar o monitor quando o jogo estiver em tela cheia")
        self.f11_mode.setChecked(getattr(self.settings, "fullscreen_compatibility", True))
        self.f11_mode.setToolTip("Captura o monitor somente enquanto o jogo selecionado está em primeiro plano. "
                                 "Se o Windows bloquear a imagem, use o modo janela sem bordas.")
        layout.addWidget(self.f11_mode)
        self.capture_note = label(
            "Dica: para maior estabilidade, use 60 FPS ou menos, modo leve ligado e codificador automático. 4K e 120 FPS exigem bastante GPU e disco.",
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
        for b in [self.start_button, self.stop_button, self.clip_button, self.print_button]:
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
        self.source_note = label("", "muted", True)
        self.source_note.hide()
        page.body.addWidget(self.source_note)
        self.action_note = label("F8 salva o replay · F9 tira um print", "eyebrow", True)
        page.body.addWidget(self.action_note)
        self.preview = QLabel("A prévia aparece aqui após iniciar.")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(240)
        self.preview.setMaximumHeight(300)
        self.preview.setStyleSheet("background:#090c11;border:1px solid #252d39;border-radius:14px;color:#8791a2;")
        page.body.addWidget(self.preview, 1)
        for combo in [self.duration, self.fps, self.quality, self.resolution, self.bitrate, self.audio_mode]:
            combo.currentIndexChanged.connect(self.capture_settings)
        self.mic_audio.toggled.connect(self.capture_settings)
        self.cursor.toggled.connect(self.capture_settings)
        self.f11_mode.toggled.connect(self.capture_settings)
        for control in (self.resolution, self.fps, self.quality, self.bitrate, self.duration, self.start_button, self.clip_button):
            add_fold_hover(control)
        self.refresh_windows()
        return page

    def settings_page(self):
        page = Page(
            "Ajustes do aplicativo.",
            "Atalhos, desempenho, aparência e pasta dos clipes.",
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
        self.encoder.addItems(["Automático", "h264_nvenc", "h264_qsv", "h264_amf", "libx264"])
        self.encoder.setCurrentText(self.settings.encoder)
        self.encoder.currentTextChanged.connect(self.set_encoder)
        layout.addWidget(label("Codificador de vídeo", "muted"), 3, 0)
        layout.addWidget(self.encoder, 3, 1)
        self.performance_check = QCheckBox("Modo leve (recomendado)")
        self.performance_check.setChecked(self.settings.performance_mode)
        self.performance_check.toggled.connect(self.toggle_performance)
        layout.addWidget(self.performance_check, 4, 0, 1, 2)
        layout.addWidget(label("Reduz o uso de CPU e memória durante a captura.", "tiny", True), 5, 0, 1, 2)
        self.motion_check = QCheckBox("Animações suaves e brilho nos botões")
        self.motion_check.setChecked(self.settings.motion)
        self.motion_check.toggled.connect(self.toggle_motion)
        layout.addWidget(self.motion_check, 6, 0, 1, 2)
        self.sound_check = QCheckBox("Som ao apertar clipe e ao salvar print")
        self.sound_check.setChecked(self.settings.notification_sounds)
        self.sound_check.toggled.connect(self.toggle_sounds)
        layout.addWidget(self.sound_check, 7, 0, 1, 2)
        self.tip_check = QCheckBox("Mostrar dicas extras")
        self.tip_check.setChecked(self.settings.tips)
        self.tip_check.toggled.connect(self.toggle_tips)
        layout.addWidget(self.tip_check, 8, 0, 1, 2)
        layout.addWidget(label("Pasta de clipes", "muted"), 9, 0)
        self.clips_path = label(self.settings.clips_dir, "muted", True)
        layout.addWidget(self.clips_path, 9, 1)
        layout.addWidget(button("Escolher pasta", self.choose_clips), 10, 1)
        page.body.addWidget(frame)
        colors = card()
        picker = QVBoxLayout(colors)
        picker.setContentsMargins(20, 16, 20, 16)
        picker.addWidget(label("APARÊNCIA", "eyebrow"))
        picker.addWidget(label("Visual dark com brilhos mais claros e menos cores exageradas.", "muted", True))
        color_controls = QHBoxLayout()
        self.accent_options = QComboBox()
        self.accent_options.addItems(list(PRESETS) + ["Personalizada…"])
        match = next((name for name, color in PRESETS.items() if color.lower() == self.settings.accent_color.lower()), "Personalizada…")
        self.accent_options.setCurrentText(match)
        self.accent_options.currentTextChanged.connect(self.select_accent)
        color_controls.addWidget(self.accent_options, 1)
        color_controls.addWidget(button("Escolher qualquer cor", self.choose_accent))
        picker.addLayout(color_controls)
        picker.addWidget(label("PAPEL DE PAREDE EM VÍDEO", "eyebrow"))
        self.wallpaper_name = label(Path(self.settings.wallpaper_path).name if self.settings.wallpaper_path else "Nenhum vídeo selecionado", "muted", True)
        picker.addWidget(self.wallpaper_name)
        self.wallpaper_state = label('Selecione um vídeo para usar como fundo.', 'tiny', True)
        picker.addWidget(self.wallpaper_state)
        self.wallpaper.preparing.connect(self.wallpaper_state.setText)
        self.wallpaper.failed.connect(self.wallpaper_state.setText)
        wallpaper_actions = QHBoxLayout()
        wallpaper_actions.addWidget(button("Escolher vídeo em loop", self.choose_wallpaper))
        wallpaper_actions.addWidget(button("Remover vídeo", lambda: self.set_wallpaper("")))
        picker.addLayout(wallpaper_actions)
        picker.addWidget(label("Vídeos pesados, inclusive 4K, são preparados uma vez para sua tela. Sem som; pausa durante gravação, exportação e ao minimizar. O arquivo original é preservado.", "tiny", True))
        wallpaper_dim = QSlider(Qt.Orientation.Horizontal)
        wallpaper_dim.setRange(35, 95)
        wallpaper_dim.setValue(self.settings.wallpaper_dim)
        wallpaper_dim.setAccessibleName("Escurecer papel de parede")
        dim_text = label(f"Escurecer fundo: {wallpaper_dim.value()}%", "muted")
        def dim_background(value):
            self.settings.wallpaper_dim = value
            self.wallpaper.dim = value
            self.wallpaper.update()
            dim_text.setText(f"Escurecer fundo: {value}%")
            self.save_settings()
        wallpaper_dim.valueChanged.connect(dim_background)
        picker.addWidget(dim_text)
        picker.addWidget(wallpaper_dim)
        page.body.addWidget(colors)
        sound_card = card()
        sound_body = QVBoxLayout(sound_card)
        sound_body.setContentsMargins(20, 16, 20, 16)
        sound_body.addWidget(label("SOM DO CLIPE", "eyebrow"))
        sound_row = QHBoxLayout()
        sound_volume = QSlider(Qt.Orientation.Horizontal)
        sound_volume.setRange(0, 100)
        sound_volume.setValue(round(self.settings.notification_volume * 100))
        sound_volume.setAccessibleName("Volume do som de confirmação")
        sound_level = label(f"{sound_volume.value()}%", "muted")
        def change_volume(value):
            self.settings.notification_volume = value / 100
            sound_level.setText(f"{value}%")
            self.save_settings()
        sound_volume.valueChanged.connect(change_volume)
        sound_row.addWidget(sound_volume, 1)
        sound_row.addWidget(sound_level)
        sound_row.addWidget(button("Ouvir som", self.sounds.queued_clip))
        sound_body.addLayout(sound_row)
        self.clip_chime_check = QCheckBox("Incluir este som perto do final dos clipes salvos")
        self.clip_chime_check.setChecked(self.settings.clip_end_sound)
        def set_clip_chime(value):
            self.settings.clip_end_sound = value
            self.save_settings()
        self.clip_chime_check.toggled.connect(set_clip_chime)
        sound_body.addWidget(self.clip_chime_check)
        sound_body.addWidget(label("Misturado ao áudio do jogo, com o volume acima. A opção também adiciona o som a gravações sem áudio do PC.", "tiny", True))
        page.body.addWidget(sound_card)
        row = QHBoxLayout()
        row.addWidget(button("Abrir dados e logs", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(data_dir())))))
        row.addWidget(button("Limpar replay temporário", self.clean_buffer))
        row.addWidget(button("Minimizar para a bandeja", self.to_tray))
        row.addStretch()
        page.body.addLayout(row)
        page.body.addStretch()
        return page

    def choose_wallpaper(self):
        path, _ = QFileDialog.getOpenFileName(self, "Escolher vídeo de fundo", "", "Vídeos (*.mp4 *.webm *.mkv *.mov)")
        if path:
            self.set_wallpaper(path)

    def set_wallpaper(self, path):
        self.settings.wallpaper_path = path
        self.wallpaper.set_video(path)
        self.wallpaper_name.setText(Path(path).name if path else "Nenhum vídeo selecionado")
        self.wallpaper_state.setText('Carregando a imagem do fundo…' if path else 'Nenhum papel de parede selecionado.')
        self.save_settings()

    def save_settings(self):
        try:
            self.settings.save()
        except OSError as error:
            self.notify("Não foi possível salvar as configurações: " + str(error))
        if hasattr(self, "summary"):
            values = dict(
                key=self.settings.clip_key,
                duration=f"{self.settings.duration}s",
                quality=f"{self.settings.quality} · {getattr(self.settings, 'resolution', '1080p')}",
                fps=str(self.settings.fps),
            )
            for key, value in values.items():
                self.summary[key].setText(value)
        if hasattr(self, "top_clip_key"):
            self.top_clip_key.setText(self.settings.clip_key)
            self.top_print_key.setText(self.settings.screenshot_key)

    def capture_settings(self, *_):
        self.settings.duration = self.duration.currentData()
        self.settings.fps = int(self.fps.currentText())
        self.settings.quality = self.quality.currentText()
        self.settings.resolution = self.resolution.currentText()
        self.settings.bitrate_mbps = int(self.bitrate.currentText().split()[0])
        self.settings.audio_mode = self.audio_mode.currentText()
        self.settings.system_audio = self.settings.audio_mode != "Sem áudio"
        self.settings.microphone_audio = self.mic_audio.isChecked()
        self.settings.cursor = self.cursor.isChecked()
        self.settings.fullscreen_compatibility = self.f11_mode.isChecked()
        self.save_settings()

    def toggle_performance(self, checked):
        self.settings.performance_mode = checked
        self.save_settings()
        if self.engine.active:
            self.notify("O modo leve será aplicado na próxima captura.")

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

    def choose_window(self):
        if self.engine.active or self.engine.starting:
            return
        picker = WindowPicker(self)
        if picker.exec() and picker.selected:
            hwnd, title = picker.selected
            self.refresh_windows()
            index = self.windows.findData(hwnd)
            if index < 0:
                self.windows.addItem(title, hwnd)
                index = self.windows.count() - 1
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
            self.source_note.hide()
            self.preview.clear()
            self._last_preview_source = None
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
            self.audio_mode,
            self.mic_audio,
            self.cursor,
            self.f11_mode,
            self.resolution,
            self.bitrate,
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
        else:
            # Both F8 and the GUI button arrive here. Acknowledgement happens
            # immediately, not when a potentially long export finishes.
            self.sounds.queued_clip()

    def screenshot(self):
        try:
            self.engine.screenshot()
        except Exception as error:
            self.notify(str(error))

    def tick(self):
        self.wallpaper.set_blocked(self.engine.active or self.engine.starting or self.engine.pending > 0 or not self.isVisible() or self.isMinimized() or not self.settings.motion)
        if self.stack.currentIndex() == 3 and self.isVisible():
            state = self.music.hud_state()
            if state.get('music'):
                state.update(t=self.engine.elapsed,capture_fps=self.engine.unique_output_fps,
                             music_phase=(time.monotonic()*48)%360 if state.get('music_playing') else 0)
                self.hud.set_live_state(state)
        while True:
            try:
                kind, message = self.engine.events.get_nowait()
            except queue.Empty:
                break
            if kind == "started":
                self.pulse_status()
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
                self.pulse_status()
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
            elif kind == "source_status":
                self.source_note.setText(message)
                self.source_note.setVisible(bool(message))
            elif kind == "resized":
                self.notify(message)
            elif kind == "performance_warning":
                self.source_note.setText(message)
                self.source_note.show()
                self.statusBar().showMessage(message, 15000)
            elif kind == "queued":
                self.action_note.setText(message)
                self.statusBar().showMessage(message, 4500)
            elif kind == "saving":
                self.action_note.setText(message)
                # Allow F8 and the GUI button to queue more clips.
                self.clip_button.setEnabled(self.engine.active)
            elif kind == "queue_update":
                if message:
                    self.action_note.setText(f"{message} clipe(s) na fila de salvamento")
                elif self.engine.active:
                    self.action_note.setText(
                        f"{self.settings.clip_key} salva o replay · {self.settings.screenshot_key} tira print"
                    )
            elif kind == "saved":
                self.sounds.saved(message)
                self.action_note.setText("SALVO · " + Path(message).name)
                self.refresh_library(True)
                self.notify("Salvo: " + Path(message).name)
                self.clip_button.setEnabled(self.engine.active)
            elif kind == "error":
                self.action_note.setText(message)
                self.notify(message)
                self.clip_button.setEnabled(self.engine.active)
        if self.engine.active:
            self.progress.setMaximum(self.engine.settings.duration)
            self.progress.setValue(
                min(self.engine.settings.duration, int(self.engine.elapsed))
            )
            self._preview_tick += 1
            if self.stack.currentIndex() == 1 and self.isVisible() and not self.isMinimized():
                with self.engine.lock:
                    pixels = self.engine.latest
                if pixels is not None and pixels is not self._last_preview_source:
                    self._last_preview_source = pixels
                    # Only render a new frame; don't scale the same buffer twice.
                    # Limit the conversion work by scaling before copying.
                    h, w = pixels.shape[:2]
                    image = QImage(pixels.data, w, h, pixels.strides[0],
                                   QImage.Format.Format_ARGB32)
                    small = image.scaled(self.preview.size(),
                                         Qt.AspectRatioMode.KeepAspectRatio,
                                         Qt.TransformationMode.FastTransformation).copy()
                    self.preview.setPixmap(QPixmap.fromImage(small))
        self._status_tick += 1
        if self._status_tick >= 10:
            self._status_tick = 0
            hud_music = any(item.get('kind') == 'music' for item in self.settings.hud)
            self.music.spotify_panel.desktop.set_active(
                (hud_music and (self.engine.active and self.settings.hud_enabled or self.stack.currentIndex() == 3))
                or self.stack.currentIndex() == 4 and self.music.tabs.currentIndex() == 1)
            if self.engine.active:
                self.top_status.setText("●  Capturando")
                received = self.engine.source_fps if time.monotonic() - self.engine.last_frame_at < 2.5 else 0
                self.top_status.setText(f"●  Capturando · {self.engine.unique_output_fps:.0f} FPS novos")
                self.top_status.setToolTip(f"Imagens recebidas: {received:.1f} FPS. Imagens novas gravadas: {self.engine.unique_output_fps:.1f} FPS. Saída: {self.engine.output_fps:.1f} FPS. Repetições: {self.engine.repeated_frames}. Meta: {self.engine.settings.fps} FPS.")
            elif self.engine.starting:
                self.top_status.setText("◌  Preparando gravação")
            else:
                self.top_status.setText("◌  Esperando pelo jogo")

    def sample_inputs(self):
        if self.engine.active and self.settings.hud_enabled:
            self.hud_sampling = True
            state = self.inputs.sample(self.engine.hwnd, self.engine.elapsed, self.music_title)
            state.update(self.music.hud_state())
            state['capture_fps'] = self.engine.unique_output_fps
            self.engine.sample(state)
        elif self.engine.active and self.hud_sampling:
            # End a held key state when recording of HUD inputs is disabled.
            self.engine.sample(
                dict(keys=[], buttons=[], cursor=[0.5, 0.5], cps=0, music="")
            )
            self.hud_sampling = False

    def set_music(self, title):
        self.music_title = title

    def navigate(self, index, record=True):
        previous = self.stack.currentIndex()
        if record and (self.history_index < 0 or self.history[self.history_index] != index):
            self.history = self.history[:self.history_index + 1]
            self.history.append(index)
            self.history_index = len(self.history) - 1
        self.back_button.setEnabled(self.history_index > 0)
        self.forward_button.setEnabled(self.history_index + 1 < len(self.history))
        if self.fade_overlay:
            self.fade_animation.stop()
            self.fade_overlay.hide()
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
            self.fade_animation.setDuration(320)
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
        if hasattr(self, "music"):
            self.music.spotify_panel.set_browser_active(index == 4 and self.music.tabs.currentIndex() == 1)
        self.save_settings()

    def finish_fade(self):
        if self.fade_overlay:
            self.fade_overlay.hide()
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

    def toggle_sounds(self, value):
        self.settings.notification_sounds = value
        self.save_settings()

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
        self.wallpaper.shutdown()
        self.timer.stop()
        self.input_timer.stop()
        self.music.player.stop()
        self.music.spotify_panel.shutdown()
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
    if len(sys.argv) == 3 and sys.argv[1] == "--check-installation":
        from .diagnostics import check_installation
        return check_installation(app, sys.argv[2])
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
