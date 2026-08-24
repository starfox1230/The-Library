from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types


sys.dont_write_bytecode = True
ADDON_ROOT = Path(__file__).resolve().parents[1] / "speed-streak-addon-v1.36"


def load_visual_colors():
    package_name = "speed_streak_v136_visual_editor_tests"
    package = types.ModuleType(package_name)
    package.__path__ = [str(ADDON_ROOT)]
    sys.modules[package_name] = package
    for module_name in ("visual_mode", "visual_colors"):
        qualified_name = f"{package_name}.{module_name}"
        spec = importlib.util.spec_from_file_location(
            qualified_name,
            ADDON_ROOT / f"{module_name}.py",
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified_name] = module
        spec.loader.exec_module(module)
    return sys.modules[f"{package_name}.visual_colors"]


def test_legacy_palette_migrates_to_each_visual_independently() -> None:
    colors = load_visual_colors()
    palettes = colors.normalize_visual_color_palettes(
        None,
        legacy_colors={"core": "#112233", "crystal": "#445566", "red": "#aa0000"},
    )

    assert palettes["sphere"] == {"core": "#112233", "red": "#aa0000"}
    assert palettes["crystal_reactor"] == {"crystal": "#445566", "red": "#aa0000"}
    assert palettes["lightweight_rows"] == {"red": "#aa0000"}
    assert palettes["singularity"] == {"core": "#112233", "red": "#aa0000"}


def test_saved_visual_palettes_remain_independent() -> None:
    colors = load_visual_colors()
    palettes = colors.normalize_visual_color_palettes(
        {
            "sphere": {"green": "#11aa33"},
            "crystal_reactor": {"green": "#77cc99"},
            "lightweight_rows": {"green": "#558866"},
            "singularity": {"green": "#00ffaa"},
        }
    )

    assert colors.palette_for_visual(palettes, "sphere")["green"] == "#11aa33"
    assert colors.palette_for_visual(palettes, "crystal_reactor")["green"] == "#77cc99"
    assert colors.palette_for_visual(palettes, "brick")["green"] == "#558866"
    assert colors.palette_for_visual(palettes, "singularity")["green"] == "#00ffaa"


def test_explicitly_reset_visual_does_not_fall_back_to_legacy_colors() -> None:
    colors = load_visual_colors()
    assert colors.palette_for_visual({}, "sphere", legacy_colors={"red": "#aa0000"}) == {}


def test_independent_palettes_are_loaded_saved_and_exported_for_the_active_visual() -> None:
    reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
    settings = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")

    assert 'config.get("visual_color_palettes")' in reviewer
    assert '"visual_color_palettes": {' in reviewer
    assert '"visualColorPalettes": {' in reviewer
    assert "palette_for_visual(" in reviewer
    assert "visual_color_palettes={" in settings
    assert "self.visual_color_palettes = normalize_visual_color_palettes(palettes)" in settings


def test_editor_is_visual_first_and_protects_unsaved_changes() -> None:
    dialog = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")
    crystal_modes = (ADDON_ROOT / "crystal_color_mode.py").read_text(encoding="utf-8")

    assert 'class VisualColorCustomizerDialog(QDialog):' in dialog
    assert '(VISUAL_MODE_CRYSTAL_REACTOR, "Crystal")' in dialog
    assert '(VISUAL_MODE_SPHERE, "Satellite")' in dialog
    assert '(VISUAL_MODE_LIGHTWEIGHT_ROWS, "Brick")' in dialog
    assert '(VISUAL_MODE_SINGULARITY, "Singularity")' in dialog
    assert '"Save"' in dialog
    assert '"Discard"' in dialog
    assert '"Cancel"' in dialog
    assert 'setEscapeButton(keep_button)' in dialog
    assert "Choose a visual to edit" not in dialog
    assert "This does not switch the visual used during review" not in dialog
    assert "def reject(self) -> None:" in dialog
    assert 'elif self.kind == "brick":' in dialog
    assert 'elif self.kind == "singularity":' in dialog
    assert "painter.drawLine(\n            QLineF(" in dialog
    assert 'CRYSTAL_COLOR_MODE_ICE, "Ice"' not in crystal_modes


def test_editor_rows_are_flat_and_separated_instead_of_nested_cards() -> None:
    dialog = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")
    editor = dialog.split("class VisualColorCustomizerDialog", 1)[1].split(
        "class SidebarSwitch", 1
    )[0]

    assert 'QFrame[visualColorRow="true"]' in editor
    assert "background: transparent;" in editor
    assert "border-radius: 0;" in editor
    assert 'QFrame[visualColorSeparator="true"]' in editor
    assert "self._add_separator()" in editor
    assert "POPUP_DIALOG_STYLESHEET" not in editor


def test_visuals_page_removes_the_obsolete_color_preview() -> None:
    dialog = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")
    appearance = dialog.split("def _build_appearance_section", 1)[1].split(
        "def _build_actions_section", 1
    )[0]

    assert 'QLabel("Color Preview"' not in appearance
    assert '"Ratings (shared)"' not in appearance
    assert 'ModernSurface("preview", frame)' not in appearance
    assert 'ModernButton("Choose Theme"' in appearance
    assert 'ModernButton("Edit Colors"' in appearance


def test_timer_context_and_controller_haptics_icon_are_present() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    styles = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")
    reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")

    assert 'id="acgTimerContextZone"' in overlay
    assert 'id="acgAdjustTimers"' in overlay
    assert 'pycmd("speed-streak:open-settings:timers")' in overlay
    assert 'message == "speed-streak:open-settings:timers"' in reviewer
    assert 'settings_page="timers"' in reviewer
    assert 'pointerIsNearTimerContext(event.clientX, event.clientY)' in overlay
    assert '.acg-timer-context-zone.open .acg-timer-context' in styles
    zone_style = styles.split(".acg-timer-context-zone", 1)[1].split("}", 1)[0]
    open_zone_style = styles.split(".acg-timer-context-zone.open {", 1)[1].split("}", 1)[0]
    context_style = styles.split(".acg-timer-context {", 1)[1].split("}", 1)[0]
    assert "pointer-events: auto;" in zone_style
    assert "height: 150px;" in zone_style
    assert "height: 150px;" in open_zone_style
    assert "height: 190px;" not in open_zone_style
    assert "top: 101px;" in context_style
    assert "M17.32 5H6.68" in overlay
    assert 'viewBox="-3 0 30 24"' in overlay
