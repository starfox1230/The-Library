# November 13, 2026 — current/future quiz review

Scope: November 13–22, through Sunday after the next configured Friday run (November 20). Fetched main contained prepared files through November 15 and no later files. Added November 16–22: 210 questions. Reviewed all 300 questions in 30 ten-item banks. Corrected eight existing items; retained the other 82. Past quizzes and unrelated work were preserved.

## Sources and assignment boundaries

Read both complete manuals (`manual/2026/week-46.txt` and `week-47.txt`) and every exact KJV daily slice from the app's source JSON before authoring. Applied `loadWeek`'s concatenation order and quotient/remainder allocation. Manual context did not expand the daily reading.

| Date | Assigned slice | Verses | Review |
| --- | --- | ---: | --- |
| November 13 | Daniel 4:29–5:23 | 32 | 30 existing items; 2 corrected |
| November 14 | Daniel 5:24–6:24 | 32 | 30 existing items; 1 corrected |
| November 15 | Daniel 6:25–7:28 | 32 | 30 existing items; 5 corrected |
| November 16 | Hosea 1:1–2:21 | 32 | 30 new items |
| November 17 | Hosea 2:22–5:6 | 32 | 30 new items |
| November 18 | Hosea 5:7–6:11; 10:1–12 | 32 | 30 new items |
| November 19 | Hosea 10:13–13:3 | 32 | 30 new items |
| November 20 | Hosea 13:4–14:9; Joel 1:1–10 | 32 | 30 new items |
| November 21 | Joel 1:11–2:22 | 32 | 30 new items |
| November 22 | Joel 2:23–3:21 | 31 | 30 new items |

## Existing content corrections

- November 13 kid 4: replaced physical returns (soldiers, treasures, children) competing with the return of understanding with parallel mental responses.
- November 13 expert 9: replaced distractors that gave manufactured gods obviously implausible powers and limited the living God. All alternatives now contrast an idol's incapacity with a proposed divine act; only the keyed pair is stated in Daniel 5:23.
- November 14 kid 2: removed the lone unfavorable judgment among three flattering descriptions. All choices now describe adverse findings, while only lacking matches Tekel.
- November 15 kid 3: replaced unwritten/erased alternatives with plausible ways of handling a dream account; only Daniel's writing matches the source.
- November 15 kid 9: replaced the river option with another human leadership group so kings compete with comparable agents.
- November 15 high-school 1: replaced restricted/temporary/hidden-sovereignty distractors with parallel affirmative proclamations. Rescue and signs, rather than tone, distinguish the answer.
- November 15 high-school 7: replaced destructive or unrelated reactions with plausible ways of seeking an interpretation.
- November 15 expert 7: removed the beasts electing a ruler; all alternatives now describe possible political endings to the horn's dominance, while judgment and the saints' possession remain the textual endpoint.

## New-bank source and adversarial review

For every item, read its stem with each option, checked the keyed claim and explanation against its cited daily verses, and checked why each alternative is wrong in that passage. Then attempted to answer without passage knowledge, inspecting grammar, category, length, tone, stem echoes, qualifications, and position. Compared each complete ten-item bank for duplicate targets, repeated choices, and cross-item clues. These semantic passes preceded the final content hashes.

Concrete revisions during review:

- Replaced the lone fleeting dew image among strong plants with four fleeting images; replaced the lone threatening bear among harmless animals with four threatening animal images.
- Replaced missing moral qualities competing with crops, personnel, and weapons with comparable moral qualities. Replaced mercy/judgment competing with wealth and weapons with other virtues.
- Removed a wrong-with-balances stem whose dishonest answer could be selected from everyday meaning; tested the merchant's stated love of oppression instead.
- Removed stems supplying the intended contrast: restored allegiance, lack of information, avoidance of a guaranteed outcome, and bodily need plus public disgrace.
- Removed the general-knowledge question about the common property of named cloud/dew/chaff/smoke; the revised item requires knowing the consequence emphasized by the source's unnamed four-image series.
- Made judgments compete with other judgments, restorative promises with other restorative promises, and forms of seeking interpretation with other forms of seeking interpretation. Removed silly colors for cosmic signs and ordinary celebration options for the threatening day.
- Corrected an ambiguous draft description of Hosea 14:8's speaker so fruitfulness is explicitly attributed to the Lord, rather than potentially to Ephraim.
- Removed the November 20 high-school shortest-answer cluster, then reviewed length ranks across all banks. Final banks have at most three uniquely shortest keys and two uniquely longest keys.

Retained source distinctions: November 13 ends before the writing's interpretation; Daniel's prayer continues his established practice; the narrated royal reprisal is not prescribed conduct; the other beasts lose dominion but live for a season; Daniel remains troubled after interpretation. Hosea's judgments remain alongside restoration, not replaced by unconditional prosperity. Hosea 11:5 and 11:11 retain their differing statements about Egypt. Hosea 13:14 is not expanded into a speculative universal-salvation claim. Joel's possible blessing in 2:14 remains a hope, the Spirit includes servants and handmaids, the tool transformation in 3:10 goes toward weapons, and the sale/reprisal and innocent bloodshed remain explicit.

Each bank has ten distinct items, four item-specific choices per item, unique normalized full option texts within the bank, similar option lengths, and irregular 3/3/2/2 stored keys. No common answer pool or rotation of other items' correct answers was used. The `qualityReview` hashes bind the actual reviewed content to all six required checks.

## Validation and publication gates

- Canonical exporter: 171 exports across 57 dates; 21 new exports and six refreshed existing level exports, in ten changed daily files. A fresh check reports zero stale files.
- `python test_quality.py`: all nine publication-gate regression tests pass.
- `python export_quizduel.py`: 171 current exports; zero updates needed.
- `python validate.py`: 57 dates, 1,710 questions, exact daily references, review hashes, and 171 exports pass.
- Local `test_ui.cjs` passed all ten dates at 390px and 1280px: exact per-level copies, copy-before-navigation, denial, blocked popups, legacy fallback, all 300 reviewed questions through completion on mobile, early exit, and reading controls. Both screenshots were visually inspected with no overflow.
- `git diff --check` and JavaScript syntax checks passed. Publication and live verification evidence are recorded in the scheduled run's report and memory after deployment; this file does not claim a deployment before it occurs.

Actual scheduled configuration read from `automation.toml`: `gpt-6.1-sol`, `high` reasoning effort; Friday 21:00 America/Chicago.
