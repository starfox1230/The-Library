# BoardVitals Quiz Workflow

Use this as the source of truth for BoardVitals quiz capture, review documents, optional Anki package generation, and local HTML quiz recreation.

## Workflow Boundary

- Treat BoardVitals capture/review and Anki deck generation as separate tasks.
- For a new BoardVitals quiz request, the default workflow is capture, parsing, ranked review document, run report, media preservation, and local HTML quiz review.
- Do not generate an APKG or new Anki cards unless the user explicitly asks for cards, a deck, Anki generation, or an APKG in that same request.
- After finishing the capture/review workflow, ask whether the user wants a deck generated only if that is the natural next step. Do not silently roll deck generation into the capture task.
- If deck generation is requested, do it as a focused second pass from the completed local quiz review data and card-writing rules below.
- During deck generation, it is acceptable and preferred to draft cards in type-based passes for consistency: image-front cards, then focused fact cards, then missed-question misconception cards. Before writing the APKG, reorder the completed notes by source question so all cards from Q1 are adjacent, then all cards from Q2, and so on.

## Capture

- Use the user's Chrome extension workflow for BoardVitals quiz pages unless the user explicitly says otherwise.
- Do not use the Codex in-app browser for BoardVitals quiz extraction.
- Save every question page locally as raw JSON, preserving the DOM snapshot and image URLs.
- Preserve whether the user marked the question in BoardVitals. Store this as `marked: true/false` in the parsed question data when the Mark checkbox/flag is selected.
- Preserve explanation list structure during capture as `explanation_lists`: save each top-level list as `{"type": "ul"|"ol", "items": [{"text": "...", "children": [...] }]}` using the page DOM. The accessibility snapshot preserves some nesting but does not reliably distinguish bullets from numbering, so it is only a fallback for older captures.
- When saving image records, include a `section` field on each image: `stem` for images that appear before the answer choices / graded response / correct-answer explanation, and `explanation` for images that appear inside or after the explanation/correct-answer section. Prefer DOM containment when available; otherwise use DOM order relative to the answer-choice list and `Correct Answer:` block.
- Create `source-pages.json` containing all captured questions.
- Create `parsed-questions.json` with question number, QID, result, difficulty, selected answer, correct answer, answer text, peer percentages, full stem, explanation, Vital Concept when present, and image records.
- Separate images into `stem_images` and `explanation_images` whenever the capture data identifies where the image appeared. Preserve a backward-compatible flat `images` list only as a combined legacy field.
- Quizzes captured on or before 2026-05-19 used a legacy flat image workflow and may display all images with the question stem because the saved image records did not reliably distinguish stem images from explanation images.
- After capture, explicitly audit multi-image questions for annotated answer-side figures. BoardVitals may expose explanation/answer images through the same Figure/Media surface as stem images, so DOM position alone is not sufficient. Images with arrows/labels that reveal the answer or are only discussed in the explanation must be labeled `explanation`, displayed in the explanation section of the review page, and excluded from Anki image-card fronts.
- During that audit, treat unannotated/annotated duplicate pairs conservatively: if one image is the same case/view with added arrows, circles, labels, colored overlays, or answer markings, classify the annotated copy as `explanation` by default unless the original question stem clearly required that annotated image to answer a labeled-structure question. This is a required correction before building HTML or Anki cards, not an optional visual cleanup.
- Before finalizing any BoardVitals review HTML or APKG, generate a stem-only contact sheet from the images still classified as `stem` and inspect it visually. If the contact sheet contains answer arrows, circles, colored lines, overlay labels, or marked duplicate answer figures, stop and reclassify those files as `explanation`, then rebuild the review HTML and APKG. Do not rely only on DOM order or filename patterns for this check.
- When extracting stems, preserve every stem paragraph before the answer choices. Do not stop at the first long paragraph. Join short follow-up lines, lab values, and the final asked question so clinical context and the actual task are not silently dropped.
- Do not assume answer choices stop at `E`; support additional choices such as `F` when present.
- For questions without a `Figure/Media` marker, still extract the stem from the main review area before the answer-choice list.
- Clean DOM/accessibility artifacts during parsing. Visible text and review artifacts must not contain `Radio Selected`, `Radio Unselected`, `img`, checkbox state text, or heading level markers such as `[level=5]`.
- Treat snapshot structural roles such as `listitem:` as markup, not explanation text. Preserve their actual content as readable prose/list entries, and rejoin inline fragments split by nested links or superscript/subscript markup so rendered explanations do not display broken phrases such as `click` / `here` or `> 1/3` / `of transthoracic diameter`.
- For legacy captures lacking saved list types, render detectable explanation list blocks as bulleted lists with retained nested indentation rather than flattening them into paragraphs or exposing structural labels.
- When parsing answer choices, prefer the clean answer text paragraph after the letter marker over checkbox label text. Ignore truncated checkbox-label lines that end with a bare backslash from escaped quotation marks.

