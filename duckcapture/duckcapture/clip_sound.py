"""Mix only the tail of the PCM file, preserving game audio and clip duration."""
import wave
from pathlib import Path
import numpy as np
from .config import ROOT


def mix_clip_chime(path, duration, volume):
    path = Path(path)
    rate, channels = 48000, 2
    count = max(1, round(duration * rate))
    with wave.open(str(ROOT / 'assets/clip.wav'), 'rb') as source:
        if (source.getframerate(), source.getnchannels(), source.getsampwidth()) != (rate, channels, 2):
            raise ValueError('Formato inesperado no som de confirmação.')
        chime = np.frombuffer(source.readframes(source.getnframes()), dtype='<i2').reshape(-1, channels).astype(np.float32)
    chime *= max(0., min(1., float(volume)))
    # Leave 80 ms after the chime; short replays get a trimmed, faded tail.
    gap = min(round(.08 * rate), count // 10)
    length = min(len(chime), count - gap)
    chime = chime[:length]
    fade = min(round(.015 * rate), length)
    chime[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)[:, None]
    start = count - gap - length
    temporary = path.with_suffix('.mixed.wav')
    existing = wave.open(str(path), 'rb') if path.exists() else None
    try:
        if existing and (existing.getframerate(), existing.getnchannels(), existing.getsampwidth(), existing.getnframes()) != (rate, channels, 2, count):
            raise ValueError('Formato inesperado no áudio do clipe.')
        with wave.open(str(temporary), 'wb') as target:
            target.setparams((channels, 2, rate, 0, 'NONE', 'not compressed'))
            for offset in range(0, count, rate):
                size = min(rate, count - offset)
                samples = (np.frombuffer(existing.readframes(size), dtype='<i2').reshape(-1, channels).copy()
                           if existing else np.zeros((size, channels), dtype='<i2'))
                left, right = max(offset, start), min(offset + size, start + length)
                if left < right:
                    original = samples[left-offset:right-offset].astype(np.float32)
                    mixed = original + chime[left-start:right-start]
                    # Stereo-linked peak reduction prevents wraparound/clipping.
                    gain = np.maximum(1., np.max(np.abs(mixed), axis=1, keepdims=True) / 32000.)
                    samples[left-offset:right-offset] = np.rint(mixed / gain).astype('<i2')
                target.writeframesraw(samples.tobytes())
    finally:
        if existing:
            existing.close()
    temporary.replace(path)
