# PowerScribe Report Exporter v0.13

## v0.13: first case, last case, Go

The launcher opens with just **First case**, **Last case**, **Go**, and a collapsed **Options** section. Select the starting worklist row in PowerScribe before Go; the entered numbers label consecutive exports and determine the count, rather than selecting numbered rows. A progress overlay and Stop remain available during the run.

**Automatic - fast first** is the default, including on upgrade. Each run begins with 10 ms input settling, 100 ms after Down, and 5 ms readiness polling. If an existing bounded copy retry is needed, input settling increases to 25 ms, then at most 100 ms for the remainder of that run. It starts fast again next time. This adjusts input settling after delayed copies; it does not guarantee recovery from every missed shortcut or change PowerScribe's loading speed. Readiness waits return as soon as their checks succeed. The normal 10-second maximum, clipboard ownership/freshness, heading validation, focus guards, and single-Down navigation checks remain in place. Options retains fixed Fast, fixed Conservative, Custom timing, report-click setup, worklist capture, and accessibility fallback.

Each run automatically gets a unique filename in **Documents\\Report comparisons**, or the folder selected in Options. No Save dialog is required. After a successful run with complete pairs, the text is copied and the website opens unless disabled in Options. Notepad is now opt-in; **Open comparison file** remains available after every run with complete pairs. Existing report-click coordinates, captured selectors, and export choices are retained. Legacy numeric timing values are loaded on upgrade; running Automatic replaces them with its defaults. Choose Custom timing before Go to use or edit those values instead.

Stopped runs keep saved captures and show a brief result with an actionable next step. **Details** and `<output>.run-summary.txt` include counts, source numbers, last attempted/saved entry, error, recovery guidance, and file locations. **Prepare remaining cases** sets the suggested starting number here; it never selects a PowerScribe row or resumes automatically. Close the comparison and select the corresponding row yourself before Go. A resumed run uses a new file. A saved entry followed by a close/navigation failure is preserved and is excluded from the suggested remaining range; check the saved result and current worklist position before continuing.

Validation: executable compiled and **111 tests passed**, including the existing 103 capture/navigation checks plus adaptive timing, migration, unique filenames, stopped-run recovery, and a native launcher layout check. Launcher previews were inspected with Options collapsed and expanded. Tests use synthetic reports and test-owned controls; they do not operate on PowerScribe or the real clipboard. The UAB workstation still needs a short trial to verify the actual range, report contents, and case order.

The following release notes describe earlier changes; the current use instructions below reflect v0.13.

## v0.12: retain worklist focus before activation

The v0.11 startup check ran only after activating PowerScribe. If activation reset child focus to the report editor, it discarded the worklist the user had selected and stopped before the first comparison. v0.12 remembers the retained child focus **before activation**, then restores and verifies that control before the first Tools shortcut. It still tries the post-activation check when no usable retained child was available.

For a workstation that still reports unusable worklist focus:

1. Close any open comparison and click **Remember worklist (F8)** in the exporter.
2. Click the first case row in PowerScribe and press **F8 while PowerScribe is active**.
3. Confirm the exporter status says **Worklist remembered**, then return to it and export a short range.

This is a native keyboard-focus capture, not UI Automation, a screenshot, or a report click coordinate. It remembers only a control handle for the current exporter session. It does not click that first row again between cases. The handle is never saved in the settings or log. A restarted PowerScribe, destroyed/hidden/disabled control, wrong parent or process, or recognized text editor invalidates capture instead of silently falling back. Use **Clear remembered worklist** to resume automatic detection. Arming a new capture clears the old one.

Focus diagnostics now distinguish a failed Windows query, no focus, main-window-only focus, focus outside the reporting window, a recognized editor, and an invalid/hidden/disabled child. Logs include native control class names but no control captions, report text, patient identifiers, handles, or row indices. Editor classification recognizes native/WinForms Edit and RichEdit controls, TextBox/Editor names, and Scintilla; incidental `edit` substrings such as `CreditGrid` no longer cause rejection. A class name is still only a heuristic, not proof that a custom control is a worklist.

