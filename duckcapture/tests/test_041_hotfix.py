"""Regression checks that do not require a graphical Windows session."""
from pathlib import Path
from PIL import Image
from duckcapture import __version__
from duckcapture.media import Media


def test_bitrate_api_accepts_new_setting():
    media = Media()
    commands = []
    media.require = lambda: None
    media.run = lambda args, **kwargs: commands.append(args)
    assert media.encoder("Automático", (1280, 720), "Equilibrado", 30, bitrate_mbps=24)
    assert commands
    assert "24M" in commands[0]


def test_fresh_version_and_brand_asset():
    root = Path(__file__).resolve().parents[1]
    assert __version__ == "0.5.2"
    with Image.open(root / "duckcapture" / "assets" / "brand-icon.png") as icon:
        assert icon.mode == "RGBA" and icon.size == (400, 400)
        assert icon.getbbox()
    assert "0.5.2" in (root / "installer" / "DuckCapture.iss").read_text("utf-8")
    assert "brand-icon.png" in (root / "duckcapture" / "app.py").read_text("utf-8")


def test_spotify_url_parser_only_allows_spotify():
    # Evaluate the pure helper without Qt to allow CI without a display server.
    import ast
    import re
    from urllib.parse import urlparse
    source = (Path(__file__).resolve().parents[1] / "duckcapture" / "spotify.py").read_text("utf-8")
    tree = ast.parse(source)
    func = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == "browser_url")
    ast.fix_missing_locations(func)
    scope = {
        "re": re, "urlparse": urlparse,
        "START_URL": "https://open.spotify.com/intl-pt/",
        "ALLOWED_HOSTS": {"spotify.com", "www.spotify.com", "open.spotify.com", "accounts.spotify.com", "spotify.link"},
    }
    exec(compile(ast.Module(body=[func], type_ignores=[]), "<browser_url>", "exec"), scope)
    browser_url = scope["browser_url"]
    assert browser_url("") == "https://open.spotify.com/intl-pt/"
    assert browser_url("spotify.com") == "https://spotify.com"
    assert browser_url("https://open.spotify.com/intl-pt/") == "https://open.spotify.com/intl-pt/"
    for forbidden in ("https://google.com", "http://open.spotify.com", "https://open.spotify.com.evil.test"):
        try:
            browser_url(forbidden)
        except ValueError:
            continue
        raise AssertionError(f"Host should be rejected: {forbidden}")
