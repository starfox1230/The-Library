# Nuclear Medicine Genitourinary System Quiz Build Notes

This temporary app turns chapter 9 of `Core Review Nuclear Medicine.pdf` into a self-contained HTML quiz.

## Source PDF

The generator expects:

```text
G:/My Drive/0. Radiology/Core Review Nuclear Medicine.pdf
```

Do not commit the PDF. The app commits only generated HTML, JSON, extracted image assets, and build notes/scripts.

## Page Ranges

Chapter 9 is split in the source PDF:

- Questions 1-15: PDF pages 323-341
- Answers 1-15: PDF pages 341-352
- Questions 16-21: PDF pages 353-359
- Answers 16-21: PDF pages 359-361
- Chapter 10 starts on PDF page 362

The generated module has 21 scored entries.

## Extraction Notes

- Use `pypdf` layout extraction: `extract_text(extraction_mode="layout")`.
- Default answers are intentionally empty for this chapter: `const DEFAULT_SELECTED = {};`.
- q2 is a nephron diagram question with choices embedded in the figure, so the generator assigns generic `Structure A` through `Structure D` choices.
- q9 is a curve-choice question with choices embedded in the figure, so the generator assigns generic `Curve set A` through `Curve set E` choices.
- Many pages include answer choices above the next stem. The final image map is page-specific to avoid attaching the previous question's image to the next question.

## Future Workflow

1. Inspect PDF page ranges and chapter boundaries first.
2. Generate a question-page contact sheet before finalizing image mappings.
3. Use generic option labels when the source embeds choices inside diagrams or curve figures.
4. Validate:
   - missing answer keys
   - image-choice questions requiring generic choices
   - questions with fewer than four choices, while documenting true source exceptions
   - question stems that reference an image but have no image attached
   - explanation-side figures that need to be included in `explanationImages`
5. Register the app in `apps/temporary-apps/index.html`.
6. Run:

```powershell
python scripts\verify-temporary-apps-index.py
& 'C:\Users\sterl\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' -e "const fs=require('fs'), vm=require('vm'); const html=fs.readFileSync('apps/temporary-apps/library/2026-05-05-nuclear-medicine-genitourinary-quiz/index.html','utf8'); new vm.Script(html.match(/<script>([\s\S]*)<\/script>/)[1]); console.log('script compiles');"
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
