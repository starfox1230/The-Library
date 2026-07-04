# Review Later Analysis Build Workflow

Use this workflow when the user provides an Anki-style "Review Later" HTML export and asks for a learning resource from the missed/flagged cards.

## Naming and placement

- App title format: `Review Later Analysis - YYYY-MM-DD` or a domain-specific variant such as `Review Later Radiology Analysis - YYYY-MM-DD`.
- Folder format: `apps/temporary-apps/library/YYYY-MM-DD-review-later-analysis/` unless a more specific slug is useful.
- Register the app in `apps/temporary-apps/index.html`.
- Keep the root landing page link to `apps/temporary-apps/index.html`.
- Run `python3 scripts/verify-temporary-apps-index.py`.
- Commit and push the completed temporary app change.

## Extraction

1. Parse the exported HTML into card entries with front, back, tags, source deck/model, and added date when available.
2. Remove Anki timer/audio/control noise.
3. Preserve the user's tags because they become the top navigation filters.
4. Infer the actual tested concept from the front/back pair, not only from the cloze text.
5. Group modules by broad tags/domains, but default the app to `All`.

## Teaching standard

Each module should be a true refresher, not a short answer key.

Required module fields:

- `title`: concise concept name.
- `domain`: tag/category used by the filter chips.
- `source`: card number or deck/tag source.
- `prompt`: original card prompt, lightly cleaned.
- `answer`: main point of the card.
- `refresher`: substantial contextual explanation. Define key words and explain why the answer is true.
- `structure`: major components, classification branches, testable distinctions, or decision points.
- `basics`: short anchors that make the card easy to remember.
- `foils`: likely wrong answer choices or neighboring concepts, each with why it is different.
- `quiz`: one quick check question with choices, answer, and explanation.
- `image` or `imageReason`: use one of these for every module.

## Visual policy

- Do not use SVGs, generated illustrations, or AI-created visuals.
- Use only real images obtained online.
- Do not force an image for every concept.
- Use images only when they clearly teach the intended concept better than text alone.
- Prefer open-access medical/academic pages, Wikimedia image files, reputable teaching sites, or source pages with a clear caption.
- Evaluate the image visually and conceptually:
  - Does it show the exact finding/concept?
  - Is it clear on mobile?
  - Is it high enough quality?
  - Does the caption/source support the intended interpretation?
  - Would it mislead by showing only a partial or adjacent concept?
- If no image passes that bar, set `imageReason` and display a "No image forced" panel.

## App layout requirements

- Mobile-first, dark, compact, and readable.
- Top header includes date/source and summary stats.
- Sticky controls include search and tag chips.
- `All` is the default filter.
- Module list should be easy to scan and horizontally scroll on mobile.
- Active module layout:
  - Prompt and main point.
  - Mark understood button.
  - Next card button.
  - Real image card or no-image rationale.
  - Refresher.
  - Topic Structure.
  - Card Anchor.
  - Likely Foils.
  - Quick Check.
  - Reference Trail.
- Keep local progress in `localStorage` with a versioned key.

## Copy controls

Every explanatory section must have a small `Copy` button at the top right of the section header.

Required section copy targets:

- Refresher.
- Topic Structure.
- Card Anchor.
- Likely Foils.
- Quick Check.

Also include a small fixed button labeled `Copy explanation` that scrolls with the viewport and copies the full active module as plain text.

The copied full explanation should include:

- Title, domain, and source.
- Prompt and main point.
- Image caption/source or no-image rationale.
- Refresher.
- Topic Structure.
- Card Anchor.
- Likely Foils.
- Quick Check with correct answer and explanation.

## Verification

Before committing:

- Run `python3 scripts/verify-temporary-apps-index.py`.
- Browser-test desktop and mobile widths.
- Confirm no console errors.
- Confirm no page-wide horizontal overflow on mobile.
- Confirm no `<svg>` elements are present.
- Confirm all selected online images load.
- Confirm every module has either one selected real image or a no-image rationale.
- Confirm section copy and `Copy explanation` work.
- Confirm `Mark understood` and `Next card` still work.

## Current example

Use `apps/temporary-apps/library/2026-07-04-review-later-radiology-basics/index.html` as the current best example of the desired look and behavior.