If F8 reports only main-window focus or no usable child even with the row selected, this build still stops. That observation is needed before choosing a custom-grid navigation strategy; v0.12 does not bypass the focus guard or promise to support every PowerScribe control. Initial and subsequent focus restoration must succeed before keyboard navigation.

Validation: application compiled and **103 tests passed**, including activation resetting focus into the editor, post-activation fallback, initial restore failure without Tools/copy/Down, native test-owned list/editor controls, rejected stale/hidden/disabled/wrong-root F8 handles, and existing clipboard, menu, pending-report and row-navigation safeguards. No test operates on PowerScribe or the real clipboard. The UAB workstation's exact rejection cause and end-to-end behavior remain unverified; test a short range and verify case order locally.

## v0.11: whole reports by default and clipboard handoff

Completed pairs now retain the entire captured resident and attending reports, including indication, technique, and comparison. **Findings and below only (previous export format)** is an optional checkbox, off by default. The choice is saved; older profiles migrate to whole-report export without changing click positions or timing. Both modes retain the existing clinical-heading validation and clipboard freshness, ownership, navigation, and pending-capture safeguards. This retains all text supplied by the report pane; it cannot retrieve metadata that PowerScribe does not expose there.

After a successful run with complete pairs, the exporter automatically copies the exact `.for-comparison.txt` content to the Windows clipboard **before** opening the website. It copies only complete pairs; pending records and unavailable placeholders remain excluded. On the updated website, select **Paste**, then **Analyze reports**. If browser clipboard permission is blocked, click the report box and press **Ctrl+V**. If Windows clipboard copy fails, the exporter says so and the saved comparison file remains available in Notepad. A run with zero complete pairs, or a stopped/failed run, does not replace the clipboard with incomplete input or automatically open the website.

Use the updated Compare Revisions `main.py` with this release: full reports supply AI context, while feedback and the clinical diff remain scoped to Findings and Impression/Conclusion. The website now keeps each numbered source case separate. Matching report templates do **not** prove linked-study identity, even when the whole report matches; actual linked studies will also remain separate until reliable identity is available.

Validation: executable compiled and **97 automated tests passed**, covering full/legacy export, old-profile migration and saved choice, labels, whole context, alternate headings, completed-only clipboard payload and clipboard failure, plus existing capture/navigation safeguards. Tests use an injected clipboard writer and synthetic text; no patient data, real clipboard or live PowerScribe session is exercised. A short UAB workstation trial is still required to verify actual report-pane capture and browser paste permissions.

## v0.10: empty attending capture and source-case outcomes

When bounded attending-copy checks observe a fresh, readable empty update owned by PowerScribe, the exporter now checks the resident report. If the resident text validates, it archives that source case as **possibly awaiting attending — capture unconfirmed**, closes the comparison, and continues through the existing navigation safeguards. This does not prove an unsigned report. No-update, unknown/foreign-owner, unreadable, wrong-focus, and invalid-resident failures still stop rather than silently skipping.

Incomplete cases are excluded from `.for-comparison.txt`; their original case numbers and resident text are retained in the original output. A new `.outcomes.csv` records case-number events such as complete, pending_suspected, comparison_unavailable, cancellation, and the stage where a run stopped, without report text. The completion message lists possible pending and unavailable case numbers. An event ledger can contain both a saved outcome and a subsequent navigation failure for the same case; do not count each event as another case.

The existing copy timeout remains **10 seconds by default**, with bounded retries. This first reliability change deliberately waits for delayed text to appear before accepting an empty-copy outcome. A smaller delay needs observation of real UAB clipboard behavior. Full-report default capture and website section handling remain a coordinated follow-up; complete-pair output keeps the existing Findings-and-below format for now.

**Validation:** application builds and all **91 automated tests pass**, including transient empty rendering, pending cases between complete cases, first/final/consecutive pending cases, clipboard ownership/freshness, invalid resident text, cancellation, close failure, and frozen-row safeguards. The tests do not operate on PowerScribe or the system clipboard. Actual UAB behavior remains unverified.

