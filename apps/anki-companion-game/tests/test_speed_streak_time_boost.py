from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import sys
import types

import pytest


sys.dont_write_bytecode = True
ADDON_ROOT = Path(__file__).resolve().parents[1] / "speed-streak-addon-v1.32"
ENGINE_ROOTS = (
    ADDON_ROOT,
    ADDON_ROOT.parent / "speed-streak-addon-v1.33",
)


def load_game_state(addon_root: Path):
    package_name = f"{addon_root.name.replace('-', '_')}_time_boost_tests"
    package = types.ModuleType(package_name)
    package.__path__ = [str(addon_root)]
    sys.modules[package_name] = package
    for module_name in ("feedback_catalog", "game_state"):
        qualified_name = f"{package_name}.{module_name}"
        spec = importlib.util.spec_from_file_location(qualified_name, addon_root / f"{module_name}.py")
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified_name] = module
        spec.loader.exec_module(module)
    return sys.modules[f"{package_name}.game_state"]


@pytest.fixture(params=ENGINE_ROOTS, ids=lambda path: path.name)
def game_state(request):
    return load_game_state(request.param)


def enter_timed_answer(engine, card_id: str = "1") -> None:
    engine.sync_visible_question_surface(card_id=card_id, deck_name="Deck", review_entry=False)
    engine.sync_visible_answer_surface(card_id=card_id, deck_name="Deck")


def enable_time_boost(engine, **overrides) -> None:
    values = {
        "gameplay_mode": "time_boost",
        "no_pause_mode": False,
        "boost_seconds": 5,
        "max_boost_charges": 3,
        "starting_boost_charges": 1,
        "cards_per_boost_charge": 2,
    }
    values.update(overrides)
    engine.update_gameplay_settings(**values)


def test_legacy_mode_remains_default_and_keeps_points(game_state) -> None:
    engine = game_state.CompanionGameEngine()
    enter_timed_answer(engine)

    engine.on_rate(3)

    assert engine.state.gameplay_mode == game_state.GAMEPLAY_MODE_LEGACY
    assert engine.state.score > 0
    assert engine.state.streak_multiplier > 1


def test_time_boost_mode_replaces_points_and_earns_charge_progress(game_state) -> None:
    engine = game_state.CompanionGameEngine()
    enable_time_boost(engine, cards_per_boost_charge=2)

    enter_timed_answer(engine, "1")
    engine.on_rate(3)
    assert engine.state.score == 0
    assert engine.state.streak_multiplier == 1
    assert engine.state.boost_charges == 1
    assert engine.state.boost_charge_progress == 1

    engine.sync_visible_question_surface(card_id="2", deck_name="Deck")
    engine.sync_visible_answer_surface(card_id="2", deck_name="Deck")
    engine.on_rate(4)

    assert engine.state.boost_charges == 2
    assert engine.state.boost_charge_progress == 0
    assert "charge earned" in engine.state.last_event_text


def test_time_boost_consumes_one_charge_and_extends_active_phase(game_state) -> None:
    engine = game_state.CompanionGameEngine()
    enable_time_boost(engine, boost_seconds=5)
    enter_timed_answer(engine)
    original_limit = engine.state.phase_limit_ms

    event = engine.use_time_boost()

    assert event == "time-boost"
    assert engine.state.phase_limit_ms == original_limit + 5_000
    assert engine.state.boost_charges == 0
    assert engine.state.boosts_used == 1
    assert engine.use_time_boost() is None


def test_boost_cannot_revive_expired_free_untimed_or_paused_phase(game_state) -> None:
    engine = game_state.CompanionGameEngine()
    enable_time_boost(engine)
    enter_timed_answer(engine)
    engine.state.phase_start_epoch_ms = game_state.now_epoch_ms() - engine.state.phase_limit_ms - 1
    assert engine.use_time_boost() is None

    engine.hard_reset()
    engine.sync_visible_question_surface(card_id="2", deck_name="Deck", review_entry=True)
    assert engine.state.first_card_free is True
    assert engine.use_time_boost() is None


