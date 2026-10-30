# October 30 request coverage

This records the items between NEW and END OF NEW UPDATES in the user's Compare
Revisions plan, plus the compact accession-copy request. The later Wednesday
parallel-work/credit notes are outside this change. Private screenshots and
identifiers are deliberately not included.

| Request | Implemented result | Verification / remaining limit |
| --- | --- | --- |
| Only the extractor's external progress display updates | v0.17 routes live phase/count changes to the progress window; launcher status stays steady and retains final results | 116 synthetic/native-control checks; real workstation trial remains |
| Recognize case/accession columns without an Accession header; remove manual selectors | Repeated row positions and two-letter accession patterns infer columns; numeric MRN-like columns are excluded; manual marking controls removed | Actual OCR headerless three-column fixture and ambiguous-column refusal; insufficient evidence requests a clearer crop |
| Paste screenshot directly below report text; no file picker | Focusable Paste screenshot here area, Ctrl+V/image paste and clipboard button | Real ClipboardEvent tests; successive screenshots/overlaps retained |
| Support XR, RF, MR, CT and OT | These and US work; other two-letter prefixes such as NM are preserved | Pure normalization/detection checks; no closed prefix whitelist |
| Export sometimes opens input site instead of review | Existing offline export retained; redirected/auth/normal-page responses now rejected before download using a parsed reader head marker | Fresh context, storage disabled, networking blocked; the user's later laptop tests also reported correct export. The initial workstation incident was not reproduced |
| OT read as 0T/07 | OCR-context correction to OT, plus O-to-zero only in numeric positions; unusual digit lengths flagged without changing existing digits | Pasted 46-row text check only for the latest example; authenticated image download unavailable, so no claim of image-level verification |
| Smaller copy action; full accession details only after expansion | Icon left of caret, 44-pixel hit area, tooltip and brief feedback; full group list after Summary/Text changes | Keyboard, no card expansion/resizing, footer copying, themes, mobile and offline checks |

## Delivery and launch

- Website source is ready for the existing two-file Cloud Run deployment;
  requirements and model credentials are unchanged. Live deployment is pending.
- PowerScribeReportExporter-v0.17.zip is in the existing Drive release folder,
  preserving old versions and sharing. No patient output is in that release.
- The revised study launch timeline is in STUDY_PLAN.md. Private Notion holds
  the resident briefing, source references and dated native tasks. No outreach
  or form invitations were sent.
- Generating both resident and attending titles in one response remains planned,
  as documented in REVIEW_EXPORT_PLAN.md. Current analysis still uses the
  selected role's title prompt. No new AI requests or grading changes here.
