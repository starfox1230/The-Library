# Canonical APKG Packaging Guide

Use this as the source of truth for APKG, media, manifest, and build behavior.

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
Do not put source provenance in front-side `Text`. Source names, app names, article titles, quiz names, question numbers, and batch identifiers belong in `Extra`, `README.md`, or `manifest.json`, not in the repeated study prompt.
Do not include multiple-choice answer letters in `Text`; package the actual tested answer only.
For image cards, use concise task-specific prompts rather than generic catch-all prompts. If more than one image appears on the front of a card, add `1/N` immediately above the first image.
For quiz review packages, include one additional misconception note for each missed question. This note should be derived from the user's selected wrong answer and should test the key term, definition, discriminator, or false association behind that miss.

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
