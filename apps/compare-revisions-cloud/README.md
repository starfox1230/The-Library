# Compare Revisions: cloud review redesign

Updated October 28, 2026. Complete replacement source for the existing Google Cloud service. Based on the latest attached `main.py` (which matched the previous local source), not a readback of the live deployment. The October 28 update changes summaries, expanded groups, text-change markers and filtering without changing the model prompt or adding model requests.

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

Extractor v0.11 copies completed pairs automatically after a successful export. Select **Paste** beside the report box, or click the box and press **Ctrl+V**, then select **Analyze reports**. Paste fills the box without submitting it; clipboard access is requested only on click and denied/empty reads preserve existing text. The input collapses after a valid submission. Cases appear immediately. The page sends up to 100 report pairs in one server batch, and the server runs their independent Azure requests concurrently, restoring the original app's 100-worker approach. Summaries stream back as each case finishes. **Summary + text changes** is on by default: opening a case displays both panels together. Switch it off for the separate Summary/Text changes tabs. **Full reports** remains available in either mode.

Larger submissions run in successive groups of up to 100 (for example, 205 pairs use 100, 100, and 5). A group may be smaller to keep its UTF-8 JSON payload below the existing 5 MB request limit; original reports are never shortened. Instructions are sent once per browser batch and included in each independent model request. This is immediate concurrent processing, not the provider's separate offline Batch API. Actual completion time depends on the deployment, output length, capacity and rate limits; a ten-second result is not guaranteed. Rate-limited cases are explicitly identified for retry, and completed results remain available if another case fails or the connection breaks. Actual cloud streaming/buffering behavior has not been measured; results can arrive together if the hosting path buffers the stream.

Each row shows the source case number, exam label, a short case title, up to two change previews, and separate revision counts. The title is intended as a memory cue, usually based on the resident's main finding. It is not an assertion that the resident's diagnosis was confirmed. The changes below it state what the attending added, removed, or changed.

The counts at the top are now visible filter buttons. **Major**, **Minor** and **Wording/detail** count revisions across the entire batch. **Needs review** counts cases with review items, partial results, missing section headings or analysis errors, including failed analyses that produced no revisions. **All cases**, **Not analyzed** and **No revisions** count cases. Counts grow as analyses complete and remain unchanged by search/filter choices.

Directional summaries such as `resident wording → attending wording` show the resident side in the normal reading color (white in night mode, dark in day mode) and the arrow plus attending side in amber. This applies both below the case title and in expanded revision headings. Summaries without an explicit arrow keep their existing category color in previews; no before/after direction is guessed. Evidence quotes remain exact.

Every revision in every group is visible when a case is expanded, including all Minor and Wording/detail items. There is no additional “Show remaining” step. The collapsed header still shows up to two previews plus the remaining count.

Click the visible filter buttons to choose one or several categories/statuses. Multiple selections include cases matching **any** selected filter; search narrows those results. Selected buttons have a checkmark and outline and expose their pressed state to assistive technology. Click a selected button again to remove it; deselecting the last restores all cases. **All cases** clears the selected buttons while keeping search. **Reset filters** clears both search and selections. Opening cases and changing filters or order never reruns analysis.

Use **Sort by** for oldest/newest/major first or highest/lowest text change. Chronology is an approximation based on original case numbers: oldest first sorts ascending; newest first sorts descending. The reports contain no reliable examination timestamps. If PowerScribe was ordered differently, the labels do not establish actual chronology. Each numbered source case remains separate, including matching normal templates. Identical report text cannot establish linked-study identity; genuine linked studies also remain separate until reliable identity is available.

A small **X.X% text changed** marker appears at the right of each case header above the revision badges. It uses the existing displayed Findings and Impression/Conclusion diff: `100 × (removed characters + added characters) / (characters in both versions)`, rounded to one decimal. Unchanged text contributes to both report lengths. Clinical heading text, whitespace and punctuation are included; context sections are excluded. Identical clinical text is 0%, a complete replacement is 100%, and missing/unrecognized/oversized pairs display a dash rather than a false zero. Cases without a percentage sort last in both directions; equal percentages use original case order. A coarse large-region diff displays ≈ and explains its approximation in the tooltip. This measures text volume, not clinical importance, and is available even if AI analysis fails.

**Customize instructions** shows the full default model prompt, prefilled and editable. Edits replace the model's system instructions; no hidden default rubric is appended. **Analyze reports** sends the edited prompt for the next batch, and **Retry analysis** uses the current editor contents for that case. An already-running batch keeps its original prompt. **Restore default instructions** restores the supplied prompt without changing existing results. The response fields, clinical-section boundaries, source-quotation checks, and Major/wording validation remain enforced by code; the editor explains those fixed requirements. Instructions have an explicit 40,000-character limit.

