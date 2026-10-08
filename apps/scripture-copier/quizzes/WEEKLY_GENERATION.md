# Come Follow Me daily quiz production

This is the durable instruction set for the Friday Codex run. The app at `apps/scripture-copier/cfm-2026.html` is static; questions are authored ahead of time as `quizzes/YYYY-MM-DD.json`. Do not generate in the browser. Existing quiz questions are published content: do not regenerate or rewrite them unless correcting a verified error. Derived `quizDuel` exports may be added or refreshed without changing the authored questions.

## Friday run

1. Work in The-Library repository. Read its `AGENTS.md`, `apps/scripture-copier/AGENTS.md`, this file, `cfm-schedule-2026.json`, `cfm-2026.html`, and `quizzes/validate.py`. Inspect `git status` and protect unrelated changes. Pull or fetch current `main` before authoring; resolve any overlap rather than overwriting work.
2. Find the upcoming daily dates without quiz files. Cover every day from the run date through the Sunday **after** the next scheduled Friday run. A little overlap is fine; do not rewrite a valid existing day.
3. Calculate each exact daily verse slice by following `loadWeek` in `cfm-2026.html`: concatenate all listed chapters in reading order, split the verse list across seven days using `floor(total / 7)`, and give the first `total % 7` days one extra verse. Use the app's `data/<volume>/<book>.json` and the current week's `manual/2026/week-NN.txt`. The daily slice is the primary source; the weekly manual supplies context but must not be used to ask about material outside the day's reading. If an assignment has no verses, do not invent a quiz; report it for review.
4. Read the assigned verses and relevant manual sections before writing. If further context is essential, consult official Church scripture or Come Follow Me pages. Keep all claims source-grounded. Create exactly 10 **distinct** questions for each of `kid`, `high-school`, and `expert` for each missing date. All levels cover that day's material, at different reading and reasoning levels. A reference may be reused across levels; the question should not merely be reworded three times.
5. Follow the schema in existing JSON. Each question needs a stable unique `id`, `date`, `difficulty`, `question`, four `{id, text}` options, one `correctOptionId`, a concise `explanation`, and `source` with a human-readable verse reference and official scripture URL. Make IDs stable across reruns. Use a fresh file per date. The UI shuffles options when played; vary stored keyed positions as well.
6. Run `python apps/scripture-copier/quizzes/export_quizduel.py --write` for **all** existing and new dates, even when no dates need new questions. This adds or refreshes each level's derived export without changing `date` or `levels`. Then run `python apps/scripture-copier/quizzes/validate.py`. Fix every error before committing. Run any relevant app checks and inspect each new day's questions manually. Commit only the new quiz files, missing/stale export updates, and directly relevant fixes, push to `main`, wait for the existing GitHub Pages deployment, and open the deployed daily page and at least one new or updated JSON URL. Verify the three level buttons copy the corresponding JSON and open QuizDuel after copying succeeds. Report actual dates added, export counts, and verification evidence. If push or deployment fails, repair it and report the remaining blocker if it cannot be resolved.

## QuizDuel export contract

