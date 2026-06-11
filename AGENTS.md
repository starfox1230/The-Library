# Repository Instructions for Bots and Contributors

## When adding a temporary app
If you create or modify an app under `apps/temporary-apps/library/`, you **must** do all of the following in the same change:

1. Add/update the app files in `apps/temporary-apps/library/YYYY-MM-DD-slug/`.
2. Register the app in `apps/temporary-apps/index.html` by adding/updating an item in `TEMP_APPS`.
3. Ensure the root landing page keeps a link to `apps/temporary-apps/index.html` in `index.html`.
4. Run:
   - `python3 scripts/verify-temporary-apps-index.py`

Do not consider the task complete unless the verification script passes.

After completing and verifying a temporary app change, commit the completed work and push the commit to GitHub. Keep the commit scoped to the app and its required registrations/documentation; do not include unrelated working-tree changes.

### Core Review quiz apps
If the temporary app is a Core Review radiology quiz, do **not** create a new top-level `apps/temporary-apps/library/YYYY-MM-DD-slug/` folder unless the user explicitly asks for a legacy duplicate.

New Core Review quiz chapters must live only under:

```text
apps/temporary-apps/library/core-review/<book-slug>/<YYYY-MM-DD-chapter-slug>/
```

For these Core Review quiz apps, the same change must also update `apps/temporary-apps/library/core-review/index.html` so the chapter appears in the grouped Core Review Quiz Library. Register the organized `library/core-review/.../index.html` path in `apps/temporary-apps/index.html`, not a root-level duplicate.

Before generating or fixing any Core Review quiz, read and follow `apps/temporary-apps/library/RADIOLOGY_QUIZ_BUILD_WORKFLOW.md`. That workflow includes required image-alignment QA steps learned from prior PDF/EPUB conversions.

When creating original quizzes from the informational content of a source document rather than extracting prewritten questions, also read and follow `apps/temporary-apps/library/DOCUMENT_TO_QUIZ_BUILD_WORKFLOW.md`.

### Physics video transcript quiz apps
Quizzes authored from the transcript collection under `apps/core-studying/YT Physics/` must live only under:

```text
apps/temporary-apps/library/physics-video-quizzes/<modality>/<YYYY-MM-DD-video-slug>/
```

The same change must update `apps/temporary-apps/library/physics-video-quizzes/index.html`, which is the grouped landing page for X-ray, CT, MRI, and ultrasound video quizzes. Register the organized `library/physics-video-quizzes/.../index.html` paths in `apps/temporary-apps/index.html`.

Before authoring these quizzes, read and follow both `apps/temporary-apps/library/DOCUMENT_TO_QUIZ_BUILD_WORKFLOW.md` and `apps/temporary-apps/library/PHYSICS_VIDEO_QUIZ_BUILD_WORKFLOW.md`. Treat each transcript as a source chapter, keep the authored bank separate from the renderer, start with empty answers, and use a versioned save key whenever the bank changes.

## Why this exists
A previous change added a temporary app folder but forgot to update the landing-page registration path. These instructions and the verifier prevent that regression.

## When modifying `apps/core-studying`
If a task touches `apps/core-studying/`, read `apps/core-studying/AGENTS.md` before making changes.

For book registration, manifest, or generated text changes under `apps/core-studying/`, run:
- `python scripts/verify_core_studying_books.py`

Do not consider those changes complete unless the verifier passes.
