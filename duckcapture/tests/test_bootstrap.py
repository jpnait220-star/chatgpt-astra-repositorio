import subprocess
import sys

import pytest

from scripts import bootstrap


def test_installer_handles_spaces_and_accents_and_reports_failure(tmp_path):
    folder = tmp_path / "pasta & com espaço d'usuário"
    folder.mkdir()
    bootstrap.run_checked([sys.executable, "-c", "print('resultado correto')"], folder)
    assert "resultado correto" in (folder / "instalacao.log").read_text(
        encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="código 7"):
        bootstrap.run_checked([sys.executable, "-c", "raise SystemExit(7)"], folder)


def test_existing_installation_does_not_reinstall_pip_dependencies(
    tmp_path, monkeypatch
):
    python = tmp_path / ".venv" / "Scripts" / "python.exe"
    python.parent.mkdir(parents=True)
    python.write_bytes(b"existing installation")
    monkeypatch.setattr(bootstrap, "validate_runtime", lambda: None)
    monkeypatch.setattr(bootstrap, "dependencies_ready", lambda *_: True)
    calls = []
    monkeypatch.setattr(bootstrap, "run_checked", lambda args, root: calls.append(args))
    assert bootstrap.prepare(tmp_path) == python
    assert not any("pip" in call or "venv" in call for call in calls)
    assert python.read_bytes() == b"existing installation"


def test_failed_installation_never_launches_the_app_and_keeps_diagnostics(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(bootstrap, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["Abrir DuckCapture.py", "--sem-pausa"])

    def failed_setup():
        raise PermissionError("Arquivo bloqueado: python.exe")

    monkeypatch.setattr(bootstrap, "prepare", failed_setup)
    launched = []
    monkeypatch.setattr(bootstrap, "launch", lambda *_: launched.append(True))
    assert bootstrap.main() == 1
    assert not launched
    assert "python.exe" in (tmp_path / "instalacao.log").read_text(encoding="utf-8")


def test_launch_reports_early_exit_instead_of_claiming_success(tmp_path, monkeypatch):
    python = tmp_path / "python.exe"
    python.with_name("pythonw.exe").touch()

    class FailedProcess:
        def wait(self, timeout):
            return 1

    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: FailedProcess())
    with pytest.raises(RuntimeError, match="inicializacao.log"):
        bootstrap.launch(python, tmp_path)


def test_launcher_rejects_wrong_python_version(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys, "version_info", (3, 11, 0))
    with pytest.raises(RuntimeError, match="Python 3.12 de 64 bits"):
        bootstrap.validate_runtime()
