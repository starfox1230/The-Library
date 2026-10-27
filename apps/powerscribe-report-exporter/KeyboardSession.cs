using System;
using System.Diagnostics;
using System.Threading;
using System.Collections.Generic;

namespace ReportExporter
{
    // This boundary also allows tests to run the real keyboard workflow against a fake desktop,
    // without injecting input into any actual app or reading the real clipboard.
    public interface IKeyboardDesktop
    {
        IntPtr FindWindow(string title, uint process);
        uint ProcessId(IntPtr hwnd);
        IntPtr Foreground { get; }
        bool VisibleEnabled(IntPtr hwnd);
        bool Visible(IntPtr hwnd);
        bool Activate(IntPtr hwnd);
        IntPtr NavigationFocus(IntPtr main);
        bool RestoreNavigationFocus(IntPtr main, IntPtr child);
        bool MenuActive(IntPtr main);
        IntPtr[] MenuPopupWindows(IntPtr main);
        string NavigationRow(IntPtr child);
        void Key(ushort key);
        void Chord(ushort modifier, ushort key);
        void Click(IntPtr hwnd, int x, int y);
        bool ClearClipboard();
        uint ClipboardSequence { get; }
        uint ClipboardOwnerProcess { get; }
        bool ReadClipboard(out string text);
    }

    public sealed class Win32Desktop : IKeyboardDesktop
    {
        private static readonly NativeClipboard clipboard = new NativeClipboard(new WindowsClipboardAccess());
        private readonly IntPtr lockedMain, lockedChild;
        private readonly Action<string> progress;
        public Win32Desktop() : this(IntPtr.Zero, IntPtr.Zero, null) { }
        public Win32Desktop(IntPtr worklistMain, IntPtr worklistChild, Action<string> reportProgress)
        { lockedMain = worklistMain; lockedChild = worklistChild; progress = reportProgress ?? (message => {}); }
        public IntPtr FindWindow(string title, uint process) { return Native.UniqueWindow(title, process, true); }
        public uint ProcessId(IntPtr hwnd) { uint pid; Native.GetWindowThreadProcessId(hwnd, out pid); return pid; }
        public IntPtr Foreground { get { return Native.GetForegroundWindow(); } }
        public bool VisibleEnabled(IntPtr hwnd) { return Native.IsWindow(hwnd) && Native.IsWindowVisible(hwnd) && Native.IsWindowEnabled(hwnd); }
        public bool Visible(IntPtr hwnd) { return Native.IsWindow(hwnd) && Native.IsWindowVisible(hwnd); }
        public bool Activate(IntPtr hwnd) { return Native.ActivateWindow(hwnd); }
        public IntPtr NavigationFocus(IntPtr main)
        {
            if (lockedChild != IntPtr.Zero)
            {
                if (main != lockedMain || !Native.IsNavigationChild(main, lockedChild))
                    throw new InvalidOperationException("The F8 worklist control is no longer valid. Use Remember worklist (F8) again after selecting the first case row.");
                progress("Using the worklist control remembered with F8 for this exporter session.");
                return lockedChild;
            }
            return Native.NavigationFocus(main, progress);
        }
        public bool RestoreNavigationFocus(IntPtr main, IntPtr child) { return Native.RestoreChildFocus(main, child); }
        public bool MenuActive(IntPtr main) { return Native.MenuActive(main); }
        public IntPtr[] MenuPopupWindows(IntPtr main) { return Native.MenuPopupWindows(main); }
        public string NavigationRow(IntPtr child) { return Native.SelectedRowIndex(child); }
        public void Key(ushort key) { Native.Key(key); }
        public void Chord(ushort modifier, ushort key) { Native.Chord(modifier, key); }
        public void Click(IntPtr hwnd, int x, int y) { Native.Click(hwnd, x, y); }
        public bool ClearClipboard()
        { return clipboard.Clear(); }
        public uint ClipboardSequence { get { return Native.GetClipboardSequenceNumber(); } }
        public uint ClipboardOwnerProcess
        {
            get { IntPtr owner = Native.GetClipboardOwner(); return owner == IntPtr.Zero ? 0 : ProcessId(owner); }
        }
        public bool ReadClipboard(out string text)
        { return ReadText(out text); }
        public static bool ReadText(out string text)
        { return clipboard.Read(out text); }
    }