**Small workstation trial:** select a short known run containing a finalized case, an unfinished attending case, and another finalized case. Check original source numbers in both output files and confirm the middle case is excluded from `.for-comparison.txt`. If the empty field produces no fresh clipboard update or no reported owner, the tool will still stop; the non-report progress log will identify that observation. Do not lower safeguards simply to force it to skip.

## Historical development notes: empty-attending capture handling (October 3, 2026)

This local change has not been published or tested on the UAB workstation. It keeps the existing limited Findings/Impression/Conclusion export for complete pairs. Full-report mode requires coordinated website section handling and is a separate change.

Previously, an empty attending copy stopped the run before the resident pane was inspected. Keyboard mode now checks the resident after the existing bounded copy wait **only** when the final clipboard observation is fresh, readable, empty, and owned by PowerScribe, with no nonempty text or foreign-owner update observed during that attempt. A valid resident report then permits an explicitly **possibly awaiting attending (capture unconfirmed)** archival record. This does not prove the field is empty, that the attending has not signed, or that capture succeeded. Unknown clipboard ownership, no fresh update, unreadable text, unsupported headings, an invalid resident, and focus failures still stop the run.

- Source case labels remain unchanged, including first, final, and consecutive possible-pending rows. Menu recovery, close verification, worklist focus, and supported native row-index checks still apply. Identical linked-study reports remain valid.
- The original export retains the resident's full captured text under a conspicuous incomplete-record marker. `.for-comparison.txt` contains **complete pairs only**. Notepad always opens that comparison file, even when empty; the website is not opened automatically if there are no complete pairs.
- The completion/stopping message lists possibly pending and unavailable source numbers separately.
- New `.outcomes.csv` is an append-only source-number event ledger. Each attempted row gets `started`; saved outcomes are `complete`, `pending_suspected`, or `comparison_unavailable`. A subsequent error/cancellation appends `stopped_<stage>` or `cancelled_<stage>` without erasing a previously saved outcome. Stages distinguish selection, opening, capture, saving/closing, and navigation. It contains no report text. Rows never attempted have no entry; the configured range and last started row identify where to resume.
- This first pass preserves the configured **Timeout** (default **10,000 ms**) and up to three copy attempts before considering an empty attending candidate. It does not implement a one-try shortcut, which could skip delayed report rendering. This may still pause for ten seconds on each candidate; capture timing helps evaluate a later optimization.
- The optional UI Automation mode is unchanged. This fallback is for the default keyboard workflow.

Local validation: application builds and 91 automated tests pass, including transient empty rendering, empty attending between complete cases, consecutive pending cases, ambiguous/foreign ownership, locked/no-update clipboard, invalid resident, cancellation, failed close, and unchanged-row navigation. These tests use synthetic reports and do not operate on PowerScribe or the system clipboard.

Before release acceptance, run a short UAB range containing a complete case, a known unsigned/empty-attending case, and another complete case. Confirm the actual empty-field copy reports a fresh sequence and PowerScribe owner; the current reported error does not establish those details. Verify the original source labels, pending summary, resident archival content, absence of the incomplete case from comparison input, and the next report's identity. If the blank field emits no update or no owner, capture only the text-free diagnostic log and stop; do not weaken freshness/ownership checks merely to force continuation. Custom worklists still cannot prove row identity or loading completeness.

A native C# Windows executable that follows the working **Review Reports 11.09.24.ahk** sequence. It has no AutoHotkey dependency. **Keyboard workflow is now the default and does not require accessibility captures.**

The first version's accessibility approach did not work on Sterling's workstation: PowerScribe exposed neither the needed case-list selection pattern nor the report-pane patterns. The keyboard workflow replaces that requirement with the original clicks and keys, while keeping readiness checks that do not depend on UI Automation.

**v0.4 fixes:** v0.3 incorrectly rejected valid reports with a Conclusion heading and no Findings heading. v0.4 accepts Findings, Impression, or Conclusion sections. It also requests clipboard text before checking the sequence number so delayed rendering can finish, tries plain text if Unicode text is unavailable, and retries a missed Ctrl+C at most twice while retaining the same selected pane. Failures now distinguish missing updates, unreadable clipboard text, unrecognized headings, and another-process ownership. Clipboard diagnostics contain counts and checks, not report text.

