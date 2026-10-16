"""Bounded cloud transcription. Errors never include provider response bodies."""

import ssl

import httpx

from settings import api_key

ENDPOINTS = {
    "groq": ("https://api.groq.com/openai/v1/audio/transcriptions", "GROQ_API_KEY"),
    "openai": ("https://api.openai.com/v1/audio/transcriptions", "OPENAI_API_KEY"),
}
MAX_UPLOAD_BYTES = 25_000_000


class TranscriptionError(Exception):
    """A recoverable provider failure; the caller must retain the recording."""


def transcribe(wav_bytes: bytes, cfg: dict) -> str:
    stt = cfg["stt"]
    provider = stt["provider"]
    if provider not in ENDPOINTS:
        raise TranscriptionError(f"Unknown transcription provider: {provider}")
    if not wav_bytes or len(wav_bytes) > MAX_UPLOAD_BYTES:
        raise TranscriptionError("Recording is empty or exceeds the 25MB upload limit")
    url, key_name = ENDPOINTS[provider]
    key = api_key(key_name)
    if not key:
        raise TranscriptionError(f"Set {key_name} in .env")
    data = {"model": stt[f"{provider}_model"], "temperature": "0"}
    if stt.get("language"):
        data["language"] = stt["language"]
    try:
        response = httpx.post(
            url,
            headers={"Authorization": f"Bearer {key}"},
            files={"file": ("audio.wav", wav_bytes, "audio/wav")},
            data=data,
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=False,
            verify=ssl.create_default_context(),
        )
    except httpx.HTTPError as exc:
        raise TranscriptionError(f"Could not reach {provider}; check your connection") from exc
    if response.status_code != 200:
        raise TranscriptionError(
            f"{provider} returned HTTP {response.status_code}; check your key, quota and model"
        )
    try:
        text = response.json()["text"]
        if not isinstance(text, str):
            raise TypeError("text must be a string")
    except (ValueError, KeyError, TypeError) as exc:
        raise TranscriptionError(f"{provider} returned an invalid transcription response") from exc
    if not text.strip():
        raise TranscriptionError(f"{provider} returned no words; recording retained")
    return text.strip()
