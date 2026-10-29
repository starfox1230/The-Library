using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Runtime.InteropServices;
using System.Runtime.Serialization;
using System.Text;
using System.Threading;
using System.Windows.Automation;
using System.Windows.Forms;

namespace ReportExporter
{
    [DataContract]
    public sealed class Profile
    {
        [DataMember] public int Version = 7;
        [DataMember] public string TimingMode = "Automatic";
        [DataMember] public string OutputDirectory;
        [DataMember] public bool OpenWebsite = true;
        [DataMember] public bool OpenTextFile = true;
        [DataMember] public int ComparisonWaitMs = 3000;
        [DataMember] public bool KeyboardWorkflow = true;
        [DataMember] public bool AutoRestoreFocus = true;
        [DataMember] public int ClickX = 800;
        [DataMember] public int ClickY = 600;
        [DataMember] public int KeyDelayMs = 10;
        [DataMember] public int CaseDelayMs = 100;
        [DataMember] public string MainTitle = "PowerScribe 360 | Reporting";
        [DataMember] public string ComparisonTitle = "Compare Report Revisions";
        [DataMember] public Locator CaseList;
        [DataMember] public Locator Attending;
        [DataMember] public Locator Resident;
        [DataMember] public Locator Close;
        [DataMember] public int TimeoutMs = 10000;
        [DataMember] public int PollMs = 5;
        [DataMember] public int StableMs = 50;
        [DataMember] public bool ClipboardOnly;
        [DataMember] public bool FindingsOnly;
        [OnDeserializing]
        private void Defaults(StreamingContext context)
        {
            Version = 0; KeyboardWorkflow = true; AutoRestoreFocus = true; ClickX = 800; ClickY = 600;
            KeyDelayMs = 25; CaseDelayMs = 100;
            ComparisonWaitMs = 3000;
            MainTitle = "PowerScribe 360 | Reporting"; ComparisonTitle = "Compare Report Revisions";
            TimeoutMs = 10000; PollMs = 10; StableMs = 50;
            FindingsOnly = false;
            TimingMode = "Automatic"; OutputDirectory = null; OpenWebsite = true; OpenTextFile = true;
        }
        public void Validate()
        {
            if (TimingMode != "Automatic" && TimingMode != "Fast" && TimingMode != "Conservative" && TimingMode != "Custom")
                throw new InvalidOperationException("Choose Automatic, Fast, Conservative, or Custom speed in Options.");
            if (ComparisonWaitMs < 250 || ComparisonWaitMs > 60000 || TimeoutMs < 250 || TimeoutMs > 60000 || PollMs < 1 || PollMs > 100 || StableMs < 0 || StableMs > 2000)
                throw new InvalidOperationException("Invalid wait settings in the saved profile.");
            if (KeyboardWorkflow)
            {
                if (ClickX < 0 || ClickY < 0 || ClickX > 10000 || ClickY > 10000 || KeyDelayMs < 0 || KeyDelayMs > 500 || CaseDelayMs < 0 || CaseDelayMs > 3000)
                    throw new InvalidOperationException("Invalid keyboard workflow position or timing.");
                return;
            }
            var missing = new List<string>();
            if (CaseList == null) missing.Add("case list");
            if (Attending == null) missing.Add("attending report");
            if (Resident == null) missing.Add("resident report");
            if (Close == null) missing.Add("OK button");
            if (missing.Count > 0)
                throw new InvalidOperationException("Setup is incomplete. Still needed: " + String.Join(", ", missing.ToArray()) +
                    ".\r\n\r\nClick each matching Capture button, point at that control in PowerScribe, and press F8. The Captured line must show four checkmarks before exporting.");
            if (Attending.SameTarget(Resident))
                throw new InvalidOperationException("Attending and resident must be different report panes.");
        }
    }

    [DataContract]
    public sealed class Locator
    {
        [DataMember] public string AutomationId;
        [DataMember] public string ClassName;
        [DataMember] public int TypeId;
        [DataMember] public int MatchCount;
        [DataMember] public double X;
        [DataMember] public double Y;

        private Condition Condition()
        {
            return new AndCondition(
                new PropertyCondition(AutomationElement.AutomationIdProperty, AutomationId),
                new PropertyCondition(AutomationElement.ClassNameProperty, ClassName),
                new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.LookupById(TypeId)));
        }

