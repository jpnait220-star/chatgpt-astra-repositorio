"""Opt-in window picker using Windows DWM live thumbnails (no screen scraping)."""

import ctypes
import os
from PySide6.QtCore import Qt, QTimer, Signal, QPoint
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLineEdit,
    QComboBox,
    QSizePolicy,
    QScrollArea,
)
from .widgets import label, button, card
from .windows import list_windows, window_minimized


class Rect(ctypes.Structure):
    _fields_ = [(key, ctypes.c_int32) for key in ("left", "top", "right", "bottom")]


class Size(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_int32), ("cy", ctypes.c_int32)]


class ThumbnailProperties(ctypes.Structure):
    _fields_ = [
        ("flags", ctypes.c_uint32),
        ("destination", Rect),
        ("source", Rect),
        ("opacity", ctypes.c_ubyte),
        ("visible", ctypes.c_int32),
        ("client_only", ctypes.c_int32),
    ]


class DwmThumbnail:
    def __init__(self, destination, source):
        self.handle = ctypes.c_void_p()
        if os.name != "nt":
            raise RuntimeError("As prévias de janelas funcionam no Windows.")
        self.api = ctypes.WinDLL("dwmapi")
        self.api.DwmRegisterThumbnail.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        self.api.DwmRegisterThumbnail.restype = ctypes.c_int32
        self.api.DwmQueryThumbnailSourceSize.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(Size),
        ]
        self.api.DwmQueryThumbnailSourceSize.restype = ctypes.c_int32
        self.api.DwmUpdateThumbnailProperties.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ThumbnailProperties),
        ]
        self.api.DwmUpdateThumbnailProperties.restype = ctypes.c_int32
        self.api.DwmUnregisterThumbnail.argtypes = [ctypes.c_void_p]
        self.api.DwmUnregisterThumbnail.restype = ctypes.c_int32
        if (
            self.api.DwmRegisterThumbnail(
                destination, source, ctypes.byref(self.handle)
            )
            < 0
        ):
            raise RuntimeError("Esta janela não disponibilizou uma prévia.")

    def update(self, widget, dialog):
        source = Size()
        if self.api.DwmQueryThumbnailSourceSize(self.handle, ctypes.byref(source)) < 0:
            return
        position = widget.mapTo(dialog, widget.rect().topLeft())
        scale = dialog.devicePixelRatioF()
        available_w, available_h = widget.width() * scale, widget.height() * scale
        factor = min(available_w / max(1, source.cx), available_h / max(1, source.cy))
        width, height = round(source.cx * factor), round(source.cy * factor)
        left = round(position.x() * scale + (available_w - width) / 2)
        top = round(position.y() * scale + (available_h - height) / 2)
        props = ThumbnailProperties()
        props.flags = 1 | 4 | 8 | 16
        props.destination = Rect(left, top, left + width, top + height)
        props.opacity, props.visible, props.client_only = 255, 1, 0
        self.api.DwmUpdateThumbnailProperties(self.handle, ctypes.byref(props))

    def hide(self):
        if self.handle.value:
            props = ThumbnailProperties()
            props.flags = 8  # DWM_TNP_VISIBLE
            props.visible = 0
            self.api.DwmUpdateThumbnailProperties(self.handle, ctypes.byref(props))

    def close(self):
        if self.handle.value:
            self.api.DwmUnregisterThumbnail(self.handle)
            self.handle = ctypes.c_void_p()


class WindowCombo(QComboBox):
    chooseRequested = Signal()

    def showPopup(self):
        self.chooseRequested.emit()


