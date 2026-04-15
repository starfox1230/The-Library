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


def test_parse_clipboard_json_cards_rejects_missing_html():
    module = _load_module()

    try:
        module.parse_clipboard_json_cards('[{"tags": ["x"]}]')
        raise AssertionError("Expected parse_clipboard_json_cards() to raise ValueError.")
    except ValueError as exc:
        assert "'html'" in str(exc)


def test_parse_clipboard_json_cards_rejects_non_array_payload():
    module = _load_module()

    try:
        module.parse_clipboard_json_cards('{"html": "x"}')
        raise AssertionError("Expected parse_clipboard_json_cards() to raise ValueError.")
    except ValueError as exc:
        assert "array of card objects" in str(exc)
