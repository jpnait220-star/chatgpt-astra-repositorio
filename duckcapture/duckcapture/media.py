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
        base = (
            Path(directory)
            if directory
            else Path(__file__).resolve().parents[1] / "tools"
        )
        self.ffmpeg = (
            str(base / ("ffmpeg" + suffix))
            if (base / ("ffmpeg" + suffix)).exists()
            else shutil.which("ffmpeg")
        )
        self.ffprobe = (
            str(base / ("ffprobe" + suffix))
            if (base / ("ffprobe" + suffix)).exists()
            else shutil.which("ffprobe")
        )
        self._encoder = None

    def require(self):
        if not self.ffmpeg or not self.ffprobe:
            raise MediaError(
                "FFmpeg não encontrado. Execute Instalar.py ou selecione a pasta com ffmpeg e ffprobe em Configurações."
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

    def encoder(self, requested="Automático"):
        self.require()
        if requested != "Automático":
            choices = [requested]
        elif self._encoder:
            return self._encoder
        else:
            choices = ["h264_nvenc", "h264_qsv", "h264_amf", "libx264"]
        for encoder in choices:
            try:
                self.run(
                    [
                        "-f",
                        "lavfi",
                        "-i",
                        "color=s=128x128:r=30",
                        "-frames:v",
                        "1",
                        "-c:v",
                        encoder,
                        "-pix_fmt",
                        "yuv420p",
                        "-f",
                        "null",
                        "-",
                    ],
                    timeout=15,
                )
                if requested == "Automático":
                    self._encoder = encoder
                return encoder
            except (MediaError, subprocess.TimeoutExpired):
                pass
        raise MediaError(
            "O codificador escolhido não funciona nesta máquina. Selecione Automático ou libx264."
        )

    @staticmethod
    def encoding(encoder, quality="Equilibrado", fps=60):
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
        return args + ["-pix_fmt", "yuv420p", "-g", str(fps * 2), "-bf", "0"]

    def thumbnail(self, path, target):
        self.run(
            [
                "-y",
                "-i",
                str(path),
                "-frames:v",
                "1",
                "-vf",
                "scale=480:-2",
                str(target),
            ],
            timeout=30,
        )

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
                    from .hud import write_title_ass

                    write_title_ass(
                        tmp / "title.ass",
                        p.text,
                        width,
                        height,
                        (p.end - p.start) / p.speed,
                    )
                    filters.append("subtitles=title.ass")
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
