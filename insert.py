"""Insert Unicode text at the cursor without touching the clipboard."""

from __future__ import annotations

import ctypes
import time
from ctypes import wintypes

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
_CHUNK_UNITS = 256
_MODIFIERS = (0x10, 0x11, 0x12, 0x5B, 0x5C)  # Shift, Ctrl, Alt, left/right Win
_RELEASE_TIMEOUT = 5.0


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUT_VALUE(ctypes.Union):
    _fields_ = [
        ("mi", _MOUSEINPUT),
        ("ki", _KEYBDINPUT),
        ("hi", _HARDWAREINPUT),
    ]


class _INPUT(ctypes.Structure):
    _anonymous_ = ("value",)
    _fields_ = [("type", wintypes.DWORD), ("value", _INPUT_VALUE)]


_user32 = ctypes.WinDLL("user32", use_last_error=True)
_user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(_INPUT), ctypes.c_int)
_user32.SendInput.restype = wintypes.UINT
_user32.GetAsyncKeyState.argtypes = (ctypes.c_int,)
_user32.GetAsyncKeyState.restype = wintypes.SHORT
_user32.GetForegroundWindow.restype = wintypes.HWND


class _GUIINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hwndActive", wintypes.HWND),
        ("hwndFocus", wintypes.HWND),
        ("hwndCapture", wintypes.HWND),
        ("hwndMenuOwner", wintypes.HWND),
        ("hwndMoveSize", wintypes.HWND),
        ("hwndCaret", wintypes.HWND),
        ("rcCaret", wintypes.RECT),
    ]


_user32.GetGUIThreadInfo.argtypes = (wintypes.DWORD, ctypes.POINTER(_GUIINFO))
_user32.GetGUIThreadInfo.restype = wintypes.BOOL


def _menu_active() -> bool:
    info = _GUIINFO(cbSize=ctypes.sizeof(_GUIINFO))
    if not _user32.GetGUIThreadInfo(0, ctypes.byref(info)):
        raise RuntimeError("Cannot verify input destination; recover this dictation from Recents.")
    return bool(info.flags & 0x1C)  # menu, popup menu or system-menu mode


def _wait_for_plain_input(target) -> None:
    """Wait until transcript characters cannot become modified shortcuts.

    Releasing either dictation key ends recording; it does not mean both
    keys are up. Never synthesize releases or change the user's key state.
    """
    deadline = time.monotonic() + _RELEASE_TIMEOUT
    while any(_user32.GetAsyncKeyState(key) & 0x8000 for key in _MODIFIERS):
        if _user32.GetForegroundWindow() != target:
            raise RuntimeError("Input focus changed; your dictation is saved in Recents.")
        if time.monotonic() >= deadline:
            raise RuntimeError("A modifier key is still held; your dictation is saved in Recents.")
        time.sleep(0.01)
    if _user32.GetForegroundWindow() != target:
        raise RuntimeError("Input focus changed; your dictation is saved in Recents.")
    if _menu_active():
        raise RuntimeError("An app menu is open; your dictation is saved in Recents.")


def _utf16_units(text: str) -> list[int]:
    """Return Windows UTF-16 code units, including surrogate pairs."""
    raw = text.encode("utf-16-le")
    return [int.from_bytes(raw[i : i + 2], "little") for i in range(0, len(raw), 2)]


def _key_input(unit: int, key_up: bool) -> _INPUT:
    flags = KEYEVENTF_UNICODE | (KEYEVENTF_KEYUP if key_up else 0)
    return _INPUT(type=INPUT_KEYBOARD, ki=_KEYBDINPUT(0, unit, flags, 0, 0))


def _send_units(units: list[int]) -> None:
    inputs = []
    for unit in units:
        inputs.extend((_key_input(unit, False), _key_input(unit, True)))
    batch = (_INPUT * len(inputs))(*inputs)
    sent = _user32.SendInput(len(batch), batch, ctypes.sizeof(_INPUT))
    if sent != len(batch):
        error = ctypes.get_last_error()
        raise OSError(error, f"SendInput inserted {sent} of {len(batch)} keyboard events")


def foreground_window():
    """Capture the destination before recording, not after a network request."""
    return _user32.GetForegroundWindow()


def insert_text(text: str, target=None) -> None:
    """Type text into the focused app through Windows Unicode input events.

    Dictate deliberately does not read, replace, empty, or restore the Windows
    clipboard. A copied image, file, rich-text block, or ordinary text remains
    exactly where it was while the dictation is inserted.
    """
    units = _utf16_units(text)
    if target is None:
        target = foreground_window()
    if not target:
        raise RuntimeError("No input destination; your dictation is saved in Recents.")
    start = 0
    while start < len(units):
        end = min(start + _CHUNK_UNITS, len(units))
        # Keep a surrogate pair in one input batch, including at chunk boundaries.
        if end < len(units) and 0xD800 <= units[end - 1] <= 0xDBFF:
            end -= 1
        _wait_for_plain_input(target)
        _send_units(units[start:end])
        start = end
        if start < len(units):
            time.sleep(0.01)
