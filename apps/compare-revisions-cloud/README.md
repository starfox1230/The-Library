# Compare Revisions: cloud review redesign

## Content-sized controls and item details — November 7, 2026 (2026.11.07.4)

Prepared source; deployment pending. Filters now take their text/icon width,
line up from the left and wrap only when space runs out. Search and sort use
compact widths instead of expanding across the page. Action tags stay vertically
centered alongside wrapped revision summaries.

Both report wording and AI explanations start hidden on a fresh page. Each
case has independent controls with a brief optional Show/Hide in all cases action.
Explicit all-case report-wording choices continue to travel with the exported
review; AI explanations remain hidden when a file is reopened, with reasons
retained in its data.

Clicking/pinning a revision reveals only that item's explanation and quoted
wording, with a short expansion animation (disabled for reduced-motion users).
Hovering only previews its source link. Clicking again returns to the
case's visibility choices. Explicit case/all-case toggles override the automatic
item reveal for their respective content, without changing classification.

The save reminder now stays visible while hovered or keyboard-focused. Leaving
starts a fresh four-second countdown; a later click restarts it. No persistent
warning is introduced. Download now still downloads the complete updated copy.

In exported readers, compact Save copy and Feedback controls appear inside the
sticky PHI banner only after the original download toolbar has scrolled past it.
They mirror the existing actions/counts and do not change banner height. On
narrow screens, the notice is abbreviated visually while controls are present;
its full wording remains in the notice text and tooltip. No new network/storage
or authentication behavior is introduced. Model and grading prompt are unchanged.

The Text changes header now contains only its title, View selector and Mark
spacing edits, aligned in one row where space permits. Redundant scope/legend,
source-location, pin status and passage navigation headers are removed; click
an already pinned revision to unpin it. Genuine unavailable comparisons still
show an error notice. Linking and inline/split source fidelity remain intact.
Automatic report scrolling uses the actual visible scrollport, including the
sticky banner/header, viewport scaling and partial clipping near a case's end.
It fits the selected complete quote (or the first line of an oversized quote)
without scrolling the page; after expansion it checks the settled layout again.
Narrow stacked layouts do not automatically scroll the document on hover.



## Compact review controls — November 7, 2026 (2026.11.07.2)

Prepared replacement source; Cloud Run deployment is pending. This implements the
13-item UI improvement list without changing the model or prompt 1.8 criteria.

- The whole case header highlights together, including the action area. Stars
  and flags have a neutral internal hover fill with no hover border. Selected
  stars are gold and selected flags red in both themes. Keyboard focus remains
  visible; pointer-driven row rebuilds do not manufacture a keyboard outline.
- Feedback wording is generic throughout the reader, tooltips and downloads.
- **Show AI Explanation / Hide AI Explanation** is a per-case toggle in the
  middle of Summary tools; Report wording remains on the right. Reasons are
  hidden on initial load and on reopening a download. The underlying explanations
  remain in analysis data and feedback files. Toggling does not alter evidence
  visibility, classification, other cases, or make a model request.
- A single wrapping filter toolbar fills the available width: All cases, Major,
  Minor, Wording/detail, Needs review, counted gold-star/red-flag icons, and More.
  Not analyzed and No revisions are under More; its active count stays visible.
  Icon-only controls retain descriptive accessible names and tooltips.
- Redundant marked/feedback counters and the persistent save warning are removed.
  Star/flag clicks and removing a flag show a four-second reminder with
  **Download now**. Hover does not extend it; keyboard focus inside the toast
  keeps its action available. The reminder remains usable inside the optional
  feedback-comment dialog, and never reappears merely from opening a saved file.
- Download now always requests the complete updated review, even if a filter or
  “Only currently shown cases” is active. The normal filtered-export option and
  flagged-only feedback download retain their separate purposes. Download and
  error notices still distinguish downloading from sending; no automatic email,
  new storage, AI calls, authentication or dependencies are introduced.

Browser verification: `dev/check-compact-review.cjs` plus the existing marks,
perspective/severity and OCR source-row suites. Synthetic reports only.

## Clinical-action rubric, case marks and dark default — November 7, 2026

