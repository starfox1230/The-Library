# Canonical Anki Card Style Guide

Use this as the source of truth for writing Anki cards for this user. If card quality needs to change, edit this file first and make other workflows point here.

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
- Do not put source labels, app names, article names, quiz names, question numbers, or batch identifiers in the front-side card substance. Card fronts should stand on their own as study facts or image prompts without making the reviewer read provenance text every time.
- Do not include answer-choice letters such as `A.`, `B.`, `C.`, `D.`, or `E.` in the card answer. Test the actual diagnosis, structure, device, threshold, management step, or fact.
- Do not use generic lazy prompts such as `What is the key answer or diagnosis?` when the source gives enough information to write a targeted prompt. Write the shortest prompt that gives enough context to answer accurately.
- Split overloaded comparisons into separate cards unless the comparison itself is the tested concept.
- Do not create cards just because text exists. Skip low-yield filler.

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
{"content":"Most likely diagnosis?<br><br>{{c1::Hepatic steatosis}}<br><br><img src=\"image-001.jpg\">","tags":["#AnkiChat::YYYY.MM.DD_Subject"],"id":"note-004"}
{"content":"Most likely diagnosis in the pancreas?<br><br>{{c1::Mucinous cystic neoplasm}}<br><br><img src=\"image-002.jpg\">","tags":["#AnkiChat::YYYY.MM.DD_Subject"],"id":"note-005"}
```

Rules:

- Only create image-front cards when the card can reasonably be a diagnosis-style prompt.
- Use `Most likely diagnosis?` when the image is the main prompt.
- Add anatomical or clinical locking context when needed.
- Convert long quiz stems into brief test-style prompts. Keep only the minimal age, symptom, modality, lab, or clinical clue needed to make the image answer unambiguous.
- Match the prompt to the task: `Most likely diagnosis?`, `What structure is indicated?`, `What device is shown?`, `What artifact is shown?`, `What BI-RADS kinetic curve is shown?`, or similarly specific wording.
- Use one diagnosis cloze.
- Append the image or images below the prompt and answer.
- Include the complete diagnostic image or panel set needed to make the diagnosis. Do not crop so tightly that only one small finding remains when the intended diagnosis depends on distribution, multiplicity, anatomy, or comparison.
- Include multiple panels when they belong to the same figure and are needed for the diagnosis.
- If an image-front card contains more than one image, place a simple image count marker immediately above the first image in the format `1/N`, where `N` is the total number of images on that card.
- Never include the figure caption in the front-side image crop.
- Never include caption text in the `Text` field for an image-front diagnosis card.
- Never prefix image-front cards with source provenance such as a quiz name, source name, article name, question number, or batch label. Put source information in `Extra`, `README.md`, or `manifest.json` only.
- Put short discriminators, pitfalls, or a brief rationale in `Extra` when useful. Do not write long explanations in `Extra`.
- If a source question or source item has images that are not already shown on the front of a given card, append all of those images after the text in `Extra`. This is required for fact-only cards derived from image-containing questions.
- For quiz-derived cards, start `Extra` with the source question number in the format `Q<number>` before result, difficulty, rationale, or images.
- Include a screenshot of the full source page in `Extra` whenever feasible so the reviewer can see the source context.
- A `Most likely diagnosis?` card must include an image.
- Do not create image-front cards for labels, arrows, or caption trivia unless the user explicitly asks for that style.

## Image-Label Cards

This style is not the default. Do not create image-label cards unless the user explicitly asks for them.

If explicitly requested, use concrete stems for arrows, arrowheads, labels, and marked findings.

Preferred stems:

- `What does the arrow indicate on this CT?`
- `What do the arrowheads indicate on this MRI?`
- `What finding is shown by the solid arrow on this angiogram?`

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

If a reviewer flags one card for testing the wrong concept, review the rest of the same generated batch for analogous mistakes before rebuilding. Fix the batch, not just the single reported card.

Skip:

- Filler or vague statements
- Administrative workflow text
- Boilerplate
- Duplicates and near-duplicates
- Long textbook sentences wrapped wholesale in one cloze
- Cards that merely restate a section title
- Cards requiring the reviewer to guess what attribute is being tested
- Cards based on figures that are not visible or not diagnostically useful

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
- No long raw prose clozes.
- No duplicate or near-duplicate notes.
- Image references point to packaged local media filenames, not remote URLs.
- Image-front diagnosis cards do not include captions in `Text` or in the front-side crop.
- A full source-page screenshot is present in `Extra` when feasible.
