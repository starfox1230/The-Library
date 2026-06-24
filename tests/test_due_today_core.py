from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from datetime import date
import os
import time


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "apps" / "anki-pocket-knife" / "due_today_core.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("due_today_core", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_rendered_question_image_detection():
    module = _load_module()
    assert module.rendered_question_has_image("<div>Question<img src='x.png'></div>")
    assert module.rendered_question_has_image("<IMG SRC='x.png' />")
    assert not module.rendered_question_has_image("<div>Text only</div>")


def test_parent_selection_wins_and_expands_to_subdecks():
    module = _load_module()
    names = {
        1: "Medicine",
        2: "Medicine::Cardiology",
        3: "Medicine::Cardiology::ECG",
        4: "Physics",
    }
    assert module.normalize_deck_selection([1, 2, 4], names) == [1, 4]
    assert module.expand_deck_selection([1, 2], names) == [1, 2, 3]


def test_deleted_remembered_decks_are_ignored():
    module = _load_module()
    assert module.normalize_deck_selection([1, 99], {1: "Existing"}) == [1]


def test_scheduler_day_and_labels():
    module = _load_module()
    selected = date(2026, 6, 18)
    assert module.selected_scheduler_day(500, 3) == 497
    assert module.days_ago_for_date(selected, date(2026, 6, 21)) == 3
    assert module.deck_date_label(0, date(2026, 6, 21)) == "Today 2026-06-21"
    assert module.deck_date_label(1, date(2026, 6, 20)) == "Yesterday 2026-06-20"
    assert module.deck_date_label(3, selected) == "2026-06-18"
    assert module.target_deck_names(0, date(2026, 6, 21)) == {
        "audio": "..Due Today 2026-06-21 Audio",
        "visual": "..Due Today 2026-06-21 Visual",
        "combined": "..Due Today 2026-06-21 Combined",
    }


def test_rollover_boundaries_preserve_dst_day_length():
    module = _load_module()
    if not hasattr(time, "tzset"):
        return
    previous_tz = os.environ.get("TZ")
    try:
        os.environ["TZ"] = "America/Chicago"
        time.tzset()
        cutoff = int(time.mktime((2026, 3, 9, 4, 0, 0, 0, 0, -1)))
        start, end = module.rollover_boundaries(cutoff, 0)
        assert end - start == 23 * 60 * 60
    finally:
        if previous_tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = previous_tz
        time.tzset()
