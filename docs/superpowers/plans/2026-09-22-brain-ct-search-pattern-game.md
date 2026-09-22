# Brain CT Search-Pattern Game Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a quiet, timed anatomical search-pattern game using a verified normal adult brain CT with linked axial, sagittal, and coronal views and true HU windowing.

**Architecture:** A static browser app loads one locally hosted HU volume and case-specific checkpoint annotations. Pure geometry and game-state modules handle coordinates, scoring, and time; a canvas renderer and a small interface provide image navigation. Offline Python tools prepare and validate the case without exposing original patient metadata.

**Tech Stack:** Native browser ES modules, Canvas 2D, Fetch, DecompressionStream, Web Crypto, localStorage, Node's built-in test runner, and Python for image preparation and contact sheets. Use NumPy and Pillow for preprocessing; install a pinned pydicom or nibabel version only after the selected input format requires it. No production web framework or remote runtime CDN.

**Spec:** `docs/superpowers/specs/2026-09-22-brain-ct-search-pattern-game-design.md` (approved by the user on 2026-09-22).

## Global Constraints

- “Version one contains one verified normal adult case, practice and timed modes, a collapsible checklist, and local personal-best storage.”
- “The game lives at `apps/search-pattern/brain-ct-game/`, with a launch link from the existing `apps/search-pattern/index.html`.”
- “No account or backend is required.”
- “Preserve HU and physical geometry; do not reduce the volume to 8-bit screenshots.”
- “Follow the lecture's order, with any order allowed among checkpoints inside the current phase.”
- “Bilateral targets require each side.”
- “A run started in practice never becomes a timed record.”
- “A volume is loaded once and shared across all views. Keep network requests out of scrolling and click handling.”
- “At 1440 × 900, the default layout leaves at least 75% of the content width for the scan.”
- “At 390 px width, controls remain reachable without horizontal page scrolling.”
- “A normal wheel event should render within 50 ms on the development machine after loading; measure and report the observed result.”
- “Keep commits scoped to the game, its launch link, and design/verification records; the working tree contains unrelated work.”

## Review Focus

1. Oblique or reversed source slices: anatomy, orientation markers, and scoring must still agree. Address with source normalization and asymmetric-volume tests in Tasks 1–2.
2. High-DPI canvas after zoom, pan, or layout change: a visible anatomical click must hit that same patient location. Address with inverse-transform tests and browser checks in Tasks 2 and 5.
3. Touchpad bursts, dragging, or keypresses in numeric inputs: navigation must not skip unpredictably, score a drag, or hijack text editing. Address with input-normalization tests in Task 4.
4. Tab hiding, failed storage, or reloading: invalid timed records must never become personal bests, and the app must remain usable. Address with injected-clock and throwing-storage tests in Tasks 3–4.
5. Partial asset loads or changing case versions: Start must remain disabled until matching case and annotation assets pass validation. Address with loader and manifest mismatch tests in Tasks 1 and 4.

## File map and shared contracts

All paths below are under `apps/search-pattern/brain-ct-game/` unless stated otherwise.

| File | Responsibility |
| --- | --- |
| `index.html`, `styles.css`, `app.mjs` | Accessible shell, layout, and event/state wiring |
| `volume.mjs` | Manifest validation, gzip decode, checksum, typed HU data |
| `geometry.mjs` | LPS coordinates, orthogonal planes, fit/pan/zoom mapping |
| `renderer.mjs` | Slice sampling, window mapping, coalesced canvas painting |
| `game.mjs` | Spatial target matching, phase progression, timer and eligibility |
| `input.mjs`, `records.mjs` | Input interpretation and resilient local records |
| `cases/normal-head/manifest.json`, `volume.i16.gz` | Accepted CT volume, dimensions, spacing, source/series metadata |
| `cases/normal-head/checkpoints.json`, `ATTRIBUTION.md` | Case-specific scoring geometry, version, teaching-source and image-source attribution |
| `tools/prepare_case.py`, `requirements-data.txt` | Reproducible case conversion; exact versions of used Python packages |
| `tools/render_checkpoint_qa.py` | Contact sheets showing every region at boundary/representative slices |
| `qa/case-review.md`, `qa/checkpoint-review.md`, `qa/browser-review.md` | Source acceptance, anatomical review, and actual browser results |
| `tests/*.test.mjs`, `tests/test_prepare_case.py` | Meaningful geometry, loading, timing, scoring, input, and storage tests |
| `README.md` | Running locally, controls, asset preparation, validation, and limitations |

