# November 6, 2026 production and semantic review

## Scope and sources

Reviewed all 300 questions in the 30 level banks for November 6–15. Added
November 9–15 (210 questions); corrected seven existing November 6–8 items and
retained the other 83 existing items. No prepared date later than November 8
existed on fetched main (`7878e70`). No date before the run date was changed.
The next scheduled Friday is November 13; coverage ends Sunday, November 15.

Read the repository and Scripture Copier instructions, the full weekly workflow
including its October 7 correction, the app's loading and splitting code, the
schedule, validator, export contract, and quality checks. Read both complete
manuals (weeks 45 and 46), and every exact daily KJV verse allocation before
authoring. The manual supplies context; the assigned verses govern each item.
The optional NRSVue app translation does not change this run's KJV source contract;
the item about Daniel 3:25 explicitly names the KJV wording.

| Date | Exact assignment | Verses |
| --- | --- | ---: |
| November 6 | Ezekiel 34:28–31; 36:1–27 | 31 |
| November 7 | Ezekiel 36:28–38; 37:1–20 | 31 |
| November 8 | Ezekiel 37:21–28; 47:1–23 | 31 |
| November 9 | Daniel 1:1–21; 2:1–11 | 32 |
| November 10 | Daniel 2:12–43 | 32 |
| November 11 | Daniel 2:44–49; 3:1–26 | 32 |
| November 12 | Daniel 3:27–30; 4:1–28 | 32 |
| November 13 | Daniel 4:29–37; 5:1–23 | 32 |
| November 14 | Daniel 5:24–31; 6:1–24 | 32 |
| November 15 | Daniel 6:25–28; 7:1–28 | 32 |

Allocations concatenate scheduled chapters, then use quotient/remainder over
seven days, matching `loadWeek` and `validate.assignments`. In particular, the
November 11 furnace account ends at the summons out; the officials' inspection
belongs to November 12. November 13 stops before the writing's interpretation.

## Existing-content findings and corrections

| Date / level / item | Verified flaw | Correction |
| --- | --- | --- |
| Nov 6 / kid / 3 | Explanation described the expanded land address beyond its cited Ezekiel 36:1 | Narrowed explanation to the actual cited command to the mountains |
| Nov 6 / high-school / 7 | Key was a complete verbal clause while distractors were noun phrases | Made all four reasons parallel noun phrases of similar length |
| Nov 6 / expert / 8 | Only the key offered a restorative sequence; military/exile alternatives gave tone clues | Wrote competing restoration sequences and retained the actual gathering–cleansing–renewal–obedience order |
| Nov 7 / high-school / 10 | Only the key described a visible explanatory sign; alternatives changed the event category | Made every alternative a visible action with a different explanation procedure |
| Nov 8 / kid / 3 | Sacred dwelling competed with commercial/military objects | Replaced distractors with religious structures and places |
| Nov 8 / high-school / 3 | Only the key described a positive witness of sanctification | Offered plausible positive public witnesses; the text specifically names the enduring sanctuary |
| Nov 8 / expert / 3 | Only the key preserved a positive covenant relationship | Compared different favorable divine actions and their proposed public significance |

Other existing items were checked against their verses and retained. This includes
the distinction between reassembly and breath, the November 7 endpoint at 37:20,
the salt-marsh exception, Joseph's two portions, and the resident-foreigner
inheritance requirement of children among Israel and allotment in the resident tribe.

## New-content source and adversarial review

For every item, checked the stem with each option, one best answer, why each
distractor fails the actual text, explanation claims, and exact source range.
Distractors were written for each stem; no shared answer pool or rotation of
other items' correct answers was used. Each level was then read as a ten-item set
without relying on passage knowledge, checking grammar, category, word echoes,
length, tone, sophistication, absolutes, repeated choices, positions, and clues
from other questions. Content signatures were written only after these reviews;
subsequent revisions were re-reviewed and re-signed before export and validation.

Concrete draft corrections from those passes:

- Replaced mismatched court-life alternatives with parallel spiritual skills,
  worship responses, restoration sequences, and royal actions. Removed a modern
  election distractor and alternatives that implied impossible reassignment of
  a captive's actual birthplace.
- Removed the threatening-beast item in which only the key sounded threatening;
  every new alternative now describes threatening imagery. Replaced a court-scene
  stem that effectively supplied “judgment” with a close comparison of scene details.
- Replaced an origin-of-defeat item whose other choices were not stones. All four
  choices now distinguish a stone's origin, agency, and point of impact.
- Removed shortest-key clusters in November 13–14 and unequal lengths in the
  queen's recommendation item. Shortened or rephrased alternatives by meaning,
  without padding correct answers. No bank has more than three uniquely shortest
  or two uniquely longest keys.
- Replaced duplicate expert testing of unconditional furnace refusal, mixed-kingdom
  cohesion, stump restoration, and final horn duration with distinct points:
  the certainty statement, material/kingdom mapping, the animals' changing place,
  and the narrative's dated setting. Reviewed cross-level targets too, replacing
  a third retelling of reward refusal with the extent of royal discretion.
