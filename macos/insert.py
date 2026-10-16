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
    "cmd": Key.cmd,
    "command": Key.cmd,
    "win": Key.cmd,
    "ctrl": Key.ctrl,
    "control": Key.ctrl,
    "alt": Key.alt,
    "option": Key.alt,
    "opt": Key.alt,
    "shift": Key.shift,
}


def _send_combo(combo: str) -> None:
    """Press a combo like 'cmd+v' or 'cmd+shift+v'."""
    parts = [p.strip().lower() for p in combo.split("+") if p.strip()]
    mods = [_MODIFIERS[p] for p in parts if p in _MODIFIERS]
    keys = [p for p in parts if p not in _MODIFIERS]
    pressed = []
    try:
        for m in mods:
            _kbd.press(m)
            pressed.append(m)
        for k in keys:
            _kbd.press(k)
            _kbd.release(k)
    finally:
        for m in reversed(pressed):
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
    try:
        _send_combo(paste_combo)
    finally:
        # Never replace a newer clipboard value copied by the user meanwhile.
        if restore and old is not None:
            time.sleep(0.4)
            try:
                if pyperclip.paste() == text:
                    pyperclip.copy(old)
            except Exception:
                pass
