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

The app requests a fixed mobile viewport, disables pinch/double-tap zoom using touch-action and gesture handlers (including WebKit gestures), and uses at least 16px text in form controls to avoid focus zoom. One-finger scrolling remains native. Browser-enforced accessibility overrides and system-wide magnification are outside the page’s control.

Haptics use the optional Web Vibration API and do not work in every browser, including iPhone Safari. Screen wake lock is best-effort. Sound defaults off and is synthesized locally after a user action. Motion respects both the app toggle and the system Reduce Motion preference. Celebrations do not block the next timer.

### Haptic auditioning

Settings → Feel includes 22 named success patterns grouped into builds, crisp taps, tactile rhythms, soft waves, and bigger finishes. A dropdown and Previous/Next controls choose the saved completion pattern. **Test pattern** auditions it in place without sound, a ledger entry, or earnings; **Stop**, another pattern, closing settings, and backgrounding cancel pending playback. Custom continuous segments are bounded to 180ms, so an already-issued native segment may finish after Stop.

The default **Crescendo + snap** progressively raises intensity/sharpness through a short buzz and ends with a distinct transient. It is an original interpretation of the requested rise-and-finish sensation, not a reproduction of Duolingo’s proprietary waveform. Other options include Power up, Charge & release, iPhone success, Coin drop, Ratchet lock, Velvet finish, and Rumble + pop.

Playback defaults to Brrrowser’s documented `navigator.haptic()` bridge when present: system presets or custom `{intensity, sharpness, duration}` events, with duration in milliseconds. HD strength is adjustable for custom patterns. Fixed native system presets keep their native strength. Standard `navigator.vibrate()` is the fallback, with pulse timing approximating intensity envelopes; it cannot control true amplitude or sharpness. Playback options can force the standard API for comparison. API failures never block case completion. Older settings/backups migrate to the default pattern and retain all records/earnings. Pattern, strength, and playback preference are included in backups.

Research and API references:

- [Brrrowser’s developer API examples](https://github.com/Web3Kev/Brrrowser/blob/main/api.html): documented native preset names and custom transient/continuous payloads.
- [Apple: Playing haptics](https://developer.apple.com/design/human-interface-guidelines/playing-haptics): purposeful, optional feedback and transient/continuous building blocks.
- [Android: Haptics design principles](https://developer.android.com/develop/ui/views/haptics/haptics-principles): clear impulses, rising intensity toward a target, and coordinated timing.

Physical feel must be auditioned on the phone; desktop mocks verify dispatch, ordering, cancellation, fallbacks, and data migration rather than the Taptic Engine sensation.

For asset updates, keep the `?v=` release in HTML references and service-worker precache entries aligned with the static cache version. Installation bypasses the HTTP cache; online asset requests revalidate, avoiding mixed old/new code on previously installed copies.

## Motion design references

- [Apple: Motion](https://developer.apple.com/design/human-interface-guidelines/motion): brief, purposeful feedback, cancellable sequences, reduced-motion alternatives.
- [Apple: Playing haptics](https://developer.apple.com/design/human-interface-guidelines/playing-haptics): discrete synchronized feedback; optional controls.
- [web.dev: Animation performance](https://web.dev/articles/animations-guide): transform/opacity for burst particles, spring-like button response, and deposit animation. Dial/progress updates are bounded and no persistent particle loop runs.

The success sequence combines immediate button compression, a ring highlight, a short radial particle burst, the earned amount, a small deposit trail, and a fund update. Overruns get a quiet saved confirmation. No streak loss, penalties, title banner, marketing copy, or background distractions.

## Checks

```powershell
node --test apps/study-reward-timer/engine.test.cjs
node --test apps/study-reward-timer/haptics.test.cjs
node --check apps/study-reward-timer/app.js
node --check apps/study-reward-timer/sw.js
```

Rebuild icons with `python apps/study-reward-timer/generate_icons.py` (Pillow). Tests cover exact deadline boundaries, pauses, lock/reload recovery, immutable reward snapshots, duplicate completion, ledger edits/deletes, invalid restores, and CSV safety.
