# Source-study settling and automatic same-case recovery — November 3, 2026 (v0.23)

## New workstation evidence

The v0.22 repeat still occurred. The user explicitly confirmed that recovery
requires only closing Compare Report Revisions and choosing Continue: no click
or reselect of the worklist row is needed. Reopening is the effective operation;
recopying an already-open comparison did not solve this report.

## Identified code gap and implementation

Advance sent Down, waited 100 ms, then accepted an enabled main window (and, when
available, changed row index) as sufficient to open the comparison. None of those
checks establish completion of asynchronous report loading. A comparison can
therefore be opened against a previous report snapshot. Direct native/clipboard
reads inside that comparison cannot make the underlying snapshot current.

- Before opening Tools after Down, Automatic/Fast settle 750 ms on the first
  switch and at least 500 ms thereafter. Conservative uses 1000/750 ms; Custom
  retains its explicit case delay. With a native row index, the interval starts
  after selection actually changes, so a queued Down cannot consume the settling
  interval before selecting the new row. Short key timing and copy checks remain.
- One repeated first pair triggers one close/reopen of the same selected study,
  with a cancellable 1000 ms settling interval after close. Keyboard mode creates
  a fresh session carrying forward its validated worklist handle, even when closing
  the comparison returned focus to the report editor. No selection click or Down
  occurs during the refresh; original source labels and saved prefix are retained.
- The suspect capture is never written. A corrected pair is captured and written
  once. A persistent repeat, invalid handle, failed close or cancellation follows
  controlled recovery/stop; the automatic reopen is limited to once for that source
  case per run. Genuine identical linked reports remain available for confirmation.
- Outcomes record same_case_reopen_started/resolved/still_matching with source
  numbers; diagnostics contain no report text or patient identifiers.

## Verification

**159 automated tests passed**, including delayed source loading while row selection
and the main window are ready, one same-study refresh without manual input, exact
labels starting at 1/10/11, saved-prefix preservation on close failure/cancellation,
settling after delayed native selection, and rejection of an invalid retained
worklist before another comparison or Down.
Existing native cross-process, clipboard snapshot, write/readback and export-delivery
checks remain passing.

`dev/check-published-study-switch.py` runs the actual v0.22 portable assembly and
the current assembly against the same synthetic desktop. Its source row changes
immediately, while report loading takes 350 ms and an opened comparison snapshots
the then-loaded report. Results for starting labels 1 and 10:

| Assembly | Manual close/reopen | Comparison opens | Down | Correct pairs |
| --- | ---: | ---: | ---: | ---: |
| Published v0.22 | 1 | 3 | 1 | 2 |
| v0.23 | 0 | 2 | 1 | 2 |

The legacy recovery closes/reopens only; it does not click/select another row.
The fixture reproduces the observed behavior under a plausible delayed-load
model, not PowerScribe's actual private implementation. The independent v0.18
clipboard-race binary replay also passes, starting at labels 1 and 11.

**Limit:** no actual PowerScribe is available here. The load synchronization gap
is demonstrated in the code and replay, but its role in the hospital failure
remains an inference. Settling intervals do not prove report identity/readiness;
the bounded same-case retry implements the user's demonstrated working recovery.

## v0.23 portable delivery

