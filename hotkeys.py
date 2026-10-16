"""Read held keys through Win32; install no global keyboard hook."""

import ctypes
from ctypes import wintypes

KEYS = {
    "left ctrl": 0xA2,
    "right ctrl": 0xA3,
    "left shift": 0xA0,
    "right shift": 0xA1,
    "left alt": 0xA4,
    "right alt": 0xA5,
    "left windows": 0x5B,
    "right windows": 0x5C,
    **{f"f{i}": 0x6F + i for i in range(1, 25)},
}
_user32 = ctypes.WinDLL("user32", use_last_error=True)
_user32.GetAsyncKeyState.argtypes = (ctypes.c_int,)
_user32.GetAsyncKeyState.restype = wintypes.SHORT


def is_pressed(first: str, second: str) -> bool:
    return all(_user32.GetAsyncKeyState(KEYS[key]) & 0x8000 for key in (first, second))
