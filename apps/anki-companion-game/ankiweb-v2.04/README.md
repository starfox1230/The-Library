# Speed Streak 2.04 AnkiWeb listing

`ankiweb-description.html` is the paste-ready AnkiWeb description. It deliberately uses conservative HTML—headings, paragraphs, lists, tables, links, and raster images—so the page remains useful even if AnkiWeb removes decorative inline styling.

The images are hosted from the public `henbitdeathmetal/anki-speed-streak` GitHub repository under `ankiweb/v2.04/assets`. They must be committed and pushed to `main` before the description is published on AnkiWeb. No separate website or image host is required.

## Local preview

Serve this directory over localhost and open `preview.html`. The preview rewrites the future GitHub image URLs to the local `assets` directory.

```powershell
python -m http.server 8766 --bind 127.0.0.1
```

## Publish order

1. Commit and push this directory so every `raw.githubusercontent.com` image URL resolves.
2. Open the Speed Streak add-on editor on AnkiWeb.
3. Replace the description with the complete contents of `ankiweb-description.html`.
4. Preview the result and confirm that all eight images load.
5. Save the description.

The current page links to:

- AnkiWeb review page: `https://ankiweb.net/shared/info/1237336370`
- Reddit feedback: `u/henbitdeadnettle92`
- Ko-fi: `https://ko-fi.com/ankispeedstreak`
- Source: `https://github.com/henbitdeathmetal/anki-speed-streak`
- Controller setup: the existing Notion instructions

An animated demo can be added later without restructuring the page. Replace or precede the hero `boosts.png` image with a hosted GIF or video link after a concise, representative recording is available.