class WindowPicker(QDialog):
    def __init__(self, parent=None, windows=None, thumbnail_factory=DwmThumbnail):
        super().__init__(parent)
        self.setWindowTitle("Escolha a janela para capturar")
        self.resize(920, 690)
        self.setMinimumSize(800, 630)
        self.windows = list_windows() if windows is None else windows
        self.factory = thumbnail_factory
        self.previews = []
        self.selected = None
        self.page = 0
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)
        layout.addWidget(label("Qual janela vai virar clipe?", "heading"))
        layout.addWidget(
            label(
                "As prévias são ao vivo. Janelas minimizadas ou protegidas podem aparecer sem imagem.",
                "muted",
                True,
            )
        )
        row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar uma janela…")
        self.search.textChanged.connect(self.filter)
        row.addWidget(self.search, 1)
        row.addWidget(button("Atualizar", self.refresh))
        layout.addLayout(row)
        self.grid_widget = QWidget()
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(14)
        self.scroller = QScrollArea()
        self.scroller.setWidgetResizable(True)
        self.scroller.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroller.setStyleSheet("QScrollArea { background: transparent; border: none; border-radius: 15px; }")
        self.scroller.setWidget(self.grid_widget)
        layout.addWidget(self.scroller, 1)
        self.empty = label(
            "Nenhuma janela disponível. Abra ou restaure o aplicativo que deseja capturar.",
            "muted",
            True,
        )
        layout.addWidget(self.empty)
        footer = QHBoxLayout()
        self.back = button("Anterior", lambda: self.turn(-1))
        self.next = button("Próxima", lambda: self.turn(1))
        self.count = label("", "tiny")
        footer.addWidget(self.back)
        footer.addWidget(self.count)
        footer.addWidget(self.next)
        footer.addStretch()
        footer.addWidget(button("Cancelar", self.reject))
        layout.addLayout(footer)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(45)
        self.timer.timeout.connect(self.update_previews)
        self.scroller.verticalScrollBar().valueChanged.connect(self.schedule_preview)
        self.finished.connect(self.cleanup)
        self.render()

    def filter(self):
        self.page = 0
        self.render()

    def refresh(self):
        self.windows = list_windows()
        self.filter()

    def turn(self, direction):
        self.page += direction
        self.render()

    def cleanup(self, *_):
        self.timer.stop()
        for _, preview in self.previews:
            if preview:
                preview.close()
        self.previews.clear()

    def render(self):
        self.cleanup()
        while self.grid.count():
            item = self.grid.takeAt(0)
            item.widget().deleteLater()
        query = self.search.text().casefold().strip()
        choices = [
            (hwnd, title) for hwnd, title in self.windows if query in title.casefold()
        ]
        pages = max(1, (len(choices) + 5) // 6)
        self.page = max(0, min(self.page, pages - 1))
        self.back.setEnabled(self.page > 0)
        self.next.setEnabled(self.page + 1 < pages)
        self.count.setText(f"{len(choices)} janelas · página {self.page + 1}/{pages}")
        self.empty.setVisible(not choices)
        for index, (hwnd, title) in enumerate(
            choices[self.page * 6 : self.page * 6 + 6]
        ):
            tile = card()
            content = QVBoxLayout(tile)
            content.setContentsMargins(12, 12, 12, 12)
            preview = label(
                "Minimizada" if window_minimized(hwnd) else "Preparando prévia…",
                "tiny",
                True,
            )
            preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            preview.setMinimumSize(210, 125)
            preview.setStyleSheet(
                "background:#030405; border-radius:8px; color:#7f8590;"
            )
            content.addWidget(preview, 1)
            preview.setCursor(Qt.CursorShape.PointingHandCursor)
            preview.mousePressEvent = (
                lambda event, h=hwnd, t=title: self.choose(h, t)
                if event.button() == Qt.MouseButton.LeftButton
                else None
            )
            choose = button(
                title, lambda checked=False, h=hwnd, t=title: self.choose(h, t)
            )
            choose.setToolTip(title)
            choose.setMinimumWidth(0)
            choose.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            choose.setAccessibleName("Capturar " + title)
            content.addWidget(choose)
            self.grid.addWidget(tile, index // 3, index % 3)
            try:
                thumbnail = self.factory(int(self.winId()), hwnd)
                preview.setText("")
            except Exception as error:
                preview.setText(
                    "Prévia indisponível\nVocê ainda pode selecionar esta janela."
                )
                preview.setToolTip(str(error))
                thumbnail = None
            self.previews.append((preview, thumbnail))
        self.scroller.verticalScrollBar().setValue(0)
        self.schedule_preview()

    def schedule_preview(self, *_):
        self.timer.start()

    def showEvent(self, event):
        super().showEvent(event)
        self.schedule_preview()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "timer"):
            self.schedule_preview()

    def update_previews(self):
        if self.isVisible():
            visible = self.scroller.viewport().rect()
            viewport = self.scroller.viewport()
            for widget, preview in self.previews:
                if not preview:
                    continue
                position = widget.mapTo(viewport, QPoint(0, 0))
                bounds = widget.rect().translated(position)
                if visible.intersects(bounds):
                    preview.update(widget, self)
                else:
                    preview.hide()

    def choose(self, hwnd, title):
        self.selected = (hwnd, title)
        self.accept()
