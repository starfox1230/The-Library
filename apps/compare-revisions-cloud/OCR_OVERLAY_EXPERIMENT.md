# OCR overlay experiment — October 30, 2026

The tested overlay comparison is **not reliable enough to validate accessions**.
It is a developer experiment, not a production step or a reason to label a row
verified. The website now accepts valid mappings without individual approval;
missing/conflicting mappings still require correction.

## What was tested

The original email image has 47 rows. The two additional images have 49 and 81
rows. Enlarged-source inspection checked the accession strings independently of
the OCR output. All 177 accession reads matched these images. Case-label repair
corrects seven, five and six labels respectively. The 81-row image exposed an
early-anchor edge case, now covered by sequence safeguards. The 49-row image
has no header and required manual column marking.

No images or identifiers are included in this repository. These are related
screenshots, not a representative clinical validation set.

`dev/benchmark-ocr-overlay.py` implements the proposed rendering test:

1. Crop the full accession cell around the detected row, excluding table borders.
2. Normalize background intensity and isolate dark text.
3. Render the proposed string, allowing small translations. Use a fixed fitted
   horizontal scale so a missing digit cannot be hidden by stretching the string.
4. Measure both uncovered source ink and excess overlay ink. Looking only for
   uncovered source text can miss an extra or substituted stroke.
5. Compare the residual with a threshold. A high residual flags a mismatch.

The primary model chose among Arial, Calibri, Segoe UI, Tahoma and Verdana at
three rendering sizes using only the original image. Its threshold accepted
all correct calibration strings. Font, scale and threshold were frozen before
inspecting the new images. No per-string candidate fitting or identifier
pattern rule was used to force altered strings to fail.

The mutations include substitutions at every position, deletions, duplicated
character insertions and adjacent transpositions. Duplicates and unchanged
variants are removed per row. Mutations from the same row are correlated;
28,632 strings do not represent 28,632 independent screenshots or patients.

## Results with the frozen primary settings

Sensitivity here means the fraction of deliberately wrong strings flagged.
Specificity means the fraction of correct strings accepted.

| Image | Correct accepted | Altered strings detected | Sensitivity |
| --- | ---: | ---: | ---: |
| Original, used for calibration | 47 / 47 | 3,561 / 7,628 | 46.7% |
| Example 2, unchanged settings | 49 / 49 | 3,675 / 7,957 | 46.2% |
| Example 3, unchanged settings | 81 / 81 | 4,976 / 13,047 | 38.1% |
| Total, including calibration | 177 / 177 | 12,212 / 28,632 | 42.7% |

Observed specificity was 100% on these images; this small sample does not
establish a general 99% specificity. The original image's specificity is fitted,
so it is not an independent result.

Correct and altered strings have overlapping residual scores. Even retuning
the scalar threshold on each evaluation image gives a best balanced operating
point of roughly 91%, 89% and 84% respectively, well below 99% for both metrics.
Those post-hoc values are exploratory and are not frozen-model validation.

A second variant combines whole-string mismatch with the worst glyph-width
local residual, to avoid diluting one wrong digit among ten correct characters.
It detects all tested insertions/deletions, but only 51%, 50% and 41% of all
alterations, and falsely flags one correct string in Example 3. This variant
was explored after the primary results, so it is not an independent holdout test.

The comparison is useful for obvious length or shape changes but cannot yet
separate subtle digit substitutions from font/anti-aliasing differences. This
does not prove every possible overlay method will fail; it shows why this
implementation should not become an automatic approval gate.

## Reproduction

Use developer-only Pillow and NumPy; neither is added to Cloud Run dependencies.
Supply a private image and a manually verified JSON reference with full-cell
rectangles, for example:

```json
{"rows": [{"text": "TEST000001", "bbox": [30, 20, 140, 36]}]}
```

Fit on the calibration image, storing all private files outside Git:

```powershell
python dev/benchmark-ocr-overlay.py --image PRIVATE_IMAGE.png --rows PRIVATE_TRUTH.json --font C:\Windows\Fonts\arial.ttf --font C:\Windows\Fonts\calibri.ttf --font C:\Windows\Fonts\segoeui.ttf --font C:\Windows\Fonts\tahoma.ttf --font C:\Windows\Fonts\verdana.ttf --model-out PRIVATE_MODEL.json --out PRIVATE_RESULTS.json
```

Then apply the frozen model:

```powershell
python dev/benchmark-ocr-overlay.py --image ANOTHER_PRIVATE_IMAGE.png --rows ANOTHER_PRIVATE_TRUTH.json --model PRIVATE_MODEL.json --out ANOTHER_PRIVATE_RESULTS.json
```

`--metric local` selects the secondary variant during calibration. The output
contains aggregate counts and residual ranges, not the source strings. Source
image/truth/model/output paths are operator-controlled and should stay outside
the repository. The aggregate experiment record is in
`dev/overlay-experiment-results.json`.

## What a stronger second check would need

Character-level registration or another independent recognizer could provide a
better discrepancy signal. It would need testing on untouched screenshots with
different fonts, zoom, display scaling, selection highlighting and compression,
including natural OCR errors. Choose error definitions and thresholds before
evaluation; report false alarms and missed wrong identifiers separately. Keep
an inconclusive state rather than forcing every image to pass. No 99% claim is
supported by the current experiment.
