from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import types


ADDON_ROOT = Path(__file__).resolve().parents[1] / "speed-streak-addon-v1.36"


def load_game_state():
    package_name = "speed_streak_v136_boost_feedback_tests"
    package = types.ModuleType(package_name)
    package.__path__ = [str(ADDON_ROOT)]
    sys.modules[package_name] = package
    for module_name in ("feedback_catalog", "game_state"):
        qualified = f"{package_name}.{module_name}"
        spec = importlib.util.spec_from_file_location(qualified, ADDON_ROOT / f"{module_name}.py")
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified] = module
        spec.loader.exec_module(module)
    return sys.modules[f"{package_name}.game_state"]


def test_default_boost_key_is_c_but_developer_preset_stays_backtick() -> None:
    shortcuts = (ADDON_ROOT / "shortcuts.py").read_text(encoding="utf-8")
    config = json.loads((ADDON_ROOT / "config.json").read_text(encoding="utf-8"))
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    controller = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")

    assert '"default": "C"' in shortcuts
    assert config["shortcut_bindings"]["boost"] == "C"
    assert '<kbd id="acgBoostShortcutLabel">C</kbd>' in overlay
    assert '{"pause": "9", "unpause": "U", "boost": "`"}' in controller


def test_boost_preserves_original_timer_and_reports_exact_rejections() -> None:
    game_state = load_game_state()
    engine = game_state.CompanionGameEngine()
    engine.update_gameplay_settings(
        gameplay_mode="time_boost",
        no_pause_mode=False,
        boost_seconds=40,
        max_boost_charges=3,
        starting_boost_charges=1,
        cards_per_boost_charge=2,
    )
    engine.sync_visible_question_surface(card_id="1", deck_name="Deck", review_entry=False)
    original_limit = engine.state.phase_limit_ms

    assert engine.state.phase_base_limit_ms == original_limit
    assert engine.use_time_boost() == "time-boost"
    assert engine.state.phase_limit_ms == original_limit + 40_000
    assert engine.state.phase_base_limit_ms == original_limit
    assert engine.state.phase_boost_remaining_ms == 40_000
    assert engine.state.phase_boost_anchor_epoch_ms > 0
    assert engine.time_boost_unavailable_reason() == "No Time Boost charges are available."

    assert engine.notify_time_boost_unavailable() == "time-boost-blocked"
    exported = engine.export()
    assert exported["lastEventType"] == "time-boost-blocked"
    assert exported["lastEventText"] == "No Time Boost charges are available."
    assert exported["phaseBaseLimitMs"] == original_limit
    assert exported["phaseBoostRemainingMs"] == 40_000


def test_boost_runtime_and_visual_diagnostics_are_persisted() -> None:
    game_state = load_game_state()
    engine = game_state.CompanionGameEngine()
    engine.state.phase = "question"
    engine.state.current_card_id = "1"
    engine.state.phase_start_epoch_ms = game_state.now_epoch_ms()
    engine.state.phase_limit_ms = 52_000
    engine.state.phase_base_limit_ms = 12_000
    engine.state.phase_boost_remaining_ms = 40_000
    engine.state.phase_boost_anchor_epoch_ms = game_state.now_epoch_ms()
    runtime = engine.export_runtime()
    restored = game_state.CompanionGameEngine()
    restored.restore_runtime(runtime)

    assert restored.state.phase_base_limit_ms == 12_000
    assert restored.state.phase_boost_remaining_ms == 40_000
    assert restored.state.phase_boost_anchor_epoch_ms > 0

    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    css = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")
    controller = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
    assert 'data.lastEventType === "time-boost-blocked"' in overlay
    assert 'const timerBound = direction === "spent";' in overlay
    assert 'timerBound ? $("acgTimerHero")' in overlay
    assert "u_overflow_turns" in overlay
    assert "gl_FragColor = mainColor + overflowColor;" not in overlay
    assert "float combinedAlpha = overflowColor.a + (mainColor.a * (1.0 - overflowColor.a));" in overlay
    assert "acgBoostOverflowBadge" in overlay
    assert ".acg-timer-hero.boost-impact" in css
    assert ".acg-timer-hero.boosted" not in css
    assert "const normalRatio = clamp(Number(timer.baseProgress || 0), 0, 1);" in overlay
    assert "const displayBaseProgress = timer.boostActive ? 0 : normalRatio;" in overlay
    assert "baseProgress: Boolean(timer?.boostActive) ? 0" in overlay
    assert "const blendTarget = normalRatio > 0.5 ? timerRamp.yellow : timerRamp.red;" in overlay
    assert '"boostShortcutHealthy"' in controller
    assert "QTimer.singleShot(120, self._claim_time_boost_shortcut)" in controller


def test_successful_boosts_and_focus_toggles_rely_on_their_visual_feedback() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    css = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")

    assert 'data.lastEventType === "time-boost"' in overlay
    assert 'spawnChargeTransfer(data, "spent");' in overlay
    assert "Time Boost activated" not in overlay
    assert 'data.lastEventType === "focus-rule"' not in overlay
    assert 'charges >= maxCharges ? "" : `Next charge ${progress} / ${required}`' in overlay
    assert "Charge bank full" not in overlay
    assert ".acg-boost-progress-text:empty" in css
