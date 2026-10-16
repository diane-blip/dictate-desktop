"""Failure regressions for bounded capture, recovery, menus and SDK cleanup."""

import io
import threading
import unittest
import wave
from unittest.mock import Mock, patch

import anthropic
import httpx2
import numpy as np

import audio
import cleanup
import dictate
import insert


class CaptureTests(unittest.TestCase):
    def test_backlog_is_bounded_and_partial_capture_is_recoverable(self):
        recorder = audio.Recorder()
        with patch.object(audio, "MAX_SAMPLES", 5):
            recorder._on_audio(np.zeros((4, 1), dtype=np.int16), 4, None, False)
            recorder._on_audio(np.zeros((4, 1), dtype=np.int16), 4, None, False)
            recorder._on_audio(np.zeros((4, 1), dtype=np.int16), 4, None, False)
        self.assertEqual(sum(len(x) for x in recorder._frames), 5)
        with self.assertRaises(audio.RecordingError) as caught:
            recorder.stop()
        with wave.open(io.BytesIO(caught.exception.wav_bytes)) as wav:
            self.assertEqual(wav.getnframes(), 5)
        self.assertEqual(recorder._frames, [])

    def test_dropped_audio_never_goes_to_transcription(self):
        app = dictate.App.__new__(dictate.App)
        app.lock = threading.Lock()
        app.state = dictate.RECORDING
        app.icon = Mock()
        app.recorder = Mock()
        app.recorder.stop.side_effect = audio.RecordingError("dropped", b"recovery")
        app._salvage_audio = Mock(return_value="saved.wav")
        app.notify = Mock()
        with patch("dictate.transcribe") as transcribe:
            app.on_release(None)
        app._salvage_audio.assert_called_once_with(b"recovery")
        transcribe.assert_not_called()
        self.assertEqual(app.state, dictate.IDLE)

    def test_stream_close_runs_when_stop_raises(self):
        recorder = audio.Recorder()
        stream = Mock()
        stream.stop.side_effect = OSError("device removed")
        recorder._stream = stream
        recorder._on_audio(np.zeros((16, 1), dtype=np.int16), 16, None, False)
        with self.assertRaises(audio.RecordingError):
            recorder.stop()
        stream.close.assert_called_once()
        self.assertIsNone(recorder._stream)


class GuardTests(unittest.TestCase):
    def test_menu_blocks_input_before_any_character(self):
        with (
            patch.object(insert._user32, "GetForegroundWindow", return_value=123),
            patch.object(insert._user32, "GetAsyncKeyState", return_value=0),
            patch.object(insert, "_menu_active", return_value=True),
            patch.object(insert, "_send_units") as send,
        ):
            with self.assertRaisesRegex(RuntimeError, "menu"):
                insert.insert_text("recover me", target=123)
            send.assert_not_called()

    def test_unavailable_menu_state_fails_closed(self):
        with patch.object(insert._user32, "GetGUIThreadInfo", return_value=0):
            with self.assertRaisesRegex(RuntimeError, "Cannot verify"):
                insert._menu_active()


class SDKTests(unittest.TestCase):
    def test_real_sdk_uses_mock_transport_and_closes_it(self):
        text = "I want these exact words."
        requests = []

        def respond(request):
            requests.append(request)
            return httpx2.Response(
                200,
                json={
                    "id": "msg_fixture",
                    "type": "message",
                    "role": "assistant",
                    "model": "claude-haiku-5-5",
                    "stop_reason": "end_turn",
                    "content": [{"type": "text", "text": text}],
                    "usage": {"input_tokens": 12, "output_tokens": 8},
                },
            )

        transport = anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(respond))
        cfg = {"cleanup": {"enabled": True, "model": "claude-haiku-5-5", "timeout_seconds": 5}}
        with (
            patch("cleanup.api_key", return_value="fictional-test-key"),
            patch("cleanup.anthropic.DefaultHttpxClient", return_value=transport),
        ):
            self.assertEqual(cleanup.clean(text, [], cfg), text)
        self.assertEqual(len(requests), 1)
        self.assertTrue(transport.is_closed)

    def test_constructor_failure_also_closes_transport(self):
        transport = anthropic.DefaultHttpxClient()
        cfg = {"cleanup": {"enabled": True, "model": "fixture", "timeout_seconds": 5}}
        with (
            patch("cleanup.api_key", return_value="fictional-test-key"),
            patch("cleanup.anthropic.DefaultHttpxClient", return_value=transport),
            patch("cleanup.anthropic.Anthropic", side_effect=RuntimeError),
        ):
            self.assertEqual(
                cleanup.clean("Keep these original words", [], cfg), "Keep these original words"
            )
        self.assertTrue(transport.is_closed)
