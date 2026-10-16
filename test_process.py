"""Regression coverage for the complete app flow, not just insert_text."""

import ctypes
import os
import tempfile
import threading
import time
import tkinter as tk
import unittest
from collections import deque
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import Mock, patch

import dictate
from recents import Recents
from test_support import focus_editor


class ProcessTests(unittest.TestCase):
    def make_app(self, log_path):
        app = dictate.App.__new__(dictate.App)
        app.cfg = {
            "snippets": {"resolved_path": "unused"},
            "log": {"enabled": True, "resolved_path": log_path},
        }
        app.recents = deque(maxlen=10)
        app.state = dictate.PROCESSING
        app.lock = threading.Lock()
        app.set_state = Mock(side_effect=lambda state: setattr(app, "state", state))
        app.notify = Mock()
        app._salvage_audio = Mock(return_value=None)
        return app

    def transcription(self, text):
        stack = ExitStack()
        stack.enter_context(patch("dictate.transcribe", return_value=text))
        stack.enter_context(patch("dictate.clean", return_value=text))
        stack.enter_context(patch("dictate.load_snippets", return_value=[]))
        copy = stack.enter_context(
            patch("dictate.pyperclip.copy", side_effect=AssertionError("automatic clipboard write"))
        )
        stack.callback(copy.assert_not_called)
        # Any reintroduction of Tk's programmatic copy path is a failure.
        stack.enter_context(
            patch.object(tk.Misc, "clipboard_clear", side_effect=AssertionError("clipboard write"))
        )
        stack.enter_context(
            patch.object(tk.Misc, "clipboard_append", side_effect=AssertionError("clipboard write"))
        )
        return stack

    def test_deliberate_recent_copy_only_runs_when_idle(self):
        for state in (dictate.IDLE, dictate.RECORDING, dictate.PROCESSING):
            with self.subTest(state=state), patch("dictate.pyperclip.copy") as copy:
                app = self.make_app(Path("unused"))
                app.state = state
                app._copy_recent("The complete selected transcript.")
                if state == dictate.IDLE:
                    copy.assert_called_once_with("The complete selected transcript.")
                else:
                    copy.assert_not_called()

    def test_insertion_failure_keeps_durable_transcript_without_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "dictation.md"
            app = self.make_app(path)

            def fail(_text, **_kwargs):
                self.assertIn("Words survive insertion failure.", path.read_text(encoding="utf-8"))
                raise OSError("target rejected input")

            with (
                self.transcription("Words survive insertion failure."),
                patch("dictate.insert_text", side_effect=fail),
            ):
                app.process(b"test audio")
            self.assertEqual(list(app.recents), ["Words survive insertion failure."])
            app.set_state.assert_called_once_with(dictate.IDLE)
            app.notify.assert_called_once()

    def test_transcription_failure_keeps_audio_and_never_inserts(self):
        app = self.make_app(Path("unused"))
        with (
            patch("dictate.transcribe", side_effect=RuntimeError("offline")),
            patch("dictate.insert_text") as insert,
        ):
            app.process(b"retained audio")
        app._salvage_audio.assert_called_once_with(b"retained audio")
        insert.assert_not_called()
        app.set_state.assert_called_once_with(dictate.IDLE)

    @unittest.skipUnless(os.environ.get("DICTATE_INTEGRATION") == "1", "Windows integration test")
    def test_real_full_pipeline_and_recovery_leave_clipboard_unchanged(self):
        root = tk.Tk()
        root.title("Dictate regression verification")
        field = tk.Text(root, height=4)
        field.pack()
        root.update()
        try:
            focus_editor(root, field)
            before = ctypes.windll.user32.GetClipboardSequenceNumber()
            expected = "Unicode: Diane’s image \U0001f5bc\ufe0f\nSecond line, with 123."
            with tempfile.TemporaryDirectory() as folder:
                app = self.make_app(Path(folder) / "dictation.md")
                with self.transcription(expected):
                    app.process(b"test audio")
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline and field.get("1.0", "end-1c") != expected:
                    root.update()
                    time.sleep(0.01)
                self.assertEqual(field.get("1.0", "end-1c"), expected)
                app.notify.assert_not_called()
                self.assertEqual(ctypes.windll.user32.GetClipboardSequenceNumber(), before)
                finished = Mock(side_effect=lambda cb: cb() if cb else None)
                with patch("dictate.pyperclip.copy") as copy:
                    popup = Recents(
                        root, [expected, "Older transcript."], app._copy_recent, Mock(), finished
                    )
                    root.update()
                    x0, y0, x1, y1 = popup.canvas.bbox("row0")
                    x, y = (x0 + x1) // 2, (y0 + y1) // 2
                    # Merely opening, typing a digit, or releasing the opening
                    # click must not copy. A new click on the row must copy.
                    popup.top.event_generate("<KeyPress-1>")
                    popup.canvas.event_generate("<Motion>", x=x, y=y)
                    popup.canvas.event_generate("<ButtonRelease-1>", x=x, y=y)
                    root.update()
                    copy.assert_not_called()
                    self.assertEqual(ctypes.windll.user32.GetClipboardSequenceNumber(), before)
                    popup.canvas.event_generate("<ButtonPress-1>", x=x, y=y)
                    popup.canvas.event_generate("<ButtonRelease-1>", x=x, y=y)
                    root.update()
                    copy.assert_called_once_with(expected)
                    finished.assert_called_once()
                    empty = Recents(root, [], app._copy_recent, Mock(), Mock())
                    root.update()
                    empty._finish(None)
                    copy.assert_called_once_with(expected)
                    self.assertEqual(ctypes.windll.user32.GetClipboardSequenceNumber(), before)
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
