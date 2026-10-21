"""Tests the venv retry path without actually installing hundreds of MB of Qt."""
from pathlib import Path
import importlib.util


def load_builder():
    path = Path(__file__).resolve().parents[1] / 'scripts' / 'build_windows.py'
    spec = importlib.util.spec_from_file_location('dc_046_venvfix', path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def setup_fake_environment(tmp_path, monkeypatch):
    builder = load_builder()
    builder.BUILD = tmp_path / 'project' / '.build'
    builder.VENV_HOME = tmp_path / 'LocalAppData' / 'DuckCaptureBuild' / 'environments'
    builder.ENV_POINTER = builder.BUILD / 'active-environment.txt'
    calls = []
    def create(folder, with_pip):
        assert with_pip
        assert folder.parent == builder.VENV_HOME
        py = folder / 'Scripts' / 'python.exe'
        py.parent.mkdir(parents=True, exist_ok=True)
        py.write_bytes(b'fake-python')
        calls.append('venv')
    def run(cmd, **kwargs):
        calls.append(tuple(str(p) for p in cmd))
    monkeypatch.setattr(builder.venv, 'create', create)
    monkeypatch.setattr(builder, 'run', run)
    return builder, calls


def test_dependencies_install_once_then_reuse(tmp_path, monkeypatch):
    b, calls = setup_fake_environment(tmp_path, monkeypatch)
    old = b.BUILD / 'venv' / 'Lib' / 'site-packages' / 'PySide6' / 'Qt6PdfWidgets.dll'
    old.parent.mkdir(parents=True)
    old.write_bytes(b'old-locked-DLL')
    b.create_build_environment()
    new_path = b.VENV
    assert b.VENV_HOME in b.VENV.parents
    assert (b.VENV / '.duckcapture-dependencies-ready').is_file()
    assert len(calls) == 3  # create, pip install, pip check
    calls.clear()
    b.create_build_environment()
    assert b.VENV == new_path
    assert calls == []
    assert old.read_bytes() == b'old-locked-DLL'


def test_partial_venv_is_not_reused(tmp_path, monkeypatch):
    b, calls = setup_fake_environment(tmp_path, monkeypatch)
    bad = b.VENV_HOME / 'venv-old-incomplete'
    (bad / 'Scripts').mkdir(parents=True)
    (bad / 'Scripts' / 'python.exe').write_bytes(b'incomplete')
    b.BUILD.mkdir(parents=True)
    b.ENV_POINTER.write_text(bad.name, encoding='ascii')
    b.create_build_environment()
    assert b.VENV != bad
    assert len(calls) == 3


def test_changed_requirements_creates_new_environment(tmp_path, monkeypatch):
    b, calls = setup_fake_environment(tmp_path, monkeypatch)
    b.create_build_environment()
    original = b.VENV
    old_sig = b._requirements_signature()
    monkeypatch.setattr(b, '_requirements_signature', lambda: old_sig + '-updated')
    b.create_build_environment()
    assert b.VENV != original
    assert len(calls) == 6


def test_invalid_pointer_is_ignored(tmp_path, monkeypatch):
    b, calls = setup_fake_environment(tmp_path, monkeypatch)
    b.BUILD.mkdir(parents=True)
    b.ENV_POINTER.write_text('../../malicious', encoding='ascii')
    b.create_build_environment()
    assert b.VENV_HOME in b.VENV.parents
    assert len(calls) == 3
