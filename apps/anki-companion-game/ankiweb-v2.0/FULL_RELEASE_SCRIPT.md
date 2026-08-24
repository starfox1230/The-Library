# Speed Streak 2.0, complete editable release script

This file is the plain-language source for the one-time in-add-on window and the AnkiWeb page. It is intentionally direct. The screenshots come from the real 2.0 interface; no generated artwork is used.

## Release order

1. Introduce Boosts as the main change.
2. Explain why they exist: a limited alternative to using Pause or Undo to preserve a streak.
3. Point to the Boost bank, its meter, the No Pause/No Undo controls, and the shortcut.
4. Say clearly that Legacy Points is still available.
5. Briefly show Fusion, Singularity, and Crystal Reactor.

## In-add-on What’s New window

### Small heading

> WHAT’S NEW

### Main heading

> Boosts ⚡

### Opening copy

> Time Boost is now the default. Complete cards to earn Boosts. Press C before the timer expires to use one and add time.

> I added this because I found myself cheating by using Pause and Undo to protect a streak.

Show `NO PAUSE` and `NO UNDO` as small inline pills matching the controls in the review window, followed by:

> are off by default, but can be turned on to counteract the urge to cheat. Hover over the Boost bank to reveal them and toggle them on or off.

> Boosts ⚡ give you a limited way to add time when you get distracted or cannot answer quickly enough, without pausing or undoing the review.

### Main screenshot

`speed-streak-addon-v2.0/whats_new_assets/boosts.png`

This is a 1280 × 720 capture rendered at double scale from the real review interface. It shows the timer, three Boost slots, the Next Boost meter, No Pause, No Undo, the C shortcut, and the Legacy Points switch.

### Three short instructions

1. **Earn**, every card you complete advances the Next Boost meter. A full meter adds one Boost to the bank.
2. **Use**, press the shortcut shown under the bank before time expires. The default shortcut is C.
3. **Adjust**, click the Boost bank for its gameplay settings. Click the shortcut key to change the key.

> New runs start with 3 of 5 Boosts. Both values are configurable in Gameplay settings.

### Legacy Points line

> Prefer the old score and multiplier? Legacy Points is still available in Settings → Gameplay.

### Visual heading

> New visual options

### Visual copy

> Fusion is the new default satellite style. Singularity and Crystal Reactor are also available. Click the visual button at the bottom-left during review to switch.

### Visual screenshots

Display these in one row:

- `fusion-248.png`, label: `Fusion`
- `singularity-248.png`, label: `Singularity`
- `crystal-53.png`, label: `Crystal Reactor`

Each image is a 1280 × 720 capture rendered at double scale by the actual 2.0 visual code.

### Footer

Left side:

> Reopen this from Speed Streak → What’s New.

Buttons:

- `Open Gameplay Settings`
- `Done`

## AnkiWeb page script

### Intro

> Speed Streak adds a timer and streak to desktop Anki reviews. It is designed to help you answer faster and keep moving when a card is taking too long.

### New: Boosts

> Time Boost is now the default gameplay mode.

- Complete cards to earn Boosts.
- Press **C** before the timer expires to use one and add time.
- Choose how many Boosts you can hold, how many cards earn one, and how much time each one adds.

> I added this because I found myself cheating by using Pause and Undo to protect a streak.

Show the `NO PAUSE` and `NO UNDO` pills, then explain:

> They are off by default. Hover over the Boost bank to reveal them, or change them in Speed Streak → Settings → Gameplay.

> Boosts ⚡ give you a limited way to add time when you get distracted or cannot answer quickly enough, without pausing or undoing the review.

Show `boosts.png` at full width.

### Where to change it

- Click the Boost bank during review to open its settings.
- Click the shortcut key below the bank to change the key.
- Or open **Speed Streak → Settings → Gameplay**.

> New runs start with 3 Boosts and can hold up to 5. These values are configurable.

> The previous score and multiplier system is still available as Legacy Points in Gameplay settings.

### New visual options

> Fusion is the new default satellite style. Singularity and Crystal Reactor are also available. Click the visual button at the bottom-left during review to switch.

Show the same three screenshots in a row with the labels used in the in-add-on window.

### Also included

- Separate question and answer timers
- Optional timer rules for note types, tags, typed-answer cards, and AnKing one-by-one cards
- Time Drain and Review Later flags
- Review Later Manager
- Optional audio and controller haptics
- Inline side panel or separate external window
- Saved external-window positions

Final note:

> Desktop Anki only. Existing settings are preserved. No Pause and No Undo are optional.

## Exact settings locations

| Setting | Location |
| --- | --- |
| Time Boost or Legacy Points | Settings → Gameplay → Gameplay mode |
| No Pause | Settings → Gameplay |
| No Undo | Settings → Gameplay |
| Time added per Boost | Settings → Gameplay |
| Boost bank capacity | Settings → Gameplay |
| Starting Boosts | Settings → Gameplay |
| Cards required to earn a Boost | Settings → Gameplay |
| Boost shortcut | Settings → Shortcuts |
| Visual mode | Visual button at bottom-left during review |
| Visual colors | Settings → Visuals → Visual Colors |

## Screenshot source and reproduction

The source page is:

`ankiweb-v2.0/actual-ui-preview.html`

It imports:

- `speed-streak-addon-v2.0/web/overlay.css`
- `speed-streak-addon-v2.0/web/overlay.js`

The 1280 × 720 browser captures are retained in:

`ankiweb-v2.0/source-captures/`

States used:

| Asset | Preview query |
| --- | --- |
| Boosts | `?preview=boost&visual=sphere&sphere=fusion&streak=27&scale=2` |
| Fusion | `?preview=visual&visual=sphere&sphere=fusion&streak=248&scale=2` |
| Singularity | `?preview=visual&visual=singularity&streak=248&scale=2` |
| Crystal Reactor | `?preview=visual&visual=crystal&streak=53&scale=2` |

The public paste-ready HTML is `ankiweb-v2.0/ankiweb-description.html`. Commit and push the four final screenshots before pasting that HTML into AnkiWeb because its image URLs use the GitHub `main` branch.

## Files that control the release later

- Window wording and layout: `speed-streak-addon-v2.0/whats_new_dialog.py`
- Public AnkiWeb wording: `ankiweb-v2.0/ankiweb-description.html`
- Screenshot state: `ankiweb-v2.0/actual-ui-preview.html`
- One-time display behavior and permanent menu action: `speed-streak-addon-v2.0/reviewer_overlay.py`
- This editable script: `ankiweb-v2.0/FULL_RELEASE_SCRIPT.md`
