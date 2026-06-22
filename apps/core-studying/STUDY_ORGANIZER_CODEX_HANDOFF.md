# Core Study Organizer Codex Handoff

Use this file when a Core Study Organizer page copies a schedule or Anki request into Codex.

## Durable schedules

- Store shared schedules under `apps/core-studying/plans/`.
- Preserve the supplied dates, order, section keys, titles, and source paths.
- Use JSON with `schemaVersion`, `id`, `title`, `book`, `startDate`, `endDate`, and `days`.
- Each day contains `date` and `sections`.
- Do not copy source textbook text into the schedule.
- Do not commit completion state unless the user explicitly asks; listen/read/Anki progress remains browser-local by default.

## Anki requests

For Core Radiology, follow:

```text
apps/anki-card-creation-codex-helper/CORE_RADIOLOGY_WORKFLOW.md
```

That workflow points to the canonical card-style and APKG-packaging rules. Inspect the corresponding PDF section and useful figures rather than relying only on extracted text.

For other books or transcript-backed material, follow:

```text
apps/anki-card-creation-codex-helper/CARD_STYLE_GUIDE.md
apps/anki-card-creation-codex-helper/APKG_PACKAGING.md
```

Use the exact source paths supplied by the handoff. Generate a finished APKG only when the request explicitly asks for one.

## Verification

When schedule, book registration, manifest, or generated text files change, run:

```powershell
python scripts/verify_core_studying_books.py
```
