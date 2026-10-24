"""Cancellable, bounded background encodes for sharing and wallpaper caches."""

import hashlib
import math
import os
from pathlib import Path
import subprocess
import tempfile
import threading

from PySide6.QtCore import QThread, Signal
from .config import data_dir
from .media import Media, MediaError, CREATE_FLAGS


def share_plan(info, limit):
    if not math.isfinite(info.duration) or info.duration <= 0:
        raise MediaError("Duração de vídeo inválida.")
    fps = min(60, max(1, info.fps))
    audio = 128 if info.audio else 0
    budget = limit - max(32_000, limit * 0.07)
    bitrate = int(budget * 8 / info.duration / 1000) - audio
    if bitrate < 120:
        raise MediaError(
            "Este vídeo é longo demais para um único link. Divida-o no editor."
        )
    height = 1080 if bitrate >= fps * 55 else 720 if bitrate >= fps * 24 else 480
    return bitrate, fps, height


class MediaJob(QThread):
    progress = Signal(int, str)
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        source,
        operation,
        *,
        limit=200_000_000,
        size=(1920, 1080),
        media=None,
        parent=None,
    ):
        super().__init__(parent)
        self.source, self.operation = Path(source), operation
        self.limit, self.size = limit, size
        self.media = media or Media()
        self.cancelled = threading.Event()
        self.process = None
        self.guard = threading.Lock()
        self.result = ""

    def cancel(self):
        self.cancelled.set()
        with self.guard:
            if self.process and self.process.poll() is None:
                try:
                    self.process.terminate()
                except OSError:
                    pass

    def encode(self, args, duration, start, portion, message, cwd):
        if self.cancelled.is_set():
            raise InterruptedError()
        flags = CREATE_FLAGS | (
            subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else 0
        )
        with tempfile.TemporaryFile() as errors:
            with self.guard:
                self.process = subprocess.Popen(
                    [
                        self.media.ffmpeg,
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-nostdin",
                        "-filter_threads",
                        "2",
                        "-filter_complex_threads",
                        "2",
                        "-progress",
                        "pipe:1",
                        "-nostats",
                        *map(str, args),
                    ],
                    stdout=subprocess.PIPE,
                    stderr=errors,
                    cwd=cwd,
                    creationflags=flags,
                )
                if self.cancelled.is_set():
                    self.process.terminate()
            try:
                for line in self.process.stdout:
                    if line.startswith(b"out_time_us="):
                        try:
                            elapsed = int(line.split(b"=")[1]) / 1_000_000
                            self.progress.emit(
                                min(99, round(start + portion * elapsed / duration)),
                                message,
                            )
                        except ValueError:
                            pass
                    if self.cancelled.is_set():
                        raise InterruptedError()
                code = self.process.wait(timeout=10)
                if self.cancelled.is_set():
                    raise InterruptedError()
                if code:
                    errors.seek(0)
                    raise MediaError(
                        errors.read().decode("utf-8", "replace")[-1400:]
                        or "Falha ao preparar o vídeo."
                    )
            finally:
                with self.guard:
                    if self.process.poll() is None:
                        self.process.kill()
                    self.process.wait(timeout=10)
                    self.process.stdout.close()
                    self.process = None

    def run(self):
        try:
            self.media.require()
            info = self.media.probe(self.source)
            if self.cancelled.is_set():
                return
            cache = data_dir() / (
                "wallpapers" if self.operation == "wallpaper" else "sharing-cache"
            )
            cache.mkdir(exist_ok=True)
            stat = self.source.stat()
            key = hashlib.sha256(
                f"v3|{self.source.resolve()}|{stat.st_size}|{stat.st_mtime_ns}|{self.operation}|{self.size}|{self.limit}".encode()
            ).hexdigest()
            target = cache / (key + ".mp4")
            if (
                target.is_file()
                and target.stat().st_size > 0
                and (self.operation != "share" or target.stat().st_size <= self.limit)
            ):
                self.result = str(target)
            else:
                with tempfile.TemporaryDirectory(prefix="prepare-", dir=cache) as temp:
                    output = Path(temp) / "ready.mp4"
                    if self.operation == "share":
                        bitrate, fps, height = share_plan(info, self.limit)
                        vf = f"scale=w=min(iw\\,{height * 16 // 9}):h=min(ih\\,{height}):force_original_aspect_ratio=decrease:force_divisible_by=2,fps={fps},format=yuv420p"
                        common = [
                            "-y",
                            "-i",
                            str(self.source.resolve()),
                            "-map",
                            "0:v:0",
                            "-vf",
                            vf,
                            "-c:v",
                            "libx264",
                            "-preset",
                            "fast",
                            "-threads",
                            "2",
                            "-b:v",
                            f"{bitrate}k",
                            "-passlogfile",
                            "pass",
                        ]
                        self.encode(
                            [*common, "-pass", "1", "-an", "-f", "null", os.devnull],
                            info.duration,
                            0,
                            45,
                            "Analisando o clipe para caber no link…",
                            temp,
                        )
                        self.encode(
                            [
                                *common,
                                "-pass",
                                "2",
                                "-map",
                                "0:a:0?",
                                "-c:a",
                                "aac",
                                "-b:a",
                                "128k",
                                "-movflags",
                                "+faststart",
                                output,
                            ],
                            info.duration,
                            45,
                            55,
                            "Preparando cópia menor; o original será preservado…",
                            temp,
                        )
                        if output.stat().st_size > self.limit:
                            raise MediaError(
                                "A cópia ainda excedeu o limite. Reduza o trecho no editor e tente novamente."
                            )
                    else:
                        w, h = self.size
                        vf = f"scale=w=min(iw\\,{w}):h=min(ih\\,{h}):force_original_aspect_ratio=decrease:force_divisible_by=2,fps=24,format=yuv420p"
                        self.encode(
                            [
                                "-y",
                                "-i",
                                str(self.source.resolve()),
                                "-map",
                                "0:v:0",
                                "-vf",
                                vf,
                                "-an",
                                "-c:v",
                                "libx264",
                                "-preset",
                                "veryfast",
                                "-threads",
                                "2",
                                "-crf",
                                "18",
                                "-movflags",
                                "+faststart",
                                output,
                            ],
                            info.duration,
                            0,
                            100,
                            "Otimizando papel de parede uma única vez…",
                            temp,
                        )
                    verified = self.media.probe(output)
                    if abs(verified.duration - info.duration) > max(
                        0.2, 2 / max(1, info.fps)
                    ) or (
                        self.operation == "share" and info.audio and not verified.audio
                    ):
                        raise MediaError(
                            "A cópia preparada não preservou a duração ou o áudio esperado."
                        )
                    if self.cancelled.is_set():
                        return
                    output.replace(target)
                    self.result = str(target)
            if not self.cancelled.is_set():
                self.progress.emit(100, "Vídeo preparado.")
                self.succeeded.emit(self.result)
        except InterruptedError:
            pass
        except Exception as error:
            if not self.cancelled.is_set():
                self.failed.emit(str(error))
