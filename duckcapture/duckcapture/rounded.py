"""Rounded native controls with their usual keyboard and mouse behavior."""
from PySide6.QtCore import QObject, QEvent, Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QRegion
from PySide6.QtWidgets import QScrollBar, QStyleOptionSlider, QStyle, QAbstractScrollArea, QMenu


class RoundScrollBar(QScrollBar):
    def paintEvent(self, event):
        if self.maximum() <= self.minimum():
            return
        option = QStyleOptionSlider()
        self.initStyleOption(option)
        handle = QRectF(self.style().subControlRect(
            QStyle.ComplexControl.CC_ScrollBar, option, QStyle.SubControl.SC_ScrollBarSlider, self))
        vertical = self.orientation() == Qt.Orientation.Vertical
        handle.adjust(3 if vertical else 1, 1 if vertical else 3, -3 if vertical else -1, -1 if vertical else -3)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor('#747984' if self.underMouse() or self.isSliderDown() else '#3b3f48'))
        radius = min(handle.width(), handle.height()) / 2
        painter.drawRoundedRect(handle, radius, radius)


class PopupRounder(QObject):
    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Show, QEvent.Type.Resize):
            if isinstance(watched, QMenu) or watched.metaObject().className() in ('QComboBoxPrivateContainer', 'QTipLabel'):
                path = QPainterPath()
                path.addRoundedRect(QRectF(watched.rect()), 14, 14)
                watched.setMask(QRegion(path.toFillPolygon().toPolygon()))
        return False


def install_rounded_controls(root):
    for area in root.findChildren(QAbstractScrollArea):
        if not isinstance(area.verticalScrollBar(), RoundScrollBar):
            area.setVerticalScrollBar(RoundScrollBar(Qt.Orientation.Vertical, area))
            area.setHorizontalScrollBar(RoundScrollBar(Qt.Orientation.Horizontal, area))
