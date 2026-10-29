# Nearby identical report pairs: implementation direction

October 29, 2026. Records Sterling's requested workflow and the recommended
next website change. This is a plan; automatic grouping is not implemented or
deployed by this documentation change.

## What the current code does

- Extractor v0.15 captures whole resident and attending reports by default.
  Its optional legacy **Findings and below only** setting must be off to retain
  indication, technique, comparison and other captured context. Every source
  row remains in the saved export under its original case number.
- Website `prepare_cases` currently creates a separate review entry for every
  parsed source row, even if both complete reports are identical.
- `summarize_case` supplies both full reports plus parsed eligible sections to
  the model. The model request does not include the app's case-number metadata.
- The prompt and clinical diff restrict assessed edits to recognized Findings,
  Impression/Conclusion and combined sections. Context-only edits are excluded.
  A clinically meaningful interval change described in Findings still matters;
  ignoring edits to the standalone Comparison section does not exclude it.
- Section scoping recognizes nonclinical headings and removes two known
  attending attestation lines. Unrecognized or unlabeled attestation prose is not
  guaranteed to be excluded by the parser; retain scope regression coverage.

These statements describe the checked-in source. Correspondence with the live
Cloud Run deployment has not been independently verified.

## Proposed grouping contract

1. Group on website import, before scheduling model requests. Keep the
   extractor's original per-row archive and comparison input intact.
2. Require complete pairs and exact equality of **both** full input strings:
   resident A equals resident B, and attending A equals attending B. Resident
   and attending need not equal each other. Matching Findings alone, matching
   only one side, or matching AI titles is insufficient.
3. Use only existing transport normalization: CRLF/CR become LF, and outer
   framing whitespace is trimmed by import. Preserve internal whitespace,
   capitalization, numbers, punctuation and every context/attestation line.
   Do not use the attestation-cleaned or clinical-only text as the identity key.
4. For a normal ascending extractor sequence, a matching entry can join the
   most recent compatible group only when its source number is 1-3 greater
   than that group's last matching member. This means at most two intervening
   source rows. Use original source numbers, not positions after incomplete
   rows, filtering or grouping have been removed. Keep nonascending inputs
   separate rather than guessing a reconstruction of their acquisition order.
5. Apply that distance to the **previous matching member**, not the first.
   Thus six consecutive identical pairs can form one group. Matching members
   at 68, 71 and 74 can chain; matching members only at 68 and 72 cannot.
   This chain behavior is deliberate and should be covered by tests.
6. Preserve every source member and original pair. Display consecutive members
   as **Cases 68-69** (typographic range dash in the UI), and nonconsecutive
   members explicitly, such as **Cases 68, 71**. Case 70 stays Case 70.
   Order groups by first appearance; never renumber source cases.
7. Analyze one representative pair per group using the current instructions
   and model configuration. Keep request IDs and membership mapping in app
   code. The model must not decide grouping or reconstruct case labels.
8. Label the result descriptively as an **identical full-report group**, not
   confirmed shared patient identity or a proven list of linked exam types.
   Fully identical nearby normal templates can still be separate examinations.
   A way to separate an incorrectly grouped entry should be available without
   losing the source labels or existing result; exact UI placement is open.
9. Retain separate totals for source rows and review entries. Revision counts
   belong to the grouped review entry and must not silently multiply by the
   number of source rows. QI/research denominators need explicit units.

## Implementation and acceptance

- Add deterministic grouping between `parse_cases` and `_base_case` inside
  `prepare_cases`; retain original member records in the derived group.
- Reuse the existing `source_numbers`, `format_case_numbers`, grouped header
  and member-note support, updating the note to explain the proximity rule.
- Replace the current tests requiring all identical pairs to remain separate.
  Cover adjacent matches, gaps of 2/3/4, six-member and spaced chains,
  different indications/comparisons/attestations on either side, one-sided
  matches, nonascending input, incomplete rows, and unchanged source labels.
- Verify a group schedules one mocked model request, two groups schedule two,
  grouped source search works, and counts, retries and sorting preserve members.
- Existing full-report context and clinical-only diff/prompt/evidence tests
  must still pass. Explicitly check trailing signatures and attestations.
- Use synthetic reports and mocked providers for development. The current
  prompt already has the required context-versus-assessment distinction;
  grouping does not require a new AI identity-classification request.
- Deliver replacement website source and clearly distinguish local checks
  from live deployment. No new extractor release is needed for this feature
  when full-report capture is enabled.
