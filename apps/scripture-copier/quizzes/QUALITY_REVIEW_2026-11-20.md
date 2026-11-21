# November 20, 2026 — current/future quiz review

Scope: November 20–29, through the Sunday after the next configured Friday run (November 27). Fetched main contained November 20–22 and no later prepared banks. Added November 23–29: 210 questions. Reviewed all 300 questions in 30 ten-item banks; corrected seven existing items and retained the other 83. No past quizzes or unrelated working-tree changes were included.

## Sources and boundaries

Read both complete local manuals (`manual/2026/week-47.txt` and `week-48.txt`) and all ten exact daily KJV slices before authoring. Followed `loadWeek`'s chapter concatenation and quotient/remainder split. Manual context did not enlarge the daily assignment.

| Date | Assigned verses | Count | Review |
| --- | --- | ---: | --- |
| November 20 | Hosea 13:4–14:9; Joel 1:1–10 | 32 | 30 existing, 3 corrected |
| November 21 | Joel 1:11–2:22 | 32 | 30 existing, 3 corrected |
| November 22 | Joel 2:23–3:21 | 31 | 30 existing, 1 corrected |
| November 23 | Amos 1:1–2:16 | 31 | 30 new |
| November 24 | Amos 3:1–5:3 | 31 | 30 new |
| November 25 | Amos 5:4–6:7 | 31 | 30 new |
| November 26 | Amos 6:8–8:7 | 31 | 30 new |
| November 27 | Amos 8:8–9:15; Obadiah 1:1–9 | 31 | 30 new |
| November 28 | Obadiah 1:10–21; Jonah 1:1–2:1 | 30 | 30 new |
| November 29 | Jonah 2:2–4:11 | 30 | 30 new |

## Verified existing flaws corrected

- November 20 expert 4: the cavalry-supplied offering was implausible and differed from the other response mechanisms. Replaced the choices with parallel forms of offering; the lips remain the textual answer.
- November 20 expert 6: renewed versus renounced reliance and punitive versus healing outcomes allowed elimination by tone. Compared plausible affirmative responses to the confession instead.
- November 20 expert 9: a multigenerational-command stem practically supplied transmitted memory, while unrelated taxes, coronation, and inheritance distracted from the disaster. Now compares possible accounts of its novelty and transmission.
- November 21 high-school 9: “private family occasions” singled out bride and bridegroom. Removed that cue and compared groups explicitly included in the assembly.
- November 21 expert 2: the former options made a common crisis the logical answer to a linking question. Now compares concrete sequences of seed, storage, and livestock conditions, with the source determining the answer.
- November 21 expert 7: foreign-worship approval and military control did not plausibly compete with a hoped-for blessing. All choices now describe plausible provisions for recovery; only the offering provision is stated in verse 14.
- November 22 high-school 9: the former wrong alternatives abandoned God's dwelling or elevated Edom over Judah, allowing a theology/tone guess. Replaced them with parallel cosmic conditions and divine actions.

## Semantic review of new banks

For every question, checked the key, each distractor, explanation, and citation against its assigned verses. Read the stem with all four choices for grammar and category. Then reviewed without relying on passage knowledge for length, tone, repeated stem words, qualifications, position, and logic-only clues. Compared every complete ten-item bank for repeated targets, shared full choices, and cross-item cues. Signed the content hashes only after those passes and re-reviewed revisions before signing.

Concrete draft findings and revisions:

- Removed the lone adverse outcome among favorable judgment outcomes, and the lone hateful response among rewards. Adverse findings now compete with plausible adverse findings.
- Replaced physical goods competing with abstract wrongdoing in the palace item with four descriptions of the goods' origins. Compared righteousness with other virtues rather than sacrifices, music, and riches.
- Rewrote the kid question answerable by ordinary logic about walking together to ask which everyday image Amos actually uses.
- Removed “sellers” pointing to selling, “reluctance” pointing to rowing ashore, “broadening” pointing to the only universal-scope option, and “repair” pointing to the only restoration option.
- Replaced the dishonest-measure question whose key followed from arithmetic with a neutral question about the two market practices Amos names.
- Replaced unrelated political or commercial alternatives in prophetic-prayer and thanksgiving items with comparable devotional actions. Removed modern voting and arbitrary king-name recall.
- Corrected ambiguous wording in the fire image: Jacob is fire, Joseph flame, and Esau stubble. It no longer says merely that two houses “burn,” which could mean being consumed.
- Kept the Creator description close to explicit acts rather than assigning the ambiguous pronoun in Amos 4:13 to human rather than divine thought.
- Removed shortest-key clusters and shortened naturally worded choices instead of adding filler. Every final bank has at most three uniquely shortest and two uniquely longest keys, and all option spreads satisfy the gate.

Source distinctions retained: Moab's offense concerns Edom's dead king; covenant recognition leads to accountability; clean teeth means lack of bread; the invitation to Bethel and Gilgal is ironic; hoped-for grace in Amos 5:15 remains qualified. The first two visions end in relenting, whereas the plumbline and summer-fruit visions repeat the limit on passing by. Amaziah's report names Jeroboam's death while the preceding oracle names Jeroboam's house. Historical agency extends beyond Israel; the survival of Jacob does not exempt complacent sinners. Obadiah's condemnation includes complicity, plundering, and intercepting escapees; the manual's temple-work application is not presented as an explicit act in the verse. November 28 stops at Jonah praying in the fish; release and the second commission belong to November 29. The sailors' failed rowing and bloodguilt plea precede casting Jonah overboard. Nineveh's changed works, not merely clothing or ritual, precede relenting. Jonah knows God's mercy yet resents its exercise; the final unanswered question includes cattle and does not prescribe a speculative identification of the city's people.

Each level has ten distinct items, item-specific distractors, no repeated normalized full option within the bank, and irregular 3/3/2/2 keys. The UI still shuffles choices. No shared answer pool or rotation of another item's answer was used. Each daily `qualityReview` binds all six required checks to the actual content.

## Validation and publication

- Canonical exporter checked all 192 exports across 64 dates: 21 new and four refreshed existing level exports, in ten changed daily JSON files.
- `python test_quality.py`: all nine regression tests passed.
- `python export_quizduel.py`: zero stale files.
- `python validate.py`: 64 dates, 1,920 questions, exact daily references, review signatures, and 192 exports passed.
- JavaScript syntax and `git diff --check` passed.
- Local `test_ui.cjs` passed for all ten dates at 390px and 1280px: exact per-level clipboard objects, successful-copy-before-navigation, clipboard denial, popup blocking with usable link, legacy copy fallback, all 300 reviewed questions through mobile completion, early exit, and reading controls. Both screenshots were visually inspected without overflow.
- Deployment and final live verification evidence are recorded in the run report and automation memory after publication; this file does not claim deployment success before it occurs.

Actual scheduled configuration read from `automation.toml`: `gpt-6.1-sol`, `high` reasoning effort; Friday 21:00 America/Chicago, unchanged.
