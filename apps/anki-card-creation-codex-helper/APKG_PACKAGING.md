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

Use the user's existing `saCloze+` style by default for all generated packaged cards. Do not switch to `saCloze++` unless the user explicitly asks for it or a specific existing workflow requires it.

Put all generated cards into:

```text
Saved Cards
```

Use tags for organization. Do not create topic-specific decks unless the user explicitly asks for that.

Fields:

- `Text`: card prompt, cloze answer, and inline images when the image belongs on the prompt/card itself.
- `Extra`: source context, page screenshot, short discriminator, pitfall, or brief rationale.

Do not put long explanations in `Extra`.

## Media Rules

- Every referenced image must exist as a real local file.
- Package images by filename and reference them with `<img src="filename.ext">`.
- Do not reference remote URLs in card HTML.
- Include every local image file referenced by card HTML in the package media list.
- If multiple images belong on one note, include all of them in order.
- If an image belongs only as answer-side support, put it in `Extra`.
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

For this helper, preserve the manifest and media practices from Radiographics, but prefer `saCloze+` and `Saved Cards` unless the user says otherwise.
