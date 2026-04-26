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

When a future chatbot changes the generated app, use this same command pattern:

```powershell
& 'C:\Users\sterl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'apps\temporary-apps\library\2026-04-24-pediatric-imaging-quiz\build_quiz.py'
python scripts\verify-temporary-apps-index.py
& 'C:\Users\sterl\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' -e "const fs=require('fs'), vm=require('vm'); const html=fs.readFileSync('apps/temporary-apps/library/2026-04-24-pediatric-imaging-quiz/index.html','utf8'); new vm.Script(html.match(/<script>([\s\S]*)<\/script>/)[1]); console.log('script compiles');"
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
- any answer explanation that includes or references an image, figure, diagram, table, or classification chart
- transition pages where one question's answer choices appear above the next question
- missing spaces where PDF extraction joined words together, for example `shownbelow`, `alongwith`, or `abdominalradiographs`
- random page numbers inserted inside question stems, choices, or explanations
- any question with fewer than four choices, unless the source PDF clearly has fewer than four choices

6. Register the new app in `apps/temporary-apps/index.html`.
7. Run:

```powershell
python scripts\verify-temporary-apps-index.py
```

## Known Limits

- Text extraction from the PDF sometimes removes spaces, for example `shownbelow`. The app preserves extracted wording rather than trying to overcorrect every phrase.
- Some questions intentionally have no images because they are text-only or refer back to earlier images.
- The generator assumes four answer choices for most questions. If a future chapter has a question with fewer or more choices, inspect `questions.json` and adjust parsing if needed.

## Required Text Cleanup For Future Builds

For future chapters, do not stop at raw extraction. Add a cleanup pass after `questions.json` is generated and before treating the app as done.

The cleanup should:

1. Correct obvious missing spaces from PDF extraction.

Examples:

```text
shownbelow -> shown below
alongwith -> along with
abdominalradiographs -> abdominal radiographs
uppergastrointestinal -> upper gastrointestinal
smallbowel -> small bowel
midgutvolvulus -> midgut volvulus
```

Use targeted replacements and review the surrounding sentence. Avoid blind global splitting that could damage medical terms, names, abbreviations, or references.

2. Remove stray page numbers.

PDF extraction can leave standalone page numbers in the middle or end of stems, choices, and explanations. Remove numbers that are clearly page artifacts rather than clinical values, ages, measurements, answer numbers, citations, or percentages.

Common page-artifact patterns:

```text
... true? 17
... most likely diagnosis? 21
... Figure A ... 63 Todani Classification ...
```

Do this with a mix of regex cleanup and manual review. Be conservative around values such as `3 weeks`, `5 mm`, `15.2 mm`, `99m`, `3%`, `2015`, or citation pages.

3. Validate answer-choice counts.

After parsing, print or inspect every question where `len(options) != 4`.

That is abnormal for this book's usual question style and should trigger manual scrutiny. It may mean:

- choices were split incorrectly
- choices were omitted because text extraction merged labels
- a page transition caused the parser to attach part of one question to another
- the source question truly has fewer than four choices

If the source really has fewer than four choices, leave it and document that exception. Otherwise, fix the parsing or manually correct `questions.json` and then update `build_quiz.py` so the correction is reproducible.

4. Add validation output to the generator.

For future automation, make `build_quiz.py` print warnings for:

```text
questions with fewer or more than four choices
question numbers with no answer key
question stems that mention an image but have no image
answer explanations that mention an image/figure/table/chart but have no attached explanation image
duplicate or missing question numbers
likely joined-word patterns
likely stray page-number endings
```

Treat these warnings as review items before saying the app is complete.

## Required Explanation Image Extraction For Future Builds

Some answer explanations contain their own images, diagrams, tables, or classification charts. Those are separate from the question images and must be extracted and shown in the answer explanation area.

This was missed in the first chapter build, so future generators should explicitly support it.

Recommended approach:

1. Extract image blocks from the answer/explanation page range, not just the question page range.
2. Track the current answer number while walking the answer pages in visual block order.
3. Attach answer-side images to a separate field, for example:

```json
{
  "number": 6,
  "images": ["assets/q06_p016_1.jpeg"],
  "explanationImages": ["assets/a06_p062_1.jpeg"]
}
```

4. Render `explanationImages` inside the explanation/review area, below or above the explanation text.
5. Give explanation images the same full-screen click/tap behavior as question images.
6. Add validation warnings when explanation text contains phrases like these but no explanation image is attached:

```text
figure
diagram
classification
table
shown
image
chart
```

7. Manually spot-check answer pages that are mostly image content or have sparse extracted text. Classification charts may not be obvious from text extraction alone.

For this PDF style, a known example is the Todani classification chart near the explanation for question 6. Future chapter builds should include analogous answer-explanation figures automatically.

## Expected Review And Copy UI Pattern

For quiz review mode, do not render one huge list of every answer explanation. Review should be one question at a time:

- the current question remains the main view
- its answer status and explanation appear in that main view
- a compact question grid appears beneath it for jumping between reviewed questions
- selecting a grid number switches the main view to that question's individual explanation

Place `Copy Question` and `Copy Chatbot Prompt` next to the feedback/status row, where the app says `Correct` or `Incorrect. You chose...`. Do not put these copy buttons in the top question toolbar, because they take space away from the question controls and are most useful while reviewing the answer.

## Required Copy Controls For Future Builds

Every future quiz chapter should use two answer-feedback copy controls, placed on the same row as the `Correct` / `Incorrect` status:

- `Copy Question Text`: copies the question stem, answer choices, selected answer, correct answer, PDF explanation, and referenced question/explanation image file paths as plain text.
- `Copy Screenshot`: copies an Anki-oriented rich HTML clipboard pack. The pack should contain separate pasteable elements in this order:
  1. original question image or images, when present
  2. a portrait-phone-style PNG card containing the question stem and answer choices
  3. explanation image or images, when present
  4. a portrait-phone-style PNG card containing the selected answer, correct answer, and explanation text

Do not implement `Copy Screenshot` as one very tall combined screenshot. Keep the pieces separate in the clipboard HTML so Anki can paste them as distinct image/card elements. Browser clipboard APIs usually cannot write several independent image clipboard items in one operation, so the practical implementation is a single rich HTML clipboard item containing multiple `<img>` elements, with a plain-text fallback.

The screenshot text cards should be narrow enough for portrait smartphone readability. The current implementation uses a 900 px wide canvas, dark background, readable 24 px body text, and wrapped lines. Keep that general shape for later chapters.

Question images and answer-explanation images must be converted to data URLs when possible before writing the rich HTML clipboard, so pasted content does not depend on local `file://` paths. If rich clipboard writing is blocked by the browser, fall back to copying the full text export.
