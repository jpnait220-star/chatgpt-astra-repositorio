from __future__ import annotations
import copy
from PySide6.QtCore import Qt, QRectF, QTimer, QPointF, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QPen, QColor, QFont, QPainter, QPixmap, QRadialGradient
from PySide6.QtWidgets import (
    QGraphicsObject,
    QScrollArea,
    QGraphicsItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QCheckBox,
    QInputDialog,
    QFileDialog,
    QGridLayout,
    QFrame,
    QVBoxLayout,
)
from .widgets import Page, Tip, label, button
from .hud import NAMES, preset
from .visuals import ExpandButton
from PySide6.QtWidgets import QButtonGroup

NAMES["image"] = "Imagem / sticker"


class HudItem(QGraphicsObject):
    def __init__(self, model, changed):
        super().__init__()
        self.model = model
        self.changed = changed
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setPos(model["x"] * 960, model["y"] * 540)
        self.setScale(model.get("scale", 1))
        self.setOpacity(model.get("opacity", 1))
        self._fold = 0.0
        self._fold_pointer = QPointF(self.boundingRect().center())
        if model.get("kind") == "music":
            self.setAcceptHoverEvents(True)
            self._fold_anim = QVariantAnimation(self)
            self._fold_anim.setDuration(180)
            self._fold_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._fold_anim.valueChanged.connect(self._fold_changed)

    def _fold_changed(self, value):
        self._fold = float(value)
        self.update()

    def _fold_to(self, target):
        from .visuals import motion_enabled
        if not hasattr(self, '_fold_anim'):
            return
        if not motion_enabled():
            self._fold_changed(target)
            return
        self._fold_anim.stop()
        self._fold_anim.setStartValue(self._fold)
        self._fold_anim.setEndValue(target)
        self._fold_anim.start()

    def hoverEnterEvent(self, event):
        if self.model["kind"] == "music":
            self._fold_pointer = event.pos()
            self._fold_to(1.0)
        super().hoverEnterEvent(event)

    def hoverMoveEvent(self, event):
        if self.model["kind"] == "music":
            self._fold_pointer = event.pos()
            self.update()
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        if self.model["kind"] == "music":
            self._fold_to(0.0)
        super().hoverLeaveEvent(event)

    def boundingRect(self):
        kind = self.model["kind"]
        if kind == "image":
            image = QPixmap(self.model.get("path", ""))
            return QRectF(
                0,
                0,
                144,
                144 * image.height() / max(1, image.width())
                if not image.isNull()
                else 90,
            )
        dimensions = {
            "keyboard": (86, 116),
            "mouse": (61, 48),
            "clicks": (110, 32),
            "fps": (132, 28),
            "timer": (64, 28),
            "music": (220, 32),
            "cps": (86, 28),
        }
        width, height = dimensions.get(kind, (180, 32))
        return QRectF(0, 0, width, height)

    def paint(self, p, option, widget):
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.boundingRect()
        kind = self.model["kind"]
        p.setPen(
            QPen(
                QColor("#eef2f8" if self.isSelected() else "#242b37"),
                2 if self.isSelected() else 1,
            )
        )
        p.setBrush(QColor("#1b202a"))
        p.drawRoundedRect(rect, 6, 6)
        if kind == "music" and self._fold > 0.005:
            px, py = self._fold_pointer.x(), self._fold_pointer.y()
            x = max(-1, min(1, 2*px/max(1, rect.width()) - 1))
            y = max(-1, min(1, 2*py/max(1, rect.height()) - 1))
            grad = QRadialGradient(self._fold_pointer, max(26, rect.width() * .40))
            grad.setColorAt(0, QColor(255,255,255,round(32 * self._fold)))
            grad.setColorAt(1, QColor(255,255,255,0))
            p.fillRect(rect.adjusted(2,2,-2,-2), grad)
            p.setPen(QPen(QColor(240,244,255,round(170*self._fold)), 1))
            p.drawLine(QPointF(rect.width()/2, 1), QPointF(rect.width()/2+3*x, 1))
            p.drawLine(QPointF(1, rect.height()/2), QPointF(1, rect.height()/2+2*y))
        p.setFont(QFont("Manrope", 10))
        if kind in ("keyboard", "mouse"):
            cells = (
                [
                    ("W", 1, 0, 25),
                    ("A", 0, 1, 25),
                    ("S", 1, 1, 25),
                    ("D", 2, 1, 25),
                    ("SHIFT", 0, 2, 25),
                    ("CTRL", 2, 2, 25),
                    ("SPACE", 0, 3, 81),
                ]
                if kind == "keyboard"
                else [("L", 0, 0, 25), ("R", 1, 0, 25)]
            )
            for key, column, row, width in cells:
                x = 2 + column * 28
                y = 2 + row * 28
                p.setBrush(QColor("#e6ebf2" if key == "W" else "#252b34"))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(x, y, width, 25, 3, 3)
                p.setFont(QFont("Manrope", 6 if len(key) > 1 else 9))
                p.setPen(QColor("#12161d" if key == "W" else "#eee"))
                p.drawText(QRectF(x, y, width, 25), Qt.AlignmentFlag.AlignCenter, key)
            if kind == "mouse":
                p.setFont(QFont("Manrope", 6))
                p.drawText(
                    QRectF(2, 29, 58, 16), Qt.AlignmentFlag.AlignCenter, "DuckMouse"
                )
        elif kind == "image":
            pixmap = QPixmap(self.model.get("path", ""))
            if not pixmap.isNull():
                p.drawPixmap(rect.toRect(), pixmap)
        else:
            p.setPen(QColor("#eeeef0"))
            text = {
                "clicks": "◎ Clique visual",
                "fps": "60 FPS • captura",
                "timer": "00:30",
                "music": "♪ Sua música",
                "cps": "6 CPS",
            }.get(kind, self.model.get("text") or "DuckCapture")
            p.drawText(
                rect.adjusted(5, 2, -5, -2),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                text,
            )

    def itemChange(self, change, value):
        if (
            change == QGraphicsItem.GraphicsItemChange.ItemPositionChange
            and self.scene()
        ):
            value.setX(
                max(0, min(960 - self.boundingRect().width() * self.scale(), value.x()))
            )
            value.setY(
                max(
                    0, min(540 - self.boundingRect().height() * self.scale(), value.y())
                )
            )
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.model["x"] = self.pos().x() / 960
            self.model["y"] = self.pos().y() / 540
            self.changed()
        return super().itemChange(change, value)


