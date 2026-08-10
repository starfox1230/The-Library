from __future__ import annotations

import struct

from screen_capture_transcriber.audio import pcm16_activity_level


def _pcm16(value: int, count: int = 100) -> bytes:
    return struct.pack(f"<{count}h", *([value] * count))


def test_audio_activity_meter_is_silent_for_zero_pcm() -> None:
    assert pcm16_activity_level(_pcm16(0)) == 0.0


def test_audio_activity_meter_makes_quiet_loopback_audio_visible() -> None:
    # Roughly -40 dBFS, representative of the user's recent recordings.
    level = pcm16_activity_level(_pcm16(328))

    assert 0.35 < level < 0.5


def test_audio_activity_meter_is_clamped_at_full_scale() -> None:
    assert pcm16_activity_level(_pcm16(32767)) == 1.0