Use an axis-aligned LPS volume after offline normalization: positive X = patient left, positive Y = posterior, positive Z = superior. Preserve source geometry/provenance separately. Arrays use X-fastest order: `index = x + nx * (y + ny * z)`. Store little-endian signed 16-bit HU values and an explicit voxel-centre origin in mm.

```js
// Manifest contract (literal field names; values are populated from accepted data).
// id, version, checkpointVersion: nonempty strings
// dimensions: [nx, ny, nz] positive integers
// spacing: [sx, sy, sz] positive finite millimetres
// originLPS: [ox, oy, oz] finite millimetres at voxel [0,0,0]
// volumeUrl: same-directory URL; encoding: 'gzip-i16le-hu'
// sha256: lowercase checksum of DECOMPRESSED bytes
// source: {url, attribution, license, normalityEvidence, seriesDescription,
//          reconstructionKernel, limitations}
// checkpoints: {caseId, caseVersion, version, phases:[{id,label,instruction,
//   sourceSeconds, targets:[{id,label,side,windows:[{width:[min,max],level:[min,max]}],
//     regions:[{plane, normal:[minMm,maxMm], polygon:[[uMm,vMm]], toleranceMm}],
//     representative:{plane,patient:[x,y,z],width,level}}]}]}
```

Plane projections use `(u,v,n)`: axial `(x,y,z)`, coronal `(x,-z,y)`, sagittal `(y,-z,x)`. Thus top is anterior on axial and superior on coronal/sagittal; screen right is patient left on axial/coronal and posterior on sagittal. Use the same basis for rendering, polygon annotation, and hit testing. Regions are per-plane physical polygons with reviewed normal-coordinate intervals. All tolerance distances are in mm.

## Task 1: Acquire, accept, and prepare the normal case

**Files:** Create `tools/prepare_case.py`, `requirements-data.txt`, `tests/test_prepare_case.py`, `cases/normal-head/manifest.json`, `cases/normal-head/volume.i16.gz`, `cases/normal-head/ATTRIBUTION.md`, and `qa/case-review.md`.

**Interfaces:** `normalize_volume(values, affine_lps) -> (values_lps, spacing, origin_lps)` returns a regular axis-aligned grid. `write_case(values_lps, spacing, origin_lps, metadata, output_dir)` emits the manifest and X-fastest gzip bytes. Reject undefined/invalid physical geometry and unsupported inputs explicitly.

- [ ] Read the approved spec, root AGENTS.md, and the using-git-worktrees skill. At execution time create an isolated checkout via the app's worktree tool; preserve the user's unrelated changes. Bring this approved spec and plan into that checkout if its starting commit lacks them.
- [ ] Investigate the primary source and raw-data access for Radiopaedia case 35508, then other public normal adult CT sources if necessary. Public normality evidence, reuse permission, raw HU, sufficient coverage, and usable reformats are all required. The Zenodo postoperative case is excluded. Log source URLs, licensing text references, slice spacing, and the acceptance decision in `qa/case-review.md`. Do not invent a dataset URL or classify “no hemorrhage” as normal.
- [ ] Download only a promising candidate's data into a task-specific staging directory outside the published app. Inspect metadata locally without logging identifiers. Verify source normality evidence and source geometry; render all three planes for review. If no suitable case is obtainable, report the precise missing requirement and request an anonymized normal volume; do not mark this task complete or silently relax the design.
- [ ] Once the format is known, pin the exact conversion-library versions actually used. Write the conversion tests before implementation:

```python
import unittest
import numpy as np
from tools.prepare_case import normalize_volume

class PrepareTests(unittest.TestCase):
    def test_reversed_axis_keeps_patient_coordinates(self):
        src = np.array([[[11]], [[22]], [[33]]], dtype=np.int16)
        affine = np.diag([-1., 2., 3., 1.])
        affine[0, 3] = 10.
        out, spacing, origin = normalize_volume(src, affine)
        self.assertEqual(out[:, 0, 0].tolist(), [33, 22, 11])
        self.assertEqual(list(spacing), [1., 2., 3.])
        self.assertEqual(list(origin), [8., 0., 0.])

    def test_singular_geometry_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_volume(np.zeros((2, 2, 2)), np.zeros((4, 4)))
```

