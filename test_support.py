"""Interactive test setup. Never type unless our own editor has foreground focus."""

import ctypes
import time
from ctypes import wintypes


def focus_editor(root, field):
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetAncestor.argtypes = (wintypes.HWND, wintypes.UINT)
    user32.GetAncestor.restype = wintypes.HWND
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.c_void_p)
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.SetForegroundWindow.argtypes = (wintypes.HWND,)
    user32.BringWindowToTop.argtypes = (wintypes.HWND,)
    root.update()
    hwnd = user32.GetAncestor(field.winfo_id(), 2)
    current = ctypes.windll.kernel32.GetCurrentThreadId()
    foreground = user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), None)
    attached = foreground != current and user32.AttachThreadInput(current, foreground, True)
    try:
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        field.focus_force()
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            root.update()
            if user32.GetForegroundWindow() == hwnd:
                return hwnd
            time.sleep(0.01)
        raise RuntimeError("Windows denied focus to the test editor; no input was sent")
    finally:
        if attached:
            user32.AttachThreadInput(current, foreground, False)
