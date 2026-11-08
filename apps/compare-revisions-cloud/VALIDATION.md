# Verification record

## November 7, 2026: item details and sticky downloads (2026.11.07.4)

- 116 offline Python tests pass, including the updated hidden-by-default report
  wording contract and explicit submitted preference preservation.
- `check-revision-details.cjs` verifies intrinsic button/search sizing and genuine
  single-row fit; two expanded cases with multiple revisions confirm hidden
  defaults, no hover expansion, per-item pin/re-pin/unpin, independent all-case
  reason/evidence controls and correct centering of wrapped action labels.
- Measured expansion heights progress from zero through an intermediate height
  to full height. Reduced-motion styling removes the transition. No scores or
  clinical judgments are changed by these controls.
- A simulated clock verifies that hovering holds the reminder past 12 seconds,
  then leaving keeps it visible for another 3.9 seconds and hides it after four.
- Exported readers verify that compact banner actions are initially absent,
  appear only after scrolling past the original toolbar, disappear on returning,
  work for full-copy and flagged-only downloads, and preserve exact banner
  height at desktop and 390px widths. Screenshots were inspected.
- `check-report-viewport.cjs` verifies the exported reader's stripped header and
  complete linked quote visibility with a PHI banner in 900/600/420px viewports,
  compact/dense summaries, inline/split views and 125%/150% CSS scaling. The
  difficult case-end clipping condition passes without moving document scrollY.
  `check-highlights.cjs` retains repeated/overlapping source matching, no heading
  leakage, source-text fidelity, pin/unpin and responsive checks; assertions for
  removed status/navigation UI were replaced by absence checks and re-click unpin.
- Existing compact-review, marks, perspectives/severity, reader/OCR-source and
  OCR-review browser suites cover the prior functionality. All data/model
  responses are synthetic. Deployment remains pending; use footer 2026.11.07.4.


## November 7, 2026: red OCR review action (2026.11.07.3)

- `check-ocr-review.cjs` verifies the pending count, prominent red background in
  light/dark themes, and return to neutral/disabled after resolving all rows.
  Existing sequence, overlap, crop, keyboard and conflict checks also pass.
- 116 offline Python tests pass; template assembly remains synchronized.
  OCR/analysis rules and authentication are unchanged. Deployment is pending.

## November 7, 2026: 13 compact-review improvements (2026.11.07.2)

- **116 offline Python tests passed.** Assembled source and authoring template
  match; prompt exports remain unchanged at 1.8 / dual-title 1.2. No clinical
  model, deployment setting, authentication or export-scope rule changed.
- **`check-compact-review.cjs` passed in Edge:** continuous header hover and
  neutral icon fills in both themes, no pointer outline, retained keyboard
  focus, gold/red selected states, generic feedback wording, counted icon filters,
  secondary filters under More with an active count, and no redundant counters
  or persistent warning. Two expanded cases verify that reasons start hidden,
  toggle independently of each other and of evidence, and remain in exported
  JSON while reopening hidden.
- The simulated clock verifies that the reminder disappears after four seconds
  and returns on marking/unmarking. Its action works within the feedback modal,
  on the website and in an offline file. A filtered export with no visible cases
  still produces all four cases when using the reminder's full-copy action.
  Source numbering, annotations and feedback explanations survive. The reminder
  is hidden on reopening; More stays within a 390px viewport. Desktop light/dark
  and mobile screenshots were inspected.
- Existing `check-marks.cjs`, `check-perspectives-severity.cjs` and
  `check-reader-sources.cjs` verify annotation/provenance roundtrips, flagged-only
  export privacy, saved preferences, severity colors, dual titles, local OCR,
  source crops and correction/save/reopen. All inputs and model responses are
  synthetic; these checks do not establish clinical grading accuracy.
- Deployment is pending. Replace/redeploy `main.py`; the footer identifies
  **2026.11.07.2**. Existing downloaded HTML files are not modified remotely.

## November 7, 2026: clinical-action rubric and case annotations (2026.11.07.1)

- **116 offline Python tests passed.** This includes clinical-only export scope,
  grouped source numbering, typed annotation limits, old/unknown provenance,
  flagged-only server selection, lookup exclusion, HTML-shaped comment handling,
  exact shared prompt exports, new defaults, template assembly, authentication
  and CSRF. Model calls and identity are substituted; no live API usage occurred.
