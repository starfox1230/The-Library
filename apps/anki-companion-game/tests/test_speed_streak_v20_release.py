from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import types

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ADDON_ROOT = ROOT / "speed-streak-addon-v2.0"
ANKIWEB_ROOT = ROOT / "ankiweb-v2.0"


def load_game_state():
    package_name = "speed_streak_v20_completion_tests"
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


def configured_boost_engine(game_state):
    engine = game_state.CompanionGameEngine()
    engine.update_gameplay_settings(
        gameplay_mode="time_boost",
        no_pause_mode=False,
        no_undo_mode=False,
        show_focus_mode_toggles=True,
        boost_seconds=10,
        max_boost_charges=5,
        starting_boost_charges=0,
        cards_per_boost_charge=3,
    )
    return engine


def test_release_metadata_and_installers_identify_2_0() -> None:
    manifest = json.loads((ADDON_ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "Speed Streak"
    assert manifest["package"] == "speed_streak_v2_0"
    assert "speed_streak_v1_36" in manifest["conflicts"]
    assert "speed_streak_v2_0" not in manifest["conflicts"]

    powershell_builder = (ADDON_ROOT / "build_ankiaddon.ps1").read_text(encoding="utf-8")
    powershell_installer = (ADDON_ROOT / "install_to_anki.ps1").read_text(encoding="utf-8")
    assert '"speed_streak_v2_0.ankiaddon"' in powershell_builder
    assert 'AddonFolderName = "speed_streak_v2_0"' in powershell_installer
    assert '"speed_streak_v1_36"' in powershell_installer


def test_boost_is_the_consistent_user_facing_name() -> None:
    settings = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    engine = (ADDON_ROOT / "game_state.py").read_text(encoding="utf-8")

    assert '"Time added per Boost"' in settings
    assert '"Boost bank capacity"' in settings
    assert '"Starting Boosts"' in settings
    assert '"Cards required to earn a Boost"' in settings
    assert "Next Boost ${progress} / ${required}" in overlay
    assert "Boost bank and controls" in overlay
    assert "of ${maxCharges} Boosts available" in overlay
    assert 'return "No Boosts are available."' in engine
    assert 'includes("Boost earned")' in overlay


def test_every_completed_card_advances_the_boost_meter() -> None:
    game_state = load_game_state()

    expired = configured_boost_engine(game_state)
    expired.sync_visible_question_surface(card_id="1", deck_name="Deck")
    expired.sync_visible_answer_surface(card_id="1", deck_name="Deck")
    expired.state.phase_start_epoch_ms = game_state.now_epoch_ms() - expired.state.phase_limit_ms - 1
    expired.on_rate(1)
    assert expired.state.boost_charge_progress == 1

    untimed = configured_boost_engine(game_state)
    no_timeout = {"mode": game_state.TIMER_POLICY_NO_TIMEOUT}
    untimed.sync_visible_question_surface(card_id="2", deck_name="Deck", timer_policy=no_timeout)
    untimed.sync_visible_answer_surface(card_id="2", deck_name="Deck", timer_policy=no_timeout)
    untimed.on_rate(2)
    assert untimed.state.boost_charge_progress == 1

    free_first = configured_boost_engine(game_state)
    free_first.sync_visible_question_surface(card_id="3", deck_name="Deck", review_entry=True)
    assert free_first.card.question_free is True
    free_first.sync_visible_answer_surface(card_id="3", deck_name="Deck")
    free_first.on_rate(4)
    assert free_first.state.boost_charge_progress == 1


def test_completed_cards_earn_boost_progress_even_when_visuals_are_hidden() -> None:
    game_state = load_game_state()
    engine = configured_boost_engine(game_state)
    engine.state.visuals_enabled = False
    engine.sync_visible_question_surface(card_id="4", deck_name="Deck")
    engine.sync_visible_answer_surface(card_id="4", deck_name="Deck")
    engine.on_rate(3)
    assert engine.state.boost_charge_progress == 1


def test_boost_timer_bar_uses_total_remaining_time_without_a_transition_jump() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")

    assert "const totalRatio = baseLimit > 0 ? remaining / baseLimit : 0;" in overlay
    assert "const totalRatio = timer.baseTotal > 0 ? remaining / timer.baseTotal : 0;" in overlay
    assert overlay.count("const overflow = Math.max(0, totalRatio - 1);") == 2
    assert "progress = clamp(totalRatio, 0, 1);" in overlay
    assert "baseProgress = clamp(normalRatio, 0, 1);" in overlay
    assert "baseProgress: Number(timer?.baseProgress ?? progress)" in overlay
    assert "const displayBaseProgress = normalRatio;" in overlay
    assert "float overflowArc = clamp(u_overflow_progress, 0.0, 1.0);" in overlay

    assert "const totalRatio = boostActive ? boostRatio : baseProgress;" not in overlay
    assert "progress = clamp(boostActive ? boostRatio : normalRatio, 0, 1);" not in overlay
    assert "baseProgress: Boolean(timer?.boostActive) ? 0" not in overlay
    assert "u_overflow_turns >= 1.0 ? 1.0" not in overlay


def test_timer_track_has_no_misaligned_container_ring() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    css = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")

    assert "float track = ring * 0.18;" in overlay
    assert "inset 0 0 24px rgba(255,255,255,0.08)" not in css
    assert "no second gray ring peeks around the timer" in css
    assert "rgba(9, 14, 28, 0.96) 0 54.75px" in css
    assert "rgba(9, 14, 28, 0) 57.75px" in css
    assert "rgba(9, 14, 28, 0) 100%" in css
    assert "rgba(9, 14, 28, 0.96) 73.8px" not in css
    assert ".acg-timer-hero.webgl-timer-ready::before" in css
    assert "inset: 4.2px;" in css
    assert "final 3px are a soft antialiasing fade" in css
    assert ".appearance-card .acg-timer-hero.webgl-timer-ready" in css


def test_whats_new_is_direct_and_uses_real_interface_images() -> None:
    dialog = (ADDON_ROOT / "whats_new_dialog.py").read_text(encoding="utf-8")
    reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")

    assert 'WHATS_NEW_VERSION = "2.0"' in dialog
    assert 'WHATS_NEW_VERSION = "2.0"' in reviewer
    assert 'ANKIWEB_BASELINE_VERSION = "1.21"' in dialog
    assert "Time Boost is now the default" in dialog
    assert "I added this because I found myself cheating by using Pause and Undo" in dialog
    assert '("•  NO PAUSE"' in dialog
    assert '("•  NO UNDO"' in dialog
    assert 'content.addWidget(_label("Boosts ⚡"' in dialog
    assert "are off by default, but can be turned on to counteract the urge to cheat" in dialog
    assert "Hover over the Boost bank to reveal them and toggle them on or off" in dialog
    assert "Boosts ⚡ give you a limited way to add time" in dialog
    assert "New runs start with 3 of 5 Boosts" in dialog
    assert "Legacy Points is still available" in dialog
    assert '"boosts.png"' in dialog
    assert '"fusion-248.png"' in dialog
    assert '"singularity-248.png"' in dialog
    assert '"crystal-53.png"' in dialog
    assert 'f"{title}  ·  {count}"' not in dialog
    assert "QScrollArea" in dialog
    assert "QWebEngine" not in dialog
    assert "QMovie" not in dialog
    paint_event = dialog.split("def paintEvent", 1)[1].split("def _instruction", 1)[0]
    assert "self._pixmap.scaled" not in paint_event
    assert "painter.drawPixmap(target, self._pixmap, source)" in paint_event


def test_release_images_have_final_crop_sizes() -> None:
    expected = {
        "boosts.png": (1280, 720),
        "fusion-248.png": (1280, 720),
        "singularity-248.png": (1280, 720),
        "crystal-53.png": (1280, 720),
    }
    for filename, size in expected.items():
        path = ADDON_ROOT / "whats_new_assets" / filename
        assert path.is_file()
        with Image.open(path) as image:
            assert image.size == size


def test_ankiweb_materials_reference_the_2_0_release() -> None:
    preview = (ANKIWEB_ROOT / "actual-ui-preview.html").read_text(encoding="utf-8")
    description = (ANKIWEB_ROOT / "ankiweb-description.html").read_text(encoding="utf-8")
    script = (ANKIWEB_ROOT / "FULL_RELEASE_SCRIPT.md").read_text(encoding="utf-8")

    assert 'href="../speed-streak-addon-v2.0/web/overlay.css"' in preview
    assert 'src="../speed-streak-addon-v2.0/web/overlay.js"' in preview
    assert 'shortcutBindings: { pause: "P", unpause: "U", boost: "C" }' in preview
    assert 'if (preview === "boost") document.body.classList.add("show-boost")' in preview
    assert 'document.documentElement.style.zoom = String(captureScale)' in preview
    for filename in ("boosts.png", "fusion-248.png", "singularity-248.png", "crystal-53.png"):
        assert f"/speed-streak-addon-v2.0/whats_new_assets/{filename}" in description
        assert filename in script
    assert "Complete cards to earn Boosts" in description
    assert "Legacy Points" in description
    assert "found myself cheating by using Pause and Undo" in description
    assert "are off by default" in description
    assert "Boosts ⚡" in description
    assert "3 Boosts" in description and "up to <strong>5</strong>" in description
    assert "Fusion · 248" not in description
    assert "Singularity · 248" not in description
    assert "Crystal Reactor · 53" not in description
    assert "no generated artwork is used" in script.lower()


def test_2_0_keeps_safe_time_boost_defaults() -> None:
    config = json.loads((ADDON_ROOT / "config.json").read_text(encoding="utf-8"))
    assert config["gameplay_mode"] == "time_boost"
    assert config["no_pause_mode"] is False
    assert config["no_undo_mode"] is False
    assert config["boost_seconds"] == 10
    assert config["max_boost_charges"] == 5
    assert config["starting_boost_charges"] == 3
    assert config["cards_per_boost_charge"] == 10
    assert config["shortcut_bindings"]["boost"] == "C"
