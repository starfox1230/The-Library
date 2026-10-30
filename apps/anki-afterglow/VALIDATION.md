# Validation — October 30, 2026

Passed on Sterling's Windows machine:

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

Not yet confirmed: listening to a real music track and judging synchronization by ear; actual live card-template/Speed Streak coexistence and performance during a normal review session. Anki was running during development, so the live add-ons folder was not changed. Synthetic tracker tests do not establish beat accuracy on arbitrary music. Use the timing advance setting to tune the first session.

Reproduce tracker tests with `python -m unittest discover -s apps/anki-afterglow/tests -v`. Run `tests/qt_smoke.py` with the installed Anki environment's Python. Run `tests/browser.cjs` with Playwright available (or `PLAYWRIGHT_MODULE` pointing to that package); it uses installed Edge and writes `preview.png`.
