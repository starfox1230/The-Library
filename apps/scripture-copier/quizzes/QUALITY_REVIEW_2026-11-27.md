# Come Follow Me quality review — November 27, 2026

## Scope and source reading

Reviewed all 300 questions in 30 level banks for November 27–December 6.
Added November 30–December 6 (210 questions); corrected six existing items and
preserved the other 84 November 27–29 items. No earlier quizzes were rewritten.
This covers Sunday after the next scheduled Friday run, December 4.

Read both complete local manuals, `manual/2026/week-48.txt` and `week-49.txt`,
before authoring. Read every exact KJV daily slice from the app's source JSON,
using `loadWeek`'s concatenation and seven-way division, rather than assuming
chapter-per-day assignments. The daily boundaries are:

| Date | Exact assigned slice | Questions reviewed |
| --- | --- | --- |
| November 27 | Amos 8:8–9:15; Obadiah 1:1–9 | 30 existing |
| November 28 | Obadiah 1:10–21; Jonah 1:1–2:1 | 30 existing |
| November 29 | Jonah 2:2–4:11 | 30 existing |
| November 30 | Micah 1:1–3:9 | 30 new |
| December 1 | Micah 3:10–6:7 | 30 new |
| December 2 | Micah 6:8–7:20; Nahum 1:1–8 | 30 new |
| December 3 | Nahum 1:9–3:17 | 30 new |
| December 4 | Nahum 3:18–19; Habakkuk 1:1–2:18 | 30 new |
| December 5 | Habakkuk 2:19–3:19; Zephaniah 1:1–16 | 30 new |
| December 6 | Zephaniah 1:17–3:20 | 30 new |

## Actual semantic review

Every item received a source pass: assigned-slice relevance, support for the
key and explanation, one best answer, and a reason each distractor fails the
particular stem. Then each item was challenged without passage knowledge for
grammar, semantic category, plausibility, repeated stem words, length, tone,
absolutes, and answer-position cues. Each ten-item set was compared for repeated
choices, duplicated questions, cross-item clues, and length or key patterns.
The content-bound `qualityReview` signatures were attached after these passes.
They attest to that review; the mechanical gates cannot perform it.

Each item's distractors were written for its own stem. No shared answer pool
or recycling of another question's key was used. All stored key distributions
are irregular 3/3/2/2. Across the reviewed banks, keys are uniquely shortest at
most three times and uniquely longest at most twice. The normal length-spread
and answer-choice uniqueness gates also pass.

### Corrections to existing published items

- November 27 kid 3: replaced the incongruous trading/carrying alternatives
  with competing outcomes of searching for the Lord's word.
- November 27 high-school 9: replaced three favorable outcomes competing
  against the sole judgment answer with four plausible adverse outcomes for
  Edom. The source alone determines the promised bringing down.
- November 28 high-school 8: removed the stem's theological-irony shortcut and
  made the item ask which claim Jonah actually makes about his God.
- November 28 expert 9: removed the implausible piracy accusation and mixed
  authorities. All options now describe a prayer to the Lord with different
  requests; only the key preserves His will and the bloodguilt plea.
- November 29 kid 5: changed the item to Jonah's forty-day warning. The old
  response question offered conspicuously martial alternatives and disclosed
  sackcloth before the nearby king question. The new item remains in Jonah 3:4.
- November 29 kid 7: replaced geography, harvest, and appointment alternatives
  with plausible changes in public conduct. The stem asks which change the
  decree explicitly names, preserving the call away from evil and violence.

### Findings and safeguards in the new banks

- Micah's accusations retain concrete land seizure, eviction, corrupt
  prophecy, violence, dishonest measures, and perverted judgment. The review
  removed questions where a moral label in the stem selected the only moral
  answer, or where a threatened loss competed against three favorable outcomes.
- December 1 stops at Micah 6:7: proposed gifts escalate through calves, vast
  offerings, and a firstborn. Micah 6:8's answer is reserved for December 2.
  The proposed gifts are questions in the text, not endorsed requirements.
- Micah 4 retains weapons becoming farm tools, nations learning God's ways,
  and cessation of war. Zion's Babylonian destination is also its promised
  place of redemption. Micah 5 retains both dew and lion images for the
  remnant, rather than flattening them into one effect.
- Micah 7 retains admission of sin alongside hope, the distinction between
  truth to Jacob and mercy to Abraham, and pardon grounded in delight in mercy.
  Nahum retains both patient power and refusal to acquit wickedness, together
  with the stronghold for those trusting Him.
- Nahum's lion image remains predatory, and No's defenses and helpers do not
  prevent captivity. Its honorable men suffer lots and chains. Numerous
  merchants and captains are not made permanent by the locust comparison.
- Habakkuk's complaint concerns violence and perverted judgment, then the
  problem of a wicked conqueror devouring someone more righteous. Judah is
  not described as sinless. The Chaldeans' corrective role does not endorse
  their violence or their attribution of power to their god.
- The vision's appointed time requires waiting; the fishing image includes
  honoring the means of conquest. The cup turns the offender's humiliation of
  others against himself. Kid stems no longer name fish while offering a hook
  and net against unrelated military tools.
- Habakkuk's prayer preserves fearful petition, wrath and mercy, cosmic
  imagery, salvation, trembling, and joy despite failed crops and livestock.
  Level questions target different features rather than repeating one fact
  across all three levels.
- Zephaniah retains mixed allegiance, failure to seek the Lord, complacency
  about His action, qualified hope of shelter ("it may be"), judgment on pride,
  truthful remnant conduct, and the Lord's saving and singing presence.
  The kid stem asking what to seek no longer supplies "meek" as a clue to
  "meekness"; speech alternatives are all comparable kinds of wrongful speech.
- Full-set review replaced repeated tone-based elimination, narrowed broad
  interpretation stems, and shortened distractors naturally where the keyed
  answer was becoming predictably shortest. No options were padded with filler.

## Validation and export scope

The canonical exporter checked all 213 level exports across 71 dates. This run
adds 21 exports and refreshes five existing exports in ten daily JSON files.
The remaining exports are unchanged.

Passed from the quizzes folder:

```text
python test_quality.py       # 9 regression tests, OK
python export_quizduel.py    # 213 checked, zero stale
python validate.py           # 71 dates, 2,130 questions, 213 exports
```

`export_quizduel.py --write` was run before the checks. Source URL validation
caught two draft Habakkuk slugs; both were corrected to the official `ot/hab`
path and the affected bank was re-signed and re-exported before passing.

The existing `test_ui.cjs` suite passed all ten dates at 390px and 1280px:
exact per-level copies, copy before navigation, clipboard denial, popup
blocking, legacy copy fallback, all 300 reviewed questions through mobile
completion, early exit, and reading controls. Both screenshots were visually
inspected without overflow. `git diff --check` also passed, and comparison with
the base commit confirmed no past authored bank changed.

Publication additionally requires scoped commit and push, successful Pages deployment, committed
content comparison at every changed live JSON URL (including the app's cache
query), and live verification of all three level-specific copy buttons. The
automation memory and final report record those observed publication outcomes.

Scheduled task configuration read for this run: `gpt-6.1-sol`, `high` reasoning
effort; active Friday at 21:00. This states the configured model, not an inferred
identity of the assistant executing the run.
