# Validation — October 30, 2026

Passed on Sterling's Windows machine:

## 0.6 Techno Club and cloud preservation

- Viewed the supplied YouTube Short in the browser: bright rounded particles in broken, rippling loops. Built an original neon ribbon renderer with large kick-driven radial/tangential/depth displacement, glow and a forward travel burst. The reference video was not downloaded or bundled.
- One batched point-sprite draw, default 1,800 particles. GPU pixel test held time fixed and found only about 3.6% of lit interbeat pixels still occupied on the kick, establishing actual spatial movement rather than just more light. Canvas fallback: about 1% retained. Both paths pass pause, reduced motion and disable checks; screenshots inspected for geometry and readable card text.
- Isolated shared-layer Qt WebEngine with a simulated beat at 1920×1080: approximately 60 FPS, p95 16.8 ms, Intel Arc / ANGLE / Direct3D11; all three decorators draw zero animation frames. The 75–250% zoom and independently zoomed answer-bar alignment test passes for the club renderer's software fallback. This is not a new live review/Speed Streak frame-rate measurement.
- The v0.5 cloud shader is unchanged and the original motion fields retain their formulas. Added independent club clock fields. Existing cloud browser and twelve beat/motion tests pass. Anki smoke test covers restoring a saved cloud profile. Installer saves prior preferences once and preserves them on subsequent replacements; generic defaults are packaged as fallback.

## 0.5 stronger beat response and lighter cloud

- Fixed the weak particle response: the shader now consumes the beat pulse for particle brightness, trail length, point size and color accent. Detected kicks also boost forward band clocks and advance a lagged camera target more strongly. The impact control scales the native kick travel/camera response and the visual pulse. No full-screen background flash or whole-cloud amplitude scaling is added.
- Default density falls from 12,000 to 4,200; Economy caps at 2,400. Only heads receive point sprites. Vertex submissions are 12,600 versus 48,000 per frame (74% fewer), independently adjustable through the new particle-count slider. This is a workload reduction, not a measured percentage improvement to live Anki FPS.
- GPU browser regression sampled an otherwise fixed scene at about 9 summed RGB units between beats and 35–36 on a detected kick (about 4×), returning to the baseline after release. A confident predicted beat without a new onset sampled about 29. Impact 0 removes the pulse; the density control changes the actual GPU particle count. Pointer movement does not alter the scene. Added a renderer-output probe for monotonic clocks/camera across a falling-rate correction.
- Twelve beat/motion tests pass, including kick acceleration/release at constant loudness and impact-0 suppression of rhythmic motion. Shared Qt WebEngine at 1920×1080, Intel Arc / ANGLE / Direct3D11: about 60 FPS, p95 16.8 ms, zero foreground animation frames. Anki library settings/lifecycle, independent 75–250% card zoom and liquid browser regression pass.
- Installed 0.5 with Anki closed, preserving the existing metadata. This turn does not establish a new live Anki FPS measurement or subjective synchronization by ear. The normal-session results recorded under 0.4.1 are historical.

## 0.4.1 live Anki integration

- Installed with Anki closed, then opened the existing profile and one ungraded review question with Speed Streak present. No answer was revealed or graded. Confirmed live music signal from TOSHIBA-TV in the settings/review meter and tempo estimates; this establishes capture, not correctness of the musical tempo or perceived synchronization.
- Added one native Qt WebEngine background under transparent existing Anki pages. Foreground pages report `decorator` and zero rendered frames. They retain text, halos and button handlers; the shared surface reports ANGLE / Intel Arc / Direct3D11. Static decorators receive configuration/geometry updates and an optional 4 Hz HUD stream instead of 30 Hz audio streams. The backdrop is lowered only when shown. Disabling/leaving review restores saved page background colors; profile close disposes the background.
- Early live builds, including the shared layer before the final communication/layout changes, measured about 40–47 FPS when unattended. The final build with the user's original hidden-meter preference measured 53–57 FPS in consecutive samples, with p95 intervals still about 33 ms and JS submission about 0.16–0.18 ms. These are short sequential observations, not a controlled A/B test or a guarantee of sustained 60 FPS. Desktop screenshot/input inspection lowered readings considerably. No claim that all remaining stutter is solved.
- Live View → Zoom In changed the card page from 1.0 to 1.1 while the background remained at 1.0; Ctrl+0 restored the card. Fullscreen entry/exit also worked. The floating Speed Streak window remains independent. The isolated 75–250% Qt zoom/pixel test passes. The shared-layer Qt benchmark at 1920×1080 measured about 60 FPS, p95 16.8 ms, with all three foreground pages drawing zero animation frames.
- Particle browser tests now cover switching into transparent decoration-only mode, no foreground animation, background FPS propagation and restoring per-pane GPU rendering. GPU/liquid/Canvas regressions, ten motion/beat tests, Anki settings/lifecycle smoke, native filter bank and standalone service checks pass. GPU readback tests explicitly repaint before reading pixels; normal GPU contexts use disposable buffers.
- Optional `diagnostics: true` config writes only renderer metrics, native sizes, zoom and graphics API to local `user_files/performance.jsonl`; no card text or audio is logged. Diagnostics is off by default and was removed from the user's configuration after testing. Original palette, intensity, motion, audio settings, hidden meter and card zoom were preserved. The shared layer is enabled.

