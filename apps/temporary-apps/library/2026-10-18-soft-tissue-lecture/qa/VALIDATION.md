# Validation

Validated October 18, 2026 (America/Chicago).

- Read all nine scanned CT-paper pages and the MRI article text/captions.
- Inspected both final contact sheets, covering all 42 numbered figures.
- Checked CT figure 5 A/B and CT figure 17 individually after final crop repairs:
  panel labels are explicit, the original arrow is retained, and no caption is
  visible in the final image. Multi-panel MRI images use the original embedded
  composites, whose panel letters are retained without captions.
- Every one of the 39 clinical figures has at least four individually authored
  questions. The three answer-bearing flowcharts appear in the guide/atlas only.
- Every figure appears in a guided lesson and has a source PDF/page reference.
- `scripts/validate.mjs` passes: 42 mappings, 162 questions, 29 reader pages,
  media existence/dimensions, valid JS, progress transfer round trip, six corrupt
  import cases, completed-round state, and unique shuffled question coverage.
- Repository temporary-app index verifier passes; existing root link is retained.
- Existing deployment checks also pass: nine scripture quiz quality tests and
  validation of 29 dates / 870 questions / 87 exports.
- Chrome UI: checked the overview and guided lesson visually; started a mixed
  round with no revealed answer; opened the image and confirmed its dialog did
  not reveal a diagnosis; used the 150% zoom control; revealed the answer;
  recorded both “Again” and “Knew it”; paused/reloaded and confirmed saved ratings
  and resume position; selected the missed pool and completed a one-item round.
- Chrome UI: navigated the CT reader to PDF page 7 and verified the corresponding
  page image loaded; searched the atlas for “blooming” and obtained figure 16;
  inspected the comparison content and guided fat lesson. No console errors or
  warnings were reported by the browser tool.
- Compact layout DOM inspection reported no horizontal page overflow and
  `touch-action: manipulation` on the quiz image. The browser tool reported a
  585 CSS-pixel viewport after requesting a 390-pixel override; screenshots with
  that override timed out, and it was reset. Desktop screenshots succeeded.
  Physical iPhone/Safari double-tap behavior has not been tested.
- JSON download event capture timed out in the browser tool; browser export/import
  end-to-end is not claimed. JSON compatibility and corrupt import rejection are
  covered by the Node validation checks.

The extracted figure IDs are the mapping keys used by the authored questions;
the renderer does not infer image relationships by page adjacency.
