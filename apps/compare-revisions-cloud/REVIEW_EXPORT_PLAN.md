# Shared review, two title perspectives, standalone HTML

Design only, October 29, 2026. No prompt, API, UI or exporter implementation is
changed by this plan. The Cloud Run deployment has not been verified or updated.

## Current source behavior

`main.py` defines a shared assessment prompt and an attending variant made by
replacing the resident title rule. Each AI response generates one title. The
mode selector chooses the prompt used for a new analysis; it does not generate
both titles or retitle existing results. All other assessment rules are shared.

Full reports are used for context and exact-pair grouping. Clinical sections
are parsed for evidence and displayed diff. That parser is not yet a complete
export filter: unfamiliar headings, mixed sections and footer variants need
explicit handling. Removing headers alone does not de-identify clinical text.

## Planned dual-title response

Request both `title_resident` and `title_attending` in a single AI response for
each grouped pair. Generate revisions, evidence, importance and summaries once.

- Resident title: memorable cue from the initial interpretation, preserving
  uncertainty. A removed resident diagnosis may still be an appropriate cue.
- Attending title: cue from the final interpretation, preserving uncertainty and
  avoiding a diagnosis the attending refuted.
- Both titles describe the case; neither is a list of revisions or a claim of
  independently verified diagnostic truth.
- Keep resident text followed by attending text in every revision. Do not
  reverse arrows, change category definitions or use role-specific judgments.
- The Resident/Attending control changes only which title is displayed, with
  no AI request. Use it in both the live review and downloaded file. Resident
  remains the initial default.
- Validate both title fields. Define a neutral fallback for legacy responses
  with only one title; switching modes must not silently rerun old cases.

## Planned standalone HTML

Build a new document from a deliberately limited export data object. Do not
save or clone the live page, serialize the entire app state, or hide unwanted
fields with CSS.

| Include | Exclude from the entire file |
| --- | --- |
| Original source case numbers and group labels | Full pasted input or full report strings |
| Both titles, modality if retained/validated | Indication/history, comparison, technique |
| Shared clinical revision summaries and categories | Attestations, signatures, administrative metadata |
| Parsed Findings/Impression/Conclusion text on both sides | Original context in hidden JSON, scripts, comments or attributes |
| Validated clinical quotes and rebuilt diff anchors | Prompts, credentials, tokens, raw errors or failed API payloads |
| Completion status and short sanitized error statuses | Input boxes, analysis controls, API calls, external runtime dependencies |
| Filters, sorting, case expansion, report wording control, title toggle | Embedded analytics or unrequested tracking |

Use an explicit allowlist of fields. Trim excluded context before serialization;
rebuild quote and diff offsets against exactly the retained clinical text.
Check generated titles/summaries too: allowed field names alone cannot prevent
an AI field from repeating excluded context. For unrecognized or ambiguous
sections, omit/flag the affected text rather than exporting the full report as
a fallback. Do not rely on an AI instruction as the sole exclusion mechanism.

Keep the review useful offline: inline required styles/scripts, no external
fonts/libraries or service calls. Escape report text as text, safely encode
embedded data, and handle literal HTML/script-like text without execution.
Preserve original case numbers and grouped labels. Incomplete entries remain
visible as sanitized statuses so missing analysis is not mistaken for normal.

This is a clinical-content export, not a claim of anonymization. Findings and
summaries can themselves contain identifying or sensitive content. Delivery and
storage need an institution-approved channel; this plan does not authorize
patient-report sharing through Google Forms, Notion or public hosting.

## Acceptance checks for future implementation

1. A mocked analysis returns both titles, with identical revisions under either
   view. Title switching makes zero network requests and preserves scroll/filter
   state.
2. A grouped pair produces one analysis and keeps its original grouped label.
3. Unique exclusion markers placed in comparison, technique, indication,
   attestations, signatures and full-input fields are absent from every byte of
   the export, including hidden serialized data and generated fields.
4. Test recognized sections, headingless text, combined headings, unfamiliar
   footers, context after Findings, failed analyses and legacy one-title data.
5. Clinical text containing markup or a closing script tag cannot execute code.
6. Open the file offline in a fresh browser context: title toggle, filters,
   sorting, expanding cases and wording controls work without credentials or
   network requests. The report-entry area is absent.
7. Clinically review a small approved sample to confirm that required learning
   context remains while excluded sections are absent.

## Sequence before the pilot

Review survey drafts and measurement choices; confirm roster, operators and
institutional determination; implement the two-title response; implement/test
the clinical-only HTML export; dry-run preparation and approved delivery;
record versions and launch the agreed 3-usual/4-tool sequence. Keep the survey
and operational log separate from the product. See [STUDY_PLAN.md](STUDY_PLAN.md).
