import ctypes
import os
import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from recents import Recents, _place_window


class RecentGestureTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get("DICTATE_INTEGRATION") == "1", "Windows UI test")
    def test_negative_desktop_coordinates_are_absolute(self):
        root = tk.Tk()
        root.withdraw()
        try:
            top = tk.Toplevel(root)
            top.overrideredirect(True)
            _place_window(top, 300, 200, -400, -250)
            root.update()
            self.assertEqual((top.winfo_rootx(), top.winfo_rooty()), (-400, -250))
        finally:
            root.destroy()

    @unittest.skipUnless(os.environ.get("DICTATE_INTEGRATION") == "1", "Windows UI test")
    def test_small_work_area_scrolls_to_log_action(self):
        root = tk.Tk()
        root.withdraw()
        try:
            open_log = Mock()
            with (
                patch("recents._work_area", return_value=(0, 0, 1024, 768)),
                patch("recents.ctypes.windll.user32.GetDpiForSystem", return_value=144),
            ):
                popup = Recents(
                    root,
                    [f"Transcript {i}" for i in range(10)],
                    Mock(),
                    open_log,
                    lambda cb: cb() if cb else None,
                )
            root.update()
            self.assertLessEqual(popup.top.winfo_height(), 752)
            self.assertGreaterEqual(popup.top.winfo_rooty(), 0)
            popup.canvas.yview_moveto(1)
            root.update()
            x0, y0, x1, y1 = popup.canvas.bbox("row10")
            x = (x0 + x1) // 2
            y = int((y0 + y1) // 2 - popup.canvas.canvasy(0))
            popup.canvas.event_generate("<Motion>", x=x, y=y)
            popup.canvas.event_generate("<ButtonPress-1>", x=x, y=y)
            popup.canvas.event_generate("<ButtonRelease-1>", x=x, y=y)
            root.update()
            open_log.assert_called_once_with()
        finally:
            root.destroy()

    @unittest.skipUnless(os.environ.get("DICTATE_INTEGRATION") == "1", "Windows UI test")
    def test_real_popup_click_copies_selected_text_without_opening_side_effects(self):
        root = tk.Tk()
        root.withdraw()
        before = ctypes.windll.user32.GetClipboardSequenceNumber()
        try:
            copy = Mock()
            popup = Recents(
                root,
                ["The exact full transcript.\nSecond line."],
                copy,
                Mock(),
                lambda cb: cb() if cb else None,
            )
            root.update()
            x0, y0, x1, y1 = popup.canvas.bbox("row0")
            x, y = (x0 + x1) // 2, (y0 + y1) // 2
            popup.canvas.event_generate("<Motion>", x=x, y=y)
            popup.canvas.event_generate("<ButtonRelease-1>", x=x, y=y)
            root.update()
            copy.assert_not_called()
            self.assertEqual(ctypes.windll.user32.GetClipboardSequenceNumber(), before)
            popup.canvas.event_generate("<ButtonPress-1>", x=x, y=y)
            popup.canvas.event_generate("<ButtonRelease-1>", x=x, y=y)
            root.update()
            copy.assert_called_once_with("The exact full transcript.\nSecond line.")
            self.assertEqual(ctypes.windll.user32.GetClipboardSequenceNumber(), before)
        finally:
            root.destroy()

    def popup(self):
        popup = Recents.__new__(Recents)
        popup.finished = False
        popup._pressed_row = None
        popup.top = Mock()
        popup.done = Mock(side_effect=lambda cb: cb() if cb else None)
        return popup

    def test_opening_release_or_drag_from_another_row_cannot_copy(self):
        popup = self.popup()
        copy = Mock()
        popup._release_row("row0", copy)
        popup._press_row("row1")
        popup._release_row("row0", copy)
        copy.assert_not_called()
        popup._press_row("row0")
        popup._release_row("row0", copy)
        copy.assert_called_once_with()

    def test_unicode_digit_cannot_trigger_copy_but_physical_digit_can(self):
        for keycode, state, expected in ((231, 0x8000, False), (49, 0, False), (49, 0x8000, True)):
            with (
                self.subTest(keycode=keycode, state=state),
                patch("recents.ctypes.windll.user32.GetAsyncKeyState", return_value=state),
            ):
                popup = self.popup()
                copy = Mock()
                popup._digit(SimpleNamespace(keycode=keycode), "1", copy)
                self.assertEqual(copy.call_count, int(expected))


if __name__ == "__main__":
    unittest.main()
