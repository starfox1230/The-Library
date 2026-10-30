# Validation — October 30, 2026

Passed on Sterling's Windows machine:

- Windows .NET compilation of the native WASAPI helper; live default-output endpoint opened and produced valid feature frames during an idle-audio smoke run. No audio files recorded.
- Four automated tracker tests: 90/120/128/150/170 BPM lock and future prediction, 40 ms phase advance, unlocking after silence, and reacquiring a 120→150 BPM change.
- Anki's installed Python/Qt libraries in a separate offscreen window: add-on import, menu registration, settings dialog, reviewer JS bridge, native helper start/stop, and disabling the feature. No user collection was opened or changed.
- Headless Edge browser: actual renderer loads without JavaScript errors; answer reveal and newly inserted text receive halos; dark letters select pale halos; demo beat renders; Motion 0 freezes the canvas; disabling hides the canvas/removes styling; OS reduced motion freezes rendering. Screenshot inspected for readable card text and full-window coverage.
- Installer run twice against an isolated add-ons fixture: old Python files replaced, `meta.json` settings preserved, helper compiled and installed. Normal installer refuses installation while Anki is running.
- Python compilation and JavaScript syntax checks. Package contains the helper and reviewer assets.

Not yet confirmed: listening to a real music track and judging synchronization by ear; actual live card-template/Speed Streak coexistence and performance during a normal review session. Anki was running during development, so the live add-ons folder was not changed. Synthetic tracker tests do not establish beat accuracy on arbitrary music. Use the timing advance setting to tune the first session.

Reproduce tracker tests with `python -m unittest discover -s apps/anki-afterglow/tests -v`. Run `tests/qt_smoke.py` with the installed Anki environment's Python. Run `tests/browser.cjs` with Playwright available (or `PLAYWRIGHT_MODULE` pointing to that package); it uses installed Edge and writes `preview.png`.
