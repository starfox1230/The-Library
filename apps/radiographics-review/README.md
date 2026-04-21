# RadioGraphics Review Automation

Canonical workspace:

```text
C:\Users\sterl\OneDrive\Documents\GitHub\The-Library\apps\radiographics-review
```

This project checks for recently published `RadioGraphics` articles, generates a phone-friendly static site under this app folder, and keeps the authenticated RSNA browser profile outside the repo.

## What it does

- Uses the Crossref API to detect recent `RadioGraphics` articles.
- Tracks which article DOIs you have already seen in `data/review-state.json`.
- Writes markdown digests into `digests/`.
- Opens article pages in a dedicated local browser profile to capture figure images and captions.
- Builds a scrollable reader HTML page for each new article under `articles/<article-slug>/reader.html`.
- Builds an Anki `.apkg` package with image cards for each new article under `articles/<article-slug>/anki/`.
- Maintains the app landing page at `index.html`.
- Keeps a mirrored article index at `articles/index.html`.
- Can publish the updated app to GitHub with a scoped commit.

## Security model

- Do not paste your RSNA password into chat.
- Do not store browser session files in Google Drive.
- The dedicated local browser profile lives at:

```text
%LOCALAPPDATA%\RadiographicsReview\browser-profile
```

## First-time setup

1. Install the local runtimes outside the repo:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-runtime.ps1
```

That installs `playwright-core` under `%LOCALAPPDATA%\RadiographicsReview\runtime` and `genanki` under `%LOCALAPPDATA%\RadiographicsReview\python-runtime`.

2. Capture a local authenticated browser session:

```powershell
npm run login
```

That script launches a normal Chrome or Edge window backed by a dedicated local profile outside Drive. Sign into RSNA manually there, confirm that a `RadioGraphics` article page loads normally, then press `Enter` in the terminal window. The login state stays in that local browser profile.

3. Run the pipeline once:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-review.ps1
```

4. If you want to rebuild outputs for already-seen recent articles, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-review.ps1 -IncludeSeen -Limit 3
```

## Scheduling

The preferred recurring setup is a Codex cron automation in this workspace. The automation can run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-and-publish.ps1
```

## Notes

- The first digest run uses a recent lookback window and treats unseen DOIs as new.
- If RSNA expires the session, rerun `npm run login`.
- Successful runs create:

```text
articles/<article-folder>/article.json
articles/<article-folder>/reader.html
articles/<article-folder>/assets/*.png
articles/<article-folder>/anki/*.apkg
index.html
articles/index.html
```

- Failed packaging runs do not mark the DOI as seen, so the next run can try again.
- If Cloudflare keeps challenging, the script is still usable in metadata-only mode.
- If you only want a metadata-only run, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-review.ps1 -NoEnrich
```
