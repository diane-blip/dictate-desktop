"""Recent-dictations popup: left-click the tray icon, click a row (or press
its digit) to copy that dictation back to the clipboard.

Native Windows recovery popup. Opening and dismissing it never copy text.
"""

import ctypes
import tkinter as tk
import tkinter.font as tkfont
from ctypes import wintypes

from theme import ACCENT, ACTION, ACTION_TEXT, EDGE, HOVER, MUTED, ROW
from theme import SURFACE as INK
from theme import TEXT as PAPER

TRANSPARENT = "#010203"  # never-drawn key color -> real rounded corners


def _work_area(root):
    """Available rectangle on the pointer's monitor, excluding taskbars."""

    class MonitorInfo(ctypes.Structure):
        _fields_ = [
            ("size", wintypes.DWORD),
            ("monitor", wintypes.RECT),
            ("work", wintypes.RECT),
            ("flags", wintypes.DWORD),
        ]

    user = ctypes.windll.user32
    user.MonitorFromPoint.argtypes = (wintypes.POINT, wintypes.DWORD)
    user.MonitorFromPoint.restype = wintypes.HANDLE
    user.GetMonitorInfoW.argtypes = (wintypes.HANDLE, ctypes.POINTER(MonitorInfo))
    monitor = user.MonitorFromPoint(wintypes.POINT(root.winfo_pointerx(), root.winfo_pointery()), 2)
    info = MonitorInfo(size=ctypes.sizeof(MonitorInfo))
    if user.GetMonitorInfoW(monitor, ctypes.byref(info)):
        return info.work.left, info.work.top, info.work.right, info.work.bottom
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


def _place_window(top, width, height, x, y):
    """Use absolute desktop coordinates, including monitors left of the primary."""
    top.geometry(f"{width}x{height}")
    top.update_idletasks()
    user = ctypes.windll.user32
    user.GetAncestor.argtypes = (wintypes.HWND, wintypes.UINT)
    user.GetAncestor.restype = wintypes.HWND
    user.SetWindowPos.argtypes = (
        wintypes.HWND,
        wintypes.HWND,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    )
    hwnd = user.GetAncestor(top.winfo_id(), 2)  # Tk's outer native window
    if not user.SetWindowPos(hwnd, None, x, y, width, height, 0x0004 | 0x0010):
        raise OSError("Could not position recent dictations")


def _round_rect(c: tk.Canvas, x0, y0, x1, y1, r, **kw):
    pts = [
        x0 + r,
        y0,
        x1 - r,
        y0,
        x1,
        y0,
        x1,
        y0 + r,
        x1,
        y1 - r,
        x1,
        y1,
        x1 - r,
        y1,
        x0 + r,
        y1,
        x0,
        y1,
        x0,
        y1 - r,
        x0,
        y0 + r,
        x0,
        y0,
    ]
    return c.create_polygon(pts, smooth=True, **kw)


def _pick_font(root, preferred, fallback="Segoe UI"):
    try:
        families = set(tkfont.families(root))
        for name in preferred:
            if name in families:
                return name
    except Exception:
        pass
    return fallback


def _ellipsize(font: tkfont.Font, text: str, max_px: int) -> str:
    """One display line: collapse whitespace, trim to fit, add an ellipsis."""
    text = " ".join(text.split())
    if font.measure(text) <= max_px:
        return text
    low, high = 0, len(text)
    while low < high:
        middle = (low + high + 1) // 2
        if font.measure(text[:middle] + "…") <= max_px:
            low = middle
        else:
            high = middle - 1
    return text[:low].rstrip() + "…"


