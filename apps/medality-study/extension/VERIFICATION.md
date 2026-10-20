# Version 1.4 verification

- 41 JavaScript tests: playback speed, copy/save, download controls, UTF-8 encoding, 90% automatic saving, duplicate prevention, missing transcripts, navigation races, native/Vimeo events, history order/selection/copy, safe rendering, bridge scoping and public-page local storage.
- 2 Python video-helper URL validation tests remain available.
- Browser QA: imported existing LI-RADS 5 JSON backup, selected and copied transcript in the new recent.html page.
- Public page and extension page share the same view code; extension version reads chrome.storage directly, hosted version uses a scoped bridge or manual JSON import.
- No extension reload is performed automatically; live installed-extension 90% tracking requires Reload and a refreshed Medality lesson.
- No automatic backfill of earlier watching. 90% is playback position; seeking counts.
- UTF-8 validation covers every extension JS/JSON/HTML/CSS file before packaging.
