# Afterglow · Study Reward Timer

Live: https://starfox1230.github.io/The-Library/apps/study-reward-timer/

Phone-first, buildless, local-only timer. No account, analytics, server ledger, patient fields, external fonts, or dependencies at runtime. Registered in the main Library landing page, alongside the existing timers.

## Defaults and behavior

- Every study starts with an **18-minute** personal target. MR studies pay **$2** only when active time is **at or below** the target. Every other modality defaults to **$0** but still records time and outcome.
- Goal: **$900**, labeled **Steam Deck · 512GB OLED**; editable to the actual checkout total. This is a personal budget tracker, not a payment service.
- Settings → Goal also saves **future goals** with a name and optional estimated cost. Add, edit, delete/Undo, or use an idea to prefill the active goal form. Save explicitly to activate it; saving ideas never changes the current goal or earnings. Future goals are included in JSON backups, and older backups automatically start with an empty list.
- Start appears only when idle; an active timer uses tap-anywhere Pause/Resume and Hold to complete, with no separate pause/resume button. Starting with touch or mouse requires a fresh press and release on Start, so a completed hold's release click cannot start another case. Keyboard and assistive activation remain available. No automatic completion or payment when the timer expires. Overruns continue in amber; completed overruns earn $0.
- The active timer snapshots the selected study, target, reward, and start timestamp. Settings affect future cases only, except the explicit long-press duration restart described below. One combined reading task such as abdomen + MRCP uses one timer/reward.
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

Settings → Feel includes 28 named patterns for each action grouped into builds, crisp taps, tactile rhythms, soft waves, and bigger finishes. Choose Start, Pause, Resume, Hold progress, or Completion payoff, then use the shared dropdown and Previous/Next controls. Each action saves its own enabled switch, pattern, HD strength, and playback engine, under a master Haptics switch. **Test pattern** auditions it in place without sound, a ledger entry, or earnings; **Stop**, another pattern, closing settings, and backgrounding cancel pending playback. Continuous segments are bounded to 100ms, so an already-issued native segment may finish after Stop. Fixed system presets can finish their native sequence because the bridge documents no HD cancellation method.

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
node --test apps/study-reward-timer/gestures.test.cjs
node --check apps/study-reward-timer/app.js
node --check apps/study-reward-timer/sw.js
```

Rebuild icons with `python apps/study-reward-timer/generate_icons.py` (Pillow). Tests cover exact deadline boundaries, pauses, lock/reload recovery, immutable reward snapshots, duplicate completion, ledger edits/deletes, invalid restores, and CSV safety.

## App gestures, curves, and clipboard transfer

- Ordinary interface text cannot be selected or open a context menu. Inputs and the backup textarea retain selection, editing, and paste. Single-finger scrolling remains native.
- Tap any non-interactive area of the main screen to pause/resume an active timer. A true pause has a warm gold background and hides Complete; the engine also refuses paused completion. Buttons, inputs, sheets, scrolling, multi-touch, and timer long presses are excluded from the tap gesture.
- Hold the timer for 500ms to open the duration selector. A preset or custom duration discards the active session with no record, starts immediately, and changes only the current study type’s saved default. Keyboard: Enter/Space on the timer pauses/resumes; Shift+Enter/Space opens duration selection.
- Settings → Feel → Hold to complete is on by default. Existing installations adopt this default once; switching it off afterward in Feel is remembered across reloads and backups. When enabled, pointerdown (or holding Space/Enter on Complete) freezes active time immediately, starts a one-second fill and separate configurable progress haptic, then saves once and plays the completion payoff. A temporary hold is distinct from a pause and never turns the screen gold. Release early, drag off, pointer cancellation, a second touch, blur, or backgrounding cancels and resumes from the frozen elapsed time. On reload or backup transfer, an orphaned hold resumes from that same exact frozen time. Screen-lock time still counts for an ordinary running timer.
- Settings → Feel → Create curve opens a full-screen SVG editor. Tap to add up to 32 points, drag to change time/strength, switch to sharpness, or use precise per-point number fields. Endpoints stay at the boundaries; points remain at least 10ms apart. Arrow keys also edit focused graph points. Curves are 0.2–3 seconds, can end with a separate snap, and support Test/Stop before Save & use. Remix creates a new curve from a preset; Edit updates an existing custom curve. Delete resets affected actions to defaults after confirmation.
- Curves linearly interpolate intensity/sharpness and dispatch 50ms native segments; standard vibration approximates intensity with duty cycles. Hold progress fits the selected pattern to one second, independently of the final payoff. Six added presets include Magnetic fill, Zip & lock, Water drop, Silk rise, Tiny win, and Aftershock. These are original patterns, not claimed copies of a proprietary app’s waveform.
- Settings → Data → Copy backup copies the same complete versioned JSON used by file export. Paste backup reads clipboard text when available and opens the overwrite review. A manual editable textarea and Review & restore remain available when clipboard permission is unavailable. Invalid JSON, incompatible versions, malformed custom curves, and invalid settings are rejected without overwriting data. Restore always requires explicit confirmation. File restore/share/download and CSV remain available.
- Schema remains version 1 with additive validated fields. Earlier backups gain action defaults derived from the previous completion choice, hold-to-complete on, and an empty custom-curve list. All action preferences, type defaults, custom curves, future goals, ledger entries and the active timer are in both clipboard and file backups.

Verification includes real browser checks of golden pause, hidden Complete, duration restart, early-release cancellation, full hold completion, editor point manipulation, independent action settings, clipboard transfer and reload persistence. Clock-injected tests exercise the exact deadline and late cases, repeat holds, interrupted gestures, orphan-hold recovery, data migration and native/fallback playback cancellation. Physical feel still needs an iPhone audition.

Start regression tests simulate mouse compatibility clicks and touch clicks retargeted onto Start when Complete disappears, releases just before/at/after the hold threshold, cancellation, and an immediate intentional new tap. There is no time-based cooldown. The [Pointer Events click-target rules](https://www.w3.org/TR/pointerevents/#the-click-auxclick-and-contextmenu-events) describe click delivery separately from the original press target.
