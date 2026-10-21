"""Build the source application ZIP; never include a venv, tools, user clips or caches."""

import argparse
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.5.0"
TOP = [
    'README.md', 'COMECE-AQUI.txt', 'LEIA-ME.md', 'THIRD-PARTY.md', 'VALIDACAO.md',
    'requirements.txt', 'requirements-dev.txt', 'requirements-build.txt', 'pytest.ini',
    'run.pyw', 'Abrir DuckCapture.py', 'Instalar.py', 'CRIAR-INSTALADOR.bat',
    'FINALIZAR-INSTALADOR.bat', 'INSTALADOR-LEIA-PRIMEIRO.txt',
    'LICENCAS-E-DISTRIBUICAO.txt', 'ATUALIZACAO-0.5.0.md',
]


def package(output):
    output.mkdir(parents=True, exist_ok=True)
    files = [ROOT / name for name in TOP]
    for folder in ["duckcapture", "scripts", "tests", "docs", "installer"]:
        files.extend(
            p
            for p in (ROOT / folder).rglob("*")
            if p.is_file()
            and not p.is_symlink()
            and p.suffix.lower() in (".py", ".png", ".md", ".wav", ".webp", ".ttf", ".txt", ".svg", ".iss")
            and "__pycache__" not in p.parts
        )
    archive = output / f"DuckCapture-{VERSION}.zip"
    with zipfile.ZipFile(
        archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as zip:
        for path in sorted(files):
            name = "DuckCapture/" + path.relative_to(ROOT).as_posix()
            entry = zipfile.ZipInfo(name, date_time=(2026, 10, 21, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            data = path.read_bytes()
            if path.suffix == ".cmd":
                data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            zip.writestr(entry, data)
    with zipfile.ZipFile(archive) as zip:
        if zip.testzip():
            raise RuntimeError("Falha na verificação do ZIP.")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".zip.sha256").write_text(
        f"{digest}  {archive.name}\n", encoding="ascii"
    )
    print(
        f"{archive}\n{len(files)} arquivos, {archive.stat().st_size / 1024**2:.2f} MB\nSHA-256: {digest}"
    )
    return archive


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT.parent / "downloads")
    package(parser.parse_args().output)
