# Canonical APKG Packaging Guide

Use this as the source of truth for APKG, media, manifest, and build behavior.

For BoardVitals-specific quiz capture, card generation, and local HTML quiz review artifacts, use `BOARDVITALS_WORKFLOW.md` together with this guide.

## Working Reference

The strongest existing implementation is:

```text
C:\Users\sterl\OneDrive\Documents\GitHub\The-Library\apps\radiographics-review
```

Key files:

```text
apps\radiographics-review\src\notes.js
apps\radiographics-review\src\anki.js
apps\radiographics-review\scripts\build_anki_package.py
apps\radiographics-review\test\content-generation.test.js
```

## Package Contract

For APKG output, always create a machine-readable note manifest before building the package. Keep the manifest after the package is built for review and debugging.

Suggested output layout:

```text
<topic-folder>\
  notes.json
  assets\
  <topic-slug>.apkg
  README.md
```

The README should include:

- Source title or textbook section.
- Source page range or figure numbers when known.
- Note count.
- Asset count.
- Build command or script used.
- Any skipped ambiguous material.

## Note Type And Fields

Use the user's existing `saCloze++` note type exactly for all generated packaged cards. Do not create a new note type, do not rename it, and do not approximate its templates or styling.

The canonical implementation to reuse is:

```text
apps\radiographics-review\scripts\build_anki_package.py
```

Use that builder's `MODEL` definition directly or copy it byte-for-byte if importing is not practical. The model name, model id, fields, templates, and CSS must remain exactly aligned with the user's current `saCloze++` template so Anki does not create a look-alike note type.

Put all generated cards into:

```text
Saved Cards
```

Use tags for organization. Do not create topic-specific decks unless the user explicitly asks for that.

Fields:

- `Text`: card prompt, cloze answer, and inline images when the image belongs on the prompt/card itself.
- `Extra`: source context, page screenshot, short discriminator, pitfall, or brief rationale.

Do not put long explanations in `Extra`.
For quiz-derived cards, `Extra` must include a short one-sentence explanation of the tested point after the question number/result metadata. Keep it useful for immediate review: identify what the image/device/finding is and why the answer follows when that context is not obvious.
Do not generate quiz-derived APKGs as an automatic tail step of quiz capture unless the user explicitly requests cards, a deck, Anki generation, or an APKG. Capture/review and card-writing are separate passes.
Do not create card fronts by truncating source stems. Rewrite concise, complete prompts. No prompt should end mid-sentence.
When the user or source note already provides a concise, grammatical card prompt, preserve that wording unless there is a concrete defect to fix, such as ambiguity, excessive length, missing required context, source provenance on the front, or broken grammar. Do not convert a clear question into a telegraphic label-fragment style merely to make it shorter.
When a user-authored Notion/database note already lays out a card in question/answer form, treat that wording as the primary specification rather than raw source material. Preserve the prompt structure and answer wording exactly when it is already intelligible, especially for intentionally parallel series such as `How does X appear on bone scintigraphy? -> normal activity`. If the user writes `similar cards for the following`, create cards using the same preceding structure so the cards remain parallel and do not leak clues through inconsistent wording. Curly-brace/cloze-like markup in the source note is a clue to keep the enclosed content together unless there is a clear technical reason not to.
Do not use `Answer:` or `Key answer:` fallback cards. Convert the tested point into a real cloze fact or a direct image prompt, or skip it.
Image-front quiz cards should usually test diagnosis, device/artifact recognition, or labeled structure identification. Do not use image fronts for multi-step management questions when the image first requires a diagnosis.
If the source quiz provides a `Vital Concept` or similarly labeled key concept, copy it word-for-word into `Extra` whenever technically possible. Put it after the question number/result metadata and before appended images.
Do not fill `Extra` prose with peer-comparison percentages. Avoid lines such as `correct answer chosen by X% of peers` or `selected answer chosen by Y% of peers`; these do not teach the tested concept. For BoardVitals-style question-context screenshot images included in `Extra`, preserve the per-choice percentages next to each answer choice because the screenshot is meant to mirror the local review page context.
Do not put source provenance in front-side `Text`. Source names, app names, article titles, quiz names, question numbers, and batch identifiers belong in `Extra`, `README.md`, or `manifest.json`, not in the repeated study prompt.
Do not include multiple-choice answer letters in `Text`; package the actual tested answer only.
For image cards, use concise but natural prompts rather than stilted label fragments. When clinical information is relevant, write a brief patient/context sentence followed by the actual task, usually `Most likely diagnosis?` for diagnosis cards. Example style: `36-year-old woman with diffuse bone pain and asymmetric breast uptake on bone scintigraphy. Most likely diagnosis?` Avoid constructions such as `Bone scintigraphy: asymmetric breast uptake. Diagnosis?` unless the source itself is a labeled diagram or device-identification prompt where that wording is genuinely clearer.
If more than one image appears on the front of a card, add `1/N` immediately above the first image.
For quiz review packages, include one additional misconception note for each missed question. This note should be derived from the user's selected wrong answer and should test the key term, definition, discriminator, or false association behind that miss.
For quiz-derived packages, card drafting may occur in separate content-type passes to preserve writing consistency, but APKG note insertion must be reordered before export by source question number. Keep each question's cards together, in the order image-front card, focused fact card, then misconception card when those cards exist. This order controls how a newly imported package appears when initially reviewed by creation/order in Anki.
For every saved quiz capture/review workflow, the last artifact should be a standalone local HTML quiz-review page rebuilt from the saved local data. Do not revisit the source website just to make this page. The page should use a dark-mode visual style by default. The page should show all questions top-to-bottom with local images, selected answer, correct answer, result/difficulty metadata, explanations, and any Vital Concept text. Show the peer percentage for each answer choice as a small right-aligned parenthetical badge inside that answer choice row. Include a question-number prefix filter, a separate word-search filter, and a result/sort control with `All`, `Incorrect`, and `Hardest` modes. `Hardest` should sort questions by the percentage of peers who chose the correct answer, ascending from lowest correct-answer percentage to highest. Clean the source snapshot so accessibility/DOM noise such as `Radio Selected`, `Radio Unselected`, `img`, checkbox state, and heading level markers never appears in the visible quiz text.
When extracting or rebuilding quiz stems, preserve every stem paragraph before the answer choices. Do not stop at the first long paragraph. Join short follow-up lines, lab values, and final question lines into the visible stem so clinical context such as age, symptoms, lab values, and the actual asked task is not silently dropped.

