# Next Up — Rotten Tomatoes to Notion

A personal Manifest V3 Chrome extension for Sterling’s existing Notion Watchlist. No build step or hosted backend. The installable folder is `extension/`; the ZIP contains that folder’s contents at its root.

## Install

1. Download `next-up-chrome-extension.zip` from the installation page and extract it to a permanent folder, or use this repository’s `apps/rt-notion-watchlist/extension` folder.
2. Open `chrome://extensions`, enable **Developer mode**, choose **Load unpacked**, and select the folder containing `manifest.json`.
3. Follow the setup screen to create an internal Notion connection with **Read content** and **Insert content**, share the Watchlist with it, and paste its secret **into the extension settings only**. Click **Connect & check Watchlist**.
4. Refresh a Rotten Tomatoes movie/show page. Click **Add to Watchlist** in the bottom-right Next Up card.

Chrome does not allow a website or ZIP to silently install an unpacked extension. This is not published to the Chrome Web Store. Updates: replace the extension files and click **Reload** on its card in `chrome://extensions`, then refresh Rotten Tomatoes. Keep the same folder to retain the extension ID and settings.

## Behavior

- Writes `Name`, `Status = For Later`, `Type = Movie / TV Show`, `Rotten Tomatoes`, and `Date Added to Watchlist` (the computer’s local calendar date).
- Adds a clickable source link inside the page. Leaves interest, reviews, thoughts, genre, platform and other personal fields empty. Does not apply a database template that might overwrite the initial status.
- Offers **Open in Notion** after saving, or can automatically open each newly created entry when enabled in settings.
- Checks the source URL before each save; an existing entry is opened without changing its status, ratings, or notes.
- Warns about a matching older title with no source URL and matching/empty Type. Open it to check, or explicitly choose **Add as a separate entry**. Remakes are never silently merged.
- Strips URL tracking, hashes, trailing slashes, and season/episode paths. TV seasons/episodes are saved as the parent show when a parent-show title link is available. Review/gallery pages don’t show the widget. Navigating between supported pages refreshes it.
- Serializes saves and coalesces concurrent requests for the same URL across tabs. Does not automatically retry a non-idempotent create request. After a lost response, retry checks Notion before creating again. Notion does not enforce a unique URL constraint: two different Chrome profiles/devices saving simultaneously can still create duplicates.

## Connection and privacy

The Notion connection in Codex cannot be transferred into an installed Chrome extension. Each Chrome profile must complete this one-time setup. Tokens are not checked into source or bundled in the ZIP. The token is stored in `chrome.storage.local`, restricted to trusted extension contexts with `setAccessLevel`, never `storage.sync`; it is not an encrypted vault. Content scripts receive save results only, never credentials. No analytics or third-party services.

Permissions: `storage`; network access only to `api.notion.com`; content scripts only on Rotten Tomatoes movie and TV URLs. No cookie, history, all-sites, scripting, or tabs permission. The worker validates sender origin, top frame, media URL and title; settings commands only accept the extension’s own settings page. API errors never echo request or response bodies. Requests time out after 20 seconds. **Disconnect** deletes the locally stored token; revoke the connection in Notion to invalidate the secret itself.

The fixed destination is data source `8a9a4d6e-106e-4da1-bcc2-b9a10a7083d7`, database `880c2a70-f634-4b5c-8824-f65fafd7f9f4`. These are identifiers, not credentials. Setup checks the actual data-source schema and read access without creating a test entry. Insert capability is checked by the first real save.

## Notion setup performed

Added the `Rotten Tomatoes` URL property and a **For Later · Quick Add** table view, filtered to For Later and sorted by Date Added to Watchlist descending. Existing entries and views are preserved. [Open Watchlist](https://www.notion.so/880c2a70f6344b5c8824f65fafd7f9f4?v=4031d7063539815db35a000cfc86069f).

## Development and validation

Run `npm test` (Node 20+). Run `python build.py` to regenerate the dependency-free ZIP and icons. Tests cover Notion payloads, schema drift, duplicate handling, timeout/error reporting, source validation, and worker authorization/concurrent saves. The browser smoke test checks the injected widget and setup screen against mocked Chrome/Notion APIs; it does not claim a live Notion insert.

API references: [Notion create page](https://developers.notion.com/reference/post-page), [query data source](https://developers.notion.com/reference/query-a-data-source), [Chrome cross-origin requests](https://developer.chrome.com/docs/extensions/develop/concepts/network-requests), [Chrome storage](https://developer.chrome.com/docs/extensions/reference/api/storage). API version pinned to `2026-03-11`.
