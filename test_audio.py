import unittest
from unittest.mock import MagicMock, call, patch

import audio
from audio import Recorder


class RecorderDeviceTests(unittest.TestCase):
    def test_preferred_input_matches_by_partial_name(self):
        devices = [
            {"name": "Camera microphone", "max_input_channels": 2},
            {"name": "Microphone (USB voice mic)", "max_input_channels": 1},
            {"name": "Speakers", "max_input_channels": 0},
        ]
        with patch("audio.sd.query_devices", return_value=devices):
            self.assertEqual(Recorder._resolve_preferred_device("USB voice mic"), 1)

    def test_candidates_prefer_named_input_then_default_then_other_inputs(self):
        devices = [
            {"name": "Built-in Microphone", "max_input_channels": 2},
            {"name": "USB voice mic", "max_input_channels": 1},
            {"name": "Speakers", "max_input_channels": 0},
            {"name": "USB voice mic", "max_input_channels": 1},
            {"name": "Line input", "max_input_channels": 1},
        ]
        with (
            patch("audio.sd.query_devices", return_value=devices),
            patch.object(audio.sd.default, "device", [0, 2]),
        ):
            self.assertEqual(Recorder._candidate_devices("USB voice mic"), [1, 3, 0, 4])

    def test_start_refreshes_audio_and_retries_until_frames_arrive(self):
        recorder = Recorder.__new__(Recorder)
        recorder.preferred_device = "USB voice mic"
        recorder.device = 99
        recorder._frames = []
        recorder._stream = None
        recorder._first_frame = MagicMock()
        devices = [
            {"name": "Unused", "max_input_channels": 0},
            {"name": "Mic 1", "max_input_channels": 1},
            {"name": "Mic 2", "max_input_channels": 1},
        ]

        def query_devices(device=None):
            return devices if device is None else devices[device]

        with (
            patch.object(recorder, "_refresh_portaudio") as refresh,
            patch.object(recorder, "_candidate_devices", return_value=[1, 2]),
            patch.object(recorder, "_open_candidate", side_effect=[False, True]) as open_candidate,
            patch.object(recorder, "_close_stream") as close_stream,
            patch("audio.sd.query_devices", side_effect=query_devices),
        ):
            recorder.start()

        refresh.assert_called_once_with()
        self.assertEqual(open_candidate.call_args_list, [call(1), call(2)])
        close_stream.assert_called_once_with()
        self.assertEqual(recorder.device, 2)

    def test_empty_microphone_stream_is_reported(self):
        recorder = Recorder()
        with self.assertRaisesRegex(RuntimeError, "returned no audio"):
            recorder.stop()


if __name__ == "__main__":
    unittest.main()
