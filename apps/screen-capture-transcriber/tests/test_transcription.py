from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from screen_capture_transcriber.models import CaptureRegion, SessionManifest
from screen_capture_transcriber.transcription import (
    SessionTranscriber,
    actual_cost,
    estimate_cost,
    merge_overlapping_text,
    recover_completed_transcript,
)


def test_merge_overlapping_text_removes_repeated_overlap() -> None:
    previous = "The quick brown fox jumps over the lazy dog and keeps running"
    current = "over the lazy dog and keeps running toward the distant hill"
    merged = merge_overlapping_text(previous, current)
    assert merged == (
        "The quick brown fox jumps over the lazy dog and keeps running "
        "toward the distant hill"
    )


def test_estimate_cost_uses_duration() -> None:
    assert estimate_cost("gpt-4o-mini-transcribe", 3600) == pytest.approx(0.18)
    assert estimate_cost("whisper-1", 3600) == pytest.approx(0.36)


def test_actual_token_cost() -> None:
    cost = actual_cost(
        "gpt-4o-mini-transcribe",
        {"input_tokens": 10_000, "output_tokens": 1_000},
    )
    assert cost == pytest.approx(0.0175)


def test_whisper_duration_cost() -> None:
    assert actual_cost("whisper-1", {"seconds": 600}) == pytest.approx(0.06)


def test_single_chapter_transcription_creates_its_work_directory(
    tmp_path,
    monkeypatch,
) -> None:
    session = SessionManifest.create(
        tmp_path,
        "Knee anatomy",
        CaptureRegion(0, 0, 640, 360),
        "Loopback",
        1,
        1.0,
        1.1,
    )
    session.duration_seconds = 10.0
    session.transcription_model = "gpt-4o-mini-transcribe"
    session.audio_path.write_bytes(b"small audio placeholder")
    transcriber = SessionTranscriber(
        "test-key",
        "gpt-4o-mini-transcribe",
        Path("ffmpeg"),
        Path("ffprobe"),
        48,
    )
    monkeypatch.setattr(
        transcriber,
        "_transcribe_file",
        lambda _path, _context: SimpleNamespace(
            text="The anterior cruciate ligament is fan-shaped distally.",
            usage={"input_tokens": 100, "output_tokens": 20},
        ),
    )

    result = transcriber.transcribe(session)

    chapter_dir = session.folder / "transcription" / "chapter-001"
    assert "anterior cruciate ligament" in result.markdown
    assert (chapter_dir / "response-001.txt").is_file()
    assert (chapter_dir / "transcript.txt").is_file()
    assert session.transcript_markdown_path.is_file()
    assert session.transcript_json_path.is_file()


def test_recover_completed_transcript_avoids_a_second_api_request(tmp_path) -> None:
    session = SessionManifest.create(
        tmp_path,
        "Recovered anatomy",
        CaptureRegion(0, 0, 640, 360),
        "Loopback",
        1,
        1.0,
        1.1,
    )
    session.duration_seconds = 20
    session.transcription_model = "gpt-4o-mini-transcribe"
    session.chapters[0].transcript = "Already returned by the API."

    result = recover_completed_transcript(session)

    assert result is not None
    assert "Already returned by the API." in session.transcript_markdown_path.read_text(
        encoding="utf-8"
    )
    assert session.state == "transcribed"
