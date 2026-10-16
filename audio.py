"""Microphone capture while the hotkey is held. 16kHz mono int16, what Whisper wants."""

import io
import threading
import wave

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
STREAM_READY_TIMEOUT = 0.75
MAX_SAMPLES = SAMPLE_RATE * 600


class RecordingError(RuntimeError):
    """A capture was incomplete; retain its WAV rather than transcribing it."""

    def __init__(self, message: str, wav_bytes: bytes):
        super().__init__(message)
        self.wav_bytes = wav_bytes


class Recorder:
    def __init__(self, preferred_device: str | None = None):
        self.preferred_device = preferred_device
        self.device = self._resolve_preferred_device(preferred_device)
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._first_frame = threading.Event()
        self._samples = 0
        self._capture_error = ""

    @staticmethod
    def _resolve_preferred_device(preferred_device: str | None) -> int | None:
        """Use a named input when it exists; otherwise keep the system default."""
        if not preferred_device:
            return None
        needle = preferred_device.casefold()
        for index, device in enumerate(sd.query_devices()):
            if device["max_input_channels"] and needle in device["name"].casefold():
                return index
        return None

    @staticmethod
    def _candidate_devices(preferred_device: str | None) -> list[int | None]:
        """Return inputs in recovery order, without stale numeric assumptions."""
        devices = list(sd.query_devices())
        candidates: list[int | None] = []

        def add(index: int | None) -> None:
            if index not in candidates:
                candidates.append(index)

        if preferred_device:
            needle = preferred_device.casefold()
            for index, device in enumerate(devices):
                if device["max_input_channels"] and needle in device["name"].casefold():
                    add(index)

        default_input = sd.default.device[0]
        if isinstance(default_input, int) and default_input >= 0:
            add(default_input)
        else:
            add(None)

        for index, device in enumerate(devices):
            name = device["name"].casefold()
            if device["max_input_channels"] and "microphone" in name:
                add(index)

        for index, device in enumerate(devices):
            if device["max_input_channels"]:
                add(index)

        return candidates

    @property
    def device_name(self) -> str:
        if self.device is None:
            return "system default microphone"
        return str(sd.query_devices(self.device)["name"])

    @staticmethod
    def _refresh_portaudio() -> None:
        """Rebuild PortAudio's device view before each new recording."""
        terminate = getattr(sd, "_terminate", None)
        initialize = getattr(sd, "_initialize", None)
        if callable(terminate) and callable(initialize):
            terminate()
            initialize()

    def start(self) -> None:
        self._refresh_portaudio()
        candidates = self._candidate_devices(self.preferred_device)
        attempted: list[str] = []
        last_error: Exception | None = None

        for device in candidates:
            self.device = device
            attempted.append(self.device_name)
            try:
                if self._open_candidate(device):
                    return
            except Exception as exc:
                last_error = exc
            self._close_stream()

        detail = ", ".join(attempted) or "no input devices"
        message = f"No microphone delivered audio. Tried: {detail}."
        if last_error is not None:
            message += f" Last error: {last_error}"
        raise RuntimeError(message)

    def _open_candidate(self, device: int | None) -> bool:
        self._frames = []
        self._samples = 0
        self._capture_error = ""
        self._first_frame.clear()
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            device=device,
            callback=self._on_audio,
        )
        self._stream.start()
        return self._first_frame.wait(STREAM_READY_TIMEOUT)

    def _close_stream(self) -> None:
        if self._stream is not None:
            stream = self._stream
            self._stream = None
            try:
                stream.stop()
            finally:
                stream.close()

    def _on_audio(self, indata, frames, time_info, status) -> None:
        if status:
            self._capture_error = "The microphone dropped audio; recording saved for review."
        remaining = MAX_SAMPLES - self._samples
        if len(indata) > remaining:
            self._capture_error = "The recording reached its memory limit; audio saved for review."
        if remaining > 0:
            block = indata[:remaining].copy()
            self._frames.append(block)
            self._samples += len(block)
        self._first_frame.set()

    def stop(self) -> tuple[bytes, float]:
        """Return WAV bytes and duration. Raise if the selected input went dead."""
        try:
            self._close_stream()
        except Exception:
            self._capture_error = "The microphone did not close cleanly; audio saved for review."
        if not self._frames:
            raise RuntimeError(
                f"{self.device_name} opened but returned no audio. "
                "Check that it is connected and selected."
            )
        data = np.concatenate(self._frames)
        self._frames = []
        duration = len(data) / SAMPLE_RATE

        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SAMPLE_RATE)
            w.writeframes(data.tobytes())
        wav_bytes = buf.getvalue()
        if self._capture_error:
            raise RecordingError(self._capture_error, wav_bytes)
        return wav_bytes, duration
