"""Small rounded color picker; changes are committed only after confirmation."""
import re
from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QLinearGradient, QPen
from PySide6.QtWidgets import QDialog, QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QSlider, QLineEdit, QPushButton
from .widgets import label, button


class ColorPlane(QFrame):
    changed = Signal(QColor)

    def __init__(self):
        super().__init__()
        self.hue, self.saturation, self.value = 0., 0., 1.
        self.setMinimumHeight(190)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setAccessibleName('Saturação e brilho da cor')

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        mask = QPainterPath(); mask.addRoundedRect(r, 14, 14)
        painter.setClipPath(mask)
        painter.fillRect(r, QColor.fromHsvF(self.hue, 1, 1))
        white = QLinearGradient(r.topLeft(), r.topRight())
        white.setColorAt(0, QColor('white')); white.setColorAt(1, QColor(255, 255, 255, 0))
        painter.fillRect(r, white)
        black = QLinearGradient(r.topLeft(), r.bottomLeft())
        black.setColorAt(0, QColor(0, 0, 0, 0)); black.setColorAt(1, QColor('black'))
        painter.fillRect(r, black)
        point = QPointF(r.left() + self.saturation * r.width(), r.top() + (1 - self.value) * r.height())
        painter.setClipping(False)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor('#14161a'), 4)); painter.drawEllipse(point, 6, 6)
        painter.setPen(QPen(QColor('white'), 2)); painter.drawEllipse(point, 6, 6)

    def pick(self, point):
        r = self.rect().adjusted(2, 2, -2, -2)
        self.saturation = max(0., min(1., (point.x() - r.left()) / max(1, r.width())))
        self.value = 1 - max(0., min(1., (point.y() - r.top()) / max(1, r.height())))
        self.changed.emit(QColor.fromHsvF(self.hue, self.saturation, self.value))
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton: self.pick(event.position())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton: self.pick(event.position())


class ColorDialog(QDialog):
    def __init__(self, initial, parent=None, title='Escolha sua cor'):
        super().__init__(parent)
        self.setObjectName("roundedColorDialog")
        self.setStyleSheet("QDialog#roundedColorDialog { background: transparent; }")
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(430)
        self.color = QColor(initial)
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0)
        frame = QFrame(); frame.setObjectName('colorDialogSurface')
        frame.setStyleSheet('QFrame#colorDialogSurface { background:#0e1014; border:1px solid #343842; border-radius:24px; }')
        root.addWidget(frame)
        content = QVBoxLayout(frame); content.setContentsMargins(25, 24, 25, 24); content.setSpacing(16)
        content.addWidget(label('SEU ESTILO', 'eyebrow'))
        content.addWidget(label(title, 'subheading'))
        self.plane = ColorPlane(); self.plane.changed.connect(self.set_color)
        content.addWidget(self.plane)
        self.hue = QSlider(Qt.Orientation.Horizontal); self.hue.setRange(0, 359)
        self.hue.setAccessibleName('Matiz')
        self.hue.setStyleSheet('QSlider::sub-page:horizontal { background:transparent; } QSlider::groove:horizontal { height:10px; border-radius:5px; background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #ff4141,stop:0.17 #ffe342,stop:0.33 #49e97c,stop:0.5 #52e5ed,stop:0.67 #5d74f6,stop:0.83 #e25ff1,stop:1 #ff4141); }')
        self.hue.valueChanged.connect(self.set_hue); content.addWidget(self.hue)
        values = QHBoxLayout()
        self.swatch = QFrame(); self.swatch.setFixedSize(46, 46); values.addWidget(self.swatch)
        self.hex = QLineEdit(); self.hex.setMaxLength(7); self.hex.setAccessibleName('Cor hexadecimal')
        self.hex.textEdited.connect(self.hex_edited); values.addWidget(self.hex, 1)
        content.addLayout(values)
        presets = QGridLayout(); presets.setSpacing(10)
        for index, value in enumerate(('#f4f6fb', '#c9d5eb', '#a6b0c0', '#646c7d', '#090b10', '#bba9fa', '#88baff', '#83e5e0', '#a4e5b2', '#f1cf8b', '#eda4ad', '#edb8df')):
            chip = QPushButton(); chip.setFixedSize(42, 32); chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.setAccessibleName(value); chip.setToolTip(value)
            chip.setStyleSheet(f'QPushButton {{ background:{value}; border:2px solid #343842; border-radius:15px; padding:0; }} QPushButton:hover {{ border-color:white; }}')
            chip.clicked.connect(lambda checked=False, color=value: self.set_color(QColor(color)))
            presets.addWidget(chip, index // 6, index % 6)
        content.addLayout(presets)
        actions = QHBoxLayout(); actions.addWidget(button('Cancelar', self.reject)); self.confirm = button('Usar esta cor', self.accept, True); actions.addWidget(self.confirm)
        content.addLayout(actions)
        self.set_color(self.color)

    def set_color(self, color):
        if not color.isValid(): return
        self.color = QColor(color)
        self.confirm.setEnabled(True)
        hue, saturation, value, _ = self.color.getHsvF()
        if hue >= 0: self.plane.hue = hue
        self.plane.saturation, self.plane.value = saturation, value
        self.hue.blockSignals(True); self.hue.setValue(round(self.plane.hue * 359)); self.hue.blockSignals(False)
        self.hex.setText(self.color.name().upper())
        self.hex.setStyleSheet('')
        self.swatch.setStyleSheet(f'background:{self.color.name()};border:1px solid #454a55;border-radius:15px;')
        self.plane.update()

    def set_hue(self, hue):
        self.plane.hue = hue / 359
        self.set_color(QColor.fromHsvF(self.plane.hue, self.plane.saturation, self.plane.value))

    def hex_edited(self, text):
        if re.fullmatch(r'#[0-9a-fA-F]{6}', text):
            self.set_color(QColor(text))
        else:
            self.confirm.setEnabled(False)
            self.hex.setStyleSheet('border-color:#d28088;')

    @staticmethod
    def getColor(initial, parent=None, title='Escolha sua cor'):
        dialog = ColorDialog(initial, parent, title)
        return dialog.color if dialog.exec() == QDialog.DialogCode.Accepted else QColor()
