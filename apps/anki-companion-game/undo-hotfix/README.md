# Time Drain undo patch

Speed Streak's **Review Time Drains Last** setting temporarily buries flagged
cards while ordinary cards remain. Previously, each hidden card created a
separate Anki undo entry. Undo restored a hidden card, the queue wrapper immediately
buried it again, and that new write discarded redo. The reviewer could appear
stuck on the same card indefinitely. Consecutive Time Drains amplified the issue.

The patch groups automatic bury/unbury operations with the preceding action and
leaves the queue alone while Anki has redo history. Repeated undo and redo can
therefore walk the existing history. The next deliberate collection write, such
as answering a card, clears redo and resumes ordinary automatic sorting.
Automatic restoration skips cards already restored by undo, manually buried
cards, and suspended cards. Non-answer undos no longer consume Speed Streak's
review snapshots or Sprint Time's undo handling. No Undo mode retains its guard.

## Which version is which?

At investigation time on November 3, 2026:

| Copy | Identity | Status |
| --- | --- | --- |
| Sterling's installed add-on | `addons21/speed_streak_v2_07`, build `2.07-sprint-time.6` | Personal experimental visuals and Sprint Time |
| Local personal source | `speed-streak-addon-v2.07/` | Experimental; patched locally, not introduced into this commit |
| Local standard development source | `speed-streak-addon-v2.05/`, `2.05-user-requests.14+diagnostics.1` | Contains other unfinished local changes; patched locally, not published wholesale |
| Committed standard source before this fix | `2.05-macos-browser-audio.2+diagnostics.1` | This commit adds only the undo patch and build suffix |
| Archived AnkiWeb download | `2.05-user-requests.12`, fetched September 30, 2026 | Public-release baseline for the separate distributable below |

The archived download is a known public baseline, not a claim about what is
currently served by AnkiWeb. Nothing in this change uploads an AnkiWeb update.
All patched builds append `+time-drain-undo.1` to their own existing build ID.

## Apply to Sterling's installed version

Close Anki, run this PowerShell command, then restart Anki:

```powershell
& 'C:\Users\sterl\Documents\GitHub\The-Library\apps\anki-companion-game\undo-hotfix\install_patch.ps1'
```

This replaces only `reviewer_overlay.py`, `build_info.py`, and the new
`time_drain_undo.py` in the installed `speed_streak_v2_07` folder. It patches the
installed code, preserving that exact version's visuals, settings and history.
Original code is backed up outside the add-on under
`Anki2/addons-data/speed_streak/code-backups/`. It refuses to apply while Anki is
open and validates the patched source in a staging directory before copying.
`-CheckOnly` prepares and validates a preview without replacing installed files.
`-AddonFolderName` selects another installed Speed Streak folder explicitly.

The usual full-track installer also includes the fix in the patched local source,
but it installs all that track's local changes. Use the focused command above
to keep exactly the installed visual build.

## Separate standard package

[`speed_streak_2_05_time_drain_undo_1.ankiaddon`](releases/speed_streak_2_05_time_drain_undo_1.ankiaddon)
starts from the archived public `2.05-user-requests.12` download. Only the reviewer
integration, build ID and new undo helper differ; all other 439 file entries are
byte-identical to the archive. The adjacent provenance JSON records both SHA256
hashes and the changed entries. This is a standard-visuals package for public
patch preparation; it is not Sterling's experimental 2.07 installation.

Reproduce it from the repository root:

```powershell
python -B apps/anki-companion-game/tools/fix_time_drain_undo.py --package apps/anki-companion-game/diagnostics/baselines/speed_streak_2_05_user_requests_12.ankiaddon --output apps/anki-companion-game/undo-hotfix/releases/speed_streak_2_05_time_drain_undo_1.ankiaddon
python -B apps/anki-companion-game/undo-hotfix/verify_package.py
```

For source tracks, use the same tool with `--directory <track-folder>`.
`undo-hotfix/time_drain_undo.py` is the canonical helper copied into each track.
Applying the tool repeatedly does not duplicate the integration or build suffix.

## Validation

Nine regressions run against real Anki **25.09.4** scheduling and undo operations
in disposable collections, using the actual reviewer queue methods without Qt
rendering. They pass against the public `.12` hotfix, committed standard source,
local standard `.14` source, local experimental 2.07 source, and a patch preview
of Sterling's exact installed `.6` source. They cover consecutive hides, repeated
undo/redo, initial review entry, return-to-Decks restoration, resumed sorting after
an answer, unrelated undos, all-Time-Drain queues, disabled sorting and bury errors.
The consecutive-hide regression fails against the original committed source.

```powershell
& "$env:LOCALAPPDATA\AnkiProgramFiles\.venv\Scripts\python.exe" -B apps/anki-companion-game/undo-hotfix/test_time_drain_undo.py -v
& "$env:LOCALAPPDATA\AnkiProgramFiles\.venv\Scripts\python.exe" -B apps/anki-companion-game/undo-hotfix/test_time_drain_undo.py --track apps/anki-companion-game/speed-streak-addon-v2.07 -v
```

The broader committed-standard suite ran 101 tests: 99 passed, one installer test
skipped because Anki was open, and the existing package/source visual-asset byte
comparison failed on line endings. Its compared visual files are unchanged by
this patch. An initial run with Anki's Python also lacked Pillow; the broader
suite was rerun with the system Python, which has Pillow. The focused archive
verification passes for all 442 hotfix entries.

The installed add-on was not replaced while Anki was running. A live reviewer
check remains: answer a normal card before several flagged Time Drains, undo
repeatedly, redo, then answer again. Confirm that undo returns to earlier reviews
without leaving the reviewer, and that Time Drains still return at the end.