- [ ] Run `python -m unittest discover -s tests -p test_prepare_case.py` from the game directory and confirm failure from the missing converter. Add tests for slope/intercept HU preservation, oblique landmark positions, little-endian byte order, and nonuniform DICOM slice spacing before implementing those cases. Unsupported source geometry must fail with a clear message instead of guessing an affine.
- [ ] Implement source conversion: sort DICOM frames by physical position, apply per-frame slope/intercept, verify consistent geometry, or use the NIfTI affine and scaling. Normalize oblique geometry using trilinear resampling with air padding (`-1000 HU`) and an explicit output grid; reorder orthogonal axes without unnecessary interpolation. Round to the nearest HU, reject values outside int16 rather than wrapping, and serialize:

```python
raw = np.rint(values_lps).astype('<i2').tobytes(order='F')
# Hash `raw` with hashlib.sha256; write gzip.compress(raw, mtime=0).
# Reopen the gzip, verify byte equality, then emit the geometry manifest.
```

- [ ] Compare source and normalized HU at several interior landmarks; record interpolation differences where applicable. Check left/right, head coverage, skull base, and soft-tissue appearance against the source. Document kernel limitations and whether a matching bone reconstruction exists. If included, give the second volume its own dimensions/geometry/checksum and validate alignment before using it for the bone phase.
- [ ] Run the converter tests to green; inspect actual asset sizes before committing. Do not add source archives or individual files exceeding the repository host's file-size limit. Split a large payload into explicit, checksummed chunks if required and extend the loader contract/tests before proceeding. Commit only the accepted case, converter, tests, pins, attribution, and review record: `git commit -m "feat: prepare verified normal head CT case"` after staging those exact paths.

## Task 2: Build the three-plane HU viewer

**Files:** Create `volume.mjs`, `geometry.mjs`, `renderer.mjs`, `tests/volume.test.mjs`, `tests/geometry.test.mjs`, `tests/renderer.test.mjs`.

**Interfaces:** `loadVolume(manifestUrl, {fetcher=fetch,onProgress}) -> Promise<{manifest,values:Int16Array}>`; `project(patient,plane) -> [u,v,n]`; `unproject([u,v,n],plane) -> patient`; `createViewTransform({width,height,bounds,zoom,pan}) -> {toScreen,toPlane}` where width/height and pan use CSS pixels. `windowHU(hu,width,level) -> integer 0..255`. `sampleSlice(volume,plane,normalMm) -> {pixels,width,height,bounds}`. `paintViewport(canvas,volume,view,overlay)` paints image, orientation, and optional crosshairs/hints; `view` holds plane, patient focus, zoom, pan, width, and level.

