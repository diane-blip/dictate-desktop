"""Dictate — hold a key anywhere, speak, release, text appears at your cursor.

Tray icon states: gray = idle, pink = recording, gold = processing.
Left-click the tray icon: recent dictations, one deliberate click to copy.

Tk owns the main thread via a
hidden root + mainloop; pystray runs detached; the keyboard poll and each
dictation run on daemon threads and post any UI work (the recents popup)
onto the Tk thread through a queue.
"""

import ctypes
import faulthandler
import hashlib
import logging
import os
import queue
import socket
import sys
import threading
import time
import tkinter as tk
from collections import deque
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pyperclip
import pystray
from PIL import Image, ImageDraw

import hotkeys
import settings
from audio import Recorder
from cleanup import clean
from insert import foreground_window, insert_text
from log import append_log, read_recent
from recents import Recents
from snippets import load_snippets
from sounds import Boops
from transcribe import TranscriptionError, transcribe

log = logging.getLogger("dictate")

COLOR_IDLE = "#8a8a8a"
COLOR_RECORDING = "#F49CBB"
COLOR_PROCESSING = "#AD8326"

IDLE, RECORDING, PROCESSING = "idle", "recording", "processing"

# Single-instance guard: two copies would record and insert twice per hold.
# We bind a loopback socket to a fixed port: the OS lets exactly one process
# own it, and frees it automatically when that process dies (no stale lock
# files to clean up, even after a crash). Held open for the whole run.
_SINGLE_INSTANCE_PORT = 49731
_instance_lock: socket.socket | None = None


def acquire_single_instance() -> bool:
    """Return True if we are the only instance; False if another already holds the lock."""
    global _instance_lock
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", _SINGLE_INSTANCE_PORT))
    except OSError:
        s.close()
        return False
    s.listen(1)
    _instance_lock = s  # keep a reference so it is not garbage-collected
    return True


def _icon_image(color: str) -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((8, 8, 56, 56), fill=color)
    d.rounded_rectangle((26, 18, 38, 38), radius=6, fill="#FEFCFD")  # mic body
    d.line((32, 40, 32, 48), fill="#FEFCFD", width=4)  # mic stem
    return img


