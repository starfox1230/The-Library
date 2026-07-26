from __future__ import annotations

import json

from screen_capture_transcriber.models import (
    CaptureRegion,
    SessionManifest,
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
    )

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
