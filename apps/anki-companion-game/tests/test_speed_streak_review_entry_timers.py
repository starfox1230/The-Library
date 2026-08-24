from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types

import pytest


sys.dont_write_bytecode = True

ADDON_ROOT = Path(__file__).resolve().parents[1]
VERSIONS = (
    ADDON_ROOT / "speed-streak-addon-v1.28B",
    ADDON_ROOT / "speed-streak-addon-v1.31",
    ADDON_ROOT / "speed-streak-addon-v1.32",
    ADDON_ROOT / "speed-streak-addon-v1.33",
    ADDON_ROOT / "speed-streak-addon-v1.34",
    ADDON_ROOT / "speed-streak-addon-v1.35",
)


def load_game_state(addon_root: Path):
    package_name = f"speed_streak_test_{addon_root.name.replace('.', '_').replace('-', '_')}"
    package = types.ModuleType(package_name)
    package.__path__ = [str(addon_root)]
    sys.modules[package_name] = package

    for module_name in ("feedback_catalog", "game_state"):
        qualified_name = f"{package_name}.{module_name}"
        spec = importlib.util.spec_from_file_location(
            qualified_name,
            addon_root / f"{module_name}.py",
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified_name] = module
        spec.loader.exec_module(module)

    return sys.modules[f"{package_name}.game_state"]


@pytest.fixture(params=VERSIONS, ids=lambda path: path.name)
def game_state(request):
    return load_game_state(request.param)


def expire_current_phase(game_state, engine) -> None:
    engine.state.phase_start_epoch_ms = (
        game_state.now_epoch_ms() - engine.state.phase_limit_ms - 1
    )


def test_review_entry_free_card_covers_both_sides_and_preserves_run(game_state) -> None:
    engine = game_state.CompanionGameEngine()
    engine.state.streak = 5
    engine.state.score = 40
    engine.state.satellite_colors = ["green"] * 5

    event = engine.sync_visible_question_surface(
        card_id="1",
        deck_name="Deck A",
        review_entry=True,
    )

    assert event == "sync"
    assert engine.state.first_card_free is True
    assert engine.state.phase == "question"
    assert engine.state.phase_limit_ms == 0
    assert engine.state.streak == 5
    assert engine.state.score == 40

    engine.sync_visible_answer_surface(card_id="1", deck_name="Deck A")

    assert engine.state.first_card_free is True
    assert engine.card.question_free is True
    assert engine.state.phase == "answer"
    assert engine.state.phase_limit_ms == 0
    assert engine.check_timeout() is None

    engine.on_rate(3)

    assert engine.state.streak == 6
    assert engine.state.score > 40


def test_only_first_card_of_review_entry_is_free(game_state) -> None:
    engine = game_state.CompanionGameEngine()
    engine.sync_visible_question_surface(
        card_id="1",
        deck_name="Deck A",
        review_entry=True,
    )
    engine.sync_visible_answer_surface(card_id="1", deck_name="Deck A")
    engine.on_rate(3)

    engine.sync_visible_question_surface(
        card_id="2",
        deck_name="Deck A",
        review_entry=False,
    )

    assert engine.state.first_card_free is False
    assert engine.state.phase_limit_ms == engine.state.question_limit_ms


def test_late_review_entry_hook_does_not_rearm_second_free_card(game_state) -> None:
    pending = True

    first_card_is_free = pending
    pending = False
    pending = game_state.review_entry_allowance_after_state_change(
        pending,
        new_state="review",
        old_state="overview",
    )

    assert first_card_is_free is True
    assert pending is False

    pending = game_state.review_entry_allowance_after_state_change(
        pending,
        new_state="deckBrowser",
        old_state="review",
    )

    assert pending is True


def test_duplicate_first_question_sync_preserves_free_card(game_state) -> None:
    engine = game_state.CompanionGameEngine()
    engine.sync_visible_question_surface(
        card_id="1",
        deck_name="Deck A",
        review_entry=True,
    )
    phase_started_at = engine.state.phase_start_epoch_ms

    event = engine.sync_visible_question_surface(
        card_id="1",
        deck_name="Deck A",
        review_entry=False,
    )

    assert event == "question"
    assert engine.state.first_card_free is True
    assert engine.card.question_free is True
    assert engine.state.phase_limit_ms == 0
    assert engine.state.phase_start_epoch_ms == phase_started_at

    engine.sync_visible_answer_surface(card_id="1", deck_name="Deck A")

    assert engine.state.first_card_free is True
    assert engine.state.phase_limit_ms == 0


