# Changes and rationale — October 4, 2026

## Single-click filters — November 7, 2026 (2026.11.07.9)

- Ordinary clicks select only the clicked filter; Ctrl/Shift-click retains the
  existing multi-filter toggle behavior. All cases clears the selection.
- Share semantics across primary/More filters and newly exported reviews.

## Independent finding expansion — November 7, 2026 (2026.11.07.8)

- Track individually revealed explanation/wording items as sets per case;
  expanding another finding no longer replaces the previous item's reveal.
- Re-click closes only that finding's automatic details. Keep explicit
  case/all-case toggles and hover/focus-driven source navigation unchanged.
- Retain expansion through case collapse/reopen and ordinary rerenders; share
  the behavior with exported reviews. No grading or recommendation-category change.

## Routine added reassurance — November 7, 2026 (2026.11.07.7)

- Shared grading prompt 1.9 puts routine added reassuring negatives in
  Wording/detail, including Impression additions. Missing documentation is not
  itself a missed finding; failing Major criteria does not establish Minor.
- Include pancreatic-cyst and routine osseous-negative examples and preserve
  substantive refutations/exclusions under usual Minor/Major criteria.
- Use Description/Wording for an existing finding; Added/Wording for a routine
  negative with no counterpart, preserving exact source-evidence requirements.
- Archive prompt 1.8 for rollback. No model, schema or automatic regrading change.

## Complete clinical case headers — November 7, 2026 (2026.11.07.6)

- Show every Major/Minor summary in collapsed headers, retaining severity order
  and within-category order, without a two-item limit or +more indicator.
- Remove Wording/detail, ungraded and status-message header fallbacks, including
  Analysis complete on cases without revisions. Keep counts and expanded content.
- Apply the same rendering to live and self-contained downloaded reviews.

## Administrator review state stays out of recipient UI — November 7, 2026 (2026.11.07.5)

- Put Wording & detail under More; retain Needs review in the original view only.
- Suppress recipient review filters/badges, ungraded summary items and admin
  warnings while retaining cases, clinical diffs, validated ungraded records and
  sanitized diagnostic metadata inside the file. Do not label those cases clear.
- Preserve original diagnostic status and analysis provenance through downloads,
  updated copies and feedback; no new visible technical toggle or AI changes.


## Content-sized layout and pinned details — November 7, 2026 (2026.11.07.4)

- Intrinsic-width left-aligned filters and compact search/sort; no premature
  grouping wraps or forced full-width buttons. Center action tags on wrapped text.
- Hover/focus holds the save reminder; leaving starts the full four-second timer.
- Default report wording off. Add per-case AI explanation Show/Hide in all cases
  offers. Pinning reveals only that revision's reason and evidence, with a
  reduced-motion-aware expansion, independent of other case/item visibility.
- Add compact exported-reader download controls inside the sticky PHI banner
  after the main download toolbar scrolls away, preserving its measured height.
- Simplify Text changes to one compact title/settings row, removing redundant
  scope, legend and pin/passage status headers. Fit linked quotes within the
  visible pane around sticky banner/header, short viewports, scaling and case-end
  clipping without moving the document; recheck after expansion settles.
- No changes to authentication, storage, model, clinical grading or report scope.


## Red OCR review action — November 7, 2026 (2026.11.07.3)

- Review OCR uses a prominent red fill whenever pending rows make it available.
  It returns to its neutral disabled appearance when checks are resolved or OCR
  is running. The existing pending-row count and review workflow are unchanged.
  Both light and dark themes retain contrasting text. Deployment is pending.

## Compact filters and quieter review — November 7, 2026 (2026.11.07.2)

- Continuous case-header hover; neutral internal star/flag hover, gold/red
  selected states, preserved keyboard focus and generic feedback text.
- Hidden-by-default per-case AI explanations, separately toggleable from report
  wording, retained in saved data and feedback. No grading or model changes.
- Full-width wrapping primary filters with counted star/flag icons and a More
  disclosure for Not analyzed/No revisions. Remove duplicate counters.
- Replace persistent save text with a four-second actionable reminder on mark
  selection/removal. Support the feedback dialog, full-copy downloads regardless
  of filters, safe saved-file reloads and narrow-screen menu positioning.
- All 13 requested improvements are included; source must be redeployed to
  update the website, and previously downloaded HTML remains self-contained.

## Clinical-action threshold and explicit saved copies — November 7, 2026 (2026.11.07.1)

- Shared prompt 1.8 / dual-title 1.2: likely substantial clinical-action difference,
  no automatic certainty/detail upgrades; new calibration and consequence ordering.
  Exact previous 1.7 instructions archived. Existing results require explicit
  reanalysis for the new rubric; model/deployment settings are unchanged.