- **`check-marks.cjs` passed in native headless Edge.** Fresh visits choose
  Attending/dark even when the OS reports light. Explicit web theme/mode choices
  survive reload; blocked storage falls back without breaking the page. Browser
  storage contains only those two literal nonclinical preferences.
- Stars never expand the case or alter its grade. Flags accept optional comments,
  filters work, grouped membership remains 68–69, and markup-shaped comments are
  inert. Live and offline feedback downloads omit an unflagged report sentinel
  and the complete accession/source-crop payload. Updated copies reopen with
  marks/comments, chosen title mode, resolved theme and combined-view choice.
  Offline interaction makes zero HTTP(S) requests. Desktop and 390px mobile
  screenshots were inspected; controls are separate from the expandable button
  and fit without horizontal overflow.
- **`check-perspectives-severity.cjs` passed:** streamed/retry dual titles,
  shared revision inventory, severity colors, both themes and offline export,
  without extra model calls when switching perspectives.
- **`check-reader-sources.cjs` passed:** actual pinned local OCR, queued headerless
  screenshots, overlap joining, optional row editing, cropped PNG export and
  correction/save/reopen continue to work with the new document controls.
- Prompt 1.8 / dual-title 1.2 instructs consequence ordering inside categories.
  This is model guidance, not a deterministic clinical ranking. The exact old
  1.7 prompt is archived. These tests do not measure clinical grading accuracy.
- The Azure model/deployment, credentials and dependencies are unchanged.
  Cloud Run deployment is **pending**; replace/redeploy the assembled `main.py`.
  Existing exported files retain their own embedded code and classifications;
  new classifications require an explicit analysis with the revised prompt.

Prepared October 4, 2026. All fixture reports are synthetic.

## November 2, 2026: truncated unique cases and current labels (2026.11.02.2)

- **111 Python tests passed.** The backend clinical prompt/severity rules did not
  change. The assembled single-file deployment remains syntax checked.
- `check-sequence.cjs` now covers unique 1-to-11 repairs with and without an OCR
  flag, a three-row middle repair, a three-row leading repair, and refusal of a
  digit substitution or a two-row crop. Existing 47/81-row truncation, offset,
  unchanged-accession, gap/reorder/spacing/insufficient-anchor checks passed.
  Local-neighbor fixtures repair 1-to-11 despite an unrelated genuine gap or
  contradictory number elsewhere, retain those original values and accessions,
  and refuse competing local answers of 10 versus 11.
- `check-lookup-recovery.cjs` verifies that a completed image's needs-correction
  label clears after fixing its case number, reappears when an edit creates a
  conflict, and clears when that conflict is resolved. Prior list-scroll,
  partial analysis/export, retained evidence and correction checks still pass.
- Actual pinned OCR, multi-image overlap/progress, offline export/correction,
  dual titles, save and reopen checks passed with synthetic data. No patient
  screenshot or paid analysis request was used. Cloud Run deployment is pending.
- The associated extractor v0.19 passes **127 synthetic/native-control tests**.
  Regressions reproduce delayed loaded reports and missed first Down, both at
  labels 1 and 11; demonstrate same-row refresh or explicit recovery before a
  duplicate is saved; preserve linked studies, saved prefixes and original labels;
  and cover Stop/cancel, close/navigation recovery and Finish without recopy.
  The actual PowerScribe failure still requires a hospital-workstation trial.
