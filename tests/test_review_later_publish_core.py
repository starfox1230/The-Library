from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "apps" / "anki-pocket-knife" / "review_later_publish_core.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("review_later_publish_core", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _card(**updates: object) -> dict[str, object]:
    card: dict[str, object] = {
        "card_id": 123,
        "note_id": 456,
        "flagged_at": "2026-08-31T06:35:00-05:00",
        "last_seen_at": "2026-08-31T13:10:00-05:00",
        "deck": "Radiology::Chest",
        "note_type": "saCloze++",
        "tags": ["chest", "review-later"],
        "fields": {"Text": "Question", "Extra": "Answer"},
        "front_html": "<b>Question</b>",
        "back_html": "<b>Answer</b>",
        "front_text": "Question",
        "back_text": "Answer",
        "media": [],
    }
    card.update(updates)
    return card


def test_content_hash_ignores_export_time_but_changes_with_queue() -> None:
    module = _load_module()
    first = module.content_hash([_card()], "Prompt", source_addon="speed_streak_v2_04", review_later_flag=4)
    same = module.content_hash([_card()], "Prompt", source_addon="speed_streak_v2_04", review_later_flag=4)
    changed = module.content_hash(
        [_card(front_html="<b>Different</b>")],
        "Prompt",
        source_addon="speed_streak_v2_04",
        review_later_flag=4,
    )

    assert first == same
    assert first != changed


def test_markdown_is_plain_and_chat_contains_one_prompt_copy() -> None:
    module = _load_module()
    cards = module.cards_markdown([_card()], "2026-08-31 18:00 CDT")
    chat = module.chat_markdown("Standing prompt", cards)

    assert "## Card 1" in cards
    assert "Question:\nQuestion" in cards
    assert "Answer:\nAnswer" in cards
    assert "<b>" not in cards
    assert chat.count("Standing prompt") == 1
    assert chat.endswith("Answer\n")


def test_data_document_has_stable_snake_case_fields() -> None:
    module = _load_module()
    document = module.data_document(
        [_card()],
        updated_at="2026-08-31 18:00 CDT",
        digest="abc",
        source_addon="speed_streak_v2_04",
        review_later_flag=4,
    )

    assert document["schema_version"] == 2
    assert document["count"] == 1
    assert document["cards"][0]["card_id"] == 123
    assert document["cards"][0]["flagged_at"].endswith("-05:00")
    assert document["cards"][0]["last_seen_at"].endswith("-05:00")


def test_mobile_page_embeds_both_copy_payloads_safely() -> None:
    module = _load_module()
    card = _card(front_html="<script>bad()</script>[anki:play:q:0]<b>Question</b>")
    page = module.page_html(
        [card],
        updated_at="2026-08-31 18:00 CDT",
        standing_instructions="Standing prompt",
    )

    assert 'name="viewport"' in page
    assert '>ChatGPT</button>' in page
    assert '>Cards</button>' in page
    assert "navigator.clipboard" in page
    assert "dateOffset" in page
    assert "Seen ↓" in page
    assert "height:clamp(330px,62svh,590px)" in page
    assert "bad()" not in page
    assert "[anki:play:q:0]" not in page


def test_empty_queue_is_a_valid_publishable_page() -> None:
    module = _load_module()
    cards = module.cards_markdown([], "2026-08-31 18:00 CDT")
    page = module.page_html([], updated_at="2026-08-31 18:00 CDT", standing_instructions="Prompt")

    assert "No currently blue cards were seen in this period." in cards
    assert "No currently blue cards were seen in this period." in page


def test_answer_side_is_separated_and_audio_markup_removed() -> None:
    module = _load_module()
    document = module.data_document(
        [_card(back_html='<b>Question</b><hr id="answer"><button class="replay-button">play</button><i>Answer</i>[sound:x.mp3]')],
        updated_at="now",
        digest="abc",
        source_addon="speed_streak_v2_04",
        review_later_flag=4,
    )

    card = document["cards"][0]
    assert "Question" not in card["back_html"]
    assert "play" not in card["back_html"]
    assert "sound:" not in card["back_html"]
    assert card["back_text"] == "Answer"
