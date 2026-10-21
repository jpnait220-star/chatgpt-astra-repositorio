"""Pointer-weighted perspective: real card deformation, with no idle render loop."""
from __future__ import annotations
from PySide6.QtCore import QObject, Qt, QRectF, QPoint, QPointF, QEvent, QVariantAnimation, QEasingCurve, QModelIndex
from PySide6.QtGui import QColor, QPainter, QPixmap, QPainterPath, QRadialGradient, QPen, QPolygonF, QTransform
from PySide6.QtWidgets import QWidget, QApplication, QGraphicsEffect, QStyledItemDelegate, QStyleOptionViewItem


def motion_enabled():
    app = QApplication.instance()
    return app is None or app.property('duckMotion') is not False


def fold_transform(rect, pointer, amount):
    """Move the pointed corner inward and lift the opposite edge, within hit bounds."""
    r = QRectF(rect)
    if not motion_enabled() or amount <= .001 or r.width() < 12 or r.height() < 12:
        return QTransform()
    nx = max(-1., min(1., (pointer.x() - r.center().x()) / (r.width() / 2)))
    ny = max(-1., min(1., (pointer.y() - r.center().y()) / (r.height() / 2)))
    source = QPolygonF([r.topLeft(), r.topRight(), r.bottomRight(), r.bottomLeft()])
    target = QPolygonF()
    depth = min(7., max(2., r.height() * .055)) * amount
    for point, sx, sy in zip(source, (-1, 1, 1, -1), (-1, -1, 1, 1)):
        weight = (1 + sx * nx) * (1 + sy * ny) / 4
        inset_x = depth * (.22 + weight * .95)
        inset_y = depth * (.22 + weight * 1.35)
        target.append(QPointF(point.x() - sx * inset_x, point.y() - sy * inset_y))
    return QTransform.quadToQuad(source, target)


def paint_sheen(painter, rect, pointer, amount):
    if amount < .001:
        return
    path = QPainterPath()
    path.addRoundedRect(QRectF(rect).adjusted(1, 1, -1, -1), 13, 13)
    glow = QRadialGradient(pointer, max(50, min(rect.width(), rect.height()) * 1.4))
    glow.setColorAt(0, QColor(255, 255, 255, round(33 * amount)))
    glow.setColorAt(.5, QColor(220, 230, 255, round(8 * amount)))
    glow.setColorAt(1, QColor(255, 255, 255, 0))
    painter.fillPath(path, glow)
    painter.setPen(QPen(QColor(226, 233, 248, round(100 * amount)), 1))
    painter.drawPath(path)


class FoldEffect(QGraphicsEffect):
    def __init__(self, controller):
        super().__init__(controller.target)
        self.controller = controller

    def draw(self, painter):
        c = self.controller
        if c.opacity <= .001 or not motion_enabled():
            self.drawSource(painter)
            return
        # Rasterize before applying perspective. Qt's raster gradient engine can
        # crash when a radial gradient is painted through a projective transform.
        offset = QPoint()
        pixmap = self.sourcePixmap(Qt.CoordinateSystem.LogicalCoordinates, offset,
                                   QGraphicsEffect.PixmapPadMode.NoPad).copy()
        if pixmap.isNull():
            return
        surface = QPainter(pixmap)
        surface.setRenderHint(QPainter.RenderHint.Antialiasing)
        surface.translate(-offset)
        paint_sheen(surface, QRectF(c.target.rect()), c.pointer, c.opacity)
        surface.end()
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setWorldTransform(fold_transform(c.target.rect(), c.pointer, c.opacity), True)
        painter.drawPixmap(offset, pixmap)
        painter.restore()


class FoldDelegate(QStyledItemDelegate):
    def __init__(self, controller):
        super().__init__(controller.item_view)
        self.controller = controller

    def paint(self, painter, option, index):
        c = self.controller
        if index != c.hovered or c.opacity <= .001 or not motion_enabled():
            super().paint(painter, option, index)
            return
        ratio = c.target.devicePixelRatioF()
        pixmap = QPixmap(option.rect.size() * ratio)
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(Qt.GlobalColor.transparent)
        surface = QPainter(pixmap)
        surface.setRenderHint(QPainter.RenderHint.Antialiasing)
        local = QStyleOptionViewItem(option)
        local.rect.moveTopLeft(QPoint())
        super().paint(surface, local, index)
        paint_sheen(surface, QRectF(local.rect), c.pointer - QPointF(option.rect.topLeft()), c.opacity)
        surface.end()
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setWorldTransform(fold_transform(option.rect, c.pointer, c.opacity), True)
        painter.drawPixmap(option.rect.topLeft(), pixmap)
        painter.restore()


class FoldController(QObject):
    def __init__(self, target, item_view=None):
        super().__init__(target)
        self.target, self.item_view = target, item_view
        self.pointer = QPointF(target.rect().center())
        self.hovered = QModelIndex()
        self.opacity = 0.
        self.active = False
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(190)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(self.on_opacity)
        self.effect = None
        if item_view is None:
            self.effect = FoldEffect(self)
            target.setGraphicsEffect(self.effect)
        else:
            item_view.setItemDelegate(FoldDelegate(self))
            item_view.model().modelAboutToBeReset.connect(self.reset)
        self.listen(target)
        for child in target.findChildren(QWidget):
            self.listen(child)

    def listen(self, widget):
        widget.setMouseTracking(True)
        widget.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        widget.installEventFilter(self)

    def eventFilter(self, watched, event):
        kind = event.type()
        if kind in (QEvent.Type.MouseMove, QEvent.Type.HoverMove, QEvent.Type.Enter):
            if hasattr(event, 'position'):
                local = event.position().toPoint()
                point = watched.mapTo(self.target, local) if watched is not self.target else local
            else:
                point = self.target.mapFromGlobal(self.target.cursor().pos())
            self.pointer = QPointF(point)
            if self.item_view is not None:
                self.hovered = self.item_view.indexAt(point)
                self.switch(self.hovered.isValid())
            else:
                self.switch(self.target.rect().contains(point))
            self.repaint()
        elif kind in (QEvent.Type.Leave, QEvent.Type.Hide) and watched is self.target:
            self.switch(False)
        elif kind == QEvent.Type.Wheel:
            self.switch(False)
        return False

    def switch(self, active):
        if active == self.active:
            return
        self.active = active
        self.anim.stop()
        if not motion_enabled():
            self.on_opacity(0)
            return
        self.anim.setStartValue(self.opacity)
        self.anim.setEndValue(float(active))
        self.anim.start()

    def reset(self):
        self.anim.stop()
        self.active = False
        self.hovered = QModelIndex()
        self.on_opacity(0)

    def on_opacity(self, value):
        self.opacity = float(value)
        self.repaint()

    def repaint(self):
        if self.effect:
            self.effect.update()
        else:
            self.target.update()


def add_fold_hover(widget, item_view=None):
    """Apply to small native cards/controls; never to video or web surfaces."""
    existing = getattr(widget, '_duck_fold_overlay', None)
    if existing is None:
        target = widget.viewport() if item_view is not None else widget
        existing = FoldController(target, item_view)
        widget._duck_fold_overlay = existing
    return existing
