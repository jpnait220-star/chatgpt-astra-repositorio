from pathlib import Path
import importlib.util
from types import SimpleNamespace


def module():
    path = Path(__file__).resolve().parents[1] / 'scripts' / 'build_windows.py'
    spec = importlib.util.spec_from_file_location('dc046oldervenv', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_previous_venv_search_is_limited_to_prior_duckcapture(tmp_path, monkeypatch):
    b = module()
    monkeypatch.setattr(Path, 'home', staticmethod(lambda: tmp_path))
    monkeypatch.delenv('USERPROFILE', raising=False)
    a = tmp_path / 'Downloads' / 'DuckCapture-0.4.5-Gerador-Corrigido-ucrtbase (2)' / 'DuckCapture' / '.build' / 'venv'
    a.mkdir(parents=True)
    found = list(b._previous_environment_candidates())
    assert a in found
    assert all(any(f'DuckCapture-{version}' in str(x) for version in ('0.4.7', '0.4.6', '0.4.5', '0.4.4')) for x in found)


def test_previous_venv_validation_checks_versions_and_modules(tmp_path, monkeypatch):
    b = module()
    previous = tmp_path / 'DuckCapture' / '.build' / 'venv'
    interpreter = previous / 'Scripts' / 'python.exe'
    interpreter.parent.mkdir(parents=True)
    interpreter.touch()
    (previous / 'pyvenv.cfg').touch()
    seen = []
    def run(cmd, **kw):
        seen.append((cmd, kw))
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(b.subprocess, 'run', run)
    assert b._compatible_previous_environment(previous)
    assert seen[0][0][0] == str(interpreter)
    assert 'PySide6-Addons' in seen[0][0][-1]
    assert 'QtWebEngineWidgets' in seen[0][0][-1]
    monkeypatch.setattr(b.subprocess, 'run', lambda *a, **kw: SimpleNamespace(returncode=1))
    assert not b._compatible_previous_environment(previous)


def test_existing_venv_is_used_without_pip(tmp_path, monkeypatch):
    b = module()
    b.BUILD = tmp_path / 'project' / '.build'
    b.VENV_HOME = tmp_path / 'environments'
    b.ENV_POINTER = b.BUILD / 'active-environment.txt'
    existing = tmp_path / 'prior' / '.build' / 'venv'
    (existing / 'Scripts').mkdir(parents=True)
    (existing / 'Scripts' / 'python.exe').touch()
    monkeypatch.setattr(b, '_reuse_previous_environment', lambda: existing)
    def must_not_call(*a, **kwargs):
        raise AssertionError('pip and venv must not run if previous environment works')
    monkeypatch.setattr(b, 'run', must_not_call)
    monkeypatch.setattr(b.venv, 'create', must_not_call)
    b.create_build_environment()
    assert b.VENV == existing
    assert b.PY == existing / 'Scripts' / 'python.exe'


def test_no_earlier_venv_keeps_safe_fallback(tmp_path, monkeypatch):
    b = module()
    b.BUILD = tmp_path / 'project' / '.build'
    b.VENV_HOME = tmp_path / 'environments'
    b.ENV_POINTER = b.BUILD / 'active-environment.txt'
    monkeypatch.setattr(b, '_reuse_previous_environment', lambda: None)
    events = []
    def create(folder, with_pip):
        (folder / 'Scripts').mkdir(parents=True)
        (folder / 'Scripts' / 'python.exe').touch()
        events.append('create')
    monkeypatch.setattr(b.venv, 'create', create)
    monkeypatch.setattr(b, 'run', lambda *args, **kwargs: events.append('run'))
    b.create_build_environment()
    assert events == ['create', 'run', 'run']
    assert b.VENV_HOME in b.VENV.parents
