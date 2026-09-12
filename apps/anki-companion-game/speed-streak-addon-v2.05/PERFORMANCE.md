# Hypernova performance and validation

Hypernova replaces the original Prism Gate draft in 2.05. The 20–24 FPS cap and timeout-before-animation-frame scheduler have been removed. It now uses a direct browser animation-frame loop with a 60 FPS deadline accumulator.

## Current measurements

Measured September 9, 2026, on Windows in headless Microsoft Edge Chromium, 390 × 820 viewport, DPR 2, 126-card streak, idle gameplay timer. Raw current results: `tests/hypernova-benchmark.json`. Historical superseded draft: `tests/prism-benchmark.json`.

**The progressive design sustained 60.0 FPS; its 95th-percentile frame interval was 16.8 ms.** The test requires at least 48 FPS on this 60 Hz host and a 95th-percentile interval below 35 ms. The original test's permissive greater-than-8-FPS threshold is gone.

CPU is summed browser-process CPU time divided by elapsed time, expressed as a percentage of **one core**, not the entire machine. Means use two 2.2-second samples per mode after warm-up. Memory columns show the second pass after all renderers have warmed up.

| Visual | Mean CPU, one core | JS heap | Sum of browser process working sets |
| --- | ---: | ---: | ---: |
| Hypernova / Smooth | 20.34% | 3.46 MiB | 701.1 MiB |
| Hypernova / Rich | 20.88% | 3.86 MiB | 691.8 MiB |
| Singularity / Balanced | 10.39% | 3.47 MiB | 706.6 MiB |
| Sphere / Fusion | 19.86% | 3.93 MiB | 738.2 MiB |
| Crystal Reactor / Animated | 14.81% | 3.39 MiB | 838.1 MiB |
| Number Only | 1.03% | 3.44 MiB | 689.7 MiB |

Smooth with counter-rotating rings averaged 20.34% of one core, close to Sphere/Fusion's 19.86% in this run. It remains more expensive than Singularity Balanced. Results across separate runs are not controlled measurements of CPU improvement. The first earned piece now starts continuous rotation even below 20 cards; only the empty seed stops drawing when settled. Still mode and all existing inactivity controls stop rotation.

Working-set totals include browser overhead and GPU-process resources retained from previous cases, and shared pages may be counted more than once. They are not isolated add-on RAM. Current results show broadly similar process memory to the existing renderers. Short headless-browser samples do not establish Anki battery duration, physical GPU energy, or performance on every device.

## Bounded rendering

- One visible Canvas 2D surface, at most 960 × 960 pixels. Smooth uses 1× pixel density; Rich uses up to 1.5×.
- Zero to six plasma arms are drawn into a reusable cached disc, then rotated as one image at 60 FPS. A second tinted disc handles loss reactions. Both caches cap at 640 × 640 pixels and rebuild only when geometry, palette, or size changes.
- Two earned-ring caches, each capped at 640 × 640, hold at most 100 segments between them. Alternating rings share a cache; the two images rotate at ±0.28 radians/second (about 16 degrees/second). They rebuild only when the streak, recent rating colors, palette, or resolution changes. Each frame composites at most two images. Higher streaks reforge existing segments instead of allocating more geometry.
- Two 96 × 96 glow sprites provide bloom without per-frame blur filters. Combined visible canvas and cached RGBA pixels cap at approximately 9.84 MiB before browser buffering; ordinary sidebar dimensions use much less. Counter-rotation adds at most 1.56 MiB of raw pixels over the previous single-ring-cache design.
- Reusable 4,680-byte geometry array. Smooth has up to 48 analytic star trails; Rich has up to 72. At most 18 travelling knots, 18 corona curves, three containment arcs, three event shells, and 32 event spray lines. These effects unlock gradually by decade.
- One replaceable event slot; rapid answers do not accumulate particles. Rendering work at 100 and 1,000,000 cards is identical after the cache is built.
- Still, OS reduced motion, pause, hidden documents, collapse, disable, and settings overlays stop continuous drawing. Switching mode releases renderer references, observer, canvas backing store, and pending callbacks.

## Verification