    public sealed class FocusRecovery
    {
        private readonly Profile profile;
        private readonly IKeyboardDesktop desktop;
        private readonly Action<string> progress;
        private readonly Stopwatch clock = Stopwatch.StartNew();
        private IntPtr pending;
        private long lastAttempt = -100;
        public int Recoveries { get; private set; }
        public FocusRecovery(Profile profile, IKeyboardDesktop desktop, Action<string> progress)
        { this.profile = profile; this.desktop = desktop; this.progress = progress; }
        public void ResetCount() { Recoveries = 0; }
        // Nonblocking attempt for dialog-open/close readiness loops, whose target can change.
        public bool TryFocus(IntPtr target, CancellationToken token)
        {
            token.ThrowIfCancellationRequested();
            if (desktop.Foreground == target)
            {
                if (pending == target) { Recoveries++; pending = IntPtr.Zero; progress("PowerScribe focus restored; continuing this case."); }
                return true;
            }
            if (!profile.AutoRestoreFocus) throw new InvalidOperationException("PowerScribe lost focus. Automatic focus recovery is disabled.");
            if (pending != target)
            { pending = target; lastAttempt = -100; progress("Another window took focus; returning focus to PowerScribe..."); }
            if (target != IntPtr.Zero && desktop.VisibleEnabled(target) && clock.ElapsedMilliseconds - lastAttempt >= 100)
            { lastAttempt = clock.ElapsedMilliseconds; desktop.Activate(target); }
            if (desktop.Foreground == target)
            { Recoveries++; pending = IntPtr.Zero; progress("PowerScribe focus restored; continuing this case."); return true; }
            return false;
        }
        public void Ensure(IntPtr target, CancellationToken token)
        {
            token.ThrowIfCancellationRequested();
            if (desktop.Foreground == target && desktop.VisibleEnabled(target)) return;
            ReadyWait.Until(() => desktop.VisibleEnabled(target) && TryFocus(target, token),
                Math.Min(profile.TimeoutMs, 3000), profile.PollMs, token,
                "Windows did not return focus to PowerScribe within the recovery timeout. No further input was sent.");
        }
    }

    public sealed class KeyboardSession : IReportSession, ISessionTelemetry
    {
        private readonly Profile profile;
        private readonly IKeyboardDesktop desktop;
        private readonly Action<string> progress;
        private readonly IntPtr main;
        private readonly uint pid;
        private IntPtr comparison;
        private IntPtr navigationFocus;
        private bool navigationInitialized;
        private readonly HashSet<IntPtr> existingPopups;
        private bool captureResolved;
        private readonly FocusRecovery focus;
        private int copyRetries;
        private long clipboardReadMs, clipboardReadMaxMs, clipboardClearMs;
        private int clipboardLockMisses;
        public int FocusRecoveries { get { return focus.Recoveries; } }
        public bool CanVerifySelectedRow { get { return false; } }
        public string SelectedCase() { throw new NotSupportedException("Keyboard mode cannot inspect the selected case row."); }

        public KeyboardSession(Profile settings, IKeyboardDesktop windows, Action<string> reportProgress)
        {
            settings.Validate(); profile = settings; desktop = windows;
            progress = reportProgress ?? (message => {});
            focus = new FocusRecovery(profile, desktop, progress);
            progress("Keyboard workflow: finding PowerScribe; no accessibility capture needed...");
            main = desktop.FindWindow(profile.MainTitle, 0);
            if (main == IntPtr.Zero) throw new InvalidOperationException("PowerScribe reporting window was not found. Its title must start with: " + profile.MainTitle);
            pid = desktop.ProcessId(main);
            // Ignore already-present floating tool windows; watch popup windows that
            // appear during this run, including managed menus with no native menu flags.
            existingPopups = new HashSet<IntPtr>(desktop.MenuPopupWindows(main));
            if (desktop.FindWindow(profile.ComparisonTitle, pid) != IntPtr.Zero)
                throw new InvalidOperationException("Close Compare Report Revisions and select your first case before starting.");
            // Reactivating PowerScribe can reset its child focus to the report editor.
            // Read the retained worklist focus before any activation, then verify/restore it.
            navigationFocus = desktop.NavigationFocus(main);
            if (navigationFocus != IntPtr.Zero) progress("Remembered worklist focus before activating PowerScribe.");
            progress("Activating PowerScribe for the same click / Tab sequence as the AHK...");
            desktop.Activate(main); // Readiness/focus recovery confirms activation before any input.
        }