## 0.4 particle cloud and performance comparison

- Read the complete supplied transcript and identified the [creator's tutorial](https://www.elekktronaut.com/tutorials/audioreactive-particle-cloud-new). Implemented original age-colored GPU line/point particles, forward-integrated band clocks and a kick-count camera target with lag. The exact TouchDesigner compute simulation and post-processing are not ported.
- Edge on ANGLE / Intel Arc / Direct3D11: approximately 60.0 FPS, p95 intervals 16.8 ms. Isolated native Qt WebEngine with three panes in a 1920×1080 hidden window: all three approximately 60.0 FPS, p95 16.7/16.7/16.8 ms. Mean JS submission cost was about 0.09–0.16 ms per pane; this excludes GPU and compositor cost. These tests load no Anki collection or other add-ons. Live review + Speed Streak + TV performance remains a user-session check.
- Cloud browser regression: GPU initialized, continued drawing, no pointer control, no movement from raw bass when integrated clocks are fixed, forward-clock updates move particles, switching between cloud and liquid works without JS errors. Screenshot inspected for trails, age colors and text visibility.
- Ten motion/beat unit tests pass, including monotonically increasing particle and camera clocks during repeated loud/quiet kicks and independent spectral-group speeds.
- Native C# filter-bank test uses the same BandBank class as WASAPI with offline 60/500/4000 Hz tones. It separates low/mid/high energy without playing sound. The live output probe identified TOSHIBA-TV but was silent during this check, so current real-music capture/band levels were inconclusive; previous versions confirmed that output's real music capture.
- Standalone smoke test: loopback-only service starts, audio/motion state and all assets load, unlisted files return 404, Stop shuts down the server and helper cleanly. No browser window is opened by the automated smoke test.
- Anki library settings/lifecycle checks pass; Qt's 75–250% zoom test remains pixel-identical and its answer-bar slice aligns. Static repaint checks wait for completed render frames to avoid sampling a pending repaint. Liquid GPU and Canvas regressions continue to pass.
- The normal running Anki installation is not hot-patched; reinstall with Anki closed activates the update.

## 0.3 liquid wall

- Replaced the dance-floor scene with an original WebGL liquid field: three-octave domain warping, broad saturated color folds, a restrained luminous crease and bass-driven displacement. No pointer or mouse handlers. Automatic Canvas 2D fallback uses seven fluid ribbons and cached color pools.
- Three new MusicMotion tests verify that steady music advances the shared flow clock more than three times faster than silence, bass opens the folds, an attack settles back to quiet drift, and repeated timestamps do not advance the clock twice. Five existing beat tests also pass.
- Browser suites run on both WebGL and explicitly forced Canvas fallback: real rendering, musical light response, letter halos, still/reduced-motion behavior, disabling and aligned pane slices. Both paths pass without JavaScript errors. The new renderer screenshot was visually inspected for flowing folds, saturated colors, dark troughs and legible card text.
- Actual Qt WebEngine 75–250% zoom regression passes with the new renderer and resolution budget. The independently zoomed answer-bar slice remains aligned (average pixel-channel difference below 0.005 in the software test).
- Installed Anki library settings/lifecycle smoke test passes with the new shared motion driver. The Windows audio capture path is unchanged. Perceived musical movement and live TV frame rate need hands-on confirmation after reinstalling this version.

## 0.2.1 zoom and rendering follow-up

- Identified a coordinate mismatch: Qt window dimensions were combined with browser CSS viewport dimensions, which change under Anki page zoom. The bridge now sends native pane dimensions and display density; background buffers and transforms use those native coordinates.
- Actual Qt WebEngine (from the installed Anki environment), isolated off-record page: 75/100/125/150/200/250% page zoom produced pixel-identical background snapshots while card text grew by more than 3×. A differently zoomed answer-bar slice differed by only 0.0037 on average per pixel channel from the corresponding full scene. The test uses a hidden native window and no Anki profile or collection. The software-rendered test environment logged GLES fallback messages.
- Browser regression checks confirm no radial gradients are created during steady-state animation after cache warm-up. Three 256×256 glow textures and a bounded 384×512-or-smaller vignette are composited instead. Toolbar button backdrop blur was removed; renderer health checks use a short boolean probe before sending any source.
- Qt library smoke checks verify that native pane width, height, offset and DPR reach the renderer. Existing audio, still-mode, halo, toolbar-alignment and beat tests continue to pass.
- These are rendering-work reductions, not a measured claim of improved live Anki FPS on the TV. Normal-review smoothness remains a hands-on check after reinstall.

## 0.2 follow-up

- The user reported imperceptible music response. A live probe confirmed changing system audio on **TOSHIBA-TV (5- HD Audio Driver for Display Audio)**. The old mapping made very small visual changes. The new mapping uses strong attack response, adaptive gain for quiet sources, visible edge arcs and a live device/signal meter.
- Automatic output selection captured audible features in 79 of 80 snapshots in an eight-second real-audio probe (the first snapshot occurs before startup). A subsequent probe detected 27 attacks and acquired a tempo hypothesis. This confirms the pipeline is receiving real HDMI audio, not that the musical tempo estimate is always correct.
- Five tracker tests pass, including quiet music with eighth-note attacks. Phase fitting now evaluates strong anchors and offbeat subdivisions instead of anchoring every hypothesis to the latest attack.
- Browser regression checks measured the same scene at **67.7 → 152.8** average RGB sum on a sound attack (more than twice the summed pixel brightness), replacing the earlier barely visible response. Card and answer-bar slices of the shared scene agree to within one average pixel-channel value. Transparent toolbar containers, still mode, reduced motion, disabling, text halos and JS errors are covered.
- Installed Anki library smoke tests cover bottom-bar payloads, stopping/restoring immersive coverage, settings and audio lifecycle.
- The running user Anki session is not hot-patched; reinstall with Anki closed is required to activate 0.2.

## Initial 0.1 checks

- Windows .NET compilation of the native WASAPI helper; live default-output endpoint opened and produced valid feature frames during an idle-audio smoke run. No audio files recorded.
- Four automated tracker tests: 90/120/128/150/170 BPM lock and future prediction, 40 ms phase advance, unlocking after silence, and reacquiring a 120→150 BPM change.
- Anki's installed Python/Qt libraries in a separate offscreen window: add-on import, menu registration, settings dialog, reviewer JS bridge, native helper start/stop, and disabling the feature. No user collection was opened or changed.
- Headless Edge browser: actual renderer loads without JavaScript errors; answer reveal and newly inserted text receive halos; dark letters select pale halos; demo beat renders; Motion 0 freezes the canvas; disabling hides the canvas/removes styling; OS reduced motion freezes rendering. Screenshot inspected for readable card text and full-window coverage.
- Installer run twice against an isolated add-ons fixture: old Python files replaced, `meta.json` settings preserved, helper compiled and installed. Normal installer refuses installation while Anki is running.
- Python compilation and JavaScript syntax checks. Package contains the helper and reviewer assets.

Still needs Sterling's judgment: perceived synchronization by ear and whether this original particle treatment matches the desired aesthetic. Live card-template/Speed Streak coexistence and HDMI music capture were checked in 0.4.1, with the measured performance limits above. Synthetic tracker tests do not establish beat accuracy on arbitrary music. Use the timing advance setting to tune the first session.

Reproduce tracker tests with `python -m unittest discover -s apps/anki-afterglow/tests -v`. Run `tests/qt_smoke.py` with the installed Anki environment's Python. Run `tests/browser.cjs` with Playwright available (or `PLAYWRIGHT_MODULE` pointing to that package); it uses installed Edge and writes `preview.png`.
