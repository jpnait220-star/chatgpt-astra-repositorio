"""Silent local wallpaper; decoding stops while recording or out of sight."""
import time
from pathlib import Path
from PySide6.QtCore import QUrl, Signal, QThread
from PySide6.QtGui import QImage, QPainter, QColor, QRadialGradient
from PySide6.QtWidgets import QWidget
from PySide6.QtMultimedia import QMediaPlayer, QVideoSink, QAudioOutput
from .theme import current_palette
from .media_jobs import MediaJob
from .frame_pacer import SourceFramePacer
from .media import Media


class PosterTask(QThread):
    """Decode one still even while animated wallpaper is paused for capture."""
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path
        self.result = QImage()
        self.error = ''

    def run(self):
        try:
            data = Media().run(['-threads', '1', '-i', self.path, '-an',
                '-vf', 'scale=w=min(iw\\,1920):h=min(ih\\,1080):force_original_aspect_ratio=decrease',
                '-frames:v', '1', '-c:v', 'png', '-threads', '1', '-f', 'image2pipe', 'pipe:1'], timeout=15).stdout
            self.result = QImage.fromData(data)
            if self.result.isNull():
                self.error = 'O vídeo não contém uma imagem legível.'
        except Exception as error:
            self.error = str(error)


class VideoBackground(QWidget):
    failed = Signal(str)
    preparing = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.frame = QImage()
        self.dim = 72
        self.path = ''
        self.blocked = True
        self.last_frame = 0.
        self.pacer = SourceFramePacer(24)
        self.job = None
        self.prepared_path = ''
        self.generation = 0
        self.poster_job = None
        self.poster_generation = None
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
        self.generation += 1
        if self.job:
            self.job.cancel()
        self.player.stop()
        self.player.setSource(QUrl())
        self.prepared_path = ''
        self.frame = QImage()
        self.last_frame = 0.
        self.pacer = SourceFramePacer(24)
        self.path = str(path or '')
        if self.path and not Path(self.path).is_file():
            self.path = ''
            self.failed.emit('O vídeo de fundo foi movido. Selecione o arquivo novamente.')
        self.sync()
        self.update()

    def set_blocked(self, blocked):
        blocked = bool(blocked)
        if self.blocked != blocked:
            self.blocked = blocked
            if blocked and self.job:
                self.job.cancel()
            self.sync()

    def shutdown(self):
        self.blocked = True
        self.generation += 1
        if self.job:
            self.job.cancel()
            self.job.wait()
        if self.poster_job:
            self.poster_job.wait()
        self.player.stop()
        self.player.setSource(QUrl())  # Release the Windows file handle as well.
        self.path = ''
        self.frame = QImage()

    def sync(self):
        if self.path and self.isVisible() and self.poster_job is None and self.poster_generation != self.generation:
            self.prepare_poster()
        if self.path and not self.blocked and self.isVisible():
            if self.prepared_path:
                self.player.play()
            elif self.job is None:
                self.prepare()
        elif self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()

    def prepare_poster(self):
        generation = self.generation
        self.poster_generation = generation
        job = PosterTask(self.path, self)
        self.poster_job = job
        def ready():
            self.poster_job = None
            if generation == self.generation and self.frame.isNull():
                if not job.result.isNull():
                    self.frame = job.result
                    self.update()
                    if self.blocked:
                        self.preparing.emit('Papel de parede visível. Animação pausada para priorizar a captura ou reduzir movimento.')
                elif job.error:
                    self.failed.emit('Não foi possível ler a imagem do papel de parede: ' + job.error)
            job.deleteLater()
            self.sync()
        job.finished.connect(ready)
        job.start()

    def prepare(self):
        # Prepare for the screen's physical pixels, not a hard-coded 720p frame.
        screen = self.screen()
        ratio = screen.devicePixelRatio() if screen else 1
        geometry = screen.size() if screen else self.size()
        width = min(2560, max(1280, round(geometry.width() * ratio)))
        height = min(1440, max(720, round(geometry.height() * ratio)))
        generation = self.generation
        job = MediaJob(self.path, 'wallpaper', size=(width, height), parent=self)
        self.job = job
        self.preparing.emit('Preparando papel de parede nítido e leve…')
        job.progress.connect(lambda percent, message: self.preparing.emit(f'{message} {percent}%') if generation == self.generation else None)
        job.failed.connect(lambda message: self.on_prepare_error(message, generation))
        def ready():
            self.job = None
            if generation == self.generation and job.result and not job.cancelled.is_set():
                self.prepared_path = job.result
                self.player.setSource(QUrl.fromLocalFile(job.result))
                self.preparing.emit('Papel de parede pronto.')
            job.deleteLater()
            self.sync()
        job.finished.connect(ready)
        job.start()

    def on_prepare_error(self, message, generation):
        if generation == self.generation:
            self.path = ''
            self.failed.emit('O fundo permanece estático. Não foi possível preparar a animação: ' + message)

    def receive_frame(self, frame):
        now = time.monotonic()
        if self.blocked or not frame.isValid():
            return
        timestamp = frame.startTime() / 1_000_000 if frame.startTime() >= 0 else now
        if not self.pacer.allow(timestamp):
            return
        self.last_frame = now
        image = frame.toImage()
        if not image.isNull():
            self.frame = image
            self.update()

    def on_error(self, *_):
        if self.path:
            self.player.stop()
            self.path = ''
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
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
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
