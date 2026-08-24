from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ADDON_ROOT = Path(__file__).resolve().parents[1] / "speed-streak-addon-v1.34"


def load_color_mode_module():
    spec = importlib.util.spec_from_file_location(
        "speed_streak_v134_crystal_color_mode",
        ADDON_ROOT / "crystal_color_mode.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_crystal_color_mode_normalization_is_safe_and_backwards_compatible() -> None:
    color_mode = load_color_mode_module()

    assert color_mode.normalize_crystal_color_mode(None) == "ice"
    assert color_mode.normalize_crystal_color_mode("unexpected") == "ice"
    assert color_mode.normalize_crystal_color_mode("RATINGS") == "answer"
    assert color_mode.normalize_crystal_color_mode("monochrome") == "core"
    assert color_mode.crystal_color_mode_label("answer") == "Answer Colors"


def test_v1_34_identity_and_default_preserve_the_existing_ice_visual() -> None:
    manifest = json.loads((ADDON_ROOT / "manifest.json").read_text(encoding="utf-8"))
    config = json.loads((ADDON_ROOT / "config.json").read_text(encoding="utf-8"))
    readme = (ADDON_ROOT / "README.md").read_text(encoding="utf-8")

    assert manifest["name"] == "Speed Streak v1.34"
    assert manifest["package"] == "speed_streak_v1_34"
    assert config["crystal_color_mode"] == "ice"
    assert "preserving the existing Ice Crystal appearance as the default" in readme


def test_crystal_color_setting_round_trips_through_controller_and_settings() -> None:
    reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
    dialog = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")

    assert 'config.get("crystal_color_mode", CRYSTAL_COLOR_MODE_ICE)' in reviewer
    assert '"crystal_color_mode": self.crystal_color_mode' in reviewer
    assert '"crystalColorMode": self.crystal_color_mode' in reviewer
    assert 'data.get("crystalColorMode", self.crystal_color_mode)' in reviewer
    assert "self.crystal_color_mode_combo" in dialog
    assert "CRYSTAL_COLOR_MODE_OPTIONS" in dialog
    assert '"Crystal Color Style"' in dialog
    assert "crystal_color_mode=str(" in dialog


def test_webgl_crystals_use_per_component_facets_without_changing_ice_mode() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")

    assert 'String(data?.crystalColorMode || "ice")' in overlay
    assert 'if (colorMode === "ice") return icePalette;' in overlay
    assert "function coloredCrystalFacetPalette(baseColor)" in overlay
    assert "crystalRatingRgb(colors[index] || data?.lastSatelliteColor || \"blue\", theme)" in overlay
    assert "const cluster = buildCrystalClusterVertices(componentCount, colors, data);" in overlay
    assert 'const answerColorSignature = colorMode === "answer" ? colors.join(",") : "";' in overlay
    assert "scene.dataset.colorMode = colorMode;" in overlay


def test_central_orb_mode_is_monochrome_and_custom_palette_drives_all_modes() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")

    assert "const palette = resolveCustomColors(data?.customColors || {}, data?.appearanceMode || \"midnight\");" in overlay
    assert 'const baseColor = colorMode === "answer"' in overlay
    assert ": theme.core;" in overlay
    assert 'const ratingA = colorMode === "core"' in overlay
    assert 'const ratingB = colorMode === "core"' in overlay
    assert "? palette.core" in overlay
