from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types


sys.dont_write_bytecode = True
ADDON_ROOT = Path(__file__).resolve().parents[1] / "speed-streak-addon-v1.35"


def load_game_state():
    package_name = "speed_streak_v135_visual_color_tests"
    package = types.ModuleType(package_name)
    package.__path__ = [str(ADDON_ROOT)]
    sys.modules[package_name] = package
    for module_name in ("feedback_catalog", "game_state"):
        qualified_name = f"{package_name}.{module_name}"
        spec = importlib.util.spec_from_file_location(
            qualified_name,
            ADDON_ROOT / f"{module_name}.py",
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified_name] = module
        spec.loader.exec_module(module)
    return sys.modules[f"{package_name}.game_state"]


def test_legacy_single_color_crystal_migrates_from_the_old_orb_color() -> None:
    game_state = load_game_state()
    engine = game_state.CompanionGameEngine()

    engine._restore_user_preferences({"custom_colors": {"core": "#1a2b3c"}})

    assert engine.state.custom_colors == {
        "core": "#1a2b3c",
        "crystal": "#1a2b3c",
    }


def test_new_orb_and_crystal_colors_remain_independent() -> None:
    game_state = load_game_state()
    engine = game_state.CompanionGameEngine()

    engine.update_time_limits(
        question_seconds=12,
        answer_seconds=8,
        custom_colors={"core": "#112233", "crystal": "#aabbcc"},
    )

    assert engine.state.custom_colors["core"] == "#112233"
    assert engine.state.custom_colors["crystal"] == "#aabbcc"


def test_native_editor_separates_shared_and_visual_specific_colors() -> None:
    dialog = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")
    labels = (ADDON_ROOT / "crystal_color_mode.py").read_text(encoding="utf-8")

    assert "RATING_COLOR_FIELDS" in dialog
    assert "VISUAL_COLOR_FIELDS" in dialog
    assert '("core", "Sphere: Central Orb"' in dialog
    assert '("crystal", "Crystal: Single Color"' in dialog
    assert 'title = QLabel("Crystal Color Source"' in dialog
    assert 'crystal_color_mode=self.draft_crystal_color_mode' in dialog
    assert 'CRYSTAL_COLOR_MODE_ICE, "Ice"' in labels
    assert 'CRYSTAL_COLOR_MODE_ANSWER, "Rating Colors"' in labels
    assert 'CRYSTAL_COLOR_MODE_CORE, "Single Crystal Color"' in labels
    assert 'elif self.kind == "crystal":' in dialog
    assert "self._paint_crystal(painter, bounds)" in dialog
    assert "swatch = OrbPreviewButton(key, row)" in dialog
    assert 'OrbPreviewButton(color_key, preview)' in dialog


def test_visual_colors_uses_rounding_only_for_complete_color_rows_and_hex_fields() -> None:
    dialog = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")
    color_dialog = dialog.split("class ColorCustomizerDialog", 1)[1].split(
        "class SidebarSwitch", 1
    )[0]

    assert 'card = QWidget(self)' in color_dialog
    assert 'card = ModernSurface("popup_card", self)' not in color_dialog
    assert 'row = QWidget(parent)' in color_dialog
    assert 'self.timer_preview_track = QWidget(card)' in color_dialog
    assert 'self.crystal_mode_combo.setStyleSheet("border-radius: 2px;")' in color_dialog
    assert 'background: rgba(255,255,255,0.08); border-radius: 0; border: none;' in color_dialog
    assert 'QDialog#speedStreakColorPicker QLabel,' in color_dialog
    assert 'background: transparent;' in color_dialog
    assert 'border: none;' in color_dialog


def test_crystal_previews_open_colors_and_select_single_color_mode() -> None:
    dialog = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")
    color_dialog = dialog.split("class ColorCustomizerDialog", 1)[1].split(
        "class SidebarSwitch", 1
    )[0]

    assert 'if key == "crystal":' in color_dialog
    assert 'self.crystal_mode_combo.findData(CRYSTAL_COLOR_MODE_CORE)' in color_dialog
    assert 'self.crystal_single_color_row.setEnabled(True)' in color_dialog
    assert 'swatch.clicked.connect(lambda _checked=False: self.open_color_picker())' in dialog
    assert 'WA_TransparentForMouseEvents' not in dialog


def test_visuals_page_stays_concise_and_hides_the_internal_crystal_combo() -> None:
    dialog = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")

    assert "self.crystal_color_mode_combo.hide()" in dialog
    assert 'preview_title = QLabel("Color Preview"' in dialog
    assert '("Visuals", (("core", "Sphere"), ("crystal", "Crystal")))' in dialog
    assert '("Ratings (shared)",' in dialog
    assert 'ModernButton("Edit Colors"' in dialog
    assert "self.color_value.setText" not in dialog
    assert "Display: {display_label}" not in dialog
    assert "Shared ratings:" not in dialog
    assert "Timer colors:" not in dialog


def test_settings_dialog_does_not_render_the_redundant_hero_header() -> None:
    dialog = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")

    assert 'hero = ModernSurface("hero", card)' not in dialog
    assert 'ModernButton("Close", hero)' not in dialog
    assert "Focused pages, live changes" not in dialog


def test_render_mode_is_owned_by_the_side_panel_resource_chooser() -> None:
    dialog = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")

    assert 'self.render_mode_combo: ScrollSafeComboBox | None = None' in dialog
    assert 'self.render_mode_combo = ScrollSafeComboBox' not in dialog
    assert '"Render mode",' not in dialog
    assert 'getattr(self.controller, "render_mode", RENDER_MODE_WEBGL)' in dialog


def test_window_presets_close_after_a_forgiving_pointer_exit() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")

    assert 'windowPresetsRoot.addEventListener("pointerenter", cancelWindowPresetClose)' in overlay
    assert 'windowPresetsRoot.addEventListener("pointerleave", scheduleWindowPresetClose)' in overlay
    assert 'pointerIsNearWindowPresets(event.clientX, event.clientY)' in overlay
    assert 'const proximity = 34;' in overlay
    assert '}, 420);' in overlay


def test_web_editor_and_webgl_renderer_use_the_dedicated_crystal_color() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    styles = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")

    assert "Shared Rating Colors" in overlay
    assert "Visual-Specific Colors" in overlay
    assert "Crystal Color Source" in overlay
    assert "Single Crystal Color" in overlay
    assert "crystal: crystalRgb(palette.crystal)" in overlay
    assert "const iceBase = crystalRgb(\"#566ed4\")" in overlay
    assert "? palette.crystal" in overlay
    assert ": theme.crystal;" in overlay
    assert "grid-template-columns: 18px 34px minmax(0, 1fr);" in styles
    assert ".acg-color-panel .acg-switch-row" in styles
