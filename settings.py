"""Validated defaults with an optional, untracked config.local.toml overlay."""

import math
import os
import tomllib
from pathlib import Path

from dotenv import dotenv_values

from hotkeys import KEYS

APP_DIR = Path(__file__).resolve().parent
_env: dict = {}


def _merge(defaults: dict, overrides: dict, prefix: str = "") -> None:
    for key, value in overrides.items():
        label = f"{prefix}{key}"
        if key not in defaults:
            raise ValueError(f"Unknown setting: {label}")
        if isinstance(defaults[key], dict):
            if not isinstance(value, dict):
                raise ValueError(f"{label} must be a table")
            _merge(defaults[key], value, f"{label}.")
        else:
            if isinstance(value, bool) != isinstance(defaults[key], bool):
                raise ValueError(f"Invalid type for {label}")
            if isinstance(defaults[key], str) and not isinstance(value, str):
                raise ValueError(f"{label} must be text")
            defaults[key] = value


def _number(cfg: dict, key: str, low: float, high: float) -> None:
    value = cfg[key]
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or not low <= value <= high
    ):
        raise ValueError(f"{key} must be between {low} and {high}")


def load() -> dict:
    global _env
    with (APP_DIR / "config.toml").open("rb") as stream:
        cfg = tomllib.load(stream)
    local = APP_DIR / "config.local.toml"
    if local.exists():
        with local.open("rb") as stream:
            _merge(cfg, tomllib.load(stream))
    first, second = cfg["hotkey_key1"], cfg["hotkey_key2"]
    if first not in KEYS or second not in KEYS or first == second:
        raise ValueError("Choose two distinct key names listed in docs/configuration.md")
    if "left ctrl" in (first, second) and any("alt" in k for k in (first, second)):
        raise ValueError("Left Ctrl + Alt can fire during AltGr typing; choose another pair")
    _number(cfg, "min_hold_ms", 0, 2000)
    _number(cfg, "max_seconds", 1, 600)
    _number(cfg, "sound_volume", 0, 1)
    _number(cfg["cleanup"], "timeout_seconds", 1, 20)
    if cfg["stt"]["provider"] not in ("groq", "openai"):
        raise ValueError("stt.provider must be groq or openai")
    for section in ("snippets", "log"):
        cfg[section]["resolved_path"] = (APP_DIR / cfg[section]["path"]).resolve()
    # Explicit environment values take precedence. Reloading also removes deleted keys.
    _env = dotenv_values(APP_DIR / ".env", interpolate=False)
    return cfg


def api_key(name: str) -> str | None:
    return os.environ.get(name) or _env.get(name) or None
