# Source Document to Quiz Build Workflow

Use this workflow when the user supplies a reference document and asks for original quizzes based on its content rather than extraction of prewritten questions.

## Source and Scope

1. Identify the authoritative, most current source corpus before writing questions.
2. Map the document into chapters and visible subsections.
3. Build a coverage list of major facts, thresholds, formulas, responsibilities, procedures, exceptions, and commonly confused distinctions.
4. Scale the number of questions to the quantity and density of material in each chapter. Do not force every chapter to have the same count.
5. Use one scored question per major testable fact when broad coverage is requested.

## Question Quality

Primary item-writing reference: [NBME Item-Writing Guide](https://www.nbme.org/sites/default/files/2021-02/NBME_Item%20Writing%20Guide_R_6.pdf).

- Follow the NBME one-best-answer principles: use a focused, closed lead-in; make the options answer the same question on the same dimension; and ensure a prepared examinee can select one clearly best answer.
- Prefer clinical or operational application, distinction, threshold, calculation, and responsibility questions over copied fact-recognition statements.
- Do not prefix routine stems with repetitive source boilerplate such as "According to this document" or "According to the 2026 guidance." Assume the source is authoritative unless attribution is itself the tested concept.
- Every question must test a named learning objective and have one defensible answer based on the authoritative source.
- Write distractors from realistic misconceptions: a nearby threshold used for a different purpose, a related agency with a different role, a correct procedure performed at the wrong time, or a rule that applies to a neighboring category.
- Never create distractors by blindly swapping words, negating a sentence, multiplying numbers, reversing a numeric range, or changing units. Each incorrect option must remain internally coherent and plausible to a learner who incompletely understands the concept.
- Keep options grammatically parallel, similarly specific, and comparable in length. The correct answer must not be systematically longer, more qualified, better written, or more complete than the distractors.
- Keep numerical ranges ordered from smaller to larger, preserve dimensional consistency, and verify every conversion independently.
- Apply the cover-the-options rule: after reading the stem, a knowledgeable learner should be able to formulate the answer before seeing the choices.
- Never allow duplicate answer choices.
- Rotate the correct-answer position and audit the final A-D distribution.
- Do not preselect answers unless the user explicitly requests defaults.
- If a source statement is ambiguous, do not invent a rule. Flag it for manual review or omit it.
- Use existing professionally edited Core Review questions as style references, but do not copy their wording or content.

## Explanations

Every item must include:

- the correct answer;
- the source-grounded fact in complete language;
- enough context to explain why the distinction matters;
- clarification of the most tempting incorrect choices, especially when they are valid rules in a different context.

Explanations must teach the concept rather than merely restate the answer. For numerical thresholds and paired concepts, identify what the distractor values or terms actually refer to.

## Reproducibility

- Prefer a generator script plus structured question JSON over manually editing many HTML files.
- Keep a manifest containing chapter titles, source files, output folders, and question counts.
- Document any source-specific parsing rules or manually resolved ambiguities.
- Re-running the generator must preserve stable app IDs and empty default answers.
- Keep authored item content separate from rendering code. A generator may balance answer positions and validate structure, but it must not invent stems or distractors mechanically.
- Increment a question-bank or save-schema version when questions are reordered or replaced so saved answers cannot silently attach to different items.

## Required QA

For every generated chapter:

1. Confirm question IDs are sequential and unique.
2. Confirm every question has exactly one valid answer.
3. Confirm each answer letter exists among the choices.
4. Confirm option text is unique within the question.
5. State the learning objective for each item during authoring and reject items that test only grammar, range order, capitalization, or test-taking tricks.
6. Inspect every numerical and unit-bearing question manually against the current source. Recalculate percentages, conversions, and effective half-lives rather than trusting generated text.
7. Audit whether the correct answer is the longest option. Investigate any chapter where this occurs in more than roughly 60% of items or where correct options are consistently much longer than the option mean.
8. Review every distractor for internal coherence, plausible confusion, grammatical parallelism, and use of the same units or conceptual category.
9. Search for repetitive source-attribution stems, malformed substitutions, broken spacing, page artifacts, inverted ranges, capitalization errors, contradictory choices, and explanations that merely restate the answer.
10. Sample questions from every source subsection, not only the beginning of a chapter.
11. Compare the final style with several professionally edited, text-only Core Review questions already in the library.
12. Compile the generated inline JavaScript with Node.
13. Register each app in both temporary-app indexes and run:

```powershell
python scripts\verify-temporary-apps-index.py
```

14. Open representative chapters in the browser, answer both correctly and incorrectly in Tutor mode, and verify Quiz mode review, persistence, reset, and state export/import.
15. Commit and push the verified work.
