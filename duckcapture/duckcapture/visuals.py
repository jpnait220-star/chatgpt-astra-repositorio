"""Small native Qt effects: animate only while interacting, never an idle render loop."""

from functools import lru_cache
from PySide6.QtCore import (
    Qt,
    QRectF,
    QPointF,
    QSize,
    QEvent,
    QVariantAnimation,
    QEasingCurve,
    QByteArray,
)
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPainterPath,
    QLinearGradient,
    QRadialGradient,
    QPen,
    QPixmap,
    QIcon,
    QFontMetrics,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication, QPushButton, QFrame, QLabel


PATHS = {
    "home": '<path d="m3 10 9-7 9 7v10H3z"/><path d="M9 20v-7h6v7"/>',
    "capture": '<rect x="3" y="4" width="18" height="14" rx="3"/><circle cx="12" cy="11" r="3"/><path d="M8 21h8"/>',
    "editor": '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="m8 8 12 12M8 16 20 4"/>',
    "hud": '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M3 9h18M9 9v12"/>',
    "music": '<path d="M9 18V5l11-2v13M9 9l11-2"/><ellipse cx="6" cy="18" rx="3" ry="2"/><ellipse cx="17" cy="16" rx="3" ry="2"/>',
    "settings": '<path d="M4 6h16M4 12h16M4 18h16"/><circle cx="8" cy="6" r="2"/><circle cx="16" cy="12" r="2"/><circle cx="10" cy="18" r="2"/>',
    "library": '<rect x="4" y="6" width="17" height="15" rx="3"/><path d="M17 3H5a3 3 0 0 0-3 3v10m8-6 6 4-6 4z"/>',
    "folder": '<path d="M3 7V5h7l2 3h9v12H3z"/>',
    "play": '<path d="m8 5 12 7-12 7z"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8" cy="8" r="1.5"/><path d="m3 17 5-5 4 4 4-6 5 7"/>',
}


@lru_cache(maxsize=32)
def icon(name, color="#c4c6d0"):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{PATHS.get(name, PATHS["capture"])}</g></svg>'
    pixmap = QPixmap(48, 48)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    QSvgRenderer(QByteArray(svg.encode())).render(painter, QRectF(3, 3, 42, 42))
    painter.end()
    return QIcon(pixmap)


def motion_enabled():
    app = QApplication.instance()
    return bool(app is None or app.property("duckMotion") is not False)


class GlowButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)
        self.setMinimumHeight(42)
        self.hover = 0.0
        self.press = 0.0
        self.pointer = QPointF(0, 0)
        self.hover_animation = QVariantAnimation(self)
        self.hover_animation.setDuration(170)
        self.hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.hover_animation.valueChanged.connect(self.hover_changed)
        self.pulse = QVariantAnimation(self)
        self.pulse.setDuration(320)
        self.pulse.setStartValue(1.0)
        self.pulse.setEndValue(0.0)
        self.pulse.valueChanged.connect(self.press_changed)
        self.clicked.connect(self.clicked_effect)

    def sizeHint(self):
        hint = super().sizeHint()
        return QSize(
            max(
                hint.width(),
                self.fontMetrics().horizontalAdvance(self.text())
                + 40
                + (27 if not self.icon().isNull() else 0),
            ),
            max(42, hint.height()),
        )

    def hover_changed(self, value):
        self.hover = float(value)
        self.update()

    def press_changed(self, value):
        self.press = float(value)
        self.update()

    def animate_hover(self, target):
        self.hover_animation.stop()
        if not motion_enabled():
            self.hover = target
            self.update()
            return
        self.hover_animation.setStartValue(self.hover)
        self.hover_animation.setEndValue(target)
        self.hover_animation.start()

    def enterEvent(self, event):
        self.pointer = QPointF(self.width() / 2, self.height() / 2)
        self.animate_hover(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animate_hover(0.0)
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        self.pointer = event.position()
        self.update()
        super().mouseMoveEvent(event)

    def clicked_effect(self):
        if motion_enabled():
            self.pulse.stop()
            self.pulse.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        enabled = self.isEnabled()
        primary = self.objectName() == "primary"
        nav = self.objectName() == "nav"
        selected = self.isChecked()
        rect = QRectF(self.rect()).adjusted(1.5, 2, -1.5, -2)
        path = QPainterPath()
        path.addRoundedRect(rect, 10, 10)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        if primary:
            gradient.setColorAt(0, QColor("#f7e9ad" if enabled else "#3a3830"))
            gradient.setColorAt(1, QColor("#e7c963" if enabled else "#292822"))
        else:
            gradient.setColorAt(
                0,
                QColor("#25252a" if selected else "#1c1d23" if not nav else "#101115"),
            )
            gradient.setColorAt(
                1,
                QColor("#18191d" if selected else "#14151a" if not nav else "#101115"),
            )
        painter.fillPath(path, gradient)
        painter.save()
        painter.setClipPath(path)
        if enabled and self.hover:
            shine = QRadialGradient(self.pointer, max(80, self.width() * 0.68))
            shine.setColorAt(
                0, QColor(255, 255, 255, round((50 if primary else 32) * self.hover))
            )
            shine.setColorAt(1, QColor(255, 255, 255, 0))
            painter.fillRect(rect, shine)
        if self.press:
            painter.fillRect(rect, QColor(255, 255, 255, round(45 * self.press)))
        painter.restore()
        edge = QColor(
            "#fff4ce"
            if primary and enabled
            else "#625941"
            if selected
            else "#45464f"
            if self.hover > 0.3
            else "#2d2f38"
        )
        edge.setAlpha(255 if enabled else 110)
        painter.setPen(QPen(edge, 1))
        painter.drawPath(path)
        if nav and selected:
            painter.setPen(QPen(QColor("#f4db83"), 3))
            painter.drawLine(
                QPointF(2, rect.center().y() - 7), QPointF(2, rect.center().y() + 7)
            )
        dx = (
            (self.pointer.x() - self.width() / 2)
            / max(1, self.width() / 2)
            * 2.4
            * self.hover
            if motion_enabled()
            else 0
        )
        dy = (
            (self.pointer.y() - self.height() / 2)
            / max(1, self.height() / 2)
            * 1.4
            * self.hover
            if motion_enabled()
            else 0
        )
        painter.translate(dx, dy + (0.7 if self.isDown() else 0))
        content = rect.adjusted(15, 0, -15, 0)
        painter.setPen(
            QColor(
                "#201d14"
                if primary and enabled
                else "#f6f6f9"
                if enabled
                else "#666974"
            )
        )
        font = self.font()
        font.setBold(primary or selected)
        painter.setFont(font)
        if not self.icon().isNull():
            self.icon().paint(
                painter, int(content.left()), int(rect.center().y() - 10), 20, 20
            )
            content.setLeft(content.left() + 30)
        text = QFontMetrics(font).elidedText(
            self.text(), Qt.TextElideMode.ElideRight, max(1, int(content.width()))
        )
        painter.drawText(
            content,
            (Qt.AlignmentFlag.AlignLeft if nav else Qt.AlignmentFlag.AlignHCenter)
            | Qt.AlignmentFlag.AlignVCenter,
            text,
        )
        if self.hasFocus():
            painter.setPen(QPen(QColor("#eee2ad"), 1, Qt.PenStyle.DotLine))
            painter.drawRoundedRect(rect.adjusted(3, 3, -3, -3), 8, 8)


class GlowFrame(QFrame):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.pointer = QPointF(-500, -500)

    def event(self, event):
        if event.type() == QEvent.Type.HoverMove:
            self.pointer = event.position()
            self.update()
        elif event.type() == QEvent.Type.HoverLeave:
            self.pointer = QPointF(-500, -500)
            self.update()
        return super().event(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.7, 0.7, -0.7, -0.7)
        path = QPainterPath()
        path.addRoundedRect(rect, 16, 16)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor("#1b1c21"))
        gradient.setColorAt(1, QColor("#111216"))
        p.fillPath(path, gradient)
        p.save()
        p.setClipPath(path)
        if self.objectName() == "hero":
            light = QRadialGradient(
                QPointF(self.width() * 0.82, self.height() * 0.43), self.height() * 0.8
            )
            light.setColorAt(0, QColor(243, 216, 134, 24))
            light.setColorAt(1, QColor(243, 216, 134, 0))
            p.fillRect(rect, light)
            p.setPen(QPen(QColor(255, 255, 255, 11), 1))
            for radius in (100, 139):
                p.drawEllipse(
                    QPointF(self.width() * 0.82, self.height() * 0.47), radius, radius
                )
            for x, y in ((0.68, 0.23), (0.94, 0.63)):
                point = QPointF(self.width() * x, self.height() * y)
                p.setPen(QPen(QColor(255, 245, 205, 110), 1))
                p.drawLine(point - QPointF(4, 0), point + QPointF(4, 0))
                p.drawLine(point - QPointF(0, 4), point + QPointF(0, 4))
        if motion_enabled() and self.underMouse():
            light = QRadialGradient(self.pointer, 230)
            light.setColorAt(0, QColor(255, 255, 255, 17))
            light.setColorAt(1, QColor(255, 255, 255, 0))
            p.fillRect(rect, light)
        p.restore()
        p.setPen(QPen(QColor("#383a43"), 1))
        p.drawPath(path)


class MascotLabel(QLabel):
    """Retain the full pixmap and always fit it to the available bounds."""

    def __init__(self, pixmap, size=180):
        super().__init__()
        self.original = pixmap
        self.setMinimumSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def sizeHint(self):
        return self.minimumSize()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        pix = self.original.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        p.drawPixmap(
            (self.width() - pix.width()) // 2, (self.height() - pix.height()) // 2, pix
        )