def test_expired_or_untimed_card_does_not_advance_charge_meter(game_state) -> None:
    engine = game_state.CompanionGameEngine()
    enable_time_boost(engine, cards_per_boost_charge=2)
    enter_timed_answer(engine)
    engine.state.phase_start_epoch_ms = game_state.now_epoch_ms() - engine.state.phase_limit_ms - 1

    engine.on_rate(3)

    assert engine.state.boost_charge_progress == 0
    assert "unchanged" in engine.state.last_event_text

    engine.sync_visible_question_surface(
        card_id="2",
        deck_name="Deck",
        timer_policy={"mode": game_state.TIMER_POLICY_NO_TIMEOUT},
    )
    engine.sync_visible_answer_surface(
        card_id="2",
        deck_name="Deck",
        timer_policy={"mode": game_state.TIMER_POLICY_NO_TIMEOUT},
    )
    engine.on_rate(4)
    assert engine.state.boost_charge_progress == 0

    engine.sync_visible_question_surface(
        card_id="3",
        deck_name="Deck",
        timer_policy={"mode": game_state.TIMER_POLICY_NO_TIMEOUT},
    )
    assert engine.use_time_boost() is None

    engine.sync_visible_question_surface(card_id="4", deck_name="Deck")
    assert engine.toggle_pause() == "pause"
    assert engine.use_time_boost() is None


def test_no_pause_blocks_manual_pause_but_not_safety_pause_or_resume(game_state) -> None:
    engine = game_state.CompanionGameEngine()
    enable_time_boost(engine, no_pause_mode=True)
    engine.sync_visible_question_surface(card_id="1", deck_name="Deck")

    assert engine.toggle_pause() == "pause-blocked"
    assert engine.state.paused is False
    assert engine.toggle_pause(count_in_stats=False) == "pause"
    assert engine.state.paused is True
    assert engine.toggle_pause() == "resume"
    assert engine.state.paused is False


def test_focus_rules_export_toggle_and_survive_hard_reset(game_state) -> None:
    engine = game_state.CompanionGameEngine()
    enable_time_boost(
        engine,
        no_pause_mode=True,
        no_undo_mode=True,
        show_focus_mode_toggles=False,
    )

    exported = engine.export()
    assert exported["noPauseMode"] == 1
    assert exported["noUndoMode"] == 1
    assert exported["showFocusModeToggles"] == 0

    assert engine.set_focus_rule("no-pause", False) == "focus-rule"
    assert engine.set_focus_rule("no-undo", False) == "focus-rule"
    assert engine.state.no_pause_mode is False
    assert engine.state.no_undo_mode is False

    engine.set_focus_rule("no-undo", True)
    engine.hard_reset()
    assert engine.state.no_undo_mode is True
    assert engine.state.show_focus_mode_toggles is False


def test_no_undo_history_can_be_discarded_without_reverting_state(game_state) -> None:
    engine = game_state.CompanionGameEngine()
    enable_time_boost(engine, no_undo_mode=True)
    enter_timed_answer(engine)
    snapshot = engine.capture_review_undo_snapshot()
    engine.on_rate(3)
    engine.commit_review_undo_snapshot(snapshot)
    streak = engine.state.streak

    engine.clear_review_undo_history()

    assert engine.undo_last_review() is False
    assert engine.state.streak == streak


def test_boost_state_round_trips_and_undo_restores_charge_bank(game_state) -> None:
    engine = game_state.CompanionGameEngine()
    enable_time_boost(engine, cards_per_boost_charge=2)
    enter_timed_answer(engine)
    snapshot = engine.capture_review_undo_snapshot()
    engine.on_rate(3)
    assert engine.state.boost_charge_progress == 1
    engine.commit_review_undo_snapshot(snapshot)

    assert engine.undo_last_review() is True
    assert engine.state.boost_charges == 1
    assert engine.state.boost_charge_progress == 0

    runtime = engine.export_runtime()
    restored = game_state.CompanionGameEngine()
    enable_time_boost(restored, cards_per_boost_charge=2)
    restored.restore_runtime(runtime)
    assert restored.state.boost_charges == engine.state.boost_charges
    assert restored.state.boost_charge_progress == engine.state.boost_charge_progress