## Card Package

- Use the user's existing `saCloze++` note type exactly.
- Put cards in `Saved Cards`.
- Do not create, rename, restyle, or approximate a note type.
- Write cards around the real retrieval direction: the front should provide the cue likely to appear in practice or on an exam, and the cloze should be the item the user needs to retrieve. Do not reverse the direction merely because the quiz answer was phrased that way.
- Prefer active recall over recognition. A card should make the user generate the answer, not merely recognize that a statement sounds familiar after the key entity has already been named.
- Avoid cue overload. Do not hand the user the key diagnosis/entity and then ask for a generic associated fact unless that is truly the real-world retrieval task. Include only the minimum cue set needed for an unambiguous answer.
- Every card must be self-contained without relying on memory of the original quiz or answer choices.
- Use one tested point per card. If the quiz required more than one step, split the worthwhile steps into separate cards rather than making a multi-step card front.
- Maintain desirable difficulty: make the cue specific enough to avoid guessing what the card wants, but not so over-cued that it becomes recognition.
- Minimize extraneous load. Remove source labels, quiz metadata, filler clinical boilerplate, and wording that does not change the tested concept.
- Do not put source labels, BoardVitals text, quiz names, question numbers, or answer-choice letters on the front of cards.
- Make one focused fact card for each worthwhile tested concept, targeting the key fact needed to answer correctly. Skip a fact card if it cannot be made into a clean, self-contained cloze without copying the quiz stem or creating a vague `Answer:` card.
- Make one image-front card for every question with meaningful diagnostic images. Include all images from that question on the front. If more than one image appears on the front, put `1/N` immediately above the first image.
- Make one additional misconception card for every missed question based on the user's selected wrong answer and the concept that would have prevented the miss.
- The final APKG note insertion order must be grouped by question number rather than drafting pass. Within each question, use the consistent order: image-front card first when present, then focused fact card, then misconception card when present. This makes initial Anki Browser review follow the source quiz.
- In the APKG, every card generated from a question the user answered incorrectly must import with Anki Flag 1 set, which is the red flag. Apply this at the Anki card level, not by adding visible text or tags to the card front.
- In the APKG, every card generated from a BoardVitals question the user marked must import with Anki Flag 5 set. If a card qualifies for both missed-question Flag 1 and marked-question Flag 5, prefer missed-question Flag 1 because Anki supports one card flag value at a time and missed questions take priority.
- For image cards, default to natural, direct wording. When clinical information is needed, give a brief patient/context sentence followed by the task, usually `Most likely diagnosis?` for diagnosis cards. Avoid stilted label fragments such as `CT abdomen: rim-enhancing lesion. Diagnosis?` when a normal sentence would read better.
- Good image prompt pattern: `16-year-old male with persistent hip pain. Most likely diagnosis?`
- Other acceptable direct prompts include `What named fracture is shown?`, `What device is shown?`, `What artifact is shown?`, or `What structure is indicated?`.
- Image-front cards should almost always test visual diagnosis, device/artifact recognition, or labeled structure identification. Do not turn image cards into multi-step management or next-best-step questions. If the source question asks for treatment after a visual diagnosis, make the image card test the diagnosis and make a separate text cloze only if the treatment rule is worth testing.
- For image cards, include only the minimum clinical context needed to make the image answer unambiguous. Keep high-yield modifiers such as recent chemotherapy, relevant age, symptoms, lab values, or modality. Remove boilerplate such as `a radiologist is reading`, spelled-out common acronyms, and irrelevant demographics.
- Use common radiology acronyms naturally, such as PET/CT, MRI, CT, US, ED, RUQ, FDG, and HCC. Do not spell out common acronyms unless ambiguity would result.
- Do not make prompts by truncating a long quiz stem and appending a question mark. If a stem is too long, rewrite it manually into a short complete sentence. No card front may end mid-sentence.
- Do not use vague prompts such as `What is the correct answer?`, `What is the key answer?`, or `What is the key diagnosis?`.
- Do not create cards that read as `... Answer: {{c1::...}}` or `... Key answer: {{c1::...}}`. Rewrite the card as a real cloze fact or a direct image prompt.
- Do not paste a Vital Concept or explanation sentence and append `Key answer:`. First identify what the question was actually testing, then write a clean cloze around that tested point.
- For fact cards derived from image-containing questions, append all source images in `Extra` if they are not already on the front of that card.
- For BoardVitals cards, use the same content set exposed by the local review page's `Copy screenshot` workflow as extra-side support: include generated question/explanation screenshot cards plus any local source images from that question that are not already used on the front of the Anki card. Do not duplicate front-side images in `Extra`; include the remaining review-page screenshot pack after the teaching sentence/Vital Concept.
- In the generated question-context screenshot used as Anki support, include the answer-choice percentages next to each answer choice, along with selected/correct labels. This mirrors the local review page. The ban on peer percentages applies to repetitive prose in the `Extra` text field, not to the compact screenshot of the original question context.
- Render those generated question/explanation screenshot cards in the same compact dark framed format used by the local review page: calculate height from the actual wrapped lines, with only a small minimum canvas height, rather than adding long unused blank space. The review page and APKG should produce the same readable crop behavior.
- Render list structure in Anki explanation screenshot cards the same way as the HTML review page: use `-` bullets or numbered markers with retained indentation from captured list metadata, and fall back to nested bullets for legacy captures without ordered/unordered type.

