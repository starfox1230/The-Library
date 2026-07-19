# Canonical Anki Card Style Guide

Use this as the source of truth for writing Anki cards for this user. If card quality needs to change, edit this file first and make other workflows point here.

For BoardVitals-specific quiz capture, Anki generation, and local HTML quiz review behavior, use `BOARDVITALS_WORKFLOW.md` together with this guide.

For the Radiology Study OS visual feed, textbook figure extraction, reviewer image behavior, and image-aware export, also use `VISUAL_STUDY_AND_ANKI_SPEC.md`.

## Default Style

- Default to cloze notes, not basic cards.
- Default to the user's existing `saCloze++` card type exactly. Do not create, rename, approximate, or restyle an Anki note type for generated cards.
- Packaged APKGs must reuse the same `saCloze++` model name, model id, fields, templates, and CSS used by the established Radiographics package builder.
- Put generated cards into the single `Saved Cards` deck. Use tags for organization instead of creating topic-specific decks.
- Prefer one clean idea per note.
- Keep cards short, direct, and radiology-board oriented.
- Use natural prose that still sounds clean if read aloud with the cloze mentally blanked.
- Use standard radiology abbreviations when they are common study language.
- Preserve clinical stems only when they help identify or lock the diagnosis.
- Keep the minimum context needed to answer accurately. Preserve key modifiers such as recent chemotherapy, relevant age, symptom, modality, lab, or timing; remove boilerplate such as `a radiologist is reading`, routine source workflow text, and irrelevant demographics.
- Do not make cards by mechanically truncating a long source stem and adding a question mark. Rewrite the front as a complete, grammatical, short prompt. No generated card front may end mid-sentence.
- Do not put source labels, app names, article names, quiz names, question numbers, or batch identifiers in the front-side card substance. Card fronts should stand on their own as study facts or image prompts without making the reviewer read provenance text every time.
- State the medical fact or question directly. Do not write framing such as `according to the source`, `in the source`, `based on the reading`, `the text states`, or equivalent wording on a card front. Source fidelity is already assumed; provenance belongs in `Extra`, not in the retrieval prompt.
- Do not include answer-choice letters such as `A.`, `B.`, `C.`, `D.`, or `E.` in the card answer. Test the actual diagnosis, structure, device, threshold, management step, or fact.
- Do not use generic lazy prompts such as `What is the key answer or diagnosis?` when the source gives enough information to write a targeted prompt. Write the shortest prompt that gives enough context to answer accurately.
- Do not use `Answer:` or `Key answer:` as a fallback card pattern. If a card cannot be written as a real cloze fact or a direct image prompt, skip it or rewrite it after identifying the tested concept.
- Split overloaded comparisons into separate cards unless the comparison itself is the tested concept.
- Do not create cards just because text exists. Skip low-yield filler.

## Saved Items and User-Selected Key Points

Treat a save or highlight as an explicit signal of what the user wants to retrieve later, not merely as background context.

- Every active highlighted key point must produce a distinct candidate that directly tests the highlighted target. A broader card about the same question does not satisfy this requirement.
- If the selected text is `MRI` in an explanation of a Segond fracture, create a card that tests that a Segond fracture prompts MRI evaluation; do not substitute a general ACL-association card.
- A saved item may yield an additional general high-yield card when useful, but the targeted highlight card must remain separate.
- For a saved question without a highlight, identify and test the shortest source-grounded discriminator needed to answer it correctly.
- Preserve stable source-event and candidate IDs so reruns do not generate duplicates. Do not mark an event processed until its candidate—and any required image media—has been stored and verified.
- Continue to apply every other rule in this guide: default to clean sentence clozes, keep `Extra` concise and contextual, and avoid generic question-answer wrappers.

## Text-First Cloze Cards

Use text-first cards for conceptual facts, mechanisms, criteria, associations, thresholds, and management pearls.

Good patterns:

```json
{"content":"A left ventricular {{c1::pseudo}}aneurysm classically has a {{c2::narrow}} neck.","tags":["#AnkiChat::YYYY.MM.DD_Subject"],"id":"note-001"}
{"content":"In neonates, low lung volumes with granular lung opacities suggests {{c1::surfactant deficiency}}.","tags":["#AnkiChat::YYYY.MM.DD_Subject"],"id":"note-002"}
{"content":"What sign suggests posterior shoulder dislocation on an AP shoulder radiograph?<br><br>{{c1::Lightbulb sign}}","tags":["#AnkiChat::YYYY.MM.DD_Subject"],"id":"note-003"}
```