def test_hard_reset_refills_configured_starting_charges(game_state) -> None:
    engine = game_state.CompanionGameEngine()
    enable_time_boost(engine, max_boost_charges=5, starting_boost_charges=2)
    enter_timed_answer(engine)
    engine.use_time_boost()
    assert engine.state.boost_charges == 1

    engine.hard_reset()

    assert engine.state.gameplay_mode == game_state.GAMEPLAY_MODE_TIME_BOOST
    assert engine.state.boost_charges == 2
    assert engine.state.boost_charge_progress == 0


def test_time_boost_hover_controls_and_blocked_undo_feedback_are_wired() -> None:
    overlay_js = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    overlay_css = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")
    reviewer_overlay = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
    settings_dialog = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")
    shortcuts = (ADDON_ROOT / "shortcuts.py").read_text(encoding="utf-8")
    config = (ADDON_ROOT / "config.json").read_text(encoding="utf-8")

    assert 'class="acg-boost-hover-zone"' in overlay_js
    assert 'class="acg-boost-hover-controls"' in overlay_js
    assert '<kbd id="acgBoostShortcutLabel">R</kbd>' in overlay_js
    assert '"default": "R"' in shortcuts
    assert '"boost": "R"' in config
    assert "speed-streak:set-focus-rule:${rule}:${enabled ? 1 : 0}" in overlay_js
    assert 'bindFocusRuleToggle("acgNoPauseToggle", "no-pause", "noPauseMode")' in overlay_js
    assert 'bindFocusRuleToggle("acgNoUndoToggle", "no-undo", "noUndoMode")' in overlay_js
    assert "speed-streak:open-settings:shortcut:boost" in overlay_js
    assert "speed-streak:open-settings:gameplay:time-boost" in overlay_js
    assert "boostHoverZone.blur()" in overlay_js
    hover_zone_rule = re.search(
        r"\.acg-boost-hover-zone\s*\{(?P<body>.*?)\}",
        overlay_css,
        flags=re.DOTALL,
    )
    assert hover_zone_rule is not None
    assert "pointer-events: auto" in hover_zone_rule.group("body")
    controls_rule = re.search(
        r"\.acg-boost-hover-controls\s*\{(?P<body>.*?)\}",
        overlay_css,
        flags=re.DOTALL,
    )
    assert controls_rule is not None
    assert "position: absolute" not in controls_rule.group("body")
    assert "display: flex" in controls_rule.group("body")
    assert "flex-wrap: nowrap" in controls_rule.group("body")
    assert "max-height: 0" in controls_rule.group("body")
    assert "border:" not in controls_rule.group("body")
    assert "background:" not in controls_rule.group("body")
    boost_key_rule = re.search(
        r"\.acg-boost-key\s*\{(?P<body>.*?)\}",
        overlay_css,
        flags=re.DOTALL,
    )
    assert boost_key_rule is not None
    assert "height: 19px" in boost_key_rule.group("body")
    assert "transform: none" in boost_key_rule.group("body")
    assert ".acg-boost-hover-zone:hover .acg-boost-hover-controls" in overlay_css
    assert ".acg-boost-hover-zone:focus-within .acg-boost-hover-controls" in overlay_css
    assert "if (event.detail > 0) button.blur()" in overlay_js
    assert "QKeySequence.StandardKey.Undo" in reviewer_overlay
    assert "_claim_no_undo_shortcuts" in reviewer_overlay
    assert "focus_shortcut_setting" in settings_dialog
    assert "focus_time_boost_settings" in settings_dialog
    assert "self._expand_settings_section(section)" in settings_dialog
    assert "self.settings_scroll.ensureWidgetVisible(field, 32, 80)" in settings_dialog


