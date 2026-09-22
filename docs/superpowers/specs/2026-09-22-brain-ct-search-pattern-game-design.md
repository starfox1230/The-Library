# Brain CT search-pattern game

Status: conversational design approved on 2026-09-22; written spec ready for review. Implementation has not started.

## Purpose and scope

Build a simple, visually quiet browser game in The Library that lets Sterling practise a complete normal noncontrast brain CT search pattern as quickly as possible. The user scrolls real images, changes between axial, sagittal, and coronal planes, adjusts the CT window, and clicks the relevant anatomy to complete the pattern. Completion measures demonstrated navigation and selected anatomical checkpoints; it cannot establish that the user inspected every voxel or excluded disease.

Version one contains one verified normal adult case, practice and timed modes, a collapsible checklist, and local personal-best storage. The game lives at `apps/search-pattern/brain-ct-game/`, with a launch link from the existing `apps/search-pattern/index.html`. Its assets and progress remain independent of the existing checklist library. No account or backend is required.

## Teaching source

Andrew Dixon, *Brain CT: search patterns and check areas*, Radiology Channel / Radiopaedia: https://www.youtube.com/watch?v=u3NPBiYDqwA.

The initial general survey at approximately 2:00–8:45 supplies the sequence. The supplied 23:58 link falls within later pathology examples. The user approved building the full normal-case survey first. Clinical presentation-specific pathology rounds are outside this version.

Captions were retrieved during research. Anatomical terms need correction against the lecture visuals before they enter the app: the automatic captions misrecognize several structures. Brief original instructions and timestamp links will be used; the full transcript and lecture images will not be bundled.

## Viewer and layout

- The scan occupies most of a neutral dark screen. A slim top bar contains plane selection, window presets, start/pause/restart, elapsed time, and completion count. A narrow collapsible side panel shows checklist progress.
- Default to one large axial image. `A`, `S`, and `C`, or labelled buttons, select planes. Optional three-panel mode displays all planes with the active viewport outlined subtly. Small screens use one viewport.
- Preserve a shared anatomical focus in patient coordinates. Wheel scrolling moves along the active plane's normal axis. Plane switching intersects the shared focus; a separate Shift-click recentres the focus without scoring a target. Successful target clicks also update focus. Crosshairs are optional and hidden by default.
- Mouse wheel and arrow keys scroll. Provide a labelled slice slider for touch and keyboard access. Right-drag adjusts width/level; visible width/level controls provide an alternative. A drag never counts as a game click.
- Brain, subdural, and bone presets coexist with continuous numeric width/level adjustment and a reset-view button. Preset values and units are visible in the controls. Manual adjustment is assessed by actual width/level, not the selected preset label.
- Show patient orientation markers and slice position. Fit the image using physical voxel spacing, preserving proportions after resizing and switching planes. Zoom and pan must use the same reversible coordinate transform as hit testing.
- Feedback is a small, short-lived confirmation and a checklist checkmark. No modal dialogue, sound, confetti, or persistent target outlines interrupt a run. A help popover lists controls.

## Search-pattern phases

Follow the lecture's order, with any order allowed among checkpoints inside the current phase. Display the current phase and its short instruction even when the checklist is collapsed.

| Phase | Required review | Plane / window |
| --- | --- | --- |
| 1 | Scalp and extracranial soft tissues, including below the skull base | Axial / soft tissue |
| 2 | Vertex falx, sulci, cortical gray-white differentiation, and convexity extra-axial spaces | Axial / brain; extra-axial check on a wider window |
| 3 | Caudate nuclei, internal capsules, lentiform nuclei, thalami, and insular ribbons | Axial / brain |
| 4 | Sylvian fissures, MCA regions, basal cisterns, interpeduncular cistern, and midbrain | Axial / brain |
| 5 | Lateral ventricles, septum pellucidum, occipital horns, and temporal horns | Axial / brain |
| 6 | Brainstem, cerebellum, cerebellopontine angles, foramen magnum, and vertebral artery regions | Axial / brain |
| 7 | Sella and orbits | Axial / soft tissue |
| 8 | Pituitary region, brainstem, tonsils, transverse sinuses, and optic nerves | Sagittal / soft tissue |
| 9 | Superior sagittal/transverse sinuses, falx, tentorium, and convexity extra-axial spaces | Coronal / soft tissue; extra-axial check on a wider window |
| 10 | Calvarium, temporal bones/mastoids, and paranasal sinuses | Bone window; axial and coronal checkpoints |

The table summarizes the source; the individual checkpoint manifest supplies exact labels, source timestamps, bilateral requirements, plane rules, and acceptable width/level intervals. Bilateral targets require each side. Broad regions use spatially separated checkpoints at several levels, preventing one click from completing an entire sweep. Checkpoint counts are determined from the verified case's visible anatomy and recorded explicitly before gameplay QA.

## Click validation and scoring

1. Convert a click from canvas coordinates through pan/zoom and plane orientation into the loaded case's patient coordinates.
2. Consider only uncompleted checkpoints in the current phase, on an allowed plane and within that checkpoint's slice extent.
3. Require containment in a case-specific anatomical region. Store regions as reviewed plane-specific polygons with explicit slice intervals, linked to patient coordinates. Do not reuse generic screen boxes across scans. Delicate structures receive annotations on individual slices or short reviewed intervals rather than unverified interpolation across long spans.
4. Use a small physical-distance tolerance recorded per target. Regions and tolerances must not credit neighbouring anatomy or the opposite side. If regions overlap, one click can complete only one checkpoint: choose the smallest containing region, then a stable checkpoint ID as the tie-breaker.
5. Check actual width/level against the target's accepted intervals. If the anatomy matches but the window does not, show a short window hint without credit. Anatomically incorrect clicks show a subtle neutral miss indicator and do not advance progress.
6. Repeated clicks on completed targets do not score. A phase advances only when every required checkpoint is complete. Earlier anatomy remains freely navigable, but later phases do not receive premature credit.