Rules:

- Usually use one to two clozes.
- Use three clozes only when the fact naturally bundles tightly related items such as name, timing, and disease state.
- Prefer short cloze answers, usually a word or short phrase.
- If a list is the answer, usually put the whole list inside one cloze unless each item is an independent tested concept.
- Keep most cards under about 42 words.

## Visual Diagnosis Cards

Use image-backed cards when the image is diagnostically important.

Preferred patterns:

```json
{"content":"What is the most likely diagnosis?<br><br>{{c1::Hepatic steatosis}}<br><br><img src=\"image-001.jpg\">","tags":["#AnkiChat::YYYY.MM.DD_Subject"],"id":"note-004"}
{"content":"Brief locking context when needed. What is the most likely diagnosis?<br><br>{{c1::Mucinous cystic neoplasm}}<br><br>1/3<br><img src=\"image-002.jpg\"><br><img src=\"image-003.jpg\"><br><img src=\"image-004.jpg\">","tags":["#AnkiChat::YYYY.MM.DD_Subject"],"id":"note-005"}
```

Rules:

- Only create image-front cards when the card can reasonably be a diagnosis-style prompt.
- For pathology diagnosis cards, use the exact default question `What is the most likely diagnosis?`
- Add anatomical or clinical locking context when needed.
- When context is necessary because imaging alone would be too ambiguous, put one brief natural sentence before `What is the most likely diagnosis?`; do not overload the stem.
- Convert long quiz stems into brief test-style prompts. Keep only the minimal age, symptom, modality, lab, or clinical clue needed to make the image answer unambiguous.
- Match the prompt to the task: `What is the most likely diagnosis?`, `What is indicated by the [color] arrow(s)?`, `What device is shown?`, `What artifact is shown?`, `What BI-RADS kinetic curve is shown?`, or similarly specific wording.
- Image-front cards should almost always test visual diagnosis, device/artifact recognition, or labeled structure identification. Do not use image-front cards for multi-step next-best-management questions. If a quiz asks for management after recognizing an image, make the image card test the diagnosis and make a separate text cloze only if the management rule itself is worth memorizing.
- `What is the most likely diagnosis?` is the preferred pathology-image prompt. Use a more specific wording only when the task is genuinely not diagnosis retrieval, such as a named fracture, device, artifact, or labeled finding.
- Use one diagnosis cloze.
- Preserve this exact vertical structure: prompt, `<br><br>`, one answer cloze, `<br><br>`, then either the single image or the `1/N` marker followed by the images.
- Include the complete diagnostic image or panel set needed to make the diagnosis. Do not crop so tightly that only one small finding remains when the intended diagnosis depends on distribution, multiplicity, anatomy, or comparison.
- When the source depicts the same patient's pathology with multiple complementary images, usually include all images needed to provide the full diagnostic picture rather than choosing only one representative image.
- If an image-front card contains more than one image, place a simple image count marker immediately above the first image in the format `1/N`, where `N` is the total number of images on that card.
- Never include the figure caption in the front-side image crop.
- Never include caption text in the `Text` field for an image-front diagnosis card.
- Never prefix image-front cards with source provenance such as a quiz name, source name, article name, question number, or batch label. Put source information in `Extra`, `README.md`, or `manifest.json` only.
- Put short discriminators, pitfalls, or a brief rationale in `Extra` when useful. Do not write long explanations in `Extra`.
- If a source question or source item has images that are not already shown on the front of a given card, append all of those images after the text in `Extra`. This is required for fact-only cards derived from image-containing questions.
- For quiz-derived cards, start `Extra` with the source question number in the format `Q<number>`. It is acceptable to include whether the user got the question correct/incorrect and the difficulty, but do not include peer-comparison percentages such as `correct answer chosen by X%` or `selected answer chosen by Y%`; those are low-yield review noise.
- For every quiz-derived card, include at least one concise teaching sentence in `Extra` after the question number/result metadata. This sentence should explain the specific tested point or discriminator in plain language. It should identify the device, structure, diagnosis clue, threshold, mechanism, or management rule being tested when that context is not already obvious from the front. Example: `Q3. Incorrect; difficulty: hard. This is a radiation survey meter; accuracy is tested yearly, while constancy is checked daily and linearity quarterly.`
- If a quiz question includes a `Vital Concept` or similarly labeled key concept, include that concept word-for-word in `Extra` whenever technically possible. Place it after the question number/result metadata and before any appended images. Do not paraphrase, shorten, or convert it into peer-style metadata; preserve the source wording so the reviewer can see the official tested concept.
- For every card derived from a textbook or other PDF source, include a screenshot of the full source PDF page in `Extra`. This applies to visual cards, text-first cards, saved-fact cards, and cards derived from auto-generated quizzes. Treat the screenshot as required source context, not as an optional visual-card enhancement.
- Preserve the exact source PDF page mapping while generating quizzes and card candidates so the later Anki pass can attach the correct page screenshot without guessing. If a card genuinely draws from multiple pages, include the necessary page screenshots in source order.
- Omit a required page screenshot only when the page cannot be identified, captured, or stored. Never substitute a guessed page; record the exception in the build report and candidate metadata.
- A `What is the most likely diagnosis?` card must include an image.
- Arrow-indicated pathology cards are a standard visual-card type when the arrow marks a useful finding. Do not create cards from arbitrary labels or caption trivia.

