from __future__ import annotations

from pathlib import Path


ADDON_ROOT = Path(__file__).resolve().parents[1] / "speed-streak-addon-v1.36"


def test_satellite_orbits_are_uploaded_only_when_the_scene_changes() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    draw_frame = overlay.split("function drawWebglFrame(renderer, timestamp = performance.now())", 1)[1].split(
        "function stopWebglOrbit()", 1
    )[0]

    assert "function uploadWebglSatellites(renderer, satellites, signature)" in overlay
    assert "renderer.orbitSignature === signature" in overlay
    assert "gl.bufferData(gl.ARRAY_BUFFER, values, gl.STATIC_DRAW);" in overlay
    assert "uploadWebglSatellites(renderer, satellites, signature);" in overlay
    assert "attribute vec3 a_orbit;" in overlay
    assert "uniform float u_time;" in overlay
    assert "float theta = a_orbit.x + (u_time * a_orbit.z);" in overlay
    assert "new Float32Array" not in draw_frame
    assert "gl.bufferData" not in draw_frame
    assert "satellites.forEach" not in draw_frame


def test_singularity_defaults_to_balanced_without_overwriting_an_active_choice() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    settings = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")

    assert 'if (visualMode === "singularity") return 1;' in overlay
    assert 'if (visualMode === "sphere") return 1;' in overlay
    assert "choice === getVisualMode(state.data || {})" in overlay
    assert "currentVisualResourceLevel(state.data || {}, choice)" in overlay
    assert "RENDER_MODE_LOW_RESOURCE" in settings
    assert "self.controller.render_mode = RENDER_MODE_LOW_RESOURCE" in settings
    assert "getattr(self.controller, \"visual_mode\", VISUAL_MODE_SPHERE) != VISUAL_MODE_SINGULARITY" in settings


def test_satellite_canvas_tracks_the_visible_viewport_instead_of_the_full_scene() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")

    assert "function configureWebglOrbitViewport(renderer, canvas, bounds, sceneScale)" in overlay
    assert "Number(bounds?.width || 1) / scale" in overlay
    assert "Number(bounds?.height || 1) / scale" in overlay
    assert "width * dpr * bufferScale" in overlay
    assert "height * dpr * bufferScale" in overlay
    assert "configureWebglOrbitViewport(renderer, renderer.canvas" in overlay


def test_empty_and_suspended_visuals_do_not_keep_animation_frames_running() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    styles = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")

    assert "function visualMotionSuspended()" in overlay
    assert "renderer?.satelliteCount > 0" in overlay
    assert "&& !visualMotionSuspended()" in overlay
    assert "isCrystalRotationEnabled(state.data) && !motionSuspended" in overlay
    assert 'sidebar.classList.toggle("motion-suspended", visualMotionSuspended());' in overlay
    assert ".speed-streak-sidebar.motion-suspended .acg-energy-disc" in styles
    assert "animation-play-state: paused !important;" in styles


def test_fusion_keeps_zooming_out_while_classic_preserves_ankiweb_sizing() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")

    assert 'minScale: sphereMode === "classic" ? 0.42 : sphereMode === "consolidate" ? 0.14 : 0.10' in overlay
    assert "Math.max(classicSizing ? 180 : 80" in overlay
    assert "classicSizing: sphereMode === \"classic\"" in overlay
    assert "const coreReadableScale = classicSizing" in overlay
    assert "? 1" in overlay


def test_webgl_satellites_shrink_in_proportion_to_each_scene_zoom() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    draw_frame = overlay.split("function drawWebglFrame(renderer, timestamp = performance.now())", 1)[1].split(
        "function stopWebglOrbit()", 1
    )[0]

    assert "const sceneScale = clamp(Number(renderer.bufferScale || 1), 0.02, 1);" in draw_frame
    assert "gl.uniform1f(renderer.pixelRatioLocation, dpr * sceneScale);" in draw_frame
    assert "gl.uniform1f(renderer.pixelRatioLocation, dpr);" not in draw_frame


