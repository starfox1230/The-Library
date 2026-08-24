# Crystal Reactor Visual History

## Preferred baseline: Golden-Angle Rosette

This is the design the user explicitly liked immediately before the rejected branch/crown experiment. Preserve it as the canonical fallback.

- One four-facet crystal component per streak card.
- Components use a golden-angle spiral around the central streak number.
- Baseline angle: `ordinal * PI * (3 - sqrt(5)) - PI/2`, with only a tiny seeded variation.
- Baseline radius: `20 + 5.8 * sqrt(ordinal)`.
- Baseline crystal length: `30 + seeded value * 17`.
- Baseline crystal width: `11 + seeded value * 8`.
- Fixed ice/cyan/lavender sheen.
- Original camera: natural radius `50 + 5.8 * sqrt(streak)` and target radius `91 + 42 * (1 - exp(-streak / 260))`.

The exact baseline calculations remain isolated in `crystalRosetteBaselineGeometry()` in `web/overlay.js`, so this appearance can be restored without reconstructing it from memory.

## Rejected experiment: Ten-Card Branches / Fifty-Card Crowns

Do not restore this design unless explicitly requested. It grouped pieces into five-spoked local snowflake structures. Although it reduced density, it lost the organic elegance of the rosette and looked poor during early streaks.

## Current candidate: Rosette Growth Eras

The preferred rosette remains exact through streak 50. After 50, each set of 50 cards occupies a spacious concentric growth era while retaining the original golden-angle placement and individual four-facet crystal shape. Ten-card and fifty-card celebrations are transient effects only; they do not reorganize the permanent crystal geometry.