- [ ] Write asymmetric geometry and quantitative window tests:

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import {project,unproject,createViewTransform} from '../geometry.mjs';
import {windowHU} from '../renderer.mjs';
test('every plane preserves a distinct patient location',()=>{
  const p=[11,23,37];
  for(const plane of ['axial','coronal','sagittal'])
    assert.deepEqual(unproject(project(p,plane),plane),p);
  assert.deepEqual(project(p,'coronal'),[11,-37,23]);
});
test('brain window maps outside bounds and the centre',()=>{
  assert.equal(windowHU(-1000,80,40),0);
  assert.equal(windowHU(1000,80,40),255);
  assert.ok(Math.abs(windowHU(40,80,40)-129)<=1);
});
test('pan and zoom remain invertible',()=>{
  const t=createViewTransform({width:901,height:711,bounds:[-90,-120,90,120],zoom:1.7,pan:[31,-17]});
  const result=t.toPlane(t.toScreen([13,-29]));
  assert.ok(Math.hypot(result[0]-13,result[1]+29)<1e-8);
});
```

- [ ] Run `node --test tests/geometry.test.mjs tests/renderer.test.mjs`; confirm the missing module/export failures. Add a synthetic asymmetric volume with distinct values in each axis and assert expected slices, outside-volume behaviour, and left/right orientation.
- [ ] Implement the shared plane bases and physical fit transforms. Map pointer coordinates from `getBoundingClientRect()` to CSS pixels; account for devicePixelRatio only when allocating/painting canvas backing pixels. Resizing must update both rendering and pointer transforms in the same frame.
- [ ] Implement HU windowing using the DICOM linear width/level rule and clamping (reject width below 1):

```js
const low=level-0.5-(width-1)/2;
const high=level-0.5+(width-1)/2;
if(hu<=low) return 0;
if(hu>high) return 255;
return Math.round(((hu-(level-0.5))/(width-1)+0.5)*255);
```

- [ ] Build `loadVolume` with injectable fetch, HTTP failure checks, positive dimensions/spacing validation, bounded decompression, decoded-length and checksum verification, and explicit little-endian decoding. Reject unsafe dimensions, mismatched encoding, nonfinite metadata, and corrupt bytes. Write loader tests with generated tiny gzip payloads, failed fetches, truncation, incorrect hash, and an unexpected byte count. Run `node --test tests/volume.test.mjs` red, implement, then rerun green.
- [ ] Implement slice sampling and coalesce wheel/render requests through `requestAnimationFrame`. Reuse typed pixel buffers; use the same volume for all planes. Limit repainting to changed viewports. Preserve shared focus on plane changes and clamp scrolling to the valid physical extent. Paint visible orientation markers and slice position.
- [ ] Run all Node tests and manually inspect the accepted volume in all three planes once wired into the shell in Task 4. Commit the independently tested viewer modules: `git commit -m "feat: add linked HU brain CT viewer"` with only this task's files staged.

## Task 3: Annotate the case and implement the game engine

**Files:** Create `cases/normal-head/checkpoints.json`, `game.mjs`, `tests/game.test.mjs`, `tests/fixtures.mjs`, `tools/render_checkpoint_qa.py`, `qa/checkpoint-review.md`.

**Interfaces:** `createGame({phases,caseId,caseVersion,checkpointVersion,mode,now})` returns methods `start(ready)`, `click({patient,plane,width,level})`, `pause()`, `resume()`, `restart(mode)`, `snapshot()`. `now` returns monotonic milliseconds. Snapshots expose `{status,mode,eligible,phaseId,completed,elapsedMs,misses}`. Click results have `{kind:'hit'|'miss'|'window'|'ignored',targetId?}`. `validateCheckpoints(manifest,checkpoints)` throws on invalid case/version, phase, region, or representative point.

- [ ] Correct anatomy names against the lecture visuals. Author original concise instructions, timestamp links, and the ten approved phases. Create actual case-specific polygons using Task 2's plane coordinates and a source viewer/contact-sheet inspection. Separate left and right targets, use multiple superior/mid/inferior and spatially distinct checkpoints for broad regions, and define short slice intervals for small structures. Do not infer anatomical contours from generic head proportions.
- [ ] Define accepted numeric width/level intervals for each checkpoint and record their rationale in the review file. Initial presets are brain W80/L40, subdural W200/L75, and bone W2500/L500; verify their usefulness on the chosen source. Soft-tissue review accepts the appropriate brain or wider soft-tissue ranges per target; do not require an exact preset name. Region tolerances start at zero and are increased only after adjacent-anatomy review, with the final mm value stored per region.
- [ ] Make `tools/render_checkpoint_qa.py` use the manifest and annotation coordinates to output a labelled contact sheet for every target, showing the normal-interval endpoints and representative slice, with and without its outline. Inspect each image; fix misplaced or overly permissive targets. Record every target ID, plane, slice interval, laterality, window range, and pass/fail outcome in `qa/checkpoint-review.md`. Do not claim clinical expert review unless performed by one.
- [ ] Add a tiny synthetic fixture for engine tests:

```js
export const phases=[{id:'scalp',label:'Scalp',instruction:'Select both sides',sourceSeconds:144,
 targets:['left','right'].map((side,i)=>({id:side,label:side,side,
 windows:[{width:[60,120],level:[25,55]}],
 regions:[{plane:'axial',normal:[9,11],polygon:[[i*20,0],[i*20+10,0],[i*20+10,10],[i*20,10]],toleranceMm:0}],
 representative:{plane:'axial',patient:[i*20+5,5,10],width:80,level:40}}))}];
```

- [ ] Write failing engine tests before implementation:

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import {createGame} from '../game.mjs';
import {phases} from './fixtures.mjs';
test('window and duplicate clicks cannot complete both sides',()=>{
 let time=0;
 const g=createGame({phases,caseId:'test',caseVersion:'1',checkpointVersion:'1',mode:'timed',now:()=>time});
 g.start(true);
 assert.equal(g.click({patient:[5,5,10],plane:'axial',width:2500,level:500}).kind,'window');
 assert.equal(g.click({patient:[5,5,10],plane:'axial',width:80,level:40}).kind,'hit');
 assert.equal(g.click({patient:[5,5,10],plane:'axial',width:80,level:40}).kind,'ignored');
 assert.equal(g.snapshot().completed.length,1);
 time=2000; g.pause(); time=9000; g.resume(); time=9500;
 assert.equal(g.snapshot().elapsedMs,2500);
 assert.equal(g.snapshot().eligible,false);
 assert.equal(g.snapshot().mode,'practice');
});
```