def test_satellite_viewport_redraws_when_its_actual_field_changes_size() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")

    assert "visualFieldResizeObserver: null" in overlay
    assert 'const visualField = document.getElementById("acgField");' in overlay
    assert "state.visualFieldResizeObserver.observe(visualField);" in overlay
    assert "function scheduleVisualViewportRedraw()" in overlay
    assert "state.visualResizeFrame = window.requestAnimationFrame" in overlay
    assert "renderRings(colors, data);" in overlay


def test_satellite_center_stays_readable_as_the_orbits_zoom_out() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    styles = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")

    assert "const minimumReadableCorePixels = 68;" in overlay
    assert "const projectedCorePixels = coreBasePixels * sceneScale;" in overlay
    assert 'scene.style.setProperty("--core-readable-scale", `${coreReadableScale}`);' in overlay
    assert "scale(var(--core-readable-scale, 1))" in styles


def test_retired_milestone_mode_is_kept_only_as_internal_compatibility_code() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    styles = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")
    sphere_mode = (ADDON_ROOT / "sphere_mode.py").read_text(encoding="utf-8")

    assert 'label: "Milestone Rings"' not in overlay
    assert "const MILESTONE_RING_CARDS = 50;" in overlay
    assert "const completedRingCount = Math.floor(colors.length / MILESTONE_RING_CARDS);" in overlay
    assert "const liveColors = colors.slice(completedRingCount * MILESTONE_RING_CARDS);" in overlay
    assert "function buildMilestoneRingsMarkup" in overlay
    assert 'ringIndex % 2 === 0 ? " clockwise" : " counterclockwise"' in overlay
    assert "function syncMilestoneLiveTrack" in overlay
    assert 'if (!sameCompletedRings)' in overlay
    assert "function spawnMilestoneRingConsolidation" in overlay
    assert 'spawnMilestoneFlare("major")' in overlay
    assert 'spawnMilestoneFlare("apex")' in overlay
    assert 'sphereMode === "classic"' in overlay
    assert ".acg-milestone-ring" in styles
    assert "acg-milestone-ring-spin-reverse" in styles
    assert ".acg-milestone-ring.counterclockwise" in styles
    assert ".acg-satellite.milestone-consolidating" in styles
    assert 'SPHERE_MODE_MILESTONE = "milestone"' in sphere_mode
    assert '(SPHERE_MODE_MILESTONE, "Milestone Rings")' not in sphere_mode
    assert "SPHERE_MODE_MILESTONE, SPHERE_MODE_FUSION" in sphere_mode


def test_fusion_rings_keep_five_live_rows_before_each_50_card_lock() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    styles = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")
    sphere_mode = (ADDON_ROOT / "sphere_mode.py").read_text(encoding="utf-8")

    assert 'label: "Fusion"' in overlay
    assert 'tick: "Fusion"' in overlay
    assert 'return getSphereMode(data) === "classic" ? 0 : 1;' in overlay
    assert "function fusionLiveRowRadius" in overlay
    assert "function buildFusionLiveSatellites" in overlay
    assert "Math.ceil(liveColors.length / 10)" in overlay
    assert "liveColors.slice(rowIndex * 10, (rowIndex + 1) * 10)" in overlay
    assert "function syncFusionLiveRows" in overlay
    assert 'sphereMode === "fusion"' in overlay
    assert '"fusion-consolidating"' in overlay
    assert ".acg-fusion-live-ring" in styles
    assert "@keyframes acg-fusion-consolidate" in styles
    assert 'SPHERE_MODE_FUSION = "fusion"' in sphere_mode
    assert '(SPHERE_MODE_FUSION, "Fusion Rings")' in sphere_mode
    assert "SPHERE_MODE_DEFAULT = SPHERE_MODE_FUSION" in sphere_mode