The browser test covers actual selector save commands, mode transitions, answer/Boost/loss effects, fifty/hundred-card milestones, narrow/large/high-DPI windows, canvas caps, long-streak work limits, and inactive/reduced-motion behavior. It measures actual drawn-frame cadence rather than only counting scheduled callbacks. It also checks ongoing motion from the first answer, opposite rotation at 17 cards, shared rotation of the first and third rings at 27, and reuse of cached paths throughout rotation.

`test_hypernova_progression.cjs` verifies persistent pixel changes at 0→1, 1→2, 12→13, 99→100, 101→102, and 212→213 with WebGL disabled, no animation, and no answer effect. It also checks that an earlier piece remains and Still mode refreshes corrected rating colors. `hypernova-progression.png` shows twelve settled stages. `test_hypernova_answer_updates.cjs` confirms completed scoreboard rows and selector nodes survive answer updates, retaining the hitch fix.

The Python suite covers independent palette persistence, package/source equality, and upgrade/reinstall preservation of existing settings and user data in an isolated PowerShell fixture. Hypernova retains the `prism_gate` storage key so existing 2.05 draft settings and colors continue to load; `hypernova` is also accepted as an input alias.

`tests/hypernova-demo.webm` is a historical recording of the earlier, fully lit design's milestone, Boost, and loss animations with WebGL explicitly disabled. Use the current interactive harness and `hypernova-progression.png` for the progressive design. The renderer uses ordinary Canvas 2D and does not add native dependencies. macOS/Linux hardware and battery tests remain unverified on this Windows host.

A separate 4× CPU-throttled trace with counter-rotating rings exercised 1→2, 9→10, 12→13, 19→20, 29→30, 49→50, and 99→100 with a live timer and five saved records. Across the two-second windows after each update, the maximum drawing callback was 7.3 ms and the largest measured frame gap was 21.0 ms. The recorded long task occurred during initial page loading, before those answer windows. This synthetic trace does not establish actual Qt/Anki frame timing. Raw data: `tests/hypernova-progression-answer-trace.json`; reproduce with `HYPERNOVA_PROGRESSION=1` and `node tests/profile_hypernova_answers.cjs`.

## Reproduce

After building: `python -m unittest discover -s tests -p 'test_*.py' -q` from this folder. Use unittest discovery because pytest tries to import the Anki entry point outside Anki.

With Playwright available through Node, run `node tests/test_prism_gate_browser.cjs`. It uses an isolated headless browser, defaults to installed Microsoft Edge, and accepts `PRISM_BROWSER=chrome` for installed Chrome. The original test filename is retained, but it now tests Hypernova and writes `hypernova-benchmark.json` and `hypernova-preview.png`.

## Answer-transition hitch investigation

The installed JavaScript matched this release before the fix. An isolated ten-answer trace with a live timer did not reproduce a consistent 0.5–1.5-second stall; individual Hypernova drawing callbacks were around 0.8–1.2 ms. This does not rule out contention from Anki, its Qt compositor, audio, other add-ons, or the host machine.

Confirmed avoidable work: every answer/phase update recreated the visual-selector SVG and resource ticks, and reformatted dates and rebuilt all completed-record rows even in Best Only. These elements now retain their nodes until their actual inputs change. The row signature includes the local date, so Today/Yesterday labels still roll over correctly. Stable record-label text is no longer replaced. Canvas resize notifications no longer clear an unchanged pixel buffer.

In the 4× CPU-throttled, live-timer/Best-Only harness, median warm state-update time dropped from 24.25 ms to 9.95 ms. These are JavaScript UI update durations, not total Anki answer latency. Short timing runs vary; this removes a confirmed source of frame-budget contention but does not prove it was the sole cause of the reported hitch. The answer ring itself has not been shortened or disabled.

`tests/hypernova-answer-update-comparison.json` retains the before/after timing summary. `node tests/test_hypernova_answer_updates.cjs` verifies node reuse across ratings and phase updates, plus correct live records, deletion, ordering, purity filtering, and date rollover. Run the broader lifecycle/FPS checks without repeating CPU benchmarks using `HYPERNOVA_SKIP_BENCHMARK=1 node tests/test_prism_gate_browser.cjs` (set that environment variable with your shell's syntax).
