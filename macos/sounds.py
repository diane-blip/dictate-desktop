"""Short local feedback sounds through macOS afplay; no microphone access."""

import math
import struct
import subprocess
import tempfile
import threading
import wave
from pathlib import Path


def _play(frequency: int, volume: float) -> None:
    def run():
        try:
            with tempfile.TemporaryDirectory(prefix="dictate-sound-") as folder:
                path = Path(folder) / "cue.wav"
                rate, count = 22050, 3307
                samples = (
                    int(
                        32767
                        * volume
                        * min(i / 330, 1)
                        * (1 - i / count) ** 1.5
                        * math.sin(2 * math.pi * frequency * i / rate)
                    )
                    for i in range(count)
                )
                with wave.open(str(path), "wb") as sound:
                    sound.setparams((1, 2, rate, 0, "NONE", "not compressed"))
                    sound.writeframes(b"".join(struct.pack("<h", s) for s in samples))
                subprocess.run(
                    ["/usr/bin/afplay", str(path)],
                    timeout=3,
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except (OSError, subprocess.SubprocessError):
            pass

    threading.Thread(target=run, daemon=True).start()


class Boops:
    def __init__(self, volume: float = 0.2):
        self.volume = max(0.0, min(volume, 1.0))

    def play_start(self):
        _play(392, self.volume)

    def play_stop(self):
        _play(294, self.volume)
