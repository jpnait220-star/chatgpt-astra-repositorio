"""Silent local wallpaper; decoding stops while recording or out of sight."""
import time
from pathlib import Path
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QImage, QPainter, QColor, QRadialGradient
from PySide6.QtWidgets import QWidget
from PySide6.QtMultimedia import QMediaPlayer, QVideoSink, QAudioOutput
from .theme import current_palette


class VideoBackground(QWidget):
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.frame = QImage()
        self.dim = 72
        self.path = ''
        self.blocked = True
        self.last_frame = 0.
        self.player = QMediaPlayer(self)
        self.sink = QVideoSink(self)
        self.player.setVideoSink(self.sink)
        self.audio = QAudioOutput(self)
        self.audio.setMuted(True)
        self.player.setAudioOutput(self.audio)
        self.player.setLoops(QMediaPlayer.Loops.Infinite)
        self.sink.videoFrameChanged.connect(self.receive_frame)
        self.player.errorOccurred.connect(self.on_error)

    def set_video(self, path):
        self.player.stop()
        self.frame = QImage()
        self.last_frame = 0.
        self.path = str(path or '')
        if self.path and not Path(self.path).is_file():
            self.path = ''
            self.failed.emit('O vídeo de fundo foi movido. Selecione o arquivo novamente.')
        self.player.setSource(QUrl.fromLocalFile(str(Path(self.path).resolve())) if self.path else QUrl())
        self.sync()
        self.update()

    def set_blocked(self, blocked):
        blocked = bool(blocked)
        if self.blocked != blocked:
            self.blocked = blocked
            self.sync()

    def sync(self):
        if self.path and not self.blocked and self.isVisible():
            self.player.play()
        elif self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()

    def receive_frame(self, frame):
        now = time.monotonic()
        if self.blocked or not frame.isValid() or now - self.last_frame < 1 / 24:
            return
        self.last_frame = now
        image = frame.toImage()
        if not image.isNull():
            self.frame = image.scaled(1280, 720, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
            self.update()

    def on_error(self, *_):
        if self.path:
            self.player.stop()
            self.path = ''
            self.frame = QImage()
            self.update()
            self.failed.emit('Não foi possível abrir o vídeo de fundo: ' + self.player.errorString())

    def hideEvent(self, event):
        self.player.pause()
        super().hideEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.sync()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('#030405'))
        if not self.frame.isNull():
            # Cover without stretching; avoid allocating another image per repaint.
            from PySide6.QtCore import QRectF
            source = QRectF(self.frame.rect())
            scale = max(self.width() / source.width(), self.height() / source.height())
            width, height = self.width() / scale, self.height() / scale
            source.setRect((source.width()-width)/2, (source.height()-height)/2, width, height)
            painter.drawImage(QRectF(self.rect()), self.frame, source)
            painter.fillRect(self.rect(), QColor(3, 4, 5, round(255 * self.dim / 100)))
        glow = QRadialGradient(self.rect().topRight(), max(1, self.width()))
        color = QColor(current_palette()['accent'])
        color.setAlpha(12)
        glow.setColorAt(0, color)
        color.setAlpha(0)
        glow.setColorAt(1, color)
        painter.fillRect(self.rect(), glow)