- [ ] Run `node --test tests/game.test.mjs` and confirm failure. Add named tests for outside polygons, slice boundaries, wrong plane/side, adjacent anatomy, tolerance, overlap ordering, phase gating, incomplete loading, all-phase completion, frozen completion time, restart, and manifest/version mismatch. Also test malformed polygons and representative points outside their own regions.
- [ ] Implement polygon containment plus distance-to-segment tolerance in physical coordinates. Filter by phase, incomplete target, plane, and interval first; sort spatial matches by polygon area then target ID; apply window criteria to the selected spatial target. One event scores at most one target. Ignore completed-only hits. Increment misses only for spatial misses while running, not drag/recentre/paused events.
- [ ] Implement explicit `idle/running/paused/complete` states. Start requires ready data; pause demotes timed to practice; resume preserves elapsed time; completion freezes time. Restart returns to idle and requires Start. Validate every annotation and case/version match before allowing a run.
- [ ] Run engine tests and all prior tests, regenerate contact sheets after annotation changes, and commit only final annotations, engine, tests, and QA: `git commit -m "feat: validate anatomical search checkpoints and timed runs"`.

## Task 4: Build the quiet interface and integrate the library

**Files:** Create `index.html`, `styles.css`, `app.mjs`, `input.mjs`, `records.mjs`, `tests/input.test.mjs`, `tests/records.test.mjs`, `README.md`; modify `apps/search-pattern/index.html` by adding one launch link in its header actions.

**Interfaces:** `normalizeWheel(event,carry) -> {steps,carry}` converts pixel/line/page delta modes to bounded slice steps; `isGameShortcut(event) -> boolean` rejects editable targets and modifier chords; `isClick(start,end) -> boolean` rejects drags over 4 CSS px. `readBest(storage,key) -> number|null`; `saveBest(storage,key,snapshot) -> number|null`; `recordKey({caseId,caseVersion,checkpointVersion,mode}) -> string` with prefix `brain-ct-game:v1:`. Storage errors are caught at this boundary.

