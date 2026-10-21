"""Create a Windows icon from the DuckCapture mascot, without new images."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def make_icon():
    target = ROOT / ".build" / "duckcapture.ico"
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(ROOT / "duckcapture" / "assets" / "brand-icon.png") as original:
        rgba = original.convert("RGBA")
        edge = max(rgba.size)
        square = Image.new("RGBA", (edge, edge), (0, 0, 0, 0))
        square.alpha_composite(rgba, ((edge - rgba.width) // 2, (edge - rgba.height) // 2))
        square.save(target, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    return target


if __name__ == "__main__":
    print(make_icon())
