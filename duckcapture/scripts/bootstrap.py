"""Prepare a local Python environment and start DuckCapture without batch files."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import struct
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
PYTHON_URL = "https://www.python.org/downloads/release/python-31210/"


def validate_runtime():
    if sys.platform != "win32":
        raise RuntimeError(
            "Este iniciador é para Windows. No Linux, use python -m duckcapture."
        )
    if sys.version_info[:2] != (3, 12) or struct.calcsize("P") != 8:
        raise RuntimeError(
            "Abra este arquivo com Python 3.12 de 64 bits.\n"
            f"Instalador oficial: {PYTHON_URL}\n"
            'Na pasta do aplicativo, também pode usar: py -3.12 "Abrir DuckCapture.py"'
        )


def run_checked(arguments, root):
    """Use explicit argument lists and preserve console output in a local log."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    child_env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    command = [str(part) for part in arguments]
    with (root / "instalacao.log").open("a", encoding="utf-8") as log:
        log.write("\nExecutando: " + repr(command) + "\n")
        log.flush()
        with subprocess.Popen(
            command,
            cwd=root,
            env=child_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
        ) as process:
            for line in process.stdout:
                print(line, end="", flush=True)
                log.write(line)
            result = process.wait()
    if result:
        raise RuntimeError(
            f"A etapa com {Path(command[0]).name} terminou com código {result}. "
            "Confira a mensagem acima e instalacao.log."
        )


def dependencies_ready(python, root):
    # This checks the exact pinned versions without loading native GUI libraries.
    script = (
        "from importlib.metadata import version; from pathlib import Path; "
        "requirements=Path('requirements.txt').read_text().splitlines(); "
        "pins=[line.split(';')[0].strip().split('==') for line in requirements "
        "if line.strip() and not line.lstrip().startswith('#')]; "
        "assert all(version(name)==wanted for name,wanted in pins)"
    )
    result = subprocess.run(
        [str(python), "-c", script],
        cwd=root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        shell=False,
    )
    return result.returncode == 0


def prepare(root=ROOT):
    validate_runtime()
    python = root / ".venv" / "Scripts" / "python.exe"
    if not python.is_file():
        print("Criando o ambiente local do DuckCapture…", flush=True)
        run_checked([sys.executable, "-m", "venv", root / ".venv"], root)
    if not dependencies_ready(python, root):
        print(
            "Instalando as dependências. A primeira abertura precisa de internet.",
            flush=True,
        )
        run_checked(
            [
                python,
                "-m",
                "pip",
                "install",
                "--no-input",
                "--disable-pip-version-check",
                "-r",
                root / "requirements.txt",
            ],
            root,
        )
        if not dependencies_ready(python, root):
            raise RuntimeError(
                "As dependências não ficaram disponíveis. Consulte instalacao.log."
            )
    run_checked([python, root / "scripts" / "install_ffmpeg.py"], root)
    return python


def launch(python, root=ROOT):
    windowed = python.with_name("pythonw.exe")
    if not windowed.is_file():
        raise RuntimeError(
            "O Python local está incompleto: pythonw.exe não foi encontrado."
        )
    with (root / "inicializacao.log").open("a", encoding="utf-8") as log:
        process = subprocess.Popen(
            [str(windowed), "-m", "duckcapture"],
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            shell=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        try:
            result = process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            print(
                "DuckCapture iniciado. Se a janela não aparecer, consulte inicializacao.log."
            )
            return
    if result:
        raise RuntimeError(
            f"DuckCapture encerrou com código {result}. Abra inicializacao.log para ver o erro."
        )


def main(install_only=False):
    parser = argparse.ArgumentParser(
        description="Instala e abre DuckCapture usando Python."
    )
    parser.add_argument(
        "--sem-pausa", action="store_true", help="Não esperar Enter em caso de erro."
    )
    options = parser.parse_args()
    try:
        python = prepare()
        if install_only:
            print('Instalação concluída. Agora abra "Abrir DuckCapture.py".')
        else:
            launch(python)
    except Exception as error:
        print(f"\nNão foi possível continuar:\n{error}\n", file=sys.stderr, flush=True)
        try:
            with (ROOT / "instalacao.log").open("a", encoding="utf-8") as log:
                traceback.print_exc(file=log)
        except OSError:
            pass
        print(
            "Se o Controle de Aplicativo Inteligente mostrar um aviso, anote o nome "
            "exato do arquivo bloqueado. O iniciador não muda as proteções do Windows.",
            flush=True,
        )
        if not options.sem_pausa and sys.stdin and sys.stdin.isatty():
            try:
                input("Pressione Enter para fechar.")
            except EOFError:
                pass
        return 1
    if install_only and not options.sem_pausa and sys.stdin and sys.stdin.isatty():
        try:
            input("Pressione Enter para fechar.")
        except EOFError:
            pass
    return 0
