from __future__ import annotations
import copy
import csv
import logging
import os
import queue
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
import numpy as np
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image
from .audio import AudioRing
from .clip_sound import mix_clip_chime
from .frame_pacer import SourceFramePacer, FrameWaiter
from .config import Settings, atomic_json, data_dir
from .hud import write_hud, copy_fonts
from .windows import window_exists, window_minimized
from .fullscreen import process_id, is_target_foreground, monitor_for_fullscreen, replacement_window
from .media import Media, MediaError, CREATE_FLAGS


class CaptureEngine:
    # One FFmpeg export at a time keeps GPU/CPU usage stable during gameplay.
    # Extra F8 presses wait here instead of being rejected.
    MAX_PENDING_CLIPS = 6

    def __init__(
        self,
        media: Media,
        source_factory=None,
        window_exists_fn=None,
        window_minimized_fn=None,
    ):
        self.media = media
        self.source_factory = source_factory
        self.is_window = window_exists_fn or (
            window_exists if source_factory is None else lambda hwnd: True
        )
        self.is_minimized = window_minimized_fn or (
            window_minimized if source_factory is None else lambda hwnd: False
        )
        self.events = queue.Queue()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="duck-export")
        self.active = False
        self.starting = False
        self.latest = None
        self.frame_queue = deque(maxlen=4)  # Small jitter buffer to avoid duplicated frames.
        self.lock = threading.RLock()
        self.done = threading.Event()
        self.samples = deque()
        self.frames = 0
        self.epoch = 0
        self.control = None
        self.audio = None
        self.session = None
        self.encoder = ""
        self.pending = 0
        self._snapshots_pending = 0
        self.pinning = False
        self.error = None
        self.source = None
        self.audio_warning = ""
        self.thread = None
        self.source_generation = 0
        self.source_closed = threading.Event()
        self.received = threading.Event()
        self.source_size = None
        self.state_message = ""
        self.last_source_attempt = 0.0
        self.source_retries = 0
        self.writer_finished = threading.Event()
        self.writer_finished.set()
        self.restart_thread = None
        self.fitted_source = None
        self.fitted_frame = None
        self.source_fps = 0.0
        self.output_fps = 0.0
        self.last_frame_at = 0.0
        self._late_warning_at = 0.0
        self._last_encoded_source = None
        self._last_encoded_size = None
        self._last_encoded_bytes = None
        self.capture_mode = "window"
        self.monitor_index = None
        self.target_pid = None
        self._last_mode_check = 0.0

    @property
    def elapsed(self):
        return self.frames / self.settings.fps if hasattr(self, "settings") else 0

    def start(self, hwnd, settings: Settings):
        if (
            self.active
            or self.starting
            or self.pending
            or self.thread
            and self.thread.is_alive()
            or self.restart_thread
            and self.restart_thread.is_alive()
        ):
            raise RuntimeError("A captura já está em andamento.")
        if os.name != "nt" and self.source_factory is None:
            raise RuntimeError(
                "A captura de janelas está disponível no Windows 10/11. Editor, HUD e música também podem ser abertos nesta máquina."
            )
        if self.is_minimized(hwnd):
            raise RuntimeError(
                "Restaure a janela para iniciar. Depois você pode minimizá-la sem encerrar a sessão."
            )
        self.starting = True
        self.error = None
        self.audio_warning = ""
        self.settings = copy.deepcopy(settings)
        self.hwnd = hwnd
        self.target_pid = process_id(hwnd)
        self.capture_mode = "window"
        self.monitor_index = None
        self._last_mode_check = 0.0
        if self.session and self.session.exists():
            shutil.rmtree(self.session, ignore_errors=True)
        self.done.clear()
        self.latest = None
        self.frame_queue.clear()
        self.frames = 0
        self.samples.clear()
        self.audio = None
        self.session = None
        self.writer_finished.clear()
        self.source_size = None
        self.fitted_source = self.fitted_frame = None
        self.state_message = ""
        self.source_retries = 0
        self.source_fps = 0.0
        self.output_fps = 0.0
        self.last_frame_at = 0.0
        self._late_warning_at = 0.0
        self._last_encoded_source = None
        self._last_encoded_size = None
        self._last_encoded_bytes = None
        self.thread = threading.Thread(
            target=self._start, daemon=True, name="duck-capture"
        )
        self.thread.start()

    def _start(self):
        process = None
        log = None
        waiter = FrameWaiter()
        try:
            self.media.require()
            try:
                import cv2
                cv2.setNumThreads(1 if self.settings.performance_mode else 2)
            except ImportError:
                pass
            self.events.put(("preparing", "Conectando à janela selecionada…"))
            # F11 may already be active when recording starts.
            self._detect_fullscreen(force=True)
            self._open_source()
            deadline = time.monotonic() + 10
            while not self.received.wait(0.05):
                if self.done.is_set():
                    raise InterruptedError()
                if self.control.is_finished():
                    self.control.wait()  # Propagate the native Windows error.
                    raise RuntimeError(
                        "O Windows encerrou a captura antes do primeiro quadro."
                    )
                if time.monotonic() >= deadline:
                    raise RuntimeError(
                        "Nenhum quadro recebido. Restaure a janela e use modo janela/sem bordas no jogo."
                    )
            if self.done.is_set():
                raise InterruptedError()
            buffer_root = data_dir() / "buffer"
            buffer_root.mkdir(exist_ok=True)
            self.session = Path(tempfile.mkdtemp(prefix="replay-", dir=buffer_root))
            height, width = self.latest.shape[:2]
            self.size = (width, height)
            # Encode a smaller frame when light mode is enabled. This also
            # reduces the huge BGRA stream transferred into FFmpeg every frame.
            resolution_limits = {"720p": 1280, "1080p": 1920, "1440p": 2560, "4K": 3840, "Origem": width}
            quality_limits = (
                {"Econômico": 960, "Equilibrado": 1280, "Alta qualidade": 1920, "Full": width}
                if self.settings.performance_mode else
                {"Econômico": 1280, "Equilibrado": 1920, "Alta qualidade": 2560, "Full": width}
            )
            maximum = min(width, quality_limits[self.settings.quality], resolution_limits.get(getattr(self.settings, "resolution", "1080p"), width))
            out_width = max(2, min(width, maximum) // 2 * 2)
            out_height = max(2, round(height * out_width / width) // 2 * 2)
            self.output_size = (out_width, out_height)
            self.encoder = self.media.encoder(
                self.settings.encoder,
                self.output_size,
                self.settings.quality,
                self.settings.fps,
                self.done,
                lambda message: self.events.put(("preparing", message)),
                realtime=True,
                bitrate_mbps=getattr(self.settings, "bitrate_mbps", 0),
            )
            if self.done.is_set():
                raise InterruptedError()
            if self.settings.system_audio and getattr(self.settings, "audio_mode", "Som do PC (jogo, Discord, navegador)") != "Sem áudio":
                self.events.put(("preparing", "Preparando áudio do sistema…"))
                self.audio = AudioRing()
                try:
                    self.audio.start()
                except Exception as error:
                    self.audio.stop()
                    self.audio = None
                    self.audio_warning = (
                        "Gravando SEM ÁUDIO: "
                        + str(error)
                        + " Confira a saída de som do Windows e reinicie a captura para tentar novamente."
                    )
                    logging.exception("Áudio indisponível; mantendo vídeo")
                    self.events.put(("warning", self.audio_warning))
            if self.done.is_set():
                raise InterruptedError()
            self.events.put(("preparing", "Iniciando gravação do replay…"))
            args = [
                self.media.ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-filter_threads",
                "2",
                "-y",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "bgra",
                "-s",
                f"{out_width}x{out_height}",
                "-r",
                str(self.settings.fps),
                "-i",
                "pipe:0",
                "-an",
                *self.media.encoding(
                    self.encoder,
                    self.settings.quality,
                    self.settings.fps,
                    realtime=True,
                    bitrate_mbps=getattr(self.settings, "bitrate_mbps", 0),
                ),
                "-force_key_frames",
                "expr:gte(t,n_forced*2)",
                "-f",
                "segment",
                "-segment_time",
                "2",
                "-segment_time_delta",
                str(0.5 / self.settings.fps),
                "-segment_list_flags",
                "+live",
                "-flush_packets",
                "1",
                "-reset_timestamps",
                "1",
                "-segment_list",
                str(self.session / "segments.csv"),
                "-segment_list_type",
                "csv",
                "-segment_list_size",
                str(self.settings.duration // 2 + 12),
                str(self.session / "frame-%09d.mkv"),
            ]
            log = open(self.session / "encoder.log", "wb")
            process = subprocess.Popen(
                args,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=log,
                creationflags=CREATE_FLAGS,
            )
            self.epoch = time.monotonic()
            rate_started, rate_frames = self.epoch, 0
            with self.lock:
                self.frame_queue.clear()  # Drop frames captured while the encoder/audio were being prepared.
            while not self.done.is_set():
                target = self.epoch + self.frames / self.settings.fps
                remaining = target - time.monotonic()
                if remaining > 0:
                    waiter.wait(remaining, self.done)
                if self.done.is_set():
                    break
                self._maintain_source()
                delay = time.monotonic() - target
                # A short stall while the game loads should not kill the replay.
                # Keep attempting to catch up with the timeline; report prolonged
                # overload so the user can select 30 FPS or Econômico.
                if delay > 0.75 and time.monotonic() - self._late_warning_at > 12:
                    self._late_warning_at = time.monotonic()
                    self.events.put(("performance_warning",
                        "Captura sobrecarregada. Experimente 30 FPS e qualidade Econômico; "
                        "a gravação vai tentar se recuperar."))
                if delay > 6:
                    raise RuntimeError(
                        "A gravação ficou mais de 6 s atrasada. Reduza o FPS/qualidade, "
                        "ative o Modo leve e selecione o codificador da GPU."
                    )
                with self.lock:
                    pixels = self.frame_queue.popleft() if self.frame_queue else self.latest
                if pixels is None:
                    continue
                process.stdin.write(
                    self._frame_payload(pixels, width, height, out_width, out_height)
                )
                self.frames += 1
                rate_frames += 1
                now = time.monotonic()
                if now - rate_started >= 1:
                    self.output_fps = rate_frames / (now - rate_started)
                    rate_started, rate_frames = now, 0
                if self.audio and self.audio.error:
                    self.audio_warning = (
                        "O áudio do sistema parou: "
                        + str(self.audio.error)
                        + ". O vídeo continua; reinicie a captura após conferir a saída de som."
                    )
                    self.audio.stop()
                    self.audio = None
                    self.events.put(("warning", self.audio_warning))
                if self.frames % self.settings.fps == 0:
                    self._prune()
                if process.poll() is not None:
                    raise RuntimeError(
                        "O codificador parou. Veja encoder.log na pasta de dados."
                    )
                if not self.active and self.frames >= 5:
                    self.active = True
                    self.starting = False
                    self.events.put(
                        (
                            "started",
                            f"{self.encoder} · {out_width}×{out_height} · {self.settings.fps} FPS",
                        )
                    )
        except InterruptedError:
            pass
        except Exception as error:
            self.error = str(error)
            logging.exception("Falha na captura")
            if self.session and (self.session / "encoder.log").exists():
                try:
                    with (self.session / "encoder.log").open("rb") as stream:
                        stream.seek(
                            max(
                                0, (self.session / "encoder.log").stat().st_size - 12000
                            )
                        )
                        (data_dir() / "last-encoder.log").write_bytes(stream.read())
                except OSError:
                    pass
            if isinstance(error, (BrokenPipeError, OSError)) and process is not None:
                try:
                    detail = (self.session / "encoder.log").read_text(
                        encoding="utf-8", errors="replace"
                    )[-2000:]
                except OSError:
                    detail = ""
                self.error = (
                    "O codificador não conseguiu iniciar ou continuar a gravação. Tente Automático/libx264 e 30 FPS.\n"
                    + (detail or str(error))
                )
            self.events.put(("capture_error", self.error))
        finally:
            waiter.close()
            self.done.set()
            self.starting = False
            self.active = False
            if self.control:
                try:
                    self.control.stop()
                except Exception:
                    pass
                self.control = None
            if self.restart_thread:
                self.restart_thread.join(timeout=3)
            if process:
                try:
                    process.stdin.close()
                    process.wait(timeout=15)
                except (OSError, subprocess.TimeoutExpired):
                    process.kill()
                    process.wait()
            self.writer_finished.set()
            if log:
                log.close()
            if self.audio:
                self.audio.stop()
            self.events.put(
                (
                    "stopped",
                    "Captura parada. Os clipes já salvos continuam na biblioteca.",
                )
            )

    def _frame_payload(self, source, width, height, out_width, out_height):
        """Reuse the encoded-input bytes while the capture source is unchanged.

        FFmpeg still receives every expected frame, preserving replay timing.
        This cuts redundant CPU work when the game briefly repeats a frame.
        """
        if (source is self._last_encoded_source and self._last_encoded_bytes is not None
                and self._last_encoded_size == (out_width, out_height)):
            return self._last_encoded_bytes
        # Fit straight to the encoded dimensions, including after F11/resizing.
        # Scaling to the old window size and then again to the output wastes a
        # full resize and several large frame copies on every frame.
        pixels = self._fit_frame(source, out_width, out_height)
        self._last_encoded_size = (out_width, out_height)
        self._last_encoded_bytes = memoryview(np.ascontiguousarray(pixels)).cast("B")
        self._last_encoded_source = source
        return self._last_encoded_bytes

    def _open_source(self):
        self.source_generation += 1
        generation = self.source_generation
        previous, self.control = self.control, None
        if previous:
            try:
                previous.stop()
            except Exception:
                logging.debug("Captura anterior já encerrada", exc_info=True)
        factory = self.source_factory
        if factory is None:
            from windows_capture import WindowsCapture

            factory = WindowsCapture
        target = ({"monitor_index": self.monitor_index}
                  if self.capture_mode == "monitor" else {"window_hwnd": self.hwnd})
        source_mode = self.capture_mode
        source = factory(
            **target,
            cursor_capture=self.settings.cursor,
            draw_border=None,
            minimum_update_interval=None,
        )
        self.source = source
        self.source_closed.clear()
        self.received.clear()
        pacer = SourceFramePacer(self.settings.fps)
        count = 0
        interval_start = time.monotonic()

        @source.event
        def on_frame_arrived(frame, capture_control):
            nonlocal count, interval_start
            if self.done.is_set() or generation != self.source_generation:
                capture_control.stop()
                return
            now = time.monotonic()
            # A fixed gap from the last accepted callback aliases 75-110 Hz
            # sources into ~38-55 unique FPS at a 60 FPS target. Keep a
            # phase-locked deadline instead, so accepted frames average the
            # requested FPS while still copying at most one frame per callback.
            # WGC timestamps are 100 ns ticks. Callback scheduling jitter must
            # not be mistaken for a slow/fast game and discard useful frames.
            timestamp = getattr(frame, 'timespan', None)
            source_time = timestamp / 10_000_000 if isinstance(timestamp, (int, float)) and timestamp > 0 else now
            if not pacer.allow(source_time):
                return
            if source_mode == "monitor":
                # Monitor capture contains everything visible. Never retain
                # frames when the game is not the foreground application.
                if not is_target_foreground(self.hwnd, self.target_pid):
                    return
            elif self.is_minimized(self.hwnd):
                return
            pixels = frame.frame_buffer.copy()
            if pixels.shape[0] < 2 or pixels.shape[1] < 2:
                return
            with self.lock:
                self.latest = pixels
                self.frame_queue.append(pixels)
            self.received.set()
            self.last_frame_at = now
            count += 1
            interval = now - interval_start
            if interval >= 1.25:
                self.source_fps = count / interval
                logging.debug("Replay source: %.1f unique frames/s (goal %s)",
                              self.source_fps, self.settings.fps)
                interval_start = now
                count = 0

        @source.event
        def on_closed():
            if generation == self.source_generation:
                self.source_closed.set()

        control = source.start_free_threaded()
        if self.done.is_set():
            control.stop()
            return
        self.control = control
        self.last_source_attempt = time.monotonic()

    def _source_status(self, message):
        if message != self.state_message:
            self.state_message = message
            self.events.put(("source_status", message))

    def _detect_fullscreen(self, *, force=False):
        """Switch the active WGC source when F11 changes how the game renders."""
        now = time.monotonic()
        if not force and now - self._last_mode_check < 0.35:
            return False
        self._last_mode_check = now
        enabled = getattr(self.settings, "fullscreen_compatibility", True)
        monitor = monitor_for_fullscreen(self.hwnd, self.target_pid) if enabled else None
        desired = "monitor" if monitor is not None else "window"
        if desired == self.capture_mode and (desired != "monitor" or monitor == self.monitor_index):
            return False
        self.capture_mode = desired
        self.monitor_index = monitor
        # Old pixels belong to a different window or resolution. Restart the
        # frame buffer smoothly without discarding the last already encoded frame.
        with self.lock:
            self.frame_queue.clear()
        if desired == "monitor":
            self._source_status(
                "F11 detectado: capturando o monitor do jogo. "
                "Ao sair do jogo, o DuckCapture não registra outras janelas."
            )
        else:
            self._source_status("Voltando à captura da janela do jogo…")
        return True

    def _maintain_source(self):
        if not self.is_window(self.hwnd):
            new_hwnd = replacement_window(self.hwnd, self.target_pid)
            if not new_hwnd:
                raise RuntimeError(
                    "A janela selecionada foi fechada. Os clipes salvos foram preservados."
                )
            self.hwnd = new_hwnd
            with self.lock:
                self.frame_queue.clear()
            self.source_closed.set()
        if self.restart_thread and self.restart_thread.is_alive():
            return
        switched = self._detect_fullscreen()
        if self.is_minimized(self.hwnd) and self.capture_mode != "monitor":
            self._source_status(
                "Janela minimizada: mantendo o último quadro e o áudio. A imagem retorna ao restaurar."
            )
            return
        finished = (
            switched or self.source_closed.is_set()
            or self.control is None or self.control.is_finished()
            or (self.last_frame_at and time.monotonic() - self.last_frame_at > 2.5)
        )
        if finished:
            if not switched:
                self._source_status(
                    "Reconectando à janela; o replay mantém o último quadro e o áudio…"
                )
            if switched or time.monotonic() - self.last_source_attempt >= 1.0:
                self.source_retries += 1

                def reconnect():
                    try:
                        self._open_source()
                    except Exception:
                        logging.exception("Tentativa de reconectar à janela")
                        self.last_source_attempt = time.monotonic()

                self.restart_thread = threading.Thread(
                    target=reconnect, daemon=True, name="duck-reconnect"
                )
                self.restart_thread.start()
                if self.source_retries >= 10:
                    raise RuntimeError(
                        "O jogo deixou de fornecer imagens após várias tentativas. "
                        "Use modo janela sem bordas nas opções do Minecraft."
                    )
        elif self.received.is_set():
            self.source_retries = 0
            if self.capture_mode == "window":
                self._source_status("")

    @staticmethod
    def _resize_channels(pixels, size):
        # BGRA capture bytes are independent channels, not premultiplied RGBA.
        # Pillow's default RGBA resize zeroes RGB for transparent source pixels.
        return np.stack([
            np.asarray(Image.fromarray(pixels[:, :, channel]).resize(size, Image.Resampling.BILINEAR))
            for channel in range(pixels.shape[2])
        ], axis=2)

    def _fit_frame(self, pixels, width, height):
        h, w = pixels.shape[:2]
        if (w, h) == (width, height):
            return pixels
        if pixels is self.fitted_source and self.fitted_frame.shape[:2] == (height, width):
            return self.fitted_frame
        if self.source_size != (w, h):
            self.source_size = (w, h)
            self.events.put(
                (
                    "resized",
                    f"Janela ajustada para {w}×{h}. O clipe mantém a resolução inicial, sem distorcer a imagem.",
                )
            )
        ratio = min(width / w, height / h)
        nw, nh = max(1, round(w * ratio)), max(1, round(h * ratio))
        try:
            import cv2

            resized = cv2.resize(
                pixels,
                (nw, nh),
                interpolation=(cv2.INTER_AREA if ratio < 1 and not getattr(getattr(self, "settings", None), "performance_mode", True) else cv2.INTER_LINEAR),
            )
        except ImportError:
            # Same per-channel interpolation in the portable test environment.
            resized = self._resize_channels(pixels, (nw, nh))
        if (nw, nh) == (width, height):
            self.fitted_source, self.fitted_frame = pixels, resized
            return resized
        result = np.zeros((height, width, 4), dtype=np.uint8)
        result[:, :, 3] = 255
        x, y = (width - nw) // 2, (height - nh) // 2
        result[y : y + nh, x : x + nw] = resized
        self.fitted_source, self.fitted_frame = pixels, result
        return result

    def _segments(self):
        if not self.session:
            return []
        found = {}
        try:
            with (self.session / "segments.csv").open(
                encoding="utf-8-sig", newline=""
            ) as stream:
                for row in csv.reader(stream):
                    if len(row) != 3:
                        continue
                    try:
                        # Only files within this capture session are valid.
                        name = row[0].replace("\\", "/").rsplit("/", 1)[-1]
                        path = self.session / name
                        start, end = float(row[1]), float(row[2])
                        if path.is_file() and end > start:
                            found[path] = (path, start, end)
                    except (ValueError, OSError):
                        continue
        except (OSError, UnicodeError, csv.Error):
            pass
        # The next numbered file is opened only after the preceding segment
        # closes. Use that fact when the CSV is empty, stale or temporarily locked.
        paths = sorted(self.session.glob("frame-*.mkv"))
        for path in paths[:-1]:
            if path not in found:
                try:
                    index = int(path.stem.split("-")[-1])
                    found[path] = (path, index * 2.0, (index + 1) * 2.0)
                except ValueError:
                    continue
        return sorted(found.values(), key=lambda segment: segment[1])

    @staticmethod
    def _snapshot_segment(source, target, *, allow_link=True):
        """Re-use completed video data instead of copying hundreds of MB.

        NTFS hard links work only on the same volume. Some drives, folder
        permissions, or filesystems forbid links; in that case use the
        previous byte-for-byte copy path. Never link a live, growing tail.
        """
        if allow_link:
            try:
                os.link(source, target)
                return
            except OSError:
                pass
        CaptureEngine._freeze_file(source, target)

    @staticmethod
    def _freeze_file(source, target):
        # Copy a finite prefix, even if FFmpeg continues appending to this MKV.
        with source.open("rb") as reader, target.open("wb") as writer:
            remaining = os.fstat(reader.fileno()).st_size
            while remaining:
                block = reader.read(min(1024 * 1024, remaining))
                if not block:
                    break
                writer.write(block)
                remaining -= len(block)

    def _freeze_replay(self, start, end, temp):
        """Prefer completed segments; decode the active tail only as a fallback.

        Previously this tried ffprobe -count_frames on an unfinished MKV while
        the encoder was still writing. Waiting for the next 2-second segment
        boundary avoids most stalls and still preserves the requested replay.
        """
        deadline = time.monotonic() + 6
        segments = []
        while time.monotonic() < deadline:
            segments = self._segments()
            if segments and segments[-1][2] >= end - 0.02:
                break
            if self.writer_finished.is_set():
                break
            time.sleep(0.10)

        selected = [s for s in segments if s[2] > start and s[1] < end]
        # The newest file may still be growing. Copy it instead of linking;
        # older, completed segments can be linked in O(1) on NTFS.
        newest = max(self.session.glob("frame-*.mkv"), default=None)
        for i, (source, _, _) in enumerate(selected):
            safe_to_link = source != newest or self.writer_finished.is_set()
            self._snapshot_segment(
                source, temp / f"part{i}.mkv", allow_link=safe_to_link
            )

        # If the encoder hasn't closed its last segment, use only a frozen
        # on-disk snapshot. Failure to probe it must never leak TimeoutExpired.
        if not selected or selected[-1][2] < end - 0.05:
            candidates = sorted(self.session.glob("frame-*.mkv"))
            tail = candidates[-1] if candidates else None
            if tail and all(s[0] != tail for s in selected):
                index = int(tail.stem.split("-")[-1])
                tail_start = index * 2.0
                target = temp / f"part{len(selected)}.mkv"
                # A short deadline bounds the whole tail recovery operation.
                until = time.monotonic() + 6
                while time.monotonic() < until:
                    try:
                        self._freeze_file(tail, target)
                        duration = self.media.decoded_duration(target, self.settings.fps)
                        if tail_start + duration >= end - 0.05:
                            selected.append((tail, tail_start, tail_start + duration))
                            break
                    except (OSError, MediaError):
                        logging.debug("O último trecho ainda não está pronto", exc_info=True)
                    if self.writer_finished.is_set():
                        break
                    time.sleep(0.20)

        if not selected or selected[0][1] > start + 0.1 or selected[-1][2] < end - 0.1:
            logging.error("Replay incompleto: pedido %.3f–%.3f, segmentos %s", start, end, selected)
            raise MediaError(
                "O último trecho do replay ainda não ficou pronto. "
                "Aguarde alguns segundos e tente salvar de novo; "
                "se continuar, use 30 FPS e o modo leve."
            )
        for left, right in zip(selected, selected[1:]):
            if right[1] - left[2] > 0.1:
                raise MediaError("O replay contém um intervalo sem vídeo. Reinicie a captura.")
        return selected

    def _prune(self):
        # Check disk space even when a queued clip temporarily pins the ring.
        if self.session and shutil.disk_usage(self.session).free < 512 * 1024**2:
            raise RuntimeError(
                "Menos de 512 MB livres no disco. Libere espaço antes de capturar."
            )
        with self.lock:
            if self.pinning:
                return
            for path, start, end in self._segments():
                if (
                    end < self.elapsed - self.settings.duration - 8
                    and path.parent == self.session
                ):
                    path.unlink(missing_ok=True)
            while (
                self.samples
                and self.samples[0]["t"] < self.elapsed - self.settings.duration - 8
            ):
                self.samples.popleft()

    def sample(self, value):
        if self.active:
            with self.lock:
                self.samples.append(dict(value, t=self.elapsed))

    def screenshot(self):
        if not self.active or self.latest is None:
            raise RuntimeError("Inicie a captura da janela antes de tirar um print.")
        with self.lock:
            pixels = self.latest.copy()
        path = (
            self.settings.clip_folder()
            / f"Print-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}.png"
        )
        Image.fromarray(pixels[:, :, [2, 1, 0]]).save(path)
        self.events.put(("saved", str(path)))
        return path

    def save_clip(self, hud_settings=None):
        with self.lock:
            if not self.active or self.elapsed < 0.5:
                raise RuntimeError(
                    "Inicie a captura e aguarde pelo menos um segundo para preencher o buffer."
                )
            if self.pending >= self.MAX_PENDING_CLIPS:
                raise RuntimeError(
                    f"Fila cheia ({self.MAX_PENDING_CLIPS} clipes). "
                    "Espere um clipe terminar de salvar e tente novamente."
                )
            self.pending += 1
            self._snapshots_pending += 1
            self.pinning = True
            queue_position = self.pending
            end = self.elapsed
            start = max(0, end - self.settings.duration)
            samples = [
                dict(s, t=max(0, s["t"] - start))
                for s in self.samples
                if start - 0.1 <= s["t"] <= end
            ]
            settings = copy.deepcopy(self.settings)
            session = self.session
            epoch = self.epoch
            audio = (
                self.audio.snapshot(epoch + start, epoch + end) if self.audio else None
            )
            if hud_settings is not None:
                settings.clip_end_sound = hud_settings.clip_end_sound
                settings.notification_volume = hud_settings.notification_volume
                settings.hud_enabled = hud_settings.hud_enabled
                settings.hud = copy.deepcopy(hud_settings.hud)
        self.events.put((
            "queued",
            f"Clipe registrado! {queue_position} "
            + ("clipe na fila." if queue_position == 1 else "clipes na fila."),
        ))
        return self.pool.submit(
            self._save_clip, start, end, samples, settings, session, epoch, audio
        )

    def _save_clip(self, start, end, samples, settings, session, epoch, audio):
        temp = None
        snapshot_released = False
        try:
            self.events.put(("saving", f"Exportando clipe de {end - start:.1f}s…"))
            temp = Path(
                tempfile.mkdtemp(prefix="duck-clip-", dir=settings.clip_folder())
            )
            selected = self._freeze_replay(start, end, temp)
            with self.lock:
                self._snapshots_pending = max(0, self._snapshots_pending - 1)
                self.pinning = self._snapshots_pending > 0
                snapshot_released = True
            (temp / "input.txt").write_text(
                "".join(
                    f"file 'part{i}.mkv'\nduration {right - left:.9f}\n"
                    for i, (_, left, right) in enumerate(selected)
                ),
                encoding="utf-8",
            )
            offset = max(0, start - selected[0][1])
            duration = end - start
            args = [
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                "input.txt",
            ]
            if audio:
                audio.write(temp / "audio.wav", epoch + start, epoch + end)
            chime = settings.clip_end_sound and settings.notification_volume > 0
            if chime:
                mix_clip_chime(temp / "audio.wav", duration, settings.notification_volume)
            has_audio = audio is not None or chime
            if has_audio:
                args += ["-i", "audio.wav"]
            # Decode before trimming: a frozen live MKV may not have a seek
            # index, and input -ss can silently produce an empty MP4.
            filters = [
                f"trim=start={offset}:duration={duration}",
                "setpts=PTS-STARTPTS",
            ]
            if settings.hud_enabled and settings.hud:
                write_hud(
                    temp / "hud.ass",
                    settings.hud,
                    samples,
                    *self.output_size,
                    duration,
                    settings.fps,
                )
                copy_fonts(temp)
                filters.append("subtitles=hud.ass:fontsdir=fonts")
            images = (
                [item for item in settings.hud if item.get("kind") == "image"]
                if settings.hud_enabled
                else []
            )
            if images:
                graph = "[0:v]" + (",".join(filters) or "null") + "[v0];"
                for i, item in enumerate(images):
                    path = Path(item.get("path", ""))
                    if not path.is_file():
                        raise MediaError(
                            "Uma imagem do HUD foi movida. Escolha a imagem novamente no editor de HUD."
                        )
                    args += ["-loop", "1", "-i", str(path.resolve())]
                    slot = i + (2 if has_audio else 1)
                    w = max(
                        24,
                        round(self.output_size[0] * 0.15 * float(item.get("scale", 1))),
                    )
                    x = round(float(item["x"]) * self.output_size[0])
                    y = round(float(item["y"]) * self.output_size[1])
                    opacity = max(0.1, min(1, float(item.get("opacity", 1))))
                    graph += f"[{slot}:v]scale={w}:-1,format=rgba,colorchannelmixer=aa={opacity}[im{i}];[v{i}][im{i}]overlay={x}:{y}:shortest=1[v{i + 1}];"
                args += [
                    "-filter_complex",
                    graph.rstrip(";"),
                    "-map",
                    f"[v{len(images)}]",
                ]
            else:
                if filters:
                    args += ["-vf", ",".join(filters)]
                args += ["-map", "0:v:0"]
            if has_audio:
                args += ["-map", "1:a:0", "-c:a", "aac", "-b:a", "160k"]
            else:
                args += ["-an"]
            args += [
                *self.media.encoding(self.encoder, settings.quality, settings.fps, bitrate_mbps=getattr(settings, "bitrate_mbps", 0)),
                "-t",
                str(duration),
                "-movflags",
                "+faststart",
                "clip.mp4",
            ]
            self.media.run(args, cwd=temp)
            verified = self.media.probe(temp / "clip.mp4")
            if abs(verified.duration - duration) > max(0.15, 2 / settings.fps) or (
                has_audio and not verified.audio
            ):
                raise MediaError(
                    "A exportação não contém toda a duração ou o áudio esperado. Confira o diagnóstico em duckcapture.log."
                )
            output = (
                settings.clip_folder()
                / f"Clipe-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}.mp4"
            )
            (temp / "clip.mp4").replace(output)
            atomic_json(
                output.with_suffix(".json"),
                dict(
                    duration=duration,
                    fps=settings.fps,
                    quality=settings.quality,
                    audio=has_audio,
                    system_audio=audio is not None,
                    clip_end_sound=chime,
                    hud=settings.hud if settings.hud_enabled else [],
                    inputs=samples,
                ),
            )
            self.events.put(("saved", str(output)))
            return output
        except Exception as error:
            logging.exception("Falha ao exportar replay")
            self.events.put(("error", "Não foi possível salvar o clipe: " + str(error)))
            raise
        finally:
            if temp:
                shutil.rmtree(temp, ignore_errors=True)
            with self.lock:
                if not snapshot_released:
                    self._snapshots_pending = max(0, self._snapshots_pending - 1)
                self.pending = max(0, self.pending - 1)
                self.pinning = self._snapshots_pending > 0
                remaining = self.pending
            self.events.put(("queue_update", remaining))

    def stop(self):
        self.done.set()

    def shutdown(self):
        self.stop()
        if self.thread:
            self.thread.join(timeout=20)
        self.pool.shutdown(wait=True)
        if (
            self.session
            and self.session.exists()
            and not (self.thread and self.thread.is_alive())
        ):
            shutil.rmtree(self.session, ignore_errors=True)