- Stars, Project feedback flags, optional comments, filters, explicit updated-copy
  downloads and flagged-only feedback. Never persist clinical data in storage or
  silently send feedback. Retain grouped source numbers, batch ID and per-analysis
  provenance; exclude unrelated case DOM/JSON and all lookup/crop data from feedback.
- Attending and dark defaults; web-only nonclinical preference persistence with
  blocked-storage fallback. Offline copies preserve their selected perspective,
  resolved theme and combined view without cross-file preference promises.
- Offline checks and Edge roundtrips use synthetic reports and mocked responses.
  No clinical validation or live Cloud Run deployment is claimed.

## Preserve dual titles and clarify Major — November 6, 2026 (2026.11.06.1)

- Fix both browser response whitelists dropping title_resident/title_attending.
  One common update path retains both, protects source identity and handles
  legacy success versus failed-result title preservation. Verify live-page and
  exported-reader switches without new analysis requests.
- Color Major arrows/attending endpoints red and Minor amber, keeping resident
  text in the reading color. Use the same renderer for previews and expanded/exported
  summaries. Verify both light and dark themes.
- Broaden Major to substantial diagnostic/management consequence, acute or
  important nonacute disease. Add source-supported suspicious prostate lesion
  and significant disease-extent calibration; retain keyword/wording/follow-up
  counterexamples, exact quotations and the existing Impression gate.
  Shared prompt IDs: deltarad-review-1.7 / deltarad-review-dual-titles-1.1.
- 113 Python checks and streamed/retry/export/browser regressions pass using
  fictional data and mocked model responses. Update assembled main.py on Cloud
  Run to activate; existing analyses need a retry to use the new grading default.

## Focused OCR review and screenshot overlap — November 4, 2026 (2026.11.04.1)

- Treat each screenshot as consecutive increasing source rows, per the updated
  workflow contract. Infer the start from consistent readings and correct missing,
  truncated or substituted case digits automatically; corrected cases need no
  human review. Exact accession matches across screenshots can anchor an unread
  image or repair an incorrect whole-image offset. Accessions are never generated
  from the numeric sequence. An otherwise unknowable start can be entered once.
- Add Review OCR: original row crop, case/accession editing, Tab/Enter to save and
  advance, Shift+Tab to go back, Escape to close, and comparison/selection of
  genuinely conflicting readings. Skip case-only checks resolved by one start
  correction. Analyze remains available with best-available mappings.
- Reconcile repeated screenshot coverage after numbering and review edits. Keep
  the first row/accession/crop for confirmed overlaps, black out later repeated
  source rows, and exclude those repeats from lookup/review/export. Preserve
  ownership when the first reading is corrected. Case labels alone do not merge
  conflicting accessions; matching/near-matching aligned accession blocks supply
  the evidence. Explicit human source selection also removes hidden repeats.
- Simplify the optional numbering override to First case and Apply numbers;
  remove the last-case field, spacing gate and confirmation checkbox.
- Verification: 111 Python tests, sequence/overlap/domain checks, desktop/mobile
  review-overlay tests, existing scroll/best-available/copy/export checks and a
  real local Tesseract OCR/export run passed using fictional data. Full screenshot
  pixels stay local to OCR; lookup crops retain the existing export behavior.
  Replacement source is assembled in main.py; Cloud Run redeployment is pending.

## Neighbor-based case repair and current image labels — November 2, 2026 (2026.11.02.2)

- Repair a unique short case reading such as 1 instead of 11 when one consistent
  sequence has at least 60% reliable anchors. Require literal omitted digits for
  readable discrepancies, retain spacing/end-anchor checks and reject gaps or
  substitutions. Permit three-row crops with two supporting anchors. Accession
  strings remain unchanged.
- When whole-image repair is blocked elsewhere, permit a unique local omitted
  digit established by two original, unflagged neighbors with consistent spacing.
  Do not use inferred rows as new anchors or bridge a genuine source gap.
- Recalculate each completed screenshot's correction/ready label from current
  canonical rows after edits, removal or range assignment. Shared overlap and
  duplicate-case conflicts update all affected image labels.
- Extractor v0.19 adds in-place interruption recovery and a fresh same-row
  comparison check before a repeated first pair can acquire a second case label.
  Its executable and the website remain separate updates.

## OCR lookup recovery — November 2, 2026 (build 2026.11.02.1)

- Preserve the OCR table's scroll position when View row highlights an image;
  avoid reattaching the already active editor and preserve offsets on rebuild.
- Replace the Analyze hard stop with one continue confirmation for flagged,
  incomplete or conflicting rows, or OCR still running. Analyze uses completed
  mappings without requiring individual approvals. The server retains unresolved
  rows and sanitized source crops for later correction, independently of report
  preparation and model inputs.
- Attach only complete, unambiguous mappings. Conflicts (including a competing
  flagged row) never become first/last-wins accessions. Download can likewise
  proceed with the usable subset after confirmation, omitting unresolved rows.