Source build **2026.11.07.1**. Deployment remains pending: replace `main.py` in the
existing Cloud Run service and redeploy. Azure settings, model/deployment,
authentication and dependencies are unchanged. No live Azure evaluation was run.

- **Attending is the initial title perspective; dark is the initial theme.**
  Resident remains one click away. Explicit theme/mode choices are remembered on
  the website using two nonclinical browser preference values, with a graceful
  fallback if storage is blocked. Downloaded files use their embedded mode/theme;
  different local filenames do not reliably share browser storage. There is no
  added cross-file explanation in the reader. A new updated copy preserves the
  currently selected mode, resolved light/dark appearance and combined view.
- **Major uses a likely substantially different clinical action**, including
  important nonacute investigation/referral/follow-up. Added certainty/detail
  does not suffice when the likely action remains substantially the same. The
  Impression gate, evidence and shared dual-title analysis stay intact. The AI
  orders revisions within each category by consequence; there are no new scores
  or extra calls. See [current criteria](REVIEW_CRITERIA.md), [exact prompt](ANALYSIS_PROMPT.md)
  and [previous prompt](prompts/deltarad-review-1.7.md).
- **Star** a case to revisit it. **Project feedback** flags a case for Sterling
  with an optional comment. Both have separate filters and never alter the AI
  grade. Marks/comments/lookup corrections remain in memory until explicitly
  downloaded. Report content, identifiers, marks and comments are never placed
  in browser storage. An updated copy retains the annotations; it does not write
  over the original file. Download notices describe a request, not a verified
  filesystem save or a message sent to anyone.
- **Download feedback** includes only flagged cases, comments and the clinical
  sections needed to assess them. It excludes all unflagged cases and the lookup
  accession/crop payload, on both the server and offline-reader paths. It still
  contains PHI and is attached manually through the project's approved work-email
  route. No automatic email, upload, analytics or additional model call occurs.
- Each new review has a random batch identifier, retained across updated copies
  and feedback. Analyses record prompt ID (or a custom-instruction hash), source
  build and configured Azure **deployment name**, not a verified underlying model
  version. Old results without provenance remain unknown rather than being
  relabeled with the current prompt. Metadata's default prompt ID describes the
  software default; per-case provenance identifies the instructions actually run.

Run offline checks with `.venv/Scripts/python.exe -m unittest discover -s tests`.
For browser checks, run `dev/serve-lookup-qa.py`, set `NODE_PATH` to the ignored
Playwright installation, and run `node dev/check-marks.cjs` and
`node dev/check-perspectives-severity.cjs`. All fixtures and responses are fictional.
The standalone HTML remains interactive without authentication or AI/network
requests; it does not inherit the live site's access controls.

## Title transport, severity colors and nonacute Major changes — November 6, 2026

Website source build **2026.11.06.1** fixes both streaming and individual-retry
response handlers: they previously discarded `title_resident`/`title_attending`
while retaining only `title`. Both titles now survive into the displayed case,
export payload and offline reader. Switching perspective uses those existing
fields, without additional analysis. Failed results preserve earlier titles;
successful legacy single-title results clear stale dual fields and use their
original title. Results/files that already lost a perspective need one reanalysis
to obtain it again.

Major summary arrows and attending endpoints are red in preview, expanded groups
and exports. Minor stays amber; resident wording retains the normal reading color.
The shared rubric now includes substantial diagnostic/management consequences
from important **nonacute** disease. Urgency is not required. Exact eligible-section
evidence and the Impression/Conclusion gate remain; cancer words, restated known
malignancy, description and routine follow-up are not automatically Major. Read
[REVIEW_CRITERIA.md](REVIEW_CRITERIA.md) for the current criteria. Reanalyze existing
results to apply the changed rubric; it is not a retrospective automatic regrade.

113 offline Python tests and production-browser checks pass, including streamed
and retry results, in-flight perspective changes, both themes, expanded colors,
real export serialization and offline switches without network calls. Model
responses are mocked; these checks do not establish clinical grading accuracy.
Cloud Run deployment remains pending; replace `main.py` and redeploy to activate.

## Screenshot lookup, OCR review and HTML export — November 4, 2026

