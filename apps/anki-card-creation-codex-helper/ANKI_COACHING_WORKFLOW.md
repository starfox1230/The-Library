# Anki Coaching Workflow

This is the canonical nightly workflow for Study OS Anki coaching. It supplements, and does not replace, `CARD_STYLE_GUIDE.md`, `VISUAL_STUDY_AND_ANKI_SPEC.md`, and `APKG_PACKAGING.md`.

## Purpose

At 9 p.m. local time, create one concise coaching report that helps Sterling understand and improve difficult Anki material. The report is displayed inside the expandable **Anki Coaching** panel on the Study OS Today page.

## Sources

1. **Notion Radiology Notes** whose `Anki Card` status is `Needed`.
2. **Anki Speed Streak — Review Later** entries exported in `C:\Users\sterl\OneDrive\Study OS Private\anki-coaching\latest.json`.
3. **Anki Pocket Knife — Study Repair** entries in that same snapshot.

Treat a card that appears in both Review Later and Study Repair as one item. Preserve its source labels and reasons, but do not repeat the teaching.

Keep the source counts independent from deduplication. `sourceCounts.reviewLater` and `sourceCounts.studyRepair` report the eligible rows in their respective cohorts, while the report may also record the smaller count of unique cards after overlap. Never lower either source count merely because one card appears in both places.

### Review Later date scope

The Review Later export is a cumulative pool. **Do not coach the entire exported pool.** For a nightly report, include only Review Later entries whose `addedAt` timestamp falls on the report's `studyDate` after conversion to `America/Chicago`. This source means cards placed into or seen in Review Later during that local study day, not every card still present in Review Later.

- Parse every `addedAt` value as an absolute timestamp before converting it to `America/Chicago`; never compare the raw UTC date string directly.
- Exclude older Review Later entries even if they remain in `latest.json`.
- If the same card was added more than once that day, keep its most recent entry.
- If a same-day Review Later card also appears in Study Repair, coach it once and retain both source labels.
- `sourceCounts.reviewLater` must report the filtered same-day count, not the size of the cumulative export.
- Record both the cumulative pool size and filtered local-day count in the run ledger so an unexpectedly broad cohort is visible during verification.

## Coaching existing Anki cards

For each selected card:

- Read the complete note, including all fields, tags, deck, note type, and available images.
- Teach the surrounding concept needed to make the card memorable, not merely restate its answer.
- Explain why the card is difficult or fragile when the available review history supports that inference.
- Flag factual errors, excessive dogmatism, ambiguity, overloaded prompts, or answerable-by-clue wording.
- Suggest a specific edit when an edit would improve the card.
- Recommend a new card only when an important, testable concept is genuinely missing. Do not duplicate the existing card.

## Notion notes and new card candidates

The ordinary nightly Notion cohort is limited to **recent entries**. Define recent as a `Created time` whose date, after conversion to `America/Chicago`, is the report's local study date or one of the preceding six local calendar dates. Select only entries in that seven-date window whose `Anki Card` property is exactly `Needed`. Use an exact database query and pagination or an aggregate count; never treat a 100-row API page limit as the cohort size.

Once a Notion page has been admitted to a nightly batch, retain its stable page id in the run ledger and retry that unresolved page on later runs until it succeeds or the user changes its status, even if its `Created time` later ages beyond the seven-date window. This retry rule prevents a transient generation, media, or Notion-write failure from silently abandoning an otherwise eligible recent entry. Older `Needed` pages that were never admitted remain outside the ordinary nightly cohort and are not an implicit backlog assignment.

For every selected Notion item, fetch the complete page content and create card candidates according to the canonical card and visual-card instructions. Include the relevant source-page screenshot in Extra when the source is a textbook or auto-generated textbook quiz. Publish these candidates to the Study OS **Cards Reviewer**; do not substitute a prose description of the queue in the Anki Coaching panel.

The Cards Reviewer database enforces uniqueness on the pair `(sourceType, sourceId)`. When one Notion page yields multiple candidates, the raw Notion page id is not a valid shared `sourceId`. Give every candidate a stable compound source id such as `<page-id>:candidate:01`, `<page-id>:candidate:02`, and so on, while retaining the raw page id separately in the ledger as the upstream parent. Candidate ids must also be stable across reruns. An accepted upsert response is not completion: compare the full expected candidate-id set and expected count with destination readback. A silent uniqueness conflict that inserts only one card from a multi-card page is a failed page, not partial success.

If a Notion page body is blank but its title itself contains a complete, unambiguous medical fact or reporting rule, that title may serve as source content. If the title is not independently sufficient, leave the page `Needed` and record it as ambiguous rather than inventing content.

After every candidate attributable to that Notion entry and all required media have been generated, uploaded, and GET-verified, update that same Notion page's `Anki Card` property from `Needed` to `Created`. Read the page back and verify that the property now equals `Created`. Only then record the Notion entry as processed in the coaching report. If generation, media upload, site verification, or the Notion update/readback fails, leave the property as `Needed` so a later nightly run can retry it. Never change an ambiguous or skipped entry to `Created`.

The actual editable cards belong in the Study OS **Cards Reviewer**. The coaching report may briefly identify which Notion pages produced cards or remain blocked, but it must not present pipeline status as teaching content.

## Report format

Use these sections, omitting empty sections:

1. `Tonight's priorities`
2. `Review Later coaching`
3. `Study Repair coaching`
4. `Notion notes ready for cards`
5. `Suggested card edits`
6. `New card candidates`

Keep the report easy to copy as plain text. State source and card/note identifiers unobtrusively so recommendations remain traceable.

**Anki Coaching is a teaching artifact.** Its primary content must teach and contextualize same-day Review Later cards and Study Repair cards. A successful upload, queue count, card-generation summary, or blocker report does not by itself satisfy coaching. When no eligible Anki snapshot content is available, publish an explicit unavailable/partial state rather than replacing the teaching report with operational status and calling it complete.

Create and upload one JSON object:

```json
{
  "id": "anki-coaching-YYYY-MM-DD",
  "studyDate": "YYYY-MM-DD",
  "title": "Anki Coaching",
  "summary": "One-sentence nightly overview",
  "contentText": "Complete plain-text coaching report",
  "sourceCounts": {
    "notion": 0,
    "reviewLater": 0,
    "studyRepair": 0
  },
  "sourceRefs": [],
  "generatedAt": "ISO-8601 timestamp"
}
```

Upload it with `study-os-site/scripts/upload-anki-coaching.mjs`, then GET `/api/state` and verify the stable report ID is present. Re-running the same date updates that report instead of creating a duplicate.

Before declaring coaching complete, verify that `contentText` contains substantive teaching for every eligible unique card or an explicit card-specific limitation. Counts, identifiers, and operational status alone do not satisfy this check.

## Failure behavior

If the Anki snapshot is missing or stale, explicitly label those sources unavailable and continue with Notion. If Notion is unavailable, continue with the Anki snapshot. Never invent source content, silently clear prior results, or fail the rest of the Study OS nightly packet solely because one coaching source is unavailable.