- Keep View row available for retained source crops after form submission and
  show the pending-check count even when lookup editing is collapsed.

## Both title perspectives and source-row review — November 2, 2026

- Website footer now identifies build 2026.11.02, separately from extractor v0.18.
- One shared prompt/schema requests both title_resident and title_attending in
  the existing single analysis call. The live/offline toggle retitles immediately
  without changing shared revisions, edited instructions or sending another call.
  Legacy single-title results remain readable in both views.
- Pasted screenshots immediately become collapsed per-image cards. The next
  paste button stays available while a FIFO queue processes earlier images.
  Editing is optional; exact overlap joins and conflict safeguards are retained.
- Preserve case/accession-only row crops with mappings through Analyze and
  export. Copy opens a source peek with an editable accession. Offline readers
  can save a corrected copy with both titles, current perspective and source
  images. Crops exclude intervening numeric/right-hand columns; export omits
  unselected mappings and strips PNG metadata/trailing data with bounded decoding.
  Crops are sent only to this application, never to the analysis provider.
- Retain prior OT corrections/headerless detection. Constrain automatic prefix
  acceptance to XR/MR/RF/OT/CT/US/NM, permit known 07-to-OT headerless evidence,
  and choose row/column OCR based on native text height as well as crop width.
  Existing identifier digits are never completed or shortened by these rules.
- Extractor v0.18 clears retained F8/capture/cancellation state after a stopped
  or failed attempt and restores Go; successful runs retain valid F8 focus.
  This is a targeted retry improvement, not a reproduced diagnosis of the user's
  first-case stall. Workstation trial and live website deployment remain pending.

## Compact accession controls and simpler screenshot paste — October 30, 2026

- Put an icon-only Copy accession action immediately left of the case caret,
  with a 44-pixel target, tooltip, keyboard support and brief feedback that does
  not expand or resize the card. Put the complete grouped accession list and
  individual copy actions below the expanded review panes.
- Move screenshot paste directly below Report input. Remove file selection and
  manual column-marking controls. Infer headerless case/accession columns from
  repeated positions and prefixed identifiers, excluding additional numeric
  columns; request a clearer crop when evidence is insufficient or ambiguous.
- Correct OCR-only OT prefix confusions and O in numeric positions. Preserve
  existing digits and leading zeros. Flag unusual digit lengths without silently
  shortening or completing identifiers. Adapt enlargement to text height and
  preserve grayscale for the wide-column pass to reduce observed extra strokes.
- Reject login/normal application HTML returned during export using a parsed
  offline-reader head marker. Verify the generated reader in a fresh browser
  context with storage unavailable and all network requests blocked.
- Record all requested NEW items and remaining workstation/image-validation
  limits in NOTION_UPDATES_2026_10_30.md. Add a November 4 baseline launch plan;
  survey cadence and follow-up cutoff remain decisions to lock before launch.
- Companion extractor v0.17 sends live progress only to its external progress
  window. The launcher retains final results. Its portable release was uploaded
  to the existing Drive folder; website Cloud Run deployment remains pending.

## Automatic lookup acceptance and overlay experiment — October 30, 2026

- Remove individual lookup confirmation checkboxes. Analyze reports and Download
  accept valid mappings directly. Missing/invalid values, conflicting accessions
  and unfinished OCR still need resolution; valid rows require no approval clicks.
- Preserve the existing backend `confirmed: true` payload for compatibility; it
  now records acceptance through the action, not individual manual verification.
- Allow an early sequence anchor in the first five rows: duplicate OCR reads of
  2/3 elsewhere can exclude the genuine early 2/3. Retain the global consistency,
  anchor-count, regular-spacing and far-end requirements.
- Test the three supplied screenshots (47, 49 and 81 rows) and a developer-only
  pixel-overlay benchmark. The overlay comparison misses too many altered
  strings to use as a production validator; findings and reproduction are in
  `OCR_OVERLAY_EXPERIMENT.md`. No source identifiers/images are committed.

## Steady OCR progress — October 29, 2026

- Stop displaying the OCR worker's per-call percentages, which restart for each
  case-number/accession read and cause rapid jumps near completion.
- Show a named column-detection phase, then completed rows (or columns) and a
  percentage for that pass. Update once per complete row/column and identify the
  screenshot. Worker callbacks cannot overwrite completion or Clear.

## Incomplete OCR case numbers — October 29, 2026

- Keep OCR case-number reads and repair incomplete/duplicate labels only when
  unique surrounding anchors establish one consistent consecutive sequence.
  Highlight repairs and require confirmation; never alter accession strings.
- Refuse automatic repairs across contradictory reads, source gaps, irregular
  row spacing or insufficient evidence. Add an optional operator-verified range
  with matching row count for genuinely consecutive screenshots.
- Explain duplicate case numbers directly instead of labeling them conflicting
  accessions. Label engine confidence as a read score rather than a percentage.