The current source build appears in the footer after deployment. This is separate
from the PowerScribe extractor executable version (now v0.25).

Implemented in replacement source; Cloud Run deployment is still pending.

- The **Paste screenshot here** area is directly below the report-text box.
  Click it and press Ctrl+V, or use Paste screenshot. No file picker or manual
  column-marking controls are shown. Capture the exact list/order used for report
  extraction, including source numbers and accessions. The final lookup uses
  accessions, not MRNs.
- OCR runs in a browser worker. The app supplies pinned, SHA-256-checked public
  Tesseract.js 6.0.1/core 6.0.0/English model assets from its own `/ocr-assets/`
  routes. Cloud Run downloads those public runtime files on first use and caches
  them in process memory; full screenshots remain local during OCR. Only the cropped case/accession row
  pixels travel with lookup rows through the normal form (usable mappings in an export) to the
  authenticated application; they are never added to model requests. No OCR API key or
  Python dependency is added. Restricted outbound asset access can prevent OCR;
  manual row entry remains available.
- Case/accession columns are inferred from repeated row positions and two-letter
  accession prefixes; an Accession header is optional. Multiple competing columns
  or insufficient evidence request a clearer crop rather than guessing. Extra
  numeric columns are excluded from the case/accession crops. Native crop edges
  are snapped to pixels and enlargement adapts to text height. Narrow images
  receive a per-row, per-column pass. Progress counts completed work in each pass.
- Use **Paste screenshot of case number and accession** directly below the
  report text. Each accepted image becomes a collapsed card and the button
  offers the next screenshot. Additional images queue while OCR runs, up to
  20 per batch. Expand a card only to inspect or edit that image's rows. Confirmed overlapping coverage is kept once, using the first screenshot. Other
  accession disagreements remain available in Review OCR. Keep original PowerScribe numbers;
  the optional verified range applies to one screenshot's actual source numbers.
- OCR context corrections normalize 0T/07/O7 to OT, and letter O to zero only in
  the numeric part. Existing numeric digits are never trimmed, padded or guessed.
  XR, RF, MR, CT, OT, US and NM are recognized; other prefixes are flagged
  for inspection rather than guessed. A stable headerless 07-prefixed column
  can use the known OT correction without requiring a visible letter. Strong
  same-image digit-length consensus flags unusual lengths for correction.
- Every screenshot is treated as consecutive, increasing source cases. The
  strongest consistent start offset repairs all inconsistent case readings,
  including missing digits, digit substitutions and unread middle numbers.
  Corrected cases have no review warning. Exact accession anchors from other
  screenshots can recover a missing or incorrect image offset. If no absolute
  anchor exists anywhere, enter the first case once; all rows follow from it.
- **Review OCR** opens a focused overlay for remaining lookup issues. It shows
  the cropped original row beside the case/accession fields. Tab or Enter saves
  and advances; Shift+Tab goes back; Escape closes. Correcting a screenshot's
  first/start number also resolves and skips other case-only checks. Conflicting
  readings can be compared and one explicitly retained. Review stays optional;
  Analyze still supports best-available mappings without per-row confirmation.
- Overlaps are evaluated after sequence correction and again after review edits.
  Exact matches, two aligned exact accession anchors, or one exact anchor with
  aligned near-identical neighbors identify repeated coverage. The first image's
  row/accession/crop remains authoritative. Later repeated rows are blacked out
  in that image and omitted from lookup/review/export, including after a first
  reading is edited. Unrelated accession disagreements remain reviewable; case
  labels or shared accession prefixes alone do not discard rows.
- **Set first case number** is an optional per-image override with one input.
  It assigns the remaining consecutive numbers without a last-case field,
  spacing gate, or confirmation checkbox. Accession characters are unchanged.
- **Analyze reports accepts valid mappings automatically.** There are no per-row
  confirmation checkboxes. If OCR is running or rows are incomplete, flagged or
  conflicting, one confirmation lets analysis proceed with available mappings.
  Only complete, unambiguous mappings attach; uncertain mappings never receive
  an arbitrary accession. Unresolved rows, flags and bounded source crops survive
  Analyze for later editing, separately from AI requests. **View or edit lookup
  rows** reopens them; View row shows the retained crop after submission.
  Download review likewise offers to proceed with usable mappings, leaving
  unresolved rows out of that file. Missing mappings are reported rather than
  shifted. Leading zeros stay intact. No universal recognition-accuracy claim
  is made. Capture larger source text where possible.
