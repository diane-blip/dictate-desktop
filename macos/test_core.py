"""Offline macOS regressions. Run with PYNPUT_BACKEND=dummy; no permission prompts."""

import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import control

import cleanup
import dictate
import insert
import settings
import sounds
import transcribe


class CleanupTests(unittest.TestCase):
    def test_incomplete_response_keeps_original(self):
        cfg = {
            "cleanup": {
                "enabled": True,
                "provider": "groq",
                "groq_model": "fixture",
                "timeout_seconds": 5,
            }
        }
        text = "Keep this complete original sentence"
        for reason in ("length", "content_filter", None):
            response = Mock(
                status_code=200,
                json=lambda reason=reason: {
                    "choices": [{"finish_reason": reason, "message": {"content": "Truncated"}}]
                },
            )
            with (
                patch("cleanup.api_key", return_value="fixture"),
                patch("cleanup.httpx.post", return_value=response),
            ):
                self.assertEqual(cleanup.clean(text, [], cfg), text)

    def test_provider_error_does_not_expose_body(self):
        cfg = {"stt": {"provider": "groq", "groq_model": "fixture"}}
        with (
            patch("transcribe.api_key", return_value="fixture"),
            patch(
                "transcribe.httpx.post", return_value=Mock(status_code=401, text="private words")
            ),
        ):
            with self.assertRaises(transcribe.TranscriptionError) as caught:
                transcribe.transcribe(b"fixture", cfg)
        self.assertNotIn("private", str(caught.exception))


class RecoveryTests(unittest.TestCase):
    def test_history_exists_before_paste_and_survives_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "history.md"
            app = dictate.Controller.__new__(dictate.Controller)
            app.cfg = {
                "snippets": {"resolved_path": "unused"},
                "log": {"enabled": True, "resolved_path": path},
                "paste_combo": "cmd+v",
                "restore_clipboard": True,
            }
            app.shutdown = threading.Event()
            app.notify = Mock()
            text = "Fictional recoverable words."

            def fail(*args):
                self.assertIn(text, path.read_text(encoding="utf-8"))
                raise OSError("paste failed")

            with (
                patch("dictate.transcribe", return_value=text),
                patch("dictate.load_snippets", return_value=[]),
                patch("dictate.clean", return_value=text),
                patch("dictate.insert_text", side_effect=fail),
            ):
                app.process(b"fixture")
            self.assertEqual(app.state, dictate.IDLE)
            app.notify.assert_called_once()

    def test_shutdown_saves_without_pasting(self):
        with tempfile.TemporaryDirectory() as folder:
            app = dictate.Controller.__new__(dictate.Controller)
            path = Path(folder) / "history.md"
            app.cfg = {
                "snippets": {"resolved_path": "unused"},
                "log": {"enabled": True, "resolved_path": path},
            }
            app.shutdown = threading.Event()
            app.shutdown.set()
            with (
                patch("dictate.transcribe", return_value="Keep me"),
                patch("dictate.load_snippets", return_value=[]),
                patch("dictate.clean", return_value="Keep me"),
                patch("dictate.insert_text") as paste,
            ):
                app.process(b"fixture")
            self.assertIn("Keep me", path.read_text())
            paste.assert_not_called()


class ClipboardTests(unittest.TestCase):
    def test_failed_paste_restores_previous_text(self):
        with (
            patch("insert.pyperclip.paste", side_effect=["original", "dictated"]),
            patch("insert.pyperclip.copy") as copy,
            patch("insert.time.sleep"),
            patch("insert._send_combo", side_effect=OSError),
        ):
            with self.assertRaises(OSError):
                insert.insert_text("dictated")
            self.assertEqual(
                [call.args[0] for call in copy.call_args_list], ["dictated", "original"]
            )

    def test_user_clipboard_change_is_preserved(self):
        with (
            patch("insert.pyperclip.paste", side_effect=["original", "new user copy"]),
            patch("insert.pyperclip.copy") as copy,
            patch("insert.time.sleep"),
            patch("insert._send_combo"),
        ):
            insert.insert_text("dictated")
            copy.assert_called_once_with("dictated")

    def test_partial_modifier_failure_releases_pressed_keys(self):
        keyboard = Mock()
        keyboard.press.side_effect = [None, OSError("second modifier failed")]
        with patch("insert._kbd", keyboard):
            with self.assertRaises(OSError):
                insert._send_combo("cmd+shift+v")
        keyboard.release.assert_called_once_with(insert.Key.cmd)


class ControlTests(unittest.TestCase):
    def test_unrelated_process_cannot_be_stopped(self):
        with tempfile.TemporaryDirectory() as folder:
            pid = Path(folder) / "pid"
            pid.write_text("123")
            with (
                patch.object(control, "PID_FILE", pid),
                patch("control.owns_process", return_value=False),
                patch("control.os.kill") as kill,
            ):
                with self.assertRaises(RuntimeError):
                    control.stop()
                kill.assert_not_called()

    def test_process_match_requires_exact_installation_command(self):
        expected = f"{control.APP_DIR / '.venv/bin/python'} {control.APP_DIR / 'dictate.py'}"
        for command, result in (
            (expected, True),
            (expected + " other", False),
            ("python /other/dictate.py", False),
        ):
            with patch("control.subprocess.run", return_value=Mock(returncode=0, stdout=command)):
                self.assertEqual(control.owns_process(123), result)

    @unittest.skipUnless(sys.platform == "darwin", "real macOS process inspection")
    def test_real_owned_process_stops_without_touching_other_process(self):
        with tempfile.TemporaryDirectory(prefix="dictate test ") as folder:
            app = Path(folder)
            python = app / ".venv/bin/python"
            python.parent.mkdir(parents=True)
            python.symlink_to(sys.executable)
            script = app / "dictate.py"
            ready = app / "ready"
            script.write_text(
                f"from pathlib import Path; import time; Path({str(ready)!r}).touch(); time.sleep(120)"
            )
            owned = subprocess.Popen([str(python), str(script)])
            other = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
            try:
                pid = app / ".dictate.pid"
                pid.write_text(str(owned.pid))
                deadline = time.monotonic() + 5
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertTrue(ready.exists(), "Fixture process did not initialize")
                with patch.object(control, "APP_DIR", app), patch.object(control, "PID_FILE", pid):
                    actual = subprocess.check_output(
                        ["/bin/ps", "-p", str(owned.pid), "-o", "command="], text=True
                    ).strip()
                    self.assertTrue(control.owns_process(owned.pid), f"Process command: {actual!r}")
                    control.stop()
                owned.wait(timeout=5)
                self.assertIsNone(other.poll())
            finally:
                for process in (owned, other):
                    if process.poll() is None:
                        process.terminate()
                    process.wait(timeout=5)


class ConfigurationTests(unittest.TestCase):
    def test_cleanup_requires_explicit_opt_in(self):
        self.assertFalse(settings.load()["cleanup"]["enabled"])

    def test_bad_local_config_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "config.toml").write_bytes((settings.APP_DIR / "config.toml").read_bytes())
            (root / "config.local.toml").write_text("max_seconds = 999999")
            with patch.object(settings, "APP_DIR", root), self.assertRaises(ValueError):
                settings.load()

    def test_feedback_is_local_and_volume_is_bounded(self):
        with patch("sounds._play") as play:
            sounds.Boops(2).play_start()
        play.assert_called_once_with(392, 1.0)