class Recents:
    """entries = newest-first list of dictated texts (max 10). pick(text) is
    called with the chosen full text; open_log() opens the log file. done(cb)
    is called exactly once — with the chosen action, or None on dismissal —
    when the popup closes."""

    def __init__(self, root: tk.Tk, entries, pick, open_log, done):
        self.done = done
        self.finished = False
        self._pressed_row = None

        try:
            s = ctypes.windll.user32.GetDpiForSystem() / 96.0
        except Exception:
            s = 1.0
        text_family = _pick_font(root, ["Segoe UI Variable Text", "Segoe UI"])
        disp_family = _pick_font(root, ["Segoe UI Variable Display", "Segoe UI"])
        row_font = tkfont.Font(family=text_family, size=-int(16 * s))

        pad = int(16 * s)
        row_h = int(44 * s)
        row_gap = int(5 * s)
        head_h = int(52 * s)
        chip = int(24 * s)
        left, upper, right, bottom = _work_area(root)
        scrollbar_width = int(17 * s)
        width = min(int(500 * s), right - left - 16 - scrollbar_width)

        # Rows: the entries (or one empty-state row), then "Open the full log".
        digits = [str((i + 1) % 10) for i in range(len(entries))]  # 1..9 then 0
        n_rows = max(len(entries), 1) + 1
        height = pad * 2 + head_h + n_rows * (row_h + row_gap) - row_gap
        visible_height = min(height, bottom - upper - 16)
        overflowing = visible_height < height

        self.top = tk.Toplevel(root)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", True)
        self.top.configure(bg=TRANSPARENT)
        self.top.attributes("-transparentcolor", TRANSPARENT)

        c = tk.Canvas(
            self.top, width=width, height=visible_height, bg=INK, highlightthickness=0, bd=0
        )
        c.pack(side="left")
        self.canvas = c
        if overflowing:
            scroll = tk.Scrollbar(
                self.top,
                orient="vertical",
                command=c.yview,
                width=scrollbar_width,
                borderwidth=0,
                highlightthickness=0,
            )
            scroll.pack(side="right", fill="y")
            c.configure(yscrollcommand=scroll.set, scrollregion=(0, 0, width, height))
            self.top.bind("<MouseWheel>", lambda e: c.yview_scroll(-int(e.delta / 120), "units"))
            self.top.bind("<Next>", lambda e: c.yview_scroll(1, "pages"))
            self.top.bind("<Prior>", lambda e: c.yview_scroll(-1, "pages"))

        _round_rect(
            c,
            1,
            1,
            width - 1,
            height - 1,
            int(20 * s),
            fill=INK,
            outline=EDGE,
            width=max(1, int(s)),
        )

        heading = "Recent dictations"
        c.create_text(
            pad + int(2 * s),
            pad + int(10 * s),
            anchor="w",
            text=heading,
            fill=PAPER,
            font=(disp_family, -int(18 * s), "bold"),
        )
        c.create_text(
            pad + int(2 * s),
            pad + int(34 * s),
            anchor="w",
            text="Click or press a number to copy. Esc closes.",
            fill=MUTED,
            font=(text_family, -int(13 * s)),
        )

        self._row_rects = {}
        label_px = width - pad * 2 - chip - int(38 * s)
        y = pad + head_h

        def add_row(i, chip_char, label, fill_label, cb):
            tag = f"row{i}"
            rect = _round_rect(
                c, pad, y, width - pad, y + row_h, int(11 * s), fill=ROW, outline="", tags=tag
            )
            self._row_rects[tag] = rect
            cy = y + row_h // 2
            cx = pad + int(10 * s)
            if chip_char is not None:
                _round_rect(
                    c,
                    cx,
                    cy - chip // 2,
                    cx + chip,
                    cy + chip // 2,
                    chip // 2,
                    fill=ACTION,
                    outline=ACCENT,
                    width=1,
                    tags=tag,
                )
                c.create_text(
                    cx + chip // 2,
                    cy - int(1 * s),
                    text=chip_char,
                    fill=ACTION_TEXT,
                    font=(disp_family, -int(12 * s), "bold"),
                    tags=tag,
                )
            c.create_text(
                cx + chip + int(12 * s),
                cy - int(1 * s),
                anchor="w",
                text=label,
                fill=fill_label,
                font=(text_family, -int(16 * s)),
                tags=tag,
            )
            if cb is not None:
                c.tag_bind(tag, "<Enter>", lambda e, t=tag: self._hover(t, True))
                c.tag_bind(tag, "<Leave>", lambda e, t=tag: self._hover(t, False))
                c.tag_bind(tag, "<ButtonPress-1>", lambda e, t=tag: self._press_row(t))
                c.tag_bind(tag, "<ButtonRelease-1>", lambda e, t=tag, x=cb: self._release_row(t, x))

        if entries:
            for i, text in enumerate(entries):

                def cb(t=text):
                    return pick(t)

                add_row(i, digits[i], _ellipsize(row_font, text, label_px), PAPER, cb)
                self.top.bind(digits[i], lambda e, d=digits[i], x=cb: self._digit(e, d, x))
                y += row_h + row_gap
        else:
            add_row(0, None, "Nothing dictated yet.", MUTED, None)
            y += row_h + row_gap

        add_row(n_rows - 1, "L", "Open the full log", ACCENT, open_log)
        self.top.bind("<KeyPress-l>", lambda e: self._digit(e, "L", open_log))
        self.top.bind("<KeyPress-L>", lambda e: self._digit(e, "L", open_log))

        self.top.bind("<Escape>", lambda e: self._finish(None))

        def focus_out(_event):
            def check():
                if self.finished:
                    return
                focused = self.top.focus_displayof()
                if focused is None or not str(focused).startswith(str(self.top)):
                    self._finish(None)

            self.top.after_idle(check)

        self.top.bind("<FocusOut>", focus_out)

        # Place near the cursor (which just clicked the tray icon), clamped
        # to the screen.
        total_width = width + (scrollbar_width if overflowing else 0)
        x = min(max(root.winfo_pointerx() - int(20 * s), left + 8), right - total_width - 8)
        yy = min(
            max(root.winfo_pointery() - visible_height + int(10 * s), upper + 8),
            bottom - visible_height - 8,
        )
        _place_window(self.top, total_width, visible_height, x, yy)
        self.top.focus_force()

    def _hover(self, tag, on):
        self.canvas.itemconfigure(self._row_rects[tag], fill=HOVER if on else ROW)
        self.canvas.configure(cursor="hand2" if on else "")

    def _press_row(self, tag):
        self._pressed_row = tag

    def _release_row(self, tag, cb):
        pressed = self._pressed_row
        self._pressed_row = None
        if pressed == tag:
            self._finish(cb)

    def _digit(self, event, digit, cb):
        # Unicode dictation events are VK_PACKET, not physical digit presses.
        key = ord(digit)
        if event.keycode == key and ctypes.windll.user32.GetAsyncKeyState(key) & 0x8000:
            self._finish(cb)

    def _finish(self, cb):
        if self.finished:
            return
        self.finished = True
        try:
            self.top.destroy()
        except Exception:
            pass
        self.done(cb)
