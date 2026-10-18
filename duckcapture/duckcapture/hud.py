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
Style: Default,Arial,24,&H00FFFFFF,&H000000FF,&H00202020,&H900D1018,0,0,0,0,100,100,0,0,1,1,0,7,0,0,0,1
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
    lines = [header(width, height)]
    samples = sorted(samples, key=lambda x: x["t"])
    if not samples or samples[0]["t"] > 0:
        samples.insert(
            0, dict(t=0, keys=[], buttons=[], cursor=[0.5, 0.5], cps=0, music="")
        )
    # Compact equal states; no keylogging beyond the fixed gameplay keys.
    spans = []
    for i, s in enumerate(samples):
        end = min(duration, samples[i + 1]["t"] if i + 1 < len(samples) else duration)
        if end > s["t"]:
            spans.append((max(0, s["t"]), end, s))
    base = height / 720
    for item in items:
        kind = item.get("kind")
        x = round(float(item["x"]) * width)
        y = round(float(item["y"]) * height)
        scale = max(0.4, min(3, float(item.get("scale", 1)))) * base
        alpha = round((1 - max(0.1, min(1, float(item.get("opacity", 1))))) * 255)
        fs = max(12, round(19 * scale))
        cell = round(34 * scale)
        gap = max(2, round(4 * scale))

        def label(a, b, text, px=x, py=y, size=fs):
            lines.append(
                dialogue(
                    a,
                    b,
                    rf"{{\pos({px},{py})\fs{size}\alpha&H{alpha:02X}&}}" + escape(text),
                    1,
                )
            )

        def key(a, b, title, px, py, pressed=False, ww=cell):
            color = "58DFFF" if pressed else "25252D"
            lines.append(
                dialogue(
                    a,
                    b,
                    rf"{{\pos({px},{py})\p1\bord0\c&H{color}&\alpha&H{alpha:02X}&}}m 0 0 l {ww} 0 {ww} {cell} 0 {cell}{{\p0}}",
                )
            )
            lines.append(
                dialogue(
                    a,
                    b,
                    rf"{{\an5\pos({px + ww // 2},{py + cell // 2})\fs{max(10, round(14 * scale))}\c&H"
                    + ("161616" if pressed else "FFFFFF")
                    + rf"&\alpha&H{alpha:02X}&}}"
                    + escape(title),
                    1,
                )
            )

        if kind == "title":
            label(0, duration, item.get("text", "DuckCapture"))
        elif kind == "fps":
            label(0, duration, f"{fps} FPS • captura")
        elif kind == "timer":
            for second in range(math.ceil(duration)):
                label(
                    second,
                    min(duration, second + 1),
                    f"{second // 60:02}:{second % 60:02}",
                )
        elif kind in ("keyboard", "mouse", "cps", "music", "clicks"):
            for a, b, s in spans:
                if kind == "keyboard":
                    mapping = [
                        ("W", 1, 0),
                        ("A", 0, 1),
                        ("S", 1, 1),
                        ("D", 2, 1),
                        ("SHIFT", 0, 2),
                        ("CTRL", 2, 2),
                    ]
                    for k, col, row in mapping:
                        key(
                            a,
                            b,
                            k,
                            x + col * (cell + gap),
                            y + row * (cell + gap),
                            k in s.get("keys", []),
                        )
                    key(
                        a,
                        b,
                        "SPACE",
                        x,
                        y + 3 * (cell + gap),
                        "SPACE" in s.get("keys", []),
                        cell * 3 + gap * 2,
                    )
                elif kind == "mouse":
                    key(a, b, "L", x, y, "L" in s.get("buttons", []))
                    key(a, b, "R", x + cell + gap, y, "R" in s.get("buttons", []))
                    label(
                        a, b, "DuckMouse", x, y + cell + gap, max(10, round(13 * scale))
                    )
                elif kind == "cps":
                    label(a, b, f"{s.get('cps', 0)} CPS")
                elif kind == "music":
                    label(a, b, "♪ " + s.get("music", "Sem música"))
                elif s.get("click"):
                    px = round(s.get("cursor", [0.5, 0.5])[0] * width)
                    py = round(s.get("cursor", [0.5, 0.5])[1] * height)
                    lines.append(
                        dialogue(
                            a,
                            min(duration, a + 0.25),
                            rf"{{\an5\pos({px},{py})\fs{round(45 * scale)}\c&H58DFFF&\fad(0,220)}}○",
                            2,
                        )
                    )
    Path(path).write_text("".join(lines), encoding="utf-8-sig")
