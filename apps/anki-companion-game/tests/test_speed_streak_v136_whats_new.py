from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import sys
import types

from PIL import Image


ADDON_ROOT = Path(__file__).resolve().parents[1] / "speed-streak-addon-v1.36"
ANKIWEB_ROOT = ADDON_ROOT.parent / "ankiweb-v1.36"


def test_whats_new_covers_the_published_ankiweb_upgrade_without_overwriting_defaults() -> None:
    dialog = (ADDON_ROOT / "whats_new_dialog.py").read_text(encoding="utf-8")

    assert 'WHATS_NEW_VERSION = "1.36"' in dialog
    assert 'ANKIWEB_BASELINE_VERSION = "1.21"' in dialog
    assert "Singularity" in dialog
    assert "Time Boost uses charges instead of points" in dialog
    assert "No Pause, No Undo" in dialog
    assert "Crystal Reactor" in dialog
    assert "previous point and multiplier system is now called Legacy Points" in dialog
    assert '"time-boost-actual.png"' in dialog
    assert '"visual-options-actual.png"' in dialog

    config = json.loads((ADDON_ROOT / "config.json").read_text(encoding="utf-8"))
    assert config["gameplay_mode"] == "time_boost"
    assert config["no_pause_mode"] is False
    assert config["no_undo_mode"] is False
    assert config["visual_mode"] == "sphere"


def test_v136_engine_uses_time_boost_as_its_new_default() -> None:
    package_name = "speed_streak_v136_default_test"
    package = types.ModuleType(package_name)
    package.__path__ = [str(ADDON_ROOT)]
    sys.modules[package_name] = package
    for module_name in ("feedback_catalog", "game_state"):
        qualified_name = f"{package_name}.{module_name}"
        spec = importlib.util.spec_from_file_location(qualified_name, ADDON_ROOT / f"{module_name}.py")
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified_name] = module
        spec.loader.exec_module(module)
    game_state = sys.modules[f"{package_name}.game_state"]

    state = game_state.CompanionState()
    assert state.gameplay_mode == game_state.GAMEPLAY_MODE_TIME_BOOST
    assert state.no_pause_mode is False
    assert state.no_undo_mode is False


def test_whats_new_is_one_time_lazy_and_can_be_reopened() -> None:
    reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")

    assert 'WHATS_NEW_VERSION = "1.36"' in reviewer
    assert 'config.get("whats_new_seen_version", "")' in reviewer
    assert '"whats_new_seen_version": self._whats_new_seen_version' in reviewer
    assert "QTimer.singleShot(900, self._show_whats_new_if_needed)" in reviewer
    assert "from .whats_new_dialog import show_whats_new_dialog" in reviewer
    assert 'menu.addAction(f"What’s New in {WHATS_NEW_VERSION}")' in reviewer
    assert 'self._open_settings_dialog(settings_page="gameplay")' in reviewer


def test_dialog_stays_lightweight_and_small_screens_can_scroll() -> None:
    dialog = (ADDON_ROOT / "whats_new_dialog.py").read_text(encoding="utf-8")

    assert "QScrollArea" in dialog
    assert "setWidgetResizable(True)" in dialog
    assert "QPixmap" in dialog
    assert "QWebEngine" not in dialog
    assert "QMovie" not in dialog


def test_shared_ankiweb_visuals_are_packaged_and_have_consistent_dimensions() -> None:
    asset_sizes = {
        "time-boost-actual.png": (420, 285),
        "visual-options-actual.png": (760, 500),
    }
    for name, expected_size in asset_sizes.items():
        path = ADDON_ROOT / "whats_new_assets" / name
        assert path.is_file()
        with Image.open(path) as image:
            assert image.size == expected_size

    description = (ANKIWEB_ROOT / "ankiweb-description.html").read_text(encoding="utf-8")
    for name in asset_sizes:
        assert f"/whats_new_assets/{name}" in description
    assert "Time Boost uses charges instead of points" in description
    assert "Settings → Gameplay" in description


