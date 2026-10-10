# Come Follow Me content review — October 10, 2026

Reviewed all 270 items in the 27 ten-item level banks for October 10–18, including the two already published dates. Added October 12–18 (210 questions) and corrected 54 of the 60 existing October 10–11 items. The other six items were retained. Dates before October 10 were not edited.

## Sources and coverage

Read the app's KJV Isaiah JSON and both complete manuals (`manual/2026/week-41.txt` and `week-42.txt`) before authoring. The manual's teaching themes supply context; each item's reference and explanatory claims remain within the assigned daily verses. Daily assignments were computed by the app's chapter concatenation and quotient/remainder split and independently checked by `validate.py`.

| Date | Exact assignment | Questions reviewed | Level exports created/refreshed |
| --- | --- | ---: | ---: |
| October 10 | Isaiah 55:13–57:4 | 30 | 3 |
| October 11 | Isaiah 57:5–21 | 30 | 3 |
| October 12 | Isaiah 58:1–59:9 | 30 | 3 |
| October 13 | Isaiah 59:10–60:11 | 30 | 3 |
| October 14 | Isaiah 60:12–62:1 | 30 | 3 |
| October 15 | Isaiah 62:2–63:12 | 30 | 3 |
| October 16 | Isaiah 63:13–65:4 | 30 | 3 |
| October 17 | Isaiah 65:5–66:2 | 30 | 3 |
| October 18 | Isaiah 66:3–24 | 30 | 3 |

The next configured Friday run is October 16; coverage reaches the following Sunday, October 18. No additional future banks existed on fetched main.

## Semantic review findings and corrections

Each item received a source pass: checked the key against the cited verses, considered whether another option could be defended, checked every distractor's conflicting detail or unsupported interpretation, and checked the explanation. Then each stem was read with each option without relying on passage knowledge, checking grammar, conceptual category, length, valence, repeated wording, and answer positions. Each ten-item set was compared for duplication and answers supplied by other stems. Mechanical checks were run after these passes; signatures were attached only to the reviewed content.

- **October 10:** Replaced unrelated or tone-cued kid choices with competing practices, fears, locations, motives, or images. The Sabbath item now asks which habit is named in the verse, with other plausible religious habits as distractors. Corrected the high-school and expert options that invoked unrelated farming, ritual replacement, or absurd leadership interpretations. Distinguished the scope of self-interest, the drinking indictment, and the rebuke of mockers rather than repeatedly testing failed vigilance. All original item IDs and stored keys remain stable.
- **October 11:** Removed birthday/farming trivia, crowded mountains, and rivers stopping downhill. Alternatives now concern plausible religious duties, competing destruction images, inheritance locations, forms of divine care, and reasons for restraint. Corrected higher-level distractors about divine ignorance, disappearance of every soul, abandoned transcendence, or impossible uses of the sea metaphor. Near/far peace is distinguished from the closing ethical warning; neither geography nor literal weather explains that warning.
- **October 12:** Revised a kid stem that made drought point too directly to the only watery option; all its options are now plausible watered landscapes. Replaced negative-tone cues in the fasting bank with competing conduct and religious practices. Kept outward affliction, relief of burdens, answered prayer, and restoration as different testing points. Divine ability is contrasted with moral separation without inventing God's dependence on offerings or rulers.
- **October 13:** Removed a light/shine echo from a kid stem and simplified an expert item to the actual noonday circumstance. Distinguished truth's collapse, the missing intercessor, judgment imagery, the generations covenant, and gathering. The altar item now competes with other plausible ritual uses of flocks, rather than non-worship uses revealed as wrong by the stem.
- **October 14:** Separated lasting inheritance from the later planting/glory question so the set does not test the same fact twice. Made the robbery item's alternatives other injustices instead of three innocent practices. The restoration questions distinguish material improvement from civic peace, divine light from ordinary cycles, and comfort from rebuilding. Recognition of the Savior and Redeemer competes with other plausible divine titles.
- **October 15:** Removed a rescue/redeemed synonym giveaway and the obvious road/stones elimination cue. The highway item now asks about the raised standard. The marriage item tests delighted attachment rather than repeating a stem verb in the key. The red-garment and winepress questions stay with the assigned judgment imagery; the memory of affliction stays with compassionate redemption. Spirit-related options compete on timing and role rather than suggesting moral obligations disappear.
- **October 16:** Removed God-as-uncle distractors and a reaching/spread-hands giveaway. Titles compete with titles, postures with postures, and pleas with pleas. Replaced distractors about God's equals, rivals, creditors, technical mountain-melting, or a fire-based calendar with plausible alternative readings of the lament. The confession is described as this people's confession; it is not expanded into a claim that righteous conduct is always worthless. The father/potter appeal rests on divine handiwork, not asserted innocence.
- **October 17:** Preserved the difficult wording of Isaiah 65:20: longevity and absence of weeping do not erase its explicit mention of death. Differentiated concrete kid facts, high-school relationships, and expert synthesis. The expert hearing item connects blessed labor/descendants with ready access to God; the expert animal item analyzes the lion's changed nourishment rather than rewording the lower-level peace question. Removed repeated shortest-answer cues by shortening distractors naturally.
- **October 18:** Replaced an impossible moving-city distractor with other plausible forms of national renewal. Removed a gathering/glory stem clue to the following proclamation item. The birth question does not supply divine completion in its stem. Reviewed maternal consolation, outward proclamation, sacred offering, priests/Levites, enduring identity, and recurring worship as separate points. The broad worship promise remains beside the final warning about transgression. Replaced a clustered expert key sequence with an irregular balanced order.

