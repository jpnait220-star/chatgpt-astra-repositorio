from __future__ import annotations
import random
import hashlib
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QUrl, Signal, QProcess
from PySide6.QtGui import QPainter, QColor, QPixmap, QPainterPath
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFileDialog,
    QListWidget,
    QSlider,
    QLineEdit,
    QCheckBox,
    QTabWidget,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from .widgets import Page, Tip, card, label, button
from .spotify import SpotifyPanel
from .visuals import motion_enabled
from .media import Media
from .config import data_dir


class Vinyl(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(175, 175)
        self.angle = 0
        self.cover = QPixmap()
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.rotate)

    def rotate(self):
        if not self.isVisible():
            return
        self.angle = (self.angle + 1.2) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(self.width() / 2, self.height() / 2)
        p.scale(self.width() / 175, self.height() / 175)
        p.rotate(self.angle)
        p.setBrush(QColor("#090b10"))
        p.setPen(QColor("#353b47"))
        p.drawEllipse(-80, -80, 160, 160)
        for r in range(34, 78, 6):
            p.drawEllipse(-r, -r, r * 2, r * 2)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#ead06d"))
        p.drawEllipse(-32, -32, 64, 64)
        if not self.cover.isNull():
            path = QPainterPath()
            path.addEllipse(-31, -31, 62, 62)
            p.setClipPath(path)
            p.drawPixmap(-31, -31, 62, 62, self.cover)
            p.setClipping(False)
        p.setBrush(QColor("#11151b"))
        p.drawEllipse(-4, -4, 8, 8)
        p.end()


