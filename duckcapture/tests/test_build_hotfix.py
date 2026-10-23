"""Offline regression tests: never reuse the destination of an old PyInstaller build."""
from pathlib import Path
import importlib.util


def load_builder():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "build_windows.py"
    spec = importlib.util.spec_from_file_location("duck_build_hotfix_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_staging_is_unique(tmp_path):
    builder = load_builder()
    builder.BUILD = tmp_path
    builder.STAGE_ROOT = tmp_path
    older = tmp_path / "dist" / "DuckCapture" / "_internal" / "PySide6"
    older.mkdir(parents=True)
    (older / "Qt6QuickParticles.dll").write_bytes(b"locked-prev-build")
    stage_a = builder.unique_stage()
    stage_b = builder.unique_stage()
    assert stage_a != stage_b
    assert stage_a.parent == tmp_path
    assert stage_b.parent == tmp_path
    assert (older / "Qt6QuickParticles.dll").read_bytes() == b"locked-prev-build"


def test_pyinstaller_uses_only_new_stage(tmp_path):
    builder = load_builder()
    builder.BUILD = tmp_path
    builder.STAGE_ROOT = tmp_path
    stage = builder.unique_stage()
    args = [str(a) for a in builder.pyinstaller_command(stage, tmp_path / "icon.ico", tmp_path / "tools")]
    assert args[args.index("--distpath") + 1] == str(stage / "dist")
    assert args[args.index("--workpath") + 1] == str(stage / "work")
    assert args[args.index("--specpath") + 1] == str(stage / "spec")
    assert str(tmp_path / "dist") not in args


def test_inno_receives_stage_and_corrected_filename(tmp_path):
    builder = load_builder()
    seen = []
    builder.run = lambda command, **kwargs: seen.extend(str(x) for x in command)
    source = tmp_path / "stage space" / "dist" / "DuckCapture"
    builder.compile_installer("ISCC.exe", source)
    assert "/DDuckCaptureSource=" + str(source) in seen
    assert "/FDuckCapture-Setup-0.5.2" in seen
    iss = (Path(__file__).resolve().parents[1] / "installer" / "DuckCapture.iss").read_text(encoding="utf-8")
    assert 'Source: "{#DuckCaptureSource}\\*"' in iss
    assert 'Source: "..\\.build\\dist\\DuckCapture\\*"' not in iss
