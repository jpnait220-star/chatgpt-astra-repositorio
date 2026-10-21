"""Generate DuckCapture's original 1.08-second stereo confirmation chime."""
from pathlib import Path
import wave
import numpy as np


def create_clip(path):
    rate = 48000
    t = np.arange(round(1.08 * rate)) / rate
    rng = np.random.default_rng(5048)
    left, right = np.zeros_like(t), np.zeros_like(t)
    for start, frequency, gain, pan in [(0, 659.255, .72, -.2), (.105, 987.767, .62, .15), (.20, 1318.51, .46, .3)]:
        u = np.maximum(0, t - start)
        envelope = (1 - np.exp(-u*300)) * np.exp(-u*7) * (t >= start)
        tone = np.sin(2*np.pi*frequency*u) + .18*np.sin(2*np.pi*2*frequency*u) + .055*np.sin(2*np.pi*3*frequency*u)
        for delay, echo in [(0, 1), (.075, .18), (.145, .08)]:
            shift = round(delay*rate)
            voice = tone * envelope * gain
            if shift:
                voice = np.concatenate((np.zeros(shift), voice[:-shift]))
            left += voice * echo * (1-pan)
            right += voice * echo * (1+pan)
    # A warm low click and a short filtered air sweep give definition without clipping.
    body = .18*np.sin(2*np.pi*(175*t+15*(1-np.exp(-t*20))))*np.exp(-t*27)*(1-np.exp(-t*500))
    noise = np.convolve(rng.normal(size=len(t)), np.ones(8)/8, mode='same')
    air = noise*.11*np.sin(np.pi*np.minimum(1,t/.15))**2*(t<.15)
    samples = np.column_stack((left+body+air, right+body+air))
    samples *= np.minimum(1, t/.004)[:, None] * np.minimum(1, (1.08-t)/.09)[:, None]
    samples *= .91/np.max(np.abs(samples))
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as output:
        output.setnchannels(2); output.setsampwidth(2); output.setframerate(rate)
        output.writeframes((samples*32767).astype('<i2').tobytes())


if __name__ == '__main__':
    create_clip(Path(__file__).resolve().parents[1] / 'duckcapture/assets/clip.wav')
