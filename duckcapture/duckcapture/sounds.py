"""Short local effects: F8 acknowledgement is immediate, not post-export."""

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect
from .config import ROOT


class CaptureSounds:
    def __init__(self, parent, settings):
        self.settings = settings
        # A small pool lets rapid F8 presses have separate chimes without
        # stopping the previous chime prematurely.
        self.clip_effects = []
        for _ in range(3):
            effect = QSoundEffect(parent)
            effect.setVolume(getattr(settings, "notification_volume", .82))
            effect.setSource(QUrl.fromLocalFile(str(ROOT / "assets" / "clip.wav")))
            self.clip_effects.append(effect)
        self.next_effect = 0
        self.print_effect = QSoundEffect(parent)
        self.print_effect.setVolume(getattr(settings, "notification_volume", .82))
        self.print_effect.setSource(
            QUrl.fromLocalFile(str(ROOT / "assets" / "print.wav"))
        )

    def queued_clip(self):
        """Play as soon as a replay request is accepted (F8 or GUI button)."""
        if not self.settings.notification_sounds:
            return
        effect = self.clip_effects[self.next_effect]
        self.next_effect = (self.next_effect + 1) % len(self.clip_effects)
        effect.setVolume(getattr(self.settings, "notification_volume", .82))
        effect.play()

    def saved(self, path):
        # Clip confirmation has already sounded on keypress; don't play it
        # again after a potentially lengthy export. Screenshots keep their
        # existing completed-only confirmation.
        if self.settings.notification_sounds and str(path).lower().endswith(".png"):
            self.print_effect.setVolume(getattr(self.settings, "notification_volume", .82))
            self.print_effect.play()