- Correct the sample validation record: three manual-reference transcription
  errors understated accession accuracy. All 47 accessions were read correctly;
  case-label repair brings this one image from 40 to 47 correct pairs.

## Accession OCR and standalone reader — October 29, 2026

- Add screenshot paste/file import, browser-local OCR, editable row confirmation,
  image column marking, enlarged source-row highlighting and explicit coverage.
  Keep accession strings exact and source-number joins batch-local; conflicts
  cannot be exported, omissions never shift other cases, and input changes
  suspend old lookup actions until the new batch is analyzed.
- Add compact card copy actions with brief feedback. Preserve grouped source
  accessions and use the earliest mapped source member for primary copying.
- Add authenticated, CSRF-protected HTML export. Rebuild clinical-only reports,
  diff offsets and evidence through an allowlist; discard original context,
  screenshots, raw errors, prompts and unselected case data. The downloaded
  reader works offline, has no analysis/input/OCR controls and displays the
  persistent PHI banner only there.
- Keep the existing two-file Cloud Run handoff. Pinned public OCR runtime assets
  are fetched by the server, hash-checked, memory-cached and served same-origin;
  screenshot pixels stay in the browser. No model/credential/dependency change.
- Keep dual-title generation deferred. Current role-specific title prompts and
  clinical grading remain unchanged. Cloud Run has not been deployed by this change.

## Resident / Attending title modes — October 29, 2026

- Add an accessible native radio pill control above the collapsible report input. Fresh visits default to Resident; form submission and Clear preserve the selection. Keep both review views, criteria, grouping and comparison direction the same.
- Derive a separate attending default by replacing only the title rule in the existing resident prompt. Export both exact defaults, preserve the strict response schema, and use one existing model call per review entry. No dual-title request or separate grading pass.
- Maintain per-mode custom drafts while switching on the page; reset only the active draft on Restore, discard both on Clear, and submit only the active editor. Snapshot mode and instructions for in-flight batches; switching sends no requests. Explicit retries use the selected mode, and failed retries do not relabel a retained title.
- Validate optional mode metadata on both API routes, default legacy callers to Resident, and retain original source identities. Add offline prompt/form/request tests and browser checks for keyboard focus, mobile layout, native submission, request count, streaming/retry provenance and Clear.
- Feedback tracking and study measurement remain deferred. Existing Azure/authentication configuration is unchanged; deployment is still pending.


## Nearby identical full-report grouping — October 29, 2026

- Group complete imported pairs only when both full resident and full attending strings match, using the existing line-ending and outer framing normalization. Keep all context and attestation text in the match; no clinical-only or one-sided matching.
- Join a group when the next matching source label is 1–3 after the previous matching member. Chain arbitrarily many nearby matches, start a new group after a gap of four, and leave nonascending input and incomplete pairs separate. Preserve first-appearance group order and every original source number.
- Schedule one representative model request per review entry. Reuse existing range/nonconsecutive headers, source/review totals, member search and retry identity protection. Count each revision once per group and explain the grouping rule in the expanded member note. Prompt and clinical criteria are unchanged.
- Add synthetic parser, import-to-mocked-provider and browser regressions. No extractor release, paid request, credential change or live deployment is included.


## Attending review scope and study planning

- Revise the attending proposal around a simple review aid with attending-anchored case titles. Keep resident titles as resident memory cues, retain the resident → attending comparison order and obtain both titles from the same future analysis response. No attending title fields or mode are implemented yet.
- Defer Discussed tracking, dashboards and saved feedback workflows. Keep proposed QI/research measurement in a separate short form.
- Add a study-planning brief with a resident-reported case-specific feedback outcome, complementary attending review measures, balanced within-attending period order, concurrent-control limitations, carryover, timing and source-shift attribution, missing data, versioning and institutional determination. The protocol elements are proposals, not approved study procedures or deployed collection features. Runtime application code is unchanged.

## Short bulk shortcut and actionable status notices — October 28, 2026

- Replace the framed wording popup and X with a plain-text action that expires two seconds after appearing. Hover no longer pauses/restarts it; keyboard focus retains the action until focus leaves. Preserve local wording choices, explicit bulk behavior and scroll position.
- Turn attempted-analysis issues and unsubmitted-input counts into exact-subset shortcuts: clear unrelated search, filter, open and focus the first affected case. Show the appropriate next step and deduplicate identical notices. Preserve notices when an entire batch was skipped. Keep these operational groups distinct from clinical uncertainty.
- Add a design proposal for an attending feedback worklist using the same comparison/evidence and optional later synthesis, rather than a second independent grading prompt. No attending mode, communication tracking or automated messaging is implemented.

## Local wording toggle with optional bulk action — October 28, 2026

