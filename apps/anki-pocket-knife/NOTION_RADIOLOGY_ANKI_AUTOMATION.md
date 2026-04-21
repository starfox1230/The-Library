# Notion -> Radiology Anki Automation Spec

Last updated: 2026-04-20

## Goal

Create a daily Codex automation that:

1. Finds radiology notes in Notion that are ready for Anki card creation.
2. Generates cards that match the user's actual recent Anki style.
3. Includes any relevant Notion images inside the generated cards.
4. Packages the result as a real `.apkg` file with working media references.
5. Leaves a clean audit trail so the run can be reviewed before trusting it fully.

This document is grounded in direct inspection of:

- The user's live Notion `Radiology Notes Database`
- The user's recent Anki backup from 2026-04-20
- The local `anki-pocket-knife` add-on, especially the existing JSON card import workflow

## Verified observations

### Notion side

The relevant Notion database is `Radiology Notes Database`.

Confirmed properties include:

- `Anki Card` with statuses `Not Needed`, `Needed`, `Created`
- `Length`
- `Category - Nightly Tags`
- `Other Tags`
- `Review Priority - Nightly Tags`

For the first version of this automation, only `Anki Card` is required as a gating property.

Important clarification from the user:

- The automation should look only for `Anki Card = Needed`.
- The other workflow-related checkboxes that appeared in the fetched schema should not be treated as required triggers.

Confirmed workflow evidence in related Notion pages:

- There is a real `Needs Anki` view.
- One workflow page explicitly breaks the process into:
  - read lecture summary
  - copy/paste key facts into OpenAI card creator
  - add lecture images to Anki cards
  - review new cards

That workflow evidence is useful for understanding the existing process, but it should not narrow the first automation's selection logic beyond `Anki Card = Needed`.

### Anki side

Direct inspection of the latest Anki backup on 2026-04-20 found:

- Recent 200 notes:
  - `117` notes of type `saCloze+`
  - `77` notes of type `saCloze++`
  - `6` notes of type `Visual_Card_Multitude`
- `158 / 200` recent notes contained inline images.
- `60 / 200` recent notes were visual diagnosis-style prompts.
- `72 / 200` recent notes used the `Extra` field.
- Average recent image count was `1.66` per note, with a maximum of `7`.
- Average recent cloze count was `1.14` per note, with a maximum of `3`.

Recent deck usage was concentrated in:

- `.NEW::Visual`
- `.NEW::Audio`
- `Recent new cards 2026-04-17 23-36-31`

Confirmed note type structures:

- `saCloze+`
  - fields: `Text`, `Extra`
- `saCloze++`
  - fields: `Text`, `Extra`

Confirmed field behavior:

- Visual cards embed media directly in `Text` as HTML like `<img src="paste-...jpg">`
- Some cards place additional supporting images or reasoning in `Extra`
- The visual-card style often uses prompts like `Most likely diagnosis?`

## Observed card-style rules

These are not guesses. They are based on the recent backup sample.

### Text-first cards

Use `saCloze+` when the source is mostly conceptual or factual and does not need images.

Observed characteristics:

- Usually one sentence or one short prompt
- Usually one to two clozes
- Sometimes three clozes when the fact naturally bundles name, timing, and disease state
- Often highly atomic
- Often split into separate cards rather than one overloaded comparison card

Observed examples:

- `A left ventricular {{c1::pseudo}} aneurysm classically has a {{c2::narrow}} neck.`
- `{{c1::An acute peripancreatic fluid collection, or APFC::What collection}} occurs {{c2::within 4 weeks of::when in}} {{c3::interstitial edematous pancreatitis}}.`

### Visual diagnosis cards

Use `saCloze++` when images are important.

Observed characteristics:

- Prompt often starts with `Most likely diagnosis?`
- Sometimes adds anatomical or clinical context:
  - `Most likely diagnosis in the pancreas?`
  - `59-year-old woman with post cholecystectomy pain. Most likely diagnosis?`
- Usually one diagnosis cloze
- Images are appended below the prompt and answer block
- `Extra` is used for discriminators or short reasoning, not for a full explanation
- Multi-image cards are common

Observed examples:

- `Most likely diagnosis?<br><br>{{c1::Hepatic steatosis...}}<br><br><img src="...">`
- `Most likely diagnosis in the pancreas?<br><br>{{c1::MCN}}`

### General style constraints

