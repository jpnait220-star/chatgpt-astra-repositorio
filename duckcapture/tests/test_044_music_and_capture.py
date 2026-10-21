"""Local regression checks for 0.4.4's audio fallback inputs and CPU work."""
from pathlib import Path
import subprocess
import wave
import shutil
import numpy as np
import pytest

from duckcapture.capture import CaptureEngine
from duckcapture.config import Settings
from duckcapture.media import Media


def test_music_library_files_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv('DUCKCAPTURE_DATA', str(tmp_path / 'data'))
    music = tmp_path / 'audio-test.wav'
    music.write_bytes(b'wave file placeholder')
    s = Settings(music_files=[str(music)])
    s.save()
    assert Settings.load().music_files == [str(music)]


def test_frame_payload_reuses_cached_bytes_until_source_changes():
    engine = CaptureEngine(Media())
    engine.settings = Settings(performance_mode=True)
    source = np.zeros((16, 16, 4), dtype=np.uint8)
    result = engine._frame_payload(source, 16, 16, 8, 8)
    assert len(result) == 8 * 8 * 4
    assert engine._frame_payload(source, 16, 16, 8, 8) is result
    other = source.copy()
    other[..., 0] = 100
    result2 = engine._frame_payload(other, 16, 16, 8, 8)
    assert result2 is not result and result2 != result
    engine.shutdown()


def test_local_audio_conversion_works_with_ffmpeg(tmp_path):
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg is None:
        pytest.skip('FFmpeg is not installed here')
    mp3 = tmp_path / 'test.mp3'
    wav = tmp_path / 'test.partial.wav'
    subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-y',
                    '-f','lavfi','-i','sine=frequency=440:duration=1',
                    '-ac','2',str(mp3)],check=True)
    subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-nostdin','-y',
                    '-i',str(mp3),'-map','0:a:0','-vn','-ac','2','-ar','44100',
                    '-c:a','pcm_s16le',str(wav)],check=True)
    with wave.open(str(wav),'rb') as f:
        assert f.getnchannels() == 2
        assert f.getframerate() == 44100
        assert 43000 <= f.getnframes() <= 45000
