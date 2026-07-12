# Visual feed pilots

These JSON files define source-grounded visual-feed pilots without storing copyrighted textbook images in the public repository.

Build the Hip pilot into a private output directory:

```powershell
& 'C:\Users\sterl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  'apps\anki-card-creation-codex-helper\scripts\build_visual_feed.py' `
  --pdf 'G:\My Drive\0. Radiology\Core Radiology 2nd ed.pdf' `
  --config 'apps\anki-card-creation-codex-helper\visual-feed-pilots\2026-07-13-hip-chunk-1.json' `
  --output 'C:\Users\sterl\OneDrive\Study OS Private\visual-feeds\2026-07-13-hip-chunk-1'
```

The output contains a mobile `index.html`, a completeness-aware `manifest.json`, and private image assets. The expected and extracted counts must match before the feed is considered complete.