**v0.5 changes:** keyboard mode automatically restores PowerScribe focus when another window takes it during opening, copying, closing, or case navigation. Recovery confirms the intended window is foreground before sending more input. Focus recovery is bounded; it does not dismiss unknown clinical dialogs. Opening uses one Alt+T chord, then I, eliminating an input pause. If focus recovery interrupted the Tools menu, it reopens that menu before sending I. Saving the already captured complete report pair now overlaps comparison closing; the next case still waits for both to succeed. Progress-log disk writes run on a separate worker. New speed presets and expanded CSV timings make tuning easier. Export/Stop buttons stay visible at the bottom.

**v0.6 changes:** addresses the reported pause while a report is already visible/highlighted. Keyboard mode reads/clears text through native Windows clipboard calls, removing the Windows Forms clipboard layer's built-in retry sleeps. Busy access returns to the existing readiness loop after one attempt. A missed Ctrl+C is eligible for retry at 100/400 ms instead of 250/750 ms, without the extra blind 100 ms settling pause. Valid fresh report text is still accepted immediately, including delayed rendering triggered by requesting the text. Fast uses 10 ms input pauses and 5 ms polling; After Down stays 100 ms. New CSV fields identify clipboard-read/clear time and failed access counts. The progress timer displays tenths of a second.

**v0.7 changes retained:** remembers the initially focused worklist child control and restores/verifies that focus before sending Down. Comparison opening has a separate configurable maximum (default three seconds), with numbered unavailable placeholders. Findings/Conclusion, Findings & Conclusion, Findings and Conclusion, dashed combinations, plurals, reversed combinations, and Findings/Impression/Conclusion are accepted.

**v0.8 corrections retained:** removes v0.7's report-text duplicate guard. Linked studies can legitimately have exactly the same attending and resident report text; all such pairs are exported under their own requested labels. Where the remembered control is a standard native ListView or ListBox, read-only row-index messages verify that Down changed the row. Custom grids are not queried with guessed messages and do not acquire a report-text heuristic.

**v0.9 menu recovery:** v0.8 relied on native menu flags and could miss a managed/custom dropdown left visible after a disabled comparison command. The exporter now also observes visible captionless popup windows on PowerScribe's UI thread. After a failed comparison it always sends two guarded Escapes to unwind the dropdown and menu bar, requires menu/popup absence to remain stable for 50 ms, then restores worklist focus and sends Down once. Alt is a bounded fallback only if a menu remains; it is no longer sent unconditionally, which could reopen a closed menu. Before I, the Tools dropdown itself must appear; menu-bar activation alone is insufficient. A failed Tools shortcut stops on that row without producing a misleading unavailable placeholder.

**Earlier v0.9 validation:** application builds; 80 automated tests passed. Tests reproduce a custom dropdown with no native menu flags, a missing first case followed by correctly labeled second/third reports, a delayed dropdown after menu-bar activation, refused/delayed recovery and a missed Tools shortcut. A real test-owned offscreen Windows Forms dropdown is detected despite absent native menu flags and disappears from detection after closing. Existing clipboard, focus, headings, linked-study and native row-index tests also pass. No input is sent to PowerScribe or the system clipboard. A small UAB trial is still needed to confirm the site's menu/control behavior.

## Use it — no PowerShell required

