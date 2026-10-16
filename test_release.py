"""Failure-path tests run offline: no API keys, microphone or clipboard writes."""

import os
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import cleanup
import dictate
import hotkeys
import settings
import transcribe
from log import append_log, read_recent
from snippets import apply_local


class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.cfg = {"cleanup": {"enabled": True, "model": "claude-haiku-5-5", "timeout_seconds": 5}}
        self.original = "I want you to keep my original words here"

    def result(self, text, reason="end_turn"):
        return SimpleNamespace(
            stop_reason=reason, content=[SimpleNamespace(type="text", text=text)]
        )

    def run_response(self, response):
        with (
            patch("cleanup.api_key", return_value="test"),
            patch("cleanup.anthropic.Anthropic") as client,
        ):
            instance = client.return_value.__enter__.return_value
            instance.messages.create.return_value = response
            result = cleanup.clean(self.original, [], self.cfg)
            client.return_value.__exit__.assert_called_once()
            return result

    def test_truncated_refused_and_incomplete_responses_fall_back(self):
        for reason in ("max_tokens", "refusal", "pause_turn", None):
            with self.subTest(reason=reason):
                self.assertEqual(
                    self.run_response(self.result("Replacement", reason)), self.original
                )

    def test_point_of_view_change_falls_back(self):
        self.assertEqual(
            self.run_response(self.result("You want me to keep your original words here")),
            self.original,
        )

    def test_commentary_falls_back(self):
        self.assertEqual(
            self.run_response(self.result("Here is the cleaned transcript.")), self.original
        )

    def test_punctuation_passes(self):
        self.assertEqual(self.run_response(self.result(self.original + ".")), self.original + ".")

    def test_network_error_falls_back_and_closes_client(self):
        with (
            patch("cleanup.api_key", return_value="test"),
            patch("cleanup.anthropic.Anthropic") as client,
        ):
            client.return_value.__enter__.return_value.messages.create.side_effect = TimeoutError()
            self.assertEqual(cleanup.clean(self.original, [], self.cfg), self.original)
            client.return_value.__exit__.assert_called_once()

    def test_short_utterance_makes_no_network_request(self):
        with (
            patch("cleanup.api_key", return_value="test"),
            patch("cleanup.anthropic.Anthropic") as client,
        ):
            self.assertEqual(cleanup.clean("thank you", [], self.cfg), "thank you")
            client.assert_not_called()