- Widened the furnace-language comparison to Daniel 3:15–26 and the opening-boast
  comparison to 4:29–37. Widened the tree image/identity item to 4:10–22. All cited
  claims now lie in the source ranges and exact daily allocation.

Source distinctions intentionally retained: divine gifts rather than personal
superiority; the dream disclosure as a credibility test without insisting the
king forgot it; deliverance-independent loyalty in Daniel 3:17–18; the KJV king's
reported description of the fourth figure; the already-disclosed dream in chapter
4; the conditional possibility of prolonged tranquility in 4:27; Belshazzar's
culpability despite knowing the earlier lesson; habitual prayer despite the decree;
the king's narrated violent reprisals rather than a recommended behavior; the
other beasts' prolonged lives after loss of dominion; and Daniel remaining troubled
even after receiving interpretation. No modern identification of the beasts or
calculation of the horn's period is asserted.

## Verification

- Canonical `export_quizduel.py --write` checked every date. Relative to main,
  21 exports are new and seven existing exports refreshed: 28 total, in ten daily
  JSON files. The subsequent no-write run reports zero stale files.
- `python test_quality.py`: all nine regression tests pass.
- `python export_quizduel.py`: 150 exports across 50 dates, zero updates.
- `python validate.py`: 50 dates, 1,500 questions, exact daily source references,
  review hashes, and 150 exports pass.
- Full browser suite covers all ten reviewed dates at 390px and 1280px, exact
  level objects, copy before navigation, clipboard denial, blocked popup links,
  legacy fallback, all 300 reviewed questions through mobile completion, early
  exit, and reading controls. Focused final rerun covers November 11–14 after
  final set refinements. Mobile and desktop screenshots inspected.
- `git diff --check` and JavaScript syntax checks pass. The commit is scoped to
  the ten daily banks and this record; original checkout changes are preserved.
- Publication gate: wait for successful Pages, compare live HTML/JS/CSS with Git
  bytes, compare all ten JSON objects (including thirty exports) at bare and app
  query URLs, repeat the full browser suite on live Pages, and separately test
  all three buttons against the real, unintercepted QuizDuel destination.

Actual automation configuration read from its local `automation.toml`:
`gpt-6.1-sol`, `high` reasoning effort. Active Friday 21:00 schedule unchanged.

## Final bank measures

Stored positions are one-based, in authored question order. Each row has an
irregular 3/3/2/2 distribution. Length checks count normalized words and count a
key as shortest/longest only when it is uniquely so. These are mechanical
supplements to the semantic review above.

| Date | Level | Stored keys | Uniquely longest keys | Uniquely shortest keys |
| --- | --- | --- | ---: | ---: |
| 2026-11-06 | kid | 1211234324 | 0 | 3 |
| 2026-11-06 | high-school | 2214321431 | 1 | 3 |
| 2026-11-06 | expert | 4113432212 | 0 | 1 |
| 2026-11-07 | kid | 1242143321 | 1 | 1 |
| 2026-11-07 | high-school | 1343241212 | 0 | 3 |
| 2026-11-07 | expert | 2111342432 | 1 | 2 |
| 2026-11-08 | kid | 2423142131 | 1 | 2 |
| 2026-11-08 | high-school | 3142312214 | 0 | 1 |
| 2026-11-08 | expert | 3431241221 | 0 | 3 |
| 2026-11-09 | kid | 2421131234 | 0 | 0 |
| 2026-11-09 | high-school | 1311422423 | 1 | 2 |
| 2026-11-09 | expert | 3423112421 | 0 | 1 |
| 2026-11-10 | kid | 1433412221 | 1 | 0 |
| 2026-11-10 | high-school | 1231122434 | 1 | 3 |
| 2026-11-10 | expert | 4123412123 | 0 | 2 |
| 2026-11-11 | kid | 3421312214 | 2 | 2 |
| 2026-11-11 | high-school | 3134241212 | 1 | 3 |
| 2026-11-11 | expert | 1124123423 | 0 | 3 |
| 2026-11-12 | kid | 2314212134 | 0 | 1 |
| 2026-11-12 | high-school | 1312124432 | 2 | 2 |
| 2026-11-12 | expert | 3134122124 | 0 | 0 |
| 2026-11-13 | kid | 2113432214 | 0 | 2 |
| 2026-11-13 | high-school | 4311122423 | 0 | 2 |
| 2026-11-13 | expert | 1322114423 | 0 | 3 |
| 2026-11-14 | kid | 4122213314 | 2 | 0 |
| 2026-11-14 | high-school | 1124213324 | 0 | 3 |
| 2026-11-14 | expert | 2413234211 | 0 | 1 |
| 2026-11-15 | kid | 1331224214 | 1 | 0 |
| 2026-11-15 | high-school | 2321341124 | 1 | 3 |
| 2026-11-15 | expert | 1224421313 | 0 | 2 |
