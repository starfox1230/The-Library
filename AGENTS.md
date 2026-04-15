# Repository Instructions for Bots and Contributors

## When adding a temporary app
If you create or modify an app under `apps/temporary-apps/library/`, you **must** do all of the following in the same change:

1. Add/update the app files in `apps/temporary-apps/library/YYYY-MM-DD-slug/`.
2. Register the app in `apps/temporary-apps/index.html` by adding/updating an item in `TEMP_APPS`.
3. Ensure the root landing page keeps a link to `apps/temporary-apps/index.html` in `index.html`.
4. Run:
   - `python3 scripts/verify-temporary-apps-index.py`

Do not consider the task complete unless the verification script passes.

## Why this exists
A previous change added a temporary app folder but forgot to update the landing-page registration path. These instructions and the verifier prevent that regression.

## When modifying `apps/core-studying`
If a task touches `apps/core-studying/`, read `apps/core-studying/AGENTS.md` before making changes.

For book registration, manifest, or generated text changes under `apps/core-studying/`, run:
- `python scripts/verify_core_studying_books.py`

Do not consider those changes complete unless the verifier passes.