- Default to cloze notes, not basic cards.
- Prefer one idea per note.
- Avoid padding or textbook phrasing.
- Use abbreviations when they are standard in radiology study language.
- Preserve clinical stems only when they help identify the diagnosis.
- Use `Extra` only when it adds a discriminator, pitfall, or short rationale.
- If a comparison naturally splits into two cards, split it.

## Recommended automation design

Use one daily project automation plus one optional weekly style-refresh task.

### Daily automation

Purpose:

- Build that day's `.apkg`
- Include media
- Write a run report
- Leave enough evidence for manual review

Recommended outputs for each run:

- `output/anki-daily/YYYY-MM-DD/radiology-daily.apkg`
- `output/anki-daily/YYYY-MM-DD/run-report.md`
- `output/anki-daily/YYYY-MM-DD/cards.json`
- `output/anki-daily/YYYY-MM-DD/media/`

### Optional weekly style refresh

Purpose:

- Re-sample the most recent 200 to 500 Anki notes
- Update a small `style-profile.md` snapshot
- Detect if the user's card habits changed

This matters because the user's recent cards are visibly style-consistent, and that style may drift over time.

Helper script now available in this repo:

- `scripts/anki_recent_style_snapshot.py`

Example:

```powershell
py .\scripts\anki_recent_style_snapshot.py --profile Default --limit 200 --output .\output\anki-style\latest.json
```

## Proposed processing rules

### Row selection

Primary filter:

- Process pages where `Anki Card = Needed`

Secondary prioritization:

- Prefer pages surfaced in the `Needs Anki` view
- Use `Review Priority - Nightly Tags` if present
- Prefer shorter source notes first when batching if the run has a cap

### Content extraction

For each selected Notion page:

1. Retrieve full page content.
2. Extract image/file blocks while the pre-signed URLs are still valid.
3. Save images into the run-local `media/` folder.
4. Distill the page into candidate facts and candidate visual diagnoses.

### Card generation

The generator should decide between:

- `saCloze+` style text cards
- `saCloze++` style image-backed cards

Rules:

- If the page contains diagnostically important images, create image-backed cards.
- If the page is mostly teaching text, create atomic cloze cards.
- If a page supports both, create both kinds, but keep each note narrow.
- Do not create cards just because text exists; skip low-yield filler.

### Media handling

Rules:

- Every referenced image must exist as a real file in the package media map.
- Card HTML must reference media by packaged filename, not a remote Notion URL.
- If multiple images belong on one note, include all of them in order.
- If one image belongs on the answer side only, place it in `Extra`.

### Status updates after successful package generation

Only after the `.apkg` is built successfully:

- Change `Anki Card` from `Needed` to `Created`

If package generation fails, do not update the page status.

## Package contract

The run should produce a machine-readable card manifest before building the package.

Builder script now available in this repo:

- `scripts/build_manifest_apkg.py`

Example:

```powershell
py .\scripts\build_manifest_apkg.py --manifest .\output\anki-daily\2026-04-20\cards.json --output .\output\anki-daily\2026-04-20\radiology-daily.apkg
```

Recommended manifest shape:

```json
[
  {
    "source_page_id": "notion-page-id",
    "source_title": "Page title",
    "deck_name": ".NEW::Visual",
    "note_type_style": "saCloze++",
    "fields": {
      "Text": "Most likely diagnosis?<br><br>{{c1::...}}<br><br><img src=\"image-001.jpg\">",
      "Extra": "short discriminator"
    },
    "tags": [
      "#AnkiChat::2026.04.20_Topic",
      "Radiology",
      "Pancreas"
    ],
    "media_files": [
      {
        "filename": "image-001.jpg",
        "local_path": "output/anki-daily/2026-04-20/media/image-001.jpg"
      }
    ]
  }
]
```

The manifest should exist even if the final output is an `.apkg`, because it makes review and debugging much easier.

## Important implementation note

The local `anki-pocket-knife` add-on already contains a real importer for clipboard JSON cards:

- file: `clipboard_json_cards.py`
- parser: `clipboard_json_cards_core.py`

That importer already accepts arrays of card objects with `html` and `tags`, and inserts them into `saCloze++`.

This does not replace `.apkg` packaging, but it is useful in two ways:

1. It confirms that JSON card objects map naturally onto the user's real Anki workflow.
2. It gives a fallback import route if the `.apkg` builder needs troubleshooting.

