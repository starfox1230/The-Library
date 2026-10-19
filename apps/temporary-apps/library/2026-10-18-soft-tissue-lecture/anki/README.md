# Soft-tissue visual diagnosis Anki set

Source readings: Subhawong et al., AJR 2010;194:1559–1567, and Wu & Hochman,
Radiology 2009;253:297–316. Both source PDFs are preserved under `../papers/`.

- 33 notes / 33 cards. Diagnosis prompts only, as explicitly requested.
- Exact canonical `saCloze++` MODEL, ID `1761198205290`, fields `Text` and `Extra`.
  No note type or template changes. The package uses the `Saved Cards` deck with
  tag `#AnkiChat::2026.10.19_Soft_Tissue_Lecture` for focused study.
- 55 front panels, with one image per line and one derived `1/N` immediately above
  the first image on a multi-image note. The unexported `textHtml` has no counter.
- Each source a/b/c/d or A/B panel is a separate image. Its original printed letter
  remains in the cropped image; caption-verified sequence/modality text is added
  beside that letter, in the white letter strip. Single-panel images receive a
  modality/sequence strip without an invented letter.
- Only essential, brief clinical history. No figure number, caption, source name,
  diagnosis-revealing annotation or unnecessary demographics on the front.
- Full diagnostic anatomy, arrows, scales and original panel letters are retained.
  Raster resampling enlarges the low-resolution embedded MRI panels for a readable
  label strip; it does not invent additional diagnostic image detail.
- 16 full source-page screenshots are reused in Extra after a brief discriminator
  and source citation. In total, 71 media files are packaged.

## Selection

`cases.json` is the authored selection and per-figure explanation of omissions.
All 62 clinical source panels were extracted and mapped. Seven of those panels
are omitted from the focused APKG because their six cases do not support a fair
specific image diagnosis with the supplied brief history:

- CT figures 13, 14, 16, 17 and 19 (nonspecific postoperative collection, cystlike
  myxoid sarcoma, solitary fibrous tumor, amyloid mass and chordoma metastasis).
- MRI figure 12, which primarily demonstrates T2 dynamic-range/display changes.
- MRI figures 17–19 are flowcharts, not patient diagnosis images.

Broad diagnostic categories are used when the image cannot establish histology,
including the benign peripheral nerve sheath tumor and benign vascular lesion
examples. Source-specific histology and historical terminology are clarified in
Extra. No extra arrow cards or nonvisual fact cards were added because this user
request explicitly limits the set to diagnosis prompts.

## Build and inspect

Requires Python 3.11+, PyMuPDF, Pillow and genanki. From the repository root:

```powershell
python apps/temporary-apps/library/2026-10-18-soft-tissue-lecture/anki/build.py
python scripts/verify-temporary-apps-index.py
```

`build.py` calls the shared `scripts/build_manifest_apkg.py`, which imports `MODEL`
directly from `apps/radiographics-review/scripts/build_anki_package.py`. Relative
asset paths are retained in the portable `notes.json` manifest; the shared builder
runs with the Anki output folder as its working directory.

Outputs include:

- `soft-tissue-visual-diagnosis.apkg` — importable package; nothing is imported into
  the live Anki collection by this build.
- `review.html` — browser front/back preview using the canonical CSS, with separate
  source-page disclosures and a download link.
- `notes.json` — exact packaged fields, stable GUIDs, tags and media map.
- `candidates.json` — source-linked content plus ordered front media, before the
  exporter adds a counter.
- `extraction-manifest.json` — all 62 source panels, source page/xref/coordinates,
  sequence labels, original-letter attestations, source hashes, instruction receipt
  and explicit omissions. Both PDFs' printed figure numbers are preserved here.
- `validation.json` — package verification result, including canonical model
  templates/CSS equality, media completeness and exact field round trip.
- `qa/panels-01.jpg` through `qa/panels-06.jpg` — complete crop contact sheets.

## QA

All six contact sheets were visually reviewed (100% of the 62 clinical panels).
Each crop contains one panel, no caption/body text, and the full diagnostic visual
boundary. All source panel letters remain present. CT figure 8a was extracted
from its full upper boundary, rather than reusing the earlier app thumbnail crop.
MRI page text intersection checks returned zero hits for every embedded crop.

Every sequence label was checked against its figure caption. Contrast/fat
suppression is stated only when provided. The plane for MRI figure 11b is omitted
because the caption calls it coronal while its displayed section looks transverse;
the caption's T1 fat-suppressed postcontrast SPGR description is retained.

The APKG is reopened as a ZIP/SQLite collection before success is reported. Checks
include 33 notes/cards, one `c1` per note, unique stable GUIDs, correct tag/deck,
separate ordered images, a single counter, source screenshots in Extra, all media
nonempty, exact field round trip, and exact canonical model ID/fields/templates/CSS.
The first verification attempt detected an integer-versus-string representation
of the model ID; normalization in the verifier fixed that check without changing
the packaged canonical model.

Browser checks cover hidden/revealed diagnoses, panel count/order, source-page
disclosures and layout. This is an HTML approximation of content appearance;
an actual Anki or AnkiMobile import/reviewer session is not claimed.