def test_screenshots_are_rendered_from_the_actual_v136_interface() -> None:
    preview = (ANKIWEB_ROOT / "actual-ui-preview.html").read_text(encoding="utf-8")

    assert 'href="../speed-streak-addon-v1.36/web/overlay.css"' in preview
    assert 'src="../speed-streak-addon-v1.36/web/overlay.js"' in preview
    assert 'gameplayMode: "time_boost"' in preview
    assert 'query.get("visual") || (preview === "visuals" ? "singularity" : "sphere")' in preview
    assert "generated" not in preview.lower()
    assert not (ANKIWEB_ROOT / "source").exists()
    assert not (ANKIWEB_ROOT / "render_ankiweb_visuals.py").exists()


def test_developer_preferences_can_be_opened_with_a_seven_second_left_click_hold() -> None:
    settings = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")

    assert 'QKeySequence("Ctrl+Shift+W")' in settings
    assert "self.developer_hold_timer.setInterval(7000)" in settings
    assert "self._install_developer_hold_filters()" in settings
    assert "target.installEventFilter(self)" in settings
    assert "application.installEventFilter(self)" not in settings
    assert "QEvent.Type.ChildAdded" in settings
    assert "def cleanup_settings_dialog()" in settings
    assert "QEvent.Type.MouseButtonPress" in settings
    assert "QEvent.Type.MouseButtonRelease" in settings
    assert "QApplication.mouseButtons() & Qt.MouseButton.LeftButton" in settings
    assert "self._set_developer_preferences(True)" in settings


def test_quick_gameplay_switches_and_forgiving_hover_controls_are_available() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    styles = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")
    reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")

    assert 'id="acgSwitchToLegacy"' in overlay
    assert 'id="acgSwitchToTimeBoost"' in overlay
    assert 'bindGameplayModeSwitch("acgSwitchToLegacy", "legacy")' in overlay
    assert 'bindGameplayModeSwitch("acgSwitchToTimeBoost", "time_boost")' in overlay
    assert 'message.startswith("speed-streak:set-gameplay-mode:")' in reviewer
    assert "scheduleEconomyHoverClose" in overlay
    assert "distanceFromPointToRect(event.clientX, event.clientY" in overlay
    assert ") <= 42" in overlay
    assert "}, 520);" in overlay
    assert ".acg-boost-hover-zone.hover-open .acg-boost-hover-controls" in styles
    assert ".acg-legacy-economy.hover-open .acg-legacy-hover-controls" in styles


def test_external_window_presets_open_smoothly_and_close_on_pane_exit() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    styles = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")

    assert "External window presets" in overlay
    assert "Save and restore the positions of Anki and the external Speed Streak window." in overlay
    assert "Restore the original Anki and Speed Streak external-window positions" in overlay
    assert "openWindowPositionPresets();" in overlay
    assert 'window.addEventListener("blur"' in overlay
    assert "scheduleWindowPresetClose();" in overlay
    assert "opacity: 0;" in styles
    assert "transform: translateY(-7px) scale(.97);" in styles
    assert ".acg-window-presets.open .acg-window-presets-panel" in styles


def test_visual_selector_offers_contextual_color_customization() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
    settings = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")

    assert 'id="acgVisualColorShortcut"' in overlay
    assert 'colorShortcut.classList.toggle("hidden", choice === "number_only")' in overlay
    assert "speed-streak:open-settings:visual-colors:" in overlay
    assert 'message.startswith("speed-streak:open-settings:visual-colors:")' in reviewer
    assert 'settings_page="visuals", color_visual=visual' in reviewer
    assert "VisualColorCustomizerDialog(self, focus_visual=focus_visual)" in settings
    assert not (ADDON_ROOT / "whats_new_assets" / "01-time-boost.png").exists()
