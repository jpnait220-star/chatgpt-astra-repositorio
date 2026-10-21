from __future__ import annotations
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

CREATE_FLAGS = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


class MediaError(RuntimeError):
    pass


@dataclass
class MediaInfo:
    path: str
    duration: float
    width: int
    height: int
    fps: float
    audio: bool


@dataclass
class EditPart:
    path: str
    start: float = 0
    end: float = 0
    speed: float = 1
    volume: float = 1
    text: str = ""
    effect: str = "Original"
    zoom: float = 1
    sticker: str = ""


class Media:
    def __init__(self, directory=""):
        suffix = ".exe" if os.name == "nt" else ""
        # In the installed version, bundled binaries are under _internal/tools.
        # An old user setting pointing to an outdated folder must not hide them.
        bundled = Path(__file__).resolve().parents[1] / "tools"
        candidates = []
        if directory:
            candidates.append(Path(directory))
        if bundled not in candidates:
            candidates.append(bundled)
        self.ffmpeg = next(
            (
                str(folder / ("ffmpeg" + suffix))
                for folder in candidates
                if (folder / ("ffmpeg" + suffix)).is_file()
            ),
            None,
        ) or shutil.which("ffmpeg")
        self.ffprobe = next(
            (
                str(folder / ("ffprobe" + suffix))
                for folder in candidates
                if (folder / ("ffprobe" + suffix)).is_file()
            ),
            None,
        ) or shutil.which("ffprobe")
        self._encoders = {}

    def require(self):
        if not self.ffmpeg or not self.ffprobe:
            raise MediaError(
                "Componentes de gravação não encontrados. Reinstale o DuckCapture "
                "usando o instalador completo."
            )

    def run(self, args, timeout=600, cwd=None):
        self.require()
        result = subprocess.run(
            [
                self.ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-nostdin",
                "-filter_threads",
                "2",
                "-filter_complex_threads",
                "2",
                *map(str, args),
            ],
            capture_output=True,
            timeout=timeout,
            creationflags=CREATE_FLAGS,
            cwd=cwd,
        )
        if result.returncode:
            raise MediaError(
                result.stderr.decode("utf-8", "replace")[-3500:] or "Falha no FFmpeg."
            )
        return result

    def probe(self, path) -> MediaInfo:
        self.require()
        result = subprocess.run(
            [
                self.ffprobe,
                "-v",
                "error",
                "-show_format",
                "-show_streams",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            timeout=30,
            creationflags=CREATE_FLAGS,
        )
        if result.returncode:
            raise MediaError("Não foi possível ler este vídeo: " + str(path))
        doc = json.loads(result.stdout)
        stream = next((s for s in doc["streams"] if s["codec_type"] == "video"), None)
        if not stream:
            raise MediaError("O arquivo não contém vídeo.")
        a, b = stream.get("avg_frame_rate", "0/1").split("/")
        return MediaInfo(
            str(path),
            float(doc.get("format", {}).get("duration", stream.get("duration", 0))),
            int(stream["width"]),
            int(stream["height"]),
            float(a) / max(1, float(b)),
            any(s["codec_type"] == "audio" for s in doc["streams"]),
        )

    def encoder(
        self,
        requested="Automático",
        size=(128, 128),
        quality="Equilibrado",
        fps=30,
        cancelled=None,
        progress=None,
        realtime=False,
        bitrate_mbps=0,
    ):
        self.require()
        key = (size, quality, fps, realtime, int(bitrate_mbps or 0))
        if requested != "Automático":
            choices = [requested]
        elif key in self._encoders:
            return self._encoders[key]
        else:
            choices = ["h264_nvenc", "h264_qsv", "h264_amf", "libx264"]
        errors = []
        for encoder in choices:
            if cancelled and cancelled.is_set():
                raise InterruptedError("Preparação cancelada.")
            if progress:
                progress(f"Verificando {encoder} em {size[0]}×{size[1]}…")
            try:
                self.run(
                    [
                        "-f",
                        "lavfi",
                        "-i",
                        f"color=s={size[0]}x{size[1]}:r={fps}",
                        "-frames:v",
                        "1",
                        *self.encoding(encoder, quality, fps, realtime=realtime, bitrate_mbps=bitrate_mbps),
                        "-f",
                        "null",
                        "-",
                    ],
                    timeout=15,
                )
                if requested == "Automático":
                    self._encoders[key] = encoder
                return encoder
            except (MediaError, subprocess.TimeoutExpired) as error:
                errors.append(f"{encoder}: {error}")
        raise MediaError(
            "O codificador escolhido não funciona nesta configuração. Selecione Automático ou libx264.\n"
            + "\n".join(errors)[-1800:]
        )

    @staticmethod
    def encoding(encoder, quality="Equilibrado", fps=60, realtime=False, bitrate_mbps=0):
        level = {"Econômico": 29, "Equilibrado": 24, "Alta qualidade": 19, "Full": 16}[
            quality
        ]
        if encoder == "h264_nvenc":
            args = [
                "-c:v",
                encoder,
                "-preset",
                "p2",
                "-rc",
                "vbr",
                "-cq",
                str(level),
                "-b:v",
                "0",
            ]
        elif encoder == "h264_qsv":
            args = [
                "-c:v",
                encoder,
                "-preset",
                "veryfast",
                "-global_quality",
                str(level),
            ]
        elif encoder == "h264_amf":
            args = [
                "-c:v",
                encoder,
                "-quality",
                "speed",
                "-rc",
                "cqp",
                "-qp_i",
                str(level),
                "-qp_p",
                str(level),
            ]
        else:
            args = [
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-crf",
                str(level),
                "-threads",
                "2",
            ]
        if realtime:
            if encoder == "h264_nvenc":
                args += [
                    "-forced-idr",
                    "1",
                    "-tune",
                    "ull",
                    "-zerolatency",
                    "1",
                    "-delay",
                    "0",
                    "-rc-lookahead",
                    "0",
                ]
            elif encoder == "h264_qsv":
                args += ["-async_depth", "1", "-look_ahead", "0", "-forced_idr", "1"]
            elif encoder == "h264_amf":
                args += ["-usage", "lowlatency"]
            elif encoder == "libx264":
                args += ["-tune", "zerolatency"]
        if bitrate_mbps and bitrate_mbps > 0:
            target = f"{int(bitrate_mbps)}M"
            args += ["-b:v", target, "-maxrate", target, "-bufsize", f"{int(bitrate_mbps) * 2}M"]
        return args + ["-pix_fmt", "yuv420p", "-g", str(fps * 2), "-bf", "0"]

    def decoded_duration(self, path, fps):
        """Measure a *frozen* MKV prefix without decoding every video frame.

        Counting decoded frames in a live/recently-frozen Matroska file can
        stall ffprobe (15-second timeouts on some GPUs). There is one video
        packet per encoded frame in the H.264 segments we produce, so counting
        compressed packets is significantly lighter. Failure is recoverable;
        the caller waits for the segment to close instead of crashing.
        """
        self.require()
        try:
            result = subprocess.run(
                [self.ffprobe, "-v", "error", "-select_streams", "v:0",
                 "-count_packets", "-show_entries", "stream=nb_read_packets",
                 "-of", "json", str(path)],
                capture_output=True,
                timeout=5,
                creationflags=CREATE_FLAGS,
            )
            if result.returncode:
                raise MediaError("O trecho ainda está sendo finalizado pelo gravador.")
            packets = int(json.loads(result.stdout)["streams"][0]["nb_read_packets"])
            if packets <= 0 or fps <= 0:
                raise MediaError("O trecho ainda não possui quadros completos.")
            return packets / fps
        except subprocess.TimeoutExpired as error:
            raise MediaError("O trecho de vídeo ainda está ocupado; aguardando a finalização.") from error
        except (ValueError, KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
            raise MediaError("O trecho ainda não contém pacotes de vídeo legíveis.") from error

    def thumbnail(self, path, target):
        """Generate a clip cover slightly after the first frame, atomically."""
        source, target = Path(path), Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.stem + ".partial.png")
        try:
            # Seek to an actual action frame, not the often-black first frame.
            # Try the beginning too (short clips and videos without seek tables).
            for seek in ("0.35", "0"):
                temporary.unlink(missing_ok=True)
                try:
                    self.run(
                        ["-y", "-ss", seek, "-i", str(source),
                         "-map", "0:v:0", "-an", "-frames:v", "1",
                         "-vf", "scale=480:-2", "-threads", "1", str(temporary)],
                        timeout=12,
                    )
                    if temporary.is_file() and temporary.stat().st_size > 100:
                        temporary.replace(target)
                        return
                except (MediaError, subprocess.TimeoutExpired, OSError):
                    pass
            raise MediaError("Não foi possível criar a capa deste clipe.")
        finally:
            temporary.unlink(missing_ok=True)

    def export(
        self,
        parts: list[EditPart],
        output: Path,
        encoder="libx264",
        fps=30,
        quality="Alta qualidade",
    ):
        if not parts:
            raise MediaError("Adicione pelo menos um trecho.")
        infos = [self.probe(p.path) for p in parts]
        for p, info in zip(parts, infos):
            if not (0 <= p.start < p.end <= info.duration + 0.1):
                raise MediaError("O início e o fim de um trecho estão fora do vídeo.")
            if (
                not 0.25 <= p.speed <= 4
                or not 0 <= p.volume <= 2
                or not 1 <= p.zoom <= 3
            ):
                raise MediaError("Velocidade, volume ou zoom inválidos.")
        width = infos[0].width // 2 * 2
        height = infos[0].height // 2 * 2
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            raise MediaError("O arquivo de saída já existe. Escolha outro nome.")
        if any(Path(p.path).resolve() == output.resolve() for p in parts):
            raise MediaError("Não substitua seu vídeo original.")
        with tempfile.TemporaryDirectory(prefix="duck-edit-", dir=output.parent) as tmp:
            tmp = Path(tmp)
            segments = []
            for index, (p, info) in enumerate(zip(parts, infos)):
                target = tmp / f"part{index}.mp4"
                filters = [
                    f"trim=start={p.start}:end={p.end}",
                    f"setpts=(PTS-STARTPTS)/{p.speed}",
                    f"crop=trunc(iw/{p.zoom}/2)*2:trunc(ih/{p.zoom}/2)*2",
                    f"scale={width}:{height}:force_original_aspect_ratio=decrease",
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
                    f"fps={fps}",
                    "setsar=1",
                ]
                effects = {
                    "Preto e branco": "hue=s=0",
                    "Quente": "colorbalance=rs=.08:bs=-.04",
                    "Contraste": "eq=contrast=1.15:saturation=1.1",
                }
                if p.effect in effects:
                    filters.append(effects[p.effect])
                if p.text:
                    # ASS avoids drawtext interpolation and keeps all user text out of executable filter expressions.
                    from .hud import write_title_ass, copy_fonts

                    write_title_ass(
                        tmp / "title.ass",
                        p.text,
                        width,
                        height,
                        (p.end - p.start) / p.speed,
                    )
                    copy_fonts(tmp)
                    filters.append("subtitles=title.ass:fontsdir=fonts")
                args = ["-y", "-i", str(Path(p.path).resolve())]
                if p.sticker:
                    if not Path(p.sticker).is_file():
                        raise MediaError("Sticker não encontrado.")
                    args += ["-loop", "1", "-i", str(Path(p.sticker).resolve())]
                if not info.audio:
                    args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
                audio_index = 0 if info.audio else (2 if p.sticker else 1)
                duration = (p.end - p.start) / p.speed
                tempo = []
                speed = p.speed
                while speed < 0.5:
                    tempo.append("atempo=0.5")
                    speed /= 0.5
                while speed > 2:
                    tempo.append("atempo=2")
                    speed /= 2
                tempo.append(f"atempo={speed}")
                audio = (
                    (
                        f"atrim=start={p.start}:end={p.end},asetpts=PTS-STARTPTS,"
                        if info.audio
                        else ""
                    )
                    + ",".join(tempo)
                    + f",volume={p.volume},aresample=48000,apad,atrim=duration={duration}"
                )
                graph = "[0:v]" + ",".join(filters) + "[base];"
                if p.sticker:
                    graph += f"[1:v]scale={max(48, width // 7)}:-1[st];[base][st]overlay=W-w-24:24:shortest=1[v];"
                else:
                    graph += "[base]null[v];"
                graph += f"[{audio_index}:a]{audio}[a]"
                self.run(
                    args
                    + [
                        "-filter_complex",
                        graph,
                        "-map",
                        "[v]",
                        "-map",
                        "[a]",
                        *self.encoding(encoder, quality, fps),
                        "-c:a",
                        "aac",
                        "-b:a",
                        "160k",
                        "-t",
                        str(duration),
                        "-movflags",
                        "+faststart",
                        str(target),
                    ],
                    cwd=tmp,
                )
                segments.append(target)
            manifest = tmp / "join.txt"
            manifest.write_text(
                "".join(f"file '{p.name}'\n" for p in segments), encoding="utf-8"
            )
            final = tmp / "export.mp4"
            self.run(
                [
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(manifest),
                    "-c",
                    "copy",
                    "-movflags",
                    "+faststart",
                    str(final),
                ],
                cwd=tmp,
            )
            final.replace(output)
        return output