class MusicPage(Page):
    trackChanged = Signal(str)

    def __init__(self, settings, save, notify):
        super().__init__(
            "Sua trilha sonora.",
            "Suas músicas locais, prévias e controles do Spotify em um só lugar.",
        )
        self.settings = settings
        self.save = save
        self.notify = notify
        self.paths = []
        self.index = -1
        self.current_title = ""
        self.history = []
        self.media_tools = Media(getattr(settings, "ffmpeg_dir", ""))
        self._fallback_attempted = False
        self._fallback_process = None
        self._play_generation = 0
        self._selected_source_path = None
        self._fallback_target = None
        self._fallback_temp = None
        self._start_watchdog = QTimer(self)
        self._start_watchdog.setSingleShot(True)
        self._start_watchdog.timeout.connect(self.check_media_start)
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.audio.setVolume(0.72)
        self.tabs = QTabWidget()
        local_page = QWidget()
        local_body = QVBoxLayout(local_page)
        local_body.setContentsMargins(0, 18, 0, 0)
        local_body.setSpacing(18)
        spotify_page = QWidget()
        spotify_body = QVBoxLayout(spotify_page)
        spotify_body.setContentsMargins(0, 18, 0, 0)
        spotify_body.setSpacing(18)
        self.tabs.addTab(local_page, "Músicas locais")
        self.tabs.addTab(spotify_page, "Spotify")
        self.body.addWidget(self.tabs, 1)
        frame = card()
        row = QHBoxLayout(frame)
        row.setContentsMargins(22, 20, 22, 20)
        self.vinyl = Vinyl()
        row.addWidget(self.vinyl)
        info = QVBoxLayout()
        info.addWidget(label("PLAYER LOCAL", "eyebrow"))
        self.title = label("Escolha sua primeira música", "subheading")
        info.addWidget(self.title)
        self.playback_note = label("Escolha uma pasta ou adicione arquivos de música para começar.", "tiny", True)
        info.addWidget(self.playback_note)
        self.position = QSlider(Qt.Orientation.Horizontal)
        self.position.setRange(0, 0)
        self.position.sliderMoved.connect(self.player.setPosition)
        info.addWidget(self.position)
        timeline = QHBoxLayout()
        self.elapsed_label = label("00:00", "tiny")
        self.duration_label = label("00:00", "tiny")
        timeline.addWidget(self.elapsed_label)
        timeline.addStretch()
        timeline.addWidget(self.duration_label)
        info.addLayout(timeline)
        controls = QHBoxLayout()
        controls.addWidget(button("⏮  Anterior", self.previous))
        self.play_button = button("⏯  Reproduzir", self.toggle, True)
        controls.addWidget(self.play_button)
        controls.addWidget(button("Próxima  ⏭", self.next))
        info.addLayout(controls)
        options = QHBoxLayout()
        self.shuffle = QCheckBox("Aleatório")
        self.repeat = QCheckBox("Repetir")
        options.addWidget(self.shuffle)
        options.addWidget(self.repeat)
        volume = QSlider(Qt.Orientation.Horizontal)
        volume.setRange(0, 100)
        volume.setValue(72)
        volume.valueChanged.connect(lambda value: self.audio.setVolume(value / 100))
        options.addWidget(label("Volume", "muted"))
        options.addWidget(volume)
        info.addLayout(options)
        row.addLayout(info, 1)
        local_body.addWidget(frame)
        folderrow = QHBoxLayout()
        self.folder = label(settings.music_dir, "muted", True)
        folderrow.addWidget(self.folder, 1)
        folderrow.addWidget(button("Adicionar músicas", self.add_music_files, True))
        folderrow.addWidget(button("Escolher pasta", self.choose_folder))
        folderrow.addWidget(button("Atualizar", self.scan))
        local_body.addLayout(folderrow)
        self.list = QListWidget()
        self.list.setMinimumHeight(180)
        self.list.itemDoubleClicked.connect(lambda item: self.play(self.list.row(item)))
        local_body.addWidget(self.list, 1)
        spotify_body.addWidget(label("Sua conta permanece no Spotify. Controle a reprodução do aplicativo do Windows ou abra uma prévia pelo link.", "muted", True))
        spotify = QHBoxLayout()
        self.spotify = QLineEdit(settings.spotify if '/track/' in settings.spotify or '/playlist/' in settings.spotify or '/album/' in settings.spotify or settings.spotify.startswith('spotify:') else '')
        self.spotify.setPlaceholderText("Cole o link de uma música, álbum ou playlist")
        self.spotify.returnPressed.connect(self.open_spotify)
        spotify.addWidget(self.spotify, 1)
        from PySide6.QtWidgets import QApplication
        spotify.addWidget(button("Colar link", lambda: self.spotify.setText(QApplication.clipboard().text().strip())))
        spotify.addWidget(button("Abrir prévia", self.open_spotify))
        spotify_body.addLayout(spotify)
        spotify_body.addWidget(button("Abrir esse link no Spotify do PC", self.open_spotify_desktop))
        self.spotify_panel = SpotifyPanel()
        self.spotify_panel.trackChanged.connect(self.trackChanged)
        self.spotify_panel.opened.connect(self.pause_for_spotify)
        self.tabs.currentChanged.connect(self.spotify_tab_selected)
        spotify_body.addWidget(self.spotify_panel)
        spotify_body.addStretch()
        self.tip = Tip(
            "MusicDuck",
            "Coloque MP3, WAV, FLAC, OGG ou M4A na sua pasta. O áudio do sistema também pode incluir a música nos clipes.",
        )
        self.body.addWidget(self.tip)
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.duration_changed)
        self.player.playbackStateChanged.connect(self.state_changed)
        self.player.mediaStatusChanged.connect(self.status_changed)
        self.player.errorOccurred.connect(self.playback_error)
        self.scan()
        self.watch = QTimer(self)
        self.watch.setInterval(10000)
        self.watch.timeout.connect(self.scan)
        self.watch.start()

    def scan(self):
        folder = Path(self.settings.music_dir).expanduser()
        try:
            folder.mkdir(parents=True, exist_ok=True)
            supported = (".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac")
            paths = sorted(set(
                [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in supported]
                + [Path(p) for p in getattr(self.settings, "music_files", [])
                   if Path(p).is_file() and Path(p).suffix.lower() in supported]
            ))
        except OSError as error:
            self.notify(str(error))
            return
        if paths == self.paths:
            return
        previous = self.paths[self.index] if 0 <= self.index < len(self.paths) else None
        self.paths = paths
        self.list.clear()
        self.list.addItems([p.stem for p in paths])
        self.index = paths.index(previous) if previous in paths else -1
        if self.index >= 0:
            self.list.setCurrentRow(self.index)
        if not paths and self.index < 0:
            self.playback_note.setText("Nenhuma música encontrada. Clique em 'Adicionar músicas' e selecione seus arquivos.")

    def add_music_files(self):
        selected, _ = QFileDialog.getOpenFileNames(
            self,
            "Adicionar músicas ao DuckCapture",
            self.settings.music_dir,
            "Músicas (*.mp3 *.wav *.flac *.ogg *.m4a *.aac)",
        )
        if not selected:
            return
        existing = list(getattr(self.settings, "music_files", []))
        for path in selected:
            if path not in existing:
                existing.append(path)
        self.settings.music_files = existing
        self.save()
        self.scan()
        first = Path(selected[0])
        if first in self.paths:
            self.play(self.paths.index(first))

    def choose_folder(self):
        path = QFileDialog.getExistingDirectory(
            self, "Pasta de músicas", self.settings.music_dir
        )
        if path:
            self.settings.music_dir = path
            self.folder.setText(path)
            self.save()
            self.scan()

    def play(self, index):
        if not 0 <= index < len(self.paths):
            self.playback_note.setText("Adicione uma música primeiro para poder reproduzir.")
            return
        self.spotify_panel.close_player()
        self._cancel_conversion()
        self._play_generation += 1
        self._fallback_attempted = False
        self.index = index
        path = self.paths[index]
        self._selected_source_path = path
        self.playback_note.setText("Carregando música…")
        self.elapsed_label.setText("00:00")
        self.duration_label.setText("00:00")
        self.position.setRange(0, 0)
        title = path.stem
        self.vinyl.cover = QPixmap()
        try:
            from mutagen import File

            tags = File(path, easy=True)
            if tags and tags.get("title"):
                title = str(tags["title"][0])
            media = File(path)
            if media and media.tags:
                for key, value in media.tags.items():
                    if str(key).startswith("APIC"):
                        self.vinyl.cover.loadFromData(value.data)
                        break
                    if str(key) == "covr":
                        self.vinyl.cover.loadFromData(bytes(value[0]))
                        break
        except Exception:
            pass
        self.current_title = title
        self.title.setText(title)
        self.trackChanged.emit(title)
        self.list.setCurrentRow(index)
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(str(path.resolve())))
        self.player.play()
        self._start_watchdog.start(6000)

    def _cancel_conversion(self):
        process = self._fallback_process
        self._fallback_process = None
        if process is not None:
            process.kill()
            process.deleteLater()
        if self._fallback_temp is not None:
            self._fallback_temp.unlink(missing_ok=True)
            self._fallback_temp = None
        self._start_watchdog.stop()

    def duration_changed(self, value):
        self.position.setMaximum(value)
        self.duration_label.setText(self._format_ms(value))
        if value > 0:
            self.playback_note.setText("Pronto para ouvir")

    def playback_error(self, error, message=""):
        if self.index < 0:
            return
        # Some Windows Qt installations have no decoder for particular audio
        # formats. Use our bundled FFmpeg for a temporary WAV fallback.
        if not self._fallback_attempted:
            QTimer.singleShot(0, self._try_wav_fallback)
        else:
            self.playback_note.setText("Não foi possível tocar esta música. Tente outro arquivo ou formato.")
            self.notify("Erro no player de música: " + (message or self.player.errorString()))

    def check_media_start(self):
        # A player stuck at 0:00 for several seconds is almost always a failed
        # decoder/open operation even if the Qt backend claims "Playing".
        if (self.index >= 0 and self.player.position() == 0
                and self.player.playbackState() != QMediaPlayer.PlaybackState.PausedState
                and not self._fallback_attempted):
            self._try_wav_fallback()

    def _try_wav_fallback(self):
        if self._fallback_attempted or self._selected_source_path is None:
            return
        self._fallback_attempted = True
        self._start_watchdog.stop()
        if not self.media_tools.ffmpeg:
            self.playback_note.setText("Áudio indisponível: não foi possível encontrar o conversor integrado.")
            self.notify("Não foi possível abrir a música. Confira o formato do arquivo.")
            return
        source = self._selected_source_path
        try:
            stat = source.stat()
        except OSError:
            self.playback_note.setText("A música foi movida ou apagada.")
            return
        cache = data_dir() / "musicas_cache"
        cache.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(f"{source}|{stat.st_mtime_ns}|{stat.st_size}".encode()).hexdigest()[:22]
        target = cache / f"{digest}.wav"
        self.player.stop()
        if target.is_file() and target.stat().st_size > 44:
            self._play_wav(target)
            return
        temp = cache / f"{digest}.partial.wav"
        self._fallback_target = target
        self._fallback_temp = temp
        self.playback_note.setText("Preparando áudio compatível… Aguarde um instante.")
        proc = QProcess(self)
        self._fallback_process = proc
        proc.setProgram(self.media_tools.ffmpeg)
        proc.setArguments([
            "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-i", str(source), "-map", "0:a:0", "-vn",
            "-ac", "2", "-ar", "44100", "-c:a", "pcm_s16le", str(temp),
        ])
        generation = self._play_generation
        proc.finished.connect(lambda code, _status, g=generation: self._conversion_finished(g, code))
        proc.errorOccurred.connect(lambda _error, g=generation: self._conversion_start_error(g))
        proc.start()

    def _conversion_start_error(self, generation):
        if generation != self._play_generation:
            return
        proc = self._fallback_process
        if proc is not None and proc.error() == QProcess.ProcessError.FailedToStart:
            self.playback_note.setText("Não foi possível iniciar a conversão da música.")
            self.notify("O conversor de áudio não abriu. Reinstale o DuckCapture e tente novamente.")

    def _conversion_finished(self, generation, code):
        if generation != self._play_generation:
            return
        process = self._fallback_process
        self._fallback_process = None
        if process is not None:
            process.deleteLater()
        temp = self._fallback_temp
        target = self._fallback_target
        self._fallback_temp = None
        self._fallback_target = None
        if code == 0 and temp is not None and temp.is_file() and temp.stat().st_size > 44:
            try:
                temp.replace(target)
            except OSError as error:
                self.playback_note.setText("Erro ao preparar a música: " + str(error))
                return
            self._play_wav(target)
        else:
            if temp is not None:
                temp.unlink(missing_ok=True)
            self.playback_note.setText("Não foi possível ler essa música. Experimente MP3 ou WAV.")
            self.notify("O áudio não pôde ser reproduzido. Tente outra música.")

    def _play_wav(self, path):
        self.playback_note.setText("Abrindo áudio compatível…")
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(str(path)))
        self.player.play()

    def toggle(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        elif self.index < 0:
            if self.paths:
                self.play(0)
            else:
                self.playback_note.setText("Não há músicas na biblioteca. Clique em 'Adicionar músicas'.")
                self.add_music_files()
        else:
            self.spotify_panel.close_player()
            self.player.play()
            if self.player.position() == 0 and not self._fallback_attempted:
                self._start_watchdog.start(6000)

    def next(self):
        if not self.paths:
            return
        if self.index >= 0:
            self.history.append(self.index)
        choices = [i for i in range(len(self.paths)) if i != self.index]
        self.play(
            random.choice(choices)
            if self.shuffle.isChecked() and choices
            else (self.index + 1) % len(self.paths)
        )

    def previous(self):
        self.play(self.history.pop() if self.history else max(0, self.index - 1))

    def update_position(self, value):
        if not self.position.isSliderDown():
            self.position.setValue(value)
        self.elapsed_label.setText(self._format_ms(value))
        if value > 0:
            self._start_watchdog.stop()

    @staticmethod
    def _format_ms(value):
        total = max(0, int(value // 1000))
        minutes, seconds = divmod(total, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"

    def state_changed(self, state):
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.play_button.setText("⏸  Pausar" if playing else "⏯  Reproduzir")
        if playing:
            self.playback_note.setText("Reproduzindo")
            if motion_enabled():
                self.vinyl.timer.start()
            self.trackChanged.emit(self.current_title)
        else:
            self.vinyl.timer.stop()
            self.trackChanged.emit(
                "Pausado · " + self.current_title if self.current_title else ""
            )

    def status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.repeat.isChecked():
                self.player.setPosition(0)
                self.player.play()
            elif self.shuffle.isChecked() or self.index + 1 < len(self.paths):
                self.next()

    def pause_for_spotify(self):
        self._cancel_conversion()
        self._play_generation += 1
        self.player.pause()

    def spotify_tab_selected(self, index):
        self.spotify_panel.set_browser_active(index == 1)

    def hud_state(self):
        import time
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            title = getattr(self, 'current_title', '')
            return dict(music=title,music_artist='Biblioteca local',music_playing=True,
                        music_position=self.player.position()/1000,music_duration=self.player.duration()/1000)
        state = self.spotify_panel.desktop_state
        if state.get('connected') and state.get('title'):
            elapsed = max(0,time.monotonic()-getattr(self.spotify_panel,'desktop_updated_at',time.monotonic())) if state.get('playing') else 0
            duration = state.get('duration',0)
            position = state.get('position',0)+elapsed
            return dict(music=state.get('title',''),music_artist=state.get('artist',''),music_playing=state.get('playing',False),
                        music_position=min(duration,position) if duration else position,music_duration=duration)
        return dict(music=getattr(self,'current_title',''),music_artist='Biblioteca local',music_playing=False,
                    music_position=self.player.position()/1000,music_duration=self.player.duration()/1000)

    def open_spotify_desktop(self):
        from .spotify import embed_url
        try:
            self.spotify_panel.url = embed_url(self.spotify.text())
        except ValueError as error:
            self.notify(str(error))
            return
        self.spotify_panel.open_external()

    def open_spotify(self):
        url = self.spotify.text().strip()
        try:
            self.spotify_panel.load(url)
        except Exception as error:
            self.notify(str(error))
            return
        self.settings.spotify = url
        self.save()