class App:
    def __init__(self):
        self.cfg = settings.load()
        self.boops = Boops(self.cfg.get("sound_volume", 0.2))
        self.recorder = Recorder(self.cfg.get("audio", {}).get("preferred_input"))
        self.state = IDLE
        self.lock = threading.Lock()
        self.pressed_at = 0.0
        self.input_target = None
        self.stop_combo_poll = threading.Event()
        self.combo_thread = None

        self.q: queue.Queue = queue.Queue()
        self.root = tk.Tk()
        self.root.withdraw()
        self.recents: deque[str] = deque(maxlen=10)
        self.recents_open = False
        self._seed_recents()

        self.icon = pystray.Icon(
            "dictate",
            _icon_image(COLOR_IDLE),
            "Dictate (hold key to speak)",
            menu=pystray.Menu(
                pystray.MenuItem(
                    "Recent dictations", lambda: self.post(self.show_recents), default=True
                ),
                pystray.MenuItem("Open snippets file", self.open_snippets),
                pystray.MenuItem("Open the full log", self.open_log),
                pystray.MenuItem("Open config", self.open_config),
                pystray.MenuItem("Reload config", lambda: self.post(self.reload_config)),
                pystray.MenuItem("Quit", lambda: self.post(self.quit)),
            ),
        )

    # -- plumbing --------------------------------------------------------------

    def post(self, fn) -> None:
        """Run fn on the Tk main thread."""
        self.q.put(fn)

    def poll_queue(self) -> None:
        # A raised exception here would end the after() chain and silently kill
        # the popup plumbing, so each queued action is contained.
        try:
            while True:
                fn = self.q.get_nowait()
                try:
                    fn()
                except Exception as e:
                    log.exception("queued action failed")
                    self.recents_open = False
                    self.notify(f"Dictate error: {e}")
        except queue.Empty:
            pass
        self.root.after(40, self.poll_queue)

    # -- state / feedback ----------------------------------------------------

    def set_state(self, state: str) -> None:
        self.state = state
        color = {IDLE: COLOR_IDLE, RECORDING: COLOR_RECORDING, PROCESSING: COLOR_PROCESSING}[state]
        self.icon.icon = _icon_image(color)

    def boop(self, which: str) -> None:
        if self.cfg.get("sounds", True):
            (self.boops.play_start if which == "start" else self.boops.play_stop)()

    def notify(self, message: str) -> None:
        log.warning(message)
        try:
            self.icon.notify(message, "Dictate")
        except Exception:
            pass

    # -- recording (one polling thread owns the recorder) --------------------

    def on_press(self, _event) -> None:
        with self.lock:
            if self.state != IDLE or self.recents_open:
                return
            self.set_state(RECORDING)
            self.input_target = foreground_window()
        self.pressed_at = time.monotonic()
        try:
            self.recorder.start()
            log.info("recording started; microphone=%r", self.recorder.device_name)
            self.boop("start")
        except Exception as e:
            with self.lock:
                self.set_state(IDLE)
            self.notify(f"Microphone error: {e}")

    def on_release(self, _event) -> None:
        with self.lock:
            if self.state != RECORDING:
                return
            self.set_state(PROCESSING)
        try:
            wav_bytes, _duration = self.recorder.stop()
        except Exception as e:
            self.set_state(IDLE)
            self.notify(f"Microphone error: {e}")
            return
        self.boop("stop")

        held_ms = (time.monotonic() - self.pressed_at) * 1000
        if held_ms < self.cfg["min_hold_ms"] or not wav_bytes:
            self.set_state(IDLE)
            return
        # No length check here on purpose: a released recording is a person who
        # just finished speaking, and their words are NEVER discarded. The
        # max_seconds cap lives in the poll loop as an auto-stop that also
        # processes everything captured.

        threading.Thread(target=self.process, args=(wav_bytes,), daemon=True).start()

    def process(self, wav_bytes: bytes) -> None:
        try:
            try:
                transcript = transcribe(wav_bytes, self.cfg)
            except Exception as e:
                # The audio still exists; save it so the words are recoverable.
                saved = self._salvage_audio(wav_bytes)
                msg = str(e) if isinstance(e, TranscriptionError) else f"Unexpected error: {e}"
                if saved:
                    msg += f" — audio saved to recordings\\{saved.name}"
                self.notify(msg)
                return
            if not transcript:
                return
            try:
                snippets = load_snippets(self.cfg["snippets"]["resolved_path"])
            except (OSError, UnicodeError):
                snippets = []
                self.notify("Could not read snippets; using the transcript without expansions.")
            text = clean(transcript, snippets, self.cfg)
            if text:
                self.recents.append(text)
                log_cfg = self.cfg.get("log", {})
                if log_cfg.get("enabled"):
                    try:
                        append_log(log_cfg["resolved_path"], text)
                    except OSError:
                        self.notify(
                            "History could not be saved to disk; copy this dictation from Recents before quitting."
                        )
                # Save recovery BEFORE input. No clipboard fallback is allowed.
                insert_text(text, target=getattr(self, "input_target", None))
        except Exception as e:
            self.notify(f"Unexpected error: {e}")
        finally:
            self.set_state(IDLE)

    def _salvage_audio(self, wav_bytes: bytes) -> Path | None:
        try:
            folder = settings.APP_DIR / "recordings"
            folder.mkdir(exist_ok=True)
            path = folder / f"failed-{datetime.now():%Y%m%d-%H%M%S-%f}.wav"
            path.write_bytes(wav_bytes)
            return path
        except Exception:
            return None

    # -- recents popup (Tk thread only, via post) ------------------------------

    def _seed_recents(self) -> None:
        """Pre-fill the recents list from the tail of the dictation log, so the
        popup is useful straight after a restart."""
        log_cfg = self.cfg.get("log", {})
        path = log_cfg.get("resolved_path")
        if not path or not log_cfg.get("enabled"):
            return
        try:
            self.recents.extend(read_recent(Path(path)))
        except OSError:
            log.warning("Could not read saved history")
            return

    def show_recents(self) -> None:
        with self.lock:
            if self.recents_open or self.state != IDLE:
                return
            self.recents_open = True

        def done(cb) -> None:
            self.recents_open = False
            if cb:
                # Let the popup vanish before acting, so a notify or file-open
                # doesn't fight the closing window for focus.
                self.root.after(120, cb)

        Recents(self.root, list(self.recents)[::-1], self._copy_recent, self.open_log, done)

    def _copy_recent(self, text: str) -> None:
        """The only clipboard writer: an explicit selection in Recents.

        Recording/processing never gets a copy fallback. In particular, text
        injected while a popup is open cannot activate a recovery copy.
        """
        with self.lock:
            if self.state != IDLE:
                return
            pyperclip.copy(text)
        log.info("clipboard copy requested from Recents")
        self.notify("Copied — paste it wherever you like.")

    # -- tray menu -------------------------------------------------------------

    def open_log(self) -> None:
        log_cfg = self.cfg.get("log", {})
        path = log_cfg.get("resolved_path")
        if path and Path(path).exists():
            os.startfile(path)
        else:
            self.notify("No dictation log yet.")

    def open_snippets(self) -> None:
        os.startfile(self.cfg["snippets"]["resolved_path"])

    def open_config(self) -> None:
        path = settings.APP_DIR / "config.local.toml"
        if not path.exists():
            path.write_text("# Override settings from config.toml here.\n", encoding="utf-8")
        os.startfile(path)

    def reload_config(self) -> None:
        with self.lock:
            if self.state != IDLE:
                self.notify("Finish this dictation before reloading configuration.")
                return
            # Validate before replacing any live settings. The poller stays alive.
            cfg = settings.load()
            recorder = Recorder(cfg["audio"]["preferred_input"])
            boops = Boops(cfg["sound_volume"])
            self.cfg, self.recorder, self.boops = cfg, recorder, boops
        self.notify("Config reloaded")

    def quit(self) -> None:
        with self.lock:
            if self.state != IDLE:
                self.notify("Finish this dictation before quitting so it can be saved.")
                return
            self.stop_combo_poll.set()
            self.state = "closing"
        if self.combo_thread:
            self.combo_thread.join(timeout=1)
        self.icon.stop()
        self.post(self.root.quit)

    # -- wiring ---------------------------------------------------------------

    def hook_keys(self) -> None:
        # Level polling handles either release order without a global hook.
        self.stop_combo_poll.clear()

        def poll() -> None:
            was_down = False
            while not self.stop_combo_poll.is_set():
                try:
                    cfg = self.cfg
                    now_down = hotkeys.is_pressed(cfg["hotkey_key1"], cfg["hotkey_key2"])
                except Exception:
                    now_down = False
                if now_down and not was_down:
                    self.on_press(None)
                elif not now_down and was_down:
                    self.on_release(None)
                elif (
                    now_down
                    and was_down
                    and self.state == RECORDING
                    and time.monotonic() - self.pressed_at > self.cfg["max_seconds"]
                ):
                    # Stuck-key / marathon safety: STOP and process everything
                    # captured. Nothing is ever discarded for length. Keys are
                    # still physically down, so was_down stays True and the
                    # eventual real release is a harmless no-op (state check
                    # in on_release).
                    self.notify(
                        f"Hit the {self.cfg['max_seconds']}s cap — processing everything captured"
                    )
                    self.on_release(None)
                was_down = now_down
                self.stop_combo_poll.wait(0.02)

        self.combo_thread = threading.Thread(target=poll, daemon=True)
        self.combo_thread.start()

    def run(self) -> None:
        self.hook_keys()
        self.poll_queue()
        revision = hashlib.sha256(
            b"".join(
                (settings.APP_DIR / name).read_bytes()
                for name in ("dictate.py", "insert.py", "recents.py")
            )
        ).hexdigest()[:12]
        log.info(
            "started; hotkey=%r+%r; clipboard=recents-gesture-only; source=%s",
            self.cfg["hotkey_key1"],
            self.cfg["hotkey_key2"],
            revision,
        )
        self.icon.run_detached()
        self.root.mainloop()  # blocks until Quit
        log.info("exited normally (Quit)")


if __name__ == "__main__":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except OSError:
        pass
    handler = RotatingFileHandler(
        settings.APP_DIR / "dictate.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8"
    )
    logging.basicConfig(
        handlers=[handler], level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    # Provider INFO logs add noise; HTTP error bodies must not enter diagnostics.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    if sys.stderr is not None:
        faulthandler.enable()
    if not acquire_single_instance():
        log.info("another instance already running; exiting")
        sys.exit(0)
    try:
        App().run()
    except Exception as exc:
        log.exception("fatal error")
        ctypes.windll.user32.MessageBoxW(
            None, f"Dictate could not start: {exc}\nSee dictate.log.", "Dictate", 0x10
        )
        raise
