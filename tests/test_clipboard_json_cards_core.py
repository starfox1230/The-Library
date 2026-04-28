from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "apps" / "anki-pocket-knife" / "clipboard_json_cards_core.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("clipboard_json_cards_core", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_clipboard_json_cards_preserves_html_and_tags():
    module = _load_module()

    cards = module.parse_clipboard_json_cards(
        """
        [
          {
            "html": "{{c1::Radiochemical}} impurity is wrong {{c2::chemical form}}.",
            "tags": ["#AnkiChat::2026.04.15_Radiopharmaceutical_Impurity_Types"]
          }
        ]
        """
    )

    assert len(cards) == 1
    assert cards[0].html == "{{c1::Radiochemical}} impurity is wrong {{c2::chemical form}}."
    assert cards[0].tags == ("#AnkiChat::2026.04.15_Radiopharmaceutical_Impurity_Types",)


def test_parse_clipboard_json_cards_accepts_json_code_fences_and_original_html_fallback():
    module = _load_module()

    cards = module.parse_clipboard_json_cards(
        """
        ```json
        [
          {
            "originalHtml": "{{c1::Radionuclide}} impurity is wrong {{c2::radioactive isotope}}.",
            "tags": "tag-one tag-two"
          }
        ]
        ```
        """
    )

    assert len(cards) == 1
    assert cards[0].html == "{{c1::Radionuclide}} impurity is wrong {{c2::radioactive isotope}}."
    assert cards[0].tags == ("tag-one", "tag-two")


def test_parse_clipboard_json_cards_accepts_content_field_and_ignores_id():
    module = _load_module()

    cards = module.parse_clipboard_json_cards(
        """
        [
          {
            "content": "For pulmonary interstitial emphysema, place the {{c1::bad side down}}.",
            "tags": ["#AnkiChat::2026.04.27_Sledgehammer"],
            "id": "note-001"
          },
          {
            "content": "For suspected bronchial foreign body on decubitus imaging, place the {{c1::lucent side down}}.",
            "tags": ["#AnkiChat::2026.04.27_Sledgehammer"],
            "id": "note-002"
          }
        ]
        """
    )

    assert [card.html for card in cards] == [
        "For pulmonary interstitial emphysema, place the {{c1::bad side down}}.",
        "For suspected bronchial foreign body on decubitus imaging, place the {{c1::lucent side down}}.",
    ]
    assert cards[0].tags == ("#AnkiChat::2026.04.27_Sledgehammer",)
    assert cards[1].tags == ("#AnkiChat::2026.04.27_Sledgehammer",)


def test_parse_clipboard_json_cards_accepts_one_cloze_card_per_line():
    module = _load_module()

    cards = module.parse_clipboard_json_cards(
        """
        {{c1::An acute peripancreatic fluid collection, or APFC::What collection}} occurs {{c2::within 4 weeks of::when in}} {{c3::interstitial edematous pancreatitis}}.
        {{c1::An acute necrotic collection, or ANC::What collection}} occurs {{c3::within 4 weeks of::when in}} {{c2::necrotizing pancreatitis}}.
        {{c1::A pancreatic pseudocyst::What collection}} occurs {{c3::at 4 weeks or more after::when in}} {{c2::interstitial edematous pancreatitis}}.
        {{c1::Walled-off necrosis, or WON::What collection}} occurs {{c3::at 4 weeks or more after::when in}} {{c2::necrotizing pancreatitis}}.
        """
    )

    assert [card.html for card in cards] == [
        "{{c1::An acute peripancreatic fluid collection, or APFC::What collection}} occurs {{c2::within 4 weeks of::when in}} {{c3::interstitial edematous pancreatitis}}.",
        "{{c1::An acute necrotic collection, or ANC::What collection}} occurs {{c3::within 4 weeks of::when in}} {{c2::necrotizing pancreatitis}}.",
        "{{c1::A pancreatic pseudocyst::What collection}} occurs {{c3::at 4 weeks or more after::when in}} {{c2::interstitial edematous pancreatitis}}.",
        "{{c1::Walled-off necrosis, or WON::What collection}} occurs {{c3::at 4 weeks or more after::when in}} {{c2::necrotizing pancreatitis}}.",
    ]
    assert all(card.tags == () for card in cards)


def test_parse_clipboard_json_cards_accepts_markdown_list_prefixes_for_cloze_lines():
    module = _load_module()

    cards = module.parse_clipboard_json_cards(
        """
        1. {{c1::First card}}
        - {{c1::Second card}}
        > {{c1::Third card}}
        """
    )

    assert [card.html for card in cards] == [
        "{{c1::First card}}",
        "{{c1::Second card}}",
        "{{c1::Third card}}",
    ]


def test_parse_clipboard_json_cards_rejects_missing_html():
    module = _load_module()

    try:
        module.parse_clipboard_json_cards('[{"tags": ["x"]}]')
        raise AssertionError("Expected parse_clipboard_json_cards() to raise ValueError.")
    except ValueError as exc:
        assert "'html' or 'content'" in str(exc)


def test_parse_clipboard_json_cards_rejects_non_array_payload():
    module = _load_module()

    try:
        module.parse_clipboard_json_cards('{"html": "x"}')
        raise AssertionError("Expected parse_clipboard_json_cards() to raise ValueError.")
    except ValueError as exc:
        assert "array of card objects" in str(exc)
        assert "one cloze card per non-empty line" in str(exc)


def test_parse_clipboard_json_cards_rejects_partial_cloze_line_sets():
    module = _load_module()

    try:
        module.parse_clipboard_json_cards(
            """
            {{c1::First card}}
            This line is not a cloze card.
            """
        )
        raise AssertionError("Expected parse_clipboard_json_cards() to raise ValueError.")
    except ValueError as exc:
        assert "Line 2" in str(exc)
        assert "{{c1::...}}" in str(exc)
