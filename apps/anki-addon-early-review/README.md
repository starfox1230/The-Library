# Early Review Deck

This folder is now a real Anki add-on, not just a code snippet page.

## What it does

- Adds `Tools -> Build Early Review Deck`
- Uses the shortcut `Ctrl+Alt+F`
- Prompts for how many cards to pull, defaulting to `50`
- Finds review cards due tomorrow
- Chooses the longest-interval cards first
- Builds or refreshes a filtered deck named `............... Early Preview Deck for YYYY-MM-DD`

## Install on Windows

From this folder, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\install_to_anki.ps1
```

That copies the add-on into Anki's default `addons21` directory as `early_review_deck`.

## Manual install

1. Open Anki.
2. Go to `Tools -> Add-ons -> View Files`.
3. Close Anki.
4. Create a folder named `early_review_deck`.
5. Copy `__init__.py` and `manifest.json` into that folder.
6. Start Anki again.

## Build a shareable package

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_ankiaddon.ps1
```

That creates `early_review_deck.ankiaddon` in this folder.