## Arrow-Indicated Pathology Cards

Arrow cards are one of the user's two main pathology-image card types. Use them when the source image contains arrows that identify a specific finding, structure, or manifestation worth retrieving. They usually need only the single image that contains the relevant arrow because the target is narrower than a diagnosis card.

Preferred exact structure:

```html
What is indicated by the <span style="color: #ff3b30;">red arrows</span>?<br><br>{{c1::The indicated finding}}<br><br><img src="image-005.jpg">
```

Rules:

- Use `What is indicated by the [color] arrow?` or `What is indicated by the [color] arrows?`, matching singular or plural to the image.
- Color the complete `[color] arrow` or `[color] arrows` phrase with inline HTML so its displayed text color visually matches the arrow color in the image. Use an appropriate hex color rather than leaving the phrase unstyled.
- Preserve the same vertical structure as diagnosis cards: prompt, `<br><br>`, cloze answer, `<br><br>`, then the image.
- Usually use one image. If multiple images are genuinely needed, use the same `1/N` marker and one-image-per-line ordering required for multi-image diagnosis cards.
- Ask about the specific indicated imaging finding, structure, or manifestation; do not mine incidental caption trivia.

Avoid vague stems:

- `High-yield takeaway?`
- `Key teaching point?`
- `Which pattern suggests...?`
- `What is important about this?`

## JSON Contract

When note JSON is requested, return a single JSON array. Each object must have exactly one of `content` or `html`, plus `tags`, plus optional `id`.

Valid shapes:

```json
{"content":"<cloze HTML>","tags":["#AnkiChat::YYYY.MM.DD_Subject"],"id":"note-001"}
{"html":"<cloze HTML>","tags":["#AnkiChat::YYYY.MM.DD_Subject"],"id":"note-002"}
```

Rules:

- Use straight double quotes.
- Do not add extra keys.
- `tags` must contain exactly one shared batch tag unless an explicit downstream APKG manifest requires additional metadata.
- Cloze syntax must be `{{cN::answer}}` or `{{cN::answer::hint}}`.
- Use `<br><br>` between a question stem and the cloze answer.
- Different concepts in one sentence use different cloze numbers.
- Multiple parts of the same concept reuse the same cloze number.
- Do not use arrows or textual arrows.
- Do not use mid-sentence colons outside cloze syntax or hint syntax.
- Avoid literal `<` and `>` in normal prose. Use words like `less than` or `greater than`; HTML tags are allowed.

Batch tag format:

```text
#AnkiChat::YYYY.MM.DD_Subject
```

Use America/Chicago for the date. Make `Subject` concise, TitleCase when reasonable, with spaces replaced by underscores and non-alphanumeric characters removed except underscores.

## What To Turn Into Cards

Prioritize:

