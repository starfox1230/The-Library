# Come Follow Me review — October 30, 2026

Run scope: October 30–November 8, through the Sunday after the next configured Friday run (November 6). Fetched `origin/main` before authoring and used an isolated worktree to protect unrelated changes. Main contained prepared dates through November 1 and no later banks.

Added November 2–8: **210 questions**, ten per level per day. Reviewed all **300 questions in 30 level banks** across the ten current/future dates. Corrected **nine existing items**, preserved the other 81 existing questions, and left all past dates unchanged. The canonical exporter added 21 new level exports and refreshed five existing ones: **26 added/refreshed exports**, in ten daily JSON files. All 129 exports across 43 published dates were checked.

## Sources read before authoring

Read `WEEKLY_GENERATION.md`, including its October 7 correction, repository/app instructions, the schedule, loader's `loadWeek` algorithm, validator, quality gates, export contract, and browser suite. Read the complete local manuals `manual/2026/week-44.txt` and `week-45.txt` and every verse of these exact KJV allocations from the app's scripture data. The allocations follow chapter concatenation and quotient/remainder division, including discontinuous chapters.

| Date | Exact assigned slice | Verses |
| --- | --- | ---: |
| October 30 | Jeremiah 38:9–39:18; Lamentations 1:1–4 | 42 |
| October 31 | Lamentations 1:5–22; 3:1–24 | 42 |
| November 1 | Lamentations 3:25–66 | 42 |
| November 2 | Ezekiel 1:1–2:4 | 32 |
| November 3 | Ezekiel 2:5–3:25 | 31 |
| November 4 | Ezekiel 3:26–27; 33:1–29 | 31 |
| November 5 | Ezekiel 33:30–33; 34:1–27 | 31 |
| November 6 | Ezekiel 34:28–31; 36:1–27 | 31 |
| November 7 | Ezekiel 36:28–38; 37:1–20 | 31 |
| November 8 | Ezekiel 37:21–28; 47:1–23 | 31 |

Applied the homogeneous, plausible, one-best-answer principles in the [NBME guide](https://www.nbme.org/sites/default/files/2021-02/NBME_Item%20Writing%20Guide_R_6.pdf). The workflow's former Vanderbilt guide URL currently redirects to its general teaching page; no claims were taken from that redirect.

## Existing-item findings and corrections

Stable IDs and stored answer positions were retained.

| Date / level / item | Verified flaw and correction |
| --- | --- |
| October 30 / expert / 2 | The oath question could be solved by rejecting logical guarantees without knowing the passage. Compare the specific protection sworn for Jeremiah with the conditional preservation of the city; all alternatives now name concrete oath/message pairings. |
| October 31 / kid / 6 | “Admit” selected the sole confession among innocence and achievement claims. Use four plausible admissions and ask for the one in 1:18. |
| October 31 / high-school / 2 | The stem supplied deer without pasture, revealing the weakened-leader interpretation. Remove that cue and compare four plausible situations of princes under pursuit. |
| October 31 / high-school / 5 | “Absent comforter” made the answer restate the stem while distractors supplied comfort. Ask how expected helpers are portrayed; compare specific accounts of comfort, allies, and leaders. |
| October 31 / high-school / 8 | The keyed “remembered prosperity” contradicted 3:17, which says “I forgat prosperity.” Correct to “forgotten prosperity.” Replace celebratory alternatives with parallel suffering and inward-condition descriptions. |
| October 31 / high-school / 10 | “Without a report of changed circumstances” excluded all three circumstance-based distractors. Ask directly for the grounds of hope and compare four plausible grounds without supplying the exclusion. |
| November 1 / kid / 5 | Turning to God competed with obviously unhelpful blame and delay. Compare meaningful religious/community responses and ask for 3:40's actual call. |
| November 1 / kid / 6 | The inward heart competed with physical crowns, swords, and harvests. Compare four parallel prayer images instead. |
| November 1 / expert / 1 | The stem's statement about hope cued the sole continued-hope interpretation. Ask for the actual framing of silence and compare plausible narrative settings. |

## New-bank source and adversarial review

Read every stem with every option, checked the explanation and one best answer against its assigned verses, and checked why each alternative does not describe that passage. Then reviewed each item without relying on passage knowledge and compared each full ten-item set for repeated content, option reuse, cross-item leakage, grammar, conceptual category, tone, length, and stored-key clues. Distractors were authored separately for each stem, not drawn from a shared answer pool.

Concrete draft revisions included:

- Replaced the lone threatening option among pleasant settings in the thorns/scorpions item with four threatening images. Removed a heart-versus-documents category mismatch in the reception-of-words item.
- Replaced the alarm question's irrelevant request for soldiers' payment with a passage-specific responsibility question. Replaced a self-answering stealing/returning stem with a choice among meaningful actions of repentance and service.
- Kept sheep choices within plausible flock behavior and care. Removed sheep carrying bowls, rebuilding folds, or appointing shepherds. The shepherd-products question now compares plausible uses of fat and wool; the neglected-care item compares actual husbandry tasks.
- Replaced easy good-versus-bad and blessing-versus-punishment options with plausible parallel promises, procedures, roles, and interpretations. Removed wording that itself announced the required contrast or conclusion.
- Removed shortest-answer clusters in the November 3 expert and November 6/8 high-school drafts by rewriting the actual choices. The final November 8 high-school bank has no uniquely shortest or longest key. All 21 new banks have at most three uniquely shortest and at most two uniquely longest keys; their length spreads pass the canonical gate.
- Retained the difference between the scroll's mournful contents and sweet taste; the prophet's warning duty and the hearer's response; simultaneous accountability when a watchman is silent; and the inadequacy of inherited or former righteousness as an excuse for current conduct.
- Kept November 7 within 37:20: the sign, inscriptions, joining, and God's hand are available that day; the national-unity explanation beginning at 37:21 is assessed November 8. Preserved reassembly without breath before the second prophecy, and the explicit interpretation of the bones as Israel.
- Preserved the river's unhealed salt-marsh exception, sanctuary water as the source of the trees' provision, Joseph's two portions, and inheritance for the specifically described resident foreigners within their resident tribes.

All 30 reviewed banks have an irregular stored **3/3/2/2** distribution and unique normalized option texts within each level. Content-bound `qualityReview` hashes and all six required checks were attached only after the source, item, and complete-set semantic review. QuizDuel exports were refreshed after the final corrections.

## Validation and publication gates

From the quizzes directory:

- `python export_quizduel.py --write`: checked 129 level exports across 43 dates; updated ten files.
- `python test_quality.py`: all nine regression tests passed.
- `python export_quizduel.py`: 129 exports checked; no stale files.
- `python validate.py`: 43 dates, 1,290 questions, exact daily scripture references, required review signatures, and 129 exports passed.
- `node --check apps/scripture-copier/cfm-quiz.js` and `git diff --check`: passed from repository root.

The full local `test_ui.cjs` suite passed with `CFM_TEST_DATES` set to all ten reviewed dates, at 390px and 1280px: all three level exports per date, successful-copy-before-navigation, denied clipboard, blocked popup links, legacy copy fallback, all 300 reviewed questions through mobile completion, early exit, and reading controls. Visually inspected both final-date screenshots; controls and failure messages fit each viewport. Final live publication evidence is recorded in the run's automation memory after deployment verification.

Configured automation model: **gpt-6.1-sol**, reasoning effort **high**, read from the actual `automation.toml`; Friday 21:00 schedule preserved.
