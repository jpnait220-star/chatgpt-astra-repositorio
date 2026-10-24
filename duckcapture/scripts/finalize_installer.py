"""Conclude an already-successful DuckCapture PyInstaller build.

This does not rerun pip, PyInstaller, or download FFmpeg. It only calls the
locally installed Inno Setup 6 compiler using /D (not --define).
"""
from __future__ import annotations

import sys

from build_windows import BUILD, STAGE_ROOT, OUTPUT, compile_installer, get_iscc


def find_completed_build():
    valid = []
    # Support both old builds inside the project and new builds in LocalAppData.
    for entry in [*BUILD.glob("stage-*/dist/DuckCapture"),
                  *STAGE_ROOT.glob("stage-*/dist/DuckCapture")]:
        version_file = entry.parent.parent / "duckcapture.version"
        if not version_file.is_file() or version_file.read_text(encoding="utf-8").strip() != "0.5.3":
            continue
        executable = entry / "DuckCapture.exe"
        if not executable.is_file():
            continue
        if not all(any(entry.rglob(tool)) for tool in ("ffmpeg.exe", "ffprobe.exe")):
            continue
        valid.append(executable)
    if not valid:
        raise RuntimeError(
            "Nao foi encontrada uma compilacao completa nesta pasta. "
            "Verifique se voce esta na mesma pasta onde gerou o log com "
            "'Build complete!'. Nao apague a pasta .build."
        )
    newest = max(valid, key=lambda entry: entry.stat().st_mtime)
    return newest.parent


def main():
    if sys.platform != "win32":
        raise RuntimeError("O instalador so pode ser finalizado no Windows.")
    iscc = get_iscc()
    if not iscc:
        raise RuntimeError("Inno Setup nao encontrado. Instale o Inno Setup 6.")
    source = find_completed_build()
    print("Aplicativo ja compilado encontrado:", source, flush=True)
    print("Finalizando apenas a etapa do Inno Setup...", flush=True)
    compile_installer(iscc, source)
    if not OUTPUT.is_file():
        raise RuntimeError("O Inno Setup terminou, mas o instalador nao foi encontrado: " + str(OUTPUT))
    print("INSTALADOR GERADO COM SUCESSO!", flush=True)
    print(OUTPUT, flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("\nFALHA NA FINALIZACAO:", type(exc).__name__ + ":", exc, file=sys.stderr)
        sys.exit(1)