        private void Guard(IntPtr window, CancellationToken token)
        {
            focus.Ensure(window, token);
        }
        private void Wait(Func<bool> ready, CancellationToken token, string reason)
        { ReadyWait.Until(ready, profile.TimeoutMs, profile.PollMs, token, reason); }
        private void InputSettle(IntPtr window, int milliseconds, CancellationToken token)
        {
            Guard(window, token);
            if (milliseconds > 0 && token.WaitHandle.WaitOne(milliseconds)) token.ThrowIfCancellationRequested();
            Guard(window, token);
        }

        private bool ToolsMenuActive()
        {
            return desktop.MenuActive(main) || ToolsPopupVisible();
        }

        private bool ToolsPopupVisible()
        {
            foreach (IntPtr popup in desktop.MenuPopupWindows(main))
                if (!existingPopups.Contains(popup)) return true;
            return false;
        }

        private void GuardMenuRecovery(CancellationToken token)
        {
            if (desktop.FindWindow(profile.ComparisonTitle, pid) != IntPtr.Zero || !desktop.VisibleEnabled(main))
                throw new InvalidOperationException("A comparison or modal appeared during menu recovery. Stopped without skipping or Down.");
            Guard(main, token);
        }

        private void WaitMenuClear(CancellationToken token, int timeout)
        {
            var clock = Stopwatch.StartNew();
            long clearSince = -1;
            ReadyWait.Until(() => {
                GuardMenuRecovery(token);
                if (ToolsMenuActive()) { clearSince = -1; return false; }
                if (clearSince < 0) clearSince = clock.ElapsedMilliseconds;
                return clock.ElapsedMilliseconds - clearSince >= 50;
            }, timeout, profile.PollMs, token, "Tools menu remained active.");
        }

        private void ExitToolsMenu(CancellationToken token, bool failedShortcut = false)
        {
            GuardMenuRecovery(token);
            if (!failedShortcut && !ToolsMenuActive()) return;
            progress("Leaving the Tools dropdown and menu bar before worklist navigation...");
            // Always unwind both levels after a failed shortcut. Native menu flags
            // alone can be false while a custom dropdown or menu bar still has input.
            // Escape never toggles a closed menu back open, unlike an unconditional Alt.
            for (int index = 0; index < 2; index++)
            {
                GuardMenuRecovery(token);
                desktop.Key(0x1B);
                InputSettle(main, Math.Max(20, profile.KeyDelayMs), token);
            }
            try
            {
                WaitMenuClear(token, Math.Min(profile.TimeoutMs, 500));
            }
            catch (TimeoutException error)
            {
                if (error.Message != "Tools menu remained active.") throw;
                GuardMenuRecovery(token);
                if (ToolsMenuActive())
                {
                    progress("A menu popup is still present; trying Alt cancellation once...");
                    desktop.Key(0x12);
                    InputSettle(main, Math.Max(20, profile.KeyDelayMs), token);
                }
                try { WaitMenuClear(token, Math.Min(profile.TimeoutMs, 500)); }
                catch (TimeoutException retryError)
                {
                    if (retryError.Message != "Tools menu remained active.") throw;
                    throw new TimeoutException("Tools menu could not be exited. Stopped without Down or another comparison attempt.");
                }
            }
            progress("Tools menu exited; navigation keys can now reach the worklist.");
        }