- Restore per-case Show/Hide report wording. Show a temporary, explicitly labeled action to apply that same state to all cases; do not change other cases without that click. Only the explicit bulk action updates the default for unopened/streamed cases and future submissions.
- Update evidence and toggle states in place without rebuilding rows or source panels. Retain the current control's viewport position when earlier cases resize, preserve focus and report selections, and reserve bottom scroll room only when necessary to prevent browser clamping near the end of the page.
- Float the optional action below the toggle so it does not move surrounding content. Dismiss after eight idle seconds, pause expiration during hover or keyboard focus, and support a dismiss button and Escape. Preserve local choices across normal rerenders; clear them with reports. Include local overrides in the synthetic conversation preview state.
- Add browser coverage for individual versus explicit bulk changes, desktop/mobile and single/paired layouts, near-end page shortening, rapid toggles, stationary controls, source pinning, streamed results and accessible expiration. This supersedes the previous always-global toggle behavior.

## Less review text and global wording visibility — October 28, 2026

- Remove the visible Filter cases heading and the full selection/count instruction line. Retain accessible labels for the category/status groups and the contextual Reset filters button.
- Shorten the numeric case-header marker to `9.4% changed`; calculation, tooltip and sort behavior are unchanged.
- Replace per-case evidence visibility with a single report-wording preference. Toggling any case updates all mounted cases and applies to later-opened cases and incoming streamed results. Preserve the choice through view/filter/order changes, Clear reports and form submissions; a fresh visit starts visible. Carry the preference in the synthetic conversation preview state too.
- Verify global updates from different cases, hidden/show states and button labels, new/streamed cases, form handoff and responsive filter controls. No changes to analysis prompts, clinical criteria or model requests.

## Explicit writing patterns and auditable criteria — October 28, 2026

- Prompt version 1.5 adds a step-by-step decision order: match assertions across sections, choose action, separate wording from clinical change, apply consequence and section requirements, then verify summaries and quotations. Existing Major/Minor thresholds and mechanical gates are preserved.
- Define a small set of writing patterns for every action. Emphasis now reads `finding → Added to Impression; finding unchanged`, and the server standardizes that phrase instead of displaying varying section-location paraphrases. Do not imply that the finding left Findings or that unchanged Impression inclusion is a new miss.
- Preserve direct clinical endpoints for reinterpretation, laterality, explicit negation, additions, removals and descriptive detail. Reasons explain the relevant consequence or uncertainty without requiring the user to infer the actual edit from them.
- Add REVIEW_CRITERIA.md describing the current custom rubric, the deliberate prohibition on Findings-only Major items, model judgments versus mechanical checks, and custom-prompt behavior. Export the exact default to ANALYSIS_PROMPT.md during assembly without importing authentication or calling an API; test it for equality with the source constant.

## Systematic resident → attending summaries — October 28, 2026

- Replace the model's free-form `summary` with required `resident_summary` and `attending_summary` fields. Prompt version 1.4 defines parallel, concise, source-specific endpoints for every action and importance, with examples covering complications, reinterpretation, negation, additions, removals, impression promotion and descriptive detail.
- Validate nonempty, single-line endpoints without embedded arrows. Preserve existing evidence checks, withhold malformed items with an incomplete-inventory warning, and derive the combined `summary` on the server in a fixed order. An absent source quote forces a documentation-status marker instead of an invented clinical negative.
- Render every accepted item from its two endpoints, always resident in the reading color and arrow plus attending in amber. Remove category-dependent summary text colors and all arrow-detection heuristics. Add a single Resident → Attending legend; preserve category badges, expanded groups, filters, percentage sorting and source links.
- Rewrite the synthetic examples to demonstrate the contract, including diverticulitis without perforation → diverticulitis with focal perforation. Update browser checks and add contract/absence/invalid-output regressions. No additional model calls or dependencies. Source-quotation checks do not independently verify a generated paraphrase's clinical correctness.

## Clear before/after summaries and direct filters — October 28, 2026

- Use the latest supplied Python file as the baseline; it matched the local source. Keep its prompt, authentication, source evidence, request limits and batching behavior.
- Split explicit arrow summaries into resident text in the normal reading color and the arrow plus attending text in amber, in both collapsed previews and expanded headings. Preserve safe text rendering and leave nondirectional prose intact.
- Show every Minor and Wording/detail revision immediately in expanded cases. Remove the per-group “Show remaining” controls; keep the compact two-preview case header.
- Restore a quiet text-change percentage at the right of the header with high/low sorting. Derive it deterministically from the existing clinical diff, label coarse results approximate, distinguish missing values from zero and sort missing values last. This supersedes the original decision below to remove all percentage controls; the marker measures text volume, not clinical severity.
- Replace the Show dropdown with visible, keyboard-accessible filter buttons integrated with batch counts. Allow multiple selections (any selected category/status), search within them, expose selection state and provide Reset filters. Keep counts global. Needs review counts cases requiring attention so an analysis failure without revision items is still visible.
- Add percentage regression checks and browser coverage for colors, fully visible groups, multi-select/search/reset, keyboard focus, missing-value ordering, responsive controls and safe text rendering. No new dependencies or model calls.

