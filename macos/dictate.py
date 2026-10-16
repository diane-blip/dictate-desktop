"""Dictate, headless. Same hotkey -> transcribe -> cleanup -> paste pipeline as
dictate.py, but with NO menu bar (that toolkit will not render on macOS 26). This
is what the background LaunchAgent runs. Feedback is the start/stop boops plus
macOS notifications; recent dictations live in dictation-log.md.

Control it with the dictatectl script (start / stop / status / log).
"""
import faulthandler
import json
import logging
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import pyperclip
from pynput import keyboard as pk

import settings
from audio import Recorder
from cleanup import clean
from insert import insert_text
from log import append_log
from snippets import load_snippets
from sounds import Boops
from transcribe import TranscriptionError, transcribe

_log_handler = logging.FileHandler(settings.APP_DIR / "dictate.log", encoding="utf-8")
logging.basicConfig(handlers=[_log_handler], level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
faulthandler.enable(_log_handler.stream)
log = logging.getLogger("dictate")

IDLE, RECORDING, PROCESSING = "idle", "recording", "processing"

KEYMAP = {
    "right cmd": pk.Key.cmd_r, "left cmd": pk.Key.cmd_l, "cmd": pk.Key.cmd,
    "right option": pk.Key.alt_r, "left option": pk.Key.alt_l, "option": pk.Key.alt,
    "right opt": pk.Key.alt_r, "left opt": pk.Key.alt_l, "opt": pk.Key.alt,
    "right ctrl": pk.Key.ctrl_r, "left ctrl": pk.Key.ctrl_l, "ctrl": pk.Key.ctrl,
    "right shift": pk.Key.shift_r, "left shift": pk.Key.shift_l, "shift": pk.Key.shift,
}

_SINGLE_INSTANCE_PORT = 49731
_instance_lock: socket.socket | None = None


def acquire_single_instance() -> bool:
    global _instance_lock
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", _SINGLE_INSTANCE_PORT))
    except OSError:
        s.close()
        return False
    s.listen(1)
    _instance_lock = s
    return True


def _resolve_key(name: str):
    key = KEYMAP.get(name.strip().lower())
    if key is None:
        raise ValueError(f"Unknown hotkey name {name!r} in config.toml")
    return key


class Controller:
    def __init__(self):
        self.cfg = settings.load()
        self.boops = Boops(self.cfg.get("sound_volume", 0.2))
        self.recorder = Recorder(self.cfg.get("audio", {}).get("preferred_input"))
        self.state = IDLE
        self.lock = threading.Lock()
        self.pressed_at = 0.0
        self.suppress_until = 0.0
        self.targets: set = set()
        self.pressed: set = set()
        self.listener: pk.Listener | None = None
        self.stop_watchdog = threading.Event()

    def boop(self, which: str) -> None:
        if self.cfg.get("sounds", True):
            (self.boops.play_start if which == "start" else self.boops.play_stop)()

    def notify(self, message: str) -> None:
        log.warning(message)
        try:
            script = f'display notification {json.dumps(message)} with title "Dictate"'
            subprocess.run(["osascript", "-e", script], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def _on_press(self, key) -> None:
        if key in self.targets:
            self.pressed.add(key)
            self._evaluate()

    def _on_release(self, key) -> None:
        if key in self.targets:
            self.pressed.discard(key)
            self._evaluate()

    def _evaluate(self) -> None:
        if time.monotonic() < self.suppress_until:
            return
        if self.targets and self.targets <= self.pressed:
            self.on_press()
        else:
            self.on_release()

    def on_press(self) -> None:
        with self.lock:
            if self.state != IDLE:
                return
            self.state = RECORDING
        self.pressed_at = time.monotonic()
        try:
            self.recorder.start()
            log.info("recording started; microphone=%r", self.recorder.device_name)
            self.boop("start")
        except Exception as e:
            with self.lock:
                self.state = IDLE
            self.notify(f"Microphone error: {e}")

    def on_release(self) -> None:
        with self.lock:
            if self.state != RECORDING:
                return
            self.state = PROCESSING
        try:
            wav_bytes, _ = self.recorder.stop()
        except Exception as e:
            self.state = IDLE
            self.notify(f"Microphone error: {e}")
            return
        self.boop("stop")
        held_ms = (time.monotonic() - self.pressed_at) * 1000
        if held_ms < self.cfg["min_hold_ms"] or not wav_bytes:
            self.state = IDLE
            return
        threading.Thread(target=self.process, args=(wav_bytes,), daemon=True).start()

    def process(self, wav_bytes: bytes) -> None:
        try:
            try:
                transcript = transcribe(wav_bytes, self.cfg)
            except Exception as e:
                saved = self._salvage_audio(wav_bytes)
                msg = str(e) if isinstance(e, TranscriptionError) else f"Unexpected error: {e}"
                if saved:
                    msg += f" — audio saved to recordings/{saved.name}"
                self.notify(msg)
                return
            if not transcript:
                return
            snippets = load_snippets(self.cfg["snippets"]["resolved_path"])
            text = clean(transcript, snippets, self.cfg)
            if text:
                self.suppress_until = time.monotonic() + 1.0
                insert_text(text, self.cfg["paste_combo"], self.cfg["restore_clipboard"])
                log_cfg = self.cfg.get("log", {})
                if log_cfg.get("enabled"):
                    try:
                        append_log(log_cfg["resolved_path"], text)
                    except Exception:
                        pass
        except Exception as e:
            self.notify(f"Unexpected error: {e}")
        finally:
            self.state = IDLE

    def _salvage_audio(self, wav_bytes: bytes) -> Path | None:
        try:
            folder = settings.APP_DIR / "recordings"
            folder.mkdir(exist_ok=True)
            path = folder / f"failed-{datetime.now():%Y%m%d-%H%M%S}.wav"
            path.write_bytes(wav_bytes)
            return path
        except Exception:
            return None

    def run(self) -> None:
        self.targets = {_resolve_key(self.cfg["hotkey_key1"]),
                        _resolve_key(self.cfg["hotkey_key2"])}
        self.listener = pk.Listener(on_press=self._on_press, on_release=self._on_release)
        self.listener.start()

        def watch() -> None:
            while not self.stop_watchdog.wait(0.25):
                if (self.state == RECORDING
                        and time.monotonic() - self.pressed_at > self.cfg["max_seconds"]):
                    self.notify(f"Hit the {self.cfg['max_seconds']}s cap — processing everything captured")
                    self.on_release()

        threading.Thread(target=watch, daemon=True).start()
        log.info("headless started; hotkey=%r+%r", self.cfg["hotkey_key1"], self.cfg["hotkey_key2"])
        self.notify("Dictate is running. Hold Right Command + Right Option to speak.")
        threading.Event().wait()  # run forever


if __name__ == "__main__":
    if not acquire_single_instance():
        log.info("another instance already running; exiting")
        sys.exit(0)
    try:
        Controller().run()
    except Exception:
        log.exception("fatal error")
        raise
