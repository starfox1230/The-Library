# Afterglow · Study Reward Timer

Live: https://starfox1230.github.io/The-Library/apps/study-reward-timer/

Phone-first, buildless, local-only timer. No account, analytics, server ledger, patient fields, external fonts, or dependencies at runtime. Registered in the main Library landing page, alongside the existing timers.

## Defaults and behavior

- Every study starts with an **18-minute** personal target. MR studies pay **$2** only when active time is **at or below** the target. Every other modality defaults to **$0** but still records time and outcome.
- Goal: **$900**, labeled **Steam Deck · 512GB OLED**; editable to the actual checkout total. This is a personal budget tracker, not a payment service.
- Settings → Goal also saves **future goals** with a name and optional estimated cost. Add, edit, delete/Undo, or use an idea to prefill the active goal form. Save explicitly to activate it; saving ideas never changes the current goal or earnings. Future goals are included in JSON backups, and older backups automatically start with an empty list.
- Start, Pause/Resume, Complete. No automatic completion or payment when the timer expires. Overruns continue in amber; completed overruns earn $0.
- The active timer snapshots the selected study, target, reward, and start timestamp. Settings affect future cases only. One combined reading task such as abdomen + MRCP uses one timer/reward.
- Uses persisted wall-clock anchors, not interval ticks. Screen lock, backgrounding, and reload do not stop a running timer. Explicit pauses exclude interruptions. The app cannot sound an alarm or guarantee background execution on iOS; it calculates the correct elapsed time on return.
- 90+ editable types grouped by modality and category. Favorites in the picker and settings, search, custom types, and bulk modality/category editing. All targets are user-configured personal goals, not validated clinical reading-time standards.
- History stores start/completion timestamps, exact active milliseconds, type, modality, category, target, and available reward. Edit time/date/type/target/reward, delete with a ten-second Undo, and derived earnings update automatically. Changing a historical type does not silently replace its historical target/reward.
- Settings → Data: share JSON via native share sheet (including email apps where available), download JSON, CSV history, email a compact summary, or restore a validated full backup with confirmation. Restore replaces rather than merges data. CSV timestamps are UTC; history displays local time.
- Local browser storage is device/browser-specific; there is no cloud sync. Original malformed storage is preserved and exportable; quota/availability failures are visible. Backup before clearing browser data or switching devices.

## Home screen and offline

On iPhone, open the live link in Safari → Share → Add to Home Screen. Includes a standalone manifest, opaque 180px Apple icon, 192/512px icons, maskable icon, safe-area layout, and a scoped static-asset service worker. Load once online and allow caching to complete before offline use. Browser and installed-home-screen storage may be separate; export/restore to transfer if needed.

Haptics use the optional Web Vibration API and do not work in every browser, including iPhone Safari. Screen wake lock is best-effort. Sound defaults off and is synthesized locally after a user action. Motion respects both the app toggle and the system Reduce Motion preference. Celebrations do not block the next timer.

## Motion design references

- [Apple: Motion](https://developer.apple.com/design/human-interface-guidelines/motion): brief, purposeful feedback, cancellable sequences, reduced-motion alternatives.
- [Apple: Playing haptics](https://developer.apple.com/design/human-interface-guidelines/playing-haptics): discrete synchronized feedback; optional controls.
- [web.dev: Animation performance](https://web.dev/articles/animations-guide): transform/opacity for burst particles, spring-like button response, and deposit animation. Dial/progress updates are bounded and no persistent particle loop runs.

The success sequence combines immediate button compression, a ring highlight, a short radial particle burst, the earned amount, a small deposit trail, and a fund update. Overruns get a quiet saved confirmation. No streak loss, penalties, title banner, marketing copy, or background distractions.

## Checks

```powershell
node --test apps/study-reward-timer/engine.test.cjs
node --check apps/study-reward-timer/app.js
node --check apps/study-reward-timer/sw.js
```

Rebuild icons with `python apps/study-reward-timer/generate_icons.py` (Pillow). Tests cover exact deadline boundaries, pauses, lock/reload recovery, immutable reward snapshots, duplicate completion, ledger edits/deletes, invalid restores, and CSV safety.