The confirmed codebase is [`starfox1230/dual-sparkle`](https://github.com/starfox1230/dual-sparkle). The import validator in [`src/pages/Generator.tsx`](https://github.com/starfox1230/dual-sparkle/blob/70d16915d4353337e16dec97d51d184fdbb9626d/src/pages/Generator.tsx#L204) accepts a `quizName`, a `questions` array, and answer strings with `correctAnswer` included in `options`. Its [generation contract](https://github.com/starfox1230/dual-sparkle/blob/70d16915d4353337e16dec97d51d184fdbb9626d/src/lib/quiz-generation.ts) specifies four distinct option strings and an explanation. Verified October 4, 2026.

Each daily JSON contains `quizDuel.kid`, `quizDuel.high-school`, and `quizDuel.expert`. Each value is a complete, independently importable object:

```json
{
  "quizName": "Come Follow Me — YYYY-MM-DD — Kid",
  "questions": [
    {
      "question": "Question stem?",
      "options": ["First choice", "Second choice", "Third choice", "Fourth choice"],
      "correctAnswer": "Second choice",
      "explanation": "Source-grounded rationale, followed by the verse reference and official URL."
    }
  ]
}
```

Export all 10 questions from the corresponding level in authored order. Resolve the keyed option ID to its **exact text**; do not export an ID or array index as `correctAnswer`. Retain the verse reference and official URL in the explanation. Do not hand-author a second question bank: `export_quizduel.py` is the canonical conversion. `validate.py` rejects missing, incomplete, or stale exports and runs in the Pages deployment workflow. `export_quizduel.py` without `--write` also checks exports without changing files.

In the app, **Copy JSON + QuizDuel** copies only that level's complete object and opens `https://quiz-duel.lovable.app/` after copying succeeds. The user pastes the JSON into QuizDuel's quiz input. Test clipboard success, clipboard denial, popup blocking, and mobile/desktop layout with `quizzes/test_ui.cjs`; set `NODE_PATH` to a Node installation containing Playwright and serve the repository root on port 8765. Include QuizDuel export counts and dates backfilled in each run report.

## Item-writing standard

### Required correction and publication gates (October 7, 2026)

The October 5–11 generation run built distractors from other items' keyed answers. This produced repeated choices, mixed grammatical categories, and questions answerable by elimination without reading. Structural validation passed because it checked only individual option uniqueness. Do not use a shared answer pool, rotate another question's answers into an item, or reuse the old October 5–11 bank as an authoring template.

For every date from October 7 forward, including already prepared future dates, inspect content quality before considering the date complete. Do not rewrite past dates. An existing file is not evidence that its content has passed review. Correct verified flaws in current or future dates; preserve valid items.

Write each item's three distractors specifically for its own stem. No full answer-choice text may repeat within a level's ten questions. Read the stem with each of the four options aloud in your review: each must answer the same question, fit grammatically, and use the same semantic category. Names compete with names, actions with actions, reasons with reasons. Kid questions require the same care; simplify reading, never supply the answer in the stem or make wrong options silly.

Keep option word counts close. `quality.py` rejects an option-length spread greater than `max(3, shortest * 0.5)`, and rejects a keyed answer that is uniquely longest or uniquely shortest in more than four of ten questions. Prefer natural equal-length options; if varying lengths, vary keyed length rank as well. Do not fix length failures by padding an option with filler. The stored key distribution must be 3/3/2/2 in an irregular order, not a repeating A/B/C/D cycle. The UI still shuffles options.

Perform two explicit passes after authoring: (1) with the assigned verses, verify one best answer, relevance, each distractor's reason for being wrong, and every explanatory claim; (2) without relying on passage knowledge, attempt to guess by grammar, length, sophistication, stem repetition, absolutes, repeated choices, and answer position. Then compare all ten together for duplication and clues from other questions. Mechanical gates supplement this semantic review; they cannot prove grammar, plausibility, or one-best-answer quality.

Only after reviewing every item, attach a content-bound review to each daily JSON:

```python
from quality import bank_hash, REVIEW_CHECKS
doc['qualityReview'] = {
    'questionSha256': bank_hash(doc),
    'checks': REVIEW_CHECKS,
}
```

This records completion of `source-grounding`, `one-best-answer`, `grammar-and-category`, `plausible-distractors`, `no-stem-giveaway`, and `no-testwise-clues`. Do not blindly sign generated questions. Any authored-content edit changes the hash and requires another review. Regenerate `quizDuel` exports after corrections. Run `test_quality.py`, `export_quizduel.py` without `--write`, and `validate.py` before committing; Pages runs the quality regression tests and validator before deployment. Earlier dates retain structural/source validation without retroactive rewriting.

The source validator now derives scripture book names and official URL paths from the schedule, so future non-Isaiah weeks must use their own assigned books rather than adapting Isaiah references.

Use the [NBME Item-Writing Guide](https://www.nbme.org/sites/default/files/2021-02/NBME_Item%20Writing%20Guide_R_6.pdf) and [Vanderbilt Center for Teaching guide](https://cft.vanderbilt.edu/guides-sub-pages/writing-good-multiple-choice-test-questions/) as the item-writing baseline. Adapt their assessment principles to scripture comprehension rather than medical testing.

- Test a central person, event, teaching, image, relationship, or consequence that is worth remembering. Prefer understanding to trivia. A thoughtful reader should enjoy the moment of recognition.
- Write a focused, positive one-best-answer stem. The reader who knows the passage should be able to anticipate an answer before seeing choices. Remove decorative context and avoid unnecessary reading load. If a negative is essential, emphasize **NOT** or **EXCEPT** visibly.
- Make four options grammatically parallel, of similar length and specificity, and in the same conceptual category. Every wrong option should be plausible to a reader with partial or nearby knowledge. Make the distinction fair and supportable from the day's verses.
- Do not use all/none of the above, combined options, absurd distractors, answer clues from grammar or repeated stem words, an unusually polished or long correct option, predictable answer positions, or absolutes used just to disqualify wrong choices. Do not turn difficult questions into obscure facts or speculative theology.
- Kid: short, concrete language; a meaningful choice about the reading; plausible options. High School: context, cause and effect, comparison, theme, or a brief application. Expert: close textual distinctions, structure, imagery, or two-step synthesis grounded in the assigned slice. Expert means depth, not ambiguity.
- Explain **why** the best option follows from the passage in one or two useful sentences. Reference the relevant assigned verse(s). Avoid claims the cited verses do not support.

### Adversarial second pass, for every item

Pretend you have **not** read the passage. Try to guess from option length, sophistication, grammar, repeated words, absurd alternatives, absolutes, answer position, or one option's extra qualifications. Rewrite if any clue works. Then pretend you **have** read carefully: can you defend another option? Rewrite until exactly one answer is clearly best. Read all 10 questions as a set to remove duplicates and repetitive stem patterns.

## Run report and model note

State dates produced, question counts, validation command/result, commit, deployment result, and the actual deployed URL. End every run with a short model note reflecting the scheduled task's **actual configured model and reasoning effort**, not a fixed string copied from this file. For the initial configuration the note is: “Model: Luna High. This quiz-generation run used Luna High. If you want future runs to use a different model—for example Sol Low or Sol High—tell me and the scheduled task can be changed.” If the configuration changes, update that note accordingly.
