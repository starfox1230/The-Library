using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using System.Collections.Generic;
using System.Runtime.Serialization.Json;
using System.Text;

namespace ReportExporter
{
    public static class Tests
    {
        private static int passed;
        private static void Assert(bool condition, string message)
        { if (!condition) throw new Exception(message); }
        private static void Test(string name, Action test)
        { test(); passed++; Console.WriteLine("PASS " + name); }
        private static void Throws<T>(Action action) where T : Exception
        { try { action(); } catch (T) { return; } throw new Exception("Expected " + typeof(T).Name); }

        private sealed class FakeSession : IReportSession
        {
            public bool CanVerifySelectedRow { get { return !NoSelectionProvider; } }
            public bool NoSelectionProvider;
            public int Row = 0, Opens, Reads, Closes, Advances;
            public bool FreezeSelection, MissingResident, FailAdvance, FailClose;
            public CancellationTokenSource CancelAfterRead;
            public bool ChangeDuringRead;
            public string SelectedCase() { if (NoSelectionProvider) throw new Exception("Unavailable selection must not be queried"); return "row-" + (FreezeSelection ? 0 : Row); }
            public void OpenComparison(CancellationToken token) { Opens++; }
            public ReportPair ReadReports(CancellationToken token)
            {
                Reads++;
                if (ChangeDuringRead) Row++;
                if (CancelAfterRead != null) CancelAfterRead.Cancel();
                return new ReportPair { Attending = "Patient header\r\nFINDINGS: attending " + Row,
                    Resident = MissingResident ? "IMPRESSION only" : "Header\r\nFindings: resident " + Row, Method = "fake" };
            }
            public void CloseComparison(CancellationToken token)
            { Closes++; if (FailClose) throw new TimeoutException("Did not close"); }
            public void Advance(string previousCase, CancellationToken token)
            { Advances++; if (FailAdvance) throw new TimeoutException("No new selected case"); Row++; }
        }

        private sealed class FakeKeyboardDesktop : IKeyboardDesktop
        {
            public readonly List<string> Events = new List<string>();
            public IntPtr Active = new IntPtr(1);
            public bool ComparisonOpen, FailOpen, FailClose, NoFreshSequence, LoseFocusOnCopy;
            public bool IdenticalReportBodies, IdenticalCopiedHeaders, NativeRowSupported;
            public bool FreezeRow, NoNavigationControl, RejectNavigationFocus, MainModal, ModalOnOpen, BlockComparison;
            public bool ResetFocusOnActivation, RejectInitialNavigationFocus, NavigationOnlyAfterActivation;
            private bool activated;
            public int UnavailableRow = -1;
            public int MenuDepth, MenuDownCount, AltCancelCount;
            public bool RefuseMenuExit, MenuStateUnreadable;
            public int MenuReadDelay;
            public bool CloseMenuOnUnavailable;
            public bool CustomPopupNoNativeFlags, IgnoreEscape, FailTools;
            public int ToolsReadDelay, EscapeExitReadDelay, DropdownReadDelay;
            public bool ExistingFloatingPopup;
            private bool toolsPending;
            private IntPtr focused = new IntPtr(10);
            public bool RenderOnlyWhenRead, FirstCopyIgnored, MissingReportHeading, ClipboardLocked;
            public bool LoseFocusOnOpen, LoseFocusOnClose, LoseFocusOnTools, BlockActivation;
            public int RejectRecoveryAttempts;
            public int BusyReadsRemaining;
            public string ReportHeading = "FINDINGS:";
            private bool residentPane;
            public int Row, CopyCount;
            public readonly HashSet<int> EmptyAttendingRows = new HashSet<int>();
            public bool EmptyResident, EmptyAttendingNoUpdate;
            public int AttendingEmptyThenTextReads;
            public CancellationTokenSource CancelOnResidentCopy;
            public uint Owner = 44;
            private uint sequence;
            private string text, pending;
            private int pendingPolls;
            public IntPtr FindWindow(string title, uint process) { return title.StartsWith("PowerScribe") ? new IntPtr(1) : ComparisonOpen ? new IntPtr(2) : IntPtr.Zero; }
            public uint ProcessId(IntPtr window) { return 44; }
            public IntPtr Foreground { get { return Active; } }
            public bool VisibleEnabled(IntPtr window) { return window == new IntPtr(1) ? !ComparisonOpen && !MainModal : ComparisonOpen && !BlockComparison; }
            public bool Visible(IntPtr window) { return window == new IntPtr(1) || ComparisonOpen; }
            public bool Activate(IntPtr window)
            {
                Events.Add("activate");
                if (Active == new IntPtr(999) && (BlockActivation || RejectRecoveryAttempts-- > 0)) return false;
                if (!activated && window == new IntPtr(1) && ResetFocusOnActivation) focused = new IntPtr(11);
                activated = true; Active = window; return true;
            }
            public IntPtr NavigationFocus(IntPtr main) { return NoNavigationControl || (NavigationOnlyAfterActivation && !activated) || focused == new IntPtr(11) ? IntPtr.Zero : focused; }
            public bool RestoreNavigationFocus(IntPtr main, IntPtr child)
            { Events.Add("restore-list"); if (RejectInitialNavigationFocus || (RejectNavigationFocus && CopyCount > 0) || child != new IntPtr(10)) return false; focused = child; return true; }
            public bool MenuActive(IntPtr main)
            {
                if (MenuStateUnreadable) throw new InvalidOperationException("Menu state unavailable");
                if (MenuReadDelay > 0 && --MenuReadDelay == 0) MenuDepth = 0;
                return !CustomPopupNoNativeFlags && MenuDepth > 0;
            }
            public IntPtr[] MenuPopupWindows(IntPtr main)
            {
                if (toolsPending && ToolsReadDelay > 0 && --ToolsReadDelay == 0) { MenuDepth = 2; toolsPending = false; }
                if (MenuDepth == 1 && DropdownReadDelay > 0 && --DropdownReadDelay == 0) MenuDepth = 2;
                var popups = new List<IntPtr>();
                if (ExistingFloatingPopup) popups.Add(new IntPtr(43));
                if (MenuDepth > 1) popups.Add(new IntPtr(42));
                return popups.ToArray();
            }
            public string NavigationRow(IntPtr child) { return NativeRowSupported ? "row:" + Row : null; }
            public void Key(ushort key)
            {
                Events.Add("key:" + key.ToString("X2"));
                if (key == 0x49 && ModalOnOpen) MainModal = true;
                if (key == 0x49 && MenuDepth == 2 && !FailOpen && Row != UnavailableRow) { MenuDepth = 0; ComparisonOpen = true; residentPane = false; Active = LoseFocusOnOpen ? new IntPtr(999) : new IntPtr(2); }
                if (key == 0x49 && (FailOpen || Row == UnavailableRow) && CloseMenuOnUnavailable) MenuDepth = 0;
                if (key == 0x1B && !RefuseMenuExit && !IgnoreEscape && MenuDepth > 0)
                { if (EscapeExitReadDelay > 0) MenuReadDelay = EscapeExitReadDelay; else MenuDepth--; }
                if (key == 0x12) { AltCancelCount++; if (!RefuseMenuExit) MenuDepth = MenuDepth == 0 ? 1 : 0; }
                if (key == 0x09) residentPane = true;
                if (key == 0x0D && !FailClose) { ComparisonOpen = false; focused = new IntPtr(11); Active = LoseFocusOnClose ? new IntPtr(999) : new IntPtr(1); }
                if (key == 0x28 && MenuDepth > 0) MenuDownCount++;
                if (key == 0x28 && MenuDepth == 0 && focused == new IntPtr(10) && !FreezeRow) Row++;
            }
            public void Chord(ushort modifier, ushort key)
            {
                Events.Add("chord:" + modifier.ToString("X2") + ":" + key.ToString("X2"));
                if (modifier == 0x12 && key == 0x54 && !FailTools) toolsPending = true;
                if (modifier == 0x12 && key == 0x54 && !FailTools && ToolsReadDelay == 0) MenuDepth = DropdownReadDelay > 0 ? 1 : 2;
                if (modifier == 0x12 && key == 0x54 && LoseFocusOnTools) { Active = new IntPtr(999); LoseFocusOnTools = false; }
                if (key == 0x43)
                {
                    CopyCount++; pendingPolls = 0;
                    string result = "HEADER " + (IdenticalCopiedHeaders ? "linked" : Row.ToString()) + "\r\n" + (MissingReportHeading ? "Report content without a section title " : ReportHeading + " ") + (IdenticalReportBodies ? "same" : (residentPane ? "resident " : "attending ") + Row);
                    if (!residentPane && EmptyAttendingRows.Contains(Row))
                    { if (EmptyAttendingNoUpdate) return; result = ""; }
                    if (residentPane && EmptyResident) result = "";
                    if (residentPane && CancelOnResidentCopy != null) CancelOnResidentCopy.Cancel();
                    if (FirstCopyIgnored && CopyCount == 1) return;
                    if (NoFreshSequence) text = result; else pending = result;
                    if (LoseFocusOnCopy) Active = new IntPtr(999);
                }
            }
            public void Click(IntPtr window, int x, int y) { Events.Add("click:" + x + ":" + y); }
            public bool ClearClipboard() { text = null; pending = null; sequence++; Events.Add("clear"); return true; }
            public uint ClipboardSequence
            {
                get
                {
                    if (!RenderOnlyWhenRead && pending != null && ++pendingPolls >= 3) { text = pending; pending = null; sequence++; }
                    return sequence;
                }
            }
            public uint ClipboardOwnerProcess { get { return Owner; } }
            public bool ReadClipboard(out string result)
            {
                if (BusyReadsRemaining-- > 0) { result = null; return false; }
                if (RenderOnlyWhenRead && pending != null) { text = pending; pending = null; sequence++; }
                result = ClipboardLocked ? null : text;
                if (!residentPane && text != null && AttendingEmptyThenTextReads-- > 0) result = "";
                return !ClipboardLocked;
            }
        }

