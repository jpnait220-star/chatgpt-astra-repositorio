"""Install-time smoke check used by the Windows build, with isolated temporary data."""
from pathlib import Path
import json
import os
import sys
import tempfile
from PySide6.QtCore import QThread


def check_installation(app, output):
    from .app import MainWindow
    from .config import Settings, ROOT
    from .media import Media
    from .typography import install_font
    from . import __version__
    result = {'version': __version__, 'platform': sys.platform, 'ok': False}
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        if sys.platform == 'win32':
            import cv2
            import importlib.util
            import windows_capture
            import winrt.windows.foundation
            import winrt.windows.foundation.collections
            import winrt.windows.media.control
            result['native_dependencies'] = bool(cv2 and windows_capture and winrt and importlib.util.find_spec('soundcard'))
        install_font()
        for name in ['fonts/Manrope-Regular.ttf', 'fonts/Manrope-Bold.ttf', 'clip.wav', 'icons/chevron-down.svg', 'brand-icon.png']:
            if not (ROOT / 'assets' / name).is_file():
                raise RuntimeError('Recurso ausente: ' + name)
        with tempfile.TemporaryDirectory(prefix='duckcapture-check-') as tmp:
            os.environ['DUCKCAPTURE_DATA'] = str(Path(tmp) / 'data')
            media = Media()
            media.require()
            clip = Path(tmp) / 'check.mp4'
            media.run(['-y', '-f', 'lavfi', '-i', 'color=c=black:s=160x90:r=30', '-t', '0.2', '-c:v', 'libx264', str(clip)])
            assert media.probe(clip).duration > 0
            result['ffmpeg_encode'] = True
            window = MainWindow(Settings(clips_dir=str(Path(tmp)/'clips'), music_dir=str(Path(tmp)/'music'), tips=False))
            try:
                window.resize(1360, 930)
                window.show()
                window.wallpaper.set_video(str(clip))
                window.wallpaper.set_blocked(False)
                for _ in range(150):
                    app.processEvents()
                    QThread.msleep(20)
                    if not window.wallpaper.frame.isNull():
                        break
                result['wallpaper_decoded'] = not window.wallpaper.frame.isNull()
                assert result['wallpaper_decoded'], 'O vídeo de fundo não produziu imagens.'
                window.wallpaper.set_blocked(True)
                from .sharing import ShareDialog
                share = ShareDialog(clip, window)
                result['sharing_dialog'] = share.reply is None
                share.reject()
                share.deleteLater()
                window.grab().save(str(output.with_suffix('.png')))
                result['window_created'] = window.isVisible()
                result['pages'] = window.stack.count()
            finally:
                window.close()
                app.processEvents()
        result['ok'] = True
    except Exception as error:
        result['error'] = repr(error)
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    return 0 if result['ok'] else 1
