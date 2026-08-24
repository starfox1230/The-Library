from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re


ADDON_ROOT = Path(__file__).resolve().parents[1] / "speed-streak-addon-v1.36"


def load_visual_mode_module():
    spec = importlib.util.spec_from_file_location(
        "speed_streak_v136_visual_mode",
        ADDON_ROOT / "visual_mode.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v136_identity_and_upgrade_paths_replace_v135() -> None:
    manifest = json.loads((ADDON_ROOT / "manifest.json").read_text(encoding="utf-8"))
    reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
    installer = (ADDON_ROOT / "install_to_anki.ps1").read_text(encoding="utf-8")
    builder = (ADDON_ROOT / "build_ankiaddon.ps1").read_text(encoding="utf-8")

    assert manifest["name"] == "Speed Streak v1.36"
    assert manifest["package"] == "speed_streak_v1_36"
    assert "speed_streak_v1_35" in manifest["conflicts"]
    assert 'ADDON_DISPLAY_NAME = "Speed Streak v1.36"' in reviewer
    assert '[string]$AddonFolderName = "speed_streak_v1_36"' in installer
    assert '"speed_streak_v1_35"' in installer
    assert '"speed_streak_v1_36.ankiaddon"' in builder


def test_installer_replaces_existing_code_directories_instead_of_nesting_them() -> None:
    installer = (ADDON_ROOT / "install_to_anki.ps1").read_text(encoding="utf-8")
    replace_block = installer.split("if ($_.PSIsContainer) {", 1)[1].split("} else {", 1)[0]

    remove = "Remove-Item -LiteralPath $destination -Recurse -Force"
    copy = "Copy-Item -Path $_.FullName -Destination $destination -Recurse -Force"
    assert "if (Test-Path -LiteralPath $destination)" in replace_block
    assert remove in replace_block
    assert replace_block.index(remove) < replace_block.index(copy)


def test_singularity_is_a_first_class_visual_mode_with_safe_aliases() -> None:
    visual_mode = load_visual_mode_module()

    assert visual_mode.normalize_visual_mode("singularity") == "singularity"
    assert visual_mode.normalize_visual_mode("gravity_core") == "singularity"
    assert visual_mode.normalize_visual_mode("black_hole") == "singularity"
    assert visual_mode.visual_mode_label("singularity") == "Singularity"
    assert ("singularity", "Singularity") in visual_mode.VISUAL_MODE_OPTIONS


def test_inline_selector_uses_a_distinct_gravity_well_icon_and_three_resource_levels() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    icon = overlay.split("singularity: `", 1)[1].split("`,", 1)[0]

    assert 'data-visual-choice="singularity"' in overlay
    assert 'title="Singularity"' in overlay
    assert "VISUAL_MODE_ICONS.singularity" in overlay
    assert '<ellipse cx="16" cy="16" rx="12"' not in icon
    assert 'class="acg-visual-mode-icon acg-singularity-mode-icon"' in icon
    assert '<ellipse cx="16" cy="16" rx="12.4" ry="5.1"' in icon
    assert '<circle cx="16" cy="16" r="6.15" fill="#03050b"' in icon
    assert 'M4.1 18.35c5.15 3.35' in icon
    assert 'M4.2 10.1c5.6-3.2' not in icon
    assert 'label: "Efficient"' in overlay
    assert 'label: "Balanced"' in overlay
    assert 'label: "Full"' in overlay
    assert 'visualMode: "singularity"' in overlay
    assert 'renderMode: level === 0 ? "ultra_low_resource" : level === 1 ? "low_resource" : "webgl"' in overlay


def test_singularity_progression_has_decade_phase_and_apex_transforms() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")

    assert "const decade = Math.floor(streak / 10);" in overlay
    assert "const fifty = Math.floor(streak / 50);" in overlay
    assert "const century = Math.floor(streak / 100);" in overlay
    assert "streak % 50 === 0" in overlay
    assert "streak % 10 === 0" in overlay
    assert "u_fifty" in overlay
    assert "u_century" in overlay
    assert "decadeBand" in overlay
    assert "decadeSegments" in overlay
    assert "phaseRing" in overlay
    assert "apexRing" in overlay
    assert "spokes" in overlay
    assert "shockwave" in overlay


def test_singularity_renderer_caps_work_and_stops_when_not_visible() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")

    assert "Math.min(deviceRatio, 0.78)" in overlay
    assert "Math.min(deviceRatio, 1.05)" in overlay
    assert "Math.min(deviceRatio, 1.45)" in overlay
    assert "Math.min(28," in overlay
    assert "Math.min(48," in overlay
    assert "Math.min(72," in overlay
    assert "renderer.quality === 0 ? 1 / 20 : renderer.quality === 1 ? 1 / 30 : 1 / 60" in overlay
    assert "if (renderer.running && !paused)" in overlay
    assert "function stopSingularityRenderer()" in overlay
    assert "stopSingularityRenderer();" in overlay
    assert "particleValues: []" in overlay
    assert "const values = renderer.particleValues;" in overlay
    assert "values.length = 0;" in overlay
    assert "renderer.particleUpload.set(particleValues, 0);" in overlay
    assert "gl.bufferSubData(" in overlay
    assert "new Float32Array(particleValues)" not in overlay
    assert "gl.drawArrays(gl.POINTS, 0, particleValues.length / 9);" in overlay


def test_singularity_recovers_context_and_releases_resources() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")

    assert 'canvas.addEventListener("webglcontextlost"' in overlay
    assert 'canvas.addEventListener("webglcontextrestored"' in overlay
    assert "event.preventDefault();" in overlay
    assert "function disposeSingularityRenderer(" in overlay
    assert "renderer.resizeObserver?.disconnect?.();" in overlay
    assert "renderer.gl.deleteBuffer(renderer.particleBuffer);" in overlay
    assert "renderer.gl.deleteProgram(renderer.particleProgram);" in overlay
    assert "gl.deleteShader(shader);" in overlay
    assert 'document.addEventListener("visibilitychange"' in overlay
    assert 'window.addEventListener("pagehide"' in overlay


def test_singularity_has_rating_comets_and_failure_debris() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")

    assert "singularityEventColor(data)" in overlay
    assert 'renderer.eventType === "again"' in overlay
    assert 'renderer.eventType === "timeout"' in overlay
    assert "appendSingularityIntakeBurst" in overlay
    assert "const explosion" in overlay
    assert "const capture" in overlay
    assert "const explosionProgress" in overlay
    assert "gl.blendFunc(gl.SRC_ALPHA, gl.ONE);" in overlay


def test_singularity_uses_colorful_bounded_particle_clusters() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")

    assert "function singularityNeonPalette(data)" in overlay
    assert "u_palette_red" in overlay
    assert "u_palette_yellow" in overlay
    assert "u_palette_green" in overlay
    assert "u_palette_blue" in overlay
    assert "const group = Math.floor(index / 3);" in overlay
    assert "const count = quality === 0 ? 9 : quality === 1 ? 15 : 22;" in overlay


def test_singularity_milestones_emit_circle_and_star_outlines() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")

    assert "function appendSingularityDecadeRing" in overlay
    assert "streak % 10 !== 0" in overlay
    assert "function appendSingularityFiftyStar" in overlay
    assert "streak % 50 !== 0" in overlay
    assert "function singularityStarPoint" in overlay
    assert "appendSingularityDecadeRing(values" in overlay
    assert "appendSingularityFiftyStar(values" in overlay


def test_charge_earned_and_spent_animate_between_visual_center_and_bank() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    styles = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")

    assert "function chargeTransferVisualAnchor(data)" in overlay
    assert "function chargeTransferBankTarget(direction)" in overlay
    assert "function spawnChargeTransfer(data, direction)" in overlay
    assert 'includes("charge earned")' in overlay
    assert 'spawnChargeTransfer(data, "earned");' in overlay
    assert 'spawnChargeTransfer(data, "spent");' in overlay
    assert "⚡ Time Boost charge earned" not in overlay
    assert "getBoundingClientRect()" in overlay
    assert "acg-charge-transfer-ring" in styles
    assert "acg-charge-transfer-spark" in styles
    assert "acg-charge-transfer-arrival" in styles
    assert ".acg-singularity-scene > .acg-charge-transfer" in styles
    assert "function chargeTransferOcclusionRadius(data, fieldRect)" in overlay
    assert 'transfer.classList.add("center-occluded")' in overlay
    assert 'transfer.style.inset = "auto"' in overlay
    assert 'transfer.style.setProperty("--charge-visual-x"' in overlay
    assert ".acg-charge-transfer.center-occluded" in styles
    assert "-webkit-mask-image: radial-gradient(" in styles
    transfer_layer = re.search(
        r"\.acg-singularity-scene\s*>\s*\.acg-charge-transfer,?\s*(?:\n|.)*?\{(?P<body>.*?)\}",
        styles,
        flags=re.DOTALL,
    )
    assert transfer_layer is not None
    assert "z-index: 3" in transfer_layer.group("body")