def test_new_review_entry_is_free_even_for_same_deck_and_keeps_streak(game_state) -> None:
    engine = game_state.CompanionGameEngine()
    engine.sync_visible_question_surface(
        card_id="1",
        deck_name="Deck A",
        review_entry=True,
    )
    engine.sync_visible_answer_surface(card_id="1", deck_name="Deck A")
    engine.on_rate(4)
    streak_before_reentry = engine.state.streak
    score_before_reentry = engine.state.score

    engine.sync_visible_question_surface(
        card_id="2",
        deck_name="Deck A",
        review_entry=True,
    )

    assert engine.state.first_card_free is True
    assert engine.state.phase_limit_ms == 0
    assert engine.state.streak == streak_before_reentry
    assert engine.state.score == score_before_reentry


def test_free_first_card_setting_can_be_disabled(game_state) -> None:
    engine = game_state.CompanionGameEngine()
    engine.update_time_limits(
        question_seconds=12,
        answer_seconds=8,
        free_first_card_on_review_entry=False,
    )

    engine.sync_visible_question_surface(
        card_id="1",
        deck_name="Deck A",
        review_entry=True,
    )

    assert engine.state.first_card_free is False
    assert engine.state.phase_limit_ms == engine.state.question_limit_ms

    engine.sync_visible_answer_surface(card_id="1", deck_name="Deck A")

    assert engine.state.first_card_free is False
    assert engine.state.phase_limit_ms == engine.state.review_limit_ms


def test_answer_timeout_breaks_streak_by_default(game_state) -> None:
    engine = game_state.CompanionGameEngine()
    engine.sync_visible_question_surface(
        card_id="1",
        deck_name="Deck A",
        review_entry=False,
    )
    engine.sync_visible_answer_surface(card_id="1", deck_name="Deck A")
    engine.state.streak = 4
    engine.state.satellite_colors = ["green"] * 4
    expire_current_phase(game_state, engine)

    event = engine.check_timeout()

    assert event == "timeout"
    assert engine.state.streak == 0
    assert engine.state.satellite_colors == []
    assert engine.state.failure_visual_active is True


def test_answer_timeout_can_preserve_streak(game_state) -> None:
    engine = game_state.CompanionGameEngine()
    engine.update_time_limits(
        question_seconds=12,
        answer_seconds=8,
        answer_timeout_breaks_streak=False,
    )
    engine.sync_visible_question_surface(
        card_id="1",
        deck_name="Deck A",
        review_entry=False,
    )
    engine.sync_visible_answer_surface(card_id="1", deck_name="Deck A")
    engine.state.streak = 4
    engine.state.satellite_colors = ["green"] * 4
    expire_current_phase(game_state, engine)

    event = engine.check_timeout()

    assert event == "answer-timeout"
    assert engine.state.streak == 4
    assert engine.state.satellite_colors == ["green"] * 4
    assert engine.state.failure_visual_active is False
    assert engine.check_timeout() is None


def test_question_timeout_still_breaks_streak_when_answer_timeout_is_soft(game_state) -> None:
    engine = game_state.CompanionGameEngine()
    engine.update_time_limits(
        question_seconds=12,
        answer_seconds=8,
        answer_timeout_breaks_streak=False,
    )
    engine.sync_visible_question_surface(
        card_id="1",
        deck_name="Deck A",
        review_entry=False,
    )
    engine.state.streak = 4
    engine.state.satellite_colors = ["green"] * 4
    expire_current_phase(game_state, engine)

    event = engine.check_timeout()

    assert event == "timeout"
    assert engine.state.streak == 0
    assert engine.state.failure_visual_active is True


def test_timer_preferences_survive_run_reset_and_settings_reset_to_on(game_state) -> None:
    engine = game_state.CompanionGameEngine()
    engine.update_time_limits(
        question_seconds=12,
        answer_seconds=8,
        free_first_card_on_review_entry=False,
        answer_timeout_breaks_streak=False,
    )

    engine.hard_reset()

    assert engine.state.free_first_card_on_review_entry is False
    assert engine.state.answer_timeout_breaks_streak is False

    engine.reset_settings_to_defaults()

    assert engine.state.free_first_card_on_review_entry is True
    assert engine.state.answer_timeout_breaks_streak is True


def test_timer_preferences_are_exported_to_both_settings_surfaces(game_state) -> None:
    engine = game_state.CompanionGameEngine()
    exported = engine.export()

    assert exported["version"] >= 9
    assert exported["freeFirstCardOnReviewEntry"] == 1
    assert exported["answerTimeoutBreaksStreak"] == 1
