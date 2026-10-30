# Shared review, two title perspectives, standalone HTML

Updated October 30, 2026. Screenshot OCR, action-accepted accession lookup, grouped
copy actions and standalone HTML export are now implemented in source. The PHI
banner appears only in the downloaded reader. Cloud Run deployment is pending.
See README.md for the implemented workflow. Dual-title generation remains planned.

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

## Standalone HTML (implemented)

Build a new document from a deliberately limited export data object. Do not
save or clone the live page, serialize the entire app state, or hide unwanted
fields with CSS.

| Include | Exclude from the entire file |
| --- | --- |
| Original source case numbers and group labels | Full pasted input or full report strings |
| Valid accessions accepted by Analyze/Download, keyed to source numbers | MRN lookup fields, raw lookup screenshots or invalid or conflicting lookup rows |
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

## Same-session screenshot lookup and recipient assignment

Capture the report list, source case numbers and visible accessions during
the same extraction session, keeping sort order and filters stable. Do not ask
recipients to reproduce the original list later. Case numbers are batch-local
labels, not permanent exam identifiers.

The optional screenshot-paste step is in the preparation web app. Process OCR
locally in the browser, show extracted rows beside their source image regions,
and accept valid mappings when Analyze/Download is used, without individual
approval checkboxes. Missing or conflicting mappings still require correction. The comparison
AI does not need the accession lookup; attach it to the review only.
Match by batch and explicit source number, never by shifting remaining rows
after an OCR omission. Case-label repair requires one consistent consecutive
sequence supported by unique anchors and regular row spacing; repairs remain
highlighted for inspection, with no individual confirmation requirement. An optional verified first/last range requires
operator acknowledgement and an exact row count. Numeric digits are never
trimmed, padded or inferred. Two-letter/numeric context corrects OT prefix
confusions and O in a numeric position; unusual digit lengths are flagged. Preserve leading zeros and flag missing, conflicting or
ambiguous rows. Preserve each source member's accession when grouping. The
accession-only lookup does not prove same-patient identity; an MRN-based identity
check is not implemented. An operator must resolve an incorrectly grouped pair.

Resident/attending attribution must be established by the operator before
delivery; automatic author assignment is not implemented. Do not infer
authorship from report wording or accession. If PowerScribe supports filtering,
preparing one known resident-attending
pair per batch is the simplest initial workflow; capability remains unverified.
Generate each recipient's file from only their assigned cases. A filter hiding
other recipients' cases is not equivalent to omitting those cases from the file.

Include the accepted lookup in the review HTML, with copyable identifiers;
recipients do not need a separate mapping file. The exported reader does not
need the original screenshots or OCR runtime. Adding these locator fields does
not permit export of excluded report context such as technique or comparison.

## Persistent PHI notice (exported reader only)

The identified review is deliberately treated as PHI. Keep a compact, visible
banner at the top of the exported review, sticky while scrolling, readable in
both themes and on narrow screens. Do not require acknowledgement or repeatedly
interrupt review. Proposed copy:

> **Contains PHI.** Use and share only within UAB-approved systems and with
> authorized recipients. Do not forward to personal email or upload to
> unapproved services.

Include the reminder in print output; keep the persistent banner off the input
website as requested. Use an
ordinary filename that contains no MRN, accession or patient name. Do not label
the file anonymous or de-identified merely because identifiers are collapsed or
removed. Clinical narratives may themselves identify a patient.

The banner is a handling reminder, not encryption, authentication, forwarding
prevention or access control. Agree on the actual delivery/storage workflow
with the project team. A downloaded HTML file does not inherit the live site's
login protection. No new tracking or recipient feedback attestation is needed.

UAB's [August 22, 2025 IT update](https://www.uab.edu/it/news/item/restricted-data-allowed-in-onedrive-and-sharepoint)
describes permitted institutional storage and email routes, prohibits forwarding
PHI to outside/personal addresses, and links the updated Data Protection Rule.
The [Data Protection Rule](https://www.uab.edu/it/home/policies/data-classification/data-protection-rule)
requires secure transmission, authorized recipients and Restricted sensitivity
labeling. A visible HTML banner is not a substitute for any required institutional
file label. The [Email Guidelines](https://www.uab.edu/it/home/policies/email-guidelines)
retain broader restrictive wording about uab.edu email. Confirm the applicable
route rather than treating the Outlook application name as approval for every
recipient, tenant, website or file location. This design does not certify the
app or any particular deployment for PHI.

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
8. Check OCR missing/conflicting rows, leading zeros, duplicate screenshots,
   overlapping source numbers in different batches, group identity conflicts
   and recipient-specific exports. Invalid or conflicting identifiers must not appear.
9. Verify the PHI banner persists while scrolling, survives title/theme changes
   and printing, and does not claim that the file has access protection.

## Sequence before the pilot

Review survey drafts and measurement choices; confirm roster, operators and
institutional determination; implement the two-title response; implement/test
the clinical-only HTML export; dry-run preparation and approved delivery;
record versions and launch the agreed 3-usual/4-tool sequence. Keep the survey
and operational log separate from the product. See [STUDY_PLAN.md](STUDY_PLAN.md).
