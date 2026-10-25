# Quiet Harbor — implementation specification

Prepared October 25, 2026. **Working title; planning deliverable, not a built app.**

This document is the implementation contract for Sterling's phone-first hand-picking tracker in The Library. Read [IMPLEMENTER_PROMPT.md](IMPLEMENTER_PROMPT.md) for a ready-to-paste assignment. The decisions below are intentional defaults: implement them without asking Sterling to choose a framework, find artwork, label sprites, or design a city.

## 1. Product in one paragraph

Open the app and see exactly how long it has been since the last recorded picking episode, alongside a beautiful island settlement that grows automatically with that time. A seed becomes a plant; a person arrives; a garden, cottage, village, and town follow. Drag around to explore. Nothing needs collecting, feeding, building, or maintaining. If picking happens, hold **“I picked — begin again”** for one continuous second. A large stylized tsunami washes away the settlement, the water retreats, and a new seed begins a different world. The timer and growth continue while the app is closed. Install it on an iPhone Home Screen with its own icon and an app-like layout.

**The core loop is:** leave hands alone → time passes → world grows → open and enjoy. Recording an episode starts the loop again.

## 2. Scope and product decisions

### Required for the first complete release

- Accurate duration display including seconds at every scale.
- Automatic, time-based growth from a single plant through a substantial town.
- A different seeded world after each confirmed restart; the same world on every ordinary return.
- Isometric artwork, visible people, vegetation, paths, homes, public spaces, and a coastline.
- A living scene: restrained water movement, plant movement, and a few walking residents.
- Camera pan, bounded scene zoom, recenter, and a small building-information card on tap.
- A one-second hold with a visible fill, proper cancellation, and exactly one restart per gesture.
- A tsunami reset, a reduced-motion alternative, and brief accidental-reset recovery.
- Local saves, offline reopening, run history, best duration, and export/import backup.
- iPhone Home Screen metadata and finished raster icons.
- Real mobile interaction polish and the verification matrix below.
- Repository registration, required verification, scoped commit/push, and an honest deployment handoff.

### Keep the interface small

One primary screen, with a small sheet for History and Settings. The main screen has one behavior-changing action: recording a picking episode. Exploring the world does not change the streak. No account, currency, purchase, daily task, notification permission, leaderboard, construction menu, obligatory journal, streak multiplier, or reward for checking in.

Use neutral text: **“Time since your last recorded pick”**, **“A new beginning”**, and **“Your next seed is already growing.”** Do not put “failed,” “dirty,” “bad,” or “you killed your village” into the interface. Keep the requested wave as a visual transition; do not depict injury or death. Past durations remain in History. This is a personal tracking experience; do not present the particular game mechanic as a clinically established treatment.

Optional later work: cloud sync, a native wrapper, additional coherent art themes, and a separate urge-support tool. None is needed for this release.

## 3. Research decision: reuse artwork and rendering, author the small growth system

The practical version of “AI built this from one prompt” is a coding agent assembling existing assets and a renderer, then writing the project-specific rules. The browser can execute those rules indefinitely. **A runtime AI model is unnecessary.** No paid model calls, image-generation calls, or continuously running computer are needed for world growth.