No shared answer pool was used. Each item's three distractors were written for its stem, and no normalized full option text repeats within a level's ten questions. All 27 level banks use exactly 3/3/2/2 stored keys, with irregular sequences. No keyed option is uniquely longest or shortest in more than four items; the final review also reduced several technically permitted four-item shortest patterns. The UI shuffles these stored choices.

### Existing items changed

Numbers below are the existing authored order, not newly assigned IDs.

| Date / level | Item numbers corrected |
| --- | --- |
| October 10 / kid | 2, 3, 4, 5, 7, 8, 9, 10 |
| October 10 / high-school | 1, 2, 3, 4, 5, 6, 7, 9, 10 |
| October 10 / expert | 1, 2, 4, 5, 6, 7, 8, 9, 10 |
| October 11 / kid | 2, 3, 4, 5, 6, 7, 8, 9, 10 |
| October 11 / high-school | 2, 3, 4, 5, 6, 7, 8, 9, 10 |
| October 11 / expert | 1–10 |

## Publication verification

- `export_quizduel.py --write`: checked 66 exports over 22 dates; refreshed or added nine files, representing 27 level exports (21 new, six corrected).
- `test_quality.py`: all nine regression tests passed.
- `export_quizduel.py` without `--write`: 66 exports checked; no stale exports.
- `validate.py`: 22 dates, 660 questions, exact daily references, content-bound reviews, and 66 exports passed.
- `node --check test_ui.cjs` and `git diff --check`: passed.
- The browser suite accepts `CFM_TEST_DATES` so each weekly run can exercise its actual reviewed dates on mobile and desktop, rather than retaining a fixed October 7–11 sample.
- Local browser suite passed for October 10–18 at 390 px and 1280 px: all three exports per date matched the corresponding local object, successful copying preceded QuizDuel navigation, clipboard denial closed the reserved blank tab, popup blocking offered a working link, and the legacy copy fallback preserved the JSON. All 270 reviewed questions completed on mobile; reading controls, early exit, and duplicate-tap handling passed. QuizDuel's destination page was intercepted with a test response; this verifies the app's clipboard/navigation contract rather than QuizDuel's external import UI.
- Initial publication `b8c6074` deployed successfully in Pages run `38094215214`. The served app assets and all nine JSON files matched Git's committed bytes (Windows checkout line endings differ). A separate browser check opened the real, unintercepted QuizDuel site from all three level buttons and verified the corresponding clipboard objects.
- The full browser suite also passed against the deployed daily app for all nine reviewed dates: mobile/desktop clipboard and navigation contracts, failure states and fallback, 270 reviewed questions through mobile completion, and reading controls.
- A final adversarial inspection identified an additional tone clue in October 11 expert item 2: asking how persistence differs from “faithful endurance” left forgetfulness as the only clearly unfaithful option. The final item asks what the text connects with persistence and offers competing plausible motives rather than three virtuous contrasts. Rechecked Isaiah 57:10–11, renewed the content hash, and regenerated that level's export. This item was already among the 54 corrected items; the correction count is unchanged.

The configured automation model was read from its current `automation.toml`: `gpt-6.1-sol`, `high` reasoning effort.
