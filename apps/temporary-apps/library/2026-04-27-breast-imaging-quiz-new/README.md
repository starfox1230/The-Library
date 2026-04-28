# Breast Imaging Regulatory Quiz (New) Build Notes

This temporary app turns chapter 1 of the newer standalone PDF export of `Breast Imaging: A Core Review` into a self-contained HTML quiz.

## Source PDF

The generator expects:

```text
G:/My Drive/0. Radiology/Core Review Books/Breast Imaging/1RegulatoryStandardso_BreastImagingACoreRev.pdf
```

Do not commit the PDF. The app commits only the generated HTML, JSON, extracted image assets, and this build script.

## PDF Extraction Notes

- The PDF is an 85-page chapter export.
- Chapter 1 content is on PDF pages 1 through 84.
- Page 85 begins chapter 2 and is intentionally excluded.
- The PDF text layer is noisy because question numbers, option letters, stems, and answer choices are often interleaved.
- For this build, the cleaned question and answer text is reused from the previously generated chapter 1 EPUB app, while images are extracted from this newer PDF with PyMuPDF.
- `build_quiz.py` extracts question images from pages 1 through 50 and explanation images from pages 51 through 84.
- Image-only continuation pages are handled by carrying forward the current question or answer number.

## Special Cases Found

- Question 2 is a matching-style item. It must remain split into separately scored entries `2A` through `2H`.
- The newer PDF places the question 2 BI-RADS matching images on separate image-only pages. `build_quiz.py` maps PDF pages 2 through 9 to all `2A` through `2H` entries as shared stem images.
- Matching-style questions should not be left as a single multiple-choice item. Split them into separately scored entries using the answer explanation lines as the source of truth for each part's correct answer.
- Preserve every part found in the source, even if a quick visual read or user note only mentions a subset.
- Reuse shared stem images for each split matching subquestion unless the source clearly maps specific images to specific subparts.
- Many questions have five choices. This is source-faithful and should not be treated as a parser failure.

## Future PDF Workflow

1. Inspect the source PDF with PyMuPDF to identify chapter page boundaries.
2. Exclude any next-chapter pages included at the end of a standalone export.
3. Inspect extracted text before trusting it. Look for interleaved question numbers, option letters, headers, footers, page numbers, and print/license notices.
4. Clean obvious OCR/text-layer problems:
   - add missing spaces where words were spliced together
   - remove random page numbers inserted inside stems or explanations
   - remove repeated headers, footers, copyright notices, and access notices
5. Validate question structure:
   - missing answer keys
   - questions with fewer than four choices when the surrounding source pattern suggests four or five choices
   - questions whose source text says image/table but no image/table was captured
   - subquestions and matching questions with unusual answer format
   - matching-style items where each lettered image/case needs its own answer selection and scoring
6. Extract all question images and all explanation-side images. If an answer explanation includes a figure, include that figure in `explanationImages`.
7. Keep the required UI behavior:
   - night mode by default
   - Tutor and Quiz modes
   - saved local state with JSON import/export
   - collapsible question navigation
   - click/tap image lightbox
   - one-question-at-a-time review
   - `Copy Question Text`
   - `Copy Screenshot` rich HTML clipboard pack for Anki-style paste
8. Register the app in `apps/temporary-apps/index.html`.
9. Run:

```powershell
python scripts\verify-temporary-apps-index.py
& 'C:\Users\sterl\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' -e "const fs=require('fs'), vm=require('vm'); const html=fs.readFileSync('apps/temporary-apps/library/2026-04-27-breast-imaging-quiz-new/index.html','utf8'); new vm.Script(html.match(/<script>([\s\S]*)<\/script>/)[1]); console.log('script compiles');"
```
