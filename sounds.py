"""Soft feedback boops, generated as sine-wave WAVs in memory.

winsound.Beep is a harsh square wave at fixed volume; these are quiet, low,
and faded in/out so they read as a gentle tap rather than an alarm.
"""

import io
import threading
import wave
import winsound

import numpy as np

SAMPLE_RATE = 22050


def _boop_wav(freq: float, duration_s: float, volume: float) -> bytes:
    n = int(SAMPLE_RATE * duration_s)
    t = np.linspace(0, duration_s, n, endpoint=False)
    tone = np.sin(2 * np.pi * freq * t)

    envelope = np.linspace(1, 0, n) ** 1.5  # smooth decay to silence
    attack = int(0.015 * SAMPLE_RATE)  # 15ms fade-in kills the click
    envelope[:attack] *= np.linspace(0, 1, attack)

    samples = (tone * envelope * max(0.0, min(volume, 1.0)) * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(samples.tobytes())
    return buf.getvalue()


def _play(data: bytes) -> None:
    # winsound forbids SND_ASYNC with SND_MEMORY, so play synchronously in a
    # short-lived thread. Sounds must never raise into the dictation path.
    def run():
        try:
            winsound.PlaySound(data, winsound.SND_MEMORY | winsound.SND_NODEFAULT)
        except Exception:
            pass

    threading.Thread(target=run, daemon=True).start()


class Boops:
    def __init__(self, volume: float = 0.2):
        self.start = _boop_wav(392, 0.14, volume)  # G4, rising feel
        self.stop = _boop_wav(294, 0.16, volume)  # D4, settling feel

    def play_start(self) -> None:
        _play(self.start)

    def play_stop(self) -> None:
        _play(self.stop)
