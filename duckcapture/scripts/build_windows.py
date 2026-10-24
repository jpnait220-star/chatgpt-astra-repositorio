"""One-click Windows release builder. Run via CRIAR-INSTALADOR.bat.

A fresh, isolated staging directory is used for every PyInstaller build. This
prevents a previous build's in-use Qt DLL from blocking the next build.
The installer remains UNSIGNED; no Windows security setting is changed.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
import venv

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / ".build"
# PyInstaller writes hundreds of DLLs here. Keep the output OUT of Downloads,
# where folder protection, sync, and real-time scanning may interfere.
STAGE_ROOT = Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()) / "DuckCaptureBuild" / "staging"
# Installing/updating Qt while the build venv is under Downloads can fail with
# PermissionError on a DLL held open by Windows scanning or an old process.
# Place Python dependencies outside the downloaded source tree and never run
# pip install again against a known-good environment for the same requirements.
VENV_HOME = Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()) / "DuckCaptureBuild" / "environments"
ENV_POINTER = BUILD / "active-environment.txt"
VENV = VENV_HOME / "not-selected"
PY = VENV / "Scripts" / "python.exe"
OUTPUT = ROOT / "installer_saida" / "DuckCapture-Setup-0.5.3.exe"
LOG = ROOT / "erro-build.log"


def run(command, *, cwd=ROOT):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    child_env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    print("\n+ " + " ".join(str(arg) for arg in command), flush=True)
    with LOG.open("a", encoding="utf-8") as log:
        log.write("\n+ " + " ".join(str(arg) for arg in command) + "\n")
        with subprocess.Popen(
            [str(a) for a in command], cwd=cwd, env=child_env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
        ) as process:
            for line in process.stdout:
                print(line, end="", flush=True)
                log.write(line)
            code = process.wait()
    if code:
        raise subprocess.CalledProcessError(code, [str(a) for a in command])


def get_iscc():
    env = os.environ.get("ISCC_PATH", "")
    roots = [
        Path(env) if env else None,
        shutil.which("ISCC.exe"),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Inno Setup 7" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Programs" / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Programs" / "Inno Setup 7" / "ISCC.exe",
    ]
    for path in roots:
        if path and Path(path).is_file():
            return Path(path)
    return None


def ensure_iscc(automatic=True):
    tool = get_iscc()
    if tool:
        return tool
    if automatic:
        winget = shutil.which("winget")
        if winget:
            print("Instalando Inno Setup (ferramenta gratuita para o instalador)...", flush=True)
            run([
                winget, "install", "--id", "JRSoftware.InnoSetup", "-e",
                "--source", "winget", "--scope", "user",
                "--accept-package-agreements", "--accept-source-agreements",
            ])
            tool = get_iscc()
            if tool:
                return tool
    raise RuntimeError(
        "Inno Setup não foi encontrado. Instale Inno Setup 6 pelo site "
        "https://jrsoftware.org/isdl.php e execute CRIAR-INSTALADOR.bat novamente."
    )


def _requirements_signature():
    """Invalidate a reusable venv whenever pinned build dependencies change."""
    h = hashlib.sha256()
    h.update(f"python-{sys.version_info.major}.{sys.version_info.minor}-{sys.maxsize}".encode("ascii"))
    for name in ("requirements.txt", "requirements-build.txt"):
        h.update(name.encode("ascii"))
        h.update((ROOT / name).read_bytes())
    return h.hexdigest()


def _ready_environment(candidate: Path, signature: str):
    """Ignore stale, partially installed or out-of-tree environments."""
    try:
        candidate = candidate.resolve()
        if VENV_HOME.resolve() not in candidate.parents:
            return False
        return (candidate / "Scripts" / "python.exe").is_file() and (
            candidate / ".duckcapture-dependencies-ready"
        ).read_text(encoding="ascii").strip() == signature
    except (OSError, ValueError):
        return False


def _compatible_previous_environment(candidate: Path) -> bool:
    """Only reuse a preexisting virtualenv if all pinned runtime/build wheels work.

    This never modifies a previous DuckCapture version. Its interpreter is used
    READ-ONLY for PyInstaller, while staging output stays isolated in LocalAppData.
    """
    exe = candidate / "Scripts" / "python.exe"
    if not exe.is_file() or not (candidate / "pyvenv.cfg").is_file():
        return False
    # Keep this independent from pip. Failed pip updates are the reason that
    # creating a new 0.5.3 environment is currently blocked on some systems.
    probe = r"""
import importlib.metadata as md
import sys
if sys.version_info[:2] != (3, 12) or sys.maxsize <= 2**32:
    raise SystemExit(1)
