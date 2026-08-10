from __future__ import annotations

import json

from screen_capture_transcriber.models import (
    CaptureRegion,
    SessionManifest,
    SourceMediaSpan,
    format_duration,
    safe_slug,
)


def test_format_duration_handles_minutes_and_hours() -> None:
    assert format_duration(65) == "01:05"
    assert format_duration(3661) == "01:01:01"


def test_safe_slug_removes_path_characters() -> None:
    assert safe_slug(" CT / MRI: intro? ") == "CT-MRI-intro"


def test_session_manifest_persists_chapters(tmp_path) -> None:
    session = SessionManifest.create(
        tmp_path,
        "Demo lecture",
        CaptureRegion(10, 20, 800, 600, "DISPLAY1"),
        "Demo output",
        7,
        100.0,
        100.2,
    )
    session.add_chapter(12.5, "Second topic")

    payload = json.loads(session.manifest_path.read_text(encoding="utf-8"))
    assert payload["title"] == "Demo lecture"
    assert payload["region"]["width"] == 800
    assert payload["chapters"][1]["title"] == "Second topic"
    assert payload["chapters"][1]["start_seconds"] == 12.5


def test_session_manifest_persists_segments_and_anatomy_captures(tmp_path) -> None:
    session = SessionManifest.create(
        tmp_path,
        "Anatomy lecture",
        CaptureRegion(0, 0, 1280, 720),
        "HDMI loopback",
        4,
        10.0,
        10.2,
    )
    segment = session.begin_segment(10.0, 10.2)
    segment.duration_seconds = 42.5
    segment.state = "ready"
    original = session.anatomy_original_path(1)
    annotated = session.anatomy_annotated_path(1)
    edit = session.anatomy_edit_path(1)
    original.write_bytes(b"original")
    annotated.write_bytes(b"annotated")
    edit.write_text("{}", encoding="utf-8")
    session.add_anatomy_capture(
        42.5,
        original,
        annotated,
        "Median nerve",
        True,
        (100, 200),
        edit,
        37.25,
    )
    session.video_link_mode = "linked"
    session.source_duration_seconds = 90
    session.source_spans.append(
        SourceMediaSpan(
            index=1,
            segment_index=1,
            source_start_seconds=0,
            source_end_seconds=42,
            recording_start_seconds=0.2,
            recording_end_seconds=21.2,
            playback_rate=2,
        )
    )
    session.save()

    payload = json.loads(session.manifest_path.read_text(encoding="utf-8"))
    assert payload["segments"][0]["recording_file"] == "segments\\segment-001.mkv"
    assert payload["anatomy_captures"][0]["label"] == "Median nerve"
    assert payload["anatomy_captures"][0]["source_click_x"] == 100
    assert payload["anatomy_captures"][0]["edit_file"].endswith(
        "capture-001-edit.json"
    )

    loaded = SessionManifest.load(session.manifest_path)
    assert loaded.segments[0].duration_seconds == 42.5
    assert loaded.anatomy_captures[0].label == "Median nerve"
    assert loaded.anatomy_captures[0].source_timestamp_seconds == 37.25
    assert loaded.source_spans[0].playback_rate == 2


def test_learning_notes_keep_stable_ids_and_source_timestamps(tmp_path) -> None:
    session = SessionManifest.create(
        tmp_path,
        "Concept lecture",
        CaptureRegion(0, 0, 1280, 720),
        "Loopback",
        1,
        10.0,
        10.1,
    )

    note = session.add_learning_note(
        12.5,
        "  The ACL primarily restrains anterior tibial translation.  ",
        25.0,
    )
    original_id = note.id
    session.update_learning_note(
        original_id,
        "The ACL is the primary restraint to anterior tibial translation.",
    )

    loaded = SessionManifest.load(session.manifest_path)

    assert len(loaded.learning_notes) == 1
    assert loaded.learning_notes[0].id == original_id
    assert loaded.learning_notes[0].timestamp_seconds == 12.5
    assert loaded.learning_notes[0].source_timestamp_seconds == 25.0
    assert "primary restraint" in loaded.learning_notes[0].text

    assert loaded.delete_learning_note(original_id) is True
    assert loaded.delete_learning_note(original_id) is False
    assert SessionManifest.load(loaded.manifest_path).learning_notes == []