- Definitions
- Diagnostic criteria
- Imaging signs
- Mechanisms
- Cause and effect relationships
- Classic associations
- Risk factors
- Pathognomonic findings
- Thresholds and measurements
- Staging and grading systems
- Board-relevant management steps
- Diagnostic clues and discriminators
- Differentials
- Named eponyms
- Pearls and pitfalls

For quiz review sources, create fact cards for the key fact needed to answer each question correctly, especially missed questions and concepts that are not fully captured by the image card. These should be clean cloze cards, not broad summaries. Do not mine every wrong-answer explanation unless the user specifically asks; prioritize the fact that distinguishes the correct answer.

For every missed quiz question, also create one additional misconception card based on the user's selected wrong answer. The card should target the underlying term, definition, discriminator, or mistaken association that would have prevented the miss. It does not need to be framed negatively; prefer a clean positive cloze fact such as a definition or key discriminator.

When converting a quiz question into a fact card, identify what the question was actually testing before writing the cloze. Do not make tautological cards where the answer is essentially restated in the prompt, such as testing that a septate uterus has a septum. Prefer the highest-yield tested discriminator or association, such as which Mullerian duct anomaly is most associated with miscarriage. If the image diagnosis card already tests the visual diagnosis, the separate fact card should usually test the nonvisual concept or board association that made the question hard.

Do not paste a Vital Concept, explanation sentence, or source stem and then append `Key answer: {{c1::...}}`. That is a failed card. Convert the concept into a direct cloze sentence where the blank is the tested discriminator, association, diagnosis, threshold, mechanism, or rule.

For BoardVitals-style work, prefer a two-pass workflow: first capture and organize the quiz into review artifacts, then generate Anki cards only when explicitly requested as a separate card-writing pass. This keeps card writing from being treated as a mechanical tail step.

If a reviewer flags one card for testing the wrong concept, review the rest of the same generated batch for analogous mistakes before rebuilding. Fix the batch, not just the single reported card.

For saved quiz capture/review workflows, also create a standalone local HTML review page as the final artifact after the card package and review docs. Build it from saved local captures and media rather than revisiting the source website. Use a dark-mode visual style by default. It should show the quiz top-to-bottom with local images, selected answer, correct answer, result/difficulty metadata, explanation text, and any Vital Concept text. Show peer percentages for each answer choice as right-aligned parenthetical badges. Include a question-number prefix filter, a separate word-search filter, and a result/sort control with `All`, `Incorrect`, and `Hardest` modes. `Hardest` sorts by the percentage of peers who chose the correct answer, ascending from lowest correct-answer percentage to highest. Strip DOM/accessibility artifacts from visible text, including `Radio Selected`, `Radio Unselected`, `img`, checkbox state text, and heading level markers.

When extracting quiz stems for review pages or card-writing context, preserve all stem paragraphs before the answer choices. Do not stop after the first long paragraph. Keep short follow-up context such as lab values and the final question line because those are often the exact details needed to understand the tested concept.

Skip:

- Filler or vague statements
- Administrative workflow text
- Boilerplate
- Duplicates and near-duplicates
- Long textbook sentences wrapped wholesale in one cloze
- Cards that merely restate a section title
- Cards requiring the reviewer to guess what attribute is being tested
- Cards based on figures that are not visible or not diagnostically useful
- Prompt fragments that are cut off mid-sentence
- `Answer:` or `Key answer:` cards created from copied quiz stems or copied Vital Concepts

## Quality Gate

Every card must pass the Smart Student Test:

```text
Could a smart student fill in this blank with a different answer that is also factually true?
```

If yes, add locking context or skip the card.

Final validation checklist:

- One clean idea per note.
- Self-contained and unambiguous.
- Uses the existing `saCloze++` card type exactly by default.
- Goes into the `Saved Cards` deck at packaging time.
- Valid cloze syntax.
- One shared batch tag.
- No arrows.
- No mid-sentence colon outside cloze syntax.
- No semicolon gluing unrelated ideas.
- No generic question stems.
- No source-framing language such as `according to the source` or `in the source` in the card front.
- No long raw prose clozes.
- No duplicate or near-duplicate notes.
- Image references point to packaged local media filenames, not remote URLs.
- Image-front diagnosis cards do not include captions in `Text` or in the front-side crop.
- Every textbook/PDF-derived card has the correct full source-page screenshot in `Extra`, including cards derived from auto-generated quizzes, or the build report records why it was technically unavailable.
