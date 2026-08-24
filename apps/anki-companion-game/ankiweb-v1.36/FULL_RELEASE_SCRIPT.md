# Speed Streak v1.36 — Editable What’s New Script

## What this release needs to explain

1. Time Boost uses charges instead of points.
2. The user earns charges by answering cards.
3. A charge adds time when the user presses the Boost shortcut before the timer expires.
4. No Pause and No Undo are optional. They are useful for people who pause or undo reviews to keep a streak.
5. The old point and multiplier system is still available under the name Legacy Points.
6. Singularity and Crystal Reactor are new visual options.

## What’s New window

### Heading

**Speed Streak 1.36**

**What’s new**

> Speed Streak now has a Time Boost mode and two new visual options.

### Time Boost

> Time Boost uses charges instead of points. Answer cards to earn charges. Press R before time runs out to spend a charge and add time.

> If you often pause or undo to keep your streak, you can turn on No Pause and No Undo. Charges give you a limited way to get extra time instead.

Show the actual Speed Streak screenshot:

`speed-streak-addon-v1.36/whats_new_assets/time-boost-actual.png`

Text under the screenshot:

> Hover over the charges to show No Pause, No Undo, and R. Click the charges or progress bar to open their settings. Click R to change the shortcut.

> Change Time Boost: Settings → Gameplay · Change R: Settings → Shortcuts

### Legacy Points

> The previous point and multiplier system is now called Legacy Points. You can switch between Legacy Points and Time Boost at any time in Settings → Gameplay.

### New visuals

> Singularity and Crystal Reactor are new visual options. Click the visual button at the bottom-left of Speed Streak to switch.

Show the actual visual selector screenshot:

`speed-streak-addon-v1.36/whats_new_assets/visual-options-actual.png`

### Buttons

- `Open Gameplay Settings`
- `Done`

## How Time Boost works

1. Select **Settings → Gameplay → Gameplay Mode → Time Boost**.
2. Complete timed cards to fill the charge meter.
3. When the card requirement is reached, one charge is added to the bank.
4. Press the Boost shortcut before the active timer expires.
5. One charge is removed and time is added to the timer.

The normal Boost shortcut is **R**.

A charge cannot be used when the timer has already expired. It also cannot be used during a free, untimed, paused, or inactive phase.

## Settings locations

| Setting | Location |
| --- | --- |
| Legacy Points or Time Boost | Settings → Gameplay → Gameplay Mode |
| No Pause | Settings → Gameplay |
| No Undo | Settings → Gameplay |
| Seconds added per charge | Settings → Gameplay → Time Boost |
| Maximum charges | Settings → Gameplay → Time Boost |
| Starting charges | Settings → Gameplay → Time Boost |
| Cards required to earn a charge | Settings → Gameplay → Time Boost |
| Boost shortcut | Settings → Shortcuts |
| Visual mode | Click the visual button at the bottom-left during review |
| Visual colors | Settings → Visuals → Visual Colors |

## Screenshot source

The screenshots are rendered from the real v1.36 interface using:

- `speed-streak-addon-v1.36/web/overlay.css`
- `speed-streak-addon-v1.36/web/overlay.js`
- `ankiweb-v1.36/actual-ui-preview.html`

No generated artwork is used.

## AnkiWeb description

The paste-ready HTML is:

`ankiweb-v1.36/ankiweb-description.html`

The two screenshots must be committed and pushed before the HTML is pasted into AnkiWeb, because the description uses raw GitHub image URLs.

## Files to edit later

- Window wording and layout: `speed-streak-addon-v1.36/whats_new_dialog.py`
- Public AnkiWeb wording: `ankiweb-v1.36/ankiweb-description.html`
- Actual interface screenshot state: `ankiweb-v1.36/actual-ui-preview.html`
- One-time display behavior: `speed-streak-addon-v1.36/reviewer_overlay.py`
- This editable script: `ankiweb-v1.36/FULL_RELEASE_SCRIPT.md`
