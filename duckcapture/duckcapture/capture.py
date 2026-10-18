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
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image
from .audio import AudioRing
from .config import Settings, atomic_json, data_dir
from .hud import write_hud
from .media import Media, MediaError, CREATE_FLAGS


class CaptureEngine:
    def __init__(self, media: Media):
        self.media = media
        self.events = queue.Queue()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="duck-export")
        self.active = False
        self.starting = False
        self.latest = None
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
        self.pinning = False
        self.error = None
        self.source = None
        self.thread = None

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
        ):
            raise RuntimeError("A captura já está em andamento.")
        if os.name != "nt":
            raise RuntimeError(
                "A captura de janelas está disponível no Windows 10/11. Editor, HUD e música também podem ser abertos nesta máquina."
            )
        self.starting = True
        self.error = None
        self.settings = copy.deepcopy(settings)
        self.hwnd = hwnd
        if self.session and self.session.exists():
            shutil.rmtree(self.session, ignore_errors=True)
        self.done.clear()
        self.latest = None
        self.frames = 0
        self.samples.clear()
        self.audio = None
        self.thread = threading.Thread(
            target=self._start, daemon=True, name="duck-capture"
        )
        self.thread.start()

    def _start(self):
        process = None
        log = None
        try:
            from windows_capture import WindowsCapture

            self.encoder = self.media.encoder(self.settings.encoder)
            source = WindowsCapture(
                window_hwnd=self.hwnd,
                cursor_capture=self.settings.cursor,
                # Leave optional Windows 11 session properties at their system
                # defaults so older Windows 10 capture sessions can also start.
                draw_border=None,
                minimum_update_interval=None,
            )
            self.source = source
            arrived = threading.Event()
            last_copy = 0.0

            @source.event
            def on_frame_arrived(frame, capture_control):
                nonlocal last_copy
                if self.done.is_set():
                    capture_control.stop()
                    return
                now = time.monotonic()
                # Keep a recent frame without copying at every high-refresh
                # desktop update. Slack avoids dropping alternate 60 Hz frames.
                if now - last_copy < 0.5 / self.settings.fps:
                    return
                last_copy = now
                pixels = frame.frame_buffer.copy()
                with self.lock:
                    self.latest = pixels
                arrived.set()

            @source.event
            def on_closed():
                if not self.done.is_set():
                    self.events.put(
                        ("error", "A janela selecionada foi fechada. A captura parou.")
                    )
                self.done.set()

            self.control = source.start_free_threaded()
            if not arrived.wait(10):
                raise RuntimeError(
                    "Nenhum quadro recebido. Restaure a janela e use modo janela/sem bordas no jogo."
                )
            if self.settings.system_audio:
                self.audio = AudioRing()
                self.audio.start()
            buffer_root = data_dir() / "buffer"
            buffer_root.mkdir(exist_ok=True)
            self.session = Path(tempfile.mkdtemp(prefix="replay-", dir=buffer_root))
            height, width = self.latest.shape[:2]
            self.size = (width, height)
            maximum = {
                "Econômico": 1280,
                "Equilibrado": 1920,
                "Alta qualidade": 2560,
                "Full": width,
            }[self.settings.quality]
            out_width = min(width, maximum) // 2 * 2
            out_height = round(height * out_width / width) // 2 * 2
            self.output_size = (out_width, out_height)
            args = [
                self.media.ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "bgra",
                "-s",
                f"{width}x{height}",
                "-r",
                str(self.settings.fps),
                "-i",
                "pipe:0",
                "-an",
                "-vf",
                f"scale={out_width}:{out_height}",
                *self.media.encoding(
                    self.encoder, self.settings.quality, self.settings.fps
                ),
                "-force_key_frames",
                "expr:gte(t,n_forced*2)",
                "-f",
                "segment",
                "-segment_time",
                "2",
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
            self.active = True
            self.starting = False
            self.events.put(
                (
                    "started",
                    f"{self.encoder} · {out_width}×{out_height} · {self.settings.fps} FPS",
                )
            )
            while not self.done.is_set():
                target = self.epoch + self.frames / self.settings.fps
                remaining = target - time.monotonic()
                if remaining > 0:
                    self.done.wait(remaining)
                if self.done.is_set():
                    break
                if time.monotonic() - target > 1.5:
                    raise RuntimeError(
                        "O computador não está acompanhando este FPS. Reduza o FPS/qualidade ou escolha um codificador da GPU."
                    )
                with self.lock:
                    pixels = self.latest
                if pixels.shape[:2] != (height, width):
                    raise RuntimeError(
                        "A janela mudou de resolução. Inicie a captura novamente para ajustar o tamanho."
                    )
                process.stdin.write(pixels.tobytes())
                self.frames += 1
                if self.audio and self.audio.error:
                    raise RuntimeError(
                        "O áudio do sistema parou. Verifique seu dispositivo de saída."
                    )
                if self.frames % self.settings.fps == 0:
                    self._prune()
                if process.poll() is not None:
                    raise RuntimeError(
                        "O codificador parou. Veja encoder.log na pasta de dados."
                    )
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
            self.events.put(("error", str(error)))
        finally:
            self.done.set()
            self.starting = False
            self.active = False
            if self.control:
                try:
                    self.control.stop()
                except Exception:
                    pass
                self.control = None
            if process:
                try:
                    process.stdin.close()
                    process.wait(timeout=15)
                except (OSError, subprocess.TimeoutExpired):
                    process.kill()
                    process.wait()
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

    def _segments(self):
        if not self.session:
            return []
        try:
            with (self.session / "segments.csv").open(
                encoding="utf-8", newline=""
            ) as stream:
                rows = list(csv.reader(stream))
            return [
                (
                    Path(row[0])
                    if Path(row[0]).is_absolute()
                    else self.session / row[0],
                    float(row[1]),
                    float(row[2]),
                )
                for row in rows
                if len(row) == 3
            ]
        except (OSError, ValueError):
            return []

    def _prune(self):
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
        if self.session and shutil.disk_usage(self.session).free < 512 * 1024**2:
            raise RuntimeError(
                "Menos de 512 MB livres no disco. Libere espaço antes de capturar."
            )

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
            if self.pending:
                raise RuntimeError(
                    "O clipe anterior ainda está sendo salvo. Aguarde a exportação."
                )
            self.pending += 1
            self.pinning = True
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
                settings.hud_enabled = hud_settings.hud_enabled
                settings.hud = copy.deepcopy(hud_settings.hud)
        self.events.put(("saving", f"Salvando {end - start:.1f}s…"))
        return self.pool.submit(
            self._save_clip, start, end, samples, settings, session, epoch, audio
        )

    def _save_clip(self, start, end, samples, settings, session, epoch, audio):
        temp = None
        try:
            # Wait for the segment containing the hotkey instant to close; never include later action.
            deadline = time.monotonic() + 12
            while time.monotonic() < deadline:
                segments = self._segments()
                if segments and segments[-1][2] >= end - 0.05:
                    break
                if not self.active and self.thread and not self.thread.is_alive():
                    break
                time.sleep(0.08)
            selected = [s for s in self._segments() if s[2] > start and s[1] < end]
            if not selected or selected[-1][2] < end - 0.15:
                raise MediaError(
                    "O último segmento ainda não ficou disponível. Tente novamente."
                )
            temp = Path(
                tempfile.mkdtemp(prefix="duck-clip-", dir=settings.clip_folder())
            )
            for i, (source, _, _) in enumerate(selected):
                shutil.copyfile(source, temp / f"part{i}.mkv")
            with self.lock:
                self.pinning = False
            (temp / "input.txt").write_text(
                "".join(f"file 'part{i}.mkv'\n" for i in range(len(selected))),
                encoding="utf-8",
            )
            offset = max(0, start - selected[0][1])
            duration = end - start
            args = [
                "-y",
                "-ss",
                str(offset),
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                "input.txt",
            ]
            if audio:
                audio.write(temp / "audio.wav", epoch + start, epoch + end)
                args += ["-i", "audio.wav"]
            filters = []
            if settings.hud_enabled and settings.hud:
                write_hud(
                    temp / "hud.ass",
                    settings.hud,
                    samples,
                    *self.output_size,
                    duration,
                    settings.fps,
                )
                filters.append("subtitles=hud.ass")
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
                    slot = i + (2 if audio else 1)
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
            if audio:
                args += ["-map", "1:a:0", "-c:a", "aac", "-b:a", "160k"]
            else:
                args += ["-an"]
            args += [
                *self.media.encoding(self.encoder, settings.quality, settings.fps),
                "-t",
                str(duration),
                "-movflags",
                "+faststart",
                "clip.mp4",
            ]
            self.media.run(args, cwd=temp)
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
                    hud=settings.hud if settings.hud_enabled else [],
                    inputs=samples,
                ),
            )
            self.events.put(("saved", str(output)))
            return output
        except Exception as error:
            self.events.put(("error", "Não foi possível salvar o clipe: " + str(error)))
            raise
        finally:
            if temp:
                shutil.rmtree(temp, ignore_errors=True)
            with self.lock:
                self.pending -= 1
                self.pinning = False

    def stop(self):
        self.done.set()

    def shutdown(self):
        self.stop()
        if self.thread:
            self.thread.join(timeout=20)
        self.pool.shutdown(wait=True)
        if self.session and self.session.exists():
            shutil.rmtree(self.session, ignore_errors=True)
