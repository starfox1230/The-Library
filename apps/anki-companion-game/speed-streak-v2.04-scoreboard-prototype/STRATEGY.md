# Proposed 2.04 run-history strategy

## Primary metric

Use **peak Speed Streak card count** as the primary record. Time Boost mode does not use Legacy Points, so a points-only high score would exclude the default gameplay mode. Legacy score can be retained as secondary run metadata.

## Run lifecycle

- A run begins when the game streak moves from 0 to 1 through a real completed review.
- A run continues through manual pauses, automatic non-review pauses, leaving and returning to Review, and an Anki restart when Restore Active Run is enabled.
- A run ends when a timeout or deliberate game reset changes a positive streak to zero, or when Anki closes while active-run restoration is disabled.
- Again does not end a run because current Speed Streak rules count a timely Again as another completed card.
- Developer test-streak controls never create or alter stored run records.
- A zero-card attempt is never stored.

Pausing and restoring are valid existing game mechanics. Record `pause_count`, `paused_ms`, and `resumed_after_restart` as neutral details rather than invalidating the run or branding it as cheating.

## Recommended display

Keep one thin, always-visible target strip beneath the timer/economy area:

```text
BEST 168                     LIVE #3 vs 5 · 82 TO GO
```

Clicking the strip opens a temporary ladder over the visual stage. It should not permanently shrink the stage or add a second external window.

Default comparison behavior:

- Select the five most recently completed runs.
- Display those five by score, highest first, because the purpose is climbing.
- Keep a relative date/time on each row so recency remains clear.
- Insert the active run as a highlighted `LIVE` row and animate it into a new rank when it passes another run.
- Phrase the rank as `#3 vs last 5`, because LIVE is being compared with five completed runs rather than being one of them.

Settings can offer one compact choice:

```text
Run target: Off | Best only | Recent 5 | Best 5
```

Avoid separate controls for chronological/ranked ordering in the first production version. Recent 5 should be selected by chronology but displayed as a ranked ladder; timestamps preserve the chronological information.

## Records and corrections

Create a dedicated `runs` table rather than deriving game runs from the existing review-events table. The existing `longestStreak` statistic measures consecutive correct answers, which is not the same as the Speed Streak gameplay streak.

Suggested fields:

- `id`, `started_at`, `ended_at`, `end_reason`;
- `peak_streak`, `ending_streak`, `legacy_score`, `gameplay_mode`;
- `cards_completed`, `active_ms`, `pause_count`, `paused_ms`;
- `resumed_after_restart`, `used_undo`, `boosts_used`;
- optional `deleted_at` for recoverable deletion.

The all-time best should always be calculated from non-deleted completed runs. Do not maintain a separate high-score number that can become inconsistent.

Provide run-history management in Settings or Stats:

- delete one selected completed run;
- reset all completed run history with confirmation;
- discard the active run separately, with explicit wording;
- recalculate BEST immediately after deletion or reset.

## Celebration

Trigger a restrained `NEW BEST` ring/glow once when the live streak first exceeds the best completed run. Do not interrupt the card or cover the timer. Store the completed record only when the run ends. Undo integration must restore the run tracker snapshot so an undone review cannot permanently inflate the run peak.