- [PowerScribeReportExporter-v0.23.zip](https://drive.google.com/file/d/1jdxUn2nQc7jJpHJEy977gpvyH9kifIi2/view?usp=drivesdk)
- ZIP: **78,726 bytes**; SHA-256
  `92475d7802b33681dd27e75550ec675c35c9f5b22a94db19338351c9f75aec28`.
- Tested EXE: version **0.23.0.0**; SHA-256
  `11f0eb6203ecf6e13c70d6ae463dcf324f44fac376304b7632d64831d9381487`.
- The archive contains exactly the tested production EXE, README and quick start.
  Embedded EXE and mounted-Drive archive hashes match their local originals.
  Connector readback confirmed the cloud ID, name, size and release-folder parent;
  older published versions were preserved. The paused-dialog preview was inspected
  with the updated once-reopened explanation and enabled recovery choices.

# Live report controls and actionable recovery — November 3, 2026 (v0.22)

## What the screenshot establishes

The v0.21 case-2 warning means the captured pair matched case 1 before saving.
It does not establish that the visible studies were identical. Worklist readiness
could disable Continue while the comparison was still open, preventing an in-place
retry. No further actual workstation logs were supplied with this screenshot.

## Changes and evidence

- Standard focused Edit/RichEdit report controls are read directly with bounded
  system-marshalled WM_GETTEXT requests, bypassing Ctrl+C and the clipboard.
  Complete report text must settle for at least 50 ms on the same child control.
  The child under the report click must receive focus, and Tab must move to a
  different child after a direct attending read. Covered click targets are rejected.
- Unsupported native text/focus providers and long reports retain the checked
  clipboard fallback. When control text becomes available after copying, it must
  agree with the clipboard, allowing only line-ending/terminal-newline differences.
- A repeated first pair offers Retry open reports. This calls ReadReports on the
  existing session/window and discards the unsaved previous capture. It sends no
  extra comparison shortcut or Down. Reselect case and linked confirmation are
  separate actions. No recovery button requires worklist readiness to be detected;
  subsequent navigation still validates focus before Down.
- Source labels, immutable snapshots, verified writes and delivery-prefix checks
  are retained. Diagnostic additions contain control handles/classes/counts only.

**153 automated checks passed.** Eleven additions cover live text versus stale
clipboard content, unsupported and absent native focus, same-pane/focus changes,
delayed click/Tab, case-2 recovery while the main window is disabled, usable
Continue without readiness, native Edit/RichEdit text including Unicode and size
limits, and real cross-process text reads. The fixture is a test-owned offscreen
Windows process: it never reads real reports or uses the user's clipboard.
Existing linked-study, start-at-10/11, one-Down, cancellation, immutable-record,
readback and verified-delivery tests remain passing.

The recovery preview was inspected in the repeated-pair state with worklist
readiness deliberately false: all four choices fit and Retry open reports is enabled.

Microsoft documents [WM_GETTEXT](https://learn.microsoft.com/en-us/windows/win32/winmsg/wm-gettext)
as retrieving an edit control's content, with limits for long RichEdit text.
The implementation declines over-limit reads instead of accepting truncation.

**Limit:** there is no PowerScribe end-to-end execution on this machine. Direct
control reading removes clipboard reuse from supported report controls, but the
specific hospital control class and cause of its stale copies remain unverified.
Do not describe the synthetic/cross-process fixtures as proof of a workstation fix.

## v0.22 portable delivery

- [PowerScribeReportExporter-v0.22.zip](https://drive.google.com/file/d/1Q5FJUiXcHyBNzoXJDjAaCfbG_RP2QbnJ/view?usp=drivesdk)
- ZIP: **77,007 bytes**; SHA-256
  `82f56174ac9b6e47e2cc9da678f71f75b392151b47fbf0aa3fda3bed4e68fe29`.
- Tested EXE: version **0.22.0.0**; SHA-256
  `a8854b4be991bd549662dc72e8efb9c55a1469e31de0415f5d97f9ec6ca4baa5`.
- Archive entries are exactly the production EXE, README and quick start. The
  embedded EXE matches the tested binary. Mounted-Drive ZIP SHA-256 matches the
  local archive; connector listing and metadata confirmed its cloud ID, name,
  size and parent release folder. Earlier versions were preserved.

# Worklist focus and recovery — November 3, 2026 (v0.21)

The case-10 screenshot identifies an initialization failure before any report
copy. The recovery path discarded remembered worklist handles and rediscovered
focus after the popup took focus; inactive focus queries and activation into the
report editor can then reproduce the pause repeatedly.

Microsoft's [GetGUIThreadInfo documentation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getguithreadinfo)
also notes that window handles can be invalid while a window loses activation.
The relevant control is now captured before that transition rather than relying
on its previous focus being discoverable afterward.

The exporter now remembers a validated worklist control while PowerScribe is
active and hands it to each new session, across Go and Continue. A readiness
indicator gates Continue until a valid control is available. This retains the
navigation safeguards and does not infer which study is selected. The requested
source label remains explicit and can start at any valid number.

**142 synthetic/native-control tests passed.** Eight new regressions cover:

- The original failure at case 10 with inactive focus unavailable and activation
  resetting child focus: zero report reads, shortcuts or Down before the failure.
- Observation before Go followed by focus loss and activation reset: cases 10,
  11 and 12 preserve their labels and distinct source reports.
- Retention through inactive focus, editor focus and temporary modals, with
  rejection of menus, foreign roots and invalid native handles.
- Saved case 10 followed by a navigation interruption: one Continue resumes at
  case 11 with three complete entries, no duplicate save and no extra Down.
- Disabled Continue before worklist detection, enabled Continue after selection,
  successful handoff after the popup regains focus, and ignored queued clicks.
- Launcher handle handoff, retained success state and cleared stopped-run state.
- Known non-navigation control classes rejected while native/custom grids remain
  eligible for validation.
- Exact stopped-run instructions: case 10 if unsaved and case 11 if 10 was saved.

The 0.18-versus-current clipboard-race replay remains passing. Dialog preview
inspection and release delivery are recorded below. These tests use synthetic
reports and test-owned controls, not PowerScribe or the real clipboard. The
hospital-workstation trial is still required.

## v0.21 portable delivery

- [PowerScribeReportExporter-v0.21.zip](https://drive.google.com/file/d/1VwoQyJ3izf6mnocLg06M3dwbrhbtRUZ_/view?usp=drivesdk)
- ZIP: **74,044 bytes**; SHA-256
  `0066d1e3d5b24d2941fc4491bd3256ec05105c9936a478e73175eceae2380542`.
- Tested EXE SHA-256:
  `d3f29bee1d719580c2116b68c536a98ebc40efd12518fa44d78d83b173421614`.
- Recovery-dialog preview was inspected: readiness, exact case-11 instructions
  after saved case 10, readable cause text and unclipped Continue/Stop controls.
- Archive contains only the tested EXE, README and quick start. Embedded EXE and
  mounted-Drive copy hashes match. Connector readback confirmed synced name,
  size, ID and release-folder parent; previous versions/sharing were preserved.
- The final native-control integration test was compiled/run without rebuilding
  the packaged production EXE; its hash remained unchanged. All 142 checks pass.

# First-pair investigation — November 2, 2026

The user confirmed the duplicate is already in the saved comparison text, before
website ingestion. This places the failure upstream of website analysis.

## Evidence and limits

- The actual v0.18 and v0.19 release assemblies were each tested across 40
  synthetic three-case exports, at source-label starts 1 and 11. The 240 distinct
  pairs remained distinct through archive, comparison file, injected clipboard
  delivery, copied-text viewer and website parser. This did not reproduce an
  unconditional duplicate append, and does not establish what PowerScribe
  returned on the hospital workstation.
- A separate controlled replay **does reproduce** a first-pair duplicate in the
  published v0.18 binary. The fake desktop advances correctly twice and issues
  exactly six Ctrl+C commands for three studies. During each second-study read,
  the earlier string is returned while the clipboard sequence advances to newer
  data. The old acceptance check associates that earlier string with the newer
  update number. Saved case 2 repeats case 1; the same occurs at starts 11/12.
- In the v0.20 binary, the exact same fixture saves the correct second pair.
  Both replays keep two row advances and six copy commands; no comparison
  reopen is needed. This demonstrates a real read/check race, not proof that it
  is the cause of the user's workstation failure.

Run the binary comparison on Windows after building:

```powershell
python apps/powerscribe-report-exporter/dev/check-published-first-pair-race.py
```

The script needs the preserved v0.18 ZIP in `dist` and the current built EXE.
It runs real assemblies against synthetic desktop/clipboard implementations;
it does not operate PowerScribe or the real clipboard. Harnesses and exports are
kept in a unique temporary directory and are not included in the release.

## v0.20 verification

**134 synthetic/native-control tests passed.** Relevant new checks cover:

- A mid-read clipboard replacement at starts 1 and 11: correct source/report
  association without extra Ctrl+C, comparison opens, navigation or confirmation.
- Permanently changing clipboard snapshots: no save or Down, with an explicit
  unstable-read diagnosis. Existing delayed-rendering and clipboard-lock checks
  remain valid. The optional accessibility copy path also samples sequence and
  owner on both sides of the read; no actual PowerScribe provider was tested.
- Snapshot object reuse and mutation, immutable source-number/formatted-record
  binding, and exact capture/save token joins for both output files.
- Deliberate same-length first-record substitution during writing: byte readback
  rejects it and retains the previously verified prefix. Duplicate source saves
  and wrong source-pair serialization are rejected before appending.
- Delivery excludes an unverified tail and rejects a truncated verified prefix.
- Repeated pairs already present at capture are distinguishable from save errors
  in the new capture-checks ledger. No report text/headers appear in that ledger;
  its equality key is random per run and never persisted.
- Existing interrupted-run recovery, cancellation, linked-study preservation,
  pending/unavailable handling and launcher checks still pass. The speculative
  automatic first-pair comparison reopen from v0.19 has been removed.

Workstation follow-up: export three known distinct studies and inspect the saved
comparison text. If it still repeats, retain `.capture-checks.csv` and the normal
progress log; the capture versus verified-save stages can then be compared
without submitting report text. The original hospital failure is not marked
resolved until that trial confirms it.

## Portable delivery

- [PowerScribeReportExporter-v0.20.zip](https://drive.google.com/file/d/18-aYcd1Kygx2Ldc1G5j1S8Y9Z2zfjq-A/view?usp=drivesdk)
- ZIP: **71,910 bytes**; SHA-256
  `69a7ff2ae9ea44ccc31d8e37b3034ddc7bea53c3bf0d3cf388689067318ef488`.
- Tested EXE SHA-256:
  `15a01953a95ef8a1fc725f6af7d9b76bd196a94b84a2332cda8c63c936e28548`.
- Archive allowlist: tested EXE, README.md and QUICK_START.txt. No captures,
  diagnostics, source reports, tests, settings or credentials are included.
- Embedded EXE hash and mounted-Drive copy hash match. Connector readback
  confirmed synced file name/size/ID and the existing release-folder parent.
  Prior versions and sharing were preserved. This update changes only the
  extractor; it does not deploy the earlier website changes.
