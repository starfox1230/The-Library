# Core Studying Instructions

## When modifying `apps/core-studying`
If a task touches `apps/core-studying/`, assume the Textbook Copier and Study Organizer may both depend on the same book registration and manifest structure.

## Registration checklist for a new book
When adding a new book or PDF-backed text corpus, do all of the following in the same change:

1. Create or update the book folder under `apps/core-studying/<Book Folder>/`.
2. Ensure the folder contains the generated text assets plus an `index.json` manifest.
3. Register the book in `apps/core-studying/books.json` with:
   - `basePath`: the directory the app should prepend when fetching section text files
   - `manifest`: the path to the book's `index.json`
4. Run:
   - `python scripts/verify_core_studying_books.py`

Do not consider the task complete unless the verifier passes.

## Preferred workflow for PDF-backed books
- Prefer a repeatable script in `scripts/` over hand-editing dozens of `.txt` files.
- If the PDF has a usable bookmark outline, prefer generating sections from the outline rather than splitting manually.
- If the PDF outline is missing or only chapter-level, build a curated section map from the printed table of contents plus the visible subsection headings in the extracted text.
- Treat bookmark or outline page numbers as search hints, not final boundaries.
- Split sections on the visible heading line in the extracted text whenever possible, even if the bookmark lands on the prior page.
- Validate boundaries after generation: each non-intro section file should begin with its own heading, not the tail of the previous section.
- Keep generated text UTF-8 and copy-pasteable. Strip repeated headers/footers/page numbers when possible.
- If the PDF outline has OCR glitches or mojibake, fix them in the generator with explicit overrides rather than hand-patching generated text.
- When curating a manual section map, prefer matching exact visible heading strings with page hints in the generator rather than hard page splits.
- Keep the source PDF in the book folder when it is part of the workflow for regeneration.

## Manifest shapes supported by the app
The app supports either of these chapter shapes:

1. Flat chapter entries:
   - root chapter object contains `"title"` plus direct section keys whose values have `"title"` and `"file"`
2. Nested chapter entries:
   - root chapter object contains `"title"` and a `"sections"` object
   - optional `"introFile"` and `"introTitle"` are supported

Examples already in this repo:
- `Neuroradiology Core Requisites`: flat chapter entries with `TXT/...` files
- `Brant and Helms`: nested `"sections"` plus `"introFile"`
- `Nuclear Medicine - The Requisites`: outline-driven generated `TXT/...` files with heading-based subsection boundary detection

## Notes for future agents
- `apps/core-studying/index.html` is the Textbook Copier UI and is the source of truth for supported manifest fields.
- `apps/core-studying/study-organizer.html` also reads `books.json` and the same manifests.
- `scripts/generate_nuclear_medicine_requisites.py` is a good example of an outline-driven PDF import.
- `scripts/generate_war_machine_physics.py` is a good example of a manually curated heading-map import when the PDF outline is too coarse.
- `scripts/generate_core_studying_abr_guides.py` is a good example of a page-range/marker-driven import.
