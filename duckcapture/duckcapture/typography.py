"""Bundled typography, shared by widgets and rendered HUD text."""
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication
from .config import ROOT

FAMILY = "Manrope"
FONT_PATH = ROOT / "assets" / "fonts" / "Manrope-Regular.ttf"


def install_font():
    app = QApplication.instance()
    if app is None or app.property("duckFontInstalled"):
        return
    for style in ('Regular', 'SemiBold', 'Bold', 'ExtraBold'):
        path = FONT_PATH.with_name(f'Manrope-{style}.ttf')
        if QFontDatabase.addApplicationFont(str(path)) < 0:
            raise RuntimeError("A fonte do DuckCapture está ausente. Extraia o pacote completo.")
    app.setFont(QFont(FAMILY, 10))
    app.setProperty("duckFontInstalled", True)
