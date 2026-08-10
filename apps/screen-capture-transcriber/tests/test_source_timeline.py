from __future__ import annotations

from screen_capture_transcriber.models import SourceMediaSpan
from screen_capture_transcriber.source_timeline import (
    build_latest_take_plan,
    output_time_for_source,
)


def _span(
    index: int,
    source_start: float,
    source_end: float,
    recording_start: float,
    recording_end: float,
    segment: int = 1,
) -> SourceMediaSpan:
    return SourceMediaSpan(
        index=index,
        segment_index=segment,
        source_start_seconds=source_start,
        source_end_seconds=source_end,
        recording_start_seconds=recording_start,
        recording_end_seconds=recording_end,
        playback_rate=(
            (source_end - source_start) / (recording_end - recording_start)
        ),
    )


def test_latest_take_replaces_only_its_overlapping_source_interval() -> None:
    plan = build_latest_take_plan(
        [
            _span(1, 0, 120, 0, 60),
            _span(2, 90, 140, 0, 50, segment=2),
        ],
        180,
    )

    assert [
        (
            piece.source_span_index,
            piece.source_start_seconds,
            piece.source_end_seconds,
        )
        for piece in plan.pieces
    ] == [
        (1, 0.0, 90),
        (2, 90, 140),
    ]
    assert [(gap.start_seconds, gap.end_seconds) for gap in plan.gaps] == [
        (140, 180),
    ]
    assert round(plan.coverage_percent, 1) == 77.8
    assert plan.output_duration_seconds == 95


def test_source_timestamp_maps_to_clean_output_at_observed_speed() -> None:
    plan = build_latest_take_plan(
        [_span(1, 0, 100, 0, 50)],
        100,
    )

    assert output_time_for_source(plan, 40) == 20
    assert output_time_for_source(plan, 101) is None


def test_missing_middle_interval_is_reported() -> None:
    plan = build_latest_take_plan(
        [
            _span(1, 0, 10, 0, 10),
            _span(2, 20, 30, 0, 10, segment=2),
        ],
        30,
    )

    assert [(gap.start_seconds, gap.end_seconds) for gap in plan.gaps] == [
        (10, 20),
    ]