def test_number_only_is_a_separate_visual_beneath_brick() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    styles = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")
    visual_mode = (ADDON_ROOT / "visual_mode.py").read_text(encoding="utf-8")

    brick_index = overlay.index('data-visual-choice="lightweight_rows"')
    number_index = overlay.index('data-visual-choice="number_only"')
    assert number_index > brick_index
    assert 'number_only: `' in overlay
    assert 'class="acg-visual-mode-icon acg-number-only-icon"' in overlay
    assert '<path d="M12.4 5.5 10.2 26.5M21.8 5.5l-2.2 21M6 12.4h20M5.2 20.1h20"></path>' in overlay
    assert '${VISUAL_MODE_ICONS.number_only}' in overlay
    assert 'sidebar.classList.toggle("orbit-static", enabled && visualsEnabled && numberOnly);' in overlay
    assert 'saveSettings({ visualMode: "number_only", renderMode: "ultra_low_resource", orbitAnimationEnabled: false });' in overlay
    assert ".speed-streak-sidebar.narrow-pane .acg-number-only-choice" in styles
    assert 'VISUAL_MODE_NUMBER_ONLY = "number_only"' in visual_mode
    assert '(VISUAL_MODE_NUMBER_ONLY, "# Only")' in visual_mode


def test_brick_selector_icon_matches_the_aligned_brick_grid() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    icon = overlay.split("lightweight_rows: `", 1)[1].split("`,", 1)[0]

    assert 'class="acg-visual-mode-icon acg-brick-mode-icon"' in icon
    assert icon.count("<rect ") == 16
    assert icon.count('width="5.45" height="4.45" rx=".9"') == 16
    assert 'M4 7h11v7H4z' not in icon


def test_visual_selector_centers_right_hand_actions_but_keeps_stacked_layout_natural() -> None:
    styles = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")
    resource_panel = styles.split(
        ".speed-streak-sidebar .acg-visual-resource-panel {", 1
    )[1].split("}", 1)[0]
    narrow_panel = styles.split(
        ".speed-streak-sidebar.narrow-pane .acg-visual-resource-panel {", 1
    )[1].split("}", 1)[0]

    assert "align-content: center;" in resource_panel
    assert "align-content: start;" in narrow_panel


def test_fusion_additions_reflow_smoothly_and_emit_a_local_shockwave() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    styles = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")

    assert "attribute vec3 a_previous_orbit;" in overlay
    assert "uniform float u_layout_transition;" in overlay
    assert "mix(previousPosition, targetPosition, transition)" in overlay
    assert "renderer.layoutTransitionStartedAt = animateFusionAddition ? performance.now() : 0;" in overlay
    assert "function spawnFusionSatelliteArrival(color)" in overlay
    assert "acg-satellite-arrival-wave" in overlay
    assert "@keyframes acg-satellite-arrival-wave" in styles


def test_fusion_loss_explodes_live_satellites_then_collapses_rings_outside_in() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    styles = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")

    assert "function triggerFusionDemolition(colors)" in overlay
    assert "for (let ringIndex = completedRingCount - 1; ringIndex >= 0; ringIndex -= 1)" in overlay
    assert "const satelliteWaveDuration = Math.max(0, liveRowCount - 1) * 50;" in overlay
    assert "const ringCollapseBase = liveSatellites.length ? satelliteWaveDuration + 760 : 240;" in overlay
    assert 'ringTrack.className = "acg-fusion-demolition acg-fusion-demolition-ring-track";' in overlay
    assert 'ring.className = "acg-fusion-demolition-ring";' in overlay
    assert "triggerFusionDemolition(state.prevColors);" in overlay
    assert "function createFusionDebrisProgram(gl)" in overlay
    assert "function buildFusionDebris(renderer)" in overlay
    assert "function uploadFusionDebris(renderer)" in overlay
    assert "const particlesPerSatellite = 9;" in overlay
    assert "const ember = particleIndex >= 6;" in overlay
    assert "Math.max(0, outerRowIndex - rowIndex) * 0.05" in overlay
    assert "uploadFusionDebris(state.webgl);" in overlay
    assert "gl.drawArrays(gl.POINTS, 0, renderer.debrisCount);" in overlay
    assert "float wedge = max(abs(local.y) - halfWidth" in overlay
    assert "float easedTravel = (1.0 - exp(-4.0 * life))" in overlay
    assert "float gravity = length(a_travel)" in overlay
    assert "float shockRing" not in overlay
    assert "float fireBody" not in overlay
    assert "float starburst" not in overlay
    assert "@keyframes acg-fusion-ring-demolition" in styles
    assert "@keyframes acg-fusion-collapse-trail" in styles
    assert "acg-fusion-demolition-impact" not in overlay
    demolition_keyframes = styles.split("@keyframes acg-fusion-ring-demolition", 1)[1].split(
        "@keyframes acg-milestone-ring-lock", 1
    )[0]
    assert "scale(1.045" not in demolition_keyframes
    assert "blur(" not in demolition_keyframes
    ring_collapse = demolition_keyframes.split(
        "@keyframes acg-fusion-ring-trajectory", 1
    )[0]
    assert "scale(" in ring_collapse
    assert "scale(.97," not in ring_collapse
    assert "rotate(" not in ring_collapse


