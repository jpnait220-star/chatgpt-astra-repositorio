"""Create reproducible source/native download archives without build caches or secrets."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import shutil
import struct

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "downloads"
OUT.mkdir(parents=True, exist_ok=True)
EXCLUDED = {".godot", ".git", "build", "__pycache__"}

with ZipFile(OUT / "LastZone-Godot-Projeto.zip", "w", ZIP_DEFLATED) as archive:
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if not path.is_file() or any(part in EXCLUDED for part in relative.parts):
            continue
        if path.suffix in {".import", ".pyc"} or path.name.startswith(".env"):
            continue
        archive.write(path, Path("last-zone-godot") / relative)

for platform, filename, output in [
    ("windows", "LastZone.exe", "LastZone-Godot-Windows.zip"),
    ("linux", "LastZone.x86_64", "LastZone-Godot-Linux.zip"),
]:
    folder = ROOT / "build" / platform
    binary = folder / filename
    if not binary.is_file():
        continue
    data = binary.read_bytes()
    if platform == "windows":
        assert data[:2] == b"MZ", "Windows export is not PE"
        offset = struct.unpack_from("<I", data, 0x3C)[0]
        assert data[offset:offset+4] == b"PE\0\0"
        assert struct.unpack_from("<H", data, offset + 4)[0] == 0x8664
    else:
        assert data[:4] == b"\x7fELF", "Linux export is not ELF"
    for name in ["README.md", "AUDIO-CREDITS.txt"]:
        shutil.copyfile(ROOT / name, folder / name)
    with ZipFile(OUT / output, "w", ZIP_DEFLATED, compresslevel=1) as archive:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                archive.write(path, Path("LastZone-Godot") / path.relative_to(folder))

for name in ["godot-town.png", "godot-island.png", "godot-character.png"]:
    if (ROOT / name).is_file():
        shutil.copyfile(ROOT / name, OUT / name)

for archive_path in OUT.glob("*.zip"):
    with ZipFile(archive_path) as archive:
        assert archive.testzip() is None, archive_path.name
checksums = [
    f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}"
    for path in sorted(OUT.glob("*.zip"))
]
(OUT / "SHA256SUMS.txt").write_text("\n".join(checksums) + "\n")
print("\n".join(checksums))
