"""Cloud speech-to-text. Groq and OpenAI share the same OpenAI-style endpoint shape."""
import httpx

from settings import api_key

ENDPOINTS = {
    "groq": ("https://api.groq.com/openai/v1/audio/transcriptions", "GROQ_API_KEY"),
    "openai": ("https://api.openai.com/v1/audio/transcriptions", "OPENAI_API_KEY"),
}


class TranscriptionError(Exception):
    pass


def transcribe(wav_bytes: bytes, cfg: dict) -> str:
    stt = cfg["stt"]
    provider = stt["provider"]
    if provider not in ENDPOINTS:
        raise TranscriptionError(f"Unknown STT provider '{provider}' in config.toml")
    url, key_name = ENDPOINTS[provider]
    key = api_key(key_name)
    if not key:
        raise TranscriptionError(f"{key_name} is not set in .env")

    model = stt["groq_model"] if provider == "groq" else stt["openai_model"]
    data = {"model": model, "temperature": "0"}
    if stt.get("language"):
        data["language"] = stt["language"]

    try:
        resp = httpx.post(
            url,
            headers={"Authorization": f"Bearer {key}"},
            files={"file": ("audio.wav", wav_bytes, "audio/wav")},
            data=data,
            timeout=30.0,
        )
    except httpx.HTTPError as e:
        raise TranscriptionError(f"Could not reach {provider}: {e}") from e
    if resp.status_code != 200:
        raise TranscriptionError(f"{provider} returned {resp.status_code}: {resp.text[:200]}")
    return (resp.json().get("text") or "").strip()
