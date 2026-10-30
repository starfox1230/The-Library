# Compare Revisions: cloud review redesign

## Screenshot lookup and HTML export — October 29, 2026

Implemented in replacement source; Cloud Run deployment is still pending.

- Expand **Case lookup · screenshots to accessions**. Add PNG/JPEG/WebP files,
  use Paste screenshot, or press Ctrl+V inside that section. Capture the exact
  list/order used for the report extraction, including source numbers and the
  accession column. The final lookup uses accessions, not MRNs.
- OCR runs in a browser worker. The app supplies pinned, SHA-256-checked public
  Tesseract.js 6.0.1/core 6.0.0/English model assets from its own `/ocr-assets/`
  routes. Cloud Run downloads those public runtime files on first use and caches
  them in process memory; screenshots are never uploaded. No OCR API key or
  Python dependency is added. Restricted outbound asset access can prevent OCR;
  manual row entry remains available.
- Headers are detected when possible. For a blank row-number header, a clearly
  separated numeric column left of Accession can be detected. Otherwise mark
  the two column widths on the image and select Read marked columns. Narrow
  images receive a per-row, per-column pass. Reading is not verification.
- Case numbers are still read by OCR. An incomplete or duplicate reading can
  be repaired when at least 60% of rows provide unique, consistent consecutive
  anchors, including anchors near both ends, with regular row spacing. A
  contradictory readable number, source gap or missing-row spacing blocks
  automatic repair. Suggested numbers are highlighted and remain unconfirmed.
  **Use verified consecutive case numbers** is an optional fallback: enter the
  first/last source numbers and explicitly verify that every row is present in
  order. The count must match. Neither method changes accession strings.
- Check every **case number and accession**, correct errors, then check Confirmed.
  View row or focus a field to see its highlighted source row in an enlarged
  image. Leading zeros stay intact. Duplicate-case conflicts block export; missing mappings
  are reported rather than shifted. No universal recognition-accuracy claim is
  made. Capture larger source text where possible.
- Source numbers are exact, batch-local keys. Confirmed lookup rows survive the
  normal Analyze form submission without sending them to Azure. Editing report
  input suspends copying/export against the old results until the new batch is
  analyzed. Clear reports clears lookup rows, screenshots and OCR worker memory.
  No lookup or screenshots are written to browser localStorage/IndexedDB.
- Each mapped review card has **Copy accession**, followed by a short copied
  confirmation. Groups retain every mapped accession; the primary button copies
  the accession belonging to the earliest mapped source member. Expand the
  accession list to copy another. This is a locator, not proof of patient or
  linked-study identity. Mapping gaps are shown explicitly.
- **Download review HTML** creates a new offline reader. Optionally export only
  currently shown entries; other cases and their lookup rows are omitted from
  the file. Do not use a display filter as a substitute for correct participant
  attribution. Resident/attending authorship is not inferred by OCR.
- The download contains validated Findings/Impression/Conclusion, summaries,
  clinical diff/evidence, source numbers and confirmed accessions. Context,
  attestations, raw errors/warnings, pasted-input controls, prompts and OCR
  screenshots/runtime are omitted. The reader supports ordinary review controls
  and copy fallback without a server connection. Ambiguous headings/footer
  variants remain a limitation; inspect a representative export before use.
- A persistent **Contains PHI** notice appears only in the exported reader,
  including print output. Use approved storage/delivery. A download does not
  retain the live website's authentication or become anonymous by removing
  headers. The banner is not access control or an institutional sensitivity label.

The existing Resident/Attending prompt modes are unchanged: one selected title
per analysis. Generating both title perspectives in one response remains a
separate planned change; this update does not add model calls or alter grading.

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

Choose **Resident** or **Attending** in the pill control directly above Report input. Resident is the default on a fresh visit. Resident titles recall the resident's original interpretation; Attending titles follow the attending's final interpretation and its uncertainty. Both modes share the same Findings/Impression scope, importance criteria, Resident → Attending summaries, case grouping, filters, sorting and display. Mode changes send no requests and do not retitle existing results. A short hint explains when older results belong to the other mode, and each title's tooltip identifies its accepted review mode. Analyze again (or explicitly retry an eligible case) to generate a title in the other mode.

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

**Customize instructions** shows the selected mode's full default prompt, prefilled and editable. Resident and Attending defaults differ only in title instructions. Switching modes keeps separate editable drafts on the current page; Restore default instructions resets only the selected mode. Edits replace the model's system instructions; no hidden default rubric is appended. **Analyze reports** sends the edited prompt for the next batch, and **Retry analysis** uses the current editor contents for that case. An already-running batch keeps its original prompt. **Restore default instructions** restores the supplied prompt without changing existing results. The response fields, clinical-section boundaries, source-quotation checks, and Major/wording validation remain enforced by code; the editor explains those fixed requirements. Instructions have an explicit 40,000-character limit.

The top **Summary + text changes** switch widens the review area and shows the summary on the left and clinical diff on the right in every expanded case, with a clear divider and matching top/bottom edges. On narrower screens, the two labeled panels stack. Full reports remain accessible. The preference stays set through a new batch submission and clearing reports on the current page; it is not saved across a fresh visit. Changing the view sends no model requests.

