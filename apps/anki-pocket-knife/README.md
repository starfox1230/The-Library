# Anki Pocket Knife

Anki Pocket Knife is a multi-tool add-on that bundles together a few focused workflow helpers in one place.

## Included tools

- `Early Review Deck`: reuses the existing early-review behavior and builds a filtered deck from tomorrow's review cards, prioritizing the longest intervals first.
- `Missed Today -> Copy Text`: copies the front/back text of every card you missed in the current Anki day.
- `Missed Today -> Save Text File`: writes that same export to a local text file inside `user_files`.
- `Missed Today -> Open HTML Viewer`: creates a local HTML page of cards missed today and rewrites image/media paths to local collection-media file URLs so images render outside Anki.
- `Missed Today -> Make Filtered Deck`: creates a filtered deck from today's missed cards with `resched = false`, so extra review does not affect future scheduling.
- `No-Image Today Deck`: lets you choose one or more exact deck levels, looks at the cards Anki is surfacing there today, filters to cards with no question-side image, and builds a `resched = true` filtered deck named `No image cards YYYY-MM-DD HH-MM-SS`. The same action is also available from the deck gear menu for a single deck. If the cards came from another filtered deck, Pocket Knife can move them out first and then rebuild the prior filtered deck automatically after the no-image deck is deleted.
- `Recent New Cards Deck`: builds a `resched = true` filtered deck from still-new cards created today or in the past few days, with a day-range prompt and both launcher/menu access plus a deck gear-menu entry for normal decks.
- `Saved Cards -> Send To .NEW::Audio`: on the exact `Saved Cards` deck gear menu, moves every card in that deck to `.NEW::Audio`, builds a `resched = true` filtered deck from the cards that were still new, names it `New cards from Saved Cards Deck (YYYY-MM-DD HH-MM-SS)`, and then deletes the emptied `Saved Cards` deck.
- `Recent Leeches Banner`: default-on deck-browser banner that appears above the main deck list whenever leeches from the last 48 hours are available, shows the count, and opens those cards in the Browser when clicked.
- `Open Suspended Cards In Browser`: opens all currently suspended cards in the Browser and orders them from most recently suspended to least recently suspended.
- `Filtered Deck -> Send Non-New Cards Home`: shows only filtered decks in a searchable picker, sends the selected deck's current non-new cards back to their original deck while keeping their current schedule, leaves still-new cards in place, and also appears in the deck gear menu for filtered decks.
- `Disable Default F3 Shortcut`: default-on toggle that removes Anki's built-in plain `F3` shortcut, so `F3` is left unused for your own workflow.
- `Add Cards -> Pink Picture-Frame Converter`: default-on button on the normal Add Cards screen that converts the current cloze note into `Visual_Card_Multitude`, sending cloze text to `English`, non-cloze text to `Question`, inline images to `Images`, and `Extra` to `More Info`. If you are already on `Visual_Card_Multitude`, the same button converts back to `saCloze++`, sending `Question` plus a clozed `English` block and `Images` into `Text`, and `More Info` back into `Extra`.
- `Add Cards -> Dx Diagnosis Template`: default-on `Dx` button beside the picture-frame button that is only enabled for cloze note types and rewrites the `Text` field to `Diagnosis?<br><br>{{c1::}}<br><br>` above any existing images, then places the cursor inside the empty cloze.
- `Add Cards -> Auto Deck Toggle`: toolbar toggle that can automatically switch cloze notes between `.NEW::Audio` and `.New::Visual` based on whether the `Text` field contains an image, and can also auto-switch `Visual_Card_Multitude` notes to `.New::Visual`.
- `Add Cards -> Live Multi-Image Counter`: optional setting that adds a `1/N` label above the first image in a cloze note's `Text` field when more than one image is present, keeps it updated as images are added, strips it during cloze-to-visual conversion, and recreates it when converting back to cloze.
- `Add Cards -> Tab Cycles Clozes`: default-on setting that changes `Tab` in the cloze note `Text` field so it cycles through cloze deletions instead of jumping to the next field. `Shift+Tab` cycles backward.
- `Auto-Scroll On Answer Reveal`: optional toggle that jumps the reviewer back to the top of the card whenever you reveal the answer.
- `TTS Card Audio Playback`: default-off toggle that lets you allow or suppress audio playback from TTS-enabled cards without muting normal non-TTS audio.

## Menu and shortcuts

- `Tools -> Anki Pocket Knife -> Open Pocket Knife Launcher`
- `Tools -> Anki Pocket Knife -> Build No-Image Today Deck`
- `Tools -> Anki Pocket Knife -> Build Recent New Cards Deck`
- `Tools -> Anki Pocket Knife -> Open Recent Leeches In Browser`
- `Tools -> Anki Pocket Knife -> Open Suspended Cards In Browser`
- `Tools -> Anki Pocket Knife -> Send Filtered Deck Non-New Cards Home`
- `Tools -> Anki Pocket Knife -> Disable Anki's Default F3 Shortcut`
- `Tools -> Anki Pocket Knife -> Recent-Leech Banner On Deck List`
- `Tools -> Anki Pocket Knife -> Auto Deck For Cloze Add Cards`
- `Tools -> Anki Pocket Knife -> Dx Diagnosis Button In Add Cards`
- `Tools -> Anki Pocket Knife -> Live Multi-Image Counter In Add Cards`
- `Tools -> Anki Pocket Knife -> Tab Cycles Clozes In Add Cards`
- `Tools -> Anki Pocket Knife -> Pink Picture-Frame Button In Add Cards`
- `Tools -> Anki Pocket Knife -> Auto-Switch Visual_Card_Multitude To .New::Visual`
- `Tools -> Anki Pocket Knife -> Auto-Scroll To Top On Answer Reveal`
- `Tools -> Anki Pocket Knife -> Play Audio From TTS-Enabled Cards`
- Default launcher shortcut: `Ctrl+Shift+Q` if Anki has not already claimed it
- Default early-review shortcut inside this add-on: `Ctrl+Alt+F`

If the standalone `early_review_deck` add-on is already installed, Pocket Knife deliberately leaves `Ctrl+Alt+F` alone to avoid double-binding the same shortcut.

## Install on Windows

From this folder, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\install_to_anki.ps1
```

That copies the add-on into Anki's default `addons21` directory as `anki_pocket_knife`.

The installer preserves `user_files`, so saved exports and generated viewer files survive reinstalls.

## Manual install

1. Open Anki.
2. Go to `Tools -> Add-ons -> View Files`.
3. Close Anki.
4. Create a folder named `anki_pocket_knife`.
5. Copy this folder's add-on files into it.
6. Start Anki again.

## Build a shareable package

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_ankiaddon.ps1
```

That creates `anki_pocket_knife.ankiaddon` in this folder.