- Portable [extractor v0.19](https://drive.google.com/file/d/1lxBMem5TiKGOuNVmJKnJrqGM7RhXOK80/view?usp=drivesdk)
  is uploaded in the existing release folder. ZIP: 68,481 bytes; SHA-256
  `b9f63b4463d42d6d2bccbf656942ca740dbe760b558f7d72ab10cf40835ad648`.
  The archive contains only the tested EXE, README and quick start; the embedded
  EXE hash matches the tested file. Mounted-Drive SHA-256 and connector readback
  of the synced file ID/name/size were verified; prior releases were preserved.

## November 2, 2026: lookup scroll and best-available analysis (2026.11.02.1)

- **111 Python tests passed.** The normal form now retains incomplete, flagged
  and conflicting lookup drafts independently of report preparation. Source
  crops remain pixel-only, bounded and sanitized; extra fields are excluded.
- `dev/check-lookup-recovery.cjs` exercises the production template and normal
  form endpoint with synthetic identifiers. In a 47-row table, repeated View row
  clicks at rows 21 and 36 preserve both inner-table and page scroll, while the
  image pane moves to the selected source. A list rebuild preserves its offset.
  The saved desktop screenshot was visually inspected.
- Browser checks cover cancel/proceed, flags/conflicts/incomplete rows retained
  after the actual POST, source-crop viewing after submission, exact-case copying
  after correction without reanalysis, partial export, continuing during active
  OCR with completed rows, and clean submission without any confirmation.
  Competing flagged rows cannot silently yield a first/last-wins accession.
- Existing pinned-OCR/progress/overlap/export (`check-lookup.cjs`) and queued
  screenshot/offline correction/title/save/reopen (`check-reader-sources.cjs`)
  checks passed. Their completion waits now target OCR status and the relevant
  screenshot's own summary rather than the former Export-disabled proxy.
- No patient information, paid model calls or live Cloud Run changes were used.
  Deployment of the replacement `main.py` remains pending.

## November 2, 2026: dual titles, queued screenshots and editable source images

- **109 Python tests passed.** Added single-call dual-title/schema checks,
  invalid-title rejection, legacy compatibility and independently sanitized
  exported titles. Source-row tests cover PNG dimensions/type/CRC, bounded
  decompression, metadata removal, exact source joins and selected-only export.
- The actual pinned-OCR browser test queues two headerless screenshots while
  recognition is active. Six rows per image with three overlaps become nine
  mappings. Cards remain collapsed; opening one shows its own rows, including
  shared overlaps. The fixture includes an intervening numeric column and a
  right-hand text column that are excluded from the source crops.
- A fresh offline reader with all networking blocked switches between both
  titles, copies an accession with its source image visible, accepts a local
  correction, saves and reopens the corrected file retaining source evidence
  and selected perspective. The source peek was visually inspected at mobile
  width; image text is readable and the page does not overflow.
- Existing actual-OCR/progress/export, mode/in-flight/retry, compact copying,
  UI, paste, review-control and passage-highlight checks passed. Clipboard
  operations use synthetic fixtures/injected test implementations. No paid
  analysis requests or patient reports were used for this update.
- **117 exporter checks passed.** The new native-control regression resets
  retained failure/cancellation state twice in the same launcher and verifies
  Go is restored; successful runs retain valid F8 state. Existing window/focus,
  clipboard freshness, menu recovery and navigation safeguards remain in place.
- The user's failed-run log was unavailable. The first-case stall has not been
  reproduced on PowerScribe; retained worklist state is a plausible contributor,
  not an established root cause. The hospital trial remains necessary. Website
  source build 2026.11.02 requires the normal Cloud Run redeployment.

## October 30, 2026: compact copying and headerless screenshot paste

- **103 Python tests passed.** Export checks now require the standalone-reader
  marker and ensure the normal application head does not contain it.
- Actual pinned Tesseract browser checks passed for image ClipboardEvents,
  headerless case/accession inference with an intervening numeric column, wide
  and narrow passes, steady progress, overlaps, conflicts, stale lookup handling,
  automatic action acceptance and native Analyze form submission. A normal-page
  export response is rejected without downloading it. A newly opened exported
  reader works with storage disabled and all networking blocked.
- Separate controls checks passed for a 44-by-44 header icon left of the caret,
  keyboard copying, no nested buttons, unchanged card height/expansion, retained
  SVG, transient feedback, grouped footer accessions, dark/light themes and a
  375-pixel viewport. Existing UI, paste, mode, highlight and review-control
  browser suites also passed.
- Pure detection checks cover XR/RF/MR/CT/OT/US/NM, contextual 0T/07/O7 and O
  corrections, leading zeros, extra numeric-column exclusion, ambiguous-column
  refusal and nondestructive digit-length warnings. An all-numeric headerless
  column cannot establish its own accession identity.
- The latest user's pasted 46-row OCR text was checked separately: 17 contextual
  string corrections and three digit-length warnings (source cases 16, 18 and
  39). Existing numeric tails are unchanged. The associated private image was
  not available as an authenticated download, so these are text-rule checks,
  not a new image-level accuracy result. No identifiers/screenshots are in Git.
- **116 exporter checks passed** for v0.17, including a native-control check
  that live updates affect only the external progress window while launcher
  status stays steady. This release does not change capture timing. The ZIP
  was locally hash-verified and its synchronized Drive file was read back.
- These checks do not establish arbitrary screenshot accuracy, correct report
  authorship or end-to-end PowerScribe compatibility. The hospital dry run and
  live Cloud Run deployment remain outstanding.

## October 30, 2026: automatic lookup acceptance and new screenshots

- The current workflow supersedes the individual-confirmation requirements
  recorded below. Valid mappings attach/copy/export without individual approval.
  The actual-OCR browser suite checks absence of row checkboxes and native
  Analyze submission of valid mappings, including after report input changes.
  Missing/conflicting mappings still stop submission; strict backend validation,
  stale-result suspension, offline export and partial-overlap checks remain.
- 102 Python tests and the actual-OCR/export browser suite passed. Sequence
  safeguards cover the newly observed missing early anchors with duplicated
  OCR readings of 2/3 elsewhere; repair still refuses contradictory source
  numbers, real numbering gaps, irregular spacing and insufficient anchors.
- Three private images contain 47, 49 and 81 rows. Enlarged-source inspection
  verified 177/177 exact accession reads. The two new images required five and
  six case-label repairs; after the early-anchor fix all 177 source numbers and
  pairs match these images. This is a small, related sample, not a general OCR
  accuracy estimate. The 49-row image lacks headers and used manual column marking.
- The primary overlay benchmark used a font/scale/threshold fitted on the
  original image, frozen before inspecting the new images. It tested 28,632
  altered strings, detecting 12,212 (42.7%) while accepting all 177 correct
  strings. A second local-residual variant improved some mutation classes but
  remained far below the requested 99% sensitivity/specificity. It is not used
  as a production validator. See `OCR_OVERLAY_EXPERIMENT.md`.

## October 29, 2026: overlapping screenshots and 47-pair paste fixture

- Added a fully synthetic paste file containing exactly 47 distinct report
  pairs, numbered 1–47 in the extractor's Attending/Resident order. The production
  parser/preparation pipeline retains all 47 original numbers and entries without
  provider calls. No real identifiers are included.
- The actual-OCR browser suite checks partial overlap: screenshots covering
  55–59 and 57–61 yield seven exact mappings, retain the first five confirmations,
  and create no duplicate-case conflict. Existing conflicting-accession tests
  still require resolution instead of silently replacing a reading.

## October 29, 2026: OCR progress correction

- Removed worker-level percentage updates that restarted on every recognition
  call. The actual-OCR browser suite checks nondecreasing 0–100% progress for
  wide-image columns and a narrow six-row image (two OCR calls per row), plus
  completion and Clear remaining stable after worker calls finish.
- The 102 Python tests and existing sequence safeguards also pass. This change
  only affects progress reporting; recognition, mappings and prompts are unchanged.

## October 29, 2026: screenshot accession lookup and offline export

- **102 Python tests passed.** New tests cover strict confirmed lookup validation,
  conflicting/duplicate source mappings, leading zeros, normal form persistence,
  export CSRF, immutable source membership, headingless-report omission, rebuilt
  evidence offsets, untrusted markup encoding, pinned asset integrity and
  whole-document exclusion of context, raw errors/warnings, prompts, inputs,
  screenshot/runtime data and unselected lookup records.
- **Nine browser suites passed:** the existing mode, UI, grouping, batching,
  review-controls, highlights, wording and paste suites, plus `check-lookup.cjs`.
  The new suite uses the actual Tesseract worker/model and production template on
  a loopback-only test server. It checks exact synthetic OCR, unconfirmed-row
  isolation, duplicate screenshot handling, grouped accession copying, primary
  selection after sorting, brief copied feedback, edited-row conflicts, stale
  report-batch suspension, manual column selection for headerless images, verified
  range acknowledgement/count checks, unchanged accession strings, mobile
  overflow and Clear. Real HTML downloads are opened from disk with network
  requests blocked, exercising filters, theme/view changes, clinical reports,
  clipboard fallback and recipient-subset exports that omit other records.
- Synthetic dark/light reader and lookup layout previews were inspected. The
  banner is absent from the preparation page and present in the reader/print.
  Exported production reviews are not labeled as illustrative synthetic output.
- **Correction to the initial sample assessment:** the manual reference had
  three transcription errors. Enlarged-source review found **47/47 exact
  accession strings**, **40/47 correct source numbers**, and **40/47 correct
  pairs** before sequence repair. The earlier 44-accession/37-pair claim is
  retracted. All 47 rows of the user-provided 115-pixel-wide screenshot were
  recovered. The new sequence repair corrects seven incomplete/unread labels,
  yielding **47/47 exact pairs on this sample**, without changing accessions.
  These are one-sample observations, not a validated accuracy estimate. Every
  row still requires confirmation; engine read scores are not measured accuracy.
  Larger source captures and more varied lists should be tested. The image and
  extracted identifiers were not added to Git or public artifacts.
- `check-sequence.cjs` passes independent safeguards for unread/truncated labels,
  non-1 source offsets, unchanged accession strings and confirmation status. It
  rejects contradictory unique reads, actual numbering gaps, reordered rows,
  irregular/missing or duplicate row spacing, and insufficient anchors.
- No patient reports, paid model calls, new API keys, auth changes or Cloud Run
  deployment were used. The Gmail sample was read only; no email was sent.

Run `python dev/assemble.py`, `python dev/synthetic_preview.py`, the Python suite,
and `python dev/cache-ocr-assets.py`, then start `python dev/serve-lookup-qa.py`
for `node dev/check-lookup.cjs`. Run `node dev/check-sequence.cjs` for the pure
sequence safeguards. The
loopback harness uses fake identity and synthetic reports only; it is not a
deployable authentication configuration. The cache helper verifies the public
bytes in `dev/ocr-assets.json` and writes only ignored `dev/qa-output/ocr-assets/`.
Production retrieves and verifies them through the app's asset route.

## October 29, 2026: Resident / Attending title modes

- **92 Python tests passed.** New checks prove the default prompts differ only in title instructions and both exported files match their embedded variants. Verify fresh Resident selection, Attending form submission/default/editor preservation, invalid-mode rejection before provider access, unchanged grouping and source labels, and exactly one mocked request per review entry using the selected or edited prompt.
- **Eight browser suites passed:** mode, UI, grouping, batching, review controls, highlights, wording and paste. New mode checks exercise native radio keyboard navigation and visible focus, 320/375/1100-pixel layout, independent prompt drafts and Restore, actual HTML form submission, Attending persistence after submission, and a frozen in-flight Attending request while the selected mode changes. Synthetic responses verify attending-based titles, no implicit calls on switching, an explicit Resident retry after a deliberately failed retry, retained title provenance after failure, unchanged group membership/counts, clearing both private drafts while retaining mode, and Resident default on a fresh GET.
- Dark and light toggle previews were inspected. These are prewritten synthetic titles with mocked provider responses, not a measurement of live model title accuracy. No patient text, paid provider calls, credential changes or Cloud Run deployment were used. Replace the deployed `main.py` and redeploy to activate the modes.


## October 29, 2026: nearby identical report groups

- **84 Python tests passed.** New coverage verifies exact equality of both full reports; adjacent and nonconsecutive groups; gaps of 1/2/3 versus 4; six-member adjacent and spaced chains; original-number gaps after incomplete captures; context, signature, known attestation, punctuation, case and internal-whitespace differences; platform line-ending normalization; nonascending input; original-label preservation; and nonmutation of parsed records.
- An actual import-route test produces a six-source group plus a separate source, submits the prepared representatives through the real batch route with a mocked Azure client, and verifies exactly two provider requests, unchanged instructions, original request IDs and no source-number metadata in the model input.
- **Grouping, UI and batching browser suites passed.** The new grouping suite uses Python-imported fixtures and the production template: six sources become four review entries and four request records; range/nonconsecutive labels survive streamed results and retries that deliberately return conflicting identity fields; every member is searchable; source/review totals and revision counts stay distinct; full reports, sorting, filtering and 320/375/1280-pixel layouts work. A partial result is retried once as the representative pair. The grouped dark preview was visually inspected after theme transitions.
- Existing 100-worker concurrency, 100/100/5 processing, source-evidence linking, clinical-only scope and UI regressions continue to pass. Prompt and criteria are unchanged. No real reports, live provider calls, new credentials, extractor update or Cloud Run deployment were involved. Replace the deployed `main.py` and redeploy to activate this feature on the live website.

## October 28, 2026 update

### Short bulk shortcut and actionable processing notices

- **73 Python tests and six browser suites passed:** wording, review controls, UI, batching, highlights and inline preview. Verified the two-second deadline expires even under the pointer, keyboard focus retains access until leaving, the X control is absent, and position-preserving local/bulk behavior remains intact.
- Status navigation checks verify exact attempted-error and skipped-input subsets, clearing an unrelated search, opening the first affected case and displaying its next step. Skipped-only batches remain actionable. A completed case with a clinical review item does not become an analysis failure. Source links, streaming, sorting, filtering and responsive layout continue to pass.
- Updated mobile shortcut output was visually inspected. Tests use synthetic data and mocked requests. The attending workflow document is a proposal only; no attending mode, feedback delivery, communication tracking, new model prompt or cloud deployment was added.

### Local wording choices with explicit bulk action

- **73 Python tests passed.** Prompt/embedded-template synchronization and the explicitly chosen all-cases default through form submissions remain covered; clinical logic and model instructions are unchanged.
- **Wording, UI, review-controls, highlights, batching and inline-preview browser suites passed.** Dedicated wording checks verify local changes leave other cases untouched; the optional all-cases action changes the default only when clicked; current controls remain within two pixels of their original viewport position during local and bulk hide/show in paired and single views at 320/375/1280/1440-pixel widths; near-end bulk collapse avoids scroll clamping; rapid toggles restore native scroll anchoring; and pinned source links stay mounted. Idle expiry, focus-paused expiry, Escape, mobile offer bounds, later-opened cases, streaming and preview state are covered.
- Desktop/mobile screenshots of the optional action were inspected. All fixtures and requests are synthetic. The update has not been deployed to Google Cloud.

### Compact labels and global report wording

- **73 Python tests passed.** The new display preference defaults to shown, accepts an explicit hide/show value through report form submissions, and falls back to shown for an invalid value. Template and prompt export synchronization still pass.
- **UI, review-controls, passage-highlight, batching and inline-preview browser suites passed.** Verified removed visible filter copy, exact `% changed` label, synchronized hide/show controls and evidence across cases, later-opened and streamed cases, view/filter/order changes, Clear reports, preview state restoration, retained pinned source links and responsive layout. Desktop output was visually inspected.
- Model prompts, grading criteria, percentage calculation and request behavior are unchanged. Checks used synthetic reports and mocked responses. Existing Google Cloud deployment still requires replacement of `main.py` and redeployment.

### Explicit patterns and criteria audit

- **72 Python tests passed.** Existing category/evidence regressions continue to pass. New checks verify server-standardized Emphasis wording and exact equality between the exported default prompt and the embedded prompt. Prompt 1.5 clarifies the decision order and writing patterns while preserving the existing importance thresholds and section gates.
- **UI, review-controls and passage-highlight browser suites passed.** The case 13 preview now reads `Small right pneumothorax → Added to Impression; finding unchanged`. Source links, fixed endpoint colors, fully visible groups, filters, sorting and responsive layout remain covered. The criteria audit explicitly distinguishes model semantic judgments from mechanical quotation/section validation.
- Updated examples remain prewritten synthetic fixtures. No live model-quality evaluation, paid API request or cloud deployment was performed.

### Systematic-summary follow-up

- **70 Python tests passed.** The strict model schema requires separate resident/attending summary fields and excludes a free-form summary. Added regression coverage for fixed server-generated order, source-absence markers, preserving explicitly quoted negation and underlying disease context, all action types, and partial-result warnings when an endpoint is missing, blank, multiline or contains an embedded arrow.
- **UI, review-controls, highlights, batching and paste browser suites passed.** Every displayed revision uses two endpoint spans in the same order, including the previous nondirectional additions and wording examples. Color remains report-side-specific in both themes and views; legacy free-form summary prose cannot control the display. Existing responsive, search/filter, percentage-sort, source-link, concurrency and clipboard checks continue to pass.
- The illustrative fixture now explicitly shows **Diverticulitis without perforation → Diverticulitis with focal perforation**, supported by synthetic quotes on both sides. Preview uses prewritten results, so these checks establish the response/display contract, not live model adherence or clinical paraphrase accuracy. No paid API calls or patient reports were used. Cloud deployment is still pending.

### Initial controls update

- **65 Python tests passed.** Includes deterministic text-change calculation, context exclusion, 0/100% bounds, approximate coarse results, unavailable values and preservation after AI failure; existing parsing, identity/CSRF, full-source fidelity, evidence and 100-worker streaming regressions also pass.
- **Five Edge/Playwright browser suites passed:** UI, review controls, passage highlights, batching and paste. New checks cover resident/attending colors in both themes and summary views; all four Minor/five Wording items visible without extra controls; safe arrow prose; category union plus search; keyboard activation/focus; stable counts; attention/status filters; both percentage sort directions with missing values last; and 320–1440-pixel controls. Existing batch checks verify 100-case streaming, 205-case grouping, byte limits, retries, interruption handling and clear.
- Desktop and mobile screenshots were inspected locally. All preview data and requests are synthetic; no patient reports, live Azure calls or live UAB sign-in were used. The update is prepared for replacement of `main.py` in the existing Google Cloud deployment; live deployment is not verified.

## Previous verification history

- **Full-report handoff/case-identity follow-up, October 5: 61 Python tests and UI/Paste/streaming/passage-link browser checks passed.** Consecutive and nonconsecutive identical templates remain separate with unique IDs and original numbers; context scoping remains covered. Paste tests use a mocked clipboard, verifying Unicode text, permission failure/missing API, empty clipboard, keyboard activation, no requests, retained manual input, Clear/edit races, and 320–1280-pixel reflow. The input screenshot was inspected. Extractor v0.11 separately passes 97 C# tests; its rendered form was inspected. A pre-existing sticky-passage test assumed a passage was offscreen when it could already be visible at a tall viewport. The check now uses a shorter desktop viewport, isolates prior scrolling, and verifies navigation to a genuinely offscreen passage; production passage-link code was unchanged. No real clipboard, PowerScribe, Azure or patient data was used. This supersedes historical duplicate-grouping assertions below.

- **Day/night switch follow-up, October 5: 61 existing Python regressions and the UI browser suite passed.** Additional offline checks verified whole-page/native-control themes, device defaults versus manual override, keyboard activation, mobile/touch layout, reduced motion, preservation of mounted reports and appearance on Clear, zero provider requests, and validated preference retention across form submissions. Light/dark/mobile screenshots were inspected.

- **Paired-view default follow-up: 61 Python tests passed, plus UI and streaming browser checks.** Verified the checked toggle/wide paired layout on fresh page routes, both panels on initial case expansion, and preservation of an explicitly selected single view through submission. Existing totals, headings, report fidelity and streaming checks passed.

- **Section-heading restoration: 60 Python tests and all three current browser suites passed.** Verified original combined/conclusion heading names, exact reconstruction when source heading names differ, body-only model/evidence sections, recalculated Unicode/body offsets, visibly bold clinical headers in inline/split/dual views, and no headings highlighted as finding evidence. Existing source fidelity, repeated/overlapping quotation, sticky scrolling, responsive layout and progressive batch checks passed.

- **Batch totals/preview-color follow-up passed the UI and streaming browser checks.** Verified totals against all accepted fixture revisions, zero values before analysis, incremental totals as results arrive, stability under search/filter, and matching Major/Minor/Wording badge/preview colors in light and dark themes. Existing 320–1600-pixel responsive checks and clear behavior passed. No model or clinical classification changes.

- **Combined batching/passage-link follow-up: 58 Python tests passed.** Seven additional checks cover exact section discrimination, all same-section repetitions, separate Major impression anchors and deduplication, UTF-16 positions after astral Unicode and section joins, missing evidence without guessed positions, lossless diff offsets, and combined headings. Current browser checks passed for batching, UI fidelity and passage links: hover, pointer/keyboard pinning, Next passage cycling, source-specific split-column highlights, overlapping quotations without unrelated navigation targets, repeated Findings versus Impression discrimination, preserved selection across rerenders/reopening, exact source reconstruction, sticky report bounds/internal scrolling without a page jump, aligned panel endpoints, and 320–1600-pixel reflow. No live Azure calls were made.

- **100-at-a-time follow-up: 51 Python tests passed.** A real 100-worker barrier against mocked model calls verifies all 100 start concurrently. Additional checks cover first-result delivery before a blocked slow case, batch identity/prompt preservation, validation before paid calls, authenticated tenant/CSRF enforcement, the 5 MB request limit, missing captures, recoverable worker/client failures, and redacted rate-limit errors. Browser checks use a real local streaming connection: 100-case progress at 0/1/100%, 205 pairs split as 100/100/5, UTF-8 byte-bounded groups without truncation, safe model-text rendering, edited-prompt retry, preserved finished results on disconnect, and Clear cancellation. Existing responsive UI checks passed. No paid API calls or live timing measurements were made. This supersedes the historical four-concurrent-request verification below.

- **Instruction editor/paired-review follow-up: 42 Python tests passed.** Added checks for exact default-prompt prefilling, replacement instructions without hidden guidance, edited-text preservation, view preference after submission, explicit blank/size rejection before API calls, and no prompt truncation above the old supplement limit. Headless Edge checks passed for aligned left/right panel boundaries, widening, 320–1600-pixel reflow, Full reports access, restoring defaults, prompt-specific retries, and no API calls for presentation changes. The actual inline sandbox was also checked for paired layout, mobile stacking, and editor/reset behavior; light/dark desktop and mobile views were inspected.

- **37 Python regression tests passed.** Section scoping, alternate headings, original report preservation, exact full-pair grouping, noncontiguous membership, pending capture handling, malformed batches, input limits, source-quote validation, impression evidence direction, Major gate enforcement, wording isolation, malformed/truncated responses, one-call request construction, no-store options, authentication/tenant/CSRF guards, removal of `/echo`, HTML-safe serialization, and template consistency.
- **Browser checks passed in headless Microsoft Edge.** Complex case counts (2 Major, 4 Minor, 5 Wording/detail), all 11 revisions reachable, Summary default, lossless full reports and split diff, search/filter behavior, both chronology directions, linked membership, 320/375/736/1024/1280-pixel layouts, dark mode, clear, zero network calls from the synthetic preview, seven mocked progressive requests, maximum four concurrent requests, session-expiration handling, and safe rendering of HTML-shaped model strings.
- **Actual identity library startup passed** with synthetic settings and network blocked. CacheLib server-side sessions and the `/redirect` callback registered successfully. The `flask_entry_point` function remains present.
- **Visual polish checks passed** against both the app and the visualization's actual sandbox wrapper: intermediate expansion heights, persistent caret elements, rapid open/close reversal, inert collapsed content, reduced-motion behavior, distinct backgrounds/boundaries, and at least 18-pixel mobile content gutters. Light and dark previews were visually inspected. The 37 backend regressions and existing browser checks were rerun successfully.
- **Progress/revision-block follow-up passed** the browser suite: exact 0%, intermediate 14%, and final 100% states for seven queued pairs; failed attempts distinguished from successful output; skipped pairs reported separately; progress hidden on clear; distinct Major/Minor backgrounds; ASCII arrows converted in prose while quotations remain unchanged; and the empty page background matching the app theme. The existing 37 Python regression tests passed again.
- **No live deployment or clinical model evaluation was performed.** Browser feedback is illustrative, and mocked calls prove plumbing and safeguards rather than clinical accuracy. No real patient text was used. No Azure tokens were purchased or consumed for these tests.

Residual limits: the section parser is conservative but cannot recognize every free-text format; chronological labels assume ascending source numbers follow the reading sequence; strict quotes and schema cannot prove semantic equivalence, severity accuracy, or complete recall; current local auth-session storage is preserved and remains instance-local. The API deployment's actual model compatibility, latency, token use, UAB sign-in, and clinical classifications need a small live synthetic check after copying the files into the existing service.

The default rubric prompt is version `deltarad-review-1.3`. It implements the accepted product decisions in `docs/compare-revisions/REVISION_RUBRIC_DRAFT.md` while retaining an explicit Needs review state for unresolved clinical importance. Users may replace the model instructions in the editor; output, evidence, and category validation still applies. The new quotation-specificity instruction helps source linking without changing the clinical rubric. No research-based clinical validation is claimed.
