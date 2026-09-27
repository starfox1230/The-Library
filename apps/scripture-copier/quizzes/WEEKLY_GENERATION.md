# Come Follow Me daily quiz production

This is the durable instruction set for the Friday Codex run. The app at `apps/scripture-copier/cfm-2026.html` is static; questions are authored ahead of time as `quizzes/YYYY-MM-DD.json`. Do not generate in the browser. Existing quiz files are published content: do not regenerate or rewrite them unless correcting a verified error.

## Friday run

1. Work in The-Library repository. Read its `AGENTS.md`, `apps/scripture-copier/AGENTS.md`, this file, `cfm-schedule-2026.json`, `cfm-2026.html`, and `quizzes/validate.py`. Inspect `git status` and protect unrelated changes. Pull or fetch current `main` before authoring; resolve any overlap rather than overwriting work.
2. Find the upcoming daily dates without quiz files. Cover every day from the run date through the Sunday **after** the next scheduled Friday run. A little overlap is fine; do not rewrite a valid existing day.
3. Calculate each exact daily verse slice by following `loadWeek` in `cfm-2026.html`: concatenate all listed chapters in reading order, split the verse list across seven days using `floor(total / 7)`, and give the first `total % 7` days one extra verse. Use the app's `data/<volume>/<book>.json` and the current week's `manual/2026/week-NN.txt`. The daily slice is the primary source; the weekly manual supplies context but must not be used to ask about material outside the day's reading. If an assignment has no verses, do not invent a quiz; report it for review.
4. Read the assigned verses and relevant manual sections before writing. If further context is essential, consult official Church scripture or Come Follow Me pages. Keep all claims source-grounded. Create exactly 10 **distinct** questions for each of `kid`, `high-school`, and `expert` for each missing date. All levels cover that day's material, at different reading and reasoning levels. A reference may be reused across levels; the question should not merely be reworded three times.
5. Follow the schema in existing JSON. Each question needs a stable unique `id`, `date`, `difficulty`, `question`, four `{id, text}` options, one `correctOptionId`, a concise `explanation`, and `source` with a human-readable verse reference and official scripture URL. Make IDs stable across reruns. Use a fresh file per date. The UI shuffles options when played; vary stored keyed positions as well.
6. Run `python apps/scripture-copier/quizzes/validate.py`. Fix every error before committing. Run any relevant app checks and inspect each new day's questions manually. Commit only the new quiz files and directly relevant fixes, push to `main`, wait for the existing GitHub Pages deployment, and open the deployed daily page and at least one new JSON URL. Report actual dates added and verification evidence. If push or deployment fails, repair it and report the remaining blocker if it cannot be resolved.

## Item-writing standard

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
