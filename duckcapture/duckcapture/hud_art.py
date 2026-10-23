"""Shared vector artwork for the HUD preview and the exported video."""

import math
import re
from functools import lru_cache

SIZES = {
    "keyboard": (114, 150),
    "mouse": (92, 126),
    "music": (350, 92),
    "fps": (170, 38),
    "cps": (120, 38),
    "timer": (102, 38),
    "title": (300, 42),
    "clicks": (50, 50),
}


@lru_cache(maxsize=20)
def font(size):
    from PIL import ImageFont
    from .config import ROOT

    return ImageFont.truetype(str(ROOT / "assets/fonts/Manrope-Regular.ttf"), size)


@lru_cache(maxsize=1024)
def elide(value, size, width):
    value = str(value).replace("\n", " ").replace("\r", " ")
    face = font(round(size))
    if face.getlength(value) <= width:
        return value
    while value and face.getlength(value + "…") > width:
        value = value[:-1]
    return value + "…"


def color(value, fallback):
    return (
        value
        if isinstance(value, str) and re.fullmatch("#[0-9a-fA-F]{6}", value)
        else fallback
    )


def rounded(x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    k = 0.55228475
    return [
        ("M", x + r, y),
        ("L", x + w - r, y),
        ("C", x + w - r + k * r, y, x + w, y + r - k * r, x + w, y + r),
        ("L", x + w, y + h - r),
        ("C", x + w, y + h - r + k * r, x + w - r + k * r, y + h, x + w - r, y + h),
        ("L", x + r, y + h),
        ("C", x + r - k * r, y + h, x, y + h - r + k * r, x, y + h - r),
        ("L", x, y + r),
        ("C", x, y + r - k * r, x + r - k * r, y, x + r, y),
        ("Z",),
    ]


def artwork(item, state):
    accent = color(item.get("accent_color"), "#dce7ff")
    text = color(item.get("text_color"), "#f5f7ff")
    background = color(item.get("background_color"), "#10131c")
    shapes = []

    def path(commands, fill, stroke=None):
        shapes.append(dict(kind="path", path=commands, color=fill, stroke=stroke))

    def box(x, y, w, h, radius, fill, stroke=None):
        path(rounded(x, y, w, h, radius), fill, stroke)

    def caption(value, x, y, size=18, fill=text, width=220):
        shapes.append(
            dict(
                kind="text",
                text=elide(value, size, width),
                x=x,
                y=y,
                size=size,
                color=fill,
                width=width,
            )
        )

    kind = item.get("kind")
    if kind == "keyboard":
        for key, col, row, width in [
            ("W", 1, 0, 34),
            ("A", 0, 1, 34),
            ("S", 1, 1, 34),
            ("D", 2, 1, 34),
            ("SHIFT", 0, 2, 53),
            ("CTRL", 1.5, 2, 53),
            ("SPACE", 0, 3, 110),
        ]:
            x, y = col * 38, row * 38
            pressed = key in state.get("keys", [])
            box(
                x,
                y,
                width,
                32,
                8,
                accent if pressed else background,
                accent if pressed else "#353b4b",
            )
            caption(
                key,
                x + 7,
                y + 8,
                11 if len(key) > 1 else 17,
                "#0a0c12" if pressed else text,
                width - 10,
            )
    elif kind == "mouse":
        body = [
            ("M", 46, 2),
            ("C", 19, 2, 6, 20, 6, 49),
            ("L", 6, 77),
            ("C", 6, 103, 18, 121, 46, 123),
            ("C", 74, 121, 86, 103, 86, 77),
            ("L", 86, 49),
            ("C", 86, 20, 73, 2, 46, 2),
            ("Z",),
        ]
        path(body, background, accent)
        left = [
            ("M", 42, 8),
            ("C", 21, 10, 12, 24, 12, 47),
            ("L", 12, 56),
            ("L", 42, 56),
            ("Z",),
        ]
        right = [
            ("M", 50, 8),
            ("C", 71, 10, 80, 24, 80, 47),
            ("L", 80, 56),
            ("L", 50, 56),
            ("Z",),
        ]
        path(left, accent if "L" in state.get("buttons", []) else "#252b3b")
        path(right, accent if "R" in state.get("buttons", []) else "#252b3b")
        box(41, 20, 10, 24, 5, accent if "M" in state.get("buttons", []) else "#69758b")
        box(34, 99, 24, 3, 1.5, accent)
    elif kind == "music":
        box(0, 0, 350, 92, 20, background, "#353d50")
        box(12, 12, 68, 68, 34, "#202635", accent)
        for diameter in (54, 42, 30):
            box(
                46 - diameter / 2,
                46 - diameter / 2,
                diameter,
                diameter,
                diameter / 2,
                "#151a25",
                "#46516a",
            )
        box(37, 37, 18, 18, 9, accent)
        box(43, 43, 6, 6, 3, background)
        playing = state.get("music_playing", False)
        angle = state.get("music_phase", 0) * math.pi / 180
        box(44 + 25 * math.cos(angle), 44 + 25 * math.sin(angle), 4, 4, 2, accent)
        title = state.get("music", "") or "Sem música"
        caption(title[:32] + ("…" if len(title) > 32 else ""), 94, 14, 17, text, 240)
        artist = state.get("music_artist", "")
        caption(
            artist[:37]
            or (
                "TOCANDO AGORA"
                if playing
                else "PAUSADO"
                if title != "Sem música"
                else "Escolha uma música"
            ),
            94,
            39,
            11,
            accent,
            240,
        )
        duration = max(0, state.get("music_duration", 0))
        position = max(0, state.get("music_position", 0))
        progress = min(1, position / duration) if duration else 0
        box(94, 64, 230, 4, 2, "#343b4e")
        if progress > 0:
            box(94, 64, max(4, 230 * progress), 4, 2, accent)

        def clock(t):
            return f"{int(t) // 60:02}:{int(t) % 60:02}"

        caption(
            f"{clock(position)} / {clock(duration)}" if duration else "—",
            94,
            75,
            9,
            accent,
            230,
        )
    elif kind == "clicks":
        box(3, 3, 44, 44, 22, accent)
        box(6, 6, 38, 38, 19, background)
        box(22, 22, 6, 6, 3, accent)
    else:
        w, h = SIZES.get(kind, (300, 42))
        box(0, 0, w, h, 12, background, "#353d50")
        box(10, h / 2 - 3, 6, 6, 3, accent)
        title = {
            "fps": f"{state.get('capture_fps', 0):.0f} FPS",
            "cps": f"{state.get('cps', 0)} CPS",
            "timer": f"{int(state.get('t', 0)) // 60:02}:{int(state.get('t', 0)) % 60:02}",
        }.get(kind, item.get("text") or "DuckCapture")
        caption(title, 24, 10, 17, text, w - 30)
    return shapes


def paint_artwork(painter, item, state):
    from PySide6.QtCore import Qt, QRectF
    from PySide6.QtGui import QColor, QPainterPath, QPen, QFont, QFontMetricsF

    for shape in artwork(item, state):
        if shape["kind"] == "path":
            path = QPainterPath()
            for command in shape["path"]:
                op, *v = command
                if op == "M":
                    path.moveTo(*v)
                elif op == "L":
                    path.lineTo(*v)
                elif op == "C":
                    path.cubicTo(*v)
                else:
                    path.closeSubpath()
            painter.setPen(
                QPen(QColor(shape["stroke"]), 1)
                if shape.get("stroke")
                else Qt.PenStyle.NoPen
            )
            painter.setBrush(QColor(shape["color"]))
            painter.drawPath(path)
        else:
            font = QFont("Manrope")
            font.setPixelSize(round(shape["size"]))
            painter.setFont(font)
            painter.setPen(QColor(shape["color"]))
            value = QFontMetricsF(font).elidedText(
                shape["text"], Qt.TextElideMode.ElideRight, shape["width"]
            )
            painter.drawText(
                QRectF(shape["x"], shape["y"], shape["width"], shape["size"] * 1.35),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                value,
            )


def ass_shapes(item, state, x, y, scale, alpha):
    from .hud import escape

    def bgr(hexcolor):
        return hexcolor[5:7] + hexcolor[3:5] + hexcolor[1:3]

    for shape in artwork(item, state):
        fill = bgr(shape["color"])
        if shape["kind"] == "text":
            yield (
                rf"{{\an7\pos({x + shape['x'] * scale:.2f},{y + shape['y'] * scale:.2f})\fs{shape['size'] * scale:.2f}\bord0\c&H{fill}&\alpha&H{alpha:02X}&}}"
                + escape(shape["text"])
            )
        else:
            commands = []
            for command in shape["path"]:
                if command[0] == "Z":
                    continue
                commands.append(
                    {"M": "m", "L": "l", "C": "b"}[command[0]]
                    + " "
                    + " ".join(f"{v * scale:.2f}" for v in command[1:])
                )
            outline = (
                rf"\bord{scale:.2f}\3c&H{bgr(shape['stroke'])}&"
                if shape.get("stroke")
                else r"\bord0"
            )
            yield (
                rf"{{\an7\pos({x},{y})\p1{outline}\c&H{fill}&\alpha&H{alpha:02X}&}}"
                + " ".join(commands)
                + r"{\p0}"
            )