def test_fusion_demolition_preserves_satellite_and_ring_trajectories() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    styles = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")

    assert "function cssRotationDegrees(node)" in overlay
    assert "new DOMMatrixReadOnly(transform)" in overlay
    assert "renderer.visualTime += clamp(now - renderer.lastFrameAt, 0, 0.08);" in overlay
    assert "state.webgl.demolitionStartedAt = performance.now();" in overlay
    assert "gl.uniform1f(renderer.demolitionElapsedLocation, demolitionElapsed);" in overlay
    assert 'original?.classList.contains("counterclockwise") ? -1 : 1' in overlay
    assert "startAngle: cssRotationDegrees(original)" in overlay
    assert "--ring-end-angle" in overlay
    assert "@keyframes acg-fusion-ring-trajectory" in styles


def test_fusion_loss_freezes_old_scene_until_center_resets_last() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
    styles = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")

    assert "fusionDemolitionActive: false" in overlay
    assert 'const fusionLossIncoming = eventNonceChanged' in overlay
    assert 'if (fusionLossIncoming) handleStateEffects(data);' in overlay
    assert "const holdFusionScene = state.fusionDemolitionActive" in overlay
    assert "const visualStreak = holdFusionScene ? state.prevStreak : streak;" in overlay
    assert "const visualColors = holdFusionScene ? state.prevColors : colors;" in overlay
    assert 'setText("acgStreak", String(visualStreak));' in overlay
    assert "renderRings(visualColors, data);" in overlay
    assert 'core.classList.toggle("failed", !holdFusionScene' in overlay
    assert "if (state.data) render(state.data);" in overlay
    assert ".speed-streak-sidebar.fusion-demolition-active #acgWebglOrbit" in styles
    assert ".speed-streak-sidebar.fusion-demolition-active .acg-core-wrap" in styles
    assert "z-index: 12;" in styles
    assert ".speed-streak-sidebar.fusion-center-resetting .acg-core-wrap" in styles


def test_satellite_selector_describes_styles_instead_of_only_hardware_cost() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")

    assert 'aria-label="Visual options"' in overlay
    assert '>Satellite style</span>' in overlay
    assert 'aria-label="Visual style"' in overlay
    assert '"Satellite style"' in overlay
    assert '"Singularity detail"' in overlay
    assert "The original Speed Streak satellite layout and sizing." in overlay
    assert "The original AnkiWeb satellite layout" not in overlay
    assert '"Crystal motion"' in overlay


def test_visual_selector_uses_measured_guidance_not_unsupported_percentages() -> None:
    overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")

    assert "Estimated at roughly" not in overlay
    assert "comparison baseline" not in overlay
    assert "The original Speed Streak satellite layout and sizing." in overlay
    assert "newer efficient renderer underneath" not in overlay
    assert "This is the default" in overlay
    assert "Idle GPU use is near zero" in overlay
    assert "essentially no continuous GPU use" in overlay


def test_developer_testing_has_fusion_milestone_quick_set_buttons() -> None:
    settings = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")

    assert "for streak_value in (48, 248, 498):" in settings
    assert 'quick_button = ModernButton(str(streak_value), frame)' in settings
    assert "self.apply_test_streak_value(value)" in settings
    assert "def apply_test_streak_value(self, streak: int) -> None:" in settings
    assert "self.test_streak_spin.setValue(int(streak))" in settings
    assert "self.apply_test_streak()" in settings
