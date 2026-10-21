from __future__ import annotations
import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

DURATIONS = (15, 30, 60, 90, 120)
FPS = (25, 30, 45, 60, 90, 120)
PROFILES = ("Econômico", "Equilibrado", "Alta qualidade", "Full")
RESOLUTION_PRESETS = ("720p", "1080p", "1440p", "4K", "Origem")
BITRATES = (8, 12, 16, 24, 40, 60, 80, 100)
AUDIO_MODES = (
    "Som do PC (jogo, Discord, navegador)",
    "Sem áudio",
)
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
    resolution: str = "1080p"
    bitrate_mbps: int = 16
    encoder: str = "Automático"
    clip_key: str = "F8"
    screenshot_key: str = "F9"
    audio_mode: str = AUDIO_MODES[0]
    system_audio: bool = True
    microphone_audio: bool = False
    cursor: bool = True
    tips: bool = True
    motion: bool = True
    notification_sounds: bool = True
    notification_volume: float = .82
    accent_color: str = "#f4f6fb"
    performance_mode: bool = True
    fullscreen_compatibility: bool = True
    clips_dir: str = str(Path.home() / "Videos" / "DuckCapture")
    music_dir: str = str(Path.home() / "Music" / "DuckCapture Music")
    music_files: list[str] = field(default_factory=list)
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
        if settings.resolution not in RESOLUTION_PRESETS:
            settings.resolution = "1080p"
        if settings.bitrate_mbps not in BITRATES:
            settings.bitrate_mbps = 16
        if settings.audio_mode not in AUDIO_MODES:
            settings.audio_mode = AUDIO_MODES[0]
        if isinstance(settings.accent_color, str) and settings.accent_color.lower() == "#63d5ff":
            settings.accent_color = "#f4f6fb"  # Migrate old default cyan to new white
        if not isinstance(settings.notification_volume, (int, float)) or not 0 <= settings.notification_volume <= 1:
            settings.notification_volume = .82
        settings.system_audio = settings.audio_mode != "Sem áudio"
        import re
        if not isinstance(settings.accent_color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", settings.accent_color):
            settings.accent_color = "#f4f6fb"
        return settings

    def save(self):
        self.system_audio = self.audio_mode != "Sem áudio"
        atomic_json(data_dir() / "settings.json", asdict(self))

    def clip_folder(self):
        folder = Path(self.clips_dir).expanduser()
        folder.mkdir(parents=True, exist_ok=True)
        return folder
