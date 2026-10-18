from __future__ import annotations
import threading
import time
import wave
from collections import deque
import numpy as np


class AudioRing:
    rate = 48000

    def __init__(self, seconds=132):
        self.seconds = seconds
        self.chunks = deque()
        self.lock = threading.Lock()
        self.done = threading.Event()
        self.ready = threading.Event()
        self.error = None
        self.epoch = None
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True, name="duck-audio")
        self.thread.start()
        if not self.ready.wait(6):
            self.stop()
            raise RuntimeError("O dispositivo de áudio não respondeu.")
        if self.error:
            raise RuntimeError("Áudio do sistema indisponível: " + str(self.error))

    def _run(self):
        try:
            import soundcard as sc

            speaker = sc.default_speaker()
            if speaker is None:
                raise RuntimeError("Nenhuma saída de áudio padrão.")
            microphone = sc.get_microphone(id=speaker.id, include_loopback=True)
            with microphone.recorder(
                samplerate=self.rate, channels=2, blocksize=2048
            ) as recorder:
                self.ready.set()
                while not self.done.is_set():
                    data = recorder.record(numframes=960)
                    now = time.monotonic()
                    duration = len(data) / self.rate
                    pcm = (np.clip(data, -1, 1) * 32767).astype("<i2").tobytes()
                    with self.lock:
                        self.chunks.append((now - duration, pcm))
                        while self.chunks and self.chunks[0][0] < now - self.seconds:
                            self.chunks.popleft()
        except Exception as error:
            self.error = error
            self.ready.set()

    def write(self, path, start, end):
        count = max(1, round((end - start) * self.rate))
        result = np.zeros((count, 2), dtype="<i2")
        with self.lock:
            chunks = list(self.chunks)
        for at, pcm in chunks:
            values = np.frombuffer(pcm, dtype="<i2").reshape(-1, 2)
            pos = round((at - start) * self.rate)
            left = max(0, pos)
            right = min(count, pos + len(values))
            if right > left:
                result[left:right] = values[left - pos : right - pos]
        with wave.open(str(path), "wb") as stream:
            stream.setnchannels(2)
            stream.setsampwidth(2)
            stream.setframerate(self.rate)
            stream.writeframes(result.tobytes())

    def snapshot(self, start, end):
        frozen = AudioRing(self.seconds)
        with self.lock:
            frozen.chunks = deque(
                (at, pcm)
                for at, pcm in self.chunks
                if at < end and at + len(pcm) / (4 * self.rate) > start
            )
        return frozen

    def stop(self):
        self.done.set()
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join(timeout=3)
