# Radiology Quiz Build Workflow

Use this note when converting Core Review PDF or EPUB chapters into the temporary quiz apps.

## Image Alignment Is Mandatory

Do not rely on automatic page adjacency for images. These books commonly place a stem at the bottom of one page, one or more images on the following page, and answer choices after the image. They also place answer choices for one question above the next question's stem on the same page.

Treat image mapping as a diagnostic QA task, not as a parsing side effect. A quiz can have no missing assets and still be wrong if adjacent images are inverted.

For every chapter:

1. Print each chapter page's text lines with PDF page index, displayed PDF page number, and image count.
2. Generate a contact sheet of all extracted images for the chapter's question pages.
3. Generate a separate contact sheet of all extracted images for the answer/explanation pages.
4. Manually map each image by `(page_index, image_index)` to question IDs. Do not use only page-level maps when a page has more than one image.
5. Rebuild and print every question's `number`, `stem` prefix, `answer`, `images`, and `explanationImages`.
6. Make a final per-question contact sheet that groups, in order, each question's prompt image(s) and explanation image(s). Visually compare the grouped images against the stem and answer explanation before delivery.
7. Specifically inspect pages where:
   - a stem says `image`, `images`, `below`, `radiograph`, `CT`, `MRI`, `MR`, `ultrasound`, or `scan`;
   - a page has answer choices for one question and a new stem below;
   - a page is image-only or mostly image-only;
   - a page has multiple unrelated images;
   - two adjacent questions or subquestions are on the same page;
   - one question has multiple patient panels, time points, or modality panels;
   - labels such as `current`, `prior`, `6 months prior`, sequence names, or figure captions could be misread as question text.
8. If a cue word appears in a stem but no image is attached, either fix it or document why it is a conceptual wording cue rather than a supplied figure.
9. If a question has an image that belongs to a neighboring question, fix the map before final validation.

The image checks must include both directions:

- Prompt-side images: match the question stem, answer choices, and any patient/time-point language.
- Explanation-side images: match the answer header and explanation text. Do not assume the explanation image order matches the prompt image extraction order.

When two neighboring image diagnoses are visually similar, use the answer text to sanity-check the mapping. Example: if q6 asks for bilateral C2 pedicle fractures/Hangman injury and q7 asks for a C1 Jefferson fracture, verify that q6 images show C2 pedicle/pars fractures and q7 images show the C1 ring/burst fracture, rather than accepting the source extraction order.

The common failure pattern is an off-by-one image shift. Examples already encountered:

- Chapter 2 MSK Normal/Normal Variants: q2 incorrectly received q3's first radial-head image; q3 needed both page 60 and page 61 images.
- Chapter 3 MSK Congenital/Developmental: q3/q4, q13/q14, and q19/q20 had continuation-page shifts before manual correction.
- Chapter 4 MSK Infection: the text `6 months prior` had to be excluded as a false question number, and q12's CT image appeared on the answer-section boundary page.
- Chapter 5 MSK Tumors: long chapters can have dozens of mixed pages. Use active-question mapping plus explicit page overrides, and make `b`/`c` subparts inherit `a` images when the subpart asks management or histology for the same lesion.
- Chapter 4 Nuclear Medicine Head and Neck: PDF page 158 had two unrelated question images on the same page. The first belonged to q8 and the second belonged to q9a, so the generator needed a per-image split map instead of a page-level map.
- Chapter 5 Nuclear Medicine Cardiology: multiple pages interleave one question's answer choices with the next question's image. Use per-image maps for mixed pages, especially ECG-strip pages and cardiac perfusion pages with subquestions.
- Chapter 6 Nuclear Medicine Vascular/Lymphatics: radiotracer text like `99m` can be misread as a question number, and diagram-labeled site questions may need generic `Site A-D` choices.
- Chapter 7 Nuclear Medicine Pulmonary: mixed pages can put prior answer choices above the next stem; PDF page 247's image belongs to q4 even though q5 starts on that page, and q12 needs adjacent-page V/Q plus chest radiograph images.
- Chapter 8 Nuclear Medicine GI: one page can contain two unrelated images, such as q4 curve choices and q5 gastric-emptying images on PDF page 282; answer labels may include OCR/source typos like `27s Answer`.
- Chapter 9 Nuclear Medicine GU: diagram and curve-choice questions may have all choices embedded in figures; use generic `Structure A-D` or `Curve set A-E` labels and verify mixed renal scintigraphy pages with a contact sheet.
- Chapter 10 Nuclear Medicine Pediatric: answer sections may begin on a page that still contains question text; include that mixed page in answer ranges and make lettered follow-up subparts inherit parent images.
- Chapter 9 Neuroradiology Spine Trauma/Degeneration: q6a/q6b and q7a/q7b were adjacent on the same question page and the PDF extracted the C1/Jefferson image before the C2/Hangman image. The correct prompt-side order was the reverse of extraction order, while the answer-side order followed the answer headers. Always check adjacent same-page images against diagnosis-specific answer text.