        private static Profile KeyboardSettings()
        { return new Profile { TimingMode = "Custom", KeyboardWorkflow = true, KeyDelayMs = 0, CaseDelayMs = 0, PollMs = 1, TimeoutMs = 250, ComparisonWaitMs = 250 }; }

        private sealed class TestOffscreenPopup : System.Windows.Forms.ToolStripDropDown
        {
            [StructLayout(LayoutKind.Sequential)]
            private struct Position { public IntPtr Window, InsertAfter; public int X, Y, Width, Height; public uint Flags; }
            protected override void WndProc(ref System.Windows.Forms.Message message)
            {
                base.WndProc(ref message);
                if (message.Msg == 0x0046 && message.LParam != IntPtr.Zero) // Test-owned WM_WINDOWPOSCHANGING.
                {
                    var position = (Position)Marshal.PtrToStructure(message.LParam, typeof(Position));
                    position.X = position.Y = -20000; position.Flags &= ~2u;
                    Marshal.StructureToPtr(position, message.LParam, false);
                }
            }
        }

        private sealed class TestOffscreenForm : System.Windows.Forms.Form
        {
            protected override bool ShowWithoutActivation { get { return true; } }
            public TestOffscreenForm()
            {
                StartPosition = System.Windows.Forms.FormStartPosition.Manual;
                Location = new System.Drawing.Point(-20000, -20000);
                ShowInTaskbar = false;
            }
        }

        private sealed class FakeClipboard : IClipboardAccess, IDisposable
        {
            public bool Busy, FailEmpty, FailLock, ThrowOnData;
            public ulong OverrideSize;
            public int Opens, Closes, Empties, Locks, Unlocks, DataRequests;
            public readonly Dictionary<uint, byte[]> Formats = new Dictionary<uint, byte[]>();
            private readonly Dictionary<IntPtr, byte[]> memory = new Dictionary<IntPtr, byte[]>();
            public bool Open() { Opens++; return !Busy; }
            public bool Empty() { Empties++; return !FailEmpty; }
            public void Close() { Closes++; }
            public bool HasFormat(uint format) { return Formats.ContainsKey(format); }
            public IntPtr Data(uint format)
            {
                DataRequests++;
                if (ThrowOnData) throw new InvalidOperationException("Synthetic data error");
                byte[] bytes = Formats[format];
                IntPtr pointer = Marshal.AllocHGlobal(Math.Max(1, bytes.Length));
                Marshal.Copy(bytes, 0, pointer, bytes.Length); memory.Add(pointer, bytes); return pointer;
            }
            public ulong Size(IntPtr data) { return OverrideSize == 0 ? (ulong)memory[data].Length : OverrideSize; }
            public IntPtr Lock(IntPtr data) { Locks++; return FailLock ? IntPtr.Zero : data; }
            public void Unlock(IntPtr data) { Unlocks++; }
            public void Dispose() { foreach (IntPtr pointer in memory.Keys) Marshal.FreeHGlobal(pointer); }
        }

