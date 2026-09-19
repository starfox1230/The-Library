# Radiology Video Library

Static mobile-first app, linked from the root Library page. Its existing URL is retained to preserve browser-local progress.

## Inventory snapshot (2026-09-19 UTC)

| Channel | Videos | Shorts | Total | Saved transcripts |
|---|---:|---:|---:|---:|
| NeuroRadish | 65 | 170 | 235 | 0 |
| LearnNeuroradiology | 245 | 6 | 251 | 141 |
| The Neuroradiologist | 33 | 1 | 34 | 0 |
| Radiology Tutorials | 195 | 6 | 201 | 104 |
| Total | 538 | 183 | 721 | 245 |

Channel Videos, Shorts and Streams tabs were queried separately; none has a Streams tab. Playlist membership is retained without importing other creators' uploads. Titles and their original case numbers are preserved. Topic tags are conservative title-based labels, not inferred diagnoses of undisclosed cases.

**Transcript collection is partial, not complete.** The bulk attempt saved 141 YouTube caption transcripts and reused 104 existing Library physics transcripts matched by exact video ID. YouTube then blocked requests (HTTP 429 / bot verification). Of 476 unsaved entries, 367 have retrieval failures, 107 were not fetched, and 2 had no English captions. A retrieval failure does not mean the video has no transcript. Files retain source provenance. Automatic captions can contain errors.

Every lesson has a button that copies its YouTube URL and opens https://www.youtube-transcript.io/. Clipboard failure shows selectable text. Users can paste a retrieved transcript and save it locally. Service availability, account requirements and usage limits are outside this app's control. No keys or third-party account credentials are embedded.

## Updating

Install Python dependencies `yt-dlp` (caption fetching uses the standard library). Run from repository root:

```powershell
py -3 scripts/collect_radiology_video_library.py --inventory
py -3 scripts/collect_radiology_video_library.py --transcripts
# Once YouTube access is restored, one resumable retry pass:
py -3 scripts/collect_radiology_video_library.py --transcripts --retry
# Reconcile existing files / legacy filter mapping without network:
py -3 scripts/collect_radiology_video_library.py --reconcile
```

An inventory-only update preserves saved transcripts. It aborts on channel-tab errors rather than overwriting the catalog with a partial inventory. Caption collection checkpoints each result and stops on blocking / repeated failures; do not repeatedly retry a blocked endpoint. Private/deleted/unlisted videos not exposed by the public tabs cannot be claimed as inventoried. New snapshots must be reviewed before publishing.

The older `build_neuroradish_catalog_app.py` is disabled to prevent overwriting this multi-channel app with the legacy HTML.

## Local state

`radiology-video-library-v2` stores per-channel filters, sort, queue/current lesson, progress, favorites, notes, custom prompt and pasted transcripts. Existing `neuroradish-catalog-v1` progress and custom filters are migrated without deleting the old key. Playback does not mark a lesson watched; use Mark watched or Done & next. Queues snapshot the selected order and never fall back into another series at the end. Storage is per browser/device, not cross-device sync or guaranteed offline access. Backup/restore supports moving saved state; clearing browser data can remove it.

## Verification

Serve the repository with `py -3 -m http.server 8765 --bind 127.0.0.1`, then run `node scripts/test_radiology_video_library.cjs` with Playwright available and Edge installed. Tests check inventory uniqueness, saved transcript identity, mobile overflow, Shorts, Buzzword case order, filtered queue/reload/end boundary, copy+prompt, link fallback, pasted transcript persistence and legacy filter migration.
