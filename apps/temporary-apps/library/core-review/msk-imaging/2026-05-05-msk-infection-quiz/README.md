# MSK Infection Quiz Build Notes

This temporary app turns chapter 4 of `Core Review MSK.pdf` into a self-contained HTML quiz.

## Source PDF

The generator expects:

```text
G:/My Drive/0. Radiology/Core Review MSK.pdf
```

Do not commit the PDF. The app commits only generated HTML, JSON, extracted image assets, and build notes/scripts.

## Page Ranges

Chapter 4 is split in the source PDF:

- Questions 1-12: PDF pages 112-138
- Answers 1-12: PDF pages 138-141
- Questions 13-14: PDF pages 142-146
- Answers 13-14: PDF page 147
- Chapter 5 starts on PDF page 148

The generated module has 17 scored entries because questions 2 and 9 have lettered subparts.

## Image Alignment Notes

The PDF often places a stem on one page, one or more images on the following page, and the answer choices after the images. Do not assign images by simple adjacency to the nearest detected question number.

For this chapter, the image map was manually checked with a contact sheet before finalizing:

- `2a`: PDF pages 113-114
- `2b`: PDF page 115
- `2c`: PDF page 116
- `3`: PDF pages 117-119
- `4`: PDF pages 120-121
- `5`: PDF pages 122-123
- `6`: PDF page 124, two images
- `7`: PDF pages 125-126
- `9a`: PDF pages 128-129
- `10`: PDF pages 131-133
- `11`: PDF pages 134-137
- `12`: PDF page 138
- `13`: PDF pages 143-144
- `14`: PDF pages 145-146

Question 4 includes the text `6 months prior`; the parser explicitly avoids treating that as a new question 6.

## Future Workflow

Before finalizing any future chapter, generate a contact sheet of all extracted question-page images and compare it against the text-layer page flow. For each image-bearing page, identify whether the image belongs to the stem above it, the answer choices below it, or a new question that starts lower on the page. Then update `question_page_targets` manually.

Required image checks:

- A question whose stem says `image`, `images`, `below`, `radiograph`, `CT`, `MRI`, `MR`, or `ultrasound` must either have images or be intentionally documented as conceptual.
- A question should not inherit the first image on a page merely because its answer choices are above that image.
- Continuation pages with only answer choices usually belong to the previous image-based question.
- If a page contains the answer choices for one question and the stem for the next question, the image usually belongs to the previous question unless the image is visibly tied to the next stem.
- Rebuild, then print every question's `number`, `images`, and first stem words to catch shifted filenames such as `q2_*` being attached to q3.
- Verify explanation-side figures separately and include them in `explanationImages` when present.

## Validation

Run:

```powershell
& 'C:\Users\sterl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'apps\temporary-apps\library\2026-05-05-msk-infection-quiz\build_quiz.py'
& 'C:\Users\sterl\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' -e "const fs=require('fs'), vm=require('vm'); const html=fs.readFileSync('apps/temporary-apps/library/2026-05-05-msk-infection-quiz/index.html','utf8'); new vm.Script(html.match(/<script>([\s\S]*)<\/script>/)[1]); console.log('script compiles');"
python scripts\verify-temporary-apps-index.py
```
