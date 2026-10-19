from __future__ import annotations
import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

DURATIONS = (15, 30, 60, 90, 120)
FPS = (30, 60, 90, 120, 144, 240)
PROFILES = ("Econômico", "Equilibrado", "Alta qualidade", "Full")
ROOT = Path(__file__).resolve().parent


def data_dir() -> Path:
    override = os.environ.get("DUCKCAPTURE_DATA")
    result = (
        Path(override)
        if override
        else Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local/share"))
        / "DuckCapture"
    )
    result.mkdir(parents=True, exist_ok=True)
    return result


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)


@dataclass
class Settings:
    duration: int = 30
    fps: int = 60
    quality: str = "Equilibrado"
    encoder: str = "Automático"
    clip_key: str = "F8"
    screenshot_key: str = "F9"
    system_audio: bool = True
    cursor: bool = True
    tips: bool = True
    motion: bool = True
    notification_sounds: bool = True
    clips_dir: str = str(Path.home() / "Videos" / "DuckCapture")
    music_dir: str = str(Path.home() / "Music" / "DuckCapture Music")
    spotify: str = ""
    hud_enabled: bool = False
    hud: list[dict] = field(default_factory=list)
    hud_presets: dict = field(default_factory=dict)
    ffmpeg_dir: str = ""

    @classmethod
    def load(cls):
        path = data_dir() / "settings.json"
        if not path.exists():
            return cls()
        value = json.loads(path.read_text(encoding="utf-8"))
        settings = cls(
            **{
                key: val
                for key, val in value.items()
                if key in cls.__dataclass_fields__
            }
        )
        if settings.duration not in DURATIONS:
            settings.duration = 30
        if settings.fps not in FPS:
            settings.fps = 60
        if settings.quality not in PROFILES:
            settings.quality = "Equilibrado"
        return settings

    def save(self):
        atomic_json(data_dir() / "settings.json", asdict(self))

    def clip_folder(self):
        folder = Path(self.clips_dir).expanduser()
        folder.mkdir(parents=True, exist_ok=True)
        return folder