        [STAThread]
        public static int Main()
        {
            string directory = Path.Combine(Path.GetTempPath(), "NativeReportExporterTests-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(directory);
            Func<string> path = () => Path.Combine(directory, Guid.NewGuid().ToString("N") + ".txt");
            try
            {
                Test("native clipboard busy returns after one open attempt without nested retries", () => {
                    using (var access = new FakeClipboard { Busy = true })
                    {
                        var clipboard = new NativeClipboard(access); string text;
                        Assert(!clipboard.Read(out text) && text == null && access.Opens == 1 && access.Closes == 0 && access.DataRequests == 0, "Busy read was retried internally or touched data");
                        Assert(!clipboard.Clear() && access.Opens == 2 && access.Empties == 0, "Busy clear was retried internally or cleared content");
                    }
                });
                Test("native clipboard Unicode is bounded, null-terminated, and preserves accents and surrogate pairs", () => {
                    using (var access = new FakeClipboard())
                    {
                        access.Formats[13] = Encoding.Unicode.GetBytes("CONCLUSION: résumé 🧠\0MUST_NOT_COPY_PADDING");
                        string text; Assert(new NativeClipboard(access).Read(out text) && text == "CONCLUSION: résumé 🧠", "Unicode text corrupted or padding copied");
                        Assert(access.Closes == 1 && access.Unlocks == 1, "Clipboard/global memory stayed locked");
                    }
                });
                Test("native clipboard preserves ANSI fallback for empty Unicode", () => {
                    using (var access = new FakeClipboard())
                    {
                        access.Formats[13] = new byte[] { 0, 0 }; access.Formats[1] = Encoding.Default.GetBytes("FINDINGS: fallback\0padding");
                        string text; Assert(new NativeClipboard(access).Read(out text) && text == "FINDINGS: fallback" && access.Unlocks == 2 && access.Closes == 1, "ANSI fallback failed or resource leaked");
                    }
                });
                Test("native clipboard with no text format remains readable and releases ownership", () => {
                    using (var access = new FakeClipboard())
                    {
                        string text; Assert(new NativeClipboard(access).Read(out text) && text == null && access.DataRequests == 0 && access.Closes == 1, "Absent text treated as ready data or kept clipboard open");
                    }
                });
                Test("native clipboard rejects oversized memory before locking or copying", () => {
                    using (var access = new FakeClipboard { OverrideSize = (ulong)NativeClipboard.MaximumBytes + 1 })
                    {
                        access.Formats[13] = new byte[] { 0, 0 };
                        string text; Assert(!new NativeClipboard(access).Read(out text) && access.Locks == 0 && access.Closes == 1, "Oversize data was copied or clipboard stayed open");
                    }
                });
                Test("native clipboard lock failure and data exception always close clipboard", () => {
                    using (var access = new FakeClipboard { FailLock = true })
                    {
                        access.Formats[13] = new byte[] { 0, 0 }; string text;
                        Assert(!new NativeClipboard(access).Read(out text) && access.Closes == 1 && access.Unlocks == 0, "Failed memory lock did not release clipboard");
                        access.ThrowOnData = true;
                        Throws<InvalidOperationException>(() => new NativeClipboard(access).Read(out text));
                        Assert(access.Closes == 2, "Exception left clipboard open");
                    }
                });
                Test("native clear success and failure release clipboard after one attempt", () => {
                    using (var access = new FakeClipboard())
                    {
                        var clipboard = new NativeClipboard(access); Assert(clipboard.Clear(), "Clear did not succeed");
                        access.FailEmpty = true; Assert(!clipboard.Clear() && access.Opens == 2 && access.Empties == 2 && access.Closes == 2, "Failed clear nested retries or leaked clipboard lock");
                    }
                });
                Test("native text decoding rejects missing terminators and malformed UTF16", () => {
                    string text;
                    Assert(!NativeClipboard.Decode(Encoding.Unicode.GetBytes("FINDINGS: unterminated"), true, out text), "Unterminated Unicode accepted");
                    Assert(!NativeClipboard.Decode(Encoding.ASCII.GetBytes("FINDINGS: unterminated"), false, out text), "Unterminated ANSI accepted");
                    Assert(!NativeClipboard.Decode(new byte[] { 0, 0xD8, 0, 0 }, true, out text), "Malformed surrogate accepted");
                });
                Test("complete pairs default to whole reports and preserve labels", () => {
                    var session = new FakeSession(); var runner = new ExportRunner(); string output = path();
                    runner.Run(session, 21, 23, output, CancellationToken.None, message => {});
                    string text = File.ReadAllText(output);
                    Assert(runner.Completed == 3 && session.Opens == 3 && session.Closes == 3 && session.Advances == 2, "Wrong transition count / extra Down after final case");
                    Assert(text.Contains("Case 21\r\nAttending Report:\r\nPatient header\r\nFINDINGS: attending 0") && text.Contains("Case 23"), "Labels or report order changed");
                    Assert(text.Contains("Patient header") && text.Contains("Header"), "Whole report context was removed");
                    Assert(File.ReadAllText(output + ".for-comparison.txt") == text, "Comparison file lost full reports");
                    Assert(File.ReadAllLines(output + ".timings.csv").Length == 4, "Missing timing rows");
                });
                Test("Findings-only option preserves the old complete-pair format", () => {
                    string output = path();
                    new ExportRunner(true).Run(new FakeSession(), 7, 7, output, CancellationToken.None, m => {});
                    string text = File.ReadAllText(output + ".for-comparison.txt");
                    Assert(text.Contains("Case 7\r\nAttending Report:\r\nFINDINGS: attending 0") && !text.Contains("header") && !text.Contains("Header"), "Legacy mode retained context or lost labels");
                });
                Test("whole-report format retains distinct indication/comparison and conclusion-only text", () => {
                    var pair = new ReportPair { Attending = "INDICATION: A\r\nCOMPARISON: B\r\nCONCLUSION: Normal.\r\n",
                        Resident = "INDICATION: C\r\nCOMPARISON: D\r\nFindings/Impression: Normal.\r\n" };
                    string text = ReportText.Format(12, pair);
                    Assert(text.Contains("INDICATION: A") && text.Contains("COMPARISON: B") && text.Contains("INDICATION: C") && text.Contains("COMPARISON: D"), "Context lost");
                    Assert(ReportText.Format(12, pair, true).Contains("CONCLUSION: Normal.") && !ReportText.Format(12, pair, true).Contains("INDICATION"), "Legacy heading fallback changed");
                });
                Test("delivery copies only the completed-pair file and preserves Unicode", () => {
                    string output = path(); File.WriteAllText(output, "ARCHIVAL PLACEHOLDER");
                    string expected = "Case 3\r\nAttending Report:\r\nINDICATION: café →\r\nFindings: normal\r\nResident Report:\r\nFindings: normal\r\n";
                    File.WriteAllText(output + ".for-comparison.txt", expected, Encoding.UTF8);
                    string copied = null;
                    Assert(ExportDelivery.CopyCompleted(output, 1, text => copied = text) && copied == expected, "Wrong file/encoding copied");
                });
                Test("zero complete pairs and empty comparison files never overwrite clipboard", () => {
                    string output = path();
                    Assert(!ExportDelivery.CopyCompleted(output, 0, text => { throw new Exception("Unexpected clipboard write"); }), "Zero pairs copied");
                    File.WriteAllText(output + ".for-comparison.txt", " ");
                    Assert(!ExportDelivery.CopyCompleted(output, 1, text => { throw new Exception("Unexpected clipboard write"); }), "Empty text copied");
                });
                Test("clipboard delivery failure leaves saved reports intact", () => {
                    string output = path(); File.WriteAllText(output + ".for-comparison.txt", "Saved report");
                    Throws<IOException>(() => ExportDelivery.CopyCompleted(output, 1, text => { throw new IOException("Locked clipboard"); }));
                    Assert(File.ReadAllText(output + ".for-comparison.txt") == "Saved report", "Delivery failure damaged export");
                });
                Test("missing resident never commits a partial attending report", () => {
                    var session = new FakeSession { MissingResident = true }; var runner = new ExportRunner(); string output = path();
                    Throws<InvalidOperationException>(() => runner.Run(session, 1, 2, output, CancellationToken.None, m => {}));
                    Assert(runner.Completed == 0 && File.ReadAllText(output) == "" && session.Advances == 0, "A partial case was committed or skipped");
                });
                Test("next-case timeout preserves completed output and never retries Down", () => {
                    var session = new FakeSession { FailAdvance = true }; var runner = new ExportRunner(); string output = path();
                    Throws<TimeoutException>(() => runner.Run(session, 8, 10, output, CancellationToken.None, m => {}));
                    Assert(runner.Completed == 1 && session.Advances == 1 && session.Opens == 1 && File.ReadAllText(output).Contains("Case 8"), "Lost completed output or sent another Down");
                });
                Test("close timeout never advances", () => {
                    var session = new FakeSession { FailClose = true }; var runner = new ExportRunner(); string output = path();
                    Throws<TimeoutException>(() => runner.Run(session, 1, 2, output, CancellationToken.None, m => {}));
                    Assert(runner.Completed == 1 && session.Advances == 0, "Advanced without a closed dialog");
                });
                Test("duplicate selected row stops before copying again", () => {
                    var session = new FakeSession { FreezeSelection = true }; var runner = new ExportRunner(); string output = path();
                    Throws<InvalidOperationException>(() => runner.Run(session, 1, 2, output, CancellationToken.None, m => {}));
                    Assert(runner.Completed == 1 && session.Reads == 1, "Copied the same selected case twice");
                });
                Test("cancellation during capture commits no pair and sends no close or Down", () => {
                    using (var cancellation = new CancellationTokenSource())
                    {
                        var session = new FakeSession { CancelAfterRead = cancellation }; var runner = new ExportRunner(); string output = path();
                        Throws<OperationCanceledException>(() => runner.Run(session, 1, 2, output, cancellation.Token, m => {}));
                        Assert(runner.Completed == 0 && session.Closes == 0 && session.Advances == 0 && File.ReadAllText(output) == "", "Cancellation still triggered a commit or input");
                    }
                });
                Test("selected row changing during capture never commits mismatched reports", () => {
                    var session = new FakeSession { ChangeDuringRead = true }; var runner = new ExportRunner(); string output = path();
                    Throws<InvalidOperationException>(() => runner.Run(session, 1, 2, output, CancellationToken.None, m => {}));
                    Assert(runner.Completed == 0 && File.ReadAllText(output) == "" && session.Closes == 0 && session.Advances == 0, "Mismatched pair was saved");
                });
                Test("existing export is preserved", () => {
                    string output = path(); File.WriteAllText(output, "existing"); var session = new FakeSession();
                    Throws<IOException>(() => new ExportRunner().Run(session, 1, 1, output, CancellationToken.None, m => {}));
                    Assert(File.ReadAllText(output) == "existing" && session.Opens == 0, "Existing export replaced");
                });
                Test("invalid range causes no UI operations", () => {
                    var session = new FakeSession();
                    Throws<ArgumentException>(() => new ExportRunner().Run(session, 9, 2, path(), CancellationToken.None, m => {}));
                    Assert(session.Opens == 0, "Invalid input opened PowerScribe");
                });
                Test("wait checks readiness immediately even with a long poll interval", () => {
                    int calls = 0; var watch = System.Diagnostics.Stopwatch.StartNew();
                    ReadyWait.Until(() => { calls++; return true; }, 1000, 1000, CancellationToken.None, "unused");
                    Assert(calls == 1 && watch.ElapsedMilliseconds < 250, "A fixed delay happened before the first check");
                });
                Test("wait observes delayed readiness", () => {
                    int calls = 0;
                    ReadyWait.Until(() => ++calls == 4, 500, 2, CancellationToken.None, "unused");
                    Assert(calls == 4, "Wait did not recheck readiness");
                });
                Test("wait timeout and cancellation are bounded", () => {
                    Throws<TimeoutException>(() => ReadyWait.Until(() => false, 20, 2, CancellationToken.None, "timed out"));
                    using (var cancellation = new CancellationTokenSource())
                    {
                        cancellation.Cancel();
                        Throws<OperationCanceledException>(() => ReadyWait.Until(() => true, 1000, 1000, cancellation.Token, "unused"));
                    }
                });
                Test("Findings matching tolerates case and retains Impression", () => {
                    Assert(ReportText.ExtractBody("header\nfindings: X\nIMPRESSION: Y\r\n") == "findings: X\nIMPRESSION: Y", "Trim lost report text");
                    Assert(ReportText.ExtractBody("") == null && ReportText.ExtractBody("only Impression") == null, "Missing section heading accepted");
                });
                Test("Conclusion-only and Impression-only reports preserve their complete body", () => {
                    Assert(ReportText.ExtractBody("HEADER\r\nCONCLUSION:\r\nSynthetic conclusion\r\n") == "CONCLUSION:\r\nSynthetic conclusion", "Conclusion-only report rejected");
                    Assert(ReportText.ExtractBody("HEADER\nImpression\nSynthetic impression") == "Impression\nSynthetic impression", "Standalone Impression heading rejected");
                    Assert(ReportText.ExtractBody("Header\n  Conclusions: Synthetic conclusion") == "Conclusions: Synthetic conclusion", "Plural conclusion heading rejected");
                    Assert(ReportText.ExtractBody("Findings/Impression: Synthetic combined section") != null, "Combined heading rejected");
                });
                Test("mentions of findings in headers do not override the actual conclusion heading", () => {
                    Assert(ReportText.ExtractBody("History: correlate with findings elsewhere\nConclusion: Synthetic conclusion") == "Conclusion: Synthetic conclusion", "History mention mistaken for section heading");
                    Assert(ReportText.ExtractBody("History: prior findings only") == null, "Non-report header accepted");
                });
                Test("Findings trimming remains preferred when Impression is also present", () => {
                    Assert(ReportText.ExtractBody("HEADER\nFINDINGS: Synthetic findings\nIMPRESSION: Synthetic impression") == "FINDINGS: Synthetic findings\nIMPRESSION: Synthetic impression", "Findings removed");
                });
                Test("same report pane calibration is rejected", () => {
                    var locator = new Locator { AutomationId = "report", ClassName = "edit", TypeId = 50004, X = .2, Y = .5 };
                    var profile = new Profile { KeyboardWorkflow = false, CaseList = locator, Attending = locator, Resident = locator, Close = locator };
                    Throws<InvalidOperationException>(() => profile.Validate());
                });
                Test("keyboard default needs no accessibility captures", () => {
                    var profile = new Profile(); profile.Validate();
                    Assert(profile.KeyboardWorkflow && profile.ClickX == 800 && profile.ClickY == 600 && profile.KeyDelayMs == 10 && profile.PollMs == 5 && profile.CaseDelayMs == 100, "Default no longer follows coordinates/faster timing or case delay changed");
                    profile.KeyboardWorkflow = false;
                    Throws<InvalidOperationException>(() => profile.Validate());
                });
                Test("old profiles acquire keyboard settings without recapturing controls", () => {
                    using (var stream = new MemoryStream(Encoding.UTF8.GetBytes("{\"TimeoutMs\":10000,\"PollMs\":10,\"StableMs\":50}")))
                    {
                        var profile = (Profile)new DataContractJsonSerializer(typeof(Profile)).ReadObject(stream);
                        profile.Validate();
                        Assert(profile.KeyboardWorkflow && profile.ClickX == 800 && profile.ClickY == 600 && profile.KeyDelayMs == 25 && profile.AutoRestoreFocus && !profile.FindingsOnly, "Legacy profile lacks keyboard/full-report defaults");
                    }
                });
                Test("explicit Findings-only setting survives profile roundtrip", () => {
                    using (var stream = new MemoryStream())
                    {
                        var serializer = new DataContractJsonSerializer(typeof(Profile));
                        serializer.WriteObject(stream, new Profile { FindingsOnly = true }); stream.Position = 0;
                        var profile = (Profile)serializer.ReadObject(stream); profile.Validate();
                        Assert(profile.FindingsOnly, "Export selection was not retained");
                    }
                });
                Test("runner does not query inaccessible row selection in keyboard mode", () => {
                    var session = new FakeSession { NoSelectionProvider = true }; var runner = new ExportRunner();
                    runner.Run(session, 1, 2, path(), CancellationToken.None, m => {});
                    Assert(runner.Completed == 2 && session.Advances == 1, "Keyboard mode still depends on selection accessibility");
                });
                Test("real keyboard session follows original menu / click / copy / Tab / Enter sequence", () => {
                    var desktop = new FakeKeyboardDesktop(); var runner = new ExportRunner(); string output = path();
                    var session = new KeyboardSession(KeyboardSettings(), desktop, m => {});
                    runner.Run(session, 5, 6, output, CancellationToken.None, m => {});
                    Assert(runner.Completed == 2 && desktop.Row == 1 && desktop.CopyCount == 4, "Wrong copy or next-case count");
                    string trace = String.Join("|", desktop.Events.ToArray());
                    Assert(trace.StartsWith("activate|restore-list|chord:12:54|key:49|click:800:600|clear|chord:11:41|chord:11:43|key:09|clear|chord:11:41|chord:11:43|key:09|key:09|key:09|key:09|key:0D|restore-list|restore-list|key:28"), "Sequence diverged from the menu / copy / Tab workflow: " + trace);
                    Assert(File.ReadAllText(output).Contains("Case 6\r\nAttending Report:\r\nHEADER 1\r\nFINDINGS: attending 1"), "Wrong report body in the second pair");
                });
                Test("keyboard copy never accepts text without a fresh clipboard sequence", () => {
                    var desktop = new FakeKeyboardDesktop { NoFreshSequence = true }; var runner = new ExportRunner();
                    var session = new KeyboardSession(KeyboardSettings(), desktop, m => {}); string output = path();
                    Throws<TimeoutException>(() => runner.Run(session, 1, 2, output, CancellationToken.None, m => {}));
                    Assert(runner.Completed == 0 && desktop.Row == 0 && !desktop.Events.Contains("key:0D"), "Failed copy closed or advanced the case");
                });
                Test("keyboard copies report when rendering and sequence update happen only on read", () => {
                    var desktop = new FakeKeyboardDesktop { RenderOnlyWhenRead = true }; var runner = new ExportRunner();
                    var session = new KeyboardSession(KeyboardSettings(), desktop, m => {}); string output = path();
                    runner.Run(session, 1, 1, output, CancellationToken.None, m => {});
                    Assert(runner.Completed == 1 && desktop.CopyCount == 2 && File.ReadAllText(output).Contains("FINDINGS: attending 0"), "Read-first delayed rendering failed");
                });
                Test("keyboard and exporter accept actual copied Conclusion-only reports", () => {
                    var desktop = new FakeKeyboardDesktop { ReportHeading = "CONCLUSION:" }; var runner = new ExportRunner(); string output = path();
                    var session = new KeyboardSession(KeyboardSettings(), desktop, m => {});
                    runner.Run(session, 1, 2, output, CancellationToken.None, m => {});
                    string text = File.ReadAllText(output);
                    Assert(runner.Completed == 2 && text.Contains("Attending Report:\r\nHEADER 0\r\nCONCLUSION: attending 0") && text.Contains("Resident Report:\r\nHEADER 1\r\nCONCLUSION: resident 1"), "Conclusion-only pairs were rejected or mislabeled");
                });
                Test("missed initial Ctrl+C gets a bounded retry without re-clicking or advancing", () => {
                    var desktop = new FakeKeyboardDesktop { FirstCopyIgnored = true }; var runner = new ExportRunner();
                    var settings = KeyboardSettings(); settings.TimeoutMs = 1200;
                    var session = new KeyboardSession(settings, desktop, m => {}); string output = path();
                    runner.Run(session, 1, 1, output, CancellationToken.None, m => {});
                    Assert(runner.Completed == 1 && desktop.CopyCount == 3 && desktop.Row == 0 && File.ReadAllText(output).Contains("FINDINGS: attending 0"), "Retry lost the selected pane or advanced the case");
                });
                Test("copy rejection identifies a fresh report with no recognized heading without logging text", () => {
                    var desktop = new FakeKeyboardDesktop { MissingReportHeading = true }; var runner = new ExportRunner();
                    var messages = new List<string>(); var session = new KeyboardSession(KeyboardSettings(), desktop, messages.Add);
                    try { runner.Run(session, 1, 1, path(), CancellationToken.None, messages.Add); throw new Exception("Should reject unidentified body"); }
                    catch (TimeoutException error) { Assert(error.Message.Contains("Fresh report text was copied") && error.Message.Contains("Conclusion"), "Incorrect copy rejection diagnosis"); }
                    Assert(runner.Completed == 0 && desktop.CopyCount == 1 && !String.Join("\n", messages.ToArray()).Contains("Report content without a section title"), "Report text logged or invalid copy retried");
                });
                Test("clipboard lock is distinguished from a missing Ctrl+C", () => {
                    var desktop = new FakeKeyboardDesktop { ClipboardLocked = true }; var runner = new ExportRunner();
                    var session = new KeyboardSession(KeyboardSettings(), desktop, m => {});
                    try { runner.Run(session, 1, 1, path(), CancellationToken.None, m => {}); throw new Exception("Should time out"); }
                    catch (TimeoutException error) { Assert(error.Message.Contains("could not be read"), "Locked clipboard diagnosis missing"); }
                    Assert(runner.Completed == 0 && desktop.Row == 0, "Locked clipboard advanced or committed");
                });
                Test("keyboard mode stops if foreground changes during copying", () => {
                    var desktop = new FakeKeyboardDesktop { LoseFocusOnCopy = true }; var runner = new ExportRunner();
                    var settings = KeyboardSettings(); settings.AutoRestoreFocus = false;
                    var session = new KeyboardSession(settings, desktop, m => {});
                    Throws<InvalidOperationException>(() => runner.Run(session, 1, 2, path(), CancellationToken.None, m => {}));
                    Assert(desktop.Row == 0 && runner.Completed == 0 && desktop.CopyCount == 1, "Sent more actions after focus loss");
                });
                Test("comparison opening recovers foreground automatically without repeating the menu", () => {
                    var desktop = new FakeKeyboardDesktop { LoseFocusOnOpen = true }; var runner = new ExportRunner(); string output = path();
                    var session = new KeyboardSession(KeyboardSettings(), desktop, m => {});
                    runner.Run(session, 1, 1, output, CancellationToken.None, m => {});
                    Assert(runner.Completed == 1 && session.FocusRecoveries == 1 && desktop.Events.FindAll(e => e == "key:49").Count == 1, "Focus loss opening comparison still aborted or reopened it");
                });
                Test("focus loss during the Tools chord reopens the menu before I", () => {
                    var desktop = new FakeKeyboardDesktop { LoseFocusOnTools = true }; var runner = new ExportRunner();
                    var session = new KeyboardSession(KeyboardSettings(), desktop, m => {});
                    runner.Run(session, 1, 1, path(), CancellationToken.None, m => {});
                    Assert(runner.Completed == 1 && desktop.Events.FindAll(e => e == "chord:12:54").Count == 2 && desktop.Events.FindAll(e => e == "key:49").Count == 1, "Dismissed menu was not reopened safely");
                });
                Test("copying and closing recover focus and log recovery counts", () => {
                    var desktop = new FakeKeyboardDesktop { LoseFocusOnCopy = true, LoseFocusOnClose = true }; var runner = new ExportRunner(); string output = path();
                    var session = new KeyboardSession(KeyboardSettings(), desktop, m => {});
                    runner.Run(session, 1, 1, output, CancellationToken.None, m => {});
                    Assert(runner.Completed == 1 && desktop.CopyCount == 2 && session.FocusRecoveries == 3, "Recoverable loss aborted or repeated a valid copy");
                    string[] columns = File.ReadAllLines(output + ".timings.csv");
                    Assert(columns[0].Contains("focus_recoveries") && columns[1].Split(',').Length == 17 && columns[1].Split(',')[11] == "3", "Detailed timing/recovery telemetry missing");
                });
                Test("temporary clipboard contention is polled and recorded without another copy", () => {
                    var desktop = new FakeKeyboardDesktop { BusyReadsRemaining = 3 }; var runner = new ExportRunner(); string output = path();
                    var session = new KeyboardSession(KeyboardSettings(), desktop, m => {});
                    runner.Run(session, 1, 1, output, CancellationToken.None, m => {});
                    string[] columns = File.ReadAllLines(output + ".timings.csv");
                    Assert(runner.Completed == 1 && desktop.CopyCount == 2 && columns[0].Contains("clipboard_read_max_ms") && columns[1].Split(',')[16] == "3", "Clipboard contention was not tracked, or copied another pane/advanced");
                });
                Test("saved timing profile preserves previously working waits until preset chosen", () => {
                    using (var stream = new MemoryStream(Encoding.UTF8.GetBytes("{\"Version\":4,\"KeyDelayMs\":100,\"CaseDelayMs\":200,\"PollMs\":10}")))
                    {
                        var profile = (Profile)new DataContractJsonSerializer(typeof(Profile)).ReadObject(stream); profile.Validate();
                        Assert(profile.KeyDelayMs == 100 && profile.CaseDelayMs == 200 && profile.PollMs == 10, "Saved timing was silently replaced");
                    }
                });
                Test("temporary activation rejection is retried without sending input elsewhere", () => {
                    var desktop = new FakeKeyboardDesktop { LoseFocusOnOpen = true, RejectRecoveryAttempts = 1 }; var runner = new ExportRunner();
                    var session = new KeyboardSession(KeyboardSettings(), desktop, m => {});
                    runner.Run(session, 1, 1, path(), CancellationToken.None, m => {});
                    Assert(runner.Completed == 1 && desktop.CopyCount == 2, "One rejected activation aborted the case");
                });
                Test("blocked focus recovery times out without close or next-case input", () => {
                    var desktop = new FakeKeyboardDesktop { LoseFocusOnCopy = true, BlockActivation = true }; var runner = new ExportRunner();
                    var session = new KeyboardSession(KeyboardSettings(), desktop, m => {});
                    Throws<TimeoutException>(() => runner.Run(session, 1, 2, path(), CancellationToken.None, m => {}));
                    Assert(runner.Completed == 0 && desktop.CopyCount == 1 && desktop.Row == 0 && !desktop.Events.Contains("key:0D"), "Unrecoverable focus sent more input");
                });
                Test("saving overlaps comparison close and commits only after save finishes", () => {
                    using (var started = new ManualResetEvent(false))
                    using (var release = new ManualResetEvent(false))
                    {
                        bool saved = false, committed = false; long saveMs, closeMs;
                        CaseCommit.SaveAndClose(() => { started.Set(); Assert(release.WaitOne(2000), "Concurrent close did not release saving"); saved = true; },
                            () => { Assert(started.WaitOne(2000), "Saving did not start while close was running"); Assert(!saved, "Saving incorrectly finished before concurrent close"); release.Set(); },
                            () => { Assert(saved, "Committed before the saving worker completed"); committed = true; }, out saveMs, out closeMs);
                        Assert(committed, "Concurrent save did not commit");
                    }
                });
                Test("close failure joins the saver and retains its committed pair", () => {
                    bool saved = false, committed = false; long saveMs, closeMs;
                    Throws<TimeoutException>(() => CaseCommit.SaveAndClose(() => saved = true, () => { throw new TimeoutException("close failed"); },
                        () => { Assert(saved, "Saver was not joined before commit"); committed = true; }, out saveMs, out closeMs));
                    Assert(saved && committed, "Close failure discarded a successfully saved pair");
                });
                Test("save failure does not claim a complete case", () => {
                    bool closed = false, committed = false; long saveMs, closeMs;
                    Throws<IOException>(() => CaseCommit.SaveAndClose(() => { throw new IOException("test write failed"); }, () => closed = true, () => committed = true, out saveMs, out closeMs));
                    Assert(closed && !committed, "Failed save counted as a complete case");
                });
                Test("background progress logger joins and preserves all messages on disposal", () => {
                    string logfile = path();
                    using (var log = new AsyncProgressLog(logfile)) for (int index = 0; index < 500; index++) log.WriteLine("Synthetic step " + index);
                    string[] lines = File.ReadAllLines(logfile);
                    Assert(lines.Length == 500 && lines[0] == "Synthetic step 0" && lines[499] == "Synthetic step 499", "Background log dropped or reordered messages");
                });
                Test("keyboard close timeout preserves saved pair and never sends Down", () => {
                    var desktop = new FakeKeyboardDesktop { FailClose = true }; var runner = new ExportRunner(); string output = path();
                    var session = new KeyboardSession(KeyboardSettings(), desktop, m => {});
                    Throws<TimeoutException>(() => runner.Run(session, 1, 2, output, CancellationToken.None, m => {}));
                    Assert(runner.Completed == 1 && desktop.Row == 0 && File.ReadAllText(output).Contains("Case 1"), "Close timeout lost saved data or advanced");
                });
                Test("keyboard mode supports identical report bodies with separate fresh copies", () => {
                    var desktop = new FakeKeyboardDesktop { IdenticalReportBodies = true, Owner = 0 }; var runner = new ExportRunner();
                    var session = new KeyboardSession(KeyboardSettings(), desktop, m => {});
                    runner.Run(session, 1, 2, path(), CancellationToken.None, m => {});
                    Assert(runner.Completed == 2 && desktop.CopyCount == 4, "Identical valid text or absent owner HWND was rejected");
                });
                Test("keyboard workflow rejects a known other-process clipboard owner", () => {
                    var desktop = new FakeKeyboardDesktop { Owner = 777 }; var runner = new ExportRunner();
                    var session = new KeyboardSession(KeyboardSettings(), desktop, m => {});
                    Throws<TimeoutException>(() => runner.Run(session, 1, 1, path(), CancellationToken.None, m => {}));
                    Assert(runner.Completed == 0, "Another application's clipboard data was accepted");
                });
                Test("unavailable comparisons preserve labels and continue without copying", () => {
                    var desktop = new FakeKeyboardDesktop { FailOpen = true }; var runner = new ExportRunner();
                    var session = new KeyboardSession(KeyboardSettings(), desktop, m => {}); string output = path();
                    runner.Run(session, 2, 3, output, CancellationToken.None, m => {});
                    string text = File.ReadAllText(output);
                    Assert(desktop.CopyCount == 0 && desktop.Row == 1 && runner.Skipped == 2 && runner.Completed == 0 && runner.Saved == 2, "Wrong skip or input count");
                    Assert(text.Contains("Case 2\r\nAttending Report:\r\n[REPORT UNAVAILABLE:") && text.Contains("Resident Report:") && text.Contains("Case 3"), "Placeholder broke labels");
                    Assert(File.ReadAllText(output + ".for-comparison.txt") == "", "Placeholders leaked into analysis input");
                });
                Test("first unavailable case is followed by actual reports with correct next labels", () => {
                    var desktop = new FakeKeyboardDesktop { UnavailableRow = 0 }; var runner = new ExportRunner(); string output = path();
                    runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 2, 4, output, CancellationToken.None, m => {});
                    string analysis = File.ReadAllText(output + ".for-comparison.txt");
                    Assert(runner.Completed == 2 && runner.Skipped == 1 && desktop.Row == 2 && desktop.CopyCount == 4, "Skip aborted or corrupted navigation");
                    Assert(analysis.Contains("Case 3\r\nAttending Report:\r\nHEADER 1\r\nFINDINGS: attending 1") && analysis.Contains("Case 4") && !analysis.Contains("UNAVAILABLE") && !analysis.Contains("Case 2"), "Wrong webapp input or labels");
                    Assert(File.ReadAllLines(output + ".timings.csv").Length == 4, "Skipped timing row missing");
                });
                Test("worklist receives Down after close moved focus into report editor", () => {
                    var desktop = new FakeKeyboardDesktop(); var runner = new ExportRunner(); string output = path();
                    runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 2, 4, output, CancellationToken.None, m => {});
                    Assert(runner.Completed == 3 && desktop.Row == 2 && File.ReadAllText(output).Contains("FINDINGS: attending 2"), "Editor swallowed Down or duplicated first case");
                });
                Test("native selected row staying unchanged stops on navigation rather than report text", () => {
                    var desktop = new FakeKeyboardDesktop { FreezeRow = true, NativeRowSupported = true }; var runner = new ExportRunner(); string output = path();
                    Throws<TimeoutException>(() => runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 2, 4, output, CancellationToken.None, m => {}));
                    Assert(runner.Completed == 1 && !desktop.ComparisonOpen && desktop.Row == 0 && desktop.CopyCount == 2 && !File.ReadAllText(output).Contains("Case 3"), "Unchanged native row was recopied");
                });
                Test("worklist focus failure sends no Down and preserves complete pair", () => {
                    var desktop = new FakeKeyboardDesktop { RejectNavigationFocus = true }; var runner = new ExportRunner();
                    Throws<InvalidOperationException>(() => runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 2, 3, path(), CancellationToken.None, m => {}));
                    Assert(runner.Completed == 1 && !desktop.Events.Contains("key:28"), "Down sent into wrong control");
                });
                Test("unidentifiable worklist stops before menu or input", () => {
                    var desktop = new FakeKeyboardDesktop { NoNavigationControl = true };
                    Throws<InvalidOperationException>(() => new ExportRunner().Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 1, 2, path(), CancellationToken.None, m => {}));
                    Assert(desktop.Events.Count == 1 && desktop.CopyCount == 0, "Unsafe worklist still received input");
                });
                Test("worklist retained before activation survives PowerScribe resetting focus to editor", () => {
                    var desktop = new FakeKeyboardDesktop { ResetFocusOnActivation = true }; var runner = new ExportRunner();
                    runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 1, 3, path(), CancellationToken.None, m => {});
                    Assert(runner.Completed == 3 && desktop.Row == 2 && desktop.CopyCount == 6, "Activation lost original worklist or repeated first case");
                });
                Test("missing preactivation focus can still be identified after activation", () => {
                    var desktop = new FakeKeyboardDesktop { NavigationOnlyAfterActivation = true }; var runner = new ExportRunner();
                    runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 1, 2, path(), CancellationToken.None, m => {});
                    Assert(runner.Completed == 2 && desktop.Row == 1, "Postactivation fallback was removed");
                });
                Test("failure restoring initial worklist stops before Tools copy or Down", () => {
                    var desktop = new FakeKeyboardDesktop { RejectInitialNavigationFocus = true }; var runner = new ExportRunner();
                    Throws<InvalidOperationException>(() => runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 1, 2, path(), CancellationToken.None, m => {}));
                    Assert(runner.Completed == 0 && desktop.CopyCount == 0 && !desktop.Events.Contains("chord:12:54") && !desktop.Events.Contains("key:28"), "Failed initial restore sent report/navigation input");
                });
                Test("editor classification rejects real editors without incidental edit substring", () => {
                    foreach (string name in new string[] { "Edit", "EDIT", "RichEdit20W", "RICHEDIT50W", "WindowsForms10.EDIT.app.0", "WindowsForms10.RichEdit20W.app.0", "CustomTextBox", "CustomReportEditor", "Scintilla" })
                        Assert(Native.IsTextEditorClass(name), "Editor accepted as worklist: " + name);
                    foreach (string name in new string[] { "SysListView32", "WindowsForms10.LISTBOX.app.0", "CreditGrid", "WindowsForms10.Window.8.app.0" })
                        Assert(!Native.IsTextEditorClass(name), "Noneditor class rejected: " + name);
                });
                Test("invalid remembered F8 worklist cannot silently fall back to current focus", () => {
                    Throws<InvalidOperationException>(() => new Win32Desktop(new IntPtr(111111), new IntPtr(222222), m => {}).NavigationFocus(new IntPtr(111111)));
                });
                Test("F8 native control validation accepts test-owned list and rejects editors stale and wrong roots", () => {
                    using (var parent = new TestOffscreenForm())
                    using (var other = new TestOffscreenForm())
                    using (var list = new System.Windows.Forms.ListView())
                    using (var editor = new System.Windows.Forms.RichTextBox())
                    {
                        parent.Controls.Add(list); parent.Controls.Add(editor); parent.Show();
                        IntPtr root = parent.Handle, child = list.Handle, text = editor.Handle;
                        Assert(Native.IsNavigationChild(root, child), "Test list is not a valid navigation child");
                        Assert(!Native.IsNavigationChild(root, text) && !Native.IsNavigationChild(root, root), "Editor or root accepted");
                        Assert(!Native.IsNavigationChild(other.Handle, child), "Unrelated root accepted");
                        var desktop = new Win32Desktop(root, child, m => {});
                        Assert(desktop.NavigationFocus(root) == child, "Explicit worklist not retained");
                        Throws<InvalidOperationException>(() => desktop.NavigationFocus(other.Handle));
                        list.Enabled = false; Throws<InvalidOperationException>(() => desktop.NavigationFocus(root));
                        list.Enabled = true; list.Visible = false; Throws<InvalidOperationException>(() => desktop.NavigationFocus(root));
                        list.Dispose(); Throws<InvalidOperationException>(() => desktop.NavigationFocus(root));
                    }
                });
                Test("Findings Conclusion heading variants preserve complete report bodies", () => {
                    foreach (string heading in new string[] { "Findings/Conclusion", "FINDINGS / CONCLUSIONS:", "Findings & Conclusion:", "Findings and Impression:", "Findings-Conclusion:", "Findings / Impression / Conclusion:", "CONCLUSION/FINDINGS:", "Impression and Findings:" })
                        Assert(ReportText.ExtractBody("Header\r\n" + heading + "\r\nSynthetic body") == heading + "\r\nSynthetic body", "Rejected " + heading);
                    var desktop = new FakeKeyboardDesktop { ReportHeading = "FINDINGS/CONCLUSION:" }; var runner = new ExportRunner();
                    runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 1, 2, path(), CancellationToken.None, m => {});
                    Assert(runner.Completed == 2, "Combined section rejected by real copy path");
                });
                Test("cancelled opening never records an unavailable placeholder", () => {
                    using (var cancel = new CancellationTokenSource())
                    {
                        var desktop = new FakeKeyboardDesktop { FailOpen = true }; var runner = new ExportRunner(); string output = path();
                        cancel.Cancel();
                        Throws<OperationCanceledException>(() => runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 1, 2, output, cancel.Token, m => {}));
                        Assert(runner.Saved == 0 && desktop.Row == 0 && File.ReadAllText(output) == "", "Cancellation created placeholder or advanced");
                    }
                });
                Test("unknown modal on opening stops without placeholder dismissal or Down", () => {
                    var desktop = new FakeKeyboardDesktop { FailOpen = true, ModalOnOpen = true }; var runner = new ExportRunner();
                    Throws<TimeoutException>(() => runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 1, 2, path(), CancellationToken.None, m => {}));
                    Assert(runner.Saved == 0 && !desktop.Events.Contains("key:1B") && !desktop.Events.Contains("key:28"), "Unknown modal was dismissed or skipped");
                });
                Test("existing but unready comparison never becomes unavailable placeholder", () => {
                    var desktop = new FakeKeyboardDesktop { BlockComparison = true }; var runner = new ExportRunner();
                    Throws<TimeoutException>(() => runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 1, 2, path(), CancellationToken.None, m => {}));
                    Assert(runner.Saved == 0 && desktop.CopyCount == 0 && !desktop.Events.Contains("key:1B") && !desktop.Events.Contains("key:28"), "Existing comparison was skipped");
                });
                Test("placeholder can never pass report heading validation", () => {
                    Assert(ReportText.ExtractBody(ReportText.FormatUnavailable(7)) == null, "Placeholder was accepted as copied report text");
                });
                Test("linked studies with identical full clipboard reports are both exported", () => {
                    foreach (bool supported in new bool[] { false, true })
                    {
                        var desktop = new FakeKeyboardDesktop { IdenticalReportBodies = true, IdenticalCopiedHeaders = true, NativeRowSupported = supported }; var runner = new ExportRunner(); string output = path();
                        runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 2, 4, output, CancellationToken.None, m => {});
                        Assert(runner.Completed == 3 && desktop.Row == 2 && desktop.CopyCount == 6 && File.ReadAllText(output).Contains("Case 4"), "Identical linked-study reports stopped the run");
                    }
                });
                Test("Win32 INPUT union has the correct native structure size", () => {
                    Type type = typeof(Native).GetNestedType("Input", System.Reflection.BindingFlags.NonPublic);
                    Assert(Marshal.SizeOf(type) == (IntPtr.Size == 8 ? 40 : 28), "SendInput would reject the native struct size");
                });
                Test("native GUI thread info matches Windows 32 and 64 bit layout", () => {
                    Type type = typeof(Native).GetNestedType("GuiThreadInfo", System.Reflection.BindingFlags.NonPublic);
                    Assert(Marshal.SizeOf(type) == (IntPtr.Size == 8 ? 72 : 48), "GetGUIThreadInfo would read the wrong layout");
                });
                Test("one Escape plus restored worklist focus can still send Down to menu", () => {
                    var desktop = new FakeKeyboardDesktop { FailOpen = true };
                    desktop.Chord(0x12, 0x54); desktop.Key(0x49); desktop.Key(0x1B);
                    Assert(desktop.RestoreNavigationFocus(new IntPtr(1), new IntPtr(10)), "Focus fixture did not restore");
                    desktop.Key(0x28);
                    Assert(desktop.Row == 0 && desktop.MenuDownCount == 1 && desktop.MenuDepth == 1, "Fixture does not reproduce v0.7 menu swallowing Down");
                });
                Test("unavailable cases exit menu and each nonfinal skip sends Down to list", () => {
                    var desktop = new FakeKeyboardDesktop { FailOpen = true }; var runner = new ExportRunner();
                    runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 2, 4, path(), CancellationToken.None, m => {});
                    Assert(runner.Skipped == 3 && desktop.Row == 2 && desktop.MenuDownCount == 0 && desktop.AltCancelCount == 0 && desktop.MenuDepth == 0, "Skipped case kept reattempting same row through active menu");
                });
                Test("already closed menu after unavailable shortcut is not reopened before Down", () => {
                    var desktop = new FakeKeyboardDesktop { FailOpen = true, CloseMenuOnUnavailable = true }; var runner = new ExportRunner();
                    runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 1, 2, path(), CancellationToken.None, m => {});
                    Assert(runner.Skipped == 2 && desktop.Row == 1 && desktop.MenuDepth == 0 && desktop.MenuDownCount == 0, "Alt accidentally left menu newly active");
                });
                Test("menu exit waits for delayed processing before Down", () => {
                    var desktop = new FakeKeyboardDesktop { FailOpen = true, EscapeExitReadDelay = 4 }; var runner = new ExportRunner();
                    runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 1, 2, path(), CancellationToken.None, m => {});
                    Assert(runner.Skipped == 2 && desktop.Row == 1 && desktop.MenuDownCount == 0, "Down raced delayed menu cancellation");
                });
                Test("menu Escape refusal has bounded Alt fallback before Down", () => {
                    var desktop = new FakeKeyboardDesktop { UnavailableRow = 0, IgnoreEscape = true }; var runner = new ExportRunner();
                    runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 1, 2, path(), CancellationToken.None, m => {});
                    Assert(runner.Skipped == 1 && runner.Completed == 1 && desktop.Row == 1 && desktop.MenuDownCount == 0, "Fallback did not leave menu before list navigation");
                });
                Test("menu that cannot exit stops without Down or another comparison attempt", () => {
                    var desktop = new FakeKeyboardDesktop { FailOpen = true, RefuseMenuExit = true }; var runner = new ExportRunner();
                    Throws<TimeoutException>(() => runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 1, 50, path(), CancellationToken.None, m => {}));
                    Assert(runner.Saved == 0 && desktop.Row == 0 && !desktop.Events.Contains("key:28") && desktop.Events.FindAll(e => e == "key:49").Count == 1, "Repeated same case after failed menu exit");
                });
                Test("unreadable menu state cannot authorize navigation or placeholder retry", () => {
                    var desktop = new FakeKeyboardDesktop { FailOpen = true, MenuStateUnreadable = true }; var runner = new ExportRunner();
                    Throws<InvalidOperationException>(() => runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 1, 50, path(), CancellationToken.None, m => {}));
                    Assert(runner.Saved == 0 && !desktop.Events.Contains("key:28"), "Unknown menu state still allowed navigation");
                });
                Test("custom dropdown with no native menu flags cannot shift labels after missing first case", () => {
                    var desktop = new FakeKeyboardDesktop { UnavailableRow = 0, CustomPopupNoNativeFlags = true }; var runner = new ExportRunner(); string output = path();
                    runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 1, 3, output, CancellationToken.None, m => {});
                    string text = File.ReadAllText(output);
                    Assert(runner.Skipped == 1 && runner.Completed == 2 && desktop.Row == 2 && desktop.MenuDownCount == 0, "Custom popup swallowed navigation");
                    Assert(text.Contains("Case 2\r\nAttending Report:\r\nHEADER 1\r\nFINDINGS: attending 1") && text.Contains("Case 3\r\nAttending Report:\r\nHEADER 2\r\nFINDINGS: attending 2"), "Available second case acquired third label");
                    Assert(desktop.Events.FindAll(e => e == "key:1B").Count == 2 && desktop.AltCancelCount == 0, "Failed shortcut did not unwind both menu levels");
                });
                Test("custom dropdown refusing dismissal stops before saving false skips or Down", () => {
                    var desktop = new FakeKeyboardDesktop { FailOpen = true, CustomPopupNoNativeFlags = true, RefuseMenuExit = true }; var runner = new ExportRunner();
                    Throws<TimeoutException>(() => runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 1, 3, path(), CancellationToken.None, m => {}));
                    Assert(runner.Saved == 0 && !desktop.Events.Contains("key:28") && desktop.Events.FindAll(e => e == "key:49").Count == 1, "Invisible native flags allowed a custom popup through recovery");
                });
                Test("Tools menu readiness waits for delayed menu before sending I", () => {
                    var desktop = new FakeKeyboardDesktop { ToolsReadDelay = 8, CustomPopupNoNativeFlags = true }; var runner = new ExportRunner();
                    runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 1, 1, path(), CancellationToken.None, m => {});
                    Assert(runner.Completed == 1 && desktop.Events.FindAll(e => e == "key:49").Count == 1 && desktop.ToolsReadDelay == 0, "I raced menu readiness");
                });
                Test("missed Tools shortcut stops without declaring report unavailable or advancing", () => {
                    var desktop = new FakeKeyboardDesktop { FailTools = true }; var runner = new ExportRunner();
                    Throws<TimeoutException>(() => runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 1, 3, path(), CancellationToken.None, m => {}));
                    Assert(runner.Saved == 0 && !desktop.Events.Contains("key:49") && !desktop.Events.Contains("key:28"), "Failed Tools shortcut generated a false skip");
                });
                Test("native menu bar alone does not authorize I before dropdown appears", () => {
                    var desktop = new FakeKeyboardDesktop { DropdownReadDelay = 8 }; var runner = new ExportRunner();
                    runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 1, 1, path(), CancellationToken.None, m => {});
                    Assert(runner.Completed == 1 && runner.Skipped == 0 && desktop.DropdownReadDelay == 0, "Native menu bar flags caused premature I");
                });
                Test("preexisting floating window is not mistaken for Tools popup readiness", () => {
                    var desktop = new FakeKeyboardDesktop { ExistingFloatingPopup = true, FailTools = true }; var runner = new ExportRunner();
                    Throws<TimeoutException>(() => runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 1, 2, path(), CancellationToken.None, m => {}));
                    Assert(runner.Saved == 0 && !desktop.Events.Contains("key:49") && !desktop.Events.Contains("key:28"), "Preexisting utility popup impersonated Tools dropdown");
                });
                Test("real managed dropdown is detected without native menu flags and disappears on close", () => {
                    using (var parent = new System.Windows.Forms.Form())
                    using (var popup = new TestOffscreenPopup())
                    {
                        IntPtr main = parent.Handle;
                        popup.AutoClose = false; popup.Items.Add("Synthetic menu item");
                        popup.Show(new System.Drawing.Point(-20000, -20000));
                        Assert(!Native.MenuActive(main), "Fixture uses native menu flags instead of a managed dropdown");
                        Assert(Array.IndexOf(Native.MenuPopupWindows(main), popup.Handle) >= 0, "Visible managed dropdown was missed");
                        Native.Rect rectangle; Native.GetWindowRect(popup.Handle, out rectangle);
                        Assert(rectangle.Left < -10000 && rectangle.Top < -10000, "Test popup is not offscreen");
                        popup.Close();
                        Assert(Array.IndexOf(Native.MenuPopupWindows(main), popup.Handle) < 0, "Hidden dropdown still blocks navigation");
                    }
                });
                Test("frozen native row after unavailable comparison stops without reopening it", () => {
                    var desktop = new FakeKeyboardDesktop { FailOpen = true, FreezeRow = true, NativeRowSupported = true }; var runner = new ExportRunner();
                    Throws<TimeoutException>(() => runner.Run(new KeyboardSession(KeyboardSettings(), desktop, m => {}), 1, 50, path(), CancellationToken.None, m => {}));
                    Assert(runner.Skipped == 1 && desktop.Events.FindAll(e => e == "key:49").Count == 1 && desktop.Events.FindAll(e => e == "key:28").Count == 1, "Unchanged native row was reopened or Down retried");
                });
                Test("native index reads target only test-owned list controls without report text", () => {
                    using (var list = new System.Windows.Forms.ListView())
                    using (var box = new System.Windows.Forms.ListBox())
                    using (var custom = new System.Windows.Forms.TextBox())
                    {
                        list.Items.Add("Synthetic row A"); list.Items.Add("Synthetic row B"); list.MultiSelect = false;
                        IntPtr handle = list.Handle;
                        list.Items[0].Selected = true;
                        Assert(Native.SelectedRowIndex(handle) == "listview:0", "Native list-view index incorrect");
                        list.Items[1].Selected = true;
                        Assert(Native.SelectedRowIndex(handle) == "listview:1", "Native list-view change unreadable");
                        box.Items.Add("Synthetic row A"); box.Items.Add("Synthetic row B"); handle = box.Handle; box.SelectedIndex = 1;
                        Assert(Native.SelectedRowIndex(handle) == "listbox:1", "Native list-box index incorrect");
                        Assert(Native.SelectedRowIndex(custom.Handle) == null, "Arbitrary control received list queries");
                    }
                });
                Test("empty attending between complete cases retains source labels and resident only in archive", () => {
                    var desktop = new FakeKeyboardDesktop(); desktop.EmptyAttendingRows.Add(1);
                    var runner = new ExportRunner(); string output = path();
                    runner.Run(new KeyboardSession(KeyboardSettings(), desktop, null), 8, 10, output, CancellationToken.None, s => {});
                    string archive = File.ReadAllText(output), comparison = File.ReadAllText(output + ".for-comparison.txt");
                    string ledger = File.ReadAllText(output + ".outcomes.csv");
                    Assert(runner.Completed == 2 && runner.Pending == 1 && runner.Saved == 3 && desktop.Row == 2, "Pending changed counters or numbering");
                    Assert(archive.Contains("Case 9\r\nCapture status: POSSIBLY") && archive.Contains("HEADER 1\r\nFINDINGS: resident 1"), "Incomplete resident source text lost");
                    Assert(comparison.Contains("Case 8\r\n") && comparison.Contains("Case 10\r\n") && !comparison.Contains("Case 9\r\n") && !comparison.Contains("resident 1"), "Incomplete pair leaked into comparison or next label shifted");
                    Assert(ledger.Contains("9,pending_suspected") && ledger.Contains("10,complete") && !ledger.Contains("FINDINGS") && runner.OutcomeSummary.Contains(": 9."), "Source outcome ledger/summary absent or contains report text");
                });
                Test("temporary empty attending rendering is allowed to become a complete report", () => {
                    var desktop = new FakeKeyboardDesktop { AttendingEmptyThenTextReads = 30 };
                    // Windows may round a 1 ms wait to a scheduler tick. Give all 30
                    // simulated transient reads time to resolve before the copy deadline.
                    var settings = KeyboardSettings(); settings.TimeoutMs = 2000;
                    var runner = new ExportRunner(); string output = path();
                    runner.Run(new KeyboardSession(settings, desktop, null), 1, 1, output, CancellationToken.None, s => {});
                    Assert(runner.Completed == 1 && runner.Pending == 0 && File.ReadAllText(output + ".for-comparison.txt").Contains("FINDINGS: attending 0"), "Transient empty rendering prematurely became pending");
                });
                Test("first final and consecutive empty attending cases close without an extra Down", () => {
                    var desktop = new FakeKeyboardDesktop(); desktop.EmptyAttendingRows.UnionWith(new int[] { 0, 1, 2 });
                    var runner = new ExportRunner(); string output = path();
                    runner.Run(new KeyboardSession(KeyboardSettings(), desktop, null), 25, 27, output, CancellationToken.None, s => {});
                    Assert(runner.Completed == 0 && runner.Pending == 3 && desktop.Row == 2 && !desktop.ComparisonOpen, "Consecutive/final pending navigation wrong");
                    Assert(File.ReadAllText(output + ".for-comparison.txt") == "" && runner.OutcomeSummary.Contains("25, 26, 27"), "Pending records became comparable or lost source labels");
                });
                Test("empty clipboard without fresh attending update stops without trying resident", () => {
                    var desktop = new FakeKeyboardDesktop { EmptyAttendingNoUpdate = true }; desktop.EmptyAttendingRows.Add(0);
                    var runner = new ExportRunner(); string output = path();
                    Throws<TimeoutException>(() => runner.Run(new KeyboardSession(KeyboardSettings(), desktop, null), 9, 10, output, CancellationToken.None, s => {}));
                    Assert(runner.Pending == 0 && desktop.Row == 0 && !desktop.Events.Contains("key:09") && File.ReadAllText(output + ".outcomes.csv").Contains("9,stopped_capture"), "No update was misclassified pending or failed source number lost");
                });
                Test("empty clipboard with absent or foreign owner cannot establish suspected pending", () => {
                    foreach (uint owner in new uint[] { 0, 123 })
                    {
                        var desktop = new FakeKeyboardDesktop { Owner = owner }; desktop.EmptyAttendingRows.Add(0);
                        var runner = new ExportRunner();
                        Throws<TimeoutException>(() => runner.Run(new KeyboardSession(KeyboardSettings(), desktop, null), 4, 5, path(), CancellationToken.None, s => {}));
                        Assert(runner.Saved == 0 && desktop.Row == 0 && !desktop.Events.Contains("key:09"), "Ambiguous empty owner became pending");
                    }
                });
                Test("unreadable attending clipboard does not enter pending fallback", () => {
                    var desktop = new FakeKeyboardDesktop { ClipboardLocked = true }; desktop.EmptyAttendingRows.Add(0);
                    var runner = new ExportRunner();
                    Throws<TimeoutException>(() => runner.Run(new KeyboardSession(KeyboardSettings(), desktop, null), 1, 2, path(), CancellationToken.None, s => {}));
                    Assert(runner.Saved == 0 && !desktop.Events.Contains("key:09"), "Unreadable data classified as empty");
                });
                Test("empty attending with invalid or empty resident does not close or advance", () => {
                    foreach (bool missingHeading in new bool[] { false, true })
                    {
                        var desktop = new FakeKeyboardDesktop { EmptyResident = !missingHeading, MissingReportHeading = missingHeading }; desktop.EmptyAttendingRows.Add(0);
                        var runner = new ExportRunner(); string output = path();
                        Throws<TimeoutException>(() => runner.Run(new KeyboardSession(KeyboardSettings(), desktop, null), 1, 2, output, CancellationToken.None, s => {}));
                        Assert(runner.Saved == 0 && desktop.Row == 0 && !desktop.Events.Contains("key:0D") && File.ReadAllText(output) == "", "Invalid resident was saved as pending");
                    }
                });
                Test("pending capture cancellation stays cancellation with no saved incomplete case", () => {
                    using (var cancellation = new CancellationTokenSource())
                    {
                        var desktop = new FakeKeyboardDesktop { CancelOnResidentCopy = cancellation }; desktop.EmptyAttendingRows.Add(0);
                        var runner = new ExportRunner(); string output = path();
                        Throws<OperationCanceledException>(() => runner.Run(new KeyboardSession(KeyboardSettings(), desktop, null), 7, 8, output, cancellation.Token, s => {}));
                        Assert(runner.Saved == 0 && desktop.Row == 0 && !desktop.Events.Contains("key:0D") && File.ReadAllText(output + ".outcomes.csv").Contains("7,cancelled_capture"), "Cancellation saved/skipped case or missing source status");
                    }
                });
                Test("pending close failure retains archive and ledger but never advances", () => {
                    var desktop = new FakeKeyboardDesktop { FailClose = true }; desktop.EmptyAttendingRows.Add(0);
                    var runner = new ExportRunner(); string output = path();
                    Throws<TimeoutException>(() => runner.Run(new KeyboardSession(KeyboardSettings(), desktop, null), 5, 6, output, CancellationToken.None, s => {}));
                    string ledger = File.ReadAllText(output + ".outcomes.csv");
                    Assert(runner.Pending == 1 && desktop.Row == 0 && !desktop.Events.Contains("key:28") && File.ReadAllText(output + ".for-comparison.txt") == "", "Close failure lost pending archive or advanced");
                    Assert(ledger.Contains("5,pending_suspected") && ledger.Contains("5,stopped_save_or_close"), "Saved outcome overwritten by close failure");
                });
                Test("pending capture cannot bypass unchanged native worklist row safeguard", () => {
                    var desktop = new FakeKeyboardDesktop { NativeRowSupported = true, FreezeRow = true }; desktop.EmptyAttendingRows.Add(0);
                    var runner = new ExportRunner(); string output = path();
                    Throws<TimeoutException>(() => runner.Run(new KeyboardSession(KeyboardSettings(), desktop, null), 25, 26, output, CancellationToken.None, s => {}));
                    string ledger = File.ReadAllText(output + ".outcomes.csv");
                    Assert(runner.Pending == 1 && !desktop.ComparisonOpen && desktop.Events.FindAll(e => e == "key:28").Count == 1 && ledger.Contains("25,stopped_navigation") && !ledger.Contains("26,started"), "Pending bypassed row verification or shifted labels");
                });
                Test("complete formatter refuses an incomplete capture even if text is present", () => {
                    Throws<InvalidOperationException>(() => ReportText.Format(1, new ReportPair { AttendingEmptyUnconfirmed = true, Attending = "FINDINGS: stale", Resident = "FINDINGS: resident" }));
                    Throws<InvalidOperationException>(() => ReportText.FormatPending(1, new ReportPair { AttendingEmptyUnconfirmed = true, Attending = "FINDINGS: stale", Resident = "FINDINGS: resident" }));
                });
                Test("automatic timing starts fast, backs off only on copy retry, and resets per run", () => {
                    var profile = new Profile(); InputTiming.Configure(profile);
                    var timing = new InputTiming(profile);
                    Assert(timing.KeyDelayMs == 10 && profile.CaseDelayMs == 100 && profile.PollMs == 5, "Automatic did not start fast");
                    Assert(timing.CopyRetry() && timing.KeyDelayMs == 25, "First retry did not add settling");
                    Assert(timing.CopyRetry() && timing.KeyDelayMs == 100 && !timing.CopyRetry(), "Adaptive settling is not bounded");
                    Assert(new InputTiming(profile).KeyDelayMs == 10 && profile.KeyDelayMs == 10, "A slow run changed the next run's fast start");
                });
                Test("fixed and custom speed never adapt their pauses", () => {
                    var profile = new Profile { TimingMode = "Conservative" }; InputTiming.Configure(profile);
                    var fixedTiming = new InputTiming(profile);
                    Assert(fixedTiming.KeyDelayMs == 100 && !fixedTiming.CopyRetry(), "Conservative changed dynamically");
                    profile.TimingMode = "Custom"; profile.KeyDelayMs = 37; InputTiming.Configure(profile);
                    Assert(new InputTiming(profile).KeyDelayMs == 37 && !new InputTiming(profile).CopyRetry(), "Custom timing was overwritten");
                });
                Test("automatic copy retry retains source safeguards and does not repeat row navigation", () => {
                    var settings = KeyboardSettings(); settings.TimingMode = "Automatic"; settings.TimeoutMs = 1000;
                    var desktop = new FakeKeyboardDesktop { FirstCopyIgnored = true };
                    var runner = new ExportRunner(); var messages = new List<string>();
                    runner.Run(new KeyboardSession(settings, desktop, messages.Add), 4, 5, path(), CancellationToken.None, messages.Add);
                    Assert(runner.Completed == 2 && desktop.Row == 1 && desktop.Events.FindAll(e => e == "key:28").Count == 1, "Retry duplicated a source row");
                    Assert(messages.Exists(s => s.Contains("Automatic speed")), "Adaptive copy settling was not recorded");
                });
                Test("old profiles acquire simple-launch defaults while keeping calibrated coordinates", () => {
                    using (var stream = new MemoryStream(Encoding.UTF8.GetBytes("{\"Version\":6,\"ClickX\":123,\"ClickY\":456,\"KeyDelayMs\":25}"))) {
                        var profile = (Profile)new DataContractJsonSerializer(typeof(Profile)).ReadObject(stream);
                        Assert(profile.TimingMode == "Automatic" && profile.OpenWebsite && profile.OpenTextFile && profile.ClickX == 123 && profile.ClickY == 456, "Migration lost setup or defaults");
                    }
                });
                Test("automatic output names are unique and do not replace a previous export", () => {
                    var stamp = new DateTime(2026, 10, 29, 1, 2, 3);
                    string one = ExportFiles.NewOutput(directory, stamp), two = ExportFiles.NewOutput(directory, stamp);
                    File.WriteAllText(one, "synthetic saved output");
                    Assert(one != two && Path.GetDirectoryName(one) == directory && File.ReadAllText(one) == "synthetic saved output", "Export path reused a name");
                });
                Test("recovery summary distinguishes saved navigation failures from unsaved captures", () => {
                    var runner = new ExportRunner();
                    Throws<TimeoutException>(() => runner.Run(new FakeSession { FailAdvance = true }, 8, 10, path(), CancellationToken.None, s => {}));
                    Assert(runner.LastAttemptedCase == 8 && runner.LastSavedCase == 8 && RunSummary.ResumeAt(runner, 8, 10) == 9, "Saved case would be exported twice");
                    runner = new ExportRunner();
                    Throws<InvalidOperationException>(() => runner.Run(new FakeSession { MissingResident = true }, 8, 10, path(), CancellationToken.None, s => {}));
                    Assert(runner.LastSavedCase == null && RunSummary.ResumeAt(runner, 8, 10) == 8, "Unsaved case would be skipped");
                });
                Test("final saved case with close failure does not suggest a nonexistent remaining range", () => {
                    var runner = new ExportRunner();
                    Throws<TimeoutException>(() => runner.Run(new FakeSession { FailClose = true }, 8, 8, path(), CancellationToken.None, s => {}));
                    Assert(!RunSummary.ResumeAt(runner, 8, 8).HasValue, "Final saved case produced a duplicate resume");
                    string summary = RunSummary.Build(runner, 8, 8, "Stopped", "Synthetic close failure", "synthetic-output.txt");
                    Assert(summary.Contains("Last saved source entry: 8") && !summary.Contains("FINDINGS:") && summary.Contains("No remaining"), "Run summary lost context or copied report text");
                });
                Test("compact launcher hides setup, expands Options and keeps Go visible", LauncherChecks.Verify);
                Test("live progress is shown only in the external overlay without resizing the launcher", LauncherChecks.VerifyProgressRouting);
                Test("typed case fields preserve valid ranges and reject blank, malformed, overflow and reversed input", LauncherChecks.VerifyTypedRange);
                Test("manual recovery reads complete pairs after a stopped run, never the archival file", () => {
                    var runner = new ExportRunner(); string output = path();
                    Throws<TimeoutException>(() => runner.Run(new FakeSession { FailAdvance = true }, 5, 7, output, CancellationToken.None, s => {}));
                    File.AppendAllText(output, "ARCHIVAL INCOMPLETE RECORD");
                    string text = ExportDelivery.ReadCompleted(output, runner.Completed);
                    Assert(text == File.ReadAllText(output + ".for-comparison.txt") && text.Contains("Case 5") && !text.Contains("ARCHIVAL"), "Stopped-run recovery loaded incomplete archival content");
                });
                Test("Notepad defaults on for new setups and retains an existing off preference", () => {
                    Assert(new Profile().OpenTextFile, "New setup does not open Notepad by default");
                    using (var stream = new MemoryStream(Encoding.UTF8.GetBytes("{\"Version\":7,\"OpenTextFile\":false}"))) {
                        var profile = (Profile)new DataContractJsonSerializer(typeof(Profile)).ReadObject(stream);
                        Assert(!profile.OpenTextFile, "Saved Notepad-off preference was lost");
                        profile.Validate();
                    }
                });
                Test("copied text recovers an overwritten clipboard, survives failures, and retains full Unicode text", LauncherChecks.VerifyCopiedText);
                Console.WriteLine(passed + " tests passed. These tests do not operate on PowerScribe or your clipboard.");
                return 0;
            }
            catch (Exception error) { Console.Error.WriteLine(error); return 1; }
            finally
            {
                // Only this test-owned, absolute directory is eligible for cleanup.
                if (Path.GetFullPath(directory).StartsWith(Path.GetFullPath(Path.GetTempPath()), StringComparison.OrdinalIgnoreCase))
                    Directory.Delete(directory, true);
            }
        }
    }
}
