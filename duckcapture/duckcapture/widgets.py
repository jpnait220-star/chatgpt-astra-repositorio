from __future__ import annotations
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QLabel,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)
from .config import ROOT
from .visuals import GlowButton, GlowFrame, MascotLabel

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
    item = GlowButton(text)
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
* { font-family: "Segoe UI", "DejaVu Sans"; font-size: 13px; color: #eeeeef; }
QMainWindow, QWidget#shell { background: #090a0d; }
QWidget { background: transparent; }
QDialog { background: #101115; }
QFrame#sidebar { background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #14151a,stop:1 #0c0d11); border-right: 1px solid #30313a; }
QFrame#tip { background: #1b1c17; border: 1px solid #3b3929; border-radius: 12px; }
QLabel#brand { color: #faf7ed; font-size: 18px; font-weight: 700; }
QLabel#heading { font-size: 29px; font-weight: 700; color: #f4f4f4; }
QLabel#heroTitle { font-size: 38px; font-weight: 700; color: #faf7ed; }
QLabel#subheading { font-size: 17px; font-weight: 600; }
QLabel#eyebrow { color: #ddd3b2; font-size: 10px; font-weight: 600; }
QLabel#subtitle, QLabel#muted { color: #979ba5; font-size: 12px; }
QLabel#tiny { color: #707784; font-size: 10px; }
QLabel#value { font-size: 27px; font-weight: 600; }
QLabel#tipName { color: #e7cf7d; font-size: 11px; font-weight: 600; }
QPushButton { background: #20242b; border: 1px solid #363b46; border-radius: 8px; padding: 10px 15px; }
QPushButton:hover { background: #2a303a; border-color: #555d6d; }
QPushButton:pressed { background: #343c48; }
QPushButton:disabled { color: #656b77; border-color: #292d35; background: #191c22; }
QPushButton#primary { background: #f3d768; color: #171713; border: 1px solid #ffeb9e; font-weight: 700; }
QPushButton#primary:hover { background: #ffe691; }
QPushButton#primary:disabled { background: #514b34; color: #aaa084; border-color: #5a5235; }
QPushButton#nav { background: transparent; border: none; text-align: left; padding: 13px 14px; color: #999fab; }
QPushButton#nav:checked { background: #2e2b20; color: #f3da82; border: 1px solid #4b422c; }
QPushButton#nav:hover { background: #20242b; }
QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox,QKeySequenceEdit { background: #101319; border: 1px solid #363c47; border-radius: 7px; padding: 8px; min-height: 20px; }
QComboBox QAbstractItemView { background: #1b2029; border: 1px solid #414957; selection-background-color: #544b2e; }
QListWidget,QTableWidget { background: #11151b; border: 1px solid #2e3541; border-radius: 9px; padding: 6px; }
QListWidget::item { padding: 10px; border-bottom: 1px solid #202630; }
QListWidget::item:selected { background: #383326; color: #f9de82; border-radius: 4px; }
QHeaderView::section { background: #1a1f27; border: none; padding: 8px; color: #8d96a6; }
QSlider::groove:horizontal { background: #343b47; height: 5px; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #f0d268; border-radius: 2px; }
QSlider::handle:horizontal { background: #ffeaa4; width: 16px; margin: -6px 0; border-radius: 8px; border: 1px solid #fff3c9; }
QSlider { min-height: 25px; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; background: #242a34; border: 1px solid #535d6d; border-radius: 4px; }
QCheckBox::indicator:checked { background: #e0c360; border-color: #ffeea4; }
QScrollArea { border: none; }
QTabWidget::pane { border: none; }
QTabBar::tab { background:#14151a; color:#999da8; border:1px solid #30323c; border-radius:8px; padding:12px 28px; margin-right:8px; }
QTabBar::tab:selected { background:#29271f; color:#f6e5b0; border-color:#655b3a; }
QTabBar::tab:hover { color:#ffffff; border-color:#626571; }
QScrollBar:vertical { background: transparent; width: 8px; }
QScrollBar::handle:vertical { background: #3b424f; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical { height: 0; }
QToolTip { background: #252b34; color: #fff; border: 1px solid #515c6c; padding: 7px; }
QProgressBar { border:1px solid #383a43; border-radius:7px; background:#101116; min-height:25px; text-align:center; }
QProgressBar::chunk { background:#b3a46c; border-radius:6px; }
QLabel#captureError { background:#2b181c; color:#ffb6bb; border:1px solid #674047; padding:14px; border-radius:10px; }
QStatusBar { background: #101319; color: #8994a5; }
QMessageBox { background: #151920; }
QMenu { background: #181d25; border: 1px solid #3c4553; }
QMenu::item { padding: 8px 18px; }
QMenu::item:selected { background: #393426; }
"""