## Structural Parsing Checks

For every chapter, run a structural summary before considering the quiz complete:

- total scored entries;
- every question number in order, including lettered subparts;
- option count per question;
- missing answers;
- question image count and explanation image count per question;
- cue-word questions with zero prompt images;
- explanation entries with figure-like text but zero explanation images.

Flag and manually inspect any normal multiple-choice item with fewer than four options, unless the source is intentionally a matching/table/true-false format. Multipart questions such as `2a` through `2f` may need to become separate scored entries even when they share a stem and image.

## Text Cleanup

After extraction, scan for:

- words spliced together without spaces;
- random page numbers inserted into stems or explanations;
- option counts under four for normal multiple-choice questions;
- false question starts caused by labels, captions, or measurements.
- transition sentences after the last answer choice, such as `An MRI was performed...`, `Key images are shown below`, or `This is a different patient...`; these often belong to the next subquestion's stem and must not remain inside the previous question's option text.

Fix these in the generator so rebuilding is repeatable.

For EPUB sources, inspect the package structure first rather than treating it like a PDF. Unzip/read the EPUB spine, locate the chapter XHTML, preserve referenced image files, and map images by their DOM position around stems and answers. Add any EPUB-specific fixes back into this workflow.

## UI and State Requirements

Unless the user says otherwise, keep the existing quiz behavior:

- night mode by default;
- Tutor and Quiz modes;
- saved local state with JSON import/export;
- collapsible question navigation;
- click/tap image lightbox;
- one-question-at-a-time quiz review;
- `Copy Question Text` including stem, answer choices, answer, explanation, and image references;
- `Copy Screenshot` using Anki-oriented portrait-readable image blocks.

## Saved Defaults

Only preselect answers when explicitly requested. If the user asks for highlighted answers, derive defaults from PDF highlight annotations, not from the answer key. Otherwise keep:

```js
const DEFAULT_SELECTED = {};
```

## Reorganizing Existing Quiz Apps

If moving these apps into a more organized library folder, copy them first and leave the original folders in place until users have had a chance to export/import saved state JSON. Browser `localStorage` may not automatically follow a changed `file://` URL or hosted path, even when the quiz content is identical.

For migrated copies:

- Keep each quiz's `APP_ID` unchanged forever so exported state JSON remains compatible.
- Do not prefill or reset user answers during the move.
- Add a small top-of-page link back to the previous/original app URL so users can open the old copy and export JSON if their local browser state does not appear in the new location.
- After a grace period, remove old copies only after confirming users no longer need old local saves.

For new chapters created after the Core Review reorganization, create only the organized app under:

```text
apps/temporary-apps/library/core-review/<book-slug>/<YYYY-MM-DD-chapter-slug>/
```

Do not create a new duplicate legacy/root-level folder for new chapters unless the user explicitly asks for one. Register only the organized app path in `apps/temporary-apps/index.html` and add/update the chapter link in `apps/temporary-apps/library/core-review/index.html`.

## Required Validation

For apps under `apps/temporary-apps/library/`:

```powershell
python scripts\verify-temporary-apps-index.py
```

Also compile the inline script from the generated HTML with Node and check that missing answers and bad option counts are empty.
