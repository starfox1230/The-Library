from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Optional


DEFAULT_COUNTDOWN_AUDIO_ENABLED = False
DEFAULT_COUNTDOWN_AUDIO_FILE = "countdown-cues/clock-tick-soft.wav"
DEFAULT_COUNTDOWN_WARNING_SECONDS = 3
DEFAULT_COUNTDOWN_AUDIO_ALIGNMENT_MS = 0
MIN_COUNTDOWN_WARNING_SECONDS = 1
MAX_COUNTDOWN_WARNING_SECONDS = 120
MAX_COUNTDOWN_AUDIO_ALIGNMENT_MS = 950
COUNTDOWN_LATE_TOLERANCE_MS = 80


def normalize_countdown_warning_seconds(value: object) -> int:
    try:
        parsed = int(round(float(value)))
    except (TypeError, ValueError):
        parsed = DEFAULT_COUNTDOWN_WARNING_SECONDS
    return max(MIN_COUNTDOWN_WARNING_SECONDS, min(MAX_COUNTDOWN_WARNING_SECONDS, parsed))


def normalize_countdown_alignment_ms(value: object) -> int:
    try:
        parsed = int(round(float(value)))
    except (TypeError, ValueError):
        parsed = DEFAULT_COUNTDOWN_AUDIO_ALIGNMENT_MS
    return max(0, min(MAX_COUNTDOWN_AUDIO_ALIGNMENT_MS, parsed))


@dataclass(frozen=True)
class CountdownCueSchedule:
    second: int
    delay_ms: int


def countdown_preview_cues(
    *, warning_seconds: object, alignment_ms: object
) -> tuple[CountdownCueSchedule, ...]:
    """Return cue launch times for a preview beginning one second early."""

    threshold = normalize_countdown_warning_seconds(warning_seconds)
    alignment = normalize_countdown_alignment_ms(alignment_ms)
    total_ms = (threshold + 1) * 1000
    return tuple(
        CountdownCueSchedule(
            second=second,
            delay_ms=max(0, total_ms - (second * 1000) - alignment),
        )
        for second in range(threshold, 0, -1)
    )


def next_countdown_cue(
    *,
    remaining_ms: int,
    warning_seconds: object,
    alignment_ms: object,
    fired_seconds: Collection[int] = (),
    late_tolerance_ms: int = COUNTDOWN_LATE_TOLERANCE_MS,
) -> Optional[CountdownCueSchedule]:
    """Return the next deadline-aligned cue, never the zero-second boundary.

    ``alignment_ms`` is the point inside the clip that should land on the
    integer boundary. For example, 120 starts playback 120 ms before the
    boundary so the sample at 120 ms is heard exactly on the mark.
    """

    remaining = max(0, int(remaining_ms or 0))
    if remaining <= 0:
        return None
    threshold = normalize_countdown_warning_seconds(warning_seconds)
    alignment = normalize_countdown_alignment_ms(alignment_ms)
    already_fired = {max(0, int(second)) for second in fired_seconds}
    tolerance = max(0, int(late_tolerance_ms or 0))

    for second in range(threshold, 0, -1):
        if second in already_fired:
            continue
        # Playback begins ``alignment`` milliseconds before this second mark.
        delay_ms = remaining - (second * 1000) - alignment
        if delay_ms < -tolerance:
            continue
        return CountdownCueSchedule(second=second, delay_ms=max(0, delay_ms))
    return None
