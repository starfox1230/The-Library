from __future__ import annotations

from types import SimpleNamespace

from screen_capture_transcriber.anatomy_suggestions import (
    suggest_anatomy_terms,
    transcript_window,
)
from screen_capture_transcriber.models import TranscriptCue


class _FakeResponses:
    def __init__(self, output_text: str) -> None:
        self.output_text = output_text
        self.requests: list[dict[str, object]] = []

    def create(self, **request):
        self.requests.append(request)
        return SimpleNamespace(output_text=self.output_text)


def test_transcript_window_uses_fifteen_seconds_on_each_side() -> None:
    cues = [
        TranscriptCue("00:15", 15.0, "before"),
        TranscriptCue("00:30", 30.0, "capture"),
        TranscriptCue("00:45", 45.0, "after"),
        TranscriptCue("00:46", 45.1, "outside"),
    ]
    assert [cue.text for cue in transcript_window(cues, 30.0)] == [
        "before",
        "capture",
        "after",
    ]


def test_suggestions_are_mapped_to_cues_deduplicated_and_time_ranked() -> None:
    cues = [
        TranscriptCue("00:25", 25.0, "The radial nerve is here."),
        TranscriptCue("00:31", 31.0, "Now the brachial artery."),
        TranscriptCue("00:38", 38.0, "Back to the radial nerve."),
    ]
    responses = _FakeResponses(
        """
        {"terms":[
          {"term":"radial nerve","cue_index":2},
          {"term":"brachial artery","cue_index":1},
          {"term":"Radial nerve","cue_index":0}
        ]}
        """
    )
    client = SimpleNamespace(responses=responses)

    terms = suggest_anatomy_terms(
        "test-key",
        "gpt-5.6-luna",
        cues,
        30.0,
        client=client,
    )

    assert [(term.term, term.timestamp_seconds) for term in terms] == [
        ("brachial artery", 31.0),
        ("Radial nerve", 25.0),
    ]
    assert responses.requests[0]["reasoning"] == {"effort": "none"}
    assert responses.requests[0]["model"] == "gpt-5.6-luna"


def test_suggestions_skip_api_when_key_or_transcript_is_unavailable() -> None:
    client = SimpleNamespace(responses=_FakeResponses('{"terms":[]}'))
    cue = TranscriptCue("00:10", 10.0, "Median nerve")

    assert suggest_anatomy_terms("", "gpt-5.6-luna", [cue], 10, client=client) == []
    assert suggest_anatomy_terms("key", "gpt-5.6-luna", [], 10, client=client) == []
    assert client.responses.requests == []
