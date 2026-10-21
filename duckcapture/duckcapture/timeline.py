"""A trim range and playhead on a real time axis; no synthetic waveform."""
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class TrimTimeline(QWidget):
    trimmed = Signal(float, float)
    seeked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.duration = self.start = self.end = self.position = 0.
        self.drag = None
        self.setMinimumHeight(74)
        self.setAccessibleName("Intervalo do trecho; ajuste também pelos campos Início e Fim")
        self.setToolTip("Arraste as pontas para cortar. Clique no centro para escolher o momento.")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_range(self, duration, start, end):
        self.duration, self.start, self.end = duration, start, end
        self.update()

    def set_position(self, milliseconds):
        self.position = milliseconds / 1000
        self.update()

    def x_at(self, seconds):
        return 15 + max(0, min(1, seconds / max(.001, self.duration))) * (self.width() - 30)

    def time_at(self, x):
        return max(0, min(1, (x - 15) / max(1, self.width() - 30))) * self.duration

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor('#151b25'))
        p.drawRoundedRect(QRectF(10, 27, self.width()-20, 34), 12, 12)
        if self.duration <= 0:
            p.setPen(QColor('#8d98ab'))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 'Importe um vídeo para começar')
            return
        left, right = self.x_at(self.start), self.x_at(self.end)
        p.setBrush(QColor('#3a465e'))
        p.drawRoundedRect(QRectF(left, 27, max(3, right-left), 34), 9, 9)
        p.setPen(QColor('#8794a8'))
        for i in range(5):
            t = self.duration * i / 4
            x = self.x_at(t)
            p.drawText(QRectF(x-25, 2, 50, 20), Qt.AlignmentFlag.AlignCenter, f'{int(t)//60:02}:{int(t)%60:02}')
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor('#eff4ff'))
        for x in (left, right):
            p.drawRoundedRect(QRectF(x-5, 28, 10, 32), 5, 5)
        p.setPen(QPen(QColor('#aacbff'), 2))
        x = self.x_at(self.position)
        p.drawLine(int(x), 24, int(x), 65)

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or self.duration <= 0:
            return
        x = event.position().x()
        dl, dr = abs(x-self.x_at(self.start)), abs(x-self.x_at(self.end))
        self.drag = 'start' if dl <= dr and dl < 12 else 'end' if dr < 12 else 'seek'
        self.mouseMoveEvent(event)

    def mouseMoveEvent(self, event):
        t = self.time_at(event.position().x())
        if self.drag == 'start':
            self.start = min(t, max(0, self.end-.05))
        elif self.drag == 'end':
            self.end = max(t, min(self.duration, self.start+.05))
        elif self.drag == 'seek':
            self.seeked.emit(round(t*1000))
        self.update()

    def mouseReleaseEvent(self, event):
        if self.drag in ('start', 'end'):
            self.trimmed.emit(self.start, self.end)
        self.drag = None