## Full-report handoff and conservative case identity — October 5, 2026

- Stop merging numbered cases on identical resident/attending text. Normal reports can share complete templates; no study identifiers are available to prove they belong to one study. Each source case keeps its own number, summary and counts. This also keeps genuine linked studies separate for now.
- Coordinate with extractor v0.11: whole reports are exported by default, with the old Findings-and-below choice optional. Context informs the AI, while clinical diff/evidence boundaries remain unchanged.
- Add a compact Paste button next to the report input label. It reads the clipboard only on click and fills the box without submitting or sending reports. Blocked, missing and empty clipboard cases preserve existing input and offer Ctrl+V; Clear/manual edits defeat delayed clipboard responses.
- Remove the report-box sample placeholder and its explanatory hint to leave a clean input area. Clipboard status appears only after using Paste.

## Day/night appearance toggle — October 5, 2026

- Add a compact sun/moon switch in the top header, with a sliding selection indicator and matching outline symbols. Keep native keyboard activation, screen-reader switch state, reduced-motion support and a 44-pixel touch target.
- Start with the device's appearance. A manual selection overrides the device theme for the current page and carries through report submissions via a validated form preference. Clear reports preserves appearance; a fresh visit follows the device again. No report data or appearance choice is saved in browser storage.
- Apply the selection to the entire page, native controls, badges and both report panels using the existing light/dark palette. Theme changes preserve mounted reports and highlights and send no model requests.

## Default to Summary + text changes

- Enable paired review on a fresh page and when no view preference was supplied. Opening a case shows its summary and clinical comparison together, including linked passages and restored headings.
- Keep the existing toggle and preserve an explicitly selected single view through analysis submissions. No prompt, API or dependency changes.

## Restore section headings in the clinical comparison

- Preserve each recognized clinical section's actual heading in the text-change view, including Findings, Impression, Conclusion, combined headings and repeated sections. Bold the heading spans in inline, side-by-side and dual views so the report structure is readable without opening Full reports.
- Include heading text in the deterministic clinical diff, preserving each side's own heading when their names differ. Indication, Technique, Comparison and footer text remain outside this comparison.
- Recalculate exact body evidence offsets after the heading text. Heading metadata comes from the original reports; model section bodies and evidence validation are unchanged, so headings do not become finding evidence or extra AI requests.
- Verify exact source reconstruction, original heading names, body-only evidence, Unicode coordinates, headings in both report columns and dual view, and passage highlighting after the restored prefixes.

## Batch totals and category-colored previews

- Add an All revisions row above the progress/filters with the same Major, Minor, Wording/detail and Needs review badges used on case rows. Count accepted revision items across all review entries, including zero totals, and update as results finish. Count linked duplicate pairs once; keep overall totals stable while searching/filtering so they remain a batch overview.
- Color each short change preview beneath the case title using its own importance: Major red, Minor amber, Wording/detail and Needs review muted, matching existing badge colors in both themes. Keep the case title, capture-status messages and +N more label independent of revision severity.
- Preserve the AI prompt, requests, classifications and numbering; these changes use the existing accepted results.

## Link summary revisions to report passages

- Calculate source positions from exact evidence quotations and explicit Findings/Impression section IDs. Added UTF-16 offsets to lossless diff runs so browser coordinates agree even with Unicode. No additional AI calls or AI-generated character coordinates.
- Ask the model for distinguishing surrounding wording. Match all repetitions within the named section instead of arbitrarily choosing one; use separate Major impression evidence as an additional anchor. Deduplicate identical anchors without conflating Findings and Impression.
- Highlight the hovered revision card and its report passages in dual view. Click or press Enter on a heading to pin it; Unpin clears it. Next passage cycles through matches, prioritizing changed text. Added-only evidence cannot highlight an invented resident phrase.
- Keep the desktop report viewer visible within its case as the longer summary scrolls. Reveal a selected passage by scrolling the report alone, keeping the page stable. Align the two outer panels; on small screens stack them without a nested report scroller. Respect reduced motion.
- Preserve original wording, insertion/deletion styling, spacing markers and both diff modes. Segment overlapping quotations without inserting text. Presentation changes cause no model requests; selections survive rerenders and collapse/reopen.
- Add synthetic repeated-phrase, overlapping-quote, emoji, section-boundary, keyboard and browser-scrolling checks. The inline demonstration uses normal document flow because its surrounding frame grows with content; sticky behavior is verified in the actual full-page app.

## Restore 100-at-a-time processing

