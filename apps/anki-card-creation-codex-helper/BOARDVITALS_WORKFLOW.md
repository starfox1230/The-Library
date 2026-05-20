# BoardVitals Quiz Workflow

Use this as the source of truth for BoardVitals quiz capture, review documents, optional Anki package generation, and local HTML quiz recreation.

## Workflow Boundary

- Treat BoardVitals capture/review and Anki deck generation as separate tasks.
- For a new BoardVitals quiz request, the default workflow is capture, parsing, ranked review document, run report, media preservation, and local HTML quiz review.
- Do not generate an APKG or new Anki cards unless the user explicitly asks for cards, a deck, Anki generation, or an APKG in that same request.
- After finishing the capture/review workflow, ask whether the user wants a deck generated only if that is the natural next step. Do not silently roll deck generation into the capture task.
- If deck generation is requested, do it as a focused second pass from the completed local quiz review data and card-writing rules below.

## Capture

- Use the user's Chrome extension workflow for BoardVitals quiz pages unless the user explicitly says otherwise.
- Do not use the Codex in-app browser for BoardVitals quiz extraction.
- Save every question page locally as raw JSON, preserving the DOM snapshot and image URLs.
- Create `source-pages.json` containing all captured questions.
- Create `parsed-questions.json` with question number, QID, result, difficulty, selected answer, correct answer, answer text, peer percentages, full stem, explanation, Vital Concept when present, and image records.
- When extracting stems, preserve every stem paragraph before the answer choices. Do not stop at the first long paragraph. Join short follow-up lines, lab values, and the final asked question so clinical context and the actual task are not silently dropped.
- Do not assume answer choices stop at `E`; support additional choices such as `F` when present.
- For questions without a `Figure/Media` marker, still extract the stem from the main review area before the answer-choice list.
- Clean DOM/accessibility artifacts during parsing. Visible text and review artifacts must not contain `Radio Selected`, `Radio Unselected`, `img`, checkbox state text, or heading level markers such as `[level=5]`.
- When parsing answer choices, prefer the clean answer text paragraph after the letter marker over checkbox label text. Ignore truncated checkbox-label lines that end with a bare backslash from escaped quotation marks.

## Card Package

- Use the user's existing `saCloze++` note type exactly.
- Put cards in `Saved Cards`.
- Do not create, rename, restyle, or approximate a note type.
- Do not put source labels, BoardVitals text, quiz names, question numbers, or answer-choice letters on the front of cards.
- Make one focused fact card for each worthwhile tested concept, targeting the key fact needed to answer correctly. Skip a fact card if it cannot be made into a clean, self-contained cloze without copying the quiz stem or creating a vague `Answer:` card.
- Make one image-front card for every question with meaningful diagnostic images. Include all images from that question on the front. If more than one image appears on the front, put `1/N` immediately above the first image.
- Make one additional misconception card for every missed question based on the user's selected wrong answer and the concept that would have prevented the miss.
- For image cards, default to a direct diagnosis-style prompt: `Most likely diagnosis?`, `What named fracture is shown?`, `What device is shown?`, `What artifact is shown?`, or `What structure is indicated?`.
- Image-front cards should almost always test visual diagnosis, device/artifact recognition, or labeled structure identification. Do not turn image cards into multi-step management or next-best-step questions. If the source question asks for treatment after a visual diagnosis, make the image card test the diagnosis and make a separate text cloze only if the treatment rule is worth testing.
- For image cards, include only the minimum clinical context needed to make the image answer unambiguous. Keep high-yield modifiers such as recent chemotherapy, relevant age, symptoms, lab values, or modality. Remove boilerplate such as `a radiologist is reading`, spelled-out common acronyms, and irrelevant demographics.
- Use common radiology acronyms naturally, such as PET/CT, MRI, CT, US, ED, RUQ, FDG, and HCC. Do not spell out common acronyms unless ambiguity would result.
- Do not make prompts by truncating a long quiz stem and appending a question mark. If a stem is too long, rewrite it manually into a short complete sentence. No card front may end mid-sentence.
- Do not use vague prompts such as `What is the correct answer?`, `What is the key answer?`, or `What is the key diagnosis?`.
- Do not create cards that read as `... Answer: {{c1::...}}` or `... Key answer: {{c1::...}}`. Rewrite the card as a real cloze fact or a direct image prompt.
- Do not paste a Vital Concept or explanation sentence and append `Key answer:`. First identify what the question was actually testing, then write a clean cloze around that tested point.
- For fact cards derived from image-containing questions, append all source images in `Extra` if they are not already on the front of that card.

## Extra Field

- Start `Extra` with `Q<number>`.
- It is acceptable to include result and difficulty after the question number.
- Do not include peer-comparison percentages in Anki `Extra`; those are not useful repeated-review content.
- Include at least one short teaching sentence explaining the tested point or discriminator.
- If the question includes `Vital Concept` or a similarly labeled concept, copy it word-for-word into `Extra` whenever technically possible. Put it after the question number/result metadata and before appended images.
- Include all unused question images after the Extra text.

## Review Documents

- Create a ranked key-testable-points document.
- Rank missed questions first, based on what the user got wrong or apparently did not understand.
- Then rank correctly answered hard/low-peer-correct questions.
- Then include the remaining key points.
- Preserve a machine-readable card manifest and run report with note/media counts and output paths.

## Local HTML Quiz Review

Create a standalone local HTML quiz-review page as the final artifact for every BoardVitals quiz workflow.

- Build it only from saved local captures and local media. Do not revisit BoardVitals just to make this page.
- Use dark-mode styling by default.
- Show all questions top-to-bottom.
- Include local images, selected answer, correct answer, result, difficulty, QID, explanation, and Vital Concept when present.
- Preserve the full multi-paragraph stem.
- Show peer percentages for every answer choice as small right-aligned parenthetical badges inside each answer-choice row.
- Include a question-number prefix filter, where typing `8` shows Q8 only and typing `5` shows Q5 and Q50.
- Include a separate word-search filter across stem, choices, answer, explanation, and Vital Concept.
- Make the two text filters mutually exclusive. If the user starts typing in the question-number filter, automatically clear the word-search filter; if the user starts typing in the word-search filter, automatically clear the question-number filter.
- Include result/sort controls with `All`, `Incorrect`, and `Hardest`.
- `Incorrect` shows only missed questions.
- `Hardest` sorts by the percentage of peers who selected the correct answer, ascending from lowest correct-answer percentage to highest.
- Clean the rebuilt page so DOM/accessibility artifacts never appear in visible text.
- Add a small `Hide` / `Show` tab at the bottom of the sticky header so the header and filters can be collapsed while scrolling.

## Validation

Before calling the workflow done, validate:

- The APKG builds.
- The APKG uses only `saCloze++`.
- The APKG deck is `Saved Cards`.
- Media counts match referenced local media.
- Card fronts contain no source labels or answer-choice letters.
- Every `Extra` starts with `Q<number>`.
- The HTML page has 50 question cards for a 50-question quiz.
- The HTML page contains the expected number of choices and local image tags.
- The HTML page has `All`, `Incorrect`, and `Hardest` controls.
- The HTML page has answer-choice percentage badges.
- The HTML page has no visible `Radio Selected`, `Radio Unselected`, `img "Radio..."`, `checkbox`, or `[level=...]` artifacts.
