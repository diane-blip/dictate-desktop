"""Insert text at the cursor of whatever app has focus, via the clipboard.

macOS: clipboard through pyperclip (pbcopy/pbpaste), paste keystroke through
pynput's controller. Sending the paste needs Accessibility permission, the same
grant the hotkey listener needs.
"""
import time

import pyperclip
from pynput.keyboard import Controller, Key

_kbd = Controller()

# Names accepted in config's paste_combo, mapped to pynput keys. Anything not
# here is treated as a literal character (e.g. "v").
_MODIFIERS = {
    "cmd": Key.cmd, "command": Key.cmd, "win": Key.cmd,
    "ctrl": Key.ctrl, "control": Key.ctrl,
    "alt": Key.alt, "option": Key.alt, "opt": Key.alt,
    "shift": Key.shift,
}


def _send_combo(combo: str) -> None:
    """Press a combo like 'cmd+v' or 'cmd+shift+v'."""
    parts = [p.strip().lower() for p in combo.split("+") if p.strip()]
    mods = [_MODIFIERS[p] for p in parts if p in _MODIFIERS]
    keys = [p for p in parts if p not in _MODIFIERS]
    for m in mods:
        _kbd.press(m)
    try:
        for k in keys:
            _kbd.press(k)
            _kbd.release(k)
    finally:
        for m in reversed(mods):
            _kbd.release(m)


def insert_text(text: str, paste_combo: str = "cmd+v", restore: bool = True) -> None:
    old = None
    if restore:
        try:
            # Text only: a copied image or file reads back as "" here, and
            # pyperclip can't restore those anyway.
            old = pyperclip.paste()
        except Exception:
            old = None
    pyperclip.copy(text)
    time.sleep(0.05)  # let the clipboard settle before pasting
    _send_combo(paste_combo)
    # Skip the restore when the snapshot is empty/None (non-text clipboard, or a
    # read error): writing "" back would just clear the clipboard, and the
    # image/file it held is already gone. Leaving the dictated text is the more
    # useful outcome in that case.
    if restore and old:
        time.sleep(0.4)  # target app must read the clipboard before we restore it
        try:
            pyperclip.copy(old)
        except Exception:
            pass