required = {
    'PySide6': '6.8.3', 'PySide6-Addons': '6.8.3',
    'PySide6-Essentials': '6.8.3', 'shiboken6': '6.8.3',
    'numpy': '2.2.6', 'Pillow': '11.2.1', 'mutagen': '1.47.0',
    'windows-capture': '2.0.1', 'soundcard': '0.4.6',
    'opencv-python': '4.11.0.86', 'cffi': '1.17.1',
    'winrt-runtime': '3.2.1', 'winrt-Windows.Foundation': '3.2.1',
    'winrt-Windows.Foundation.Collections': '3.2.1', 'winrt-Windows.Media.Control': '3.2.1',
}
if any(md.version(name) != version for name, version in required.items()):
    raise SystemExit(2)
if md.version('pyinstaller').split('.')[0] != '6':
    raise SystemExit(3)
from PySide6 import QtWidgets, QtWebEngineWidgets, QtMultimedia
import numpy, PIL, cv2, soundcard, windows_capture
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager
"""
    try:
        result = subprocess.run(
            [str(exe), "-I", "-c", probe],
            cwd=ROOT, capture_output=True, text=True, timeout=45,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _previous_environment_candidates():
    """Check only adjacent, recognized DuckCapture download folders, not disk."""
    roots = [Path.home() / "Downloads"]
    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        alt = Path(userprofile) / "Downloads"
        if alt not in roots:
            roots.append(alt)
    seen = set()
    # The earlier 0.4.5 build succeeded with this very same dependency set.
    for root in roots:
        for pattern in ("DuckCapture-0.4.7*", "DuckCapture-0.4.6*", "DuckCapture-0.4.5*", "DuckCapture-0.4.4*"):
            for folder in sorted(root.glob(pattern), reverse=True):
                for candidate in (folder / "DuckCapture" / ".build" / "venv",
                                  folder / ".build" / "venv"):
                    if candidate not in seen:
                        seen.add(candidate)
                        yield candidate


def _reuse_previous_environment():
    for candidate in _previous_environment_candidates():
        if _compatible_previous_environment(candidate):
            return candidate
    return None


def create_build_environment():
    """Install once in LocalAppData; never modify a potentially locked old venv.

    A failed installation is left isolated rather than deleted (which can itself
    fail on a locked Qt DLL). The next run creates a different, empty venv.
    """
    global VENV, PY
    BUILD.mkdir(parents=True, exist_ok=True)
    VENV_HOME.mkdir(parents=True, exist_ok=True)
    signature = _requirements_signature()
    try:
        env_name = ENV_POINTER.read_text(encoding="ascii").strip()
        candidate = VENV_HOME / env_name
        if env_name and candidate.name == env_name and _ready_environment(candidate, signature):
            VENV = candidate
            PY = VENV / "Scripts" / "python.exe"
            print("Bibliotecas prontas: reutilizando ambiente de compilacao verificado.", flush=True)
            return
    except (OSError, ValueError):
        pass

    previous = _reuse_previous_environment()
    if previous is not None:
        VENV = previous
        PY = previous / "Scripts" / "python.exe"
        print("\nBibliotecas compativeis encontradas em uma versao anterior:", VENV, flush=True)
        print("Reutilizando sem instalar nem alterar bibliotecas antigas.", flush=True)
        return

    print("\nNao encontrei bibliotecas anteriores compativeis; sera criado um ambiente novo.", flush=True)
    VENV = Path(tempfile.mkdtemp(prefix="venv-", dir=VENV_HOME))
    PY = VENV / "Scripts" / "python.exe"
    print("Criando ambiente NOVO fora de Downloads: " + str(VENV), flush=True)
    try:
        venv.create(VENV, with_pip=True)
        run([PY, "-m", "pip", "install", "--no-input", "--disable-pip-version-check",
             "-r", ROOT / "requirements.txt", "-r", ROOT / "requirements-build.txt"])
        run([PY, "-m", "pip", "check"])
    except (OSError, subprocess.CalledProcessError) as exc:
        print("\nNao foi possivel preparar as bibliotecas na pasta nova. "
              "Feche outras compilacoes, reinicie o computador se necessario "
              "e consulte a Seguranca do Windows > Historico de protecao. "
              "Se um arquivo foi bloqueado, veja os detalhes e mantenha a protecao ativada. "
              "Tente recuperar a pasta de build 0.4.5 que ja funcionou.", flush=True)
        raise RuntimeError("Falha ao instalar dependencias no ambiente isolado: " + str(VENV)) from exc
    # Write the completion marker last, and only then change the reusable pointer.
    (VENV / ".duckcapture-dependencies-ready").write_text(signature, encoding="ascii")
    ENV_POINTER.write_text(VENV.name, encoding="ascii")
    print("Bibliotecas instaladas com sucesso; serao reutilizadas na proxima compilacao.", flush=True)


def unique_stage():
    """Never reuse the dist/work/spec tree from a prior interrupted build."""
    STAGE_ROOT.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="stage-", dir=STAGE_ROOT))


def pyinstaller_command(stage: Path, icon: Path, tools: Path):
    return [
        PY, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir", "--windowed", "--noupx",
        "--name", "DuckCapture", "--icon", icon,
        "--distpath", stage / "dist", "--workpath", stage / "work", "--specpath", stage / "spec",
        "--add-data", str(ROOT / "duckcapture" / "assets") + ";duckcapture/assets",
        "--add-binary", str(tools / "ffmpeg.exe") + ";tools",
        "--add-binary", str(tools / "ffprobe.exe") + ";tools",
        "--hidden-import", "PySide6.QtWebEngineWidgets",
        "--hidden-import", "PySide6.QtWebEngineCore",
        "--hidden-import", "windows_capture",
        "--hidden-import", "soundcard",
        "--hidden-import", "cv2",
        "--collect-all", "winrt",
        ROOT / "run.pyw",
    ]


def make_windows_exe():
    # All third-party Python dependencies are installed only in the build venv.
    run([PY, ROOT / "scripts" / "create_icon.py"])
    icon = BUILD / "duckcapture.ico"
    if not icon.is_file():
        raise RuntimeError("Nao foi possivel criar o icone do DuckCapture.")

    run([PY, ROOT / "scripts" / "install_ffmpeg.py", "--require-local"])
    tools = ROOT / "tools"
    for binary in ("ffmpeg.exe", "ffprobe.exe"):
        if not (tools / binary).is_file():
            raise RuntimeError("Não foi encontrado tools/" + binary)

    stage = unique_stage()
    for folder in ("dist", "work", "spec"):
        (stage / folder).mkdir(parents=True, exist_ok=True)
    output = stage / "dist" / "DuckCapture"
    print("\nCompilando em pasta NOVA para evitar DLLs bloqueadas: " + str(stage), flush=True)
    try:
        run(pyinstaller_command(stage, icon, tools))
    except subprocess.CalledProcessError as exc:
        print("\nA compilação parou. Se o log mostrar PermissionError em uma DLL, "
              "feche processos de compilação anteriores e consulte "
              "Segurança do Windows > Histórico de proteção para ver se houve bloqueio. "
              "Não desative o antivírus ou a proteção de pastas.", flush=True)
        raise RuntimeError("Falha no empacotamento. Veja erro-build.log. Pasta isolada: " + str(stage)) from exc

    if not (output / "DuckCapture.exe").is_file():
        raise RuntimeError("PyInstaller não gerou DuckCapture.exe.")
    for binary in ("ffmpeg.exe", "ffprobe.exe"):
        if not list(output.rglob(binary)):
            raise RuntimeError("O executável gerado não contém " + binary)
    print("Executável e FFmpeg incluídos no pacote isolado.", flush=True)
    (stage / "duckcapture.version").write_text("0.5.3", encoding="utf-8")
    return output, stage


def compile_installer(iscc, source_dir: Path):
    """Tell ISCC to use the exact fresh build, never the old shared dist."""
    run([iscc, "/DDuckCaptureSource=" + str(source_dir), "/F" + OUTPUT.stem, ROOT / "installer" / "DuckCapture.iss"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-winget", action="store_true", help="For CI: do not install Inno Setup")
    args = parser.parse_args()
    LOG.write_text("DuckCapture 0.5.3 - log de geração do instalador (venv antigo validado ou novo ambiente isolado)\n", encoding="utf-8")
    if os.name != "nt":
        raise RuntimeError("A geração do .exe precisa ser executada em Windows 10/11 x64.")
    if sys.version_info[:2] != (3, 12) or sys.maxsize <= 2**32:
        raise RuntimeError("Use Python 3.12 de 64 bits para criar o instalador.")

    iscc = ensure_iscc(automatic=not args.no_winget)
    create_build_environment()
    output, stage = make_windows_exe()
    compile_installer(iscc, output)
    if not OUTPUT.is_file():
        raise RuntimeError("Inno Setup não produziu " + str(OUTPUT))
    print("\nOK! Seu instalador está em: " + str(OUTPUT), flush=True)
    # Do not remove the live stage immediately: antivirus scanners on Windows
    # may briefly hold Qt DLLs after the packaging process finishes. Keeping
    # the stage avoids errors and allows diagnosis. The user can delete older
    # .build/stage-* directories when not building.
    print("Arquivos temporários da compilação: " + str(stage), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        message = traceback.format_exc()
        print("\nFALHA AO GERAR INSTALADOR\n" + message, file=sys.stderr, flush=True)
        with LOG.open("a", encoding="utf-8") as log:
            log.write("\n" + message)
        sys.exit(1)
