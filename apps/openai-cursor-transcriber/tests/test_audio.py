from __future__ import annotations

import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from cursor_transcriber.audio import MicrophoneRecorder


class FakeStream:
    def __init__(self, **kwargs):
        self.active = False
        self.callback = kwargs["callback"]

    def start(self):
        self.active = True

    def stop(self):
        self.active = False

    def close(self):
        self.active = False


class AudioTests(unittest.TestCase):
    def capture(self, samples: bytes, *, interrupted: bool = False):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        with patch("cursor_transcriber.audio._input_candidates", return_value=[("test", {})]), \
             patch("cursor_transcriber.audio.sounddevice.RawInputStream", FakeStream), \
             patch("cursor_transcriber.audio.perf_counter", side_effect=[10.0, 12.0]):
            recorder = MicrophoneRecorder(Path(directory.name), 16000, 1)
            recorder.start()
            recorder._stream.callback(samples, len(samples) // 2, None, None)
            if interrupted:
                recorder._stream.active = False
                self.assertFalse(recorder.has_received_audio())
            return recorder.stop()

    def test_full_capture_preserves_pcm_and_wav_metadata(self):
        pcm = b"\x01\x00" * 32000
        result = self.capture(pcm)
        self.assertIsNone(result.capture_error)
        with wave.open(str(result.path), "rb") as recording:
            self.assertEqual((recording.getnchannels(), recording.getsampwidth(), recording.getframerate()), (1, 2, 16000))
            self.assertEqual(recording.getnframes(), 32000)
            self.assertEqual(recording.readframes(32000), pcm)

    def test_initial_silent_chunk_from_stopped_driver_is_rejected(self):
        result = self.capture(b"\x00\x00" * 416, interrupted=True)
        self.assertIn("stopped unexpectedly", result.capture_error)

    def test_stalled_capture_is_rejected_even_if_stream_reports_active(self):
        result = self.capture(b"\x01\x00" * 416)
        self.assertIn("stopped unexpectedly", result.capture_error)

    def test_full_length_digital_silence_is_rejected(self):
        result = self.capture(b"\x00\x00" * 32000)
        self.assertIn("No microphone signal", result.capture_error)


if __name__ == "__main__":
    unittest.main()
