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
            media.run(['-y', '-f', 'lavfi', '-i', 'color=c=lime:s=160x90:r=30', '-t', '0.2', '-c:v', 'libx264', str(clip)])
            assert media.probe(clip).duration > 0
            result['ffmpeg_encode'] = True
            from .capture import CaptureEngine
            import numpy as np
            engine = CaptureEngine(media)
            engine.pipe_format = 'yuv420p'
            try:
                payload = engine._frame_payload(np.zeros((90,160,4),dtype=np.uint8),160,90,160,90)
                assert len(payload) == 160*90*3//2
                result['yuv_pipe'] = True
                engine.session = Path(tmp) / 'replay'
                engine.session.mkdir()
                moving = engine.session / 'frame-000000000.mkv'
                media.run(['-y','-f','lavfi','-i','testsrc2=s=160x90:r=30','-t','2','-c:v','libx264','-threads','2','-bf','0','-g','60',str(moving)])
                (engine.session / 'segments.csv').write_text(f'{moving.name},0,2\n')
                engine.output_size, engine.encoder = (160,90), 'libx264'
                settings = Settings(fps=30, clips_dir=str(Path(tmp)/'copy-check'), clip_end_sound=True)
                copied = engine._save_clip(13/30, 43/30, [], settings, engine.session, 0, None)
                assert abs(media.probe(copied).duration - 1) < .05
                def frame(path, offset):
                    return media.run(['-ss',str(offset),'-i',path,'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','pipe:1']).stdout
                assert frame(moving,13/30) == frame(copied,0)
                assert frame(copied,0) != frame(copied,.8)
                result['lossless_clip_export'] = True
            finally:
                engine.shutdown()
            from .media_jobs import MediaJob
            job = MediaJob(clip, 'share', limit=100_000)
            job.start()
            if not job.wait(30_000):
                job.cancel()
                job.wait()
                raise RuntimeError('A preparação da cópia para link excedeu o prazo.')
            assert job.result and Path(job.result).stat().st_size <= 100_000
            result['share_encode'] = True
            window = MainWindow(Settings(clips_dir=str(Path(tmp)/'clips'), music_dir=str(Path(tmp)/'music'), tips=False))
            try:
                window.resize(1360, 930)
                window.show()
                window.wallpaper.set_video(str(clip))
                window.wallpaper.set_blocked(False)
                for _ in range(400):
                    app.processEvents()
                    QThread.msleep(20)
                    if window.wallpaper.last_frame > 0:
                        break
                result['wallpaper_decoded'] = window.wallpaper.last_frame > 0
                assert result['wallpaper_decoded'], 'O vídeo de fundo não produziu imagens.'
                assert window.wallpaper.frame.pixelColor(80,45).green() > 180, 'O fundo decodificado ficou preto.'
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
        import traceback
        result['traceback'] = traceback.format_exc()
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    return 0 if result['ok'] else 1