        public void OpenComparison(CancellationToken token)
        {
            captureResolved = false;
            focus.ResetCount(); copyRetries = 0;
            clipboardReadMs = clipboardReadMaxMs = clipboardClearMs = 0; clipboardLockMisses = 0;
            Wait(() => desktop.VisibleEnabled(main) && focus.TryFocus(main, token), token, "PowerScribe did not become active and enabled.");
            Guard(main, token);
            bool firstOpen = !navigationInitialized;
            if (navigationFocus == IntPtr.Zero)
            {
                navigationFocus = desktop.NavigationFocus(main);
                if (navigationFocus == IntPtr.Zero)
                    throw new InvalidOperationException("PowerScribe did not expose usable worklist focus. Use Remember worklist (F8), click the first CASE ROW in PowerScribe, then press F8 while PowerScribe is active. If capture is rejected, the status/progress log gives the focus reason. No comparison shortcut or Down was sent.");
                progress("Remembered the focused worklist control for this run; it will be restored before Down.");
            }
            ExitToolsMenu(token);
            if (firstOpen)
            {
                Guard(main, token);
                if (!desktop.RestoreNavigationFocus(main, navigationFocus))
                    throw new InvalidOperationException("The remembered worklist could not regain focus before export. Use Remember worklist (F8) again. No comparison shortcut or Down was sent.");
                navigationInitialized = true;
            }
            progress("Opening Tools with Alt+T, then I...");
            bool menuCompleted = false;
            for (int attempt = 0; attempt < 3 && !menuCompleted; attempt++)
            {
                Guard(main, token);
                int recoveryCount = focus.Recoveries;
                desktop.Chord(0x12, 0x54); // One chord instead of separate Alt/T events and two waits.
                InputSettle(main, profile.KeyDelayMs, token);
                // A focus change can dismiss the menu. Reopen it before sending I.
                if (focus.Recoveries != recoveryCount) continue;
                ReadyWait.Until(() => {
                    GuardMenuRecovery(token);
                    return focus.Recoveries != recoveryCount || ToolsPopupVisible();
                }, Math.Min(profile.TimeoutMs, 1000), profile.PollMs, token,
                    "Tools dropdown did not become visible. Stopped on this row without marking it unavailable or advancing.");
                if (focus.Recoveries != recoveryCount) continue;
                desktop.Key(0x49);
                menuCompleted = true;
            }
            if (!menuCompleted) throw new InvalidOperationException("Focus changed repeatedly during the Tools menu shortcut. Stopped without sending I to a dismissed menu.");
            progress("Waiting for Compare Report Revisions to appear...");
            try { ReadyWait.Until(() => {
                comparison = desktop.FindWindow(profile.ComparisonTitle, pid);
                if (comparison != IntPtr.Zero && desktop.VisibleEnabled(comparison)) return focus.TryFocus(comparison, token);
                if (desktop.VisibleEnabled(main)) focus.TryFocus(main, token);
                return false;
            }, profile.ComparisonWaitMs, profile.PollMs, token, "Comparison opening wait expired."); }
            catch (TimeoutException error)
            {
                if (error.Message != "Comparison opening wait expired.") throw;
                // A slow-but-existing comparison or unknown modal is NOT an unavailable case.
                comparison = desktop.FindWindow(profile.ComparisonTitle, pid);
                if (comparison != IntPtr.Zero || !desktop.VisibleEnabled(main))
                    throw new TimeoutException("Comparison opening timed out, but a window or modal is still present. Stopped without skipping or sending Down.");
                Guard(main, token);
                ExitToolsMenu(token, true);
                if (desktop.FindWindow(profile.ComparisonTitle, pid) != IntPtr.Zero || !desktop.VisibleEnabled(main))
                    throw new TimeoutException("A comparison or modal appeared after menu recovery. Stopped without skipping.");
                throw new ComparisonUnavailableException("Compare Report Revisions did not open; revisions may be unavailable.");
            }
        }

        public ReportPair ReadReports(CancellationToken token)
        {
            Guard(comparison, token);
            progress("Clicking the attending report body at " + profile.ClickX + ", " + profile.ClickY + "...");
            desktop.Click(comparison, profile.ClickX, profile.ClickY);
            InputSettle(comparison, profile.KeyDelayMs, token);
            var attendingClock = Stopwatch.StartNew();
            string attending = Copy("attending", token, true);
            long attendingMs = attendingClock.ElapsedMilliseconds;
            Guard(comparison, token);
            progress("Tab to the resident report body — same as the AHK...");
            desktop.Key(0x09);
            InputSettle(comparison, profile.KeyDelayMs, token);
            var residentClock = Stopwatch.StartNew();
            string resident = Copy("resident", token);
            captureResolved = true;
            return new ReportPair { Attending = attending, Resident = resident, Method = "keyboard-clipboard",
                AttendingEmptyUnconfirmed = attending == null,
                AttendingCopyMs = attendingMs, ResidentCopyMs = residentClock.ElapsedMilliseconds, CopyRetries = copyRetries,
                ClipboardReadMs = clipboardReadMs, ClipboardReadMaxMs = clipboardReadMaxMs,
                ClipboardClearMs = clipboardClearMs, ClipboardLockMisses = clipboardLockMisses };
        }

