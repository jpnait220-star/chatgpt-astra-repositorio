"""Validate 0.3.0 assets/config and UI using standard project test dependencies."""
from pathlib import Path
from PIL import Image
from duckcapture.config import Settings
from duckcapture import __version__


def test_version_and_banners_present_and_small():
    root = Path(__file__).resolve().parents[1]
    assert __version__ == '0.5.1'
    for name in ('jogos', 'editor', 'atalhos', 'captura'):
        path = root / 'duckcapture' / 'assets' / 'banners' / (name + '.webp')
        assert path.is_file() and path.stat().st_size < 120000
        with Image.open(path) as image:
            assert image.size == (960, 540)


def test_settings_default_light_mode_and_config_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv('DUCKCAPTURE_DATA', str(tmp_path))
    settings = Settings()
    assert settings.fps == 60
    assert settings.performance_mode is True
    settings.accent_color = '#ab23cd'
    settings.save()
    saved = Settings.load()
    assert saved.accent_color == '#ab23cd'
    assert saved.performance_mode is True


def test_older_configuration_automatically_gets_new_fields(tmp_path, monkeypatch):
    monkeypatch.setenv('DUCKCAPTURE_DATA', str(tmp_path))
    (tmp_path / 'settings.json').write_text('{"fps": 60, "quality": "Equilibrado"}')
    restored = Settings.load()
    assert restored.fps == 60
    assert restored.performance_mode is True
    assert restored.accent_color == '#f4f6fb'
