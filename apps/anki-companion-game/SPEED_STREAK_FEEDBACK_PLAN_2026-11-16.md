# Speed Streak: feedback assessment and implementation handoff

Reviewed: November 16, 2026. Status: **proposal for Sterling's review**.
This change adds this document only. No add-on behavior, installed files,
packages, Anki data, or AnkiWeb release have been changed.

## 1. What people requested and what I recommend

Primary source: [Speed Streak on AnkiWeb](https://ankiweb.net/shared/info/1237336370),
read in a JavaScript-enabled browser on the review date. Dates below are the
dates displayed by AnkiWeb; edited reviews may describe later developments.
These are paraphrases, not quotations. The page has no individual review links.

| ID | Review date | Request/report | Assessment | Proposed disposition |
| --- | --- | --- | --- | --- |
| A | Nov 5 | Deck completion does not save the streak; breaking it does. | Record durability should not depend on failure. | Highest priority: investigate and fix saving. |
| B | Nov 1 | Optional pause and flag buttons for tablet/AnkiDraw use. | Useful accessibility improvement with limited scope. | Recommend optional touch controls. |
| C | Nov 10 | Show accumulated saved time; possibly a snake competing against a personal best. | Interesting, but the metric needs a precise definition. | Consider a counter first; defer the snake. |
| D | Sep 17 | A quieter/smaller timer, no fractional seconds, perhaps an hourglass. | Some appearance controls already exist in development. | Validate those first; consider size/reduced motion separately. |
| E | Sep 4, edited | Rating audio fails or selections revert after restarting. | Reliability issue with existing diagnostic/fix work. | Reproduce against a named build before adding another fix. |

The Oct 20 review is positive feedback without an actionable request.
No newer review than Nov 10 was visible at inspection.

**Recommended first release scope:** A plus B, after approval. D and E should
be checked against existing development work. C changes the reward system and
deserves its own decision. These recommendations are not approval to implement.

### Older feedback: keep it visible without reopening solved requests

| Dates | Earlier topic | Current assessment / next action |
| --- | --- | --- |
| Aug 29 | Best/five runs; macOS rumble. | Record UI exists; hardware validation remains necessary. |
| Aug 27 | A replenishing shared time bank instead of per-card pressure. | Manual Boosts differ from an automatic shared bank. Separate proposal F below. |
| Jul 17; Apr 23; May 26 | Note-type, one-by-one and typed-answer timing. | Special timer implementations exist; verify before adding duplicates. |
| Jul 15; Mar 31/25 | Long-streak rendering, CPU/battery and smooth timers. | Performance work exists; real-machine measurements remain necessary. |
| Jun 23; Mar 25/23 | Hide panel/window; narrower/right-side pane. | Panel visibility/right-side controls exist; arbitrary width needs separate review. |
| May 24; Mar 24 | Pause hotkey conflicts. | Configurable shortcuts exist; retain compatibility regression checks. |
| May 19; Mar 25/24/29 | Haptic controls, audio alternative and Mac playback. | Settings/audio implementations exist; avoid promising universal hardware support. |
| Apr 21 | Linux Flatpak inline mode; deprecated flag API. | Platform verification needed; current flag reader prefers `user_flag`. |
| Apr 19 | DualSense haptics; light appearance. | Review reports haptics resolved; verify available themes before adding another. |
| Mar 24 | Keep streak across restart; longest-streak stats; flag/defer workflow. | Resume preference, stats, Review Later and Time Drain exist; permanent automatic deck moves are a separate behavior. |
| Mar 23 | Deduct a point and restart timer instead of breaking streak. | Distinct gameplay rule; defer unless explicitly selected. |

The older items are context, not a mandate to implement everything.

## 2. Which version is which

Evidence was read from the **original working directory**
`C:\Users\sterl\Documents\GitHub\The-Library`, including its uncommitted files.
This plan is committed in an isolated worktree so those files remain untouched.
Original HEAD at inspection: `4975172e229c649bfd5a1dddf9bf3940643595cd`.

| Copy | Evidence | Interpretation |
| --- | --- | --- |
| AnkiWeb | Page describes 2.04; updated Sep 17, 2026. | Advertised public release is 2.04. The downloadable archive was not independently fingerprinted. |
| Public source | [henbitdeathmetal/anki-speed-streak](https://github.com/henbitdeathmetal/anki-speed-streak), README and folder list. | Public source documents 2.04; it does not contain these local 2.05–2.07 tracks. |
| Local 2.05 | `2.05-user-requests.14+diagnostics.1+time-drain-undo.1` | Standard candidate with user-request changes and unfinished local edits. |
| Local 2.06 | `2.06-user-requests.14` | Experimental visuals/Hypernova track. |
| Local 2.07 | `2.07-sprint-time.6+diagnostics.1+time-drain-undo.1` | Experimental Sprint Time track. |
| Installed | `%APPDATA%\Anki2\addons21\speed_streak_v2_07`; label `2.07-sprint-time.6+time-drain-undo.1` | Installed source substantially matches local 2.07 in the files checked. |

Installed/repository byte comparison: `run_history.py`, `stats_store.py`,
`reviewer_overlay.py`, `game_state.py`, `audio_feedback.py`, `web/overlay.js`,
and `web/card_timer.js` match. `build_info.py` differs. This was an eight-file
comparison, not a complete installation/package audit or proof of what the
already-running Anki process has loaded.

`SPEED_STREAK_VERSION_TRACKS.md` in the original working directory explains the
standard/experimental split and a prior answer-animation regression. It was
untracked when read. Do not assume it or all inspected fixes exist in a fresh
GitHub checkout. Many 2.05 edits and unrelated repository changes were present.

### Required baseline procedure for the implementing agent

1. Get approval for ticket IDs and the target track. Suggested target: standard
   2.05; forward-port approved behavior to 2.07 without importing its visuals.
   Confirm whether 2.06 is still maintained before changing that additional copy.
2. Read root/app instructions, the local track document, build IDs and diffs.
   Record source commit plus the approved uncommitted baseline. A fresh checkout
   must first receive the intended existing work through a separately reviewed
   commit; this document does not contain that work.
3. Work on a dedicated branch/worktree. Never overwrite, commit or discard
   unrelated pending edits. Do not start from an old numbered folder just because
   its version looks stable. Prefer a narrow change to the chosen current track.
4. Before implementation, capture one baseline review session covering normal
   ratings, final-card completion, Undo, Time Drain and pause rules. Record the
   actual Anki version and build label.
5. Use the symbols below as anchors; line numbers are deliberately omitted
   because local edits move them. Proposed new symbols/keys are marked as such.

## 3. Ticket A — save records without requiring a streak break

**Recommendation:** durable checkpoints for a continuing run. Do not make deck
completion reset a streak by default. A streak can legitimately span decks.
Alternative, only if Sterling prefers it: finish the run at natural deck completion,
then define and test last-card Undo across that boundary. Do not silently choose
that alternative during implementation.

### Finding and confidence

`ReviewerOverlayController._finalize_rate()` calls
`RunHistoryTracker.observe_answer()`. That updates an in-memory active run.
`_handle_non_review_state()` calls `begin_review_exit()` and safety-pauses;
it does not save a completed run. `complete()` calls `_record_active()`, which
inserts the record through `StatsStore.record_speed_streak_run()`.
`display_payload()` distinguishes live best from saved best and saved rows.

An isolated probe against local 2.05 produced **zero saved rows after an answer
and Review exit**, despite a live best of 12; calling `complete()` produced one.
That supports the report, but is not a live-Anki reproduction of natural deck
completion. Settings also persist runtime state, so this is not proof every exit
permanently loses data. The difference between a restorable run and a visible,
durable record is central to the fix.

### Proposed implementation contract

Files: `run_history.py`, `stats_store.py`, `reviewer_overlay.py`,
`stats_dialog.py`, and record rendering in `web/overlay.js`.

1. Give each new logical run a UUID, proposed active key `runUid`. Allocate on
   its first counted answer; preserve it across checkpoint, navigation and restart.
   Do not derive identity from streak length, deck or a second-resolution time.
2. Extend `speed_streak_runs` additively with proposed columns `run_uid TEXT`,
   `record_state TEXT NOT NULL DEFAULT 'completed'`,
   `checkpoint_payload TEXT`, and `checkpoint_revision INTEGER NOT NULL DEFAULT 0`.
   Add a unique partial index on non-null `run_uid`. Old rows retain their IDs,
   rank data and completed status. Migration must be transactional and repeatable.
3. Add proposed `checkpoint(state)` and a shared record-serialization function.
   Upsert one row per UUID as `record_state='active'`; persist the complete
   normalizable tracker payload in the same transaction as its record columns.
   Use that payload/revision as recovery authority for run history. Existing
   settings runtime still controls live engine restoration; reconcile by UUID
   and matching streak, never combine mismatched runs. If runtime cannot resume,
   keep the record and close it as interrupted rather than inventing gameplay.
4. Checkpoint after a counted answer, after an applied review Undo, and once on
   the Review-to-non-Review transition. Flush at profile close. Pause/resume,
   boost-use and purity-changing events also checkpoint when an active run exists.
   Do not write on every 100 ms tick or on every browser render.
5. Keep the tracker active after checkpoint. Final completion updates that same
   row to `completed` with the actual end reason, then clears active state only
   after the transaction succeeds. Duplicate exit/close hooks must be idempotent.
   At a checkpoint, existing non-null `ended_at` can hold the checkpoint time;
   UI must label it as last saved, not as a completed end time.
6. Query best/recent/today using checkpoint rows as eligible records. Show
   **In progress** or **Saved — continuing**. The overlay's active row and saved
   row must not appear twice. Update detail lookup, ranking and purity queries
   together; adding rows without fixing all views is incomplete. Compute the
   benchmark/new-best indicator against other UUIDs, excluding the current run,
   so checkpointing does not make a new record compete against itself.
7. Preserve the current calendar-day definition of Today. Active checkpoints
   use their most recent progress date for Today and recent ordering; navigation
   alone must not turn yesterday's performance into today's record. This can be
   implemented by retaining last-progress time in checkpoint `ended_at`.
8. Review Undo lowers that same checkpoint and restores active time/progress.
   Undo to zero removes the provisional row and active identity. Final-card Undo
   after leaving Review must update the existing UUID. Re-answering must not
   insert a second run. Unrelated collection Undo does not change the checkpoint.
9. Preserve existing Pure rules: Review departure currently makes a run impure.
   A saved record can therefore disappear from the Pure filter after exiting;
   explain that state rather than pretending it was not saved. If Sterling wants
   successful deck completion exempted, that requires a separate rule decision.
10. Deleting/resetting records must not resurrect an active checkpoint on the
    next tick. If deleting the current active record, suppress persistence for its
    UUID until that run ends; retain a tombstone and honor it during restore.
    A fresh run gets a fresh UUID. Deletion should explain this effect in the UI.
11. On SQLite failure, retain in-memory active state, report a concise save error,
    and retry at the next explicit save event. Do not mark success or erase the
    run first. Profile switching must bind to that profile's own database.
12. Migrate legacy restored active payloads without UUID once, persist the new
    identity, and never match an old completed row by score alone. Back up the
    database/config before migration. Downgrades may not understand checkpoint
    lifecycle: test against a copied profile and restore the backup if rolling
    back, rather than claiming unrestricted downgrade safety.

Benchmark checkpoint serialization and SQLite commits with the existing bounded
5,000-entry progress payload. Measure rating-to-next-card latency before/after;
do not ship a new visible hitch. Reuse transactions and skip unchanged writes.
If deferred I/O is needed, snapshot immutable payloads with ordered revisions,
flush on exit, and leave reviewer/animation callback ordering unchanged. A failed
write must not advance the acknowledged revision. Do not introduce an unbounded
per-answer worker queue to make a benchmark look faster.

### Acceptance cases

| Scenario | Required result |
| --- | --- |
| Answer last due card; see finished screen | One saved record immediately; no timeout needed. |
| Leave manually, switch decks, open settings, close Anki | Last earned result retained; continuation follows current preference/rules. |
| Finish with Again and a learning delay remaining | Save progress without relying on a simplistic zero-card test. |
| Repeated non-Review ticks/close hooks | One logical row, never duplicates. |
| Undo final answer, then answer again | Same run corrected and updated exactly once. |
| Timeout/reset after earlier checkpoint | Same row becomes completed. |
| Resume on/off; two profiles; legacy data | Correct independent records and truthful lifecycle. |
| Delete current record; reset all records | No resurrection of that UUID. |
| Today/best/recent/Pure/detail views | Correct rank, dates and explicit in-progress state. |
| Inject database failure | Memory retained; visible retryable failure; no false save confirmation. |

## 4. Ticket B — optional touch controls

**Proposed default:** off, preserving existing layouts. Settings label:
**Show touch controls during review**. Buttons: Pause/Resume, Review Later,
Time Drain. A direct Use Boost button can be included if Sterling selects it;
the current Boost keycap opens shortcut settings and must retain that function.

Files: controller, `settings_dialog.py`, `config.json`, `web/overlay.js`,
`web/overlay.css`, `web/card_timer.js`, `web/card_timer.css`. A small shared
touch-controls asset/module is preferable to duplicating the action logic.

1. Proposed preference `touch_controls_enabled=false` must round-trip through
   native settings, controller load/save, exports, defaults and all relevant tracks.
2. Put a compact labelled row in the side panel for inline/external mode. If the
   panel is hidden, render the same controls in a small reviewer toolbar even if
   the top countdown is hidden. It must not require hover, right-click or keyboard.
   Maintain a visible Resume control above the paused/dimmed layer.
3. Use real buttons, accessible names/pressed states, at least 44 CSS-pixel targets,
   keyboard focus and adequate contrast. Wrap on narrow windows; avoid overlaying
   answer buttons, drawing areas, typed-answer input or the timer context menu.
4. Route Pause/Resume through a common controller action used by the existing
   `speed-streak:toggle-pause` bridge and shortcuts. Keep No Pause rejection,
   manual-pause bookkeeping, feedback and 2.07 Sprint reset behavior identical.
   Disabled/rejected commands must not alter the timer or animation nonce.
5. Proposed flag commands carry action plus expected card ID. Validate that the
   caller is a Speed Streak/reviewer surface, Review is active, and the current
   card still matches before acting. Ignore stale/delayed commands after a rating.
   Never accept an arbitrary collection search or list of cards from the browser.
6. Use the configured runtime flag colors, never hardcoded blue/red. If the
   current card already has the chosen flag, clear it; otherwise replace its
   single Anki flag. Explain replacement in the setting/help text. Disable a
   button if its flag is unconfigured; preserve existing conflicting-flag checks.
7. Perform flag changes through Anki's current collection-operation/Undo path,
   preserving non-flag bits. Check the installed Anki API rather than guessing
   method names. Reuse existing `_sync_live_flag_state()` and Review Later sync;
   do not bypass Time Drain auto-pause, cohort timestamps, undo classification or
   the 2.07 same-card-unflagging tracker. Do not rate, bury or move a card just
   because it was flagged.
8. Bind one activation handler per button. Do not combine touchend and click
   handlers that toggle twice. Restore reviewer focus after pointer activation
   without stealing focus during AnkiDraw strokes or typed answers.

Tests must cover a real tablet/touch review if available, mouse and keyboard,
hidden panel/top bar, paused state, No Pause, question/answer sides, changed flag
colors, flag replacement/removal/Undo, rapid next-card transitions and AnkiDraw.
Use bridge-unit/DOM tests for deterministic behavior, plus real Anki for focus.

## 5. Ticket C — optional saved-time metric, then perhaps a rival

**Decision required:** whether this reward is desirable. Fast self-ratings can
increase the number without proving better learning. Name it **Time under your
timer budget**, with a short explanation; do not claim measured life-time saved.
Sprint Time measures uninterrupted review duration and is a different metric.

### C1: proposed counter specification

Files: a proposed pure `saved_time.py` module; integration in `game_state.py`
and controller; optional columns/payload in history/store; settings and overlay.
Feature defaults off. Start with a counter, no changes to actual countdown rules.

* Unit: integer milliseconds. At each phase start freeze its effective base
  budget after special/deck/tag rules, **before Boost additions**, and its timer
  eligibility. Exclude free-entry phases, untimed phases, Time Drain phases and
  phases whose timing policy changes mid-card. Count only timed active elapsed;
  exclude manual/safety pause intervals.
* At a committed rating, for each eligible phase compute
  `max(0, base_budget_ms - active_elapsed_ms)`. Sum question and answer values.
  Example: 10 s question + 5 s answer, taking 6 s + 3 s, earns 6 s.
  A question that uses 12 s after Boost earns zero for that phase, not negative
  savings and not extra credit from the Boost. A question using 8 s of a 10 s
  base earns 2 s even if a Boost was available/used.
* Proposed eligible ratings: Good and Easy. Again/Hard earn zero savings, while
  keeping their existing effect on streaks and Boost progress. Do not add another
  rating settings matrix in the first version. This is a proposed policy, not a
  claim that these buttons objectively measure correct recall.
* Add the contribution exactly once per committed review event; question/reveal
  callbacks and repaints do not award it. A review Undo subtracts that event's
  contribution. Redo/re-answer awards once. Include counters in runtime snapshots
  and checkpoint payloads; a missing legacy value means unknown, not fabricated
  historical savings. Reset the run total with the logical streak run.
* Record a versioned policy signature with rating rule, timing rules and mode.
  Compare best totals only under the same policy. If those settings change mid-run,
  reset only the saved-time segment and benchmark; keep the ordinary streak and
  mark the segment boundary. Existing streak ranking stays based on streak count.
* Display `m:ss` with a tooltip; update on committed events. Hidden feature should
  create no animation loop. Explain that easier cards and generous timer settings
  affect the metric. Never backfill it from historic average review durations.

Test example totals, timed/untimed mixtures, special timers, free first card,
Boosts, overtime, pauses, Time Drain, accepted/rejected rating, Undo to zero,
restart and policy changes with a fake clock. Persist through A's checkpoint path.

### C2: snake/rival visual — explicitly deferred

If approved later, implement as an optional new visual, leaving existing modes
available. It must not alter scoring, timers or scheduling. Avoid collision-driven
failure until separately requested.

Use two normalized tracks on the same fixed board. The player's length represents
saved-time total; the ghost replays the best comparable record at equal active
review elapsed time. Freeze the benchmark at run/segment start so it cannot chase
itself. New records need bounded `(active_ms, saved_ms)` progress points; old
records cannot supply a ghost. With no compatible record show the player alone.
Interpolate ghost values between stored points, never extrapolate beyond its end.
Show an explicit lead/lag label. Cap rendered segments, use one canvas, pause
rendering while hidden/non-Review, and provide a static reduced-motion form.
No DOM node per card; test 1,000+ cards and actual energy use before shipping.

## 6. Tickets D/E and separate gameplay proposals

### D: finish the quieter-timer work first

2.05's `request_preferences.py` normalizes `decimal`, `seconds`, `hidden`.
`request_controls.py` exposes independent circle and horizontal number controls;
`tests/test_user_requests.py`, `tests/test_request_timers.cjs` and
`USER_REQUESTS_TEST_CHECKLIST.md` cover them. They also cover answer-side untimed
mode, deck rules and rating-based Boost earning. Verify existing behavior and
publication status before reimplementing it. The author's reply alone does not
prove these features are in the current downloadable AnkiWeb archive.

If a smaller timer is still desired, proposed settings are visual scale presets
75/100/125%, default 100%, applied through CSS variables to both relevant surfaces
with a minimum 44-pixel interactive target. No change to deadlines/audio. A proposed
reduced-motion option should suppress decorative pulses while retaining a smooth
progress bar. Test zoom, high DPI, narrow external windows and mixed number modes.
Defer a dedicated hourglass until the existing quiet options are evaluated.

### E: verify the audio fix already underway

Read `SPEED_STREAK_AUDIO_LIFETIME_HOTFIX.md` and
`SPEED_STREAK_MACOS_BROWSER_AUDIO_FIX.md` before changing playback. Inspect
`audio_feedback.py`, `data_paths.py`, feedback preferences and
`on_profile_did_open()`. Local code rebinds profile storage and preserves selected
audio keys; pending 2.05 edits already touch this path. Do not equate an accepted
playback request with audible sound.

On Windows, use an isolated profile with distinct packaged WAV, packaged MP3 and uploaded
files for each rating. Cold-start Anki, play the first real review event, preview
both diagnostic backends, restart, switch profiles, and reinstall a copied build.
Check that selected key, resolved file and diagnostic-selected file agree and
remain unchanged. Test missing uploaded media without silently overwriting the
saved selection. Run `tests/test_audio_feedback.py` and relevant browser/audio
tests. If reproduction persists, isolate one failing path and add a regression
case before editing it. macOS/haptics claims require real platform/hardware tests.

### F: automatic shared bank — a separate optional gameplay mode

This older request is not satisfied exactly by manual Boosts, and is not C's
saved-time counter. Do not merge their meanings.

If selected: add an opt-in mode with proposed defaults of 120 s initial time,
12 s replenished after each accepted rating, cap 120 s. Drain during active
question and answer review; freeze during pauses, non-Review and untimed/Time
Drain phases. Again/Hard replenish too under the proposed default, so users need
not misrate to protect the bank. Boosts are disabled in this mode and their
settings/balance retained for switching back. At zero, end this run once and
require an explicit restart; never loop timeouts or automatically rate a card.
Use a monotonic clock for elapsed time and snapshots for Undo. Settings changes
end the current bank run before applying new rules. Define a separate benchmark
policy and exercise zero-boundary races, sleep/wake and Undo. Sterling should
approve the drain/earning rules before coding this larger change.

### Other deferred changes

* Arbitrary sidebar width: add a clamped persisted width only after checking
  `_apply_sidebar_width()` and floating geometry constraints; retain collapsed
  width and per-monitor bounds. Default remains existing width.
* Automatic move-on-flag: prefer existing Review Later/filtered-deck workflow.
  Permanent deck moves change study organization and need an explicit design.
* Deduct-one-point timeout: opt-in Legacy Points rule only if approved; preserve
  streak meaning and separate records. Never silently change default timeouts.
* Linux Flatpak inline repair and Mac energy/haptics: first reproduce on those
  platforms, then assign a specific defect. Windows-only tests cannot close them.

## 7. Execution order and verification handoff

1. Select ticket IDs and reconcile the approved baseline (section 2).
2. Implement A alone; migration + tracker tests, then last-card live-Anki QA.
3. Implement B alone; action tests, then touch/focus QA. Keep it optional.
4. Validate already-existing D/E behavior and make only reproduced fixes.
5. Implement C1, C2 or F only if explicitly selected, in separate changes.
6. Forward-port approved shared behavior; preserve each maintained track's
   distinct visuals and Sprint semantics. Do not wholesale-copy controllers.
7. Generate web assets, build the selected package, verify source/archive equality,
   exclude tests/caches/user data, and verify stable package identity/conflicts.
   Review local installers for every known track: 2.05's inspected previous-folder
   list omits `speed_streak_v2_07`, so switching back needs installer correction
   or an explicit tested removal list before claiming one active installation.
8. Commit/push only completed approved changes, give a repository link, and keep
   AnkiWeb publication separate. No public release approval is implied here.

Existing targeted test commands, from repository root (run each as a separate
command; use the corresponding selected-track path):

```powershell
python -B apps/anki-companion-game/speed-streak-addon-v2.05/tests/test_run_history.py
python -B apps/anki-companion-game/speed-streak-addon-v2.05/tests/test_stats_records.py
python -B apps/anki-companion-game/speed-streak-addon-v2.05/tests/test_user_requests.py
node apps/anki-companion-game/speed-streak-addon-v2.05/tests/test_request_timers.cjs
python apps/anki-companion-game/tools/verify_release_tracks.py
```

The track verifier checks shared-file parity and built packages. It is a final
gate after ports/builds, not evidence that existing local differences are safe.
Record baseline failures before changing anything; do not weaken assertions just
to make divergent tracks pass. Add meaningful behavior tests for A/B/C/F as needed.

Real Anki release checks must also cover Again/Hard/Good/Easy transitions,
satellite arrival/displacement, experimental formation effects if applicable,
rejected No Pause commands, Undo, both display modes, disabled/hidden visuals,
audio/haptics and a large streak. A prior async delivery/nonce change broke
animations despite synthetic browser checks. Keep event ordering intact.

### Verification performed for this planning change

* Read all visible AnkiWeb reviews and public description; checked public repo.
* Inspected local code, pending diffs, track documentation and installed build.
* Ran the two direct Python record test files above: **11 tests passed**.
* Ran the isolated save probe described in A using a temporary database.
* An initial pytest invocation failed during package collection because the
  hyphenated add-on folder imports relative modules without a package context.
  The direct unittest entry points are the working commands; no product failure
  was inferred from that runner error.
* No live review reproduction, new-feature tests, package build or installation
  was performed. This document specifies future work; it does not certify it.

### Future reinstall command (reference only)

No reinstall is needed for this documentation-only change. If later-approved
work is made in the existing **2.07 source in the original checkout**, close
Anki completely and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\sterl\Documents\GitHub\The-Library\apps\anki-companion-game\speed-streak-addon-v2.07\install_to_anki.ps1"
```

That installer replaces its target and listed earlier Speed Streak installations,
preserving settings/data, for the next Anki restart. Recheck its list and verify
one active copy as part of future implementation. The final implementing agent
must give the command for the actual approved track/path, not blindly reuse 2.07.
Do not run this reference command to install the proposed features: they do not exist yet.

## 8. Decision sheet

All boxes start unselected. A future implementation instruction should name the
approved IDs; a preference expressed during discussion is not blanket approval.

- [ ] A: durable records while streaks continue across decks (recommended).
- [ ] B: optional touch controls (recommended); decide whether to include Boost.
- [ ] C1: optional time-under-budget counter under the specified earning policy.
- [ ] C2: optional snake/rival, after C1 is stable.
- [ ] D: validate existing quiet controls; optionally add scale/reduced motion.
- [ ] E: validate audio fixes already underway and repair a reproduced failure.
- [ ] F: independent automatic shared-bank mode.

Also decide the target track and whether natural deck completion should affect
Pure classification. Until then, the recommended first scope remains A/B, with
existing streak continuation and Pure rules preserved.
