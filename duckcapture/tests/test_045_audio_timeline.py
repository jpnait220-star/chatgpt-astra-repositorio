"""No-PySide6 regression tests for real-time audio chunk placement."""
from __future__ import annotations
import wave
from pathlib import Path
import numpy as np
from duckcapture.audio import AudioRing


def block(n=2048, sample=8900):
    return (np.ones((n,2),dtype='<i2')*sample).tobytes()


def wav_data(path):
    with wave.open(str(path), 'rb') as w:
        assert w.getframerate()==48000 and w.getnchannels()==2
        return np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2)


def test_timestamp_jitter_does_not_make_20ms_holes(tmp_path):
    audio = AudioRing()
    length = 2048/48000
    baseline = 1000.0
    jitter = [0.0,0.015,-0.012,0.010,-0.018,0.005]
    for i in range(42):
        audio.append_pcm(block(), baseline + (i+1)*length + jitter[i%len(jitter)])
    dest=tmp_path/'stable.wav'
    audio.write(dest, baseline, baseline+42*length)
    result=wav_data(dest)
    assert len(result)==42*2048
    assert np.count_nonzero(result[:,0]==0)<5
    assert audio.interruptions==0


def test_genuine_device_interruption_is_preserved(tmp_path):
    audio=AudioRing()
    length=2048/48000
    audio.append_pcm(block(sample=2000), 21.0+length)
    audio.append_pcm(block(sample=2000), 21.0+2*length)
    audio.append_pcm(block(sample=4000), 21.7+length)
    assert audio.interruptions==1
    dest=tmp_path/'gap.wav'
    audio.write(dest,21.0,21.8)
    result=wav_data(dest)
    gap=result[int(.2*48000):int(.5*48000),0]
    assert np.all(gap==0)


def test_snapshot_keeps_audio_and_prevents_extra_blocks(tmp_path):
    audio=AudioRing()
    audio.append_pcm(block(sample=777), 20+2048/48000)
    frozen=audio.snapshot(20,20.05)
    audio.append_pcm(block(sample=999), 20+2*2048/48000)
    dest=tmp_path/'snap.wav'
    frozen.write(dest,20,20.09)
    result=wav_data(dest)
    assert np.max(result[:,0])==777
    assert np.any(result[:,0]==0)


def test_stereo_pcm_alignment_errors():
    audio=AudioRing()
    try:
        audio.append_pcm(b'\x01\x02', 20)
    except ValueError:
        pass
    else:
        raise AssertionError('alignment check absent')


def test_wav_can_be_muxed_with_video_without_underrun(tmp_path):
    import subprocess, shutil
    import pytest
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        pytest.skip('FFmpeg unavailable')
    audio=AudioRing()
    start=20.
    chunks=24
    sample_frames=2048
    for i in range(chunks):
        # Stereo 48k PCM with slightly irregular callback arrival.
        data=(np.tile(np.array([1500, -1500],dtype='<i2'),(sample_frames,1))).tobytes()
        audio.append_pcm(data,start+(i+1)*sample_frames/48000 + (0.011 if i%2 else -0.007))
    wav=tmp_path/'system.wav'
    audio.write(wav,start,start+chunks*sample_frames/48000)
    result=tmp_path/'clip.mp4'
    subprocess.run([shutil.which('ffmpeg'),'-hide_banner','-loglevel','error','-y',
                    '-f','lavfi','-i','color=c=black:s=256x144:r=30:d=1.024',
                    '-i',str(wav),'-map','0:v:0','-map','1:a:0',
                    '-c:v','mpeg4','-c:a','aac','-shortest',str(result)],check=True,timeout=20)
    assert result.is_file() and result.stat().st_size>1000