In dual view, hover over a revision to highlight its exact report wording. Click its heading or card to pin the selection; keyboard users can focus a heading and press Enter. **Unpin** clears it. The report panel stays visible as you scroll a long desktop summary, and brings an offscreen passage into its own scroll area without moving the page. On narrow screens the report stays in normal flow.

The text-change view retains and bolds the original clinical headings, including Findings, Impression/Conclusion and combined headings. They remain visible in inline, side-by-side and dual views. Each source retains its own heading names; context-only headings such as Indication and Technique remain available in Full reports. Passage evidence is matched to section bodies with positions adjusted for the displayed headings.

Links use the model's already-required exact quotations and section IDs. The server calculates positions against the same text used by the diff; the AI never invents character positions. Findings and Impression are distinguished, including a separate eligible impression anchor for Major changes. If a quotation occurs more than once within its named section, all occurrences are highlighted and **Next passage** cycles between them. The prompt requests specific surrounding wording to reduce ambiguity. Missing/invalid quotations cannot create a guessed link. Only the side with quoted evidence is marked; added findings do not fabricate resident passages. Overlapping quotations and Unicode are supported without changing report text. This adds no model calls.

Clear reports removes reports, results and both edited prompt drafts from the current page, keeps the selected mode, and restores its default prompt. A request already received by the server may finish even after the browser cancels it.

## Long reports and uncertainty

- Full reports go to the model as context. Only recognized Findings, Impression/Conclusion, and combined sections enter the clinical diff and revision evidence.
- The parser handles singular/plural headings, combined headings, conclusion-only reports, repeated clinical sections, anatomy subheadings, and common contextual/footer headings. Headings are expected at line starts. It cannot guarantee correct interpretation of every institution's free-text format.
- Missing section boundaries produce **Needs review**, not an AI grade or a false clean result. Original reports remain available.
- The limits are 5 MB per submitted request, 250 source cases per batch, and 120,000 characters per individual report. Oversized content is explicitly rejected or left unprocessed; it is never silently shortened.
- Long text diffs have a bounded matching fallback. A very large rewritten region may appear as one replacement, but the original text remains intact.
- The model gets an output allowance of 16,384 tokens, including any reasoning tokens the deployment charges against that allowance. If the API says it did not finish, the case is marked unavailable rather than graded from a truncated response. Extremely complex cases can still exceed this allowance.
- Exact quotation and section checks detect unsupported evidence. Valid items survive a partially invalid response, accompanied by a conspicuous limitation notice. These checks cannot establish clinical truth or guarantee that the model found every revision.

## What was verified

For the complete current importance criteria, the Major section rule, calibration examples and the limits of mechanical validation, read [REVIEW_CRITERIA.md](REVIEW_CRITERIA.md). [ANALYSIS_PROMPT.md](ANALYSIS_PROMPT.md) and [ATTENDING_ANALYSIS_PROMPT.md](ATTENDING_ANALYSIS_PROMPT.md) export the exact Resident and Attending defaults. `dev/assemble.py` produces both without importing authentication or contacting the provider; regression tests verify equality and that only the title rule differs. Customized instructions replace this default; the current editor contents are what the model receives.

Local regression tests use synthetic reports and mocked Azure responses. A 100-party barrier proves that 100 server workers reach the model call concurrently. Browser checks cover 100-case progressive results, 205-case grouping, UTF-8 byte limits, interrupted connections, prompt-specific retries, exact/repeated/overlapping passage links, keyboard pinning, page-stable sticky report scrolling, and responsive layout/report fidelity. No live latency measurement is claimed.

The actual installed identity library was also imported with synthetic configuration and network access blocked: startup, server-side session setup, and `/redirect` registration succeeded. The existing Microsoft login flow and actual Azure model responses have **not** been exercised against your live service. The prototype contains prewritten illustrative feedback, not a clinical model evaluation. No patient reports or paid API calls were used to build or test it.

After your deployment, verify a small synthetic pair through UAB login before relying on a work batch. The current code preserves the supplied local filesystem authentication session cache; the prior single-instance/session-affinity considerations still apply. This redesign does not establish institutional PHI approval or change your cloud provider's retention agreements.

## Development

`dev/review-template.html` is the authoring source for the embedded UI. Run `python dev/assemble.py` after editing it. Backend code lives directly in `main.py` above the template marker. Run `python -m unittest discover -s tests -v` for regression tests. `python dev/synthetic_preview.py` creates ignored synthetic QA output; `node dev/check-ui.cjs` checks layout, `node dev/check-review-controls.cjs` checks the October 28 controls, `node dev/check-paste.cjs` checks clipboard handoff without accessing the system clipboard, and `node dev/check-mode.cjs` checks native mode selection, defaults/drafts, form submission, request snapshots, explicit retries and title provenance, `node dev/check-grouping.cjs` checks imported group labels/counts, representative requests, search, sort, filters, retries and mobile layout, and `node dev/check-batching.cjs` checks progressive batches against a synthetic local streaming server, using Edge and Playwright. These commands are for development; you do not need a terminal to copy the replacement files into Google Cloud.

Run `node dev/check-highlights.cjs` after generating the synthetic preview to verify passage links, keyboard interaction and sticky scrolling.

See [CHANGELOG.md](CHANGELOG.md) for each change and its rationale, and [VALIDATION.md](VALIDATION.md) for the verification record and limits.
