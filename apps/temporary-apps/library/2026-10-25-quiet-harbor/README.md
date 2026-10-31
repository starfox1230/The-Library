# Quiet Harbor

A phone-first, local-only tracker that lets a small seeded island grow while time passes. Recording a picking episode holds the current timer and starts a fresh world. No account or network service is used for progress.

Open `index.html` from this app on the deployed Library site. On iPhone, use Safari → Share → Add to Home Screen; keep Open as Web App enabled if offered. Home Screen and Safari storage can differ, so export a backup before moving between them. Backups are JSON files held where you choose to save them. The app itself does not upload, sync or include runs in this repository.

Progress uses this browser's IndexedDB, with a request for persistent storage when the browser supports it. Export a backup if you want a copy elsewhere. The exported timer trusts the device clock.

The main screen keeps the timer, island, and restart action. The counter separates calendar units from hours, minutes, and seconds; labels sit underneath the clock digits. Best time is shown only when there is a previous run to compare. Town stages, growth badges, encouragement, decorative captions, the explore link, and the footer are omitted. Town totals and the next landmark remain in History & settings → Town life.

## A town full of places

Thirteen public-place designs join the cottages automatically. Schools have a bell tower and flag; museums have columns and a pediment; fire stations have garage doors and a small engine. The remaining designs are a bakery, café, market, fountain garden, library, clinic, town hall, glasshouse, observatory, and theater. Tap any building to see its name, description, and arrival time. History & settings → Town life lists the designs that have arrived and the next arrival.

| First arrival | Place |
| --- | --- |
| 6 hours | Bakery |
| 9 hours 36 minutes | Café |
| 15 hours | Market |
| 1 day | School |
| 2 days | Fire station |
| 2 days 20 hours | Fountain garden |
| 4 days | Library |
| 6 days | Clinic |
| 9 days 8 hours | Museum |
| 14 days | Town hall |
| 19 days 14 hours 24 minutes | Glasshouse |
| 25 days 4 hours 48 minutes | Observatory |
| 28 days | Theater |

Later 16-lot districts contain twelve cottages, a shop, two different community places, and a park. Shop and community designs rotate reproducibly by run seed and district, so later growth has variety. Existing lot coordinates, IDs, total building counts, construction times, saved progress, and backup format are preserved. Runs already beyond an arrival time gain their landmarks when the new version loads; no reset is needed.

This is an expanding illustration, not a management simulation: schools and fire stations do not require staffing, resources, or maintenance. New designs can be added to the vector catalog without external services or additional asset downloads. The renderer draws only the part of the town near the camera; scene detail and visible object count remain the practical phone-performance constraints.

## Sources and credits

The current island, cottages, clock towers, gardens, and neighbors are original vector illustrations drawn by the renderer. Ground, paths, and objects use separate layers, and objects sort by their ground position. Existing run seeds and growth schedules are unchanged. The earlier Kenney art remains bundled with its licenses.

The church illustration follows the long brick form, broad gabled roof, and slender white steeple of a Latter-day Saint meetinghouse ([Spanish Fork reference](https://local.churchofjesuschrist.org/en/us/ut/spanish-fork/1552-east-750-south)). The later temple is an original miniature inspired by the Salt Lake Temple's six attached towers and spires ([official architectural background](https://newsroom.churchofjesuschrist.org/additional-resources/background-on-the-salt-lake-temple)). These references inform the silhouettes; the artwork is drawn locally from vector primitives.

- [Kenney Isometric Tiles Landscape](https://kenney.nl/assets/isometric-tiles-landscape), [Buildings](https://kenney.nl/assets/isometric-tiles-buildings), and [City](https://kenney.nl/assets/isometric-tiles-city), CC0. License copies and archive hashes are in `assets/licenses/` and `assets/sources.json`.
- PixiJS 8.22.0, vendored locally under its MIT license in `vendor/PIXI-LICENSE.txt`.
- The app icon is original Quiet Harbor artwork. The resident and water effects are drawn by the app.

## Local development

Use any static HTTP server from this folder. Open `index.html`; no install/build is required. A service worker caches the app shell and selected art after its first successful online load.

Run `npm test` for pure timer, growth, seed layout and backup validation checks. Run `npm run check` for module syntax. `python scripts/prepare-assets.py` verifies the pinned free Kenney archives and crops only the selected sprites; `python scripts/make-contact-sheets.py` creates labeled visual reviews. `python scripts/prepare-icons.py` regenerates the PNG icon family. `python scripts/generate-precache.py` regenerates the app-local offline asset list.

Run `python scripts/generate-precache.py` after changing runtime files. Its content fingerprint gives every release a separate offline cache, so an update cannot keep serving a previous version's renderer. The update button activates the waiting worker and reloads the app; saved runs stay in IndexedDB.

The app's main document comes from the same cache revision as its modules until the update is installed. Hidden empty compatibility targets also let older cached clients install this interface update safely; they are not visible app content.

Serve this folder and open `tests/visual-review.html` to compare the seed, ten-minute garden, one-hour neighborhood, two-day village, and hundred-day district. These deterministic scene fixtures do not modify saved progress. The page also embeds the real app at a 390 × 844 phone size.

Open `tests/landmark-review.html` for a labeled gallery of all sixteen building/place designs, their descriptions, and first arrival times. Add `?places=church,temple` to view the two religious landmarks together. Only visible cards create drawing contexts, and hidden cards release them.

The Home Screen shell uses `viewport-fit=cover`, `black-translucent` status-bar styling, safe-area padding, and a shared solid background/theme color. These let the page extend behind the system status area without a gradient seam. iOS controls its status icons and home indicator; web content does not hide those. Verify the installed presentation on a physical iPhone, since a desktop browser cannot reproduce that system chrome.