        private string Copy(string role, CancellationToken token, bool inspectResidentAfterEmpty = false)
        {
            var clearClock = Stopwatch.StartNew();
            Wait(() => {
                Guard(comparison, token);
                bool cleared = desktop.ClearClipboard();
                if (!cleared) clipboardLockMisses++;
                return cleared;
            }, token, "Clipboard remained locked before copying " + role + ".");
            clipboardClearMs += clearClock.ElapsedMilliseconds;
            uint before = desktop.ClipboardSequence;
            Guard(comparison, token);
            progress("Select all and copy the " + role + " report body...");
            desktop.Chord(0x11, 0x41);
            InputSettle(comparison, profile.KeyDelayMs, token);
            desktop.Chord(0x11, 0x43);
            progress("Waiting for a fresh " + role + " report copy with Findings, Impression, or Conclusion...");
            string text = null;
            bool changed = false, readable = false, gotText = false, wrongOwner = false, foundHeading = false;
            bool sawChange = false, sawText = false, sawLocked = false, sawWrongOwner = false, sawMissingHeading = false;
            bool freshOwnedEmpty = false;
            int attempts = 1;
            var clock = Stopwatch.StartNew();
            string lastObservation = null;
            try
            {
                Wait(() => {
                    Guard(comparison, token);
                    // Read FIRST. Delayed-rendering providers may not increment the sequence
                    // until a data request causes them to render the selected text.
                    var readClock = Stopwatch.StartNew();
                    readable = desktop.ReadClipboard(out text);
                    long readMs = readClock.ElapsedMilliseconds;
                    clipboardReadMs += readMs; clipboardReadMaxMs = Math.Max(clipboardReadMaxMs, readMs);
                    if (!readable) clipboardLockMisses++;
                    if (readMs >= 100) progress(role + " clipboard data read took " + readMs + " ms (including Windows/provider time).");
                    Guard(comparison, token);
                    changed = desktop.ClipboardSequence != before;
                    uint owner = desktop.ClipboardOwnerProcess;
                    wrongOwner = owner != 0 && owner != pid;
                    gotText = readable && !String.IsNullOrWhiteSpace(text);
                    freshOwnedEmpty = changed && readable && !gotText && owner == pid;
                    foundHeading = gotText && ReportText.ExtractBody(text) != null;
                    sawChange |= changed; sawText |= gotText; sawLocked |= !readable;
                    sawWrongOwner |= changed && wrongOwner;
                    sawMissingHeading |= changed && gotText && !wrongOwner && !foundHeading;
                    string observation = role + " clipboard: changed=" + changed + ", readable=" + readable +
                        ", characters=" + (text == null ? 0 : text.Length) + ", owner=" +
                        (owner == 0 ? "unreported" : wrongOwner ? "another process" : "PowerScribe") + ", recognized heading=" + foundHeading + ".";
                    if (observation != lastObservation) { progress(observation); lastObservation = observation; }
                    // Preserve the freshness, foreground, owner and section checks.
                    if (changed && !wrongOwner && foundHeading) return true;
                    int retryAt = attempts == 1 ? 100 : 400;
                    if (attempts < 3 && clock.ElapsedMilliseconds >= retryAt &&
                        profile.TimeoutMs - clock.ElapsedMilliseconds > profile.PollMs &&
                        !sawWrongOwner && !sawMissingHeading && (!changed || !readable || !gotText))
                    {
                        // Selection has already settled; keep checking text until this point,
                        // rather than adding a blind 100 ms sleep before retrying Ctrl+C.
                        Guard(comparison, token);
                        progress("Retrying Ctrl+C for the already selected " + role + " report (attempt " + (attempts + 1) + " of 3)...");
                        desktop.Chord(0x11, 0x43);
                        attempts++; copyRetries++;
                    }
                    return false;
                }, token, "Report copy timed out.");
            }
            catch (TimeoutException error)
            {
                if (error.Message != "Report copy timed out.") throw; // Preserve a focus-recovery timeout's actual cause.
                if (inspectResidentAfterEmpty && freshOwnedEmpty && !sawText && !sawWrongOwner && !sawMissingHeading)
                {
                    progress("Fresh empty attending clipboard update observed after bounded retries. Checking resident report; pending signature is possible, not confirmed.");
                    return null;
                }
                string reason = sawWrongOwner ? "A fresh clipboard update was owned by another process; it was rejected." :
                    sawMissingHeading ? "Fresh report text was copied, but it did not contain a Findings, Impression, or Conclusion heading." :
                    !sawChange && sawText ? "Text was readable, but the clipboard never showed a fresh sequence after clearing." :
                    !sawChange ? "Ctrl+C produced no fresh clipboard update." :
                    sawLocked && !sawText ? "The clipboard changed but its text could not be read." :
                    "The clipboard changed but no usable plain report text was available.";
                throw new TimeoutException("The " + role + " report was not copied. " + reason +
                    " Copy attempts: " + attempts + ". No incomplete case was saved. PowerScribe was left at this case. " +
                    "Try Ctrl+C manually and paste into Notepad; do not send report text. The progress log contains clipboard checks without report text.");
            }
            return text;
        }

