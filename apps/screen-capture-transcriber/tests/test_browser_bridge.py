from __future__ import annotations

from screen_capture_transcriber.browser_bridge import (
    BrowserBridge,
    browser_source_title,
)


def test_bridge_tracks_player_and_delivers_commands_once() -> None:
    bridge = BrowserBridge()
    bridge.set_app_state(
        linked_session_active=True,
        recorder_state="paused",
    )
    command_id = bridge.enqueue_command("play")
    bridge._receive_payload(
        {
            "event": "heartbeat",
            "top_url": "https://medality.com/course/example/",
            "top_title": "Example lesson",
            "player": {
                "provider": "Medality / Vimeo",
                "current_time": 12.5,
                "duration": 120.0,
                "paused": True,
            },
        },
        heartbeat=True,
    )

    player = bridge.current_player()
    first_poll = bridge._poll_response()
    second_poll = bridge._poll_response()

    assert player is not None
    assert player["provider"] == "Medality / Vimeo"
    assert player["top_url"].startswith("https://medality.com/")
    assert first_poll["commands"] == [{"id": command_id, "action": "play"}]
    assert first_poll["app_state"]["recorder_state"] == "paused"
    assert second_poll["commands"] == []
    assert first_poll["bridge_instance_id"] == second_poll["bridge_instance_id"]


def test_new_bridge_process_has_a_new_transcript_handshake_id() -> None:
    first = BrowserBridge()._page_poll_response()
    second = BrowserBridge()._page_poll_response()

    assert first["bridge_instance_id"]
    assert first["bridge_instance_id"] != second["bridge_instance_id"]


def test_bridge_accepts_structured_source_transcript() -> None:
    bridge = BrowserBridge()
    received: list[object] = []
    bridge.transcript_received.connect(received.append)

    bridge._receive_transcript(
        {
            "event": "source_transcript",
            "top_url": "https://medality.com/course/example/",
            "transcript": {
                "provider": "Medality built-in transcript",
                "cues": [
                    {"timestamp": "0:01", "seconds": 1, "text": "Knee anatomy."}
                ],
            },
        }
    )

    transcript = bridge.current_transcript()
    assert transcript is not None
    assert transcript["cues"][0]["text"] == "Knee anatomy."
    assert received


def test_top_page_learning_note_intent_reuses_recent_iframe_player() -> None:
    bridge = BrowserBridge()
    received: list[object] = []
    bridge.player_event.connect(received.append)
    bridge._receive_payload(
        {
            "event": "heartbeat",
            "top_url": "https://medality.com/course/example/",
            "player": {
                "provider": "Medality / Vimeo",
                "current_time": 82.25,
                "duration": 120.0,
                "paused": False,
            },
        },
        heartbeat=True,
    )

    bridge._receive_payload(
        {
            "event": "learning_note_intent",
            "reason": "backspace",
            "top_url": "https://medality.com/course/example/",
        },
        heartbeat=False,
    )

    assert received[-1]["event"] == "learning_note_intent"
    assert received[-1]["current_time"] == 82.25


def test_browser_source_title_prefers_matching_medality_lesson_title() -> None:
    player = {
        "top_url": "https://medality.com/course/example/",
        "top_title": "MRI Online | Medality",
        "frame_title": "Vimeo Player",
    }
    transcript = {
        "url": "https://medality.com/course/example/",
        "title": "  Anatomy of the Brachial Plexus  ",
    }

    assert (
        browser_source_title(player, transcript)
        == "Anatomy of the Brachial Plexus"
    )


def test_browser_source_title_ignores_transcript_from_another_lesson() -> None:
    player = {
        "top_url": "https://medality.com/course/current/",
        "top_title": "Current MRI lesson",
    }
    transcript = {
        "url": "https://medality.com/course/previous/",
        "title": "Previous MRI lesson",
    }

    assert browser_source_title(player, transcript) == "Current MRI lesson"


def test_selected_tab_owns_commands_events_and_transcript() -> None:
    bridge = BrowserBridge()
    received_players: list[object] = []
    received_transcripts: list[object] = []
    bridge.player_event.connect(received_players.append)
    bridge.transcript_received.connect(received_transcripts.append)

    for tab_id, provider, url, paused in (
        (11, "Medality / Vimeo", "https://medality.com/course/mcl/", True),
        (22, "YouTube", "https://www.youtube.com/watch?v=abc", False),
    ):
        bridge._receive_payload(
            {
                "event": "heartbeat",
                "tab_id": tab_id,
                "top_url": url,
                "top_title": provider,
                "player": {
                    "provider": provider,
                    "paused": paused,
                    "current_time": 10,
                    "duration": 100,
                },
            },
            heartbeat=True,
        )

    bridge.select_source(22)
    command_id = bridge.enqueue_command("pause")
    medality_poll = bridge._poll_response({"tab_id": 11})
    youtube_poll = bridge._poll_response({"tab_id": 22})

    assert medality_poll["commands"] == []
    assert medality_poll["app_state"]["source_selected"] is False
    assert youtube_poll["commands"] == [
        {"id": command_id, "action": "pause"}
    ]
    assert youtube_poll["app_state"]["source_selected"] is True

    bridge._receive_transcript(
        {
            "tab_id": 11,
            "top_url": "https://medality.com/course/mcl/",
            "transcript": {
                "provider": "Medality built-in transcript",
                "cues": [{"timestamp": "0:01", "seconds": 1, "text": "Wrong tab"}],
            },
        }
    )
    assert bridge.current_transcript() is None

    bridge._receive_transcript(
        {
            "tab_id": 22,
            "top_url": "https://www.youtube.com/watch?v=abc",
            "transcript": {
                "provider": "YouTube built-in transcript",
                "cues": [{"timestamp": "0:02", "seconds": 2, "text": "Right tab"}],
            },
        }
    )
    assert bridge.current_transcript()["cues"][0]["text"] == "Right tab"
    assert received_transcripts[-1]["tab_id"] == 22


def test_navigating_selected_tab_discards_its_previous_video_transcript() -> None:
    bridge = BrowserBridge()
    bridge._receive_payload(
        {
            "event": "heartbeat",
            "tab_id": 22,
            "top_url": "https://www.youtube.com/watch?v=first",
            "player": {"provider": "YouTube", "paused": True},
        },
        heartbeat=True,
    )
    bridge.select_source(22)
    bridge._receive_transcript(
        {
            "tab_id": 22,
            "top_url": "https://www.youtube.com/watch?v=first",
            "transcript": {
                "provider": "YouTube built-in transcript",
                "cues": [{"timestamp": "0:01", "seconds": 1, "text": "First video"}],
            },
        }
    )
    assert bridge.current_transcript() is not None

    bridge._receive_payload(
        {
            "event": "player_detected",
            "tab_id": 22,
            "top_url": "https://www.youtube.com/watch?v=second",
            "player": {"provider": "YouTube", "paused": True},
        },
        heartbeat=False,
    )

    assert bridge.current_transcript() is None
