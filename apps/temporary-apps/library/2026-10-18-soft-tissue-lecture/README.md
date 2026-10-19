# Soft Tissue Lecture Lab

## Visual Anki diagnosis cards

The October 19 addition is in [anki/review.html](anki/review.html), with a direct
download of [the APKG](anki/soft-tissue-visual-diagnosis.apkg). It contains 33
diagnosis-only `saCloze++` notes for `Saved Cards`, with 55 individually cropped
and sequence-labeled front panels. See [anki/README.md](anki/README.md) for the
selection, source mapping, validation and rebuild instructions.

Image-first preparation for Dr. Yulia Melenevsky's October 19, 2026 noon conference.

- Both assigned PDFs, downloadable and readable in-app as 29 sharp page renders.
- All 42 numbered figures: 21 CT-paper figures, 18 clinical MRI-paper figures,
  and three MRI teaching algorithms. Original arrows and MRI panel letters are
  retained. CT figure 5 and 8 panels are explicitly labeled A/B in the extraction.
- Eight guided lessons, eight side-by-side comparisons, and 162 individually
  authored image recall questions across every clinical figure.
- Fisher–Yates shuffle without replacement within a round; 20, 50, or all
  matching questions; paper/pattern filters; missed and unreviewed pools.
- Reveal-and-rate practice (self-assessed recall, not an automatically scored
  multiple-choice examination). Algorithms are excluded from quiz prompts because
  their embedded labels disclose the answers. This deliberately uses the requested
  rapid image recall interaction rather than the existing Core Review MCQ renderer.
- Versioned browser-local progress, round resume, validated JSON backup/import.
- iPhone touch-action manipulation, explicit viewport constraints, 16px inputs,
  and prevented double-click defaults avoid accidental double-tap zoom. Images
  have explicit enlargement and 100–300% zoom buttons with scrollable inspection.
  No physical-iPhone verification is claimed.

## Sources and provenance

The user requested these two attachments from the forwarded “Articles for noon
conference” email dated October 16, 2026. The original message explicitly says
they prepare residents for Monday conference. Email addresses, message headers,
and private correspondence are not included in the app.

1. Subhawong TK et al. *Soft-Tissue Masses and Masslike Conditions: What Does CT
   Add to Diagnosis and Management?* AJR 2010;194:1559–1567.
   DOI: https://doi.org/10.2214/AJR.09.3736
   Supplied attachment: `ST masses CT.pdf` (scanned, nine pages).
   SHA256: `14327d1b33b3dd0f283b8ebbe891a18beb09e18209b21b5160ebaba9f553a45f`
2. Wu JS, Hochman MG. *Soft-Tissue Tumors and Tumorlike Lesions: A Systematic
   Imaging Approach.* Radiology 2009;253:297–316.
   DOI: https://doi.org/10.1148/radiol.2532081199
   Supplied attachment: `STT Radiology 2009.pdf` (20 pages).
   SHA256: `4629e4d6d0b6c3874c2667e157bf6df3d1afddbc80ac20164288be7f544ef4dd`

Figure explanations and question answers are paraphrases grounded in the supplied
captions and corresponding article text. Each figure has a direct PDF/page link.
The historical classification/vascular terminology is identified as such; this is
lecture preparation from the assigned readings, not an updated management guideline.
Source copyrights remain with their respective rights holders.

## Rebuild and validate

Requires Python with PyMuPDF and Pillow, plus Node.js for structural verification.
Serve this folder over HTTP (for example, `python -m http.server 8743` from the
repository root); opening `index.html` as `file://` does not support manifest fetch.

```powershell
python apps/temporary-apps/library/2026-10-18-soft-tissue-lecture/scripts/extract_figures.py
node apps/temporary-apps/library/2026-10-18-soft-tissue-lecture/scripts/validate.mjs
python scripts/verify-temporary-apps-index.py
```

`bank.js` holds the authored content separately from `app.js`. `figure-manifest.json`
records every image's source page, CT crop region or MRI image xref, and dimensions.
Extraction is deterministic; the CT crop map was manually checked against the
captions. `qa/ct-contact.jpg` and `qa/mr-contact.jpg` show the entire final mapping.
Increment the bank version and save key when replacing/reordering authored items.
Stable question IDs combine the figure ID and authored per-figure question number.