## Extra Field

- Start `Extra` with `Q<number>`.
- It is acceptable to include result and difficulty after the question number.
- Do not include peer-comparison percentages as prose in Anki `Extra`; avoid lines such as `correct answer chosen by X% of peers` or `selected answer chosen by Y% of peers`. Keep per-choice percentages in the generated question-context screenshot support image.
- Include at least one short teaching sentence explaining the tested point or discriminator.
- If the question includes `Vital Concept` or a similarly labeled concept, copy it word-for-word into `Extra` whenever technically possible. Put it after the question number/result metadata and before appended images.
- Include all unused question/explanation images after the Extra text.
- At the very end of every BoardVitals Anki `Extra`, append a direct published GitHub Pages link to the HTML review page for that exact question. The link should target the per-question anchor, e.g. `.../quiz-<quiz-id>-review.html#q17`, so opening it jumps directly to the source question while keeping the full review page available from phone or desktop.

## Review Documents

- Create a ranked key-testable-points document.
- Rank missed questions first, based on what the user got wrong or apparently did not understand.
- Then rank correctly answered hard/low-peer-correct questions.
- Then include the remaining key points.
- Preserve a machine-readable card manifest and run report with note/media counts and output paths.

## Local HTML Quiz Review

Create a standalone local HTML quiz-review page as the final artifact for every BoardVitals quiz workflow.