There is also a separate prior-art automation outside this repo in `G:\My Drive\Codex Automations` that already proved out the `genanki` packaging path.

What to reuse from that project:

- manifest/article payload -> Python packaging step
- stable GUIDs
- real packaged media files
- package build failure should block status updates

What not to reuse from that project:

- naive summarization from raw abstract sentences
- naive summarization from figure captions
- prompts like `High-yield takeaway?` or `Key teaching point?` as default card stems
- one-cloze wrapping of long raw prose

The quality failure in that older automation is upstream, not in the `.apkg` writer:

- `src/summarize.js` builds `keyFacts` by taking long abstract sentences or figure-caption sentences
- `scripts/build_anki_package.py` then wraps those strings into simple cloze cards

For the radiology Notion workflow, card text must be rewritten into the user's actual observed style before the package step.

## Daily automation prompt

Use this as the durable Codex automation prompt.

```md
Build today's radiology Anki package from the Notion Radiology Notes Database.

Use the actual user style reflected in recent Anki cards:

- Default to cloze cards.
- Prefer atomic cards.
- Use short, direct wording.
- Use `saCloze+` style for text-only facts.
- Use `saCloze++` style for visual diagnosis cards.
- Visual cards usually use prompts like `Most likely diagnosis?`, `Most likely diagnosis in the pancreas?`, or a short clinical stem plus `Most likely diagnosis?`.
- Put short discriminators in `Extra` only when they add value.
- Do not write long explanations.
- Split overloaded facts into multiple notes when needed.

Select candidate pages from the user's Notion Radiology Notes Database where:

- `Anki Card` is `Needed`

Do not require any additional checkbox fields to be set.

When a page is selected:

1. Retrieve the page content and any relevant images.
2. Download relevant Notion images immediately during the same run.
3. Distill the page into high-yield candidate cards.
4. Generate cards that match the user's actual style.
5. Include images inside cards when they are diagnostically important.
6. Build a real `.apkg` package with working media references.
7. Write a run report that lists:
   - processed pages
   - skipped pages
   - generated cards
   - any ambiguous cards that need review
8. Save outputs in a dated folder under `output/anki-daily/YYYY-MM-DD/`.

Required outputs:

- `radiology-daily.apkg`
- `cards.json`
- `run-report.md`
- downloaded media files

Quality rules:

- No filler cards.
- No cards that merely restate the page title.
- No giant multi-fact cards.
- Keep most text cards to one sentence or one short prompt.
- Usually use one to two clozes, only using three when the structure naturally calls for it.
- For visual cards, use one diagnosis cloze plus image support.
- If the distinction between two entities is important, prefer separate cards.
- If a card is weak or ambiguous, skip it and mention the skip in the report.

State updates:

- Only after the `.apkg` builds successfully, update the source Notion page from `Anki Card = Needed` to `Anki Card = Created`.
- Do not update Notion statuses if package generation fails.

If the run finds no good candidate pages, write a short report explaining why and stop without making status changes.
```

## Validation plan before full unattended use

Do not trust the first unattended daily run.

Run this sequence first:

1. Dry run on `5` real `Needed` pages.
2. Compare generated cards against the user's actual recent cards.
3. Verify:
   - correct deck choice
   - correct card type choice
   - image placement
   - `Extra` field discipline
   - tag quality
   - no broken media
4. Import the `.apkg` into a test profile or temporary deck.
5. Only then enable the daily schedule.

## Remaining unknowns

These are the main unresolved items:

- Exact preferred daily run time
- Whether the automation should hard-cap cards per day
- Whether `Category - Nightly Tags` and `Other Tags` should map directly into Anki tags or only partially
- Whether the package should try to mirror the user's exact in-collection note templates or use a dedicated exported model that mimics the observed style

## Supporting references

- Codex automations: <https://developers.openai.com/codex/app/automations>
- GPT-5.4 model docs: <https://developers.openai.com/api/docs/models/gpt-5.4>
- Prompt guidance: <https://developers.openai.com/api/docs/guides/prompt-guidance>
- Notion markdown content and file handling: <https://developers.notion.com/guides/data-apis/working-with-markdown-content>
- Notion request limits: <https://developers.notion.com/reference/request-limits>
- Anki media in fields: <https://docs.ankiweb.net/templates/fields.html#media-latex>
- genanki: <https://github.com/kerrickstaley/genanki>
