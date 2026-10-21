"""Install FFmpeg from a build distributor linked by ffmpeg.org, retaining TLS and SHA-256 checks."""

import hashlib
import os
from pathlib import Path
import shutil
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"


def install(require_local=False):
    if os.name != "nt":
        raise SystemExit(
            "Este instalador de FFmpeg é para Windows. No Linux, use o FFmpeg do seu sistema."
        )
    tools = ROOT / "tools"
    tools.mkdir(exist_ok=True)
    if (tools / "ffmpeg.exe").exists() and (tools / "ffprobe.exe").exists():
        print("FFmpeg já está disponível na pasta tools.")
        return
    if not require_local and shutil.which("ffmpeg") and shutil.which("ffprobe"):
        print("FFmpeg e ffprobe já estão no PATH.")
        return
    print("Baixando FFmpeg Essentials (Gyan). O arquivo pode ter mais de 100 MB.")
    with urllib.request.urlopen(URL + ".sha256", timeout=30) as response:
        expected = response.read().decode().strip().split()[0].lower()
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        raise RuntimeError("Checksum oficial inválido. Instalação interrompida.")
    with tempfile.TemporaryDirectory(prefix="duck-ffmpeg-") as work:
        archive = Path(work) / "ffmpeg.zip"
        digest = hashlib.sha256()
        with (
            urllib.request.urlopen(URL, timeout=90) as response,
            archive.open("wb") as output,
        ):
            while chunk := response.read(1024 * 1024):
                digest.update(chunk)
                output.write(chunk)
        if digest.hexdigest() != expected:
            raise RuntimeError(
                "O SHA-256 não corresponde ao publicado pelo distribuidor. Nenhum binário foi instalado."
            )
        with zipfile.ZipFile(archive) as source:
            for filename in ("ffmpeg.exe", "ffprobe.exe"):
                matches = [
                    n for n in source.namelist() if n.endswith("/bin/" + filename)
                ]
                if len(matches) != 1:
                    raise RuntimeError("Estrutura inesperada do pacote FFmpeg.")
                with (
                    source.open(matches[0]) as src,
                    (tools / (filename + ".tmp")).open("wb") as dst,
                ):
                    shutil.copyfileobj(src, dst)
            for filename in ("ffmpeg.exe", "ffprobe.exe"):
                (tools / (filename + ".tmp")).replace(tools / filename)
        (tools / "SOURCE.txt").write_text(
            f"FFmpeg instalado de {URL}\nSHA-256 do ZIP: {expected}\nLicenças e código-fonte: https://www.gyan.dev/ffmpeg/builds/ e https://ffmpeg.org/legal.html\n",
            encoding="utf-8",
        )
    print("FFmpeg instalado com verificação SHA-256.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Instalador do FFmpeg para o DuckCapture")
    parser.add_argument("--require-local", action="store_true", help="Baixe copias locais mesmo se existir FFmpeg no PATH")
    args = parser.parse_args()
    try:
        install(require_local=args.require_local)
    except Exception as error:
        raise SystemExit(
            f"Não foi possível instalar o FFmpeg: {error}\nAlternativa: coloque ffmpeg.exe e ffprobe.exe manualmente em tools, usando uma distribuição confiável."
        )
