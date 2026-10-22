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
from .theme import current_palette
from PySide6.QtWidgets import QApplication, QPushButton, QFrame, QLabel, QWidget


PATHS = {
    "gamepad": '<path d="M7 6h10c3 0 4 3 5 10 .4 3-2 4-4 1l-2-2H8l-2 2c-2 3-4.4 2-4-1C3 9 4 6 7 6Z"/><path d="M6 9v5m-2.5-2.5h5M16 10h.1M19 12h.1"/>',
    "clip": '<rect x="3" y="5" width="18" height="15" rx="4"/><path d="m9 9 6 4-6 4zM7 2h10"/>',
    "camera": '<path d="M8 5 10 2h4l2 3h4a2 2 0 0 1 2 2v12H2V7a2 2 0 0 1 2-2Z"/><circle cx="12" cy="12" r="4"/>',
    "pause": '<path d="M8 5v14M16 5v14"/>',
    "previous": '<path d="m17 5-10 7 10 7ZM4 5v14"/>',
    "next": '<path d="m7 5 10 7-10 7ZM20 5v14"/>',
    "undo": '<path d="m8 3-5 5 5 5M3 8h11a6 6 0 0 1 0 12h-4"/>',
    "trash": '<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7"/>',
    "export": '<path d="M12 15V2m-5 5 5-5 5 5M4 12v8h16v-8"/>',
    "link": '<path d="m10 14 4-4m-6 1-2 2a4 4 0 0 0 5 6l3-3m-4-8 3-3a4 4 0 0 1 6 5l-2 2"/>',
    "home": '<path d="m3 10 9-7 9 7v10H3z"/><path d="M9 20v-7h6v7"/>',
    "capture": '<rect x="3" y="4" width="18" height="14" rx="3"/><circle cx="12" cy="11" r="3"/><path d="M8 21h8"/>',
    "editor": '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="m8 8 12 12M8 16 20 4"/>',
    "hud": '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M3 9h18M9 9v12"/>',
    "music": '<path d="M9 18V5l11-2v13M9 9l11-2"/><ellipse cx="6" cy="18" rx="3" ry="2"/><ellipse cx="17" cy="16" rx="3" ry="2"/>',
    "settings": '<path d="M4 6h16M4 12h16M4 18h16"/><circle cx="8" cy="6" r="2"/><circle cx="16" cy="12" r="2"/><circle cx="10" cy="18" r="2"/>',
    "library": '<rect x="4" y="6" width="17" height="15" rx="3"/><path d="M17 3H5a3 3 0 0 0-3 3v10m8-6 6 4-6 4z"/>',
    "folder": '<path d="M3 7V5h7l2 3h9v12H3z"/>',
    "play": '<path d="m8 5 12 7-12 7z"/>',
    "keyboard": '<rect x="2" y="5" width="20" height="14" rx="3"/><path d="M5 9h2m3 0h2m3 0h2m-12 4h2m3 0h2m3 0h2M7 16h10"/>',
    "mouse": '<rect x="6" y="2" width="12" height="20" rx="6"/><path d="M12 2v8M6 10h12"/>',
    "timer": '<circle cx="12" cy="13" r="8"/><path d="M9 2h6m-3 3v-3m0 7v5l3 2"/>',
    "text": '<path d="M4 4h16M12 4v16M8 20h8M4 4v4m16-4v4"/>',
    "activity": '<path d="M2 12h5l3-8 4 16 3-8h5"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8" cy="8" r="1.5"/><path d="m3 17 5-5 4 4 4-6 5 7"/>',
}


@lru_cache(maxsize=64)
def icon(name, color="#c4c6d0"):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{PATHS.get(name, PATHS["capture"])}</g></svg>'
    pixmap = QPixmap(48, 48)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    QSvgRenderer(QByteArray(svg.encode())).render(painter, QRectF(3, 3, 42, 42))
    painter.end()
    return QIcon(pixmap)


