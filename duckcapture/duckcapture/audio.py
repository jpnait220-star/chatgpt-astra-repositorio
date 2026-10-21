"""Continuous 48 kHz WASAPI loopback audio for local replay export.

Do not timestamp every callback using ``monotonic() - duration``. Python/OS
scheduling jitter causes tiny gaps and overlaps in exported audio even if every
PCM buffer was successfully read. Instead advance on the sample clock, only
resetting after a genuine interruption (e.g., device suspension).
"""
from __future__ import annotations
import os
import threading
import time
import wave
from collections import deque
import numpy as np


class AudioRing:
    rate = 48000
    channels = 2
    # A callback may arrive late while the OS still delivers every sample.
    # Do not mistake such jitter for missing audio.
    discontinuity_seconds = 0.35

    def __init__(self, seconds=132):
        self.seconds = seconds
        self.chunks = deque()
        self.lock = threading.Lock()
        self.done = threading.Event()
        self.ready = threading.Event()
        self.error = None
        self.epoch = None
        self.thread = None
        self._next_sample_at = None
        self.interruptions = 0

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True, name="duck-audio")
        self.thread.start()
        if not self.ready.wait(6):
            self.stop()
            raise RuntimeError("O dispositivo de áudio não respondeu.")
        if self.error:
            raise RuntimeError("Áudio do sistema indisponível: " + str(self.error))

    def append_pcm(self, pcm: bytes, observed_end: float):
        """Append a stereo s16le block; observed_end is monotonic-clock time.

        The clock for successive chunks comes from their frame counts. Genuine
        pauses are preserved as silence rather than stretching stale samples.
        """
        if not pcm:
            return
        frame_bytes = 2 * self.channels
        if len(pcm) % frame_bytes:
            raise ValueError("Bloco PCM não alinhado a frames estéreo")
        seconds = (len(pcm) // frame_bytes) / self.rate
        measured_start = observed_end - seconds
        with self.lock:
            if self._next_sample_at is None:
                start = measured_start
            else:
                predicted = self._next_sample_at
                if measured_start - predicted > self.discontinuity_seconds:
                    # Real gap: indicate missing device data with silence.
                    start = measured_start
                    self.interruptions += 1
                elif predicted - observed_end > self.discontinuity_seconds:
                    # The device clock jumped backwards (sleep/device reset).
                    start = measured_start
                    self.interruptions += 1
                else:
                    start = predicted
            self.chunks.append((start, pcm))
            self._next_sample_at = start + seconds
            cutoff = observed_end - self.seconds
            while self.chunks and self.chunks[0][0] + len(self.chunks[0][1]) / (frame_bytes * self.rate) < cutoff:
                self.chunks.popleft()
        self.ready.set()

    def _run(self):
        com = None
        try:
            # Import first: SoundCard 0.4.6 initializes COM at import time.
            import soundcard as sc
            if os.name == "nt":
                import ctypes
                candidate = ctypes.WinDLL("ole32")
                candidate.CoInitializeEx.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
                candidate.CoInitializeEx.restype = ctypes.c_long
                candidate.CoUninitialize.argtypes = []
                candidate.CoUninitialize.restype = None
                result = candidate.CoInitializeEx(None, 0)
                if result not in (0, 1):
                    raise OSError(f"Falha ao iniciar áudio COM: 0x{result & 0xFFFFFFFF:08X}")
                com = candidate
            speaker = sc.default_speaker()
            if speaker is None:
                raise RuntimeError("Nenhuma saída de áudio padrão.")
            microphone = sc.get_microphone(id=speaker.id, include_loopback=True)
            # ~43ms buffers avoid 50 Python callbacks/sec and reduce scheduler
            # contention while keeping sound latency low.
            with microphone.recorder(samplerate=self.rate, channels=2, blocksize=4096) as recorder:
                while not self.done.is_set():
                    values = recorder.record(numframes=2048)
                    observed_end = time.monotonic()
                    if values is None or len(values) == 0:
                        continue
                    pcm = (np.clip(values, -1, 1) * 32767).astype('<i2').tobytes()
                    self.append_pcm(pcm, observed_end)
        except Exception as error:
            self.error = error
            self.ready.set()
        finally:
            if com is not None:
                com.CoUninitialize()

    def write(self, path, start, end):
        count = max(1, round((end - start) * self.rate))
        result = np.zeros((count, self.channels), dtype='<i2')
        with self.lock:
            chunks = list(self.chunks)
        last_right = 0
        for at, pcm in chunks:
            values = np.frombuffer(pcm, dtype='<i2').reshape(-1, self.channels)
            pos = round((at - start) * self.rate)
            left = max(0, pos)
            right = min(count, pos + len(values))
            if right <= left:
                continue
            # Only soften edges of *real* gaps. Ordinary contiguous blocks
            # remain bit-perfect; crossfading every block damages game audio.
            if left > last_right + int(self.rate * 0.008):
                tail = min(192, last_right)
                if tail:
                    result[last_right-tail:last_right] = (result[last_right-tail:last_right].astype(np.float64) * np.linspace(1, 0, tail)[:, None]).astype('<i2')
                fade = min(192, right - left)
                if fade:
                    values = values.copy()
                    x = (values[left-pos:left-pos+fade].astype(np.float64) * np.linspace(0, 1, fade)[:, None]).astype('<i2')
                    values[left-pos:left-pos+fade] = x
            result[left:right] = values[left-pos:right-pos]
            last_right = max(last_right, right)
        with wave.open(str(path), 'wb') as stream:
            stream.setnchannels(self.channels)
            stream.setsampwidth(2)
            stream.setframerate(self.rate)
            stream.writeframes(result.tobytes())

    def snapshot(self, start, end):
        frozen = AudioRing(self.seconds)
        with self.lock:
            frozen.chunks = deque((at, pcm) for at, pcm in self.chunks
                                  if at < end and at + len(pcm) / (2 * self.channels * self.rate) > start)
            frozen.interruptions = self.interruptions
        return frozen

    def stop(self):
        self.done.set()
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join(timeout=3)
