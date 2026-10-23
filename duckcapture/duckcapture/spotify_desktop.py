"""Control only the official Spotify Windows media session, without credentials."""
from __future__ import annotations
import asyncio
import sys
from PySide6.QtCore import QObject, QThread, QTimer, Signal


def is_spotify_session(session):
    app_id = session.source_app_user_model_id.lower()
    return app_id == 'spotify.exe' or app_id.startswith('spotifyab.spotifymusic_')


async def query_session(manager, command='status'):
    session = next((s for s in manager.get_sessions() if is_spotify_session(s)), None)
    if session is None:
        return {'connected': False, 'message': 'Abra o Spotify do Windows e toque uma música para conectar.'}
    if command != 'status':
        methods = {'toggle': 'try_toggle_play_pause_async', 'next': 'try_skip_next_async', 'previous': 'try_skip_previous_async'}
        if command not in methods:
            raise ValueError('Comando de reprodução inválido.')
        accepted = await getattr(session, methods[command])()
        if not accepted:
            return {'connected': True, 'message': 'O Spotify não liberou esse controle para a reprodução atual.'}
    properties = await session.try_get_media_properties_async()
    playback = session.get_playback_info()
    controls = playback.controls
    position, duration = 0., 0.
    if hasattr(session, 'get_timeline_properties'):
        try:
            timeline = session.get_timeline_properties()
            def seconds(value):
                return value.total_seconds() if hasattr(value, 'total_seconds') else float(value) / 10_000_000
            start = seconds(timeline.start_time)
            position = max(0., seconds(timeline.position) - start)
            duration = max(0., seconds(timeline.end_time) - start)
        except Exception:
            # Some Spotify sessions expose metadata before a usable timeline.
            # Keep the title and playback controls available in that interval.
            position, duration = 0., 0.
    # Windows enum: Closed=0, Opened=1, Changing=2, Stopped=3, Playing=4, Paused=5.
    return {
        'connected': True, 'title': properties.title or 'Spotify',
        'artist': properties.artist or '', 'playing': int(playback.playback_status) == 4,
        'position': position, 'duration': duration,
        'toggle': bool(controls.is_play_pause_toggle_enabled),
        'next': bool(controls.is_next_enabled), 'previous': bool(controls.is_previous_enabled),
    }


class SessionTask(QThread):
    result = Signal(dict)

    def __init__(self, command, parent=None):
        super().__init__(parent)
        self.command = command

    def run(self):
        if sys.platform != 'win32':
            self.result.emit({'connected': False, 'message': 'A conexão com o aplicativo Spotify está disponível no Windows.'})
            return
        try:
            import winrt.runtime
            from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager
            winrt.runtime.init_apartment(winrt.runtime.ApartmentType.MULTI_THREADED)
            try:
                async def request():
                    manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()
                    return await query_session(manager, self.command)
                async def bounded_request():
                    return await asyncio.wait_for(request(), timeout=5)
                self.result.emit(asyncio.run(bounded_request()))
            finally:
                winrt.runtime.uninit_apartment()
        except ImportError:
            self.result.emit({'connected': False, 'message': 'Atualize a instalação do DuckCapture para conectar o Spotify do Windows.'})
        except (TimeoutError, asyncio.TimeoutError):
            self.result.emit({'connected': False, 'message': 'O Spotify demorou a responder. Tente conectar novamente.'})
        except Exception:
            self.result.emit({'connected': False, 'message': 'Não foi possível conectar ao Spotify. Abra o aplicativo e tente novamente.'})


class SpotifyDesktop(QObject):
    changed = Signal(dict)
    busyChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.task = None
        self.closed = False
        self.timer = QTimer(self)
        self.timer.setInterval(2500)
        self.timer.timeout.connect(self.refresh)

    def refresh(self, command='status'):
        if self.closed or (self.task and self.task.isRunning()):
            return
        if self.task:
            self.task.deleteLater()
        self.task = SessionTask(command, self)
        self.task.result.connect(self.changed)
        self.task.finished.connect(lambda: self.busyChanged.emit(False))
        self.busyChanged.emit(True)
        self.task.start()

    def set_active(self, active):
        if active and not self.closed:
            if not self.timer.isActive():
                self.refresh()
                self.timer.start()
        else:
            self.timer.stop()

    def shutdown(self):
        self.closed = True
        self.timer.stop()
        if self.task and self.task.isRunning():
            # Every request has a five-second deadline; never destroy a live QThread.
            self.task.wait()
