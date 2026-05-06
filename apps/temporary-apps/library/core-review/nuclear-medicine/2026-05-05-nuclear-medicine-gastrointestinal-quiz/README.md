# Nuclear Medicine Gastrointestinal System Quiz Build Notes

This temporary app turns chapter 8 of `Core Review Nuclear Medicine.pdf` into a self-contained HTML quiz.

## Source PDF

The generator expects:

```text
G:/My Drive/0. Radiology/Core Review Nuclear Medicine.pdf
```

Do not commit the PDF. The app commits only generated HTML, JSON, extracted image assets, and build notes/scripts.

## Page Ranges

Chapter 8 is split in the source PDF:

- Questions 1-21: PDF pages 281-296
- Answers 1-21: PDF pages 296-313
- Questions 22-32: PDF pages 314-318
- Answers 22-32: PDF pages 319-322
- Chapter 9 starts on PDF page 323

The generated module has 33 scored entries because source question 16 is split into `16a` and `16b`.

## Extraction Notes

- Use `pypdf` layout extraction: `extract_text(extraction_mode="layout")`.
- Default answers are intentionally empty for this chapter: `const DEFAULT_SELECTED = {};`.
- PDF page 282 has two separate images. Image 1 is q4's curve-choice figure, and image 2 is q5's gastric-emptying image, so the generator uses per-image mapping for that page.
- q4 is an image-choice question where choices are embedded in the figure, so the generator assigns generic `Curve A` through `Curve D` choices.
- The answer key has a source typo, `27s Answer A`; the generator accepts that typo and maps it to q27.

## Future Workflow

1. Inspect PDF page ranges and chapter boundaries first.
2. Generate a question-page contact sheet before finalizing image mappings.
3. Use per-image mapping when one page contains more than one unrelated figure.
4. Validate:
   - missing answer keys, including typo variants such as `27s Answer`
   - image-choice questions requiring generic choices
   - questions with fewer than four choices, while documenting true source exceptions
   - question stems that reference an image but have no image attached
   - explanation-side figures that need to be included in `explanationImages`
5. Register the app in `apps/temporary-apps/index.html`.
6. Run:

```powershell
python scripts\verify-temporary-apps-index.py
& 'C:\Users\sterl\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' -e "const fs=require('fs'), vm=require('vm'); const html=fs.readFileSync('apps/temporary-apps/library/2026-05-05-nuclear-medicine-gastrointestinal-quiz/index.html','utf8'); new vm.Script(html.match(/<script>([\s\S]*)<\/script>/)[1]); console.log('script compiles');"
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