- **View row preserves list position.** It highlights and scrolls the image pane
  without reattaching the active editor or resetting the table's scroll offset.
- Screenshot-level **needs correction** labels are recalculated after edits,
  removals and range changes, including conflicts shared by overlapping images.
- Source numbers are exact, batch-local keys. Lookup rows survive the
  normal Analyze form submission without sending them to Azure. Editing report
  input suspends copying/export against the old results until the new batch is
  analyzed. Clear reports clears lookup rows, screenshots and OCR worker memory.
  No lookup or screenshots are written to browser localStorage/IndexedDB.
- Each mapped card has a low-profile, 44-pixel **copy icon left of the caret**,
  with a Copy accession tooltip and brief feedback. It copies the earliest mapped
  group member without expanding the card. The full accession list and individual
  copy buttons sit below the Summary/Text changes content when expanded. Groups
  retain every mapped accession. Missing mappings remain explicit.
- **Download review HTML** creates a new offline reader. Optionally export only
  currently shown entries; other cases and their lookup rows are omitted from
  the file. Login or normal-page HTML is rejected before creating a download.
  Do not use a display filter as a substitute for correct participant
  attribution. Resident/attending authorship is not inferred by OCR.
- The download contains validated Findings/Impression/Conclusion, summaries,
  clinical diff/evidence, source numbers and accepted accessions. Context,
  attestations, raw errors/warnings, pasted-input controls, prompts and OCR
  runtime are omitted. Only case/accession row crops are embedded as source
  images; full screenshots and unrelated columns are excluded. The reader supports ordinary review controls
  and copy fallback without a server connection. Reports are embedded in the file,
  not loaded from localStorage; tests also cover unavailable storage. Ambiguous headings/footer
  variants remain a limitation; inspect a representative export before use.
- A persistent **Contains PHI** notice appears only in the exported reader,
  including print output. Use approved storage/delivery. A download does not
  retain the live website's authentication or become anonymous by removing
  headers. The banner is not access control or an institutional sensitivity label.

Every new analysis returns both resident-anchored and attending-anchored titles
in one response. The Resident/Attending toggle changes only the displayed title,
including in the offline reader, without another model request. Clinical grading
and the revision inventory are shared. Legacy single-title results keep their
original title in either view until explicitly reanalyzed.

Copying an accession opens a compact peek beneath its icon, with the recognized
number and original case/accession row image. Edit and copy a corrected value
there if needed. Corrections apply in memory to the open review. The offline
**Save review with corrections** button writes an updated standalone HTML file,
including the selected title perspective; it does not overwrite the old file or
contact a server. Image imports accept bounded PNG pixels and discard metadata.

## Overlay comparison experiment — October 30, 2026

A developer-only render/compare benchmark tests correct accessions against
substitutions, insertions, deletions and transpositions. It is **not enabled as a
production validator**: its frozen threshold detected only 38–47% of altered
strings on the three supplied screenshots. See `OCR_OVERLAY_EXPERIMENT.md` for
methods, limits, aggregate results and reproduction instructions. Screenshot
pixels and identifiers remain outside Git; Cloud Run dependencies are unchanged.

## Paste-ready 47-case test file

Open `dev/fixtures/synthetic-47-report-pairs.txt` and copy its entire contents
into Report input. It starts directly with `Case 1` and uses the extractor's
`Attending Report:` then `Resident Report:` format through `Case 47`.

All clinical content is invented and unrelated to any real accession list.
There are 47 distinct full report pairs, so grouping should retain 47 entries
with source numbers 1–47. Examples include unchanged reports, wording edits,
clinical additions/removals, laterality and interpretation changes, and a finding
added to the impression without changing its wording in Findings. Every report
includes an explicit synthetic-test indication. This is an input/UI fixture,
not a validated reference for model importance labels or clinical accuracy.

