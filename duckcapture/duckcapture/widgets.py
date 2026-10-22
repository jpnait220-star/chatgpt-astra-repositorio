from __future__ import annotations
from PySide6.QtCore import Qt, QRect, QRectF, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QPainter, QColor, QLinearGradient, QPainterPath
from PySide6.QtWidgets import (
    QLabel,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)
from .config import ROOT
from .visuals import GlowButton, GlowFrame, MascotLabel, motion_enabled, icon
from .theme import current_palette

CHARACTERS = {
    "Duck": 0,
    "EditDuck": 1,
    "KeyDuck": 2,
    "ClickDuck": 3,
    "MusicDuck": 4,
    "ProfDuck": 5,
    "SettingDuck": 6,
    "SpeedDuck": 7,
    "GuardDuck": 8,
}


def mascot(name="Duck", height=180):
    if name == "Duck" and (ROOT / "assets/duck.png").exists():
        return QPixmap(str(ROOT / "assets/duck.png")).scaled(
            height,
            height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    grid = QPixmap(str(ROOT / "assets/mascots-grid.png"))
    if not grid.isNull():
        index = CHARACTERS.get(name, 0)
        column = index % 3
        row = index // 3
        left = round(column * grid.width() / 3)
        right = round((column + 1) * grid.width() / 3)
        # The generated atlas has asymmetric row gutters; keep every foot,
        # headphone and accessory inside its own tile.
        rows = (0, 440 / 1254, 850 / 1254, 1)
        top = round(rows[row] * grid.height())
        bottom = round(rows[row + 1] * grid.height())
        return grid.copy(QRect(left, top, right - left, bottom - top)).scaled(
            height,
            height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    return QPixmap(str(ROOT / "assets/duck.png")).scaledToHeight(
        height, Qt.TransformationMode.SmoothTransformation
    )


def label(text, role="body", wrap=False):
    item = QLabel(text)
    item.setObjectName(role)
    item.setWordWrap(wrap)
    return item


def button(text, callback=None, primary=False):
    clean = text
    symbol = None
    for glyph, name in [('⏮', 'previous'), ('⏭', 'next'), ('⏯', 'play'), ('▶', 'play')]:
        if glyph in clean:
            clean = clean.replace(glyph, '').strip()
            symbol = name
    for prefix, name in [('Importar', 'folder'), ('+ Importar', 'folder'), ('Exportar', 'export'), ('Desfazer', 'undo'), ('Dividir', 'editor'), ('Remover', 'trash'), ('Colar link', 'link'), ('Criar link', 'link')]:
        if clean.startswith(prefix):
            symbol = name
            clean = clean.removeprefix('+ ')
            break
    item = GlowButton(clean)
    if symbol:
        item.setProperty("duckVectorIcon", symbol)
        item.setIcon(icon(symbol, current_palette()['dark_text'] if primary else '#cbd4e6'))
    item.setObjectName("primary" if primary else "button")
    item.setCursor(Qt.CursorShape.PointingHandCursor)
    if callback:
        item.clicked.connect(callback)
    return item


def card():
    frame = GlowFrame()
    frame.setObjectName("card")
    return frame


class Tip(QFrame):
    def __init__(self, mascot_name, text):
        super().__init__()
        self.setObjectName("tip")
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 6, 16, 6)
        art = MascotLabel(mascot(mascot_name, 100), 76)
        art.setFixedSize(76, 76)
        row.addWidget(art)
        col = QVBoxLayout()
        col.addWidget(label(mascot_name, "tipName"))
        col.addWidget(label(text, "muted", True))
        row.addLayout(col, 1)


class Page(QWidget):
    def __init__(self, title, subtitle):
        super().__init__()
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(30, 22, 30, 22)
        self.body.setSpacing(18)
        self.body.addWidget(label(title, "heading"))
        self.body.addWidget(label(subtitle, "subtitle", True))


STYLE = """
* { font-family: "Manrope"; font-size: 13px; color: #eef0f6; }
QWidget { background: transparent; }
QMainWindow { background: #030405; }
QWidget#shell, QFrame#workspace { background: transparent; }
QDialog { background: #08090c; }
QFrame#sidebar { background: #08090b; border-right: 1px solid #1c1e24; }
QFrame#topbar { background: #07080b; border-bottom: 1px solid #1c1e24; }
QLabel#brand { font-size: 21px; font-weight: 800; }
QLabel#heading { font-size: 27px; font-weight: 800; }
QLabel#heroTitle { font-size: 32px; font-weight: 800; }
QLabel#subheading, QLabel#cardHeading { font-size: 17px; font-weight: 700; }
QLabel#eyebrow, QLabel#cardEyebrow { color: #b9c0cf; font-size: 10px; font-weight: 700; }
QLabel#subtitle, QLabel#muted { color: #a0a5b2; font-size: 12px; }
QLabel#tiny { color: #858c9b; font-size: 10px; }
QLabel#value { font-size: 26px; font-weight: 800; }
QLabel#tipName { font-weight: 700; }
QLabel#topStatus { background: #101216; border: 1px solid #292d36; border-radius: 15px; padding: 9px 12px; font-size: 12px; }
QLabel#topDescription, QLabel#cardAction { color: #adb5c5; font-size: 11px; }
QLabel#hotkeyTag { background: #191c23; border: 1px solid #373d49; border-bottom: 3px solid #333945; border-radius: 10px; padding: 5px 9px; font-size: 11px; font-weight: 800; }
QPushButton { background: #15171d; border: 1px solid #2b2f39; border-radius: 15px; padding: 10px 15px; font-weight: 600; }
QPushButton:hover { background: #20242d; border-color: #626a7b; }
QPushButton:pressed { background: #2b303d; }
QPushButton:disabled { color: #676e7c; border-color: #1e222b; background: #101216; }
QPushButton#primary { background: #f3d768; color: #171713; border-color: #fff3c9; font-weight: 800; }
QPushButton#primary:hover { background: #ffeb9e; }
QPushButton#primary:disabled { background: #414754; color: #a6adbb; border-color: #414754; }
QPushButton#nav { background: transparent; border: 1px solid transparent; text-align: left; padding: 13px 14px; color: #a0a7b7; }
QPushButton#nav:checked { background: #2e2b20; color: #fff3c9; border-color: #544b2e; }
QPushButton#nav:hover { background: #181b22; border-color: #323846; }
QPushButton#topNav { padding: 5px; border-radius: 13px; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QKeySequenceEdit { background: #0d0f14; border: 1px solid #303440; border-radius: 13px; padding: 9px 11px; min-height: 20px; selection-background-color: #3b4354; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QKeySequenceEdit:focus { border-color: #858d9f; }
QComboBox { padding-right: 25px; }
QComboBox::drop-down { width: 24px; border: none; }
QComboBox::down-arrow { image: url(@down@); width: 11px; height: 11px; }
QSpinBox::up-button, QDoubleSpinBox::up-button { subcontrol-origin: border; subcontrol-position: top right; width: 22px; border: none; border-top-right-radius: 13px; background: transparent; }
QSpinBox::down-button, QDoubleSpinBox::down-button { subcontrol-origin: border; subcontrol-position: bottom right; width: 22px; border: none; border-bottom-right-radius: 13px; background: transparent; }
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow { image: url(@up@); width: 9px; height: 9px; }
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow { image: url(@down@); width: 9px; height: 9px; }

QComboBox QAbstractItemView { background: #11141a; border: 1px solid #3a414e; border-radius: 14px; padding: 7px; selection-background-color: #2c3340; outline: none; }
QComboBox QAbstractItemView::item { min-height: 28px; border-radius: 8px; padding: 4px 9px; }
QListWidget, QTableWidget { background: #090b10; border: 1px solid #242936; border-radius: 17px; padding: 7px; outline: none; }
QListWidget::item { padding: 10px; border: 1px solid transparent; border-radius: 13px; margin: 3px; }
QListWidget::item:hover { background: #181c25; border-color: #414957; }
QListWidget::item:selected { background: #222936; color: #ffffff; border-color: #657085; }
QHeaderView::section { background: #141820; border: none; padding: 9px; color: #a0a7b7; }
QSlider { min-height: 28px; }
QSlider::groove:horizontal { background: #262c38; height: 6px; border-radius: 3px; }
QSlider::sub-page:horizontal { background: #f3d768; border-radius: 3px; }
QSlider::handle:horizontal { background: #fff3c9; width: 18px; margin: -6px 0; border-radius: 9px; }
QCheckBox { spacing: 9px; }
QCheckBox::indicator { width: 18px; height: 18px; background: #171c25; border: 1px solid #515c70; border-radius: 8px; }
QCheckBox::indicator:checked { background: #f3d768; border: 3px solid #655b3a; }
QScrollArea, QTabWidget::pane { border: none; }
QTabBar::tab { background: #10141b; color: #9ba4b6; border: 1px solid #2b3240; border-radius: 14px; padding: 11px 18px; margin: 2px 6px 8px 0; }
QTabBar::tab:selected { background: #242c39; color: #ffffff; border-color: #58647a; }
QTabBar::tab:hover { color: #ffffff; border-color: #667086; }
QScrollBar:vertical { background: transparent; width: 13px; margin: 0; border: none; }
QScrollBar:horizontal { background: transparent; height: 13px; margin: 0; border: none; }
QScrollBar::handle:vertical { min-height: 38px; }
QScrollBar::handle:horizontal { min-width: 38px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; border: none; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
QToolTip { background: #202632; color: #fff; border: 1px solid #515d73; padding: 8px; border-radius: 10px; }
QProgressBar { border: 1px solid #303744; border-radius: 13px; background: #10141c; min-height: 26px; text-align: center; }
QProgressBar::chunk { background: #f3d768; border-radius: 12px; }
QLabel#captureError { background: #27151d; color: #ffc2ce; border: 1px solid #67414e; padding: 14px; border-radius: 16px; }
QStatusBar { background: #07090d; color: #929dad; }
QMessageBox { background: #11151c; }
QMenu { background: #141922; border: 1px solid #3b4658; border-radius: 14px; padding: 6px; }
QMenu::item { padding: 9px 20px; border-radius: 9px; }
QMenu::item:selected { background: #293344; }
QMenu::separator { height: 1px; background: #343d4b; margin: 6px 12px; }
QFrame#tip, QFrame#card, QFrame#hero, QFrame#readyHudSection { background: #0e1117; border: 1px solid #282e39; border-radius: 20px; }
QFrame#backdropCard { background: #10151e; border: none; border-radius: 18px; }
QFrame#accentSwatch { border: 1px solid #515d73; border-radius: 12px; }
QFrame#readyHudSection QCheckBox { padding: 9px; }
QSplitter::handle { background: transparent; width: 10px; }
"""
STYLE = STYLE.replace('@down@', '"' + (ROOT / 'assets/icons/chevron-down.svg').as_posix() + '"').replace('@up@', '"' + (ROOT / 'assets/icons/chevron-up.svg').as_posix() + '"')


class BackdropCard(QFrame):
    """Cinematic native card; static image is drawn only on paint/resize."""
    def __init__(self, image_name, eyebrow, heading, destination):
        super().__init__()
        self.setObjectName("backdropCard")
        self.setMinimumHeight(154)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.destination = destination
        self.hover_level = 0.0
        self.hover_effect = QVariantAnimation(self)
        self.hover_effect.setDuration(200)
        self.hover_effect.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.hover_effect.valueChanged.connect(self.set_hover_level)
        self.image = QPixmap(str(ROOT / 'assets' / 'banners' / (image_name + '.webp')))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 15, 13)
        layout.setSpacing(3)
        hint = label(eyebrow.upper(), 'cardEyebrow')
        title = label(heading, 'cardHeading', True)
        action = label('Explorar  →', 'cardAction')
        layout.addWidget(hint)
        layout.addWidget(title)
        layout.addStretch(1)
        layout.addWidget(action)
        from .fold_hover import add_fold_hover
        add_fold_hover(self)

    def set_hover_level(self, value):
        self.hover_level = float(value)
        self.update()

    def _set_hover(self, level):
        self.hover_effect.stop()
        if not motion_enabled():
            self.set_hover_level(level)
        else:
            self.hover_effect.setStartValue(self.hover_level)
            self.hover_effect.setEndValue(level)
            self.hover_effect.start()

    def enterEvent(self, event):
        self._set_hover(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._set_hover(0.0)
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(rect), 18, 18)
        painter.setClipPath(clip)
        if not self.image.isNull():
            # Cropping rather than stretching retains the intended subject.
            scaled = self.image.scaled(rect.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            offset = (scaled.width() - rect.width()) // 2
            oy = (scaled.height() - rect.height()) // 2
            painter.drawPixmap(rect.topLeft(), scaled, scaled.rect().adjusted(offset, oy, -offset, -oy))
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor(3, 7, 17, 245))
        gradient.setColorAt(.48, QColor(3, 7, 17, 143))
        gradient.setColorAt(1, QColor(3, 7, 17, 122))
        painter.fillRect(rect, gradient)
        tint = QColor(current_palette()['accent'])
        tint.setAlpha(round(27 * self.hover_level))
        painter.fillRect(rect, tint)
        edge = QColor(current_palette()['accent']) if self.hover_level > 0 else QColor('#354354')
        edge.setAlpha(round(90 + 125 * self.hover_level))
        painter.setPen(edge)
        painter.drawRoundedRect(rect, 18, 18)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.destination()
        super().mouseReleaseEvent(event)
