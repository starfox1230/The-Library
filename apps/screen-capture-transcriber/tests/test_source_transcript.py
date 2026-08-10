from __future__ import annotations

import json

from screen_capture_transcriber.models import CaptureRegion, SessionManifest
from screen_capture_transcriber.source_transcript import apply_source_transcript


def test_medality_cues_become_saved_default_transcript(tmp_path) -> None:
    session = SessionManifest.create(
        tmp_path,
        "ACL anatomy",
        CaptureRegion(0, 0, 640, 360),
        "Demo output",
        1,
        0,
        0,
    )
    session.source_url = "https://medality.com/course/example/"

    markdown = apply_source_transcript(
        session,
        {
            "cues": [
                {"timestamp": "0:01", "seconds": 1, "text": "Knee anatomy."},
                {"timestamp": "0:03", "seconds": 3, "text": "Cruciates."},
            ]
        },
    )

    assert session.transcript_source == "medality"
    assert "**[00:01]** Knee anatomy." in markdown
    assert session.transcript_markdown_path.read_text(encoding="utf-8") == markdown
    payload = json.loads(session.transcript_json_path.read_text(encoding="utf-8"))
    assert payload["source"] == "Medality built-in transcript"
    assert payload["cues"][1]["text"] == "Cruciates."


def test_youtube_cues_are_saved_as_the_youtube_source(tmp_path) -> None:
    session = SessionManifest.create(
        tmp_path,
        "Knee MRI",
        CaptureRegion(0, 0, 640, 360),
        "Demo output",
        1,
        0,
        0,
    )
    session.source_url = "https://www.youtube.com/watch?v=abc"

    markdown = apply_source_transcript(
        session,
        {
            "provider": "YouTube built-in transcript",
            "cues": [
                {"timestamp": "0:05", "seconds": 5, "text": "The MCL is shown."}
            ],
        },
    )

    assert session.transcript_source == "youtube"
    assert "YouTube built-in transcript" in markdown
    payload = json.loads(
        session.transcript_json_path.read_text(encoding="utf-8")
    )
    assert payload["source"] == "YouTube built-in transcript"