class HudEditor(Page):
    def __init__(self, settings, save, notify):
        super().__init__(
            "Seu estilo, em cada frame.",
            "Arraste os elementos. A prévia é ilustrativa; teclas e cliques reais aparecem nos clipes.",
        )
        self.settings = settings
        self.save = save
        self.notify = notify
        self.loading = False
        self.debounce = QTimer(self)
        self.debounce.setSingleShot(True)
        self.debounce.setInterval(250)
        self.debounce.timeout.connect(self.save)
        top = QHBoxLayout()
        self.enabled = QCheckBox("Aplicar HUD aos próximos clipes")
        self.enabled.setChecked(settings.hud_enabled)
        self.enabled.toggled.connect(self.toggle)
        top.addWidget(self.enabled)
        top.addStretch()
        self.presets = QComboBox()
        self.presets.addItems(
            [
                "Minecraft PvP",
                "Tutorial",
                "Speedrun",
                "Minimal",
                *settings.hud_presets.keys(),
            ]
        )
        top.addWidget(self.presets)
        top.addWidget(button("Aplicar preset", self.apply_preset))
        top.addWidget(button("Salvar preset", self.save_preset))
        self.body.addLayout(top)
        self.kind = QComboBox()
        self.kind.hide()
        self.tool_group = QButtonGroup(self)
        self.tool_group.setExclusive(True)
        tools = QHBoxLayout()
        tools.setSpacing(7)
        self.hud_tools = {}
        symbols = {
            "keyboard": "keyboard",
            "mouse": "mouse",
            "clicks": "mouse",
            "cps": "activity",
            "fps": "activity",
            "timer": "timer",
            "music": "music",
            "title": "text",
            "image": "image",
        }
        for key, title in NAMES.items():
            self.kind.addItem(title, key)
            control = ExpandButton(title, symbols.get(key, "hud"), 205)
            control.clicked.connect(
                lambda checked=False, k=key: self.kind.setCurrentIndex(
                    self.kind.findData(k)
                )
            )
            self.tool_group.addButton(control)
            self.hud_tools[key] = control
            tools.addWidget(control)
        self.kind.currentIndexChanged.connect(
            lambda _: self.hud_tools[self.kind.currentData()].setChecked(True)
        )
        self.hud_tools[self.kind.currentData()].setChecked(True)
        # Classic advanced palette stays available, but is no longer the only
        # way to add a built-in HUD to a preset.
        tools.addStretch()
        self.ready_section = QFrame()
        self.ready_section.setObjectName("readyHudSection")
        ready_layout = QVBoxLayout(self.ready_section)
        ready_layout.setContentsMargins(17, 16, 17, 16)
        ready_layout.setSpacing(10)
        ready_layout.addWidget(label("HUDS PRONTOS PARA O PRESET", "eyebrow"))
        ready_layout.addWidget(label(
            "Ative os módulos que deseja. Eles aparecem no jogo gravado, sem importar arquivos.",
            "muted", True,
        ))
        choices = QGridLayout()
        choices.setSpacing(10)
        self.ready_checks = {}
        ready_kinds = ("keyboard", "mouse", "cps", "fps", "music", "timer", "clicks", "title")
        for index, kind in enumerate(ready_kinds):
            control = QCheckBox(NAMES[kind])
            control.setToolTip("Adicionar ou remover este HUD dos próximos clipes")
            control.toggled.connect(lambda enabled, k=kind: self.toggle_ready_hud(k, enabled))
            self.ready_checks[kind] = control
            choices.addWidget(control, index // 4, index % 4)
        ready_layout.addLayout(choices)
        self.body.addWidget(self.ready_section)
        advanced_row = QHBoxLayout()
        advanced_row.addWidget(label("PERSONALIZAÇÃO AVANÇADA", "eyebrow"))
        advanced_row.addStretch()
        advanced_row.addWidget(label("Escolha um módulo abaixo e clique em Adicionar", "tiny"))
        self.body.addLayout(advanced_row)
        self.tool_scroll = QScrollArea()
        self.tool_scroll.setWidgetResizable(True)
        self.tool_scroll.setMaximumHeight(76)
        self.tool_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tool_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        tools_frame = QFrame()
        tools_frame.setLayout(tools)
        self.tool_scroll.setWidget(tools_frame)
        self.body.addWidget(self.tool_scroll)
        self.scene = QGraphicsScene(0, 0, 960, 540, self)
        self.scene.setBackgroundBrush(QColor("#090a0c"))
        self.view = QGraphicsView(self.scene)
        self.view.setMinimumHeight(320)
        self.view.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.view.setStyleSheet(
            "QGraphicsView { border: 1px solid #38414f; border-radius: 10px; background:#0c1017; }"
        )
        self.body.addWidget(self.view, 1)
        self.scene.selectionChanged.connect(self.selected)
        row = QHBoxLayout()
        row.addWidget(button("+ Adicionar", self.add))
        row.addWidget(button("Remover", self.remove))
        row.addStretch()
        self.body.addLayout(row)
        config = QHBoxLayout()
        self.scale = QDoubleSpinBox()
        self.scale.setRange(0.4, 3)
        self.scale.setSingleStep(0.1)
        self.scale.setValue(1)
        self.opacity = QDoubleSpinBox()
        self.opacity.setRange(0.1, 1)
        self.opacity.setSingleStep(0.1)
        self.opacity.setValue(1)
        self.text = QLineEdit()
        self.text.setPlaceholderText("Texto personalizado")
        config.addWidget(label("Escala", "muted"))
        config.addWidget(self.scale)
        config.addWidget(label("Opacidade", "muted"))
        config.addWidget(self.opacity)
        config.addWidget(self.text, 1)
        self.body.addLayout(config)
        for control in [self.scale, self.opacity]:
            control.valueChanged.connect(self.update_item)
        self.text.textEdited.connect(self.update_item)
        self.tip = Tip(
            "SettingDuck",
            "O teclado só acompanha W, A, S, D, Espaço, Shift e Ctrl enquanto a janela escolhida está em foco. As mudanças valem para o próximo clipe. O círculo de clique acompanha o cursor.",
        )
        self.body.addWidget(self.tip)
        if not settings.hud:
            settings.hud = preset()
        self.render()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def showEvent(self, event):
        super().showEvent(event)
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def toggle(self, value):
        self.settings.hud_enabled = value
        self.save()

    def changed(self):
        if not self.loading:
            self.debounce.start()

    def toggle_ready_hud(self, kind, enabled):
        if self.loading:
            return
        matching = [item for item in self.settings.hud if item.get("kind") == kind]
        if enabled and not matching:
            placements = {
                "keyboard": (.04, .69), "mouse": (.22, .77),
                "fps": (.83, .04), "cps": (.83, .10),
                "music": (.04, .05), "timer": (.83, .16),
                "clicks": (.48, .5), "title": (.35, .08),
            }
            x, y = placements.get(kind, (.4, .35))
            self.settings.hud.append(dict(kind=kind, x=x, y=y,
                                          scale=1.0, opacity=.92,
                                          text="Meu título" if kind == "title" else ""))
        elif not enabled:
            self.settings.hud = [item for item in self.settings.hud if item.get("kind") != kind]
        self.render()
        self.save()

    def render(self):
        self.loading = True
        if hasattr(self, "ready_checks"):
            included = {item.get("kind") for item in self.settings.hud}
            for kind, control in self.ready_checks.items():
                control.blockSignals(True)
                control.setChecked(kind in included)
                control.blockSignals(False)
        self.scene.clear()
        # Subtle alignment grid.
        for x in range(0, 961, 60):
            self.scene.addLine(x, 0, x, 540, QPen(QColor("#1c2531")))
        for y in range(0, 541, 60):
            self.scene.addLine(0, y, 960, y, QPen(QColor("#1c2531")))
        for item in self.settings.hud:
            self.scene.addItem(HudItem(item, self.changed))
        self.loading = False

    def add(self):
        item = dict(
            kind=self.kind.currentData(),
            x=0.4,
            y=0.35,
            scale=1,
            opacity=0.9,
            text="DuckCapture",
        )
        if item["kind"] == "image":
            path, _ = QFileDialog.getOpenFileName(
                self, "Imagem do HUD", "", "Imagens (*.png *.jpg *.jpeg *.webp)"
            )
            if not path:
                return
            item["path"] = path
        self.settings.hud.append(item)
        self.render()
        self.save()

    def remove(self):
        for item in self.scene.selectedItems():
            if isinstance(item, HudItem):
                self.settings.hud.remove(item.model)
        self.render()
        self.save()

    def selected(self):
        items = [i for i in self.scene.selectedItems() if isinstance(i, HudItem)]
        if not items:
            return
        self.loading = True
        item = items[0]
        self.scale.setValue(item.model["scale"])
        self.opacity.setValue(item.model["opacity"])
        self.text.setText(item.model.get("text", ""))
        self.loading = False

    def update_item(self, *_):
        if self.loading:
            return
        for item in self.scene.selectedItems():
            if not isinstance(item, HudItem):
                continue
            item.model.update(
                scale=self.scale.value(),
                opacity=self.opacity.value(),
                text=self.text.text(),
            )
            item.setScale(self.scale.value())
            item.setOpacity(self.opacity.value())
            item.setPos(
                max(0, min(item.x(), 960 - item.boundingRect().width() * item.scale())),
                max(
                    0, min(item.y(), 540 - item.boundingRect().height() * item.scale())
                ),
            )
            item.update()
        self.changed()

    def apply_preset(self):
        name = self.presets.currentText()
        self.settings.hud = copy.deepcopy(
            self.settings.hud_presets.get(name, preset(name))
        )
        self.render()
        self.save()

    def save_preset(self):
        name, ok = QInputDialog.getText(self, "Salvar preset", "Nome do preset:")
        if ok and name.strip():
            name = name.strip()
            self.settings.hud_presets[name] = copy.deepcopy(self.settings.hud)
            self.save()
            if self.presets.findText(name) < 0:
                self.presets.addItem(name)
            self.presets.setCurrentText(name)
            self.notify("Preset salvo: " + name)
