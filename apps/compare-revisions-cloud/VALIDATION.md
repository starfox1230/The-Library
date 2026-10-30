# Verification record

Prepared October 4, 2026. All fixture reports are synthetic.

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
