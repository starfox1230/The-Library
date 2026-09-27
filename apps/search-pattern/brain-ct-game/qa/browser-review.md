# Browser and final review

Tested 2026-09-22 in the Codex in-app Chromium browser on Windows, Intel Core Ultra 9 185H. Served the actual checked-in brain and bone volumes over localhost.

## Observed passes

- Full practice run: 70/70, all ten phases, zero missed clicks, using Locate and actual canvas clicks. All corrected optic nerve and superior maxillary sinus targets reachable.
- Full timed run: 70/70, zero missed clicks, all three planes, using normal plane/preset/slider controls without hints. Completion froze at 04:30.3; best persisted after reload. This was an automated functionality test, not a human benchmark. Test best was cleared through Reset personal best.
- Wrong window produced “Right region · adjust your window” without credit. Left drag did not score. Pause changed a timed attempt to practice. Restart returned to idle and reset the clock.
- Plane buttons and A/S/C keyboard handling, arrow scrolling, wheel scrolling, slider navigation, presets, typed numeric W/L, single/three-plane layout, double zoom, reset and checklist visibility worked. Typed W350/L60 persisted. Automation's programmatic fill did not dispatch native change reliably; keyboard entry was used for this test.
- An actual canvas hit succeeded after switching to three planes and zooming to 2×. Fractional sagittal Shift-click recenter followed by axial scrolling still scored the displayed zero-span scalp target after the quantization fix. Recenter itself gave no credit.
- 1440×900: imaging pane 1202 px, 83.5% of total width. 390×844: document width 375 px plus scrollbar, no horizontal overflow; plane and window controls reachable. Source images retained physical aspect ratio. Actual tested canvas ratio was 1; DPR 2 was not available through the viewport tool.
- Warm axial wheel-event-to-render timing, measured inside the real event handler through completed paint: 20 samples, median 3.3 ms, maximum/p95 sample 5.9 ms. All below 50 ms. Browser tool transport latency excluded. Measurement emitted by the app's console diagnostic.
- New library launch link resolves correctly. Existing CT Head selection, timer start/pause/reset and first-item checklist progression worked. Test checkbox was restored; existing library JS/storage were not changed.
- Final release loaded both volumes and enabled Start. No browser error logs observed. An earlier unavailable local server displayed the load error; restarting serving and reloading recovered. Explicit Retry after a corrupt asset was not browser-tested; loader rejection paths are unit-tested.

## Independent review and fixes

A fresh read-only reviewer found three issues. All were reproduced, corrected and regression-tested:

1. Fractional focus used for scoring while the image showed a rounded slice: shared `sliceNormal` now quantizes scoring and hints to the rendered slice.
2. Width-one paint used a gray ramp: actual RGBA paint now uses the DICOM binary threshold at W1, covered by a painted-pixel test.
3. Bone assets only checked physical alignment: the primary manifest now pins companion identity, case/checkpoint versions and checksum; mismatches prevent readiness.

Cache-sensitive metadata fetches bypass stored responses, and the static module graph carries a release version. Reviewer declined clinical anatomy/normality, licensing, real-browser and original-source conversion judgments; source/visual review and browser evidence are recorded separately. No clinical expert validation is claimed.

## Remaining verification limits

The available browser tool cannot hold right/middle buttons while dragging, so right-drag windowing and middle-drag pan were checked in code rather than exercised end-to-end. Numeric windowing and zoom provide tested alternatives. Its separate tabs did not produce a real hidden-document transition; the visibility listener and pause behavior were inspected and pause demotion was tested, but real tab-hiding was not reproduced in this environment. Clinical checkpoint validation remains outstanding; these are author-reviewed landmark patches, not complete anatomical segmentations.
