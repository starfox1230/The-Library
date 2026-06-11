# Source Document to Quiz Build Workflow

Use this workflow when the user supplies a reference document and asks for original quizzes based on its content rather than extraction of prewritten questions.

## Source and Scope

1. Identify the authoritative, most current source corpus before writing questions.
2. Map the document into chapters and visible subsections.
3. Build a coverage list of major facts, thresholds, formulas, responsibilities, procedures, exceptions, and commonly confused distinctions.
4. Scale the number of questions to the quantity and density of material in each chapter. Do not force every chapter to have the same count.
5. Use one scored question per major testable fact when broad coverage is requested.

## Question Quality

- Prefer application, distinction, threshold, and responsibility questions over trivia.
- Every question must have one defensible answer based on the source.
- Distractors should be plausible contrasts: altered thresholds, swapped responsible parties, reversed requirements, or commonly confused paired concepts.
- Never allow duplicate answer choices.
- Rotate the correct-answer position and audit the final A-D distribution.
- Do not preselect answers unless the user explicitly requests defaults.
- If a source statement is ambiguous, do not invent a rule. Flag it for manual review or omit it.

## Explanations

Every item must include:

- the correct answer;
- the source-grounded fact in complete language;
- the source chapter and subsection;
- enough context to explain why the distinction matters.

When practical, explain why the distractors are wrong, especially for numerical thresholds and paired concepts.

## Reproducibility

- Prefer a generator script plus structured question JSON over manually editing many HTML files.
- Keep a manifest containing chapter titles, source files, output folders, and question counts.
- Document any source-specific parsing rules or manually resolved ambiguities.
- Re-running the generator must preserve stable app IDs and empty default answers.

## Required QA

For every generated chapter:

1. Confirm question IDs are sequential and unique.
2. Confirm every question has exactly one valid answer.
3. Confirm each answer letter exists among the choices.
4. Confirm option text is unique within the question.
5. Inspect all numerical and unit-bearing questions manually.
6. Search for malformed word substitutions, broken spacing, page artifacts, and contradictory choices.
7. Sample questions from every source subsection, not only the beginning of a chapter.
8. Compile the generated inline JavaScript with Node.
9. Register each app in both temporary-app indexes and run:

```powershell
python scripts\verify-temporary-apps-index.py
```

10. Commit and push the verified work.