- Confirmed the user's supplied pre-redesign code used `ThreadPoolExecutor(max_workers=100)` with a separate model request per report pair. The redesign's four-request browser queue introduced a significant scheduling bottleneck.
- Added `/analyze-batch`: one authenticated browser request starts up to 100 independent Azure calls concurrently on the server. This avoids relying on 100 simultaneous browser connections or Cloud Run HTTP request concurrency. The existing single-case endpoint remains for retries.
- Stream complete case results as newline-delimited events so the existing progress display still advances by actual finished pairs. Heartbeats do not advance the percentage. Model outputs remain fully parsed and evidence-checked before a case is displayed; no partial AI text is graded.
- Automatically divide larger inputs into groups of 100 and keep each request below a 4.5 MB UTF-8 JSON budget within the existing 5 MB server limit. Keep the 250-source-case paste limit, exact full-pair deduplication, and all source numbering. No report text is truncated.
- Validate every batch's IDs, prompt and envelope before starting any model calls. Failures stay attached to the affected case; finished results survive worker errors or an interrupted stream. Clear aborts the browser connection and prevents stale results from reappearing; already-running Azure requests may finish.
- Identify rate/quota errors in plain language rather than suggesting every failure is a bad deployment setting. Existing SDK retry settings and model/instructions are preserved.
- No new environment variables, secrets, dependencies or controls are required. Copy the updated complete main.py. Restored concurrency is verified locally; ten-second live completion has not been established.

## Full instruction editor and paired review

- Replaced the optional supplementary-guidance box with the complete model instructions, prefilled and editable. The edited text becomes the system prompt, allowing users to test a replacement analysis approach without modifying source. No hidden default prompt is appended.
- Added Restore default instructions. The next batch uses the prompt shown at submission; a case retry uses the latest editor text. Already-running requests keep their starting prompt so one batch does not quietly mix instructions.
- Kept mechanical output/evidence/category validation and disclosed it under What stays fixed. The model still must return the fields the interface expects. Increased the instruction limit to 40,000 characters and reject blank/oversized prompts instead of truncating them.
- Added a global Summary + text changes switch. It expands the review area from a 1,248-pixel maximum to 1,840 pixels and applies to all expanded cases. Each case uses a shared two-column frame: summary left, diff right, clear divider, equal top and bottom boundaries. Narrow screens stack the labeled panels; wide screens can show paired evidence excerpts within a panel.
- Preserved Full reports, filters, order, open cases, source numbering, progress, and existing revision colors. Changing the display does not make API requests. The view choice survives a batch submission on the current page, without adding browser storage of reports or preferences.
- Clear reports also clears edited prompt text and restores the default instructions. No new environment variables, secrets, or dependencies are required. Only the complete main.py needs to be recopied. Default prompt version: deltarad-review-1.2.

## Progress and revision-block follow-up

- Added a slim progress bar with a smooth width transition and an exact `finished / total` count plus percentage. It measures unique report pairs submitted for analysis, so grouped linked reports count once. Failed attempts count as finished processing and remain explicitly marked as needing attention; skipped pairs are separately identified. It does not estimate elapsed time or progress within an individual model request.
- Kept the progress element mounted while case rows update, allowing its width to animate rather than jump. Clear resets/hides it; reduced-motion preferences disable its animation.
- Gave every Major revision its own rounded soft-red block and every Minor revision a soft-yellow block. Each block includes its action, summary, explanation, and evidence. Wording/detail retains a neutral background; action labels remain independent of importance.
- Made the standalone page background cover the viewport in both themes, including below a short collapsed list or the initial input form, avoiding the browser's default white lower area.
- Updated the prompt to request `→` for transitions. A display fallback also converts ASCII arrows in generated prose. Source quotes, original reports, and diff tokens remain exact. Prompt version is now `deltarad-review-1.1`; comparison rules and title instructions are unchanged.

Only the complete `main.py` needs to be recopied. No dependency or environment changes are required.

## Visual polish follow-up

- Replaced mismatched text caret characters with one consistently sized chevron that rotates in place.
- Added a brief eased expansion/collapse of the actual content height. Case toggles keep their existing elements, so the caret and panel can transition together rather than rebuilding the list on every click. Rapid reversals and Collapse all remain supported.
- Gave each case a separate rounded boundary and a small gap. The entire expanded case uses a subtle blue-gray tint and slightly stronger outline, making its endpoint apparent even for incomplete reports.
- Aligned desktop detail content with the case title and added dependable mobile gutters; tabs, notices, quotes, and full reports no longer sit against the outer border.
- Scoped the interface's styles to its own root so the inline preview's surrounding styles cannot override its spacing. The prototype now uses the same scoped template as the app.
- Kept keyboard focus and collapsed-content accessibility, and respected reduced-motion preferences. No AI, authentication, environment, or dependency changes were made in this follow-up.

The updated complete file is still `main.py`; `requirements.txt` is unchanged.

## Original redesign

