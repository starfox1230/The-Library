from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import CoverageGap, SourceMediaSpan


@dataclass(frozen=True)
class TimelinePiece:
    source_span_index: int
    segment_index: int
    source_start_seconds: float
    source_end_seconds: float
    recording_start_seconds: float
    recording_end_seconds: float
    playback_rate: float
    output_start_seconds: float = 0.0

    @property
    def output_duration_seconds(self) -> float:
        return max(0.0, self.recording_end_seconds - self.recording_start_seconds)


@dataclass(frozen=True)
class CoveragePlan:
    pieces: tuple[TimelinePiece, ...]
    gaps: tuple[CoverageGap, ...]
    source_duration_seconds: float
    covered_source_seconds: float
    output_duration_seconds: float

    @property
    def coverage_percent(self) -> float:
        if self.source_duration_seconds <= 0:
            return 0.0
        return min(
            100.0,
            100.0 * self.covered_source_seconds / self.source_duration_seconds,
        )


def _usable_spans(spans: Iterable[SourceMediaSpan]) -> list[SourceMediaSpan]:
    return [
        span
        for span in spans
        if span.source_end_seconds - span.source_start_seconds > 0.025
        and span.recording_end_seconds - span.recording_start_seconds > 0.025
    ]


def build_latest_take_plan(
    spans: Iterable[SourceMediaSpan],
    source_duration_seconds: float,
) -> CoveragePlan:
    usable = _usable_spans(spans)
    duration = max(
        0.0,
        source_duration_seconds,
        max((span.source_end_seconds for span in usable), default=0.0),
    )
    boundaries = {0.0, duration}
    for span in usable:
        boundaries.add(max(0.0, min(duration, span.source_start_seconds)))
        boundaries.add(max(0.0, min(duration, span.source_end_seconds)))
    ordered = sorted(boundaries)

    pieces: list[TimelinePiece] = []
    gaps: list[CoverageGap] = []
    for start, end in zip(ordered, ordered[1:]):
        if end - start <= 0.001:
            continue
        candidates = [
            span
            for span in usable
            if span.source_start_seconds <= start + 0.001
            and span.source_end_seconds >= end - 0.001
        ]
        if not candidates:
            if gaps and abs(gaps[-1].end_seconds - start) <= 0.002:
                gaps[-1].end_seconds = end
            else:
                gaps.append(CoverageGap(start_seconds=start, end_seconds=end))
            continue
        selected = max(candidates, key=lambda span: span.index)
        source_length = (
            selected.source_end_seconds - selected.source_start_seconds
        )
        recording_length = (
            selected.recording_end_seconds - selected.recording_start_seconds
        )
        ratio = recording_length / source_length
        recording_start = selected.recording_start_seconds + (
            start - selected.source_start_seconds
        ) * ratio
        recording_end = selected.recording_start_seconds + (
            end - selected.source_start_seconds
        ) * ratio
        piece = TimelinePiece(
            source_span_index=selected.index,
            segment_index=selected.segment_index,
            source_start_seconds=start,
            source_end_seconds=end,
            recording_start_seconds=recording_start,
            recording_end_seconds=recording_end,
            playback_rate=selected.playback_rate,
        )
        if pieces and _can_merge(pieces[-1], piece):
            previous = pieces.pop()
            piece = TimelinePiece(
                source_span_index=previous.source_span_index,
                segment_index=previous.segment_index,
                source_start_seconds=previous.source_start_seconds,
                source_end_seconds=piece.source_end_seconds,
                recording_start_seconds=previous.recording_start_seconds,
                recording_end_seconds=piece.recording_end_seconds,
                playback_rate=piece.playback_rate,
            )
        pieces.append(piece)

    output_cursor = 0.0
    positioned: list[TimelinePiece] = []
    for piece in pieces:
        positioned.append(
            TimelinePiece(
                **{
                    **piece.__dict__,
                    "output_start_seconds": output_cursor,
                }
            )
        )
        output_cursor += piece.output_duration_seconds
    covered = sum(
        piece.source_end_seconds - piece.source_start_seconds
        for piece in positioned
    )
    return CoveragePlan(
        pieces=tuple(positioned),
        gaps=tuple(gaps),
        source_duration_seconds=duration,
        covered_source_seconds=covered,
        output_duration_seconds=output_cursor,
    )


def output_time_for_source(
    plan: CoveragePlan,
    source_seconds: float,
) -> float | None:
    for piece in plan.pieces:
        if (
            piece.source_start_seconds - 0.001
            <= source_seconds
            <= piece.source_end_seconds + 0.001
        ):
            source_length = piece.source_end_seconds - piece.source_start_seconds
            if source_length <= 0:
                return piece.output_start_seconds
            fraction = min(
                1.0,
                max(
                    0.0,
                    (source_seconds - piece.source_start_seconds) / source_length,
                ),
            )
            return piece.output_start_seconds + (
                piece.output_duration_seconds * fraction
            )
    return None


def _can_merge(left: TimelinePiece, right: TimelinePiece) -> bool:
    return (
        left.source_span_index == right.source_span_index
        and left.segment_index == right.segment_index
        and abs(left.source_end_seconds - right.source_start_seconds) <= 0.002
        and abs(left.recording_end_seconds - right.recording_start_seconds) <= 0.02
    )

