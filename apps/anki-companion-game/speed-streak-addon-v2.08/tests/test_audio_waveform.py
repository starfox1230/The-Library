from __future__ import annotations

import importlib.util
import math
import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path


ADDON_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "speed_streak_audio_waveform_test", ADDON_ROOT / "audio_waveform.py"
)
assert SPEC and SPEC.loader
WAVEFORM = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = WAVEFORM
SPEC.loader.exec_module(WAVEFORM)


class AudioWaveformTests(unittest.TestCase):
    def test_pcm_wav_produces_normalized_first_second_peaks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tick.wav"
            sample_rate = 8000
            with wave.open(str(path), "wb") as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(sample_rate)
                samples = [
                    int(24000 * math.sin((index / sample_rate) * math.tau * 440))
                    for index in range(sample_rate * 2)
                ]
                audio.writeframes(b"".join(struct.pack("<h", sample) for sample in samples))

            result = WAVEFORM.load_audio_waveform(path, visible_ms=1000, point_count=100)

        self.assertTrue(result.available)
        self.assertEqual(result.duration_ms, 2000)
        self.assertEqual(result.visible_ms, 1000)
        self.assertGreaterEqual(len(result.peaks), 90)
        self.assertAlmostEqual(max(result.peaks), 1.0)

    def test_non_wav_keeps_timing_preview_available_without_fake_waveform(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cue.mp3"
            path.write_bytes(b"not needed for this format check")
            result = WAVEFORM.load_audio_waveform(path)

        self.assertFalse(result.available)
        self.assertEqual(result.peaks, ())
        self.assertIn("Timing preview still works", result.message)

    def test_extensible_pcm_wav_works_on_python_builds_that_reject_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "extensible.wav"
            sample_rate = 8000
            samples = b"".join(
                struct.pack("<h", int(16000 * math.sin((index / sample_rate) * math.tau * 220)))
                for index in range(sample_rate)
            )
            pcm_guid = bytes.fromhex("0100000000001000800000aa00389b71")
            fmt = struct.pack(
                "<HHIIHHHHI16s",
                0xFFFE,
                1,
                sample_rate,
                sample_rate * 2,
                2,
                16,
                22,
                16,
                0,
                pcm_guid,
            )
            riff_size = 4 + 8 + len(fmt) + 8 + len(samples)
            path.write_bytes(
                b"RIFF"
                + struct.pack("<I", riff_size)
                + b"WAVEfmt "
                + struct.pack("<I", len(fmt))
                + fmt
                + b"data"
                + struct.pack("<I", len(samples))
                + samples
            )
            result = WAVEFORM.load_audio_waveform(path, point_count=80)

        self.assertTrue(result.available)
        self.assertEqual(result.duration_ms, 1000)
        self.assertAlmostEqual(max(result.peaks), 1.0)


if __name__ == "__main__":
    unittest.main()