| Change | Why |
| --- | --- |
| Separate case number, exam label, stable title, and short change preview | A long CT CAP can have many revisions without turning its title into an unreadable list. The resident's memorable finding remains searchable even if the attending changes it. |
| Display two preview items and an accurate `+N more` count | Keep collapsed rows useful and compact without suggesting only two revisions exist. |
| Show simultaneous Major, Minor, Wording/detail, and Needs review counts | A case can contain multiple kinds of changes. One overall badge cannot convey that reliably. Counts are derived from accepted revision items, not separately invented by the model. |
| Default opened cases to Summary | Put feedback first while keeping text changes and original reports one tab away. |
| Show all major/uncertain items; progressively reveal minor/wording items | Make complex cases manageable while making every accepted revision reachable. Counts do not change when groups collapse. |
| Simple search, Show filter, and Order selector | Replace the prior crowded review controls with one place for each decision. |
| Add oldest-first and newest-first ordering | Let residents follow their reading sequence in either direction. Uses source case numbers, not unavailable examination timestamps. |
| Collapse report input after submission | Give results the screen space once the paste step is finished. |
| Remove Load demo and Compare text only buttons | One primary analysis path. The diff still works when AI fails; a separate competing button is unnecessary. |
| Remove download JSON, upload JSON, and Copy JSON | Remove user-facing mechanisms for saving/transferring report-containing datasets. No browser persistent report storage was added. Internal authenticated requests still use JSON. |
| Remove numerical scores, percentage-change grading, and score controls | Text volume and arbitrary aggregate scores obscure the actual clinical revisions and imply precision this system cannot establish. |
| Remove obsolete UI controls and keyboard shortcuts tied to the old panels | Keep interaction consistent with the new compact layout; native keyboard navigation and accessible case/tab controls remain. |
| Preserve inline and side-by-side diff modes plus spacing markers | Retain useful comparison functionality and the original lossless token/line matching algorithm. |
| Restrict clinical diff and feedback to Findings/Impression/Conclusion | Exclude indication, technique, comparison, and demographic edits from revision feedback. Full reports still provide AI context and remain visible. |
| Treat ambiguous sections and incomplete captures as ungraded states | Pending reports or capture failures must not look like excellent/no-change reports. No fabricated removals from empty attending text. |
| Group identical complete full report pairs | Analyze linked duplicate reports once, reduce repeated feedback and requests, and preserve exact original member numbers. Noncontiguous membership displays `25, 27`, never `25–27`. |
| Rebuild the entire prompt and structured response | Each model call gets its own goal, scope, direction rules, importance rules, title instructions, context-specific examples, evidence contract, and uncertainty handling. It does not depend on this chat. |
| Separate action from importance | Added/Removed/Changed tell the resident what happened; Major/Minor tell how consequential the specific revision appears. Emphasis/Description stay outside clinical change counts. |
| Require relevant impression evidence for a Major label | Reflect the agreed product rule, including resident-impression evidence for important removed/refuted calls. Impression inclusion alone still does not establish Major. |
| Explicitly calibrate promotion, complication, and descriptive examples | Pure impression promotion is wording; newly added perforation can be a major complication; an already-described multiloculated collection renamed abscess is descriptive in the agreed context. Avoid labeling a recognized underlying disease as entirely missed. |
| Keep evidence quotes and short rationales with each revision | Make it faster to understand the exact before/after change without returning to PowerScribe. Quotes are matched to eligible source sections. |
| Enforce strict schema, validate quotations, and detect unfinished responses | Prevent malformed, ungrounded, or cut-off responses from silently appearing as complete clean analyses. Semantic and clinical accuracy still require evaluation. |
| Progressive per-case requests, four at a time per page | Show completed summaries while remaining cases run, instead of waiting for the entire batch. Avoid the old 100-worker burst. Concurrent tabs/users can still exceed four in aggregate. |
| Keep one structured model call per unique complete pair, with individual retry | Avoid an extra formatting-model pass and its latency. The SDK may retry a transient request once; clicking Retry intentionally requests another analysis. |
| Request `store=False`; no report persistence added | Avoid storing a retrievable Responses object where the API supports this option. It is not a guarantee about provider abuse-monitoring/retention policy. |
| Remove debug echo route, raw SDK error text, and external frontend assets | Avoid unnecessary report reflection, potential content in error logs, and extra browser dependencies. This does not replace cloud access controls or PHI governance. |
| Keep existing UAB authentication, tenant guard, CSRF checks, no-store response headers, and Azure configuration | Change the review experience without recreating the sign-in and deployment work already completed. No new required environment variables or secrets. |
| Keep the deployed name Compare Revisions | DeltaRad remains a future branding decision; no new logo or rebranding is assumed. |

No extractor code, Google Cloud deployment, Azure deployment, secrets, or GitHub publication was changed by this package. The source is saved locally in the Library repository as `apps/compare-revisions-cloud/`.
