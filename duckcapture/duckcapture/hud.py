from __future__ import annotations
import math
from pathlib import Path

NAMES = {
    "keyboard": "DuckKeyboard",
    "mouse": "DuckMouse",
    "clicks": "Cliques visuais",
    "fps": "FPS da captura",
    "timer": "Tempo do clipe",
    "title": "Texto",
    "music": "Música",
    "cps": "Cliques por segundo",
}


def preset(name="Minecraft PvP"):
    common = [
        dict(kind="keyboard", x=0.035, y=0.69, scale=1, opacity=0.9, text=""),
        dict(kind="mouse", x=0.19, y=0.77, scale=1, opacity=0.9, text=""),
    ]
    if name == "Minimal":
        return [dict(kind="timer", x=0.85, y=0.04, scale=1, opacity=0.85, text="")]
    if name == "Tutorial":
        return common + [
            dict(kind="clicks", x=0.5, y=0.5, scale=1, opacity=0.8, text=""),
            dict(kind="title", x=0.05, y=0.06, scale=1, opacity=1, text="Meu tutorial"),
        ]
    if name == "Speedrun":
        return common + [
            dict(kind="timer", x=0.8, y=0.05, scale=1.5, opacity=1, text="")
        ]
    return common + [
        dict(kind="fps", x=0.82, y=0.04, scale=1, opacity=0.85, text=""),
        dict(kind="cps", x=0.82, y=0.09, scale=1, opacity=0.85, text=""),
    ]


def escape(text):
    return (
        str(text)
        .replace("\\", "／")
        .replace("{", "(")
        .replace("}", ")")
        .replace("\r", "")
        .replace("\n", r"\N")
    )


def clock(seconds):
    cs = max(0, round(seconds * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02}:{cs // 100 % 60:02}.{cs % 100:02}"


def header(w, h):
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 2
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Manrope,24,&H00FFFFFF,&H000000FF,&H00202020,&H900D1018,0,0,0,0,100,100,0,0,1,1,0,7,0,0,0,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def dialogue(start, end, text, layer=0):
    return f"Dialogue: {layer},{clock(start)},{clock(end)},Default,,0,0,0,,{text}\n"


def write_title_ass(path, text, w, h, duration):
    Path(path).write_text(
        header(w, h)
        + dialogue(
            0,
            duration,
            rf"{{\an2\pos({w // 2},{int(h * 0.9)})\fs{max(18, h // 23)}}}"
            + escape(text),
        ),
        encoding="utf-8-sig",
    )


def write_hud(path, items, samples, width, height, duration, fps):
    from .hud_art import ass_shapes, color

    lines = [header(width, height)]
    samples = sorted(samples, key=lambda sample: sample["t"])
    if not samples or samples[0]["t"] > 0:
        samples.insert(0, dict(t=0, keys=[], buttons=[], cps=0, music=""))
    for item in items:
        kind = item.get("kind")
        if kind == "image":
            continue
        x, y = round(item["x"] * width), round(item["y"] * height)
        scale = max(0.4, min(3, float(item.get("scale", 1)))) * height / 720
        alpha = round((1 - max(0.1, min(1, float(item.get("opacity", 1))))) * 255)
        spans = []
        item_samples = (
            [dict(t=second) for second in range(math.ceil(duration))]
            if kind == "timer"
            else samples
        )
        for i, sample in enumerate(item_samples):
            a = max(0, sample["t"])
            b = min(
                duration,
                item_samples[i + 1]["t"] if i + 1 < len(item_samples) else duration,
            )
            if b <= a:
                continue
            state = dict(sample)
            state["capture_fps"] = round(sample.get("capture_fps", fps))
            state["music_position"] = round(sample.get("music_position", 0) * 4) / 4
            state["music_phase"] = (
                (math.floor(a * 4) * 12) % 360 if sample.get("music_playing") else 0
            )
            keys = {
                "keyboard": ("keys",),
                "mouse": ("buttons",),
                "cps": ("cps",),
                "fps": ("capture_fps",),
                "music": (
                    "music",
                    "music_artist",
                    "music_position",
                    "music_duration",
                    "music_playing",
                    "music_phase",
                ),
            }.get(kind, ())
            key = repr([state.get(k) for k in keys])
            if kind == "timer":
                key = str(int(a))
            if kind == "clicks":
                if not sample.get("click"):
                    continue
                px = round(sample.get("cursor", [0.5, 0.5])[0] * width)
                py = round(sample.get("cursor", [0.5, 0.5])[1] * height)
                accent = color(item.get("accent_color"), "#dce7ff")
                accent = accent[5:7] + accent[3:5] + accent[1:3]
                lines.append(
                    dialogue(
                        a,
                        min(duration, a + 0.25),
                        rf"{{\an5\pos({px},{py})\fs{round(45 * scale)}\c&H{accent}&\fad(0,220)}}○",
                        2,
                    )
                )
                continue
            if spans and spans[-1][3] == key and abs(spans[-1][1] - a) < 0.001:
                spans[-1][1] = b
            else:
                spans.append([a, b, state, key])
        for a, b, state, _ in spans:
            for drawing in ass_shapes(item, state, x, y, scale, alpha):
                lines.append(dialogue(a, b, drawing))
    Path(path).write_text("".join(lines), encoding="utf-8-sig")


def copy_fonts(destination):
    """Keep rendered captions consistent on machines without our UI font installed."""
    import shutil
    from .config import ROOT

    fonts = Path(destination) / "fonts"
    fonts.mkdir(exist_ok=True)
    for source in (ROOT / "assets/fonts").glob("Manrope-*.ttf"):
        shutil.copyfile(source, fonts / source.name)