The recommended stack is **vanilla JavaScript modules + PixiJS v8 + Kenney's 2D Isometric Tiles assets**, served as static files by the repository's existing GitHub Pages setup. Keep controls and timer in ordinary HTML; use PixiJS only for the world. [PixiJS quick start](https://pixijs.com/8.x/guides/getting-started/quick-start), [source repository](https://github.com/pixijs/pixijs).

### Options considered

| Approach | Useful material already available | Decision for this app |
| --- | --- | --- |
| PixiJS + 2D isometric sprites | Open-source renderer; reusable landscape/building/city packs | **Choose this.** Gives a dimensional miniature-world appearance with a bounded camera and a relatively small art pipeline. |
| Three.js + 3D Kenney kits | [Three.js](https://github.com/mrdoob/three.js), [Suburban City Kit](https://kenney.nl/assets/city-kit-suburban), [Nature Kit](https://kenney.nl/assets/nature-kit) | Viable for a later real-3D version. Camera, lighting, model loading, and mobile rendering add work the core loop does not require. |
| An existing procedural city generator | [Three.js CityGenerator](https://threejs.org/docs/pages/CityGenerator.html); [threex.proceduralcity](https://github.com/jeromeetienne/threex.proceduralcity) | Useful examples of automated layout. A tower/block generator does not supply the plant-to-garden story, timer, saved runs, or phone behavior. Do not make a general city simulator the foundation. |
| Phaser | [Open-source game framework](https://github.com/phaserjs/phaser) | Reasonable alternative, but its broader game systems are unnecessary for this small renderer plus DOM interface. |
| Hand-draw every asset or generate each scene with AI | Complete stylistic freedom | Too much art work; generated scenes also complicate deterministic growth and exploration. Reuse a coherent asset family. |

These are engineering judgments for this project, not comparative performance benchmarks. The referenced examples and APIs have been researched, not integrated or performance-tested in this planning task.

### Exact asset sourcing plan

| Role | Primary source | Verified listing |
| --- | --- | --- |
| Terrain, water edges, trees, natural variation | [Kenney Isometric Tiles Landscape](https://kenney.nl/assets/isometric-tiles-landscape) | 128 files; CC0 |
| Early homes and architectural variation | [Kenney Isometric Tiles Buildings](https://kenney.nl/assets/isometric-tiles-buildings) | 128 files; CC0 |
| Later town/city variety | [Kenney Isometric Tiles City](https://kenney.nl/assets/isometric-tiles-city) | 128 files; CC0 |
| Alternative cohesive miniature theme, if the first art proof is unsatisfactory | [Miniature Farm](https://kenney.nl/assets/isometric-miniature-farm), [Miniature Prototype](https://kenney.nl/assets/isometric-miniature-prototype) | 60 files each; CC0 |

Counts are pack listings, not guarantees of that many unique houses or characters. Download and inspect the actual archives. The first three packs share a named art family, but anchors, canvas dimensions, scale, and edge compatibility must still be checked visually. **Do not mix the Isometric Tiles and Isometric Miniature families by default.**

The implementing agent must:

1. Download the free packs from Kenney's official pages. Use the free continuation link when presented; purchasing an all-in-one bundle is unnecessary.
2. Preserve each archive's license; record source URL, pack name, download date, archive SHA-256, and selected filenames in an asset-source manifest.
3. Generate a labeled contact sheet automatically. Inspect it to identify land, shore, path, foliage, and building pieces. Sterling should not need to do this work.
4. Make semantic names in `assets/catalog.json`; never spread opaque `tile_###` assumptions throughout code.
5. Record each piece's ground anchor, scale, footprint, orientation, and category. Assemble a proof scene containing adjacent tiles, two building sizes, trees, a garden, and one resident before authoring the entire town.
6. Select at least 6 natural variations, 8 house/building variations, 4 civic/market/decorative variations, and the shore/path pieces needed for clean joins. If a pack lacks a specific named landmark, use a visually suitable composite and name it honestly.
7. For the tiny seed, sprout, garden plots, and resident, use suitable pack assets if actually present; otherwise draw a few reusable matching primitives once with code. Do not claim the city packs include animated characters without checking. A tiny oval shadow, body, head, and two alternating leg poses are enough for a distant walking person.
8. Use the pack's sheet if suitable, or build local texture atlases. Ship only the selected assets and licenses; keep the acquisition script and source manifest reproducible.

Retain the vendored renderer's license too. PixiJS's [license is available in its repository](https://github.com/pixijs/pixijs/blob/dev/LICENSE). Verify the license of the actual downloaded release. No assets may be scraped from an unlicensed commercial game.

## 4. Visual direction and screen design

**Style:** an inviting miniature coastal settlement, angled overhead, with soft sage land, cream paths, warm roofs, and deep teal water. Crisp illustrated sprites rather than photorealism. The scene is the visual centerpiece. Avoid a dashboard of boxes competing with it.

Proposed interface palette: sea `#173F49`, shallow water `#4F9BA2`, paper `#FAF7EF`, foliage `#6E956B`, ink `#193633`, muted text `#506862`, restart accent `#8E594E`. Adjust colors to the downloaded art, and check actual contrast before shipping. Use system UI fonts; large tabular numerals for the timer. No web-font network dependency.

```text
 ┌────────────────────────────────────┐
 │ Quiet Harbor                •••    │  safe area + title/menu
 │                                    │
 │ Time since your last recorded pick  │
 │         2d 03h 14m 08s              │  real DOM text
 │ Best: 4d 07h                       │
 │                                    │
 │       [explorable island]          │
 │  water · garden · homes · walkers   │  fills remaining space
 │                                    │
 │  −   +                 Recenter    │  scene camera only
 │                                    │
 │ Your village is taking root        │  one line of stage text
 │ [ Hold: I picked — begin again ]    │  broad thumb target
 │             Hold for 1 second      │
 └────────────────────────────────────┘
```

On very short displays, reduce the scene's minimum height before shrinking controls or hiding seconds. At large text sizes, allow the interface region to scroll rather than clip content. In landscape, use a slim information/action column beside the scene. On desktop, center a generous app view rather than stretching labels across the entire monitor.

### First open

Show a tiny bare island and seed with one sentence: **“Give your hands a break. Let a little world grow.”** A single **“Begin growing”** tap saves the first run immediately. No setup form. Never start or replace a run merely because the page loaded. If a saved run exists, go directly to it.

### Ordinary open

Restore saved data, calculate current elapsed time, show the timer, then load/render the appropriate world. Avoid flashing a zero timer or seed-only world while loading an older settlement. If the renderer is slow or unavailable, the functional timer and restart action remain available.

When returning after a long absence, show the current settlement promptly. Animate at most a few recent additions for 1–2 seconds; do not replay hours of construction. No “offline earnings” claim or collect button.

### Exploring

- One-finger drag pans the scene. A tap under the movement threshold opens a small card such as “First cottage · appeared after 30 minutes.”
- Scene pinch changes the camera scale; it never scales the timer or action button.
- Provide visible `+`, `−`, and Recenter buttons so pinch is optional.
- Clamp zoom to an art-appropriate range, initially 0.65×–2.5× relative to the default camera. Clamp pan to the discovered settlement bounds plus a small water margin.
- Initial framing includes the seed or inhabited area. Fit early worlds fully; for large towns frame the recent neighborhood with a compact overview/recenter option. Do not fit years of growth into an unreadable dot.
- Once the user pans, do not automatically yank the camera toward each addition. On ordinary reopen, restore a valid camera or fit the current neighborhood if the saved camera is invalid.
- Tapping a building never spends anything, pauses growth, or changes state.

### Settings/History sheet

Include completed runs, best duration, motion setting (System / Full / Reduced), **Calm restart** toggle (default off unless reduced motion applies), Export backup, Import backup, install instructions, credits, and storage status. Sound is off in v1; do not add autoplay or depend on haptics.

Keep backup and storage explanations here. The main screen should describe the experience in ordinary language, not IndexedDB, cache versions, or engine details.

## 5. Timer contract

Use elapsed real duration from a persisted epoch timestamp. Do not count interval callbacks as elapsed seconds. The normal calculation is:

```js
const elapsedMs = Math.max(0, Date.now() - run.startedAtMs);
const elapsedSeconds = Math.floor(elapsedMs / 1000);
```

An interval schedules display refreshes only. Refresh at second boundaries while visible; recompute immediately on `pageshow`, focus, and `visibilitychange` when becoming visible. Stop unnecessary repainting while hidden. Background browser suspension must not stop growth. No service-worker heartbeat or background simulation is needed.

### Display all smaller units once a larger unit appears

| Actual duration | Display |
| --- | --- |
| 0 seconds | `0s` |
| 9 seconds | `9s` |
| 59 seconds | `59s` |
| 60 seconds | `1m 00s` |
| 3,599 seconds | `59m 59s` |
| 3,600 seconds | `1h 00m 00s` |
| 86,400 seconds | `1d 00h 00m 00s` |
| 604,800 seconds | `1w 0d 00h 00m 00s` |
| 788,645 seconds | `1w 2d 03h 04m 05s` |
| 31,536,000 seconds | `1y 0w 0d 00h 00m 00s` |

Use fixed durations: minute = 60 seconds; hour = 60 minutes; day = 24 hours; week = 7 days; display year = 365 days. Months are omitted because their length varies. Decompose largest-first with remainders; do not display total days alongside total weeks. At year scale, allow a second line so seconds remain visible on a narrow phone. Explain fixed-duration years in Help if needed. Dates in History can use local date formatting; duration math must not use calendar subtraction. DST and timezone changes do not change elapsed duration.

Timer text is selectable only through an explicit copy action if one is added; routine repeated taps should not select it. Its screen-reader label should read the units in full. Do not use an assertive or every-second live region. Announce run starts and completed resets politely once.

### Device clock policy

This local-only app trusts the device clock. During a foreground session, compare wall-clock movement to `performance.now()`; a large mismatch or elapsed time moving below the last saved observed duration is a clock anomaly. Preserve the last valid duration and display a small “Device time changed” message with a **“Keep this duration and continue”** action. That action rebases `startedAtMs` to current wall time minus the preserved duration and retains `originalStartedAtMs` for history. Do not record an episode or play the wave because the clock changed.

Checkpoint the maximum observed elapsed duration on meaningful lifecycle events and at most once per minute, not every frame. A forward clock jump while the app was fully closed cannot reliably be distinguished from genuine elapsed time without a trusted server; accept it. This is a personal tracker, not an anti-cheat system. Test clock handling without pretending offline timestamps are independently verified.

## 6. Growth: specific milestones and a scalable continuation

Growth is entirely a function of **run seed + generator version + growth version + elapsed duration**. The following schedule is the release default; keep it in data, not renderer conditionals.

| Time since start | Visible event / state | Target completed buildings |
| --- | --- | ---: |
| 0 seconds | A seed on a small patch of earth | 0 |
| 10 seconds | A small shoot emerges | 0 |
| 30 seconds | Leaves unfold; gentle life in the scene | 0 |
| 1 minute | First resident arrives from the shore and notices the plant | 0 |
| 3 minutes | A short path appears; a garden is marked out | 0 |
| 5 minutes | The resident tends a planted garden | 0 |
| 15 minutes | Cottage foundation and scaffold | 0 |
| 30 minutes | First cottage completes | 1 |
| 1 hour | Orchard/fence details; second home | 2 |
| 3 hours | A small cluster connected by paths | 4 |
| 6 hours | Shared green/well or a suitable composite landmark | 7 |
| 12 hours | Hamlet, several gardens, more residents | 12 |
| 1 day | Village with a recognizable central space | 20 |
| 3 days | Market/gathering place and second neighborhood | 32 |
| 1 week | Small town with a developed waterfront | 48 |
| 2 weeks | More neighborhoods, larger public garden | 72 |
| 4 weeks | Established coastal town | 112 |
| After 4 weeks | An additional district of 16 lots develops each week | +16 / week |

Before 30 minutes, use the explicit story events. Starting at 30 minutes, derive integer completed-building counts by piecewise linear interpolation between the count anchors above. Round down and never remove an already completed building. Every lot has a stable ID and an exact derived birth timestamp. Between a lot's construction start and completion, show a foundation/scaffold rather than stretching the completed house. The first cottage follows its explicit 15-minute foundation / 30-minute completion story. For subsequent buildings, set construction duration to `min(120 seconds, max(10 seconds, 0.25 * gapSincePreviousCompletion))`; calculate this from the schedule.

After 28 days, let `q = (elapsedSeconds - 28*86400) / 604800`. Additional completed buildings = `floor(16*q)`. Each 16-lot district has a reserved central path and decoration locations. Allocate its completed lots in a stable predetermined order. The timer continues for years and new districts keep appearing. Do not secretly stop visual growth after the last named milestone.

Milestones unlock visible structures and new compositions, not just a different text label or a progress bar. Between additions, allow slow plant growth, garden changes, resident movement, and construction staging. Waiting one second should not erect a whole house; reaching a minute should already show meaningful change.

Day/night tint and garden color cycles may use elapsed time for a coherent world rhythm; they must not drive structural layout or randomize it. Avoid extremely dark nights on a phone. These are decorative cycles, not extra unlock systems.

## 7. Deterministic procedural world generation

### State model

Create a cryptographically random 128-bit seed once per new run, store it as a hex string, and use a fixed documented integer hash/PRNG implementation to derive layout. `crypto.getRandomValues()` supplies the new seed; normal rendering must not consume unseeded `Math.random()` for structural decisions.

Use independently keyed randomness: `hash(seed, "terrain", chunkX, chunkY)`; `hash(seed, "lot", lotId)`; `hash(seed, "resident", residentId)`. Adding a butterfly must not change all building choices by advancing a shared random stream. Store generator/growth version on each run; retain old implementations for existing saves when algorithms change.

### Layout algorithm

1. Use integer logical grid coordinates. Reserve a starting island/core area, seed clearing, first house lot, arrival shore, and connected path network. Guarantee these exist for every seed.
2. Reserve a 3×3 group of 16×16-cell chunks centered on the origin for the core town. Generate its 112 lot placements once as a deterministic plan, whether or not they are visible yet. Use a seeded low-frequency coastline and guaranteed land corridors; reserve civic spaces before placing houses. If procedural candidates fail, use a known-valid core template with seed-based details.
3. Place buildings only on eligible land, without footprint overlap, with a path-facing entrance. Roads/paths connect to the central network. Keep the original plant as a visible central garden/tree landmark.
4. Allocate future 16-lot districts into 16×16-cell chunks on a deterministic outward square spiral, skipping the nine reserved core chunks. Reserve chunk-edge path connection points; adjacent chunks derive the same shared boundary terrain from world coordinates. Where a connection crosses water, create a preplanned bridge or quay. Never reroll the starting coast when a district unlocks.
5. Do not require simulating every intermediate second. Map elapsed time to completed lots; map lot/district IDs directly to coordinates and assets.
6. Draw only the camera's visible chunks plus one chunk of margin. At far zoom, render district summaries instead of every roof. Bound cached chunks with an LRU policy. Long-running worlds can be logically large while the active scene remains small.
7. Make an object record with `id`, `kind`, `gridPosition`, `footprint`, `assetId`, `birthAtSeconds`, `variant`, and ground anchor. Keep those records separate from Pixi display objects.

The exact noise algorithm can be simple hashed value noise; a dependency is unnecessary. Reject maps with unreachable first lots or broken shore seams in automated fixture checks. Use a bounded search with a deterministic fallback, never an unbounded random-placement loop.

### Isometric rendering

Start with `screenX = (gridX-gridY)*tileWidth/2` and `screenY = (gridX+gridY)*tileHeight/2`. Calibrate actual tile dimensions from the downloaded assets. Use base/ground anchors, not the center of the full transparent image. Sort buildings/residents by ground depth with stable IDs as tie-breakers; support footprint-aware occlusion for multi-tile structures. Keep ocean, terrain, paths, structures, residents, foreground effects, and reset overlay in separate layers.

Cache stable ground layers. Move sprites and change alpha/tint for subtle animation; avoid rebuilding vector shapes and uploading text every frame. PixiJS specifically recommends spritesheets and warns about excessive filters and frequently changing text. [Performance guidance](https://pixijs.com/8.x/guides/concepts/performance-tips).

### Residents

Residents are ambient actors, not persistent economic agents. Derive a population label from the completed town stage if desired, but render at most 24 animated residents. Each follows a short deterministic path on the current road network with a phase derived from elapsed time. A returning app positions them directly. No saved AI simulation, job system, hunger, traffic, collision physics, or overnight simulation.

### New run variation

Vary coastline detail, vegetation, building sequence within role constraints, roof palette from approved variants, garden placement, and neighborhood layout. Always preserve the seed → person → garden → cottage narrative. A new seed should give an obviously different composition by the village stage, not merely a new invisible ID.

## 8. Restart gesture and wave: exact behavior

### Gesture state machine

`idle → holding → committing → transitioning → idle`

- Pointer down on the button starts an in-memory hold using `performance.now()`, captures that pointer, and displays a left-to-right fill plus “Keep holding…”. Only the primary pointer may start it.
- Threshold: **1,000 ms of continuous active hold**, not accumulated taps. A 900 ms hold followed by another 900 ms hold must not reset.
- Pointer up before threshold, pointer cancellation, lost capture, leaving the button's bounds (allow 12px tolerance), window blur, hidden document, or a second touch cancels the hold and clears the fill.
- With pointer capture, check coordinates against the button explicitly; relying only on `pointerleave` is insufficient.
- Reaching the threshold triggers one commit while the originating pointer/key is still active. Gate reentry synchronously. A later `click` from the same gesture does nothing.
- On release, perform one final elapsed-time check before clearing an otherwise valid active hold, so a release just after 1,000 ms is not missed between animation frames. A release before 1,000 ms always cancels.
- Use `requestAnimationFrame` for fill updates while visible; never let a throttled timeout finish a hold after backgrounding. Also verify the active visible hold at completion.
- Space/Enter may hold with auto-repeat ignored; release/blur cancels. For assistive technology that synthesizes clicks, provide a Settings action “Record a picking episode” that opens a plainly worded Cancel / Begin again confirmation. A synthesized click on the main hold button alone must not reset.

Use a real `<button>` with visible focus and an accessible description of the one-second requirement. Do not announce each percentage point. Suppress text selection and the native context menu on this specific button.

### Commit before animation

At the threshold, use one IndexedDB read/write transaction to:

1. Read the current state and verify the expected active run ID and revision.
2. Finish the old run at the threshold timestamp; store its completed elapsed duration.
3. Insert a new run with a new seed and start time equal to the same timestamp.
4. Change the active run ID, advance revision, and store a short-lived reset/undo receipt.

Show the wave only after the transaction completes successfully. If saving fails, keep the old run, cancel the transition, and show a retryable “Couldn't save that restart” message. Do not visually erase a world before knowing its restart was saved. If closed during the animation, reopening shows the new run at its real current age. Do not create another run or replay the disaster on every reopen.

### Wave storyboard, approximately 4.5 seconds

| Time after committed reset | Scene |
| --- | --- |
| 0–0.5 s | Camera eases to show the settlement; sea draws back slightly |
| 0.5–1.6 s | Large layered teal wave with foam sweeps diagonally across the island |
| 1.6–2.8 s | Wave covers the scene; settlement sprites fade/dissolve behind the crest |
| 2.8–3.8 s | Water retreats; reveal the newly seeded world's bare starting shore |
| 3.8–4.5 s | New seed settles into view; “A new beginning” |

Implement with a small number of animated graphics/sprite layers, masks, and foam particles. No fluid simulation, physics engine, or heavy fullscreen blur. Reduce particle counts on slower devices. The new timer starts at commit, so it may read `4s` when the wave finishes. That is correct.

If the destroyed town is huge, show its current neighborhood and a small zoom-out suggestion; do not attempt to render every district in one disaster frame. The entire old run's world is replaced logically.

Reduced-motion or Calm restart replaces travel and destruction animation with a 300–500 ms crossfade to new shore. Timer/state semantics remain identical. Sound stays off. No flashing, shaking, injured people, or mortality messages.

### Accidental-reset recovery

Show **“New beginning · Undo accidental reset”** for 10 seconds after the committed timestamp, including time spent in animation. Undo uses the stored receipt to restore the prior run and its original start time/seed, removes the accidental replacement run, and updates revision atomically. It is allowed only while that replacement is still active, before the deadline, and once per receipt. On restore, the old streak includes time that passed during the accidental restart. Reloading does not extend the deadline. Expired receipts can be pruned. History has no arbitrary edit/run-resume controls in v1.

## 9. Data, persistence, recovery, and privacy

Use a namespaced IndexedDB database, e.g. `the-library-quiet-harbor`, schema version 1. Use explicit transactions for state transitions. [IndexedDB transactions](https://developer.mozilla.org/en-US/docs/Web/API/IDBDatabase/transaction).

```text
meta store:
  key: "state"
  schemaVersion, revision, activeRunId, firstOpenedAtMs
  settings: {motion: "system", calmRestart: false}
  camera: {runId, centerX, centerY, zoom}
  resetReceipt: {oldRunId, newRunId, committedAtMs, undoUntilMs} | null

runs store (key: id):
  id, seed, generatorVersion, growthVersion
  startedAtMs, originalStartedAtMs
  endedAtMs: number | null
  elapsedAtEndMs: number | null
  maxObservedElapsedMs, lastObservedAtMs
```

- Derive best duration from valid completed runs and the active run. Do not increment an independent best counter that can drift or survive Undo incorrectly.
- Persist start/reset/undo/settings/import immediately, camera after a short debounce, and elapsed checkpoints at most once per minute plus lifecycle opportunities. No per-frame saves.
- Browser tabs share the database in a given storage context. Re-read the authoritative active run and revision inside each mutation transaction. If a second tab already changed the active run, adopt that state instead of resetting again. Broadcast committed revisions with `BroadcastChannel` when available, and also resync on focus; correctness must not depend on BroadcastChannel.
- Treat an IndexedDB read error as an error, not evidence of a new user. Never silently overwrite unreadable state with a fresh run. Offer retry and import; keep a recognizable error state.
- If storage is unavailable at first launch, show a persistent “Progress can't be saved in this browser” notice and allow an explicitly labeled temporary session. Do not claim durable saving.
- Save data stays on the device/browser context. No analytics, advertising SDK, health-data upload, or third-party fonts. The public repository must never contain Sterling's personal run data.
- Namespacing prevents accidental collisions, but this is still shared-origin web storage: other same-origin scripts are not a security-isolated app. Do not claim encryption or isolation that is absent.

### Backups

Export a small versioned JSON file containing metadata, settings, runs, seeds, and algorithm versions. Do not export cached artwork. Import validates schema, types, finite timestamps, seed format, unique IDs, run relationships, version support, and file size (limit 5 MB). Preview the active duration and number of runs, then explicitly confirm replacement; commit atomically after saving the previous database state as a recovery snapshot. Never render imported strings as HTML or use imported asset paths as URLs.

Detect unsupported future formats and explain them rather than resetting. Keep a migration function for each supported schema change. No arbitrary history pruning; store run records, not per-second events or large screenshots.

### iPhone storage reality

Request persistence with feature detection and show the actual result. WebKit documents best-effort storage, possible eviction, and persistent-mode heuristics, including Home Screen use. Installation helps the experience but is not a backup guarantee. [WebKit storage policy](https://webkit.org/blog/14403/updates-to-storage-policy/).

Do not promise that Safari, private browsing, a Home Screen app, another browser, or another phone will share the same data. Test Safari → Home Screen on the actual device/browser version. In the install sheet, suggest installing before starting a long run and offer Export/Import if the installed app opens with a different save context. Clearing site data or changing the app's origin can lose local progress; explain this once in Settings/backup help, not as a recurring main-screen warning.

## 10. Phone behavior and accessibility are release requirements

These details specifically address Sterling's complaint about web interfaces feeling unlike apps.

```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#173F49">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Quiet Harbor">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="manifest" href="./manifest.webmanifest">
<link rel="apple-touch-icon" sizes="180x180" href="./icons/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="32x32" href="./icons/favicon-32.png">
```

```css
html { box-sizing: border-box; -webkit-text-size-adjust: 100%; }
*, *::before, *::after { box-sizing: inherit; }
html, body { margin: 0; width: 100%; }
.app {
  min-height: 100vh;
  min-height: 100dvh;
  padding: max(12px, env(safe-area-inset-top))
           max(12px, env(safe-area-inset-right))
           max(12px, env(safe-area-inset-bottom))
           max(12px, env(safe-area-inset-left));
}
button, a, .app-chrome { touch-action: manipulation; }
.app-chrome, .world-surface, .hold-button {
  -webkit-user-select: none;
  user-select: none;
  -webkit-touch-callout: none;
}
.world-surface, .hold-button { touch-action: none; }
input, textarea, select {
  font: inherit;
  font-size: max(16px, 1rem);
  -webkit-user-select: text;
  user-select: text;
}
button { min-height: 48px; min-width: 48px; }
.timer { font-variant-numeric: tabular-nums; }
```

This is a starting contract, not a substitute for testing. `touch-action: manipulation` disables double-tap page zoom on controls while retaining ordinary pan/pinch behavior; use `none` only for the two custom gesture surfaces. [WebKit tapping behavior](https://webkit.org/blog/5610/more-responsive-tapping-on-ios/), [touch-action reference](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/touch-action).

Additional rules:

- Repeatedly tapping buttons or the timer must not select text or zoom the page. Long-holding the reset button must not summon Copy or a link preview.
- Inputs use an actual computed font size of at least 16 CSS pixels, without a transform that visually shrinks them. This is an implementation convention to avoid Safari focus zoom; verify actual Safari behavior instead of claiming a universal browser guarantee. No autofocus when opening a sheet.
- Do not set `user-scalable=no` or `maximum-scale=1` globally. Disable accidental control gestures while preserving accessibility page zoom outside the scene. Scene zoom and page zoom are separate systems.
- Scope selection suppression to app chrome and game surfaces. Keep normal selection/copy in help, backup previews, errors, and editable text.
- Use Pointer Events; a second finger on the scene enters camera pinch mode and never records a pick. A gesture starting on the world must not activate the restart button when dragged over it.
- Handle Safari's dynamic toolbar, `dvh`, safe-area insets, rotation, and keyboard appearance. Use `visualViewport` only if a measured keyboard/viewport issue needs it. Do not freeze the whole page to an assumed screen height.
- The primary view should have no accidental horizontal scrolling or rubber-band camera movement. Sheets scroll normally and their controls remain reachable. Do not globally cancel every touch event.
- At least 48×48 CSS-pixel controls, visible focus, clear contrast, semantic buttons, dialog focus containment/return, Escape to close, and keyboard camera controls.
- Honor `prefers-reduced-motion`; provide the explicit override in Settings. Timer and functions remain usable if animations are disabled or WebGL fails.
- Provide a textual scene summary such as “Village: 20 buildings, garden and waterfront.” The canvas cannot be the sole source of progress information.
- If an icon-only control exists, give it an accessible label. Do not depend solely on a red/green color distinction.

## 11. Home Screen icon, manifest, and installation

Working icon: a small warm-roof cottage and green sprout on a deep teal rounded island field. Readable at 32px, no letters, no picking/medical imagery. Draw the original vector in code and rasterize once. The user should not need to make icons manually. The tile-set license does not require using its branding as the app logo.

Deliver actual local image files:

- `icons/apple-touch-icon.png`: 180×180, opaque background, square source image; let iOS apply its system mask.
- `icons/icon-192.png`: 192×192.
- `icons/icon-512.png`: 512×512.
- `icons/icon-maskable-512.png`: 512×512 with important content inside the central 80% diameter safe zone.
- `icons/favicon-32.png`: 32×32.
- `icons/source.svg`: editable source.

Do not substitute an SVG-only icon for the Apple touch PNG, generate the icon from the current changing village, or leave a default framework icon. Apple documents explicit page-specific `apple-touch-icon` links. [Apple configuration reference](https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariWebContent/ConfiguringWebApplications/ConfiguringWebApplications.html).

Example manifest, resolved relative to this app's directory:

```json
{
  "id": "./",
  "name": "Quiet Harbor",
  "short_name": "Quiet Harbor",
  "description": "Let a little world grow while you give your hands a break.",
  "start_url": "./index.html",
  "scope": "./",
  "display": "standalone",
  "background_color": "#173F49",
  "theme_color": "#173F49",
  "icons": [
    {"src":"./icons/icon-192.png","sizes":"192x192","type":"image/png","purpose":"any"},
    {"src":"./icons/icon-512.png","sizes":"512x512","type":"image/png","purpose":"any"},
    {"src":"./icons/icon-maskable-512.png","sizes":"512x512","type":"image/png","purpose":"maskable"}
  ]
}
```

Keep `id`, deployment folder, and `start_url` stable after release. An app path/origin migration needs an explicit save-transfer plan.

Install help: **Open in Safari → Share (possibly inside the page menu) → Add to Home Screen → keep “Open as Web App” enabled if shown → Add.** Use accurate text, not a fake install button that claims to control iOS. Hide the installation hint when launched standalone. Current Apple guidance describes the Home Screen flow and the Open as Web App option. [Apple iPhone guide](https://support.apple.com/guide/iphone/bookmark-a-website-iph42ab2f3a7/ios).

Icon rendering and installed storage behavior require a real iPhone check. Browser emulation cannot confirm the final Home Screen icon or all installed-app behaviors.

## 12. Offline and update strategy

Place `sw.js` inside the app folder and register with scope `./`. Use only relative app-local asset paths. Scope must not expand to The Library root. Service workers require HTTPS except supported local development origins. [Service worker lifecycle and usage](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers).

- Vendor one pinned, stable PixiJS v8 release locally, with release number and checksum. No runtime CDN dependency. Verify v8 initialization/API usage; do not paste v7 code into the renderer.
- Use a generated precache file list for the app shell, runtime modules, renderer, catalog, used textures, icons, and necessary notices. All required assets must download before claiming “Ready offline.”
- App-namespaced cache IDs, e.g. `quiet-harbor-assets-<release>`. Cache cleanup deletes only that app's obsolete caches; never all caches on the origin.
- Version coherent HTML/modules/assets together. An installation with a missing required asset fails rather than activating a partly cached release. Keep the previous working worker/cache until the replacement is ready.
- A new worker waits. Show “Update available” in Settings. Activate/reload only after user action while not holding, resetting, importing, or undoing. Never auto-reload a person mid-gesture.
- Keep saved runs in IndexedDB, separate from disposable asset caches. Updating artwork or a worker must not clear progress. Version generator/growth code so old runs retain their layout.
- Serve the scoped app shell for this app's navigation as appropriate; do not intercept unrelated library navigation. Confirm compatibility with any existing ancestor service worker before registration.
- Simulate airplane mode after a successful first visit. A first-ever visit with no connectivity cannot install missing assets; show a truthful load error.

## 13. Repository implementation layout

This planning change belongs under `docs/quiet-harbor/`. Do not register an unbuilt app in the library. At implementation time, create the app once under:

```text
apps/temporary-apps/library/YYYY-MM-DD-quiet-harbor/
  index.html
  styles.css
  app.js
  manifest.webmanifest
  sw.js
  precache-manifest.js
  core/
    time.js
    growth-v1.js
    random-v1.js
    world-v1.js
    persistence.js
    reset-controller.js
    backup.js
  scene/
    renderer.js
    camera.js
    residents.js
    wave.js
  assets/
    catalog.json
    sources.json
    atlases/
    licenses/
  icons/
  vendor/
    pixi-<pinned-release>.min.js
    PIXI-LICENSE.txt
  scripts/
    prepare-assets.mjs
    prepare-icons.mjs
    generate-precache.mjs
  tests/
    time.test.mjs
    growth-world.test.mjs
    reset-persistence.test.mjs
    browser-checklist.md
  README.md
```

Use the actual creation date in the folder once, then retain that path for updates. Buildless native modules fit the inspected repository: the current Pages workflow uploads repository files directly. Do not introduce a new site-wide build pipeline just for this app. Asset preparation may use local Node/Python tooling, but committed runtime files must work without a build on Pages. Do not put private saves, browser profiles, downloaded ZIP archives, or `node_modules` in the commit.

Keep domain functions independent of DOM/Pixi so timing and world generation can be tested with ordinary Node tests. A small dev-only package manifest is acceptable for necessary test/asset tooling; no server component is required. Use JSDoc types for boundary records and keep modules small enough to review.

The implementation change must also:

1. Add a `TEMP_APPS` entry near the top of `apps/temporary-apps/index.html` with the exact organized app path, creation/update date, name, and description.
2. Preserve the root `index.html` link to `apps/temporary-apps/index.html`.
3. Run `python scripts/verify-temporary-apps-index.py` successfully.
4. Commit only the app, required registration, and relevant documentation; push to GitHub per Sterling's repository instructions.
5. Verify the actual Pages workflow/deployment state before saying it is live. The inspected workflow deploys pushes to `main`; pushing a feature branch alone does not publish the app.
6. Return the verified live app URL if deployed. If awaiting merge/deploy, explicitly say so and provide the repository/branch link. Do not present a guessed future URL as live.

## 14. Implementation sequence with concrete completion gates

Complete the full sequence; these are work checkpoints, not six separate requests for Sterling's permission.

### A. Prove the art and mobile shell

Read applicable AGENTS.md files, inspect existing Pages/service-worker behavior, download/inspect assets, pin PixiJS, and make the icon family. Produce one attractive proof scene with aligned shore, path, houses, plants, and resident. Establish the responsive shell, real DOM timer position, and thumb-friendly button. **Gate:** no tile gaps or floating buildings at phone scale; no default starter branding.

### B. Build time and saved runs

Implement first start, timer decomposition, lifecycle refresh, IndexedDB state, history, clock policy, and backup. **Gate:** close for an emulated three days, reopen to the correct duration; refresh does not start a new run; save failure is visible and nondestructive.

### C. Build deterministic growth and exploration

Implement narrative events, growth anchors, stable core lots, district generation, resident ambience, camera, and textual scene summary. **Gate:** fixtures at 0s, 30s, 5m, 30m, 6h, 1d, 7d, 28d, 1y, and 10y show actual different development; same seed/version/time reproduces the world; new seeds vary it.

### D. Build the hold, transaction, and tsunami

Implement the gesture state machine, commit receipt, animation, reduced-motion path, undo, and multi-tab conflict behavior. **Gate:** short taps/partial holds/backgrounding never reset; one completed hold does; reload during the wave preserves exactly one new run.

### E. Finish PWA and mobile polish

Generate local precache manifest, test offline cold reopening and updates, finish Settings/History, verify icon files, selection behavior, focus sizing, safe areas, accessibility, and performance. **Gate:** airplane-mode reopen has a functioning timer/world/restart, the main UI does not zoom on repeated taps, and actual iPhone checks are documented as tested or pending.

### F. Integrate and deliver

Register the app, run required verifier and meaningful tests, review the scoped diff, commit/push, and determine deployment status. Include a short README with install steps, backup semantics, credits, test commands, and browser-test evidence. **Gate:** provide source commit and honest published/pending state. Never mark the entire app done because only the timer or an animated placeholder works.

## 15. Verification matrix

Use pure-function tests for tricky logic and real browser interaction for gestures and layout. Do not add tests that merely compare a constant to itself.

| Area | Required evidence |
| --- | --- |
| Duration | Boundary tests at 59→60s, 3,599→3,600s, 86,399→86,400s, week/year transitions, and the exact examples above. No smaller unit disappears. |
| Lifecycle | Refresh, browser back/forward restoration, overnight closed app, background/foreground, timezone/DST changes, backward clock change; no interval drift. |
| Seed stability | Rebuild the same world repeatedly; compare entity IDs/positions/variants. Later growth preserves earlier layout. Extra ambient randomness leaves buildings unchanged. |
| Growth | Milestone counts match the table/formula. Future districts continue after week four. Construction stages do not overwrite completed objects. |
| Layout | Multiple seeds have valid starting land, connected paths, nonoverlapping footprints, matching chunk seams, and reachable house entrances. |
| Hold | 999ms cancels; threshold commits once; release outside, slide off, pointercancel, second touch, blur, and tab hiding cancel. Two partial holds never add together. |
| Save/reset | Inject transaction failure; old run survives. Two tabs try reset together; only one replaces the expected active run. Reload during wave causes no duplicate reset. |
| Undo | Restores prior seed/start/history before the original deadline; reload doesn't extend it; undo fails safely after another restart/import. |
| Backup | Round trip, invalid/oversized/future-schema files, unsupported generator version, and replacement confirmation. Failure leaves original data intact. |
| Offline/update | Cold reopen offline after precache, missing asset during new install, updated worker waiting, old save surviving activation, unrelated app caches untouched. |
| Touch polish | Repeated button/timer taps do not zoom/select; reset hold causes no callout; scene pan/pinch doesn't move chrome; input focus doesn't auto-zoom. |
| Accessibility | Keyboard hold and assistive confirmation, focus management, reduced motion, text scene summary, large text, meaningful contrast, no per-second announcements. |
| PWA | Manifest/icons resolve from the nested Pages path; installed launch goes to this app; real iPhone Home Screen icon and standalone view are checked. |
| Repository | Required temporary-app verifier passes, registration path matches, scoped commit pushed, actual deployment state reported. |

### Browser/device coverage

- iPhone Safari and installed Home Screen app, in portrait and landscape, with the actual tested iOS version recorded.
- A compact width around 320–375 CSS pixels and a taller modern phone around 390–430 pixels; short landscape, 200% text, and keyboard-open sheets.
- Android Chrome and desktop Chromium/Firefox as secondary checks.
- A real touch browser for final gesture/install behavior; emulation is supplementary.

### Performance targets, to measure rather than assume

- Timer/shell usable promptly before art is ready; aim for under 1 second on a warm open.
- Aim for 30 fps or better on a representative older iPhone during ordinary exploration and wave; allow an adaptive low-detail tier.
- Cap renderer resolution at `min(devicePixelRatio, 2)` initially, frame rate at 30 for ambient motion, resident count at 24, and foam particles around 80 (lower tier 24).
- Initial complete offline payload target below 8 MB; texture atlas target at most 2048×2048 per page. If art quality requires more, measure and document the tradeoff rather than silently downloading whole asset libraries.
- Render visible chunks, bound the LRU, and use district-level detail at wide zoom. A ten-year fixture should not create every historical building sprite at startup.
- Stop the Pixi ticker when hidden. Reduced motion can use event-driven static renders. No background battery drain to advance time.
- Recover gracefully from renderer/context loss: preserve domain state and show timer/retry even if the scene cannot recover.

## 16. Definition of done and handoff boundaries

Sterling can install the page, begin once, leave it closed, return to a visibly richer coherent world, explore without managing it, and deliberately record a picking episode with a one-second hold. That creates exactly one fresh streak and one randomized beginning, accompanied by the requested wave. The app works offline after preparation and does not lose a run simply because a scene, gesture, or update failed.

The implementing agent owns asset acquisition, mapping, code, icons, QA, registration, commit, and push. Only inherently device-side steps—adding to the Home Screen and any unavailable real-device verification—may need Sterling. Report those limits plainly. Do not ask Sterling to hand-assemble a sprite pack, choose obscure architecture details, or repeatedly authorize ordinary implementation steps.

**This specification itself does not create an app or a live deployment.** Its repository publication is separate from the future app release.
