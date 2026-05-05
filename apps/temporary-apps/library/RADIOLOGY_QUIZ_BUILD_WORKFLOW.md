# Radiology Quiz Build Workflow

Use this note when converting Core Review PDF or EPUB chapters into the temporary quiz apps.

## Image Alignment Is Mandatory

Do not rely on automatic page adjacency for images. These books commonly place a stem at the bottom of one page, one or more images on the following page, and answer choices after the image. They also place answer choices for one question above the next question's stem on the same page.

For every chapter:

1. Print each chapter page's text lines with PDF page index, displayed PDF page number, and image count.
2. Generate a contact sheet of all extracted images for the chapter's question pages.
3. Manually map each image page to question IDs in `question_page_targets`.
4. Rebuild and print every question's `number`, `images`, and stem prefix.
5. Specifically inspect pages where:
   - a stem says `image`, `images`, `below`, `radiograph`, `CT`, `MRI`, `MR`, `ultrasound`, or `scan`;
   - a page has answer choices for one question and a new stem below;
   - a page is image-only or mostly image-only;
   - labels such as `current`, `prior`, `6 months prior`, sequence names, or figure captions could be misread as question text.
6. If a cue word appears in a stem but no image is attached, either fix it or document why it is a conceptual wording cue rather than a supplied figure.
7. If a question has an image that belongs to a neighboring question, fix the map before final validation.

The common failure pattern is an off-by-one image shift. Examples already encountered:

- Chapter 2 MSK Normal/Normal Variants: q2 incorrectly received q3's first radial-head image; q3 needed both page 60 and page 61 images.
- Chapter 3 MSK Congenital/Developmental: q3/q4, q13/q14, and q19/q20 had continuation-page shifts before manual correction.
- Chapter 4 MSK Infection: the text `6 months prior` had to be excluded as a false question number, and q12's CT image appeared on the answer-section boundary page.
- Chapter 4 Nuclear Medicine Head and Neck: PDF page 158 had two unrelated question images on the same page. The first belonged to q8 and the second belonged to q9a, so the generator needed a per-image split map instead of a page-level map.

## Text Cleanup

After extraction, scan for:

- words spliced together without spaces;
- random page numbers inserted into stems or explanations;
- option counts under four for normal multiple-choice questions;
- false question starts caused by labels, captions, or measurements.

Fix these in the generator so rebuilding is repeatable.

## Saved Defaults

Only preselect answers when explicitly requested. If the user asks for highlighted answers, derive defaults from PDF highlight annotations, not from the answer key. Otherwise keep:

```js
const DEFAULT_SELECTED = {};
```

## Required Validation

For apps under `apps/temporary-apps/library/`:

```powershell
python scripts\verify-temporary-apps-index.py
```

Also compile the inline script from the generated HTML with Node and check that missing answers and bad option counts are empty.
