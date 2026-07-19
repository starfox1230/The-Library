# Core Radiology Workflow

Use this for Codex conversations centered on the Core Radiology textbook.

## Primary Textbook

```text
G:\My Drive\0. Radiology\Core Radiology 2nd ed.pdf
```

## Canonical Instructions

Before making cards, read:

```text
C:\Users\sterl\OneDrive\Documents\GitHub\The-Library\apps\anki-card-creation-codex-helper\CARD_STYLE_GUIDE.md
C:\Users\sterl\OneDrive\Documents\GitHub\The-Library\apps\anki-card-creation-codex-helper\APKG_PACKAGING.md
C:\Users\sterl\OneDrive\Documents\GitHub\The-Library\apps\anki-card-creation-codex-helper\VISUAL_STUDY_AND_ANKI_SPEC.md
```

## Default Behavior

- When the user asks a question, open or search the Core Radiology PDF and answer normally from the relevant section.
- Keep the textbook visible in Chrome when the user asks for it.
- Do not generate cards unless the user explicitly asks for Anki cards, cards, a deck, or an APKG.
- When cards are requested, identify the exact source section and relevant figures before drafting cards.

## Card Generation Flow

1. Locate the source section in the textbook.
2. Extract high-yield facts and relevant figures.
3. Draft atomic cloze notes using `CARD_STYLE_GUIDE.md`.
4. Capture the full source page into an `assets\` folder for required `Extra` context on every card derived from that textbook page.
5. Capture or extract relevant diagnosis images into `assets\` only when a clean image crop can be made without the caption.
6. Build `notes.json` and `manifest.json` targeting the `Saved Cards` deck and the user's existing `saCloze++` note type exactly.
7. Build a downloadable `.apkg` using `APKG_PACKAGING.md`.
8. Report the APKG path, note count, source section, and any skipped ambiguous material.

## Core Radiology Image Requirement

For Core Radiology APKG requests, actively inspect the corresponding PDF pages before drafting cards. Do not rely only on the extracted `.txt` section when the source is PDF-backed.

- If the section contains useful diagnostic figures, create image-front cards unless the figure is nondiagnostic, caption-dependent, redundant, too low quality, or cannot be cleanly cropped without caption text.
- For a typical image-rich section, aim for 2-5 image-backed cards plus focused text cloze cards.
- Prefer complete diagnostic images or panel sets over tiny crops. Preserve enough anatomy, distribution, and comparison context to make the diagnosis visually answerable.
- Keep captions out of front-side card images and out of the front-side `Text` field.
- Put the correct full source-page screenshot in `Extra` for every Core Radiology-derived card, including cards created from auto-generated quizzes and nonvisual facts.
- Preserve an exact question-to-PDF-page and candidate-to-PDF-page mapping during quiz generation and card drafting. Do not try to reconstruct the page from topic similarity after the fact.
- If a card genuinely uses multiple textbook pages, include the necessary page screenshots in source order. If a page cannot be identified, captured, or stored, record the exception and never attach a guessed page.
- If no image-front cards are created for a Core Radiology request, explicitly report why in the final handoff and README.
- If PDF page localization is uncertain, still inspect the best matching PDF pages by section heading and note the uncertainty rather than silently falling back to text-only cards.

## Output Location

Use this pattern unless the user specifies another location:

```text
apps\anki-card-creation-codex-helper\core-radiology\<YYYY-MM-DD-topic-slug>\
  notes.json
  assets\
  <topic-slug>.apkg
  README.md
```

Use `apps\temporary-apps\library\core-review\...` only for standalone quiz or reader apps that should appear in the Core Review Quiz Library.
