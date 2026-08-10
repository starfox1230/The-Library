from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "apps"
    / "anki-pocket-knife"
    / "selected_card_export_core.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "selected_card_export_core", MODULE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


core = load_module()


def test_html_to_readable_text_keeps_media_names_and_layout() -> None:
    value = (
        "<style>.card { color: red; }</style>"
        "<div>First&nbsp;line<br>Second line</div>"
        '<img src="scan.png">'
        "[sound:answer.mp3]"
    )

    assert core.html_to_readable_text(value) == (
        "First\u00a0line\nSecond line\n[Image: scan.png][Audio: answer.mp3]"
    )


def test_answer_side_only_removes_repeated_question() -> None:
    answer = '<div>Question</div><hr class="x" id="answer"><div>Answer</div>'

    assert core.answer_side_only(answer) == "<div>Answer</div>"


def test_render_text_export_includes_rendered_sides_and_every_field() -> None:
    card = core.ExportCard(
        card_id=123,
        note_id=456,
        deck_name="Radiology",
        original_deck_name="",
        note_type_name="saCloze++",
        card_template_name="Cloze",
        tags=("abdomen", "ct"),
        front_html="<div>What is {{c1::this}}?</div>",
        back_html='<div>Question</div><hr id="answer"><b>This.</b>',
        fields=(
            ("Text", "What is {{c1::this}}?"),
            ("Extra", '<img alt="Example scan" src="scan.png">'),
        ),
    )

    exported = core.render_text_export([card])

    assert "Selected cards: 1" in exported
    assert "Card ID: 123" in exported
    assert "Tags: abdomen ct" in exported
    assert "FRONT (rendered)" in exported
    assert "BACK (rendered)" in exported
    assert "[Text]\nWhat is {{c1::this}}?" in exported
    assert "[Extra]\n[Image: Example scan]" in exported
