# Quiet Harbor

A phone-first, local-only tracker that lets a small seeded island grow while time passes. Recording a picking episode holds the current timer and starts a fresh world. No account or network service is used for progress.

Open `index.html` from this app on the deployed Library site. On iPhone, use Safari → Share → Add to Home Screen; keep Open as Web App enabled if offered. Home Screen and Safari storage can differ, so export a backup before moving between them. Backups are JSON files held where you choose to save them. The app itself does not upload, sync or include runs in this repository.

Progress uses this browser's IndexedDB, with a request for persistent storage when the browser supports it. Export a backup if you want a copy elsewhere. The exported timer trusts the device clock.

## Sources and credits

- [Kenney Isometric Tiles Landscape](https://kenney.nl/assets/isometric-tiles-landscape), [Buildings](https://kenney.nl/assets/isometric-tiles-buildings), and [City](https://kenney.nl/assets/isometric-tiles-city), CC0. License copies and archive hashes are in `assets/licenses/` and `assets/sources.json`.
- PixiJS 8.22.0, vendored locally under its MIT license in `vendor/PIXI-LICENSE.txt`.
- The app icon is original Quiet Harbor artwork. The resident and water effects are drawn by the app.

## Local development

Use any static HTTP server from this folder. Open `index.html`; no install/build is required. A service worker caches the app shell and selected art after its first successful online load.

Run `npm test` for pure timer, growth, seed layout and backup validation checks. Run `npm run check` for module syntax. `python scripts/prepare-assets.py` verifies the pinned free Kenney archives and crops only the selected sprites; `python scripts/make-contact-sheets.py` creates labeled visual reviews. `python scripts/prepare-icons.py` regenerates the PNG icon family. `python scripts/generate-precache.py` regenerates the app-local offline asset list.
