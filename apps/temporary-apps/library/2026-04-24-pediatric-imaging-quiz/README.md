# Pediatric GI Imaging Quiz Build Notes

This temporary app turns chapter 1 of `Core Review Pediatric Imaging.pdf` into a self-contained HTML quiz.

## What The App Contains

- `index.html`: the generated quiz app.
- `questions.json`: extracted question data, answer keys, explanations, and image paths.
- `assets/`: extracted PDF figures used by the quiz.
- `build_quiz.py`: the reproducible generator.

The app saves progress in browser `localStorage` under:

```text
temporary-app-state:pediatric-gi-imaging-quiz-ch1
```

The Settings panel can copy or download that saved-state JSON. Pasting the JSON into the Settings panel on another computer restores answers, mode, current question, review state, and whether the question navigator is open.

## Current Source PDF

The generator looks for the source PDF here:

```text
G:/My Drive/0. Radiology/Core Review Pediatric Imaging.pdf
```

If that path is unavailable, it falls back to:

```text
apps/temporary-apps/Core Review Pediatric Imaging.pdf
```

The fallback is only for temporary local generation. Do not commit the full PDF into the repo.

## Extraction Method

The PDF has a regular board-review layout:

1. Front matter.
2. Chapter question pages.
3. Chapter answer and explanation pages.
4. Later chapters with the same pattern.

For chapter 1:

- Questions are PDF page indexes `8..55` in zero-based Python indexing, shown as pages 9-56 in a PDF viewer.
- Answers and explanations are PDF page indexes `56..89`, shown as pages 57-90.
- Chapter 2 starts on PDF page 91.

`build_quiz.py` uses two PDF libraries:

- `pypdf` extracts question and explanation text.
- `PyMuPDF` (`fitz`) extracts image blocks in visual page order, which gives more reliable image-to-question pairing than `pypdf` image extraction alone.

Question parsing works by finding sequential question starts such as `1.`, `2.`, `3.` and ignoring incidental references like `Question 14`. Options are parsed from `A.` through `D.`. Answers are parsed from explanation text matching patterns like `12 Answer A.`.

## Rebuilding This App

From the repo root:

```powershell
& 'C:\Users\sterl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'apps\temporary-apps\library\2026-04-24-pediatric-imaging-quiz\build_quiz.py'
python scripts\verify-temporary-apps-index.py
```

The generator rewrites:

- `index.html`
- `questions.json`
- every file in `assets/`

Manual UI changes should be made in `build_quiz.py`, not directly in `index.html`, unless they are throwaway experiments.

## Adapting To Another Chapter Or Similar PDF

1. Find chapter boundaries using the PDF outline or text sampling.
2. Update these constants in `build_quiz.py`:

```python
QUESTION_START_PAGE = ...
QUESTION_END_PAGE = ...
ANSWER_START_PAGE = ...
ANSWER_END_PAGE = ...
```

The constants are zero-based page indexes, and the end values are exclusive.

3. Update `APP_ID`, page title, heading, and registration metadata if making a new standalone temporary app.
4. Run the generator.
5. Spot-check:

- question count and numbering
- answer keys
- any questions whose stem says an image is shown but no image is attached
- transition pages where one question's answer choices appear above the next question

6. Register the new app in `apps/temporary-apps/index.html`.
7. Run:

```powershell
python scripts\verify-temporary-apps-index.py
```

## Known Limits

- Text extraction from the PDF sometimes removes spaces, for example `shownbelow`. The app preserves extracted wording rather than trying to overcorrect every phrase.
- Some questions intentionally have no images because they are text-only or refer back to earlier images.
- The generator assumes four answer choices for most questions. If a future chapter has a question with fewer or more choices, inspect `questions.json` and adjust parsing if needed.