The top **Summary + text changes** switch widens the review area and shows the summary on the left and clinical diff on the right in every expanded case, with a clear divider and matching top/bottom edges. On narrower screens, the two labeled panels stack. Full reports remain accessible. The preference stays set through a new batch submission and clearing reports on the current page; it is not saved across a fresh visit. Changing the view sends no model requests.

In dual view, hover over a revision to highlight its exact report wording. Click its heading or card to pin the selection; keyboard users can focus a heading and press Enter. **Unpin** clears it. The report panel stays visible as you scroll a long desktop summary, and brings an offscreen passage into its own scroll area without moving the page. On narrow screens the report stays in normal flow.

The text-change view retains and bolds the original clinical headings, including Findings, Impression/Conclusion and combined headings. They remain visible in inline, side-by-side and dual views. Each source retains its own heading names; context-only headings such as Indication and Technique remain available in Full reports. Passage evidence is matched to section bodies with positions adjusted for the displayed headings.

Links use the model's already-required exact quotations and section IDs. The server calculates positions against the same text used by the diff; the AI never invents character positions. Findings and Impression are distinguished, including a separate eligible impression anchor for Major changes. If a quotation occurs more than once within its named section, all occurrences are highlighted and **Next passage** cycles between them. The prompt requests specific surrounding wording to reduce ambiguity. Missing/invalid quotations cannot create a guessed link. Only the side with quoted evidence is marked; added findings do not fabricate resident passages. Overlapping quotations and Unicode are supported without changing report text. This adds no model calls.

Clear reports removes reports, results, and edited instructions from the current page and restores the default prompt. A request already received by the server may finish even after the browser cancels it.

## Long reports and uncertainty

- Full reports go to the model as context. Only recognized Findings, Impression/Conclusion, and combined sections enter the clinical diff and revision evidence.
- The parser handles singular/plural headings, combined headings, conclusion-only reports, repeated clinical sections, anatomy subheadings, and common contextual/footer headings. Headings are expected at line starts. It cannot guarantee correct interpretation of every institution's free-text format.
- Missing section boundaries produce **Needs review**, not an AI grade or a false clean result. Original reports remain available.
- The limits are 5 MB per submitted request, 250 source cases per batch, and 120,000 characters per individual report. Oversized content is explicitly rejected or left unprocessed; it is never silently shortened.
- Long text diffs have a bounded matching fallback. A very large rewritten region may appear as one replacement, but the original text remains intact.
- The model gets an output allowance of 16,384 tokens, including any reasoning tokens the deployment charges against that allowance. If the API says it did not finish, the case is marked unavailable rather than graded from a truncated response. Extremely complex cases can still exceed this allowance.
- Exact quotation and section checks detect unsupported evidence. Valid items survive a partially invalid response, accompanied by a conspicuous limitation notice. These checks cannot establish clinical truth or guarantee that the model found every revision.

## What was verified

Local regression tests use synthetic reports and mocked Azure responses. A 100-party barrier proves that 100 server workers reach the model call concurrently. Browser checks cover 100-case progressive results, 205-case grouping, UTF-8 byte limits, interrupted connections, prompt-specific retries, exact/repeated/overlapping passage links, keyboard pinning, page-stable sticky report scrolling, and responsive layout/report fidelity. No live latency measurement is claimed.

The actual installed identity library was also imported with synthetic configuration and network access blocked: startup, server-side session setup, and `/redirect` registration succeeded. The existing Microsoft login flow and actual Azure model responses have **not** been exercised against your live service. The prototype contains prewritten illustrative feedback, not a clinical model evaluation. No patient reports or paid API calls were used to build or test it.

After your deployment, verify a small synthetic pair through UAB login before relying on a work batch. The current code preserves the supplied local filesystem authentication session cache; the prior single-instance/session-affinity considerations still apply. This redesign does not establish institutional PHI approval or change your cloud provider's retention agreements.

## Development

`dev/review-template.html` is the authoring source for the embedded UI. Run `python dev/assemble.py` after editing it. Backend code lives directly in `main.py` above the template marker. Run `python -m unittest discover -s tests -v` for regression tests. `python dev/synthetic_preview.py` creates ignored synthetic QA output; `node dev/check-ui.cjs` checks layout, `node dev/check-review-controls.cjs` checks the October 28 controls, `node dev/check-paste.cjs` checks clipboard handoff without accessing the system clipboard, and `node dev/check-batching.cjs` checks progressive batches against a synthetic local streaming server, using Edge and Playwright. These commands are for development; you do not need a terminal to copy the replacement files into Google Cloud.

Run `node dev/check-highlights.cjs` after generating the synthetic preview to verify passage links, keyboard interaction and sticky scrolling.

See [CHANGELOG.md](CHANGELOG.md) for each change and its rationale, and [VALIDATION.md](VALIDATION.md) for the verification record and limits.