- Build it only from saved local captures and local media. Do not revisit BoardVitals just to make this page.
- Save review pages in the permanent Library repository under `apps/anki-card-creation-codex-helper/boardvitals/<date>-quiz-<quiz-id>/`, not in a temporary-app library.
- After creating or updating a review page, update the permanent BoardVitals Reviews index by running `python scripts/build_boardvitals_reviews_index.py` from the root of `The-Library`. The resulting `apps/boardvitals-reviews/reviews.js` must include the completed review before finishing.
- Use dark-mode styling by default.
- Keep long quiz pages responsive while scrolling: use `content-visibility: auto` with an appropriate `contain-intrinsic-size` on each question card, use asynchronous/lazy image decoding, and avoid expensive sticky-header effects such as `backdrop-filter` blur. Also avoid paint-heavy repeated card effects such as large shadows on every question, and give image/figure containers stable dimensions so fast scrollbar movement does not force large relayout or repaint bursts.
- Do not solve hash-link scrolling by disabling `content-visibility` for every question on the page. If a direct `#qN` link needs help, temporarily force visibility only on the target question long enough to scroll to it, then remove that class so the rest of the page remains virtualized.
- Show all questions top-to-bottom.
- Give every rendered question card a stable HTML anchor id in the format `q<number>` so Anki Extra links can jump directly to the source question.
- Include local images, selected answer, correct answer, result, difficulty, QID, explanation, and Vital Concept when present.
- Display stem images directly under the question stem. Display explanation images inside the explanation section, not with the question stem.
- Never display annotated answer-side images with the question stem. If an image would give away the answer or appears to be an explanation overlay/annotated copy, it belongs in the explanation section and in Anki `Extra`, not on the front of an image card.
- Before generating an APKG, regenerate or inspect a stem-only contact sheet after any image-section edits and confirm that image-card fronts do not include answer arrows, circles, labels, or colored overlays unless the card is explicitly asking for an indicated structure. This check must happen after the final `downloaded-media.json`/image-section edits, not just after the initial scrape.
- Render captured explanation lists in their original ordered or unordered form with nesting preserved. For legacy captures where ordered/unordered type was not saved, render retained list hierarchy as bullet lists rather than presenting it as plain paragraphs.
- Preserve the full multi-paragraph stem.
- Show peer percentages for every answer choice as small right-aligned parenthetical badges inside each answer-choice row.
- Include a question-number prefix filter, where typing `8` shows Q8 only and typing `5` shows Q5 and Q50.
- Include a separate word-search filter across stem, choices, answer, explanation, and Vital Concept.
- Make the two text filters mutually exclusive. If the user starts typing in the question-number filter, automatically clear the word-search filter; if the user starts typing in the word-search filter, automatically clear the question-number filter.
- When the user clears a non-empty question-number or word-search filter, preserve the on-screen position of the currently displayed question while restoring the complete question list. This should let the user search for Q37, clear the filter, and continue scrolling from Q37 to Q38 without being returned to the top.
- Include result/sort controls with `All`, `Incorrect`, and `Hardest`.
- `Incorrect` shows only missed questions.
- `Hardest` sorts by the percentage of peers who selected the correct answer, ascending from lowest correct-answer percentage to highest.
- Include a `Favorite` filter. Each question header should have a star button next to the correctness badge; the empty star is white, clicking it turns it yellow/filled, and the selected favorites persist across page reloads with per-quiz local storage. Questions marked in BoardVitals should be default favorites on first page load for that quiz.
- Include per-question `Copy question text` and `Copy screenshot` buttons, matching the core review quiz behavior. `Copy question text` should copy the stem, choices, selected/correct answer, Vital Concept, and explanation. `Copy screenshot` should create a rich clipboard pack with generated text-card images plus the local question images, falling back to copied text if the rich clipboard API is blocked.
- Both `Copy question text` and `Copy screenshot` must visibly change the clicked button label to `Copied` after success so it is clear the copy action worked.
- For `Copy screenshot`, generate compact dark framed text-card images whose height is measured from the wrapped visible content. Match the Anki screenshot-card layout; do not use character-count estimates or tall fixed minimums that leave large blank areas below short text.
- Clean the rebuilt page so DOM/accessibility artifacts never appear in visible text.
- Add a small `Hide` / `Show` tab at the bottom of the sticky header so the header and filters can be collapsed while scrolling.
- BoardVitals review pages should open with the sticky header collapsed by default. The visible tab should say `Show` on initial load, with the full header available when clicked.

## Validation

Before calling the workflow done, validate:

- The APKG builds.
- The APKG uses only `saCloze++`.
- The APKG deck is `Saved Cards`.
- Cards from missed questions import with Anki Flag 1/red flag set.
- Cards from BoardVitals-marked questions import with Anki Flag 5 set, with Flag 1 taking precedence over Flag 5 if the question was also missed.
- Media counts match referenced local media.
- Stem-vs-explanation image placement has been audited, especially for multi-image questions with annotated answer-side copies.
- A stem-only image contact sheet was generated from the final media labels and visually inspected; all answer-marked/annotated explanation images were moved out of the question stem and out of Anki fronts.
- Card fronts contain no source labels or answer-choice letters.
- Every `Extra` starts with `Q<number>`.
- Every BoardVitals Anki `Extra` ends with a direct published GitHub Pages review-page link for that source question, not a `127.0.0.1` local dev-server link.
- The HTML page has 50 question cards for a 50-question quiz.
- The HTML page contains the expected number of choices and local image tags.
- Long-review performance settings are present in the generated HTML: question cards keep `content-visibility:auto`, no large repeated box shadows are applied, images use lazy/async decoding, figure containers have stable sizing, and hash-link handling does not globally disable virtualization.
- The HTML page has `All`, `Incorrect`, and `Hardest` controls.
- The HTML page has a persisted `Favorite` filter and per-question star buttons that toggle filled yellow favorites.
- BoardVitals-marked questions are default favorites in the HTML review page before user-local favorite edits.
- The HTML page has answer-choice percentage badges.
- The HTML page has per-question `Copy question text` and `Copy screenshot` buttons.
- The `Copy question text` button visibly changes to `Copied` after copying.
- The HTML page has no visible `Radio Selected`, `Radio Unselected`, `img "Radio..."`, `checkbox`, or `[level=...]` artifacts.
- The permanent `apps/boardvitals-reviews/index.html` landing page lists the newly generated review after rebuilding `reviews.js`.
