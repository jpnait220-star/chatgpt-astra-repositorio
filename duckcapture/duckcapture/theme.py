"""Lightweight app theming: precomputed color values, no render loop."""
from __future__ import annotations
import re
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

DEFAULT_ACCENT = "#f4f6fb"
PRESETS = {
    "Branco gelo": "#f4f6fb",
    "Azul gelo": "#dbe8ff",
    "Prata": "#d9dee8",
    "Roxo frio": "#cdbdff",
    "Vermelho clean": "#ffd1d8",
    "Ciano soft": "#d8f9ff",
}


def palette(accent):
    if not isinstance(accent, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", accent):
        accent = DEFAULT_ACCENT
    color = QColor(accent)

    def mix(other, part):
        blend = QColor(other)
        rgb = [
            round(a * (1 - part) + b * part)
            for a, b in zip(
                (color.red(), color.green(), color.blue()),
                (blend.red(), blend.green(), blend.blue()),
            )
        ]
        return "#%02x%02x%02x" % tuple(rgb)

    return dict(
        accent=accent,
        bright=mix("#ffffff", 0.52),
        muted=mix("#485266", 0.60),
        selected=mix("#0f131a", 0.77),
        glow=mix("#ffffff", 0.75),
        dark_text="#091019" if color.lightness() > 155 else "#ffffff",
    )


def theme_style(base, accent):
    c = palette(accent)
    for old, new in {
        '#f3d768': c['accent'], '#ffeb9e': c['bright'], '#ffe691': c['bright'],
        '#f3da82': c['bright'], '#2e2b20': c['selected'], '#4b422c': c['muted'],
        '#f9de82': c['bright'], '#544b2e': c['selected'], '#f0d268': c['accent'],
        '#ffeaa4': c['bright'], '#fff3c9': c['bright'], '#e0c360': c['accent'],
        '#ffeea4': c['bright'], '#b3a46c': c['accent'], '#e7cf7d': c['bright'],
        '#ddd3b2': c['bright'], '#383326': c['selected'], '#393426': c['selected'],
        '#29271f': c['selected'], '#f6e5b0': c['bright'], '#655b3a': c['muted'],
        '#514b34': c['selected'], '#aaa084': c['bright'], '#5a5235': c['muted'],
        '#171713': c['dark_text'],
    }.items():
        base = base.replace(old, new)
    return base


def current_palette():
    app = QApplication.instance()
    return palette(app.property('duckAccent') if app is not None else DEFAULT_ACCENT)