- [ ] Write and run failing input/storage tests:

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import {isClick,isGameShortcut} from '../input.mjs';
import {readBest,saveBest} from '../records.mjs';
test('drag and numeric input do not trigger game actions',()=>{
 assert.equal(isClick([0,0],[12,0]),false);
 assert.equal(isGameShortcut({target:{tagName:'INPUT'},ctrlKey:false,metaKey:false,altKey:false}),false);
});
test('storage failure is harmless and paused runs are ineligible',()=>{
 const storage={getItem(){throw Error('blocked')},setItem(){throw Error('blocked')}};
 assert.equal(readBest(storage,'k'),null);
 assert.equal(saveBest(storage,'k',{status:'complete',eligible:false,mode:'practice',elapsedMs:1234}),null);
});
```

- [ ] Add tests for wheel bursts/delta modes, touch pointer cancellation, corrupted/negative stored durations, distinct case and annotation versions, and eligible-only record replacement. Implement the small input/storage modules and rerun tests to green.
- [ ] Build semantic controls and the canvas region with this layout basis:

```css
.workspace { display:grid; grid-template-columns:minmax(0,1fr) min(240px,22vw); min-height:0; }
.workspace.checklist-hidden { grid-template-columns:minmax(0,1fr); }
.viewport { position:relative; min-width:0; min-height:0; overflow:hidden; }
canvas { display:block; width:100%; height:100%; touch-action:none; }
@media(max-width:700px) { .workspace { grid-template-columns:1fr; } .toolbar { flex-wrap:wrap; } }
```

- [ ] Wire loading/progress/error/retry and version validation before enabling Start. Disable run-dependent controls on failed load. Create defaults: axial, fit-to-view, brain preset, crosshairs off, checklist visible. Provide A/S/C buttons/shortcuts, arrow and slider scrolling, preset buttons, numeric W/L controls, right-drag windowing, explicit zoom control, middle-drag pan, reset, optional three-plane view, optional crosshairs, and help.
- [ ] Maintain the shared patient focus; Shift-click recentres without scoring and a hit updates focus. Select active view before using its controls. Stop page scrolling only over the viewer. Numeric inputs, editable content, and browser modifier shortcuts remain unaffected. Touch users can use slider, numeric window, and zoom controls; ordinary image taps score without requiring a gesture.
- [ ] Connect the ten phases, progress count, and subtle feedback to engine snapshots. Practice hint controls reveal one selected current-phase target and its representative slice. Hide these controls and all overlays in timed mode. Pause or `document.visibilitychange` while hidden calls `game.pause()` and clears scoring gestures. Display the changed practice status before resuming.
- [ ] On completion show elapsed time, misses, mode, and local best without covering the image. Clear highlights and timer state on restart. Link sources and image attribution in a small details panel; explain reconstruction-kernel limitations there. Persist only eligible completed records; refreshing starts idle.
- [ ] Add `<a class="btn primary" href="brain-ct-game/index.html">Brain CT search game</a>` to the existing Search Pattern Library actions, preserving its data, timer, and storage. Write README commands using `python -m http.server 8765 --bind 127.0.0.1` from the repository root and the exact `/apps/search-pattern/brain-ct-game/` URL.
- [ ] Run `node --test tests/*.test.mjs` from the game directory. Commit the interface, supporting modules/tests, README, and the single library link: `git commit -m "feat: connect minimal brain CT search game interface"`.

## Task 5: Verify the real case and finish

**Files:** Update `qa/case-review.md`, `qa/checkpoint-review.md`, `qa/browser-review.md`, and README with actual outcomes; change product files only to resolve observed failures.

**Interfaces:** This task exercises the public app and the existing library through their served URLs, not a separate mock implementation.

- [ ] Run the full Node and Python test suites once after the last code change, plus `git diff --check`. Inspect every result. Re-run only affected checks when fixing a failure, followed by the final relevant suite.
- [ ] Read the computer-use skill before browser interaction. Start the local server without a visible helper window, and use supported browser tools for actual UI operation and screenshots. Verify loading, retry, Start readiness, A/S/C, wheel, arrows, slider, right-drag and numeric windowing, zoom/pan, reset, and single/three-plane modes with the accepted scan.
- [ ] Test at 1440 × 900 and 390 px wide, including devicePixelRatio 2 if available. Confirm image aspect ratio/orientation, usable focus indicators, no horizontal overflow, and >=75% default desktop width for images. Score known targets after zoom, pan, resize, and plane transitions to expose transform mistakes.
- [ ] Complete one practice run using hints and one timed run without hints through all ten phases. Attempt wrong-side, adjacent-anatomy, wrong-window, wrong-plane, and repeated clicks. Check final time, personal best, refresh, pause demotion, and tab-hiding demotion. Confirm no drag/recentre event scores. Verify every annotated target is reachable through normal controls.
- [ ] Measure wheel event-to-render latency on the development machine after warm loading and record the browser, hardware, sample count, and observed timings in `qa/browser-review.md`. If ordinary events exceed 50 ms, profile the renderer, reduce unnecessary allocations/repaints, and repeat the measurement. Do not hide a slow result behind an unmeasured claim.
- [ ] Check original and normalized CT landmarks side-by-side, all annotation contact sheets, source attribution/license, asset hashes, and source links. If any required anatomy is not visible or any target cannot be accurately placed, do not label the case/game complete; resolve the case or explain the specific blocker.
- [ ] Recheck the existing Search Pattern Library's study selection, checklist, timer, and stored progress after adding the launch link. Review the final diff for unrelated changes and accidental source data/identifiers.
- [ ] Use the requesting-code-review and verification-before-completion skills before claiming completion. Resolve actionable findings and record any limits accurately. Commit the final scoped fixes and QA. Follow the finishing-a-development-branch skill and the user's chosen integration method; attach any created PR with the app tool. This app is outside `apps/temporary-apps/library/`, so its temporary-app registration rule does not apply.
- [ ] Deliver the usable local preview and repository path, briefly state what was built and verified, cite the case and lecture sources, and identify any remaining limitations. Never call the task complete on the strength of synthetic tests alone.

## Execution recommendation and current status

Use native execution in this session with one final independent review: the geometry, selected case, and annotations share enough context that keeping implementation together is useful. Subagent-driven execution remains an option if the user prefers independent review after each task. The user has approved the design spec; this plan awaits review and selection of execution method. No product code or dataset has been changed by writing this plan.
