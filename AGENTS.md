# Repository Instructions for Bots and Contributors

## When adding a temporary app
If you create or modify an app under `apps/temporary-apps/library/`, you **must** do all of the following in the same change:

1. Add/update the app files in `apps/temporary-apps/library/YYYY-MM-DD-slug/`.
2. Register the app in `apps/temporary-apps/index.html` by adding/updating an item in `TEMP_APPS`.
3. Ensure the root landing page keeps a link to `apps/temporary-apps/index.html` in `index.html`.
4. Run:
   - `python3 scripts/verify-temporary-apps-index.py`

Do not consider the task complete unless the verification script passes.

### Core Review quiz apps
If the temporary app is a Core Review radiology quiz, do **not** create a new top-level `apps/temporary-apps/library/YYYY-MM-DD-slug/` folder unless the user explicitly asks for a legacy duplicate.

New Core Review quiz chapters must live only under:

```text
apps/temporary-apps/library/core-review/<book-slug>/<YYYY-MM-DD-chapter-slug>/
```

For these Core Review quiz apps, the same change must also update `apps/temporary-apps/library/core-review/index.html` so the chapter appears in the grouped Core Review Quiz Library. Register the organized `library/core-review/.../index.html` path in `apps/temporary-apps/index.html`, not a root-level duplicate.

## Why this exists
A previous change added a temporary app folder but forgot to update the landing-page registration path. These instructions and the verifier prevent that regression.

## When modifying `apps/core-studying`
If a task touches `apps/core-studying/`, read `apps/core-studying/AGENTS.md` before making changes.

For book registration, manifest, or generated text changes under `apps/core-studying/`, run:
- `python scripts/verify_core_studying_books.py`

Do not consider those changes complete unless the verifier passes.