Practice mode exposes an optional hint that highlights only the current selected target and offers a jump to its representative slice. Timed mode has no target outlines or jump-to-target controls. A run started in practice never becomes a timed record.

The timer begins only after the complete volume and annotations are ready and the user presses Start. Use a monotonic clock. Pause and browser visibility loss freeze time and block scoring; any paused timed attempt becomes practice and cannot replace a personal best. Restart clears all checkpoint state and starts a fresh attempt after an explicit Start. The timer stops automatically on the last checkpoint. The result shows elapsed time, misses, mode, and personal best. Misses add no arbitrary time penalty; random clicks already consume time and cannot satisfy spatial, plane, and window requirements.

Store personal bests locally by case ID, case version, checkpoint version, and mode. Corrupt or unavailable storage must not prevent play. Do not restore a partially completed timed run after a page reload.

## Case acquisition and release requirement

Select a de-identified, publicly reusable normal adult noncontrast head CT with raw intensity values, reliable physical geometry, and complete coverage from vertex through skull base. Prefer a soft-tissue reconstruction with at most 1.25 mm slice spacing for useful sagittal/coronal reformats. Include a matching bone reconstruction if supplied; changing the window alone does not reproduce a different reconstruction kernel.

Before accepting the case, verify its source report or teaching description supports normality, its reuse terms permit distribution with this app, the coverage supports every required checkpoint, and all three planes are visually usable. A label such as “no hemorrhage” is insufficient evidence of normality. Save source URL, attribution, license, series description, geometry, integrity checksum, and limitations with the case. Do not publish patient identifiers or unreviewed DICOM metadata.

Research findings as of 2026-09-22:

- Radiopaedia's Normal Neuroradiology playlist identifies a normal brain CT case (case 35508). Direct case retrieval returned HTTP 406 during research; downloadable raw volume and reuse suitability remain unverified. Source: https://radiopaedia.org/play/22945?lang=us.
- Zenodo record 3374839 provides a 0.625 mm CT volume under CC BY 4.0, but its description explicitly says follow-up after left frontal drill-hole trepanation. Exclude it from the normal case. Source: https://zenodo.org/records/3374839; description and license verified via its public API.
- PhysioNet CT-ICH supplies raw scans, but the documented approximately 5 mm slice thickness and trauma cohort make it a poor default for this request. Absence of hemorrhage does not establish normality. Source: https://physionet.org/content/ct-ich/1.3.0/.

No case has yet passed the acceptance requirements. Case selection and visual review are the first implementation milestone. If a suitable distributable normal volume cannot be obtained, report that specific blocker and request a suitable anonymized volume; do not substitute a postoperative case, a synthetic scan, or pre-windowed screenshots while claiming the requested game is complete.

## Components and data flow

Use a static browser app consistent with the repository. Prepare the chosen case offline into a compressed signed 16-bit HU volume and a small geometry/provenance manifest. Native source data remain the reference for verification. Preserve HU and physical geometry; do not reduce the volume to 8-bit screenshots. Separate licensed assets from code, and pin any required viewer dependency version.

Components have explicit boundaries:

- Volume loader: fetch, validate dimensions and expected byte count, decompress, and expose HU sampling plus voxel/patient transforms. Handle corrupt, missing, or unsupported case data with an actionable error and Retry.
- Renderer: create correctly oriented orthogonal slices, apply true HU windowing, maintain focus/pan/zoom, and convert screen coordinates to patient coordinates. Use one canvas per visible plane with a render loop that coalesces input events.
- Case/checkpoint manifest: immutable metadata, reviewed region geometry, phase order, source timestamps, laterality, accepted plane/window rules, and version identifiers.
- Game engine: deterministic checkpoint matching, phase transitions, run state, timing, and result eligibility. It must be testable independently of rendering.
- Interface/storage: accessible controls, quiet progress feedback, optional hints, local records, and links back to the library and sources.

A volume is loaded once and shared across all views. Keep network requests out of scrolling and click handling. Show loading progress; enable Start only after the case is usable. Host assets with the app when redistribution permits; never make normal gameplay depend on scraping a live third-party viewer.

## Verification and acceptance

- Check HU values, voxel spacing, orientation, head coverage, and several axial/coronal/sagittal landmarks against the original source data. Explicitly check left/right and superior/inferior; annotations must not be mirrored.
- Visually review every scoring region against the loaded scan in its allowed planes, including representative slices and both boundaries of each interval. Verify bilateral targets separately. Preserve review contact sheets and a checkpoint QA record.
- Test correct hits, adjacent-anatomy misses, out-of-slice clicks, wrong laterality, wrong window, overlapping targets, duplicate clicks, phase gating, and pan/zoom/resize coordinate mapping.
- Test the timer's loading/start/pause/visibility/completion behaviour and personal-best eligibility/version separation.
- Browser-test a complete practice and timed run, keyboard and mouse controls, continuous windowing, plane switching, three-panel mode, resizing, loading errors, and storage failures.
- At 1440 × 900, the default layout leaves at least 75% of the content width for the scan. At 390 px width, controls remain reachable without horizontal page scrolling. A normal wheel event should render within 50 ms on the development machine after loading; measure and report the observed result.
- Verify all links and the existing Search Pattern Library still work. Keep commits scoped to the game, its launch link, and design/verification records; the working tree contains unrelated work.

The feature is complete only when the accepted normal case is bundled, all required phases can be completed using validated anatomy clicks, all three planes and true windowing work, and the checks above pass. A working viewer with placeholder annotations is not a completed game.