To test overlapping OCR with the user's 1–47 sample image, capture rows 1–20,
18–35 and 33–47 with their original case numbers and accession header. Add all
three images to the same batch without clearing lookup. Identical overlaps
should leave 47 mappings. Correct any OCR disagreements before analyzing.

To update the existing service, replace `main.py` and redeploy using the steps
below. `requirements.txt` is unchanged; the generated source includes all new
application code and the pinned asset manifest.

Updated October 29, 2026. Complete replacement source for the existing Google Cloud service. Based on the latest attached `main.py` (which matched the previous local source), not a readback of the live deployment. The October 29 updates add Resident/Attending title modes and group nearby identical full report pairs before analysis; the October 28 updates change summaries, expanded groups, text-change markers and filtering. The systematic-summary follow-up updates the prompt and required response fields without adding model requests.

## What to copy into Google Cloud

1. Save a copy of the currently working Google Cloud `main.py` before replacing it, so you can revert if needed.
2. Replace **all** of `main.py` with [main.py](main.py).
3. Keep the existing `requirements.txt`. [requirements.txt](requirements.txt) is included for reference and matches the supplied UAB-enabled version; this update adds no dependencies.
4. Keep the current environment variables, secret references, service settings, and the function entry point **`flask_entry_point`**. No new variables or secrets are required.
5. Redeploy through the same Google Cloud interface you already use.

Only those two files are needed in Google Cloud. The `dev` and `tests` folders are local development material; do not paste them into the cloud editor. The page template is already embedded inside `main.py`.