class FadeNavButton(QPushButton):
    """Uses the same perspective and slow return as every clickable control."""
    pass


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
        self.hover_animation.setDuration(180 if target else 650)
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
        colors = current_palette()
        primary = self.objectName() == "primary"
        nav = self.objectName() == "nav"
        selected = self.isChecked()
        rect = QRectF(self.rect()).adjusted(1.5, 2, -1.5, -2)
        path = QPainterPath()
        path.addRoundedRect(rect, 15, 15)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        if primary:
            gradient.setColorAt(0, QColor(colors["bright"] if enabled else "#313641"))
            gradient.setColorAt(1, QColor(colors["accent"] if enabled else "#232832"))
        else:
            gradient.setColorAt(
                0,
                QColor(colors["selected"] if selected else "#1c1d23" if not nav else "#101115"),
            )
            gradient.setColorAt(
                1,
                QColor(colors["selected"] if selected else "#14151a" if not nav else "#101115"),
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
            radius = max(8, (1 - self.press) * max(self.width(), self.height()) * 1.4)
            ripple = QRadialGradient(self.pointer, radius)
            ripple.setColorAt(0, QColor(255, 255, 255, round(12 * self.press)))
            ripple.setColorAt(.72, QColor(255, 255, 255, round(65 * self.press)))
            ripple.setColorAt(1, QColor(255, 255, 255, 0))
            painter.fillRect(rect, ripple)
        painter.restore()
        edge = QColor(
            colors["bright"]
            if primary and enabled
            else colors["muted"]
            if selected
            else "#45464f"
            if self.hover > 0.3
            else "#2d2f38"
        )
        edge.setAlpha(255 if enabled else 110)
        painter.setPen(QPen(edge, 1))
        painter.drawPath(path)
        if nav and selected:
            painter.setPen(QPen(QColor(colors["accent"]), 3))
            painter.drawLine(
                QPointF(2, rect.center().y() - 7), QPointF(2, rect.center().y() + 7)
            )
        content = rect.adjusted(15, 0, -15, 0)
        painter.setPen(
            QColor(
                colors["dark_text"]
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
            painter.setPen(QPen(QColor(colors["accent"]), 1, Qt.PenStyle.DotLine))
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
        gradient.setColorAt(0, QColor("#0b0c10"))
        gradient.setColorAt(1, QColor("#111216"))
        p.fillPath(path, gradient)
        p.save()
        p.setClipPath(path)
        if self.objectName() == "hero":
            light = QRadialGradient(
                QPointF(self.width() * 0.82, self.height() * 0.43), self.height() * 0.8
            )
            tone = QColor(current_palette()['accent'])
            tone.setAlpha(24)
            light.setColorAt(0, tone)
            tone.setAlpha(0)
            light.setColorAt(1, tone)
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
        p.setPen(QPen(QColor("#2b2d35"), 1))
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


class ExpandButton(GlowButton):
    """A fixed icon becomes a filled labeled pill when selected; no magnet motion."""

    def __init__(self, text, symbol, expanded_width=190):
        super().__init__(text)
        self.setObjectName("nav")
        self.setIcon(icon(symbol))
        self.setCheckable(True)
        self.setToolTip(text)
        self.setAccessibleName(text)
        self.expanded_width = expanded_width
        self.reveal = 0.0
        self.setFixedWidth(50)
        self.expand_animation = QVariantAnimation(self)
        self.expand_animation.setDuration(210)
        self.expand_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.expand_animation.valueChanged.connect(self.reveal_changed)
        self.toggled.connect(self.expand)

    def sizeHint(self):
        return QSize(round(50 + (self.expanded_width - 50) * self.reveal), 44)

    def minimumSizeHint(self):
        return QSize(50, 44)

    def reveal_changed(self, value):
        self.reveal = float(value)
        self.setFixedWidth(round(50 + (self.expanded_width - 50) * self.reveal))
        self.update()

    def expand(self, selected):
        self.expand_animation.stop()
        target = 1.0 if selected else 0.0
        if not motion_enabled() or not self.isVisible():
            self.reveal_changed(target)
            return
        self.expand_animation.setStartValue(self.reveal)
        self.expand_animation.setEndValue(target)
        self.expand_animation.start()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1.5, 2, -1.5, -2)
        path = QPainterPath()
        path.addRoundedRect(rect, 11, 11)
        p.fillPath(path, QColor("#0c0d10"))
        p.save()
        p.setClipPath(path)
        fill = QLinearGradient(rect.topLeft(), rect.bottomRight())
        fill.setColorAt(0, QColor(230, 212, 145, round(42 * self.reveal)))
        fill.setColorAt(1, QColor(230, 212, 145, round(14 * self.reveal)))
        p.fillRect(rect, fill)
        if self.hover:
            p.fillRect(rect, QColor(255, 255, 255, round(9 * self.hover)))
        if self.press:
            p.fillRect(rect, QColor(255, 255, 255, round(30 * self.press)))
        p.restore()
        p.setPen(
            QPen(
                QColor(
                    "#706445"
                    if self.isChecked()
                    else "#383a43"
                    if self.hover
                    else "#202127"
                ),
                1,
            )
        )
        p.drawPath(path)
        self.icon().paint(p, 15, round(rect.center().y() - 10), 20, 20)
        if self.reveal > 0.15:
            p.save()
            p.setOpacity(self.reveal)
            p.setPen(QColor("#f6e6b2" if self.isChecked() else "#afb2bc"))
            text_rect = rect.adjusted(45, 0, -12, 0)
            p.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                self.fontMetrics().elidedText(
                    self.text(),
                    Qt.TextElideMode.ElideRight,
                    max(1, round(text_rect.width())),
                ),
            )
            p.restore()
        if self.hasFocus():
            p.setPen(QPen(QColor("#aa9c71"), 1, Qt.PenStyle.DotLine))
            p.drawRoundedRect(rect.adjusted(3, 3, -3, -3), 8, 8)


class StudioBackground(QWidget):
    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#030405"))
        glow = QRadialGradient(QPointF(self.width() * 0.78, 0), self.width() * 0.70)
        col = QColor(current_palette()["accent"])
        col.setAlpha(9)
        glow.setColorAt(0, col)
        col.setAlpha(0)
        glow.setColorAt(1, col)
        p.fillRect(self.rect(), glow)
