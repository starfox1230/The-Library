from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "apps" / "anki-pocket-knife" / "hard_cards_core.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("hard_cards_core", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_recent_unstable_card_outranks_old_historical_baggage():
    module = _load_module()
    config = module.merge_hard_cards_config({})

    recent_unstable = module.HardCardMetrics(
        card_id=1,
        note_id=11,
        deck_name="Deck",
        note_type_name="Cloze",
        is_cloze=True,
        current_state="relearning",
        created_age_hours=10.0,
        total_reps=5,
        total_lapses=1,
        again_count=3,
        hard_count=1,
        good_count=0,
        easy_count=0,
        total_answers=4,
        most_recent_ease=1,
        last_review_at_s=1000,
        failure_cluster_count=2,
        content=module.SelectedContent(("Text",), "{{c1::Acute PE}}"),
    )
    old_baggage = module.HardCardMetrics(
        card_id=2,
        note_id=22,
        deck_name="Deck",
        note_type_name="Cloze",
        is_cloze=True,
        current_state="review",
        created_age_hours=24.0 * 180.0,
        total_reps=300,
        total_lapses=18,
        again_count=1,
        hard_count=0,
        good_count=6,
        easy_count=2,
        total_answers=9,
        most_recent_ease=3,
        last_review_at_s=900,
        failure_cluster_count=0,
        content=module.SelectedContent(("Text",), "{{c1::Chronic stable card}}"),
    )

    ranked = module.rank_hard_cards([old_baggage, recent_unstable], config=config, top_n=10)

    assert [entry.metrics.card_id for entry in ranked] == [1, 2]


def test_select_note_content_prefers_cloze_text_field_and_preserves_markup():
    module = _load_module()
    config = module.merge_hard_cards_config({})

    selected = module.select_note_content(
        note_type_name="Cloze",
        fields={
            "Text": "Diagnosis?<br><br>{{c1::Pulmonary embolism}}",
            "Extra": "<div>aux</div>",
        },
        is_cloze=True,
        config=config,
    )

    assert selected.field_names == ("Text",)
    assert "{{c1::Pulmonary embolism}}" in selected.content_text


def test_exact_note_type_mapping_can_include_multiple_fields():
    module = _load_module()
    config = module.merge_hard_cards_config({})

    selected = module.select_note_content(
        note_type_name="Visual_Card_Multitude",
        fields={
            "Question": "<div>What finding matters?</div>",
            "English": "<div>{{c1::Tension pneumothorax}}</div>",
            "More Info": "<div>aux</div>",
        },
        is_cloze=False,
        config=config,
    )

    assert selected.field_names == ("Question", "English")
    assert "Question:" in selected.content_text
    assert "English:" in selected.content_text


def test_build_tutor_clipboard_text_uses_requested_format():
    module = _load_module()
    config = module.merge_hard_cards_config({})
    ranked = [
        module.RankedHardCard(
            metrics=module.HardCardMetrics(
                card_id=7,
                note_id=70,
                deck_name="Chest",
                note_type_name="Cloze",
                is_cloze=True,
                current_state="relearning",
                created_age_hours=12.0,
                total_reps=8,
                total_lapses=2,
                again_count=2,
                hard_count=1,
                good_count=0,
                easy_count=0,
                total_answers=3,
                most_recent_ease=1,
                last_review_at_s=500,
                failure_cluster_count=1,
                content=module.SelectedContent(("Text",), "{{c1::PE}}"),
            ),
            score=42.0,
            explanation=("2 Again", "currently relearning"),
            preview_text="{{c1::PE}}",
            score_components={"again": 24.0},
        )
    ]

    text = module.build_tutor_clipboard_text(ranked, config=config)

    assert "Card 1" in text
    assert "Deck: Chest" in text
    assert "Note type: Cloze" in text
    assert "Field source: Text" in text
    assert "{{c1::PE}}" in text


def test_partial_field_mapping_override_keeps_default_heuristics():
    module = _load_module()
    config = module.merge_hard_cards_config(
        {
            "preferred_field_names_by_note_type": {
                "Visual_Card_Multitude": ["Question", "English"],
            }
        }
    )

    assert config["preferred_field_names_by_note_type"]["Visual_Card_Multitude"] == [
        "Question",
        "English",
    ]
    assert config["preferred_field_names_by_note_type"]["__cloze__"] == ["Text"]
    assert "Front" in config["preferred_field_names_by_note_type"]["__default__"]