The existing `AUTHORITY`, `CLIENT_ID`, `CLIENT_SECRET`, `REDIRECT_URI`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION`, `MODEL_ID`, and optional `VERBOSITY` settings are used as before. This package does not require `TENANT_ID` or introduce a `FLASK_SECRET_KEY` requirement. It preserves the existing AzureOpenAI client and its endpoint/API-version convention; do not change a working endpoint solely because of this redesign.

## Reviewing a batch

Use the sun/moon switch at the upper right to select normal or night mode. It starts with your device's appearance, keeps a manual selection through report submissions and Clear reports, and returns to the device default on a fresh visit. It changes the entire page without rerunning analysis.

Choose **Resident** or **Attending** above Report input, or in the downloaded
reader. A fresh live visit defaults to Resident. Both titles are generated in the
same request, and switching instantly retitles results without new analysis.
Both modes share Findings/Impression scope, importance, Resident → Attending
summaries, grouping and filters. Older results with one title retain that title.


Extractor v0.11 copies completed pairs automatically after a successful export. Select **Paste** beside the report box, or click the box and press **Ctrl+V**, then select **Analyze reports**. Paste fills the box without submitting it; clipboard access is requested only on click and denied/empty reads preserve existing text. The input collapses after a valid submission. Cases appear immediately. The page sends up to 100 review entries (one representative full pair per group) in one server batch, and the server runs their independent Azure requests concurrently, restoring the original app's 100-worker approach. Summaries stream back as each case finishes. **Summary + text changes** is on by default: opening a case displays both panels together. Switch it off for the separate Summary/Text changes tabs. **Full reports** remains available in either mode.

Larger queues run in successive batches of up to 100 review entries (for example, 205 review entries use 100, 100, and 5). A group may be smaller to keep its UTF-8 JSON payload below the existing 5 MB request limit; original reports are never shortened. Instructions are sent once per browser batch and included in each independent model request. This is immediate concurrent processing, not the provider's separate offline Batch API. Actual completion time depends on the deployment, output length, capacity and rate limits; a ten-second result is not guaranteed. Rate-limited cases are explicitly identified for retry, and completed results remain available if another case fails or the connection breaks. Actual cloud streaming/buffering behavior has not been measured; results can arrive together if the hosting path buffers the stream.

Each row shows the source case number, exam label, a short case title, up to two change previews, and separate revision counts. The title is a memory cue based on the selected mode's report. It does not establish image truth or confirm the resident's diagnosis. The changes below it state what the attending added, removed, or changed.

The counts at the top are now visible filter buttons. **Major**, **Minor** and **Wording/detail** count revisions across the entire batch. **Needs review** counts cases with review items, partial results, missing section headings or analysis errors, including failed analyses that produced no revisions. **All cases**, **Not analyzed** and **No revisions** count cases. Counts grow as analyses complete and remain unchanged by search/filter choices.

Every revision uses the same **Resident → Attending** summary order. The resident side uses the normal reading color (white in night mode, dark in day mode); the arrow and attending side are amber. A short legend above the cases explains the order. Category badges identify importance independently of these colors. This applies to every action and category in both collapsed previews and expanded headings.

The model must return separate, concise `resident_summary` and `attending_summary` fields without embedded arrows. The resident side states the resident's finding; the attending side names its specific revision using a small set of action-specific patterns. Impression inclusion always reads, for example, `Small right pneumothorax → Added to Impression; finding unchanged`. The server standardizes that attending-side phrase for Emphasis items. Added detail, explicit negation and removal keep the same order. A new complication retains the already reported underlying finding as context instead of implying the entire diagnosis was missed. For example: `Diverticulitis without perforation → Diverticulitis with focal perforation`.

When a side has no quoted corresponding assertion, the server uses **Not documented** on the resident side or **Not retained in attending report** on the attending side. These indicate documentation status, not an inferred negative or a clinical resolution. Explicit negatives require quotation evidence. The server validates the two fields and generates the combined summary and arrow; it never extracts the two sides from free-form prose. Missing/malformed fields cause a visible incomplete-inventory warning rather than silently falling back to inconsistent summaries. Exact evidence-quotation checks remain in place; they do not independently verify the clinical meaning of a generated paraphrase.

Every revision in every group is visible when a case is expanded, including all Minor and Wording/detail items. There is no additional “Show remaining” step. The collapsed header still shows up to two previews plus the remaining count.

Click the visible filter buttons to choose one or several categories/statuses. Multiple selections include cases matching **any** selected filter; search narrows those results. Selected buttons have a checkmark and outline and expose their pressed state to assistive technology. Click a selected button again to remove it; deselecting the last restores all cases. **All cases** clears the selected buttons while keeping search. **Reset filters** clears both search and selections. Opening cases and changing filters or order never reruns analysis.

Use **Sort by** for oldest/newest/major first or highest/lowest text change. Chronology is an approximation based on original case numbers: oldest first sorts ascending; newest first sorts descending. The reports contain no reliable examination timestamps. If PowerScribe was ordered differently, the labels do not establish actual chronology. Original source numbers remain unchanged when cases are grouped. Group headers show ranges such as Cases 68–69 or explicit nonconsecutive numbers such as Cases 68, 71; the next separate case keeps its original number.

On import, [nearby identical full-report pairs](LINKED_REPORT_GROUPING_PLAN.md) are grouped before any AI requests. Both full resident reports and both full attending reports must match exactly after existing line-ending normalization and outer import trimming. Indication, comparison, technique, signatures, case, punctuation and internal whitespace remain part of equality; matching Findings alone or matching only one report side is insufficient. Each matching member must be 1–3 original source-case numbers after the previous matching member, so six consecutive identical pairs can form one entry. A gap of four starts a separate group; missing/incomplete rows still count in the original numbering. Complete pairs only are grouped, and nonascending pasted input stays separate. Groups are ordered by first appearance.

One representative pair is analyzed per group, with all member numbers retained in application metadata and mapped to that same full pair. Source totals and review-entry totals are shown separately; revision counts count the result once per group, not once per source row. Search finds every member number, sorting uses the group's first/last original numbers, and retry analyzes the representative once while retaining membership. The expanded note describes identical full reports and the proximity rule; this is a workflow heuristic, not confirmed shared patient identity or a proven list of linked studies. Fully identical nearby normal reports can still be separate examinations. Original extractor files are unchanged.

A small **X.X% changed** marker appears at the right of each case header above the revision badges. It uses the existing displayed Findings and Impression/Conclusion diff: `100 × (removed characters + added characters) / (characters in both versions)`, rounded to one decimal. Unchanged text contributes to both report lengths. Clinical heading text, whitespace and punctuation are included; context sections are excluded. Identical clinical text is 0%, a complete replacement is 100%, and missing/unrecognized/oversized pairs display a dash rather than a false zero. Cases without a percentage sort last in both directions; equal percentages use original case order. A coarse large-region diff displays ≈ and explains its approximation in the tooltip. This measures text volume, not clinical importance, and is available even if AI analysis fails.

The filter buttons appear directly above the case controls without a visible section label or instructional paragraph. Their accessible group labels remain available, and Reset filters appears when needed.

**Show/Hide report wording** changes only the current case. A plain-text **Hide in all cases** or **Show in all cases** action appears below it for two seconds, without a box or X button. Mouse movement and hovering do not extend that deadline. Keyboard focus keeps the action available until focus leaves; Escape dismisses it. Only choosing that action changes the other cases and sets the default for unopened cases, incoming results and subsequent report submissions. A later individual toggle remains local. Local choices survive collapse/reopen, filtering, sorting, view changes and streaming; Clear reports discards them while retaining the last explicit all-cases default. A fresh visit starts with wording shown.

Both actions keep the current toggle in the same viewport position, including when earlier cases shrink or expand. Evidence and button states update in place, preserving focus, pinned report links and report-panel scrolling. The optional action floats below the toggle without pushing the content down. Hiding evidence does not hide the summary or the text-change report panel; these controls send no model requests.

The **analysis needs attention** and **not submitted for analysis** notices are clickable. Each clears an unrelated search, filters to the exact cases counted by that notice, opens the first affected case and scrolls to it. Its summary explains the next step: retry an attempted analysis, recapture an incomplete pair, or correct input/section problems and resubmit. Skipped-only batches still show the notice. These are processing/input groups; the broader **Needs review** filter also includes uncertain clinical revision items. Opening a notice never retries, uploads or analyzes reports automatically.

See [ATTENDING_VIEW_PROPOSAL.md](ATTENDING_VIEW_PROPOSAL.md) for the implemented title-mode contract and deferred ideas. Feedback tracking remains deferred, and [STUDY_PLAN.md](STUDY_PLAN.md) keeps proposed QI/research outcomes and measurement outside the website. No study data collection is implemented.

**Customize instructions** shows one shared, editable default prompt. Switching
title perspective leaves edits intact. Analyze and explicit Retry use the current
instructions; in-flight analyses keep the prompt they started with. Restore default
instructions resets the shared draft. Responses require both titles plus one shared
revision inventory; legacy single-title results remain readable. Existing quotation,
section and category validation still applies. Instructions are limited to 40,000
characters.

The top **Summary + text changes** switch widens the review area and shows the summary on the left and clinical diff on the right in every expanded case, with a clear divider and matching top/bottom edges. On narrower screens, the two labeled panels stack. Full reports remain accessible. The preference stays set through a new batch submission and clearing reports on the current page; it is not saved across a fresh visit. Changing the view sends no model requests.

In dual view, hover over a revision to highlight its exact report wording. Click its heading or card to pin the selection; keyboard users can focus a heading and press Enter. **Unpin** clears it. The report panel stays visible as you scroll a long desktop summary, and brings an offscreen passage into its own scroll area without moving the page. On narrow screens the report stays in normal flow.

The text-change view retains and bolds the original clinical headings, including Findings, Impression/Conclusion and combined headings. They remain visible in inline, side-by-side and dual views. Each source retains its own heading names; context-only headings such as Indication and Technique remain available in Full reports. Passage evidence is matched to section bodies with positions adjusted for the displayed headings.

Links use the model's already-required exact quotations and section IDs. The server calculates positions against the same text used by the diff; the AI never invents character positions. Findings and Impression are distinguished, including a separate eligible impression anchor for Major changes. If a quotation occurs more than once within its named section, all occurrences are highlighted and **Next passage** cycles between them. The prompt requests specific surrounding wording to reduce ambiguity. Missing/invalid quotations cannot create a guessed link. Only the side with quoted evidence is marked; added findings do not fabricate resident passages. Overlapping quotations and Unicode are supported without changing report text. This adds no model calls.

Clear reports removes reports, results and the edited prompt draft from the current page, keeps the selected mode, and restores its default prompt. A request already received by the server may finish even after the browser cancels it.

## Long reports and uncertainty

- Full reports go to the model as context. Only recognized Findings, Impression/Conclusion, and combined sections enter the clinical diff and revision evidence.
- The parser handles singular/plural headings, combined headings, conclusion-only reports, repeated clinical sections, anatomy subheadings, and common contextual/footer headings. Headings are expected at line starts. It cannot guarantee correct interpretation of every institution's free-text format.
- Missing section boundaries produce **Needs review**, not an AI grade or a false clean result. Original reports remain available.
- The limits are 5 MB per submitted request, 250 source cases per batch, and 120,000 characters per individual report. Oversized content is explicitly rejected or left unprocessed; it is never silently shortened.
- Long text diffs have a bounded matching fallback. A very large rewritten region may appear as one replacement, but the original text remains intact.
- The model gets an output allowance of 16,384 tokens, including any reasoning tokens the deployment charges against that allowance. If the API says it did not finish, the case is marked unavailable rather than graded from a truncated response. Extremely complex cases can still exceed this allowance.
- Exact quotation and section checks detect unsupported evidence. Valid items survive a partially invalid response, accompanied by a conspicuous limitation notice. These checks cannot establish clinical truth or guarantee that the model found every revision.

## What was verified

For the complete current importance criteria, the Major section rule, calibration examples and the limits of mechanical validation, read [REVIEW_CRITERIA.md](REVIEW_CRITERIA.md). [ANALYSIS_PROMPT.md](ANALYSIS_PROMPT.md) and [ATTENDING_ANALYSIS_PROMPT.md](ATTENDING_ANALYSIS_PROMPT.md) export the identical shared defaults for both views. `dev/assemble.py` produces both without importing authentication or contacting the provider; regression tests verify shared instructions and both required title fields. Customized instructions replace this default; the current editor contents are what the model receives.

Local regression tests use synthetic reports and mocked Azure responses. A 100-party barrier proves that 100 server workers reach the model call concurrently. Browser checks cover 100-case progressive results, 205-case grouping, UTF-8 byte limits, interrupted connections, prompt-specific retries, exact/repeated/overlapping passage links, keyboard pinning, page-stable sticky report scrolling, and responsive layout/report fidelity. No live latency measurement is claimed.

The actual installed identity library was also imported with synthetic configuration and network access blocked: startup, server-side session setup, and `/redirect` registration succeeded. The existing Microsoft login flow and actual Azure model responses have **not** been exercised against your live service. The prototype contains prewritten illustrative feedback, not a clinical model evaluation. No patient reports or paid API calls were used to build or test it.

After your deployment, verify a small synthetic pair through UAB login before relying on a work batch. The current code preserves the supplied local filesystem authentication session cache; the prior single-instance/session-affinity considerations still apply. This redesign does not establish institutional PHI approval or change your cloud provider's retention agreements.

## Development

`dev/review-template.html` is the authoring source for the embedded UI. Run `python dev/assemble.py` after editing it. Backend code lives directly in `main.py` above the template marker. Run `python -m unittest discover -s tests -v` for regression tests. `python dev/synthetic_preview.py` creates ignored synthetic QA output; `node dev/check-ui.cjs` checks layout, `node dev/check-review-controls.cjs` checks the October 28 controls, `node dev/check-paste.cjs` checks clipboard handoff without accessing the system clipboard, and `node dev/check-mode.cjs` checks native mode selection, defaults/drafts, form submission, request snapshots, explicit retries and title provenance, `node dev/check-grouping.cjs` checks imported group labels/counts, representative requests, search, sort, filters, retries and mobile layout, and `node dev/check-batching.cjs` checks progressive batches against a synthetic local streaming server, using Edge and Playwright. These commands are for development; you do not need a terminal to copy the replacement files into Google Cloud.

Run `node dev/check-highlights.cjs` after generating the synthetic preview to verify passage links, keyboard interaction and sticky scrolling.

See [CHANGELOG.md](CHANGELOG.md) for each change and its rationale, and [VALIDATION.md](VALIDATION.md) for the verification record and limits.
