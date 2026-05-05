# MSK Tumors and Tumor-Like Conditions Quiz Build Notes

This temporary app turns chapter 5 of `Core Review MSK.pdf` into a self-contained HTML quiz.

## Source PDF

The generator expects:

```text
G:/My Drive/0. Radiology/Core Review MSK.pdf
```

Do not commit the PDF. The app commits only generated HTML, JSON, extracted image assets, and build notes/scripts.

## Page Ranges

Chapter 5 is split in the source PDF:

- Questions 1-75: PDF pages 148-263
- Answers 1-75: PDF pages 263-282
- Questions 76-87: PDF pages 283-287
- Answers 76-87: PDF pages 287-290
- Chapter 6 starts on PDF page 291

The generated module has 104 scored entries because many source questions have lettered subparts.

## Image Alignment Notes

This chapter is long and image-heavy. The generator uses a dynamic active-question map plus explicit overrides for pages where the page text starts with one question's answer choices but the image belongs to the next question.

Manual overrides currently include:

- PDF page 185 image belongs to q29a, not q28.
- PDF pages 201-202 images belong to q39, not q38b/q40.
- PDF page 238 image belongs to q61a, while q60b reuses q60a's images.
- Follow-up `b` and `c` subparts reuse the `a` subpart images when applicable.

Before changing this chapter or building the next one, regenerate a contact sheet and check pages that contain both answer choices and a new question stem.

## Future Workflow

1. Inspect PDF page ranges and chapter boundaries first.
2. Generate a question-page contact sheet before finalizing image mappings.
3. Print all question IDs, image paths, and stem prefixes after rebuilding.
4. Validate:
   - missing answer keys
   - questions with fewer than four choices, while documenting true source exceptions
   - image cue questions without images
   - subpart follow-ups that should share the same images
   - neighboring questions that accidentally received each other's images
   - explanation-side figures that need to be included in `explanationImages`
5. Register the app in `apps/temporary-apps/index.html`.
6. Run:

```powershell
python scripts\verify-temporary-apps-index.py
& 'C:\Users\sterl\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' -e "const fs=require('fs'), vm=require('vm'); const html=fs.readFileSync('apps/temporary-apps/library/2026-05-05-msk-tumors-quiz/index.html','utf8'); new vm.Script(html.match(/<script>([\s\S]*)<\/script>/)[1]); console.log('script compiles');"
```

## Required UI Behavior

Keep the same behavior as the prior quiz apps:

- night mode by default
- Tutor and Quiz modes
- saved local state with JSON import/export
- collapsible question navigation
- click/tap image lightbox
- one-question-at-a-time review
- `Copy Question Text`
- `Copy Screenshot` rich HTML clipboard pack for Anki-style paste