1. Close the earlier exporter and Review Reports AHK. Extract the portable ZIP and double-click `PowerScribeReportExporter.exe` on the PowerScribe workstation. The title should say **v0.13**.
2. Close any open Compare Report Revisions dialog and **click the first case row in PowerScribe's worklist**. Leave focus on that row. Keep the comparison-window size that works with the AHK.
3. Enter **First case** and **Last case**, then **Go**. These labels determine the count; they do not select numbered rows. Start with one case, then a small batch. Options is unnecessary for a normally configured workstation.
4. A small progress window shows the current action, elapsed time, saved count, and available stop shortcut (**Numpad \*** or **Ctrl+Shift+F12**). Use its Stop button to cancel.
5. On success, complete pairs are copied and the [Compare Revisions website](https://compare-revisions-646439009049.us-central1.run.app/) opens if enabled. Select **Paste**, or Ctrl+V in the report box, then **Analyze reports**. The extractor does not paste or upload reports itself.
6. **Open comparison file**, **Open save folder**, and **Details** are available after the run. Options lets you choose another save folder, enable Notepad, or adjust setup. Only `<output>.for-comparison.txt` contains comparison input; the original `<output>` retains incomplete entries too. Zero complete pairs leaves the clipboard unchanged and does not open the website. Stopped/failed runs retain completed pairs but do not automatically copy them or open the website.

If automatic worklist detection fails, use **Options > Remember worklist (F8)**, select the first case row, and press F8 while PowerScribe is active. Return to the exporter and try Go. This focus capture lasts for the exporter session, rather than being saved permanently.

### Report click position

The default report-body click is **X=800, Y=600 relative to the comparison window's top-left corner**, matching the November AHK. It is the report text area, not the attending/resident name label.

If the window layout has changed, expand **Options** and use **Capture report click (optional)**: open the comparison manually, click this button, point inside the **attending report body**, and press F8. This records a mouse position only. It does not take a screenshot, perform OCR, or require a selectable accessibility control. Then close the comparison and start the export. No case-list, resident, or OK-button capture is required in keyboard mode.

If the click lies outside the window or copying fails, the app stops with an explanation. Repositioning the window on another monitor does not change the window-relative coordinate, but resizing it, changing display scaling, or changing the pane layout may require updating that position.

## What it does

The default mode mirrors the known working sequence:

1. Activate the reporting window, exit any leftover menu, send **Alt+T**, wait for the Tools dropdown, then send **I**.
2. Wait for **Compare Report Revisions** to become visible, enabled, and active.
3. Click the attending report body; select all and copy with **Ctrl+A / Ctrl+C**.
4. Request clipboard text to trigger any delayed rendering, then require a fresh update containing a Findings, Impression, or Conclusion section heading.
5. Send **Tab**, select all and copy the resident report, and wait for its fresh clipboard update.
6. Start saving the complete pair directly to the selected text file on a separate worker.
7. While saving runs, send **four Tabs and Enter** from the resident report and wait for the comparison to close. Wait for saving to finish successfully too.
8. Count that saved case, verify menu mode is inactive, restore the original worklist control's focus, send **Down once** if another case is requested, and allow the transition to settle before the next iteration. If focus/menu checks fail, stop without Down. A supported native list control must report a different selected row index before the next comparison attempt; a custom grid retains the configured settling pause.

By default it retains whole captured reports. If **Findings and below only** is enabled in Options, it trims both reports to Findings, or to the first Impression/Conclusion section when Findings is absent. It keeps the `Case N`, `Attending Report:`, `Resident Report:` format. Matching is case-insensitive and recognizes section headings at the start of a line, with a colon or on their own line, including combined Findings/Conclusion and Findings/Impression headings, `/`, `&`, `and`, dash separators, reversed combinations and plural Conclusions. Incidental mentions of findings in a history/header do not count as a section. It does not separately extract attending or resident names from the interface labels. If PowerScribe itself cannot copy a report body through this sequence, this app cannot recover it through pixel reading.

### Unavailable comparisons and linked studies

**Missing comparison wait (s)** defaults to three seconds and is independent of the normal readiness Timeout. A comparison that appears and becomes ready returns immediately. If the wait expires, no comparison exists, and the main window is enabled, the exporter saves this marker under both report labels, counts a placeholder separately from complete pairs, and advances:

```text
Case 2
Attending Report:
[REPORT UNAVAILABLE: Compare Report Revisions did not open within the configured wait. Revisions may be unavailable for this case. This is a placeholder, not report text.]

Resident Report:
[REPORT UNAVAILABLE: Compare Report Revisions did not open within the configured wait. Revisions may be unavailable for this case. This is a placeholder, not report text.]
```

Unavailable is an inference: a missed shortcut or an unusually slow open can produce the same observation. Increase this wait or choose Conservative timing if known available cases are skipped. Unknown modal dialogs, existing-but-unready comparisons, focus failures and copy failures still stop, so recovery cannot send navigation into the wrong dialog. Placeholder rows appear as `comparison-unavailable` in timings. The next genuine pair retains the next requested label.

**Identical report text is always allowed**, including identical headers and both identical report bodies on linked studies. v0.7's text-duplicate check was incorrect and has been removed. Case navigation is assessed through window/menu/focus state and, only for recognized standard native list controls, the selected row index. This does not establish accession identity or report-loading completeness on a custom grid.

After a missing comparison, two Escapes unwind the dropdown and menu bar even if native menu flags say inactive. Each Escape has at least 20 ms input settling; the app then polls for menu and popup absence to stay clear for 50 ms, within at most 500 ms (or the shorter normal Timeout). If needed, one guarded Alt and another bounded exit check follow. A popup that cannot disappear stops the run before committing that skip or pressing Down. Existing floating popup windows are recorded at run start and excluded; tooltips and menu shadows are excluded. An unknown new captionless popup on the same UI thread conservatively blocks navigation. These are native window checks, with no screenshot, OCR or accessibility-pattern captures.

Once cleanup succeeds, the skip placeholder is committed, worklist focus is restored and Down is sent once for every nonfinal entry. Cleanup is also checked before the next Tools attempt. Normal successful cases do not receive the two-Escape/50-ms recovery waits. Tools opening is observed for at most one second (or the shorter normal Timeout), separately from the comparison-opening maximum; failure to observe its dropdown stops on the current row. Native popup enumeration follows [Microsoft's EnumThreadWindows API](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumthreadwindows); Windows Forms dropdown popup styles are documented in [Microsoft's ToolStripDropDown source](https://github.com/dotnet/winforms/blob/main/src/System.Windows.Forms/System/Windows/Forms/Controls/ToolStrips/ToolStripDropDown.cs).

### Speed settings

- **Poll:** 5 ms with Automatic/Fast, 10 ms with Conservative. Readiness is checked immediately; polling occurs only while waiting for a window or clipboard update. Windows scheduling can make the actual interval longer. Lowering 10 ms polling saves only a few milliseconds of poll delay in a normal transition, not a whole second.
- **Input pause:** **Automatic - fast first** starts at 10 ms and increases to 25 ms, then 100 ms if a bounded copy retry is needed. The increased delay applies to later input settling in the same run and resets next run. **Fast (fixed)** stays at 10 ms; **Conservative (fixed)** uses 100 ms. **Custom timing** exposes the numeric input, case-transition, and poll values. These pauses affect Tools, click/Tab settling, Ctrl+A before Ctrl+C, and closing Tabs before Enter. Zero can send actions before the control is ready.
- **After Down:** 100 ms by default, matching the old script's case-transition pause. Standard native list controls receive an additional immediate row-index check; custom grids have no supported row-index check. Neither establishes that the new report contents have finished loading.
- **Timeout:** 10 seconds by default. This is a maximum readiness wait, not a fixed delay added to each action.
- **Missing comparison wait:** three seconds by default, used for opening in keyboard mode; missing comparisons produce marked placeholders and continue only after the window-state checks above.

Fast uses six 10 ms input pauses plus the 100 ms case-transition pause for a typical non-final case: about 160 ms of programmed waits, compared with v0.5's 250 ms. This reduces deliberate waits, not PowerScribe's actual loading time. Retries and Windows scheduling add time. Native clipboard calls remove nested Windows Forms retry sleeps, but a Windows data request can still block while PowerScribe renders clipboard text; a visible/highlighted report does not guarantee that clipboard text is ready.

Window-opening and clipboard waits continue immediately when their observed condition is satisfied. Lowering Timeout does not speed a successful operation. Report copies cannot run concurrently because they use the same focus and clipboard; navigation cannot begin until both texts are captured. Saving already overlaps closing using immutable captured strings. Log writes already run in the background. An internal report API remains the route that could remove the GUI operations altogether.

For the next speed investigation, use the CSV to distinguish PowerScribe opening time from clipboard capture, disk saving, close time, and case transition. Do not assume a smaller After Down value is safe: this workstation does not expose dependable selected-row/loading state. Verify the resulting pairs locally before reducing it.

## Progress, output, and limits

- Setup errors appear before any capture starts. Stopped runs show a brief result and next step; **Details** and `<output>.run-summary.txt` contain counts, the error, recovery guidance, and output locations. During export, the progress overlay shows the current step and how long it has been there.
- `<output>.progress.log` records timestamped steps and error messages, not report bodies or patient names. A background writer keeps its disk flushes off the keyboard worker. The log is drained on exit; progress can appear in the UI before its line reaches disk. If the run appears stuck, the recent log lines identify the current operation.
- Clipboard observations in that log record whether the sequence changed, whether text was readable, the character count, the owner category, and whether a supported heading was found. They do not record clipboard text. The final error identifies the observed copy failure, rather than treating every rejection as a failed Ctrl+C.
- `<output>.timings.csv` records `case,open_ms,capture_ms,save_close_ms,next_ms,read_method,attending_copy_ms,resident_copy_ms,save_ms,close_ms,total_ms,focus_recoveries,copy_retries`. `save_close_ms` is wall time for overlapping saving/closing, so it is not the sum of `save_ms` and `close_ms`. Copy sub-times include selection/copy waits; `capture_ms` also includes click/Tab settling and validation. No report text or author/patient identifiers appear in the CSV. An iteration that fails after saving a pair may not have a timing row.
- Existing exports and logs are never replaced. Saving overlaps closing, and each complete pair must finish flushing to disk before counting it or advancing. If close fails but save succeeds, the pair is counted/preserved and the exporter stops. If save fails, the case is not counted and no Down is sent. The saving task is always joined before streams are disposed.
- v0.6 appends CSV fields `clipboard_read_ms` (sum of data-read calls), `clipboard_read_max_ms` (longest individual read), `clipboard_clear_ms` (clear readiness wait, including contention/focus recovery), and `clipboard_lock_misses` (failed clear/read attempts, including non-lock access failures). These are zero in direct UIA mode. Reads taking at least 100 ms also produce a duration-only progress line. These fields help distinguish an actual blocked read from waiting between checks. They contain no report text.
- The clipboard is cleared before each pane's copy, and a new sequence number is required. Text is requested before checking that sequence: Windows can defer a sequence update until delayed data is rendered. If a clipboard owner is reported, it must belong to the PowerScribe process. A missing owner HWND is allowed because some apps publish text that way. A changed clipboard owned by another process is still rejected.
- If no usable new text arrives, keyboard mode retries Ctrl+C on the already selected report up to twice within the same timeout, eligible at 100 ms and 400 ms after the initial request. Readiness is checked first on every poll, so a valid fresh copy returns before retrying. Automatic adds 25 ms, then 100 ms input settling immediately before those retries; fixed/custom modes retain their selected input settling. A known other-process update or fresh text lacking all recognized headings is not retried. No retry closes the dialog, clicks another pane, or advances the case.
- Keyboard mode automatically recovers focus by default and confirms PowerScribe is foreground before sending more input. A temporary refused activation is retried about every 100 ms. Guarded input allows up to three seconds of recovery (or the shorter configured timeout); close readiness uses the normal Timeout and opening uses Missing comparison wait. Missing all supported headings, a clipboard timeout, a blocked recovery, or an unclosed comparison stops the run at the current case. Missing comparisons are explicitly marked and skipped only after confirming safe window state. Uncheck automatic recovery to restore strict stop-on-focus-loss behavior. No Down is sent after the final requested case.
- **Keyboard mode does not infer case identity from report text.** It verifies Windows menu state and restores the remembered focused control. Standard native ListView/ListBox controls additionally receive bounded read-only selected-row queries; a row that fails to change stops before another comparison attempt, without retrying Down. Unsupported custom grids log that row-index verification is unavailable and retain keyboard navigation. Neither path proves accession identity/loading completeness or detects every manual selection change. Use a fixed ordering and avoid interacting with PowerScribe during a small multi-case trial. Handles and row indices are not saved to a profile or log.
- The clipboard is replaced as in the original AHK. No report content is transferred to a network service by the extractor.

## Optional accessibility mode

Unchecking **Keyboard workflow** reveals the original advanced mode. It requires capturing the case list, attending pane, resident pane, and OK button through UI Automation. Direct reads are attempted unless **Use clipboard instead of direct text reads** is checked. This mode can verify selected-row changes when the provider supports selection.

**It is not suitable for the workstation that reported unsupported controls.** The default keyboard mode is the intended route there. Direct mode's 50 ms settling check only observes stable text; it does not prove background loading or accession identity. A stuck provider call may outlast the readiness timeout. Stop, then close again to exit immediately if necessary.

Settings live in `%LOCALAPPDATA%\PowerScribeReportExporter\controls.json`. Old profiles retain saved click coordinates and captures, migrate to keyboard mode where required, and use Automatic timing by default. The profile contains positions, control selectors, and settings, not report bodies. Keyboard mode matches window-title prefixes, as the old AHK did. Change `MainTitle` / `ComparisonTitle` in the profile if needed.

## Build and tests

PowerShell is needed only to rebuild the executable from source:

```powershell
& 'C:\Users\sterl\Documents\GitHub\The-Library\apps\powerscribe-report-exporter\build.ps1' -Test
```

The executable uses Windows' .NET Framework 4.x and built-in Windows assemblies. It has no NuGet packages or AutoHotkey runtime. Tests cover the actual keyboard menu/click/copy/Tab/close sequence, delayed rendering that occurs only on read, stale clipboard results, Conclusion-only paired exports, heading detection, bounded copy retry, text-free diagnostics, owner checking, automatic/strict focus behavior, bounded failed recovery, interrupted menu recovery, no extra Down, concurrent save/close coordination, completed-pair preservation, background logging, inaccessible selection providers, and old-profile defaults. They do not run PowerScribe or read the real clipboard.

## Sources and internal-export research

- For a separate portable server-address finder and one-accession API diagnostic, see [PowerScribe API Probe](api-probe/README.md). It runs on the UAB workstation without PowerShell, Python, or AutoHotkey. It is a connection test, not a completed historical-revision exporter.
- Original workflow: [Review Reports 11.09.24.ahk](https://drive.google.com/file/d/10Q4LyN_0QgcdPbnzQlzOw9_RJYt7BSSP/view), modified November 9, 2024. The Drive file and UAB master script were not changed.
- [Microsoft: SendInput](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput)
- [Microsoft: GetGUIThreadInfo](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getguithreadinfo), [SetFocus](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setfocus), and [AttachThreadInput](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-attachthreadinput) for native child-control focus capture/restoration
- [Microsoft: GUITHREADINFO menu flags](https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-guithreadinfo), [LVM_GETNEXTITEM](https://learn.microsoft.com/en-us/windows/win32/controls/lvm-getnextitem), [LB_GETCURSEL](https://learn.microsoft.com/en-us/windows/win32/controls/lb-getcursel), and [SendMessageTimeout](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendmessagetimeoutw) for menu and standard-list navigation checks
- [Microsoft: GetClipboardSequenceNumber](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getclipboardsequencenumber), including delayed-rendering behavior
- [Microsoft: Windows clipboard operations](https://learn.microsoft.com/en-us/windows/win32/dataxchg/clipboard-operations), including delayed rendering and global-memory lifetime
- [Microsoft Windows Forms clipboard source](https://source.dot.net/Microsoft.Private.Windows.Core/System/Private/Windows/Ole/ClipboardCore.cs.html), including its internal retry sleeps
- [Microsoft: TextPattern.DocumentRange](https://learn.microsoft.com/en-us/dotnet/api/system.windows.automation.textpattern.documentrange)
- See `POWERSCRIBE_INTERNAL_EXPORT.md` for the investigation of PowerScribe 360 Web Services and an administrator-provided revision extract.