## Media Rules

- Every referenced image must exist as a real local file.
- Package images by filename and reference them with `<img src="filename.ext">`.
- Do not reference remote URLs in card HTML.
- Include every local image file referenced by card HTML in the package media list.
- If multiple images belong on one note, include all of them in order.
- If an image belongs only as answer-side support, put it in `Extra`.
- If a source question or item contains images that are not already present on the front of a generated card, append all of those images after the text in `Extra`.
- For quiz-derived cards, begin `Extra` with the source question number in the format `Q<number>`.
- Include a full source-page screenshot in `Extra` whenever feasible.
- When a quiz workflow generates question-context or explanation screenshot cards for `Extra`, use the same compact dark framed renderer as its local review page: size the image from measured wrapped text lines with only a small minimum height, avoiding large blank tails. The copied review-page screenshot pack and packaged Anki media should follow the same crop behavior.
- BoardVitals question-context screenshot images should include selected/correct labels and per-answer percentages. Do not replace this with separate peer-comparison prose in the `Extra` field.
- For BoardVitals-derived cards, append a direct published GitHub Pages review-page link at the very end of `Extra`, after all text and images. Use the public Library URL, not `127.0.0.1` or a local file path, so the link works from AnkiMobile and other devices. The link should include the question anchor, e.g. `https://starfox1230.github.io/The-Library/apps/anki-card-creation-codex-helper/boardvitals/<date>-quiz-<quiz-id>/quiz-<quiz-id>-review.html#q17`, so the card opens the full review page scrolled directly to the source question.
- Front-side diagnosis images must include the complete diagnostic figure or all relevant panels, while excluding figure captions.
- Do not crop front-side diagnosis images so tightly that distribution, multiplicity, anatomy, or comparison information is lost.
- Captions may inform card creation, but caption text should not appear in the front-side `Text` field.

## Build Rules

- Use stable GUIDs so reruns do not create needless duplicate notes.
- Validate note keys before building.
- Validate cloze syntax before building.
- Validate tag format before building.
- Validate media references before building.
- A package build failure blocks any claim that the APKG is ready.
- For workflows that update upstream status, do not mark source items as completed unless the APKG builds successfully.

## Radiographics Details To Preserve

The Radiographics builder:

- Uses a `saCloze++` model with `Text` and `Extra` fields.
- Uses `genanki`.
- Includes all local figure media paths from the article payload.
- Adds article/source context and a figure appendix to `Extra`.
- Has tests that catch weak disease, technique, and image-card behavior.

Those ideas should be reused for Core Radiology and other future card-generation workflows.

For this helper, preserve the manifest and media practices from Radiographics, and use `saCloze++` and `Saved Cards` unless the user says otherwise.