        public static Locator Capture(AutomationElement root, AutomationElement target)
        {
            var state = target.Current;
            var box = state.BoundingRectangle;
            var rootBox = root.Current.BoundingRectangle;
            if (box.IsEmpty || rootBox.IsEmpty || rootBox.Width <= 0 || rootBox.Height <= 0)
                throw new InvalidOperationException("The control has no visible rectangle.");
            Locator result = new Locator {
                AutomationId = state.AutomationId, ClassName = state.ClassName, TypeId = state.ControlType.Id,
                X = (box.Left + box.Width / 2 - rootBox.Left) / rootBox.Width,
                Y = (box.Top + box.Height / 2 - rootBox.Top) / rootBox.Height
            };
            result.MatchCount = root.FindAll(TreeScope.Descendants, result.Condition()).Count;
            if (!Automation.Compare(result.Find(root), target))
                throw new InvalidOperationException("This control cannot be identified unambiguously. Try pointing at the middle of the pane.");
            return result;
        }

        public bool SameTarget(Locator other)
        {
            return AutomationId == other.AutomationId && ClassName == other.ClassName && TypeId == other.TypeId &&
                Math.Abs(X - other.X) < 0.02 && Math.Abs(Y - other.Y) < 0.02;
        }

        public AutomationElement Find(AutomationElement root)
        {
            var matches = root.FindAll(TreeScope.Descendants, Condition());
            if (matches.Count != MatchCount || matches.Count == 0)
                throw new InvalidOperationException("The captured control layout changed. Capture the controls again.");
            if (matches.Count == 1) return matches[0];
            var box = root.Current.BoundingRectangle;
            if (box.Width <= 0 || box.Height <= 0) throw new InvalidOperationException("Window is not visible.");
            AutomationElement nearest = null;
            double best = Double.MaxValue, second = Double.MaxValue;
            foreach (AutomationElement candidate in matches)
            {
                var rect = candidate.Current.BoundingRectangle;
                if (rect.IsEmpty || candidate.Current.IsOffscreen) continue;
                double dx = (rect.Left + rect.Width / 2 - box.Left) / box.Width - X;
                double dy = (rect.Top + rect.Height / 2 - box.Top) / box.Height - Y;
                double distance = Math.Sqrt(dx * dx + dy * dy);
                if (distance < best) { second = best; best = distance; nearest = candidate; }
                else if (distance < second) second = distance;
            }
            if (nearest == null || best > 0.12 || second - best < 0.05)
                throw new InvalidOperationException("Report panes moved or cannot be distinguished. Capture them again.");
            return nearest;
        }
    }

    public sealed class WindowsSession : IReportSession
    {
        public bool CanVerifySelectedRow { get { return true; } }
        private readonly Profile profile;
        private readonly IntPtr main;
        private IntPtr comparison;
        private AutomationElement dialog;
        private AutomationElement list;
        private readonly uint processId;
        private readonly Action<string> progress;

        public WindowsSession(Profile settings, Action<string> reportProgress = null)
        {
            progress = reportProgress ?? (message => {});
            progress("Finding the PowerScribe reporting window...");
            settings.Validate();
            profile = settings;
            main = Native.UniqueWindow(profile.MainTitle, 0);
            if (main == IntPtr.Zero) throw new InvalidOperationException("PowerScribe reporting window not found.");
            Native.GetWindowThreadProcessId(main, out processId);
            if (Native.UniqueWindow(profile.ComparisonTitle, processId) != IntPtr.Zero)
                throw new InvalidOperationException("Close the comparison window, select the first case, then start.");
            progress("PowerScribe found; locating the captured case list...");
            list = profile.CaseList.Find(AutomationElement.FromHandle(main));
            progress("Activating PowerScribe...");
            if (!Native.SetForegroundWindow(main))
                throw new InvalidOperationException("Windows would not activate PowerScribe. Bring it forward and try again.");
        }

        private void CheckForeground(IntPtr expected, CancellationToken token)
        {
            token.ThrowIfCancellationRequested();
            if (Native.GetForegroundWindow() != expected)
                throw new InvalidOperationException("PowerScribe lost focus. Export stopped before sending more input.");
        }

        private void Wait(Func<bool> predicate, CancellationToken token, string reason)
        {
            ReadyWait.Until(predicate, profile.TimeoutMs, profile.PollMs, token, reason);
        }

        public string SelectedCase()
        {
            object pattern;
            if (!list.TryGetCurrentPattern(SelectionPattern.Pattern, out pattern))
                throw new InvalidOperationException("PowerScribe does not expose the captured case list selection. Batch navigation cannot be verified.");
            var selected = ((SelectionPattern)pattern).Current.GetSelection();
            if (selected.Length != 1) throw new InvalidOperationException("Select exactly one case in the captured list.");
            // Runtime IDs identify a UI row without putting patient names or report text in logs.
            return String.Join("/", selected[0].GetRuntimeId().Select(i => i.ToString()).ToArray());
        }

        public void OpenComparison(CancellationToken token)
        {
            progress("Waiting for PowerScribe to be the active window...");
            Wait(() => Native.GetForegroundWindow() == main, token, "PowerScribe did not regain focus.");
            CheckForeground(main, token);
            progress("Opening Tools > Compare Report Revisions...");
            Native.Chord(0x12, 0x54); // Alt+T
            CheckForeground(main, token);
            Native.Key(0x49); // I; same Tools > Compare Report Revisions route as the AHK.
            progress("Waiting for the comparison window to appear...");
            Wait(() => {
                token.ThrowIfCancellationRequested();
                IntPtr foreground = Native.GetForegroundWindow();
                comparison = Native.UniqueWindow(profile.ComparisonTitle, processId);
                if (foreground != main && (comparison == IntPtr.Zero || foreground != comparison))
                    throw new InvalidOperationException("Another window took focus while opening the comparison.");
                return comparison != IntPtr.Zero && Native.IsWindowVisible(comparison) && Native.IsWindowEnabled(comparison) && foreground == comparison;
            }, token, "Comparison window did not become ready. This case was not skipped.");
            progress("Comparison window found; connecting to its controls...");
            dialog = AutomationElement.FromHandle(comparison);
        }

        private static bool Usable(AutomationElement element)
        {
            var state = element.Current;
            return state.IsEnabled && !state.IsOffscreen && !state.BoundingRectangle.IsEmpty;
        }

        private static string DirectText(AutomationElement element)
        {
            object pattern;
            if (element.TryGetCurrentPattern(TextPattern.Pattern, out pattern))
                return ((TextPattern)pattern).DocumentRange.GetText(-1);
            if (element.TryGetCurrentPattern(ValuePattern.Pattern, out pattern))
                return ((ValuePattern)pattern).Current.Value;
            return null;
        }

        public ReportPair ReadReports(CancellationToken token)
        {
            progress("Finding the captured attending and resident panes...");
            AutomationElement attending = null, resident = null;
            Wait(() => {
                CheckForeground(comparison, token);
                // Discover once the provider has built the dialog's controls.
                try { attending = profile.Attending.Find(dialog); resident = profile.Resident.Find(dialog); }
                catch (InvalidOperationException) { return false; }
                return Usable(attending) && Usable(resident);
            }, token, "The captured report panes did not become available.");
            if (Automation.Compare(attending, resident)) throw new InvalidOperationException("Report panes resolved to the same control.");
            if (!profile.ClipboardOnly)
            {
                progress("Reading attending report directly...");
                string a = DirectText(attending);
                progress("Reading resident report directly...");
                string r = DirectText(resident);
                if (a != null && r != null)
                {
                    Stopwatch stable = Stopwatch.StartNew();
                    ReportPair latest = new ReportPair { Attending = a, Resident = r, Method = "direct" };
                    progress("Waiting for both direct-read reports to contain Findings, Impression, or Conclusion and settle...");
                    Wait(() => {
                        CheckForeground(comparison, token);
                        string nextA = DirectText(attending), nextR = DirectText(resident);
                        if (nextA != latest.Attending || nextR != latest.Resident)
                        {
                            latest.Attending = nextA; latest.Resident = nextR; stable.Restart();
                        }
                        return ReportText.ExtractBody(nextA) != null && ReportText.ExtractBody(nextR) != null &&
                            stable.ElapsedMilliseconds >= profile.StableMs;
                    }, token, "Both reports did not finish loading with a Findings, Impression, or Conclusion section.");
                    return latest;
                }
            }
            progress("Copying attending report to the clipboard...");
            string copiedAttending = Copy(attending, token);
            progress("Copying resident report to the clipboard...");
            string copiedResident = Copy(resident, token);
            return new ReportPair { Attending = copiedAttending, Resident = copiedResident, Method = "clipboard" };
        }

        private string Copy(AutomationElement pane, CancellationToken token)
        {
            CheckForeground(comparison, token);
            if (!pane.Current.IsKeyboardFocusable) throw new InvalidOperationException("Report pane cannot receive keyboard focus.");
            pane.SetFocus();
            Wait(() => { CheckForeground(comparison, token); return pane.Current.HasKeyboardFocus; }, token, "Report pane did not receive focus.");
            bool cleared = false;
            Wait(() => {
                CheckForeground(comparison, token);
                try { Clipboard.Clear(); cleared = true; return true; }
                catch (ExternalException) { return false; }
            }, token, "Clipboard is locked by another application.");
            if (!cleared) throw new InvalidOperationException("Could not clear stale clipboard data.");
            uint before = Native.GetClipboardSequenceNumber();
            Native.Chord(0x11, 0x41); // Ctrl+A
            CheckForeground(comparison, token);
            Native.Chord(0x11, 0x43); // Ctrl+C
            string text = null;
            Wait(() => {
                CheckForeground(comparison, token);
                if (!pane.Current.HasKeyboardFocus) throw new InvalidOperationException("Focus moved away from the report during copying.");
                // Request text before testing the sequence so delayed rendering can complete.
                if (!Win32Desktop.ReadText(out text)) return false;
                CheckForeground(comparison, token);
                if (Native.GetClipboardSequenceNumber() == before) return false;
                uint clipboardProcess;
                IntPtr owner = Native.GetClipboardOwner();
                if (owner != IntPtr.Zero)
                {
                    Native.GetWindowThreadProcessId(owner, out clipboardProcess);
                    if (clipboardProcess != processId) return false;
                }
                return ReportText.ExtractBody(text) != null;
            }, token, "No fresh report with Findings, Impression, or Conclusion was copied. Export stopped to avoid stale data.");
            return text;
        }

        public void CloseComparison(CancellationToken token)
        {
            progress("Invoking the captured OK button...");
            CheckForeground(comparison, token);
            object invoke;
            AutomationElement close = profile.Close.Find(dialog);
            if (!close.TryGetCurrentPattern(InvokePattern.Pattern, out invoke))
                throw new InvalidOperationException("The captured comparison close button cannot be invoked.");
            ((InvokePattern)invoke).Invoke();
            progress("Waiting for the comparison to close...");
            Wait(() => {
                IntPtr fg = Native.GetForegroundWindow();
                if (fg != main && fg != comparison)
                    throw new InvalidOperationException("Another window took focus while closing the comparison.");
                return (!Native.IsWindow(comparison) || !Native.IsWindowVisible(comparison)) &&
                    Native.IsWindowEnabled(main) && fg == main;
            }, token, "Comparison window did not close. No next-case input was sent.");
            comparison = IntPtr.Zero;
        }

        public void Advance(string previousCase, CancellationToken token)
        {
            progress("Returning keyboard focus to the selected case...");
            CheckForeground(main, token);
            object selection;
            if (!list.TryGetCurrentPattern(SelectionPattern.Pattern, out selection))
                throw new InvalidOperationException("Case selection is unavailable.");
            var selected = ((SelectionPattern)selection).Current.GetSelection();
            if (selected.Length != 1 || SelectedCase() != previousCase)
                throw new InvalidOperationException("The selected case changed outside the exporter.");
            selected[0].SetFocus();
            Wait(() => {
                CheckForeground(main, token);
                return selected[0].Current.HasKeyboardFocus || list.Current.HasKeyboardFocus;
            }, token, "The selected case could not receive focus.");
            CheckForeground(main, token);
            Native.Key(0x28); // Down once; never repeat on a timeout.
            progress("Down sent once; waiting for a different selected row...");
            Wait(() => {
                CheckForeground(main, token);
                return list.Current.IsEnabled && SelectedCase() != previousCase;
            }, token, "The selected case did not change. At the end of the list, or PowerScribe is still busy.");
        }

        public static AutomationElement CaptureTarget(string role, string expected, out AutomationElement root)
        {
            Native.Point point;
            Native.GetCursorPos(out point);
            AutomationElement target = AutomationElement.FromPoint(new System.Windows.Point(point.X, point.Y));
            for (int depth = 0; target != null && depth < 15; depth++)
            {
                object pattern;
                bool suitable = role == "CaseList" ? target.TryGetCurrentPattern(SelectionPattern.Pattern, out pattern) :
                    role == "Close" ? target.TryGetCurrentPattern(InvokePattern.Pattern, out pattern) :
                    (target.Current.ControlType == ControlType.Edit || target.Current.ControlType == ControlType.Document) &&
                    (target.TryGetCurrentPattern(TextPattern.Pattern, out pattern) || target.TryGetCurrentPattern(ValuePattern.Pattern, out pattern) || target.Current.IsKeyboardFocusable);
                if (suitable)
                {
                    AutomationElement ancestor = target;
                    IntPtr hwnd = IntPtr.Zero;
                    while (ancestor != null && hwnd == IntPtr.Zero)
                    {
                        hwnd = new IntPtr(ancestor.Current.NativeWindowHandle);
                        ancestor = TreeWalker.ControlViewWalker.GetParent(ancestor);
                    }
                    if (hwnd == IntPtr.Zero) break;
                    hwnd = Native.GetAncestor(hwnd, 2);
                    string title = Native.Title(hwnd);
                    if (title != expected) throw new InvalidOperationException("Point inside " + expected + ". Captured window: " + title);
                    root = AutomationElement.FromHandle(hwnd);
                    return target;
                }
                target = TreeWalker.ControlViewWalker.GetParent(target);
            }
            throw new InvalidOperationException("This control does not expose the accessibility pattern needed for " + role + ".");
        }
    }

    internal static class Native
    {
        [StructLayout(LayoutKind.Sequential)] public struct Point { public int X, Y; }
        [StructLayout(LayoutKind.Sequential)] public struct Rect { public int Left, Top, Right, Bottom; }
        [StructLayout(LayoutKind.Sequential)] private struct Input { public uint Type; public InputUnion Data; }
        [StructLayout(LayoutKind.Explicit)] private struct InputUnion
        {
            [FieldOffset(0)] public Keyboard Keyboard;
            [FieldOffset(0)] public Mouse Mouse;
        }
        [StructLayout(LayoutKind.Sequential)] private struct Keyboard
        { public ushort Vk, Scan; public uint Flags, Time; public UIntPtr Extra; }
        [StructLayout(LayoutKind.Sequential)] private struct Mouse
        { public int X, Y; public uint Data, Flags, Time; public UIntPtr Extra; }
        private delegate bool EnumCallback(IntPtr hwnd, IntPtr state);
        [DllImport("user32.dll")] private static extern bool EnumWindows(EnumCallback callback, IntPtr state);
        [DllImport("user32.dll")] private static extern bool EnumThreadWindows(uint thread, EnumCallback callback, IntPtr state);
        [DllImport("user32.dll", EntryPoint = "GetWindowLongW", SetLastError = true)] private static extern int GetWindowLong32(IntPtr window, int index);
        [DllImport("user32.dll", EntryPoint = "GetWindowLongPtrW", SetLastError = true)] private static extern IntPtr GetWindowLong64(IntPtr window, int index);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetWindowText(IntPtr hwnd, StringBuilder text, int length);
        [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr hwnd);
        [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hwnd);
        [DllImport("user32.dll")] public static extern bool IsWindowEnabled(IntPtr hwnd);
        [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
        [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hwnd);
        [DllImport("user32.dll")] private static extern bool IsIconic(IntPtr hwnd);
        [DllImport("user32.dll")] private static extern bool ShowWindowAsync(IntPtr hwnd, int command);
        [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);
        [DllImport("user32.dll")] public static extern IntPtr GetAncestor(IntPtr hwnd, uint flags);
        [DllImport("user32.dll")] public static extern bool GetCursorPos(out Point point);
        [DllImport("user32.dll")] public static extern IntPtr WindowFromPoint(Point point);
        [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hwnd, out Rect rect);
        [DllImport("user32.dll")] private static extern bool SetCursorPos(int x, int y);
        [DllImport("user32.dll")] public static extern uint GetClipboardSequenceNumber();
        [DllImport("user32.dll")] public static extern IntPtr GetClipboardOwner();
        [DllImport("user32.dll", SetLastError = true)] private static extern uint SendInput(uint count, Input[] inputs, int size);
        [DllImport("user32.dll")] public static extern bool RegisterHotKey(IntPtr hwnd, int id, uint modifiers, uint key);
        [DllImport("user32.dll")] public static extern bool UnregisterHotKey(IntPtr hwnd, int id);
        [DllImport("user32.dll")] private static extern bool GetGUIThreadInfo(uint thread, ref GuiThreadInfo info);
        [DllImport("user32.dll")] private static extern bool IsChild(IntPtr parent, IntPtr child);
        [DllImport("user32.dll")] private static extern IntPtr SetFocus(IntPtr window);
        [DllImport("user32.dll")] private static extern bool AttachThreadInput(uint first, uint second, bool attach);
        [DllImport("kernel32.dll")] private static extern uint GetCurrentThreadId();
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetClassName(IntPtr window, StringBuilder name, int size);
        [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern IntPtr SendMessageTimeout(IntPtr window, uint message, IntPtr wparam, IntPtr lparam, uint flags, uint timeout, out UIntPtr result);
        [StructLayout(LayoutKind.Sequential)]
        private struct GuiThreadInfo
        {
            public uint Size, Flags;
            public IntPtr Active, Focus, Capture, MenuOwner, MoveSize, Caret;
            public Rect CaretRectangle;
        }

        public static IntPtr FocusedChild(IntPtr parent)
        {
            uint pid; uint thread = GetWindowThreadProcessId(parent, out pid);
            var info = new GuiThreadInfo { Size = (uint)Marshal.SizeOf(typeof(GuiThreadInfo)) };
            if (thread == 0 || !GetGUIThreadInfo(thread, ref info) || !IsChild(parent, info.Focus)) return IntPtr.Zero;
            return info.Focus;
        }
        public static string WindowClass(IntPtr window)
        { var name = new StringBuilder(256); GetClassName(window, name, name.Capacity); return name.ToString(); }
        public static IntPtr NavigationFocus(IntPtr parent, Action<string> progress)
        {
            uint pid; uint thread = GetWindowThreadProcessId(parent, out pid);
            var info = new GuiThreadInfo { Size = (uint)Marshal.SizeOf(typeof(GuiThreadInfo)) };
            if (thread == 0 || !GetGUIThreadInfo(thread, ref info))
            { progress("Worklist focus rejected: Windows GUI-thread focus query failed."); return IntPtr.Zero; }
            if (info.Focus == IntPtr.Zero)
            { progress("Worklist focus rejected: Windows reported no focused control."); return IntPtr.Zero; }
            if (info.Focus == parent)
            { progress("Worklist focus rejected: only the main window has focus; no separate child control."); return IntPtr.Zero; }
            if (!IsChild(parent, info.Focus))
            { progress("Worklist focus rejected: the focused control is outside the reporting window."); return IntPtr.Zero; }
            if (IsTextEditor(info.Focus))
            { progress("Worklist focus rejected: an editor control has focus (class: " + WindowClass(info.Focus) + ")."); return IntPtr.Zero; }
            if (!IsNavigationChild(parent, info.Focus))
            { progress("Worklist focus rejected: child control is hidden, disabled, invalid, or belongs to another process."); return IntPtr.Zero; }
            progress("Worklist focus accepted (control class: " + WindowClass(info.Focus) + ").");
            return info.Focus;
        }
        public static bool IsNavigationChild(IntPtr parent, IntPtr child)
        {
            uint parentPid, childPid;
            GetWindowThreadProcessId(parent, out parentPid); GetWindowThreadProcessId(child, out childPid);
            return parentPid != 0 && parentPid == childPid && IsWindow(child) && IsChild(parent, child) &&
                IsWindowEnabled(child) && IsWindowVisible(child) && !IsTextEditor(child);
        }
        public static bool MenuActive(IntPtr parent)
        {
            uint pid; uint thread = GetWindowThreadProcessId(parent, out pid);
            var info = new GuiThreadInfo { Size = (uint)Marshal.SizeOf(typeof(GuiThreadInfo)) };
            if (thread == 0 || !GetGUIThreadInfo(thread, ref info))
                throw new InvalidOperationException("Could not read PowerScribe's menu state. Stopped before navigation.");
            // GUI_INMENUMODE | GUI_SYSTEMMENUMODE | GUI_POPUPMENUMODE.
            return (info.Flags & 0x1C) != 0;
        }
        public static IntPtr[] MenuPopupWindows(IntPtr parent)
        {
            uint pid; uint thread = GetWindowThreadProcessId(parent, out pid);
            if (thread == 0) throw new InvalidOperationException("PowerScribe's UI thread is no longer available.");
            var popups = new List<IntPtr>();
            bool enumerated = EnumThreadWindows(thread, (window, state) => {
                if (window == parent || !IsWindowVisible(window)) return true;
                var name = new StringBuilder(256); GetClassName(window, name, name.Capacity);
                string className = name.ToString();
                // These decorative windows do not intercept worklist navigation.
                if (className.Equals("tooltips_class32", StringComparison.OrdinalIgnoreCase) ||
                    className.Equals("SysShadow", StringComparison.OrdinalIgnoreCase)) return true;
                long style = IntPtr.Size == 8 ? GetWindowLong64(window, -16).ToInt64() : GetWindowLong32(window, -16);
                // Managed ToolStrip dropdowns are captionless WS_POPUP windows and
                // can exist without GUI_INMENUMODE. Treat an unknown new popup
                // conservatively: do not send Down through it.
                if (className == "#32768" || ((style & 0x80000000L) != 0 && (style & 0x00C00000L) == 0))
                    popups.Add(window);
                return true;
            }, IntPtr.Zero);
            if (!enumerated) throw new InvalidOperationException("Could not inspect PowerScribe popup windows. Stopped before navigation.");
            return popups.ToArray();
        }
        private static int ReadIndex(IntPtr child, uint message, int start, int flags)
        {
            UIntPtr result;
            if (SendMessageTimeout(child, message, new IntPtr(start), new IntPtr(flags), 2, 250, out result) == IntPtr.Zero)
                throw new InvalidOperationException("Worklist row-index query failed or timed out. No extra Down was sent.");
            return unchecked((int)result.ToUInt64());
        }
        public static string SelectedRowIndex(IntPtr child)
        {
            var name = new StringBuilder(256); GetClassName(child, name, name.Capacity);
            string className = name.ToString();
            // Only these native controls support these exact read-only messages. Do not
            // guess custom-grid messages or read patient text to establish case identity.
            if (className.Equals("SysListView32", StringComparison.OrdinalIgnoreCase) || className.StartsWith("WindowsForms10.SysListView32.", StringComparison.OrdinalIgnoreCase))
            {
                int index = ReadIndex(child, 0x100C, -1, 2); // LVM_GETNEXTITEM, LVNI_SELECTED.
                if (index < 0 || ReadIndex(child, 0x100C, index, 2) >= 0)
                    throw new InvalidOperationException("Select exactly one worklist row before navigation.");
                return "listview:" + index;
            }
            if (className == "ListBox" || className.StartsWith("WindowsForms10.LISTBOX.", StringComparison.OrdinalIgnoreCase))
            {
                int index = ReadIndex(child, 0x188, 0, 0); // LB_GETCURSEL.
                if (index < 0) throw new InvalidOperationException("No focused worklist row index was available.");
                int count = ReadIndex(child, 0x190, 0, 0); // LB_GETSELCOUNT; -1 for a single-select list.
                if (count >= 0 && (count != 1 || ReadIndex(child, 0x187, index, 0) != 1))
                    throw new InvalidOperationException("Select exactly one worklist row before navigation.");
                return "listbox:" + index;
            }
            return null;
        }
        public static bool IsTextEditor(IntPtr window)
        {
            return IsTextEditorClass(WindowClass(window));
        }
        internal static bool IsTextEditorClass(string name)
        {
            // Native and WinForms edit classes; an incidental substring such as
            // CreditGrid is not an editor. Retain common custom editor safeguards.
            return name.Equals("Edit", StringComparison.OrdinalIgnoreCase) ||
                name.StartsWith("RichEdit", StringComparison.OrdinalIgnoreCase) ||
                name.StartsWith("WindowsForms10.EDIT.", StringComparison.OrdinalIgnoreCase) ||
                name.StartsWith("WindowsForms10.RichEdit", StringComparison.OrdinalIgnoreCase) ||
                name.IndexOf("TextBox", StringComparison.OrdinalIgnoreCase) >= 0 ||
                name.IndexOf("Editor", StringComparison.OrdinalIgnoreCase) >= 0 ||
                name.Equals("Scintilla", StringComparison.OrdinalIgnoreCase);
        }
        public static bool RestoreChildFocus(IntPtr parent, IntPtr child)
        {
            if (GetForegroundWindow() != parent || !IsWindowEnabled(parent) || !IsNavigationChild(parent, child)) return false;
            if (FocusedChild(parent) == child) return true;
            uint pid; uint other = GetWindowThreadProcessId(child, out pid), current = GetCurrentThreadId();
            if (other == 0 || (other != current && !AttachThreadInput(current, other, true))) return false;
            try { SetFocus(child); }
            finally { if (other != current) AttachThreadInput(current, other, false); }
            return GetForegroundWindow() == parent && FocusedChild(parent) == child;
        }

        public static string Title(IntPtr hwnd)
        { var buffer = new StringBuilder(512); GetWindowText(hwnd, buffer, buffer.Capacity); return buffer.ToString(); }
        public static bool ActivateWindow(IntPtr hwnd)
        {
            if (!IsWindow(hwnd)) return false;
            if (IsIconic(hwnd)) ShowWindowAsync(hwnd, 9); // Restore only the known PowerScribe window.
            SetForegroundWindow(hwnd);
            return GetForegroundWindow() == hwnd;
        }
        public static IntPtr UniqueWindow(string title, uint process, bool prefix = false)
        {
            var matches = new List<IntPtr>();
            EnumWindows((hwnd, state) => {
                uint pid; GetWindowThreadProcessId(hwnd, out pid);
                if ((prefix ? Title(hwnd).StartsWith(title, StringComparison.Ordinal) : Title(hwnd) == title) &&
                    IsWindowVisible(hwnd) && (process == 0 || pid == process)) matches.Add(hwnd);
                return true;
            }, IntPtr.Zero);
            if (matches.Count > 1) throw new InvalidOperationException("Multiple matching PowerScribe windows are open.");
            return matches.Count == 1 ? matches[0] : IntPtr.Zero;
        }
        private static Input Event(ushort key, bool up)
        { return new Input { Type = 1, Data = new InputUnion { Keyboard = new Keyboard { Vk = key,
            Flags = (up ? 2u : 0u) | (key >= 0x21 && key <= 0x2E ? 1u : 0u) } } }; }
        private static void Send(Input[] inputs)
        {
            if (SendInput((uint)inputs.Length, inputs, Marshal.SizeOf(typeof(Input))) != inputs.Length)
                throw new InvalidOperationException("Windows blocked input. Run at the same privilege level as PowerScribe.");
        }
        public static void Key(ushort key) { Send(new Input[] { Event(key, false), Event(key, true) }); }
        public static void Chord(ushort modifier, ushort key)
        { Send(new Input[] { Event(modifier, false), Event(key, false), Event(key, true), Event(modifier, true) }); }
        public static void Click(IntPtr hwnd, int x, int y)
        {
            Rect rect;
            if (!GetWindowRect(hwnd, out rect) || x < 0 || y < 0 || x >= rect.Right - rect.Left || y >= rect.Bottom - rect.Top)
                throw new InvalidOperationException("The report click position is outside the comparison window. Use Capture report click to set the position for this window size.");
            if (!SetCursorPos(rect.Left + x, rect.Top + y)) throw new InvalidOperationException("Windows blocked moving the pointer to the report pane.");
            Send(new Input[] {
                new Input { Type = 0, Data = new InputUnion { Mouse = new Mouse { Flags = 2 } } },
                new Input { Type = 0, Data = new InputUnion { Mouse = new Mouse { Flags = 4 } } }
            });
        }
    }
}