class TranscriptionTests(unittest.TestCase):
    cfg = {"stt": {"provider": "groq", "groq_model": "whisper-large-v3-turbo", "language": "en"}}

    def request(self, response):
        with (
            patch("transcribe.api_key", return_value="test"),
            patch("transcribe.httpx.post", return_value=response),
        ):
            return transcribe.transcribe(b"test audio", self.cfg)

    def test_valid_response(self):
        self.assertEqual(
            self.request(Mock(status_code=200, json=lambda: {"text": " hello "})), "hello"
        )

    def test_error_body_is_not_exposed(self):
        with self.assertRaises(transcribe.TranscriptionError) as result:
            self.request(Mock(status_code=401, text="PRIVATE TRANSCRIPT"))
        self.assertNotIn("PRIVATE", str(result.exception))

    def test_malformed_or_empty_response_is_recoverable(self):
        for payload in ({}, {"text": ""}, {"text": None}, {"text": 123}, []):
            with self.subTest(payload=payload), self.assertRaises(transcribe.TranscriptionError):
                self.request(Mock(status_code=200, json=lambda payload=payload: payload))

    def test_oversized_recording_is_not_uploaded(self):
        with (
            patch.object(transcribe, "MAX_UPLOAD_BYTES", 3),
            patch("transcribe.httpx.post") as post,
        ):
            with self.assertRaises(transcribe.TranscriptionError):
                transcribe.transcribe(b"1234", self.cfg)
            post.assert_not_called()


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        (self.root / "config.toml").write_bytes((settings.APP_DIR / "config.toml").read_bytes())
        self.scope = patch.object(settings, "APP_DIR", self.root)
        self.scope.start()
        self.addCleanup(self.scope.stop)

    def override(self, text):
        (self.root / "config.local.toml").write_text(text, encoding="utf-8")
        return settings.load()

    def test_partial_override_preserves_defaults(self):
        cfg = self.override('[stt]\nlanguage = ""\n')
        self.assertEqual(cfg["stt"]["language"], "")
        self.assertEqual(cfg["stt"]["provider"], "groq")

    def test_invalid_settings_fail_before_recording(self):
        for text in (
            "max_seconds = 9999",
            "max_seconds = nan",
            "sounds = 1",
            'hotkey_key1 = "unknown"',
            'hotkey_key2 = "left ctrl"',
            'hotkey_key2 = "right alt"',
            "sound_volume = -1",
            '[stt]\nprovider = "other"',
            "typo = true",
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.override(text)

    def test_env_reload_removes_deleted_key_and_does_not_interpolate(self):
        with patch.dict(os.environ, {}, clear=True):
            env = self.root / ".env"
            env.write_text("GROQ_API_KEY=literal-\u0024{MISSING}\n", encoding="utf-8")
            settings.load()
            self.assertEqual(settings.api_key("GROQ_API_KEY"), "literal-\u0024{MISSING}")
            env.write_text("", encoding="utf-8")
            settings.load()
            self.assertIsNone(settings.api_key("GROQ_API_KEY"))


class HistoryTests(unittest.TestCase):
    def test_multiline_unicode_round_trip_and_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "history.md"
            for index in range(15):
                append_log(path, f"Entry {index}\nSecond line 🖼\n\nLast line")
            entries = read_recent(path)
            self.assertEqual(len(entries), 10)
            self.assertEqual(entries[0], "Entry 5\nSecond line 🖼\n\nLast line")
            self.assertEqual(entries[-1], "Entry 14\nSecond line 🖼\n\nLast line")

    def test_large_history_reads_only_tail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.md"
            path.write_text("x" * 300_000 + "\n- **12:00** Latest\n", encoding="utf-8")
            self.assertEqual(read_recent(path), ["Latest"])

    def test_snippets_do_not_expand_recursively(self):
        self.assertEqual(
            apply_local(
                "brand email and email", [("brand email", "email"), ("email", "a@example.com")]
            ),
            "email and a@example.com",
        )

    def test_snippet_replacement_is_literal(self):
        self.assertEqual(apply_local("path", [("path", r"C:\work\1")]), r"C:\work\1")


class LifecycleTests(unittest.TestCase):
    def test_recording_cannot_start_inside_recents(self):
        app = dictate.App.__new__(dictate.App)
        app.lock = threading.Lock()
        app.state = dictate.IDLE
        app.recents_open = True
        app.recorder = Mock()
        app.on_press(None)
        app.recorder.start.assert_not_called()
        self.assertEqual(app.state, dictate.IDLE)

    def test_reload_and_quit_during_work_do_not_mutate_runtime(self):
        for state in (dictate.RECORDING, dictate.PROCESSING):
            for action in ("reload_config", "quit"):
                app = dictate.App.__new__(dictate.App)
                app.lock = threading.Lock()
                app.state = state
                app.notify = Mock()
                with patch("dictate.settings.load") as load:
                    getattr(app, action)()
                self.assertEqual(app.state, state)
                load.assert_not_called()
                app.notify.assert_called_once()

    def test_invalid_reload_preserves_old_config(self):
        app = dictate.App.__new__(dictate.App)
        app.lock = threading.Lock()
        app.state = dictate.IDLE
        app.cfg = {"old": True}
        with patch("dictate.settings.load", side_effect=ValueError("bad config")):
            with self.assertRaises(ValueError):
                app.reload_config()
        self.assertEqual(app.cfg, {"old": True})

    def test_two_keys_required_without_global_hook(self):
        first, second = "left ctrl", "left windows"
        for held in (
            set(),
            {hotkeys.KEYS[first]},
            {hotkeys.KEYS[second]},
            {hotkeys.KEYS[first], hotkeys.KEYS[second]},
        ):
            with patch.object(
                hotkeys._user32,
                "GetAsyncKeyState",
                side_effect=lambda key, held=held: 0x8000 if key in held else 0,
            ):
                self.assertEqual(hotkeys.is_pressed(first, second), len(held) == 2)


if __name__ == "__main__":
    unittest.main()
