"""Short local completion chimes; never play success before a file is saved."""

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect
from .config import ROOT


class CaptureSounds:
    def __init__(self, parent, settings):
        self.settings = settings
        self.effects = {}
        for name in ("clip", "print"):
            effect = QSoundEffect(parent)
            effect.setVolume(0.24)
            effect.setSource(QUrl.fromLocalFile(str(ROOT / "assets" / (name + ".wav"))))
            self.effects[name] = effect

    def saved(self, path):
        if self.settings.notification_sounds:
            effect = self.effects[
                "print" if str(path).lower().endswith(".png") else "clip"
            ]
            effect.stop()
            effect.play()