def test_v1_33_interaction_contracts_are_wired() -> None:
    addon_root = ADDON_ROOT.parent / "speed-streak-addon-v1.33"
    overlay_js = (addon_root / "web" / "overlay.js").read_text(encoding="utf-8")
    overlay_css = (addon_root / "web" / "overlay.css").read_text(encoding="utf-8")
    reviewer_overlay = (addon_root / "reviewer_overlay.py").read_text(encoding="utf-8")
    settings_dialog = (addon_root / "settings_dialog.py").read_text(encoding="utf-8")
    card_timer_js = (addon_root / "web" / "card_timer.js").read_text(encoding="utf-8")
    manifest = (addon_root / "manifest.json").read_text(encoding="utf-8")

    assert '"name": "Speed Streak v1.33"' in manifest
    assert '"package": "speed_streak_v1_33"' in manifest
    assert overlay_js.index('id="acgBoostProgressText"') < overlay_js.index('class="acg-boost-hover-controls"')
    assert '"cards"' in overlay_js and '"capacity"' in overlay_js
    assert "speed-streak:open-settings:gameplay:time-boost:${setting}" in overlay_js
    assert "self.cards_per_boost_charge_spin" in settings_dialog
    assert "self.max_boost_charges_spin" in settings_dialog

    for marker in (
        "VISUAL_MODE_ICONS",
        'id="acgVisualSelector"',
        'id="acgVisualResourceSlider"',
        "visualResourceLevels",
        "applyVisualResourceLevel",
        'id="acgStage"',
    ):
        assert marker in overlay_js
    for removed_id in ("acgLayoutSphere", "acgLayoutCrystal", "acgLayoutBrick"):
        assert removed_id not in overlay_js
    assert ".acg-visual-selector-panel" in overlay_css
    assert "Estimated at roughly" in overlay_js
    assert "--acg-visual-panel-width" in overlay_css
    assert "sidebarResizeObserver" in overlay_js
    assert "narrow-pane" in overlay_js and "narrow-pane" in overlay_css
    assert "overflow-wrap: anywhere" in overlay_css
    assert "user-select: none" in overlay_css
    assert '${VISUAL_MODE_ICONS.sphere}<span>Orbit</span>' not in overlay_js
    assert 'aria-label="Satellite Orbit"' in overlay_js

    assert "WINDOW_PRESET_ICON" in overlay_js
    assert 'data-preset-action="set-default"' in overlay_js
    assert "windowPositionDefaultPresetId" in overlay_js
    assert "_toggle_default_window_position_preset" in reviewer_overlay
    assert "_window_position_default_preset_id" in reviewer_overlay
    assert 'id="acgInlineSideToggle"' in overlay_js
    assert "speed-streak:toggle-inline-side" in overlay_js
    assert "_apply_inline_side_position" in reviewer_overlay

    assert "const signatureChanged = nextSignature !== renderer.animationSignature" in card_timer_js
    assert "if (signatureChanged && renderer.frameId)" in card_timer_js
    assert "(timer.deadlineEpochMs - Date.now()) / timer.total" in card_timer_js
    assert "if (!renderer.needsResize && renderer.dpr === dpr)" in card_timer_js
    assert "stopTimerBarWebgl();" in card_timer_js
    assert "startedAt: Date.now()" not in card_timer_js

    live_timer_body = overlay_js[
        overlay_js.index("function renderLiveTimerState(data)") : overlay_js.index("function render(data)")
    ]
    full_render_body = overlay_js[
        overlay_js.index("function render(data)") : overlay_js.index("function renderGameplayEconomy(data)")
    ]
    assert "renderGameplayEconomy(data);" not in live_timer_body
    assert "renderGameplayEconomy(data);" in full_render_body
    assert "lastBoostBankSignature" in overlay_js
    assert "boostBankResizeObserver" in overlay_js
    assert "const nextSignature = `${charges}|${maxCharges}|${Number(useFraction)}`" in overlay_js

    assert "const signatureChanged = nextSignature !== renderer.animationSignature" in overlay_js
    assert "const drawStateChanged = nextDrawStateSignature !== renderer.drawStateSignature" in overlay_js
    assert "(timer.deadlineEpochMs - Date.now()) / timer.total" in overlay_js
    assert "computeSharedRemainingMs(data) > 0" in overlay_js
    assert "startedAt: Date.now()" not in overlay_js
    assert "function initializeWebglCanvasSizing" in overlay_js
    assert "if (!renderer.needsResize && renderer.dpr === dpr)" in overlay_js
    assert "renderer.canvas.offsetWidth * clamp" not in overlay_js

    assert "self._last_inline_sidebar_hidden: Optional[bool] = None" in reviewer_overlay
    assert "self._last_inline_sidebar_web is self._sidebar_web" in reviewer_overlay
    assert "self._last_inline_sidebar_hidden is hidden" in reviewer_overlay