        public void CloseComparison(CancellationToken token)
        {
            if (!captureResolved) throw new InvalidOperationException("A complete pair or a validated resident with an unconfirmed empty attending copy is required before closing the comparison.");
            Guard(comparison, token);
            progress("From resident report: Tab four times, then Enter — same as the AHK...");
            for (int index = 0; index < 4; index++) { Guard(comparison, token); desktop.Key(0x09); }
            InputSettle(comparison, profile.KeyDelayMs, token);
            desktop.Key(0x0D);
            progress("Waiting for the comparison window to close...");
            Wait(() => {
                if (!desktop.Visible(comparison) && desktop.VisibleEnabled(main)) return focus.TryFocus(main, token);
                if (desktop.VisibleEnabled(comparison)) focus.TryFocus(comparison, token);
                return false;
            }, token, "The comparison did not close after four Tabs and Enter. No Down key was sent.");
            comparison = IntPtr.Zero;
        }

        public void Advance(string previousCase, CancellationToken token)
        {
            Guard(main, token);
            ExitToolsMenu(token);
            progress("Restoring the original worklist control before moving to the next case...");
            if (!desktop.RestoreNavigationFocus(main, navigationFocus))
                throw new InvalidOperationException("The original worklist control could not regain focus. Stopped without Down, so the report editor cannot accidentally receive it.");
            Guard(main, token);
            if (!desktop.RestoreNavigationFocus(main, navigationFocus))
                throw new InvalidOperationException("Worklist focus changed before Down. Stopped without advancing.");
            if (ToolsMenuActive())
                throw new InvalidOperationException("A menu became active before Down. Stopped before retrying the same case.");
            string before = desktop.NavigationRow(navigationFocus);
            Guard(main, token);
            if (desktop.FindWindow(profile.ComparisonTitle, pid) != IntPtr.Zero || ToolsMenuActive())
                throw new InvalidOperationException("A comparison or menu appeared before Down. Stopped without navigation.");
            progress("Worklist focused; Down once to the next case...");
            desktop.Key(0x28);
            InputSettle(main, profile.CaseDelayMs, token);
            Wait(() => { Guard(main, token); return desktop.VisibleEnabled(main); }, token, "PowerScribe did not become ready after Down.");
            if (before != null)
            {
                Wait(() => {
                    Guard(main, token);
                    string after = desktop.NavigationRow(navigationFocus);
                    if (after == null) throw new InvalidOperationException("Worklist row-index verification became unavailable after Down.");
                    return after != before;
                }, token, "Down was sent once, but the selected worklist row index did not change. Stopped without relabeling the same row or retrying Down.");
                progress("Selected worklist row index changed after Down. Identical report text is allowed.");
            }
            else progress("Down sent to the remembered control; this custom worklist does not expose a supported native row index. Report text is not used to infer case identity.");
        }
    }
}
