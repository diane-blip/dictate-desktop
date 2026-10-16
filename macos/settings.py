"""Config + env loading. Everything resolves relative to the app folder."""
import os
import tomllib
from pathlib import Path

from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parent


def load() -> dict:
    load_dotenv(APP_DIR / ".env")
    with open(APP_DIR / "config.toml", "rb") as f:
        cfg = tomllib.load(f)
    cfg["snippets"]["resolved_path"] = (APP_DIR / cfg["snippets"]["path"]).resolve()
    if "log" in cfg:
        cfg["log"]["resolved_path"] = (APP_DIR / cfg["log"]["path"]).resolve()
    return cfg


def api_key(name: str) -> str | None:
    return os.environ.get(name) or None
