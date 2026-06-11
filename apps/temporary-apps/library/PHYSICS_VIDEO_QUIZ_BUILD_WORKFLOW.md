# Physics Video Transcript Quiz Build Workflow

Use this workflow for the X-ray, CT, MRI, and ultrasound transcripts registered in `apps/core-studying/YT Physics/index.json`.

## Organization

- Keep the source transcripts unchanged under `apps/core-studying/YT Physics/`.
- Treat one video transcript as one independently saved quiz app.
- Place apps under `apps/temporary-apps/library/physics-video-quizzes/<modality>/<YYYY-MM-DD-video-slug>/`.
- Update the modality sections in `apps/temporary-apps/library/physics-video-quizzes/index.html`.
- All modality accordions are closed for a first-time visitor. Persist the user's open sections in local storage.
- Register the collection landing page and every generated quiz in `apps/temporary-apps/index.html`.

## Source Handling

1. Use `index.json` as the authoritative video order, title, and transcript path.
2. Read each transcript header to preserve its source-video URL.
3. Remove timestamps only for analysis; do not interpret them as content.
4. Review the entire transcript before finalizing coverage. Later examples and summary sections often contain qualifications that are absent from the introduction.
5. Resolve speech-to-text errors from context and established terminology. Omit a scored fact if the transcript remains ambiguous.
6. Link the source video from the quiz and record both the transcript path and video URL in its README.

## Question Authoring

- Follow `DOCUMENT_TO_QUIZ_BUILD_WORKFLOW.md`.
- Build a concise coverage outline for each video, then write one-best-answer questions for the major concepts, causal relationships, formulas, parameter tradeoffs, and common confusions.
- Do not copy transcript phrasing mechanically or prefix stems with "According to the video."
- Use distractors that represent believable MRI, CT, ultrasound, or X-ray physics misconceptions on the same conceptual dimension.
- Do not create answer choices by reversing a range, changing capitalization, using malformed units, or making the correct choice uniquely detailed.
- Keep learning objectives in the curated bank even if they are not displayed in the app.
- Explanations should identify the governing principle and distinguish the most tempting alternative.

## Application Behavior

- Use night mode by default.
- Start with Tutor mode, no selected or submitted answers, and the question navigator closed.
- Preserve Tutor mode, Quiz mode, review, reset, state JSON copy/download/import, question copying, and screenshot copying.
- Use a stable app ID and a versioned storage key. Increment the bank version if item order, meaning, or answer keys change.
- Do not add image placeholders when the source transcript has no figures.

## Required QA

1. Validate a one-to-one match between the source manifest and curated quiz bank.
2. Verify every question ID, answer key, option set, explanation, and learning objective.
3. Manually check every numerical value, formula, polarity, directional relationship, and increase/decrease tradeoff against its transcript.
4. Audit answer-position balance and correct-answer length.
5. Search generated HTML for inherited template titles, app IDs, source labels, and save-state placeholders.
6. Compile every generated inline script with Node.
7. Check all landing-page links and source-video links.
8. Test representative early, middle, and late quizzes in both Tutor and Quiz modes, including persistence and reset.
9. Run `python scripts\verify-temporary-apps-index.py`.
10. Commit and push the complete verified collection.
