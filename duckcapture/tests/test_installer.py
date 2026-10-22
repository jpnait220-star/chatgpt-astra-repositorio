"""Offline checks for installer packaging and FFmpeg location resolution."""
from pathlib import Path
import duckcapture.media as media_module
from duckcapture.media import Media


def test_media_uses_bundled_ffmpeg_if_old_config_is_stale(tmp_path, monkeypatch):
    project = tmp_path / "project"
    package = project / "duckcapture"
    tools = project / "tools"
    package.mkdir(parents=True)
    tools.mkdir()
    for name in ("ffmpeg", "ffprobe"):
        (tools / name).touch()
    monkeypatch.setattr(media_module, "__file__", str(package / "media.py"))
    monkeypatch.setattr(media_module.shutil, "which", lambda _: None)
    m = Media(str(tmp_path / "pasta_antiga_inexistente"))
    assert m.ffmpeg == str(tools / "ffmpeg")
    assert m.ffprobe == str(tools / "ffprobe")


def test_media_respects_valid_user_custom_ffmpeg(tmp_path, monkeypatch):
    project = tmp_path / "project"
    package = project / "duckcapture"
    package.mkdir(parents=True)
    tools = project / "tools"
    tools.mkdir()
    custom = tmp_path / "custom ffmpeg"
    custom.mkdir()
    for folder in (tools, custom):
        for name in ("ffmpeg", "ffprobe"):
            (folder / name).touch()
    monkeypatch.setattr(media_module, "__file__", str(package / "media.py"))
    monkeypatch.setattr(media_module.shutil, "which", lambda _: None)
    m = Media(str(custom))
    assert m.ffmpeg == str(custom / "ffmpeg")
    assert m.ffprobe == str(custom / "ffprobe")


def test_windows_installer_sources_present():
    root = Path(__file__).resolve().parents[1]
    script = (root / "installer" / "DuckCapture.iss").read_text("utf-8")
    assert "PrivilegesRequired=lowest" in script
    assert "OutputBaseFilename=DuckCapture-Setup-" in script
    assert "[Icons]" in script and "[Run]" in script
    assert (root / "CRIAR-INSTALADOR.bat").is_file()
    assert (root / "scripts" / "build_windows.py").is_file()
    assert "__version__ = \"0.5.1\"" in (root / "duckcapture" / "__init__.py").read_text()
