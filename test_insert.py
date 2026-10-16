import ctypes
import os
import time
import tkinter as tk
import unittest
from unittest.mock import patch

import insert
from test_support import focus_editor


class InsertTextTests(unittest.TestCase):
    def test_emoji_is_not_split_at_batch_boundary(self):
        batches = []
        text = "x" * (insert._CHUNK_UNITS - 1) + "\U0001f600"
        with (
            patch.object(insert, "_send_units", side_effect=batches.append),
            patch.object(insert, "_wait_for_plain_input"),
            patch.object(insert, "foreground_window", return_value=123),
        ):
            insert.insert_text(text)
        self.assertEqual([len(batch) for batch in batches], [255, 2])
        self.assertEqual(batches[-1], insert._utf16_units("\U0001f600"))

    def test_destination_captured_before_network_work_is_respected(self):
        with (
            patch.object(insert._user32, "GetForegroundWindow", return_value=456),
            patch.object(insert._user32, "GetAsyncKeyState", return_value=0),
            patch.object(insert, "_send_units") as send,
        ):
            with self.assertRaisesRegex(RuntimeError, "focus changed"):
                insert.insert_text("saved text", target=123)
            send.assert_not_called()

    def test_waits_for_each_held_modifier_without_sending_shortcuts(self):
        for modifier in insert._MODIFIERS:
            with self.subTest(modifier=modifier):
                held = {modifier}
                sent = []

                def release(_seconds, sent=sent, held=held):
                    self.assertEqual(sent, [])
                    held.clear()

                with (
                    patch.object(
                        insert._user32,
                        "GetAsyncKeyState",
                        side_effect=lambda k, held=held: 0x8000 if k in held else 0,
                    ),
                    patch.object(insert._user32, "GetForegroundWindow", return_value=123),
                    patch.object(insert.time, "sleep", side_effect=release),
                    patch.object(
                        insert,
                        "_send_units",
                        side_effect=lambda units, sent=sent: sent.extend(units),
                    ),
                ):
                    insert.insert_text("abc")
                self.assertEqual(sent, insert._utf16_units("abc"))

    def test_held_key_timeout_does_not_insert(self):
        with (
            patch.object(insert._user32, "GetAsyncKeyState", return_value=0x8000),
            patch.object(insert._user32, "GetForegroundWindow", return_value=123),
            patch.object(insert, "_RELEASE_TIMEOUT", 0),
            patch.object(insert, "_send_units") as send,
        ):
            with self.assertRaisesRegex(RuntimeError, "saved in Recents"):
                insert.insert_text("keep this recoverable")
            send.assert_not_called()

    def test_focus_change_aborts_without_typing_into_another_app(self):
        with (
            patch.object(insert._user32, "GetAsyncKeyState", return_value=0),
            patch.object(insert._user32, "GetForegroundWindow", side_effect=[123, 456]),
            patch.object(insert, "_send_units") as send,
        ):
            with self.assertRaisesRegex(RuntimeError, "focus changed"):
                insert.insert_text("keep this recoverable")
            send.assert_not_called()

    def test_utf16_units_preserve_ascii_smart_punctuation_and_emoji(self):
        text = "Diane’s image \U0001f5bc\ufe0f"
        units = insert._utf16_units(text)
        rebuilt = b"".join(unit.to_bytes(2, "little") for unit in units)
        self.assertEqual(rebuilt.decode("utf-16-le"), text)

    def test_insert_uses_direct_input(self):
        batches = []

        with patch.object(insert, "_send_units", side_effect=lambda units: batches.append(units)):
            insert.insert_text("copied image stays put")

        self.assertEqual(batches, [insert._utf16_units("copied image stays put")])

    def test_long_text_is_sent_in_order_across_chunks(self):
        text = "x" * (insert._CHUNK_UNITS + 7)
        batches = []
        with (
            patch.object(insert, "_send_units", side_effect=lambda units: batches.append(units)),
            patch.object(insert.time, "sleep"),
        ):
            insert.insert_text(text)

        self.assertEqual([len(batch) for batch in batches], [insert._CHUNK_UNITS, 7])
        self.assertEqual([unit for batch in batches for unit in batch], insert._utf16_units(text))

    @unittest.skipUnless(
        os.environ.get("DICTATE_INTEGRATION") == "1", "manual Windows integration test"
    )
    def test_real_insertion_does_not_change_clipboard(self):
        root = tk.Tk()
        root.title("Dictate input verification")
        field = tk.Text(root, width=50, height=3)
        field.pack()
        root.update()
        try:
            focus_editor(root, field)

            clipboard_before = ctypes.windll.user32.GetClipboardSequenceNumber()
            expected = "Direct Unicode: Diane’s image \U0001f5bc\ufe0f\nSecond line."
            insert.insert_text(expected)
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline and field.get("1.0", "end-1c") != expected:
                root.update()
                time.sleep(0.01)

            self.assertEqual(field.get("1.0", "end-1c"), expected)
            self.assertEqual(ctypes.windll.user32.GetClipboardSequenceNumber(), clipboard_before)
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
