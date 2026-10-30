using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Globalization;
using System.Reflection;
using System.Runtime.Serialization.Json;
using System.Threading;
using System.Windows.Forms;

[assembly: AssemblyVersion("0.17.0.0")]
[assembly: AssemblyFileVersion("0.17.0.0")]

namespace ReportExporter
{
    public static class Program
    {
        [STAThread]
        public static void Main(string[] args)
        {
            if (args.Length == 2 && (args[0] == "--preview" || args[0] == "--preview-options" || args[0] == "--preview-copied" || args[0] == "--preview-progress"))
            {
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                using (Form form = args[0] == "--preview-progress" ? (Form)new ProgressOverlay("Numpad *") : new ExportForm(true))
                {
                    if (args[0] == "--preview-options") ((ExportForm)form).SetOptionsVisible(true);
                    if (args[0] == "--preview-copied")
                    {
                        var exporter = (ExportForm)form;
                        exporter.SetCopiedText("Case 1\r\nAttending Report:\r\nFINDINGS: Synthetic attending report for preview.\r\n\r\nResident Report:\r\nFINDINGS: Synthetic resident report for preview.\r\n", "Preview only - synthetic reports");
                        exporter.SetCopiedTextVisible(true);
                    }
                    var progress = form as ProgressOverlay;
                    if (progress != null) progress.SetPhase("Waiting for fresh attending report text...", 2, 10);
                    form.StartPosition = FormStartPosition.Manual; form.Location = new Point(-20000, -20000);
                    form.ShowInTaskbar = false; form.Show(); Application.DoEvents();
                    CreateHandles(form);
                    form.PerformLayout();
                    using (var bitmap = new Bitmap(form.Width, form.Height))
                    {
                        form.DrawToBitmap(bitmap, new Rectangle(0, 0, bitmap.Width, bitmap.Height));
                        bitmap.Save(args[1], System.Drawing.Imaging.ImageFormat.Png);
                    }
                }
                return;
            }
            bool created;
            using (Mutex instance = new Mutex(true, "Local\\PowerScribeReportExporter", out created))
            {
                if (!created) { MessageBox.Show("The exporter is already open."); return; }
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                Application.Run(new ExportForm());
            }
        }

        private static void CreateHandles(Control control)
        {
            IntPtr handle = control.Handle;
            foreach (Control child in control.Controls) CreateHandles(child);
            control.PerformLayout();
        }
    }

    public sealed class ExportForm : Form
    {
        private Profile profile = new Profile();
        private readonly string settingsDirectory = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "PowerScribeReportExporter");
        private readonly TextBox first = new TextBox { Text = "1", Width = 76, Font = new Font("Segoe UI", 11), AccessibleName = "First case" };
        private readonly TextBox last = new TextBox { Text = "1", Width = 76, Font = new Font("Segoe UI", 11), AccessibleName = "Last case" };
        private readonly NumericUpDown timeout = Number(1, 60, 10);
        private readonly NumericUpDown comparisonWait = Number(1, 60, 3);
        private readonly NumericUpDown poll = Number(1, 100, 5);
        private readonly NumericUpDown stable = Number(0, 2000, 50);
        private readonly NumericUpDown clickX = Number(0, 10000, 800);
        private readonly NumericUpDown clickY = Number(0, 10000, 600);
        private readonly NumericUpDown keyPause = Number(0, 500, 10);
        private readonly NumericUpDown casePause = Number(0, 3000, 100);
        private readonly CheckBox keyboard = new CheckBox { Text = "Keyboard workflow — same sequence as the working AHK", AutoSize = true, Checked = true };
        private readonly CheckBox autoFocus = new CheckBox { Text = "Automatically return focus to PowerScribe and continue", AutoSize = true, Checked = true };
        private readonly CheckBox clipboard = new CheckBox { Text = "Use clipboard instead of direct text reads", AutoSize = true };
        private readonly CheckBox website = new CheckBox { Text = "Open Compare Revisions website after export", AutoSize = true, Checked = true };
        private readonly CheckBox findingsOnly = new CheckBox { Text = "Findings and below only (previous export format)", AutoSize = true, Checked = false };
        private readonly Label status = new Label { AutoSize = false, Width = 570, Height = 70, Text = "Select the first case row in PowerScribe.\nEnter the first and last case numbers below, then Go." };
        private readonly Label stopHint = new Label { AutoSize = true };
        private readonly Label captured = new Label { AutoSize = false, Width = 590, Height = 30 };
        private readonly Button start = new NightButton { Name = "Go", Text = "Go", Width = 108, Height = 36, Primary = true, Margin = new Padding(3, 1, 7, 1) };
        private readonly Button stop = new NightButton { Text = "Stop", Width = 76, Height = 36, Margin = new Padding(3, 1, 7, 1), AutoSize = false, Enabled = false };
        private FlowLayoutPanel body;
        private Panel feedback;
        private string captureRole;
        // Session-only native handles: never serialize them to controls.json.
        private IntPtr lockedWorklistMain, lockedWorklistChild;
        private CancellationTokenSource cancellation;
        private bool running;
        private bool captureHotkey, stopHotkey;
        private ProgressOverlay overlay;
        private FlowLayoutPanel keyboardSettings, accessibilitySettings;
        private FlowLayoutPanel optionsPanel, resultActions, customTiming;
        private readonly Button optionsButton = new NightButton { Name = "Options", Text = "Options", Width = 380, Height = 36, AutoSize = false, Disclosure = true };
        private readonly ComboBox speed = new NightComboBox { Name = "Speed", DropDownStyle = ComboBoxStyle.DropDownList, Width = 230 };
        private readonly TextBox outputFolder = new TextBox { Width = 390, ReadOnly = true };
        private readonly CheckBox openText = new CheckBox { Name = "OpenNotepad", Text = "Open the saved comparison file in Notepad", AutoSize = true, Checked = true };
        private readonly Button copiedToggle = new NightButton { Name = "CopiedTextToggle", Text = "Copied text", Width = 380, Height = 36, AutoSize = false, Disclosure = true, Visible = false };
        private readonly FlowLayoutPanel copiedPanel = new FlowLayoutPanel { Name = "CopiedTextPanel", AutoSize = true, Padding = new Padding(12), Width = 620, MinimumSize = new Size(620, 0), MaximumSize = new Size(620, 0), FlowDirection = FlowDirection.TopDown, WrapContents = false, Visible = false };
        private readonly TextBox copiedText = new TextBox { Name = "CopiedText", Width = 590, Height = 240, Font = new Font("Consolas", 10), Multiline = true, ReadOnly = true, ScrollBars = ScrollBars.Both, WordWrap = false, MaxLength = Int32.MaxValue };
        private readonly Label copiedSource = new Label { Name = "CopiedSource", AutoSize = true, MaximumSize = new Size(570, 0) };
        private readonly Button copyAgain = new NightButton { Name = "CopyAgain", Text = "Copy again", AutoSize = true };
        private readonly Label copyStatus = new Label { Name = "CopyStatus", AutoSize = true, MaximumSize = new Size(440, 0) };
        private bool copiedExpanded;
        internal Action<string> ClipboardWriter;
        private readonly TextBox details = new TextBox { Name = "RunDetails", Width = 570, Height = 180, Multiline = true, ReadOnly = true, ScrollBars = ScrollBars.Vertical, Visible = false };
        private readonly Button detailsButton = new NightButton { Text = "Details", AutoSize = true };
        private readonly Button openComparison = new NightButton { Text = "Open comparison file", AutoSize = true };
        private readonly Button resume = new NightButton { Text = "Prepare remaining cases", AutoSize = true, Visible = false };
        private readonly bool previewMode;
        private bool optionsExpanded;
        private string lastOutput;
        private int? resumeCase;
        private string stopShortcut = "Numpad *";

        private static NumericUpDown Number(int min, int max, int value)
        { return new NumericUpDown { Minimum = min, Maximum = max, Value = value, Width = 90 }; }

        public ExportForm() : this(false) { }
        public ExportForm(bool preview)
        {
            previewMode = preview;
            ClipboardWriter = preview ? (Action<string>)(text => { throw new InvalidOperationException("Preview does not use the clipboard."); }) : text => Clipboard.SetDataObject(text, true, 3, 100);
            Text = "PowerScribe Report Exporter v0.17";
            ClientSize = new Size(420, 300);
            MinimumSize = SizeFromClientSize(ClientSize);
            Font = new Font("Segoe UI", 10);
            DoubleBuffered = true;
            body = new FlowLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(20, 4, 20, 8), FlowDirection = FlowDirection.TopDown, WrapContents = false, AutoScroll = true };
            Controls.Add(body);
            feedback = new Panel { Dock = DockStyle.Top, Height = 52, Padding = new Padding(20, 4, 20, 4), BackColor = NightTheme.Canvas };
            status.Dock = DockStyle.Fill;
            status.Font = new Font("Segoe UI", 10);
            feedback.Controls.Add(status);
            Controls.Add(feedback);
            first.Name = "FirstCase"; last.Name = "LastCase";
            var range = Row("First case", first, "Last case", last);
            range.Name = "CaseRange"; range.Margin = new Padding(0, 0, 0, 8);
            body.Controls.Add(range);
            body.Controls.Add(new Label { Text = "Case numbers label the export.", AutoSize = true, MaximumSize = new Size(380, 0), Font = new Font("Segoe UI", 9), ForeColor = Color.DimGray, Margin = new Padding(0, 0, 0, 8) });
            optionsButton.FlatAppearance.BorderSize = 0;
            body.Controls.Add(optionsButton);
            optionsPanel = new FlowLayoutPanel { Name = "OptionsPanel", AutoSize = true, Padding = new Padding(12), Width = 620, MinimumSize = new Size(620, 0), MaximumSize = new Size(620, 0), FlowDirection = FlowDirection.TopDown, WrapContents = false, Visible = false };
            body.Controls.Add(optionsPanel);
            speed.Items.AddRange(new object[] { "Automatic - fast first", "Fast (fixed)", "Conservative (fixed)", "Custom timing" });
            speed.SelectedIndex = 0;
            optionsPanel.Controls.Add(Row("Speed", speed, "", new Label { AutoSize = true }));
            optionsPanel.Controls.Add(new Label { Text = "Automatic starts fast and adds input settling only when a copy needs retrying.\nWindow and clipboard waits finish as soon as their checks succeed.", AutoSize = true, MaximumSize = new Size(570, 0) });
            customTiming = new FlowLayoutPanel { AutoSize = true, FlowDirection = FlowDirection.TopDown, WrapContents = false, Visible = false };
            customTiming.Controls.Add(Row("Input pause (ms)", keyPause, "After Down (ms)", casePause));
            customTiming.Controls.Add(Row("Readiness poll (ms)", poll, "", new Label { AutoSize = true }));
            optionsPanel.Controls.Add(customTiming);
            optionsPanel.Controls.Add(keyboard);
            keyboardSettings = new FlowLayoutPanel { AutoSize = true, FlowDirection = FlowDirection.TopDown, WrapContents = false };
            keyboardSettings.Controls.Add(new Label { Text = "PowerScribe setup (only if needed)", AutoSize = true });
            var worklistButtons = new FlowLayoutPanel { AutoSize = true };
            var rememberWorklist = new NightButton { Text = "Remember worklist (F8)", AutoSize = true };
            rememberWorklist.Click += (sender, args) => {
                if (!captureHotkey) { ShowError("F8 is in use", "Close the other program using F8 and reopen this exporter."); return; }
                lockedWorklistMain = lockedWorklistChild = IntPtr.Zero;
                captureRole = "WorklistFocus";
                status.Text = "Click the FIRST CASE ROW in PowerScribe, then press F8 while PowerScribe is active. This remembers keyboard focus; no accessibility capture is used.";
            };
            var clearWorklist = new NightButton { Text = "Clear remembered worklist", AutoSize = true };
            clearWorklist.Click += (sender, args) => {
                lockedWorklistMain = lockedWorklistChild = IntPtr.Zero; captureRole = null;
                status.Text = "Remembered worklist cleared. The next export will detect focus automatically.";
            };
            worklistButtons.Controls.Add(rememberWorklist); worklistButtons.Controls.Add(clearWorklist);
            keyboardSettings.Controls.Add(worklistButtons);
            keyboardSettings.Controls.Add(Row("Report click X", clickX, "Y", clickY));
            var captureClick = new NightButton { Text = "Capture report click (optional)", AutoSize = true };
            captureClick.Click += (sender, args) => {
                if (!captureHotkey) { ShowError("F8 is in use", "Close the other program using F8 and reopen this exporter, or enter the X/Y position manually."); return; }
                captureRole = "KeyboardPoint";
                status.Text = "Open Compare Report Revisions manually. Point inside the ATTENDING REPORT BODY, then press F8. This stores a click position, not a screenshot.";
            };
            keyboardSettings.Controls.Add(captureClick);
            keyboardSettings.Controls.Add(autoFocus);
            keyboardSettings.Controls.Add(Row("Missing comparison wait (s)", comparisonWait, "", new Label { Text = "Then save placeholder / continue", AutoSize = true }));
            keyboardSettings.Controls.Add(new Label { Text = "Fast reduces input waits; use Conservative if keys are missed.\nAfter Down remains 100 ms because the selected row cannot be verified.", AutoSize = true });
            optionsPanel.Controls.Add(keyboardSettings);
            accessibilitySettings = new FlowLayoutPanel { AutoSize = true, FlowDirection = FlowDirection.TopDown, WrapContents = false };
            accessibilitySettings.Controls.Add(new Label { Text = "Optional accessibility mode requires four captures; it does not work\nwhen PowerScribe does not expose these controls. Point and press F8.", AutoSize = true });
            var captureButtons = new FlowLayoutPanel { AutoSize = true, MaximumSize = new Size(590, 100) };
            foreach (string role in new string[] { "CaseList", "Attending", "Resident", "Close" })
            {
                string current = role;
                var button = new NightButton { Text = role == "Close" ? "Capture OK button" : "Capture " + role, AutoSize = true };
                button.Click += (sender, args) => {
                    if (running) return;
                    if (!captureHotkey) { status.Text = "F8 is in use by another program. Close that program and reopen the exporter."; return; }
                    captureRole = current;
                    status.Text = "Point at " + current + " in PowerScribe, then press F8. For a report pane, point at its text area.";
                };
                captureButtons.Controls.Add(button);
            }
            accessibilitySettings.Controls.Add(captureButtons);
            accessibilitySettings.Controls.Add(captured);
            accessibilitySettings.Controls.Add(Row("Text settling (ms)", stable, "", new Label { AutoSize = true, Text = "Direct-read settling check" }));
            accessibilitySettings.Controls.Add(clipboard);
            optionsPanel.Controls.Add(accessibilitySettings);
            optionsPanel.Controls.Add(Row("Maximum wait (s)", timeout, "", new Label { AutoSize = true, Text = "Not a fixed delay" }));
            optionsPanel.Controls.Add(findingsOnly);
            optionsPanel.Controls.Add(website); optionsPanel.Controls.Add(openText);
            optionsPanel.Controls.Add(new Label { Text = "A backup file is always saved. Notepad only controls opening it.", AutoSize = true, MaximumSize = new Size(570, 0), ForeColor = Color.DimGray });
            outputFolder.Text = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "Report comparisons");
            var chooseFolder = new NightButton { Text = "Save folder...", AutoSize = true };
            chooseFolder.Click += (sender, args) => { using (var picker = new FolderBrowserDialog { Description = "Choose where reports are saved", SelectedPath = outputFolder.Text }) { if (picker.ShowDialog(this) == DialogResult.OK) outputFolder.Text = picker.SelectedPath; } };
            var folderRow = new FlowLayoutPanel { AutoSize = true }; folderRow.Controls.Add(outputFolder); folderRow.Controls.Add(chooseFolder); optionsPanel.Controls.Add(folderRow);
            stopHint.Text = "Stop with " + stopShortcut + ". Close the old Review Reports script\nso it does not run during this export.";
            optionsPanel.Controls.Add(stopHint);
            copiedToggle.FlatAppearance.BorderSize = 0;
            copiedToggle.Click += (sender, args) => SetCopiedTextVisible(!copiedExpanded);
            body.Controls.Add(copiedToggle); body.Controls.Add(copiedPanel);
            // Keep the completed export above setup, even when Options is open.
            body.Controls.SetChildIndex(copiedToggle, 2); body.Controls.SetChildIndex(copiedPanel, 3);
            copiedPanel.Controls.Add(copiedSource);
            copiedPanel.Controls.Add(copiedText);
            var copyRow = new FlowLayoutPanel { AutoSize = true, MaximumSize = new Size(570, 0) };
            copyRow.Controls.Add(copyAgain); copyRow.Controls.Add(copyStatus); copiedPanel.Controls.Add(copyRow);
            copyAgain.Click += (sender, args) => {
                try { ClipboardWriter(copiedText.Text); copyStatus.Text = "Copied. Ready to paste."; }
                catch (Exception) { copyStatus.Text = "Clipboard busy. Try Copy again, or select the text and Ctrl+C."; }
            };
            resultActions = new FlowLayoutPanel { Name = "ResultActions", AutoSize = true, MaximumSize = new Size(570, 0), Visible = false };
            var openFolder = new NightButton { Text = "Open save folder", AutoSize = true };
            openComparison.Click += (sender, args) => OpenComparisonFile();
            openFolder.Click += (sender, args) => { try { Process.Start(Path.GetDirectoryName(lastOutput)); } catch (Exception error) { ShowError("Folder did not open", error.Message); } };
            detailsButton.Click += (sender, args) => { details.Visible = !details.Visible; detailsButton.Text = details.Visible ? "Hide details" : "Details"; ResizeForContent(); };
            resume.Click += (sender, args) => { if (resumeCase.HasValue) { first.Text = resumeCase.Value.ToString(CultureInfo.InvariantCulture); status.Text = "Select case " + resumeCase.Value + " in PowerScribe, then Go. This button only sets the range here."; } };
            resultActions.Controls.Add(openComparison); resultActions.Controls.Add(openFolder); resultActions.Controls.Add(detailsButton); resultActions.Controls.Add(resume);
            body.Controls.Add(resultActions); body.Controls.Add(details);
            var footer = new Panel { Dock = DockStyle.Bottom, Height = 58, Padding = new Padding(20, 8, 20, 8), BackColor = NightTheme.Surface };
            var actionRow = new FlowLayoutPanel { Dock = DockStyle.Fill, FlowDirection = FlowDirection.RightToLeft, WrapContents = false, BackColor = NightTheme.Surface, Margin = new Padding(0) };
            actionRow.Controls.Add(start); actionRow.Controls.Add(stop); footer.Controls.Add(actionRow); Controls.Add(footer);
            var header = new Panel { Dock = DockStyle.Top, Height = 60, BackColor = NightTheme.Canvas, Padding = new Padding(20, 6, 20, 0) };
            var brand = new Label { Text = "COMPARE REVISIONS", Dock = DockStyle.Top, Height = 16, Font = new Font("Segoe UI", 8, FontStyle.Bold), ForeColor = Color.DimGray };
            var title = new Label { Text = "Report exporter", Dock = DockStyle.Fill, Font = new Font("Segoe UI", 18, FontStyle.Bold) };
            header.Controls.Add(title); header.Controls.Add(brand); Controls.Add(header);
            start.Click += (sender, args) => StartExport();
            stop.Click += (sender, args) => CancelExport();
            if (!previewMode) LoadProfile();
            RefreshCaptured();
            keyboard.CheckedChanged += (sender, args) => ApplyMode();
            ApplyMode();
            speed.SelectedIndexChanged += (sender, args) => { customTiming.Visible = speed.SelectedIndex == 3; ResizeForContent(); };
            customTiming.Visible = speed.SelectedIndex == 3;
            optionsButton.Click += (sender, args) => SetOptionsVisible(!optionsExpanded);
            AcceptButton = start;
            status.TextChanged += (sender, args) => ResizeForContent();
            NightTheme.Apply(this);
            copiedSource.ForeColor = NightTheme.Muted;
            optionsPanel.BackColor = copiedPanel.BackColor = NightTheme.Surface;
            FormClosing += (sender, args) => {
                if (running && cancellation != null && !cancellation.IsCancellationRequested)
                { CancelExport(); args.Cancel = true; status.Text = "Stopping... close again to exit immediately if PowerScribe's accessibility provider is stuck."; }
            };
        }

        private void ApplyMode()
        {
            profile.KeyboardWorkflow = keyboard.Checked;
            keyboardSettings.Visible = keyboard.Checked;
            accessibilitySettings.Visible = !keyboard.Checked;
            captureRole = null;
            status.Text = keyboard.Checked ? "Select the first case row in PowerScribe.\nEnter the first and last case numbers below, then Go." :
                "Accessibility mode needs four saved captures in Options before Go.";
        }

        public void SetOptionsVisible(bool visible)
        {
            optionsExpanded = visible; optionsPanel.Visible = visible; ((NightButton)optionsButton).Expanded = visible; optionsButton.Invalidate();
            ResizeForContent();
        }
        internal void SetCopiedText(string text, string source)
        {
            // Keep the previous completed export if this run produced no usable text.
            if (String.IsNullOrWhiteSpace(text)) return;
            copiedText.Text = text; copiedSource.Text = source;
            copyStatus.Text = ""; copiedToggle.Visible = true;
            SetCopiedTextVisible(false);
        }
        internal void SetCopiedTextVisible(bool visible)
        {
            copiedExpanded = visible && copiedText.TextLength > 0;
            copiedPanel.Visible = copiedExpanded; ((NightButton)copiedToggle).Expanded = copiedExpanded; copiedToggle.Invalidate();
            ResizeForContent();
        }
        private void ResizeForContent()
        {
            bool expanded = optionsExpanded || copiedExpanded || details.Visible;
            int width = expanded ? 700 : 420;
            int contentWidth = expanded ? 620 : 380;
            optionsButton.Width = copiedToggle.Width = contentWidth;
            resultActions.MaximumSize = new Size(contentWidth, 0);
            resultActions.MinimumSize = new Size(contentWidth, 0);
            resultActions.Width = contentWidth;
            int textHeight = TextRenderer.MeasureText(status.Text, status.Font, new Size(width - 40, Int32.MaxValue), TextFormatFlags.WordBreak).Height;
            feedback.Height = Math.Max(52, Math.Min(148, textHeight + 12));
            // Grow only as much as the visible sections need, up to the screen limit.
            body.PerformLayout();
            int desired = Math.Max(300, 118 + feedback.Height + body.GetPreferredSize(new Size(width, 0)).Height);
            ClientSize = new Size(width, Math.Min(desired, Screen.FromControl(this).WorkingArea.Height - 80));
        }
        internal void ReadCaseRange(out int firstLabel, out int lastLabel)
        {
            firstLabel = ReadCaseNumber(first, "First case");
            lastLabel = ReadCaseNumber(last, "Last case");
            if (lastLabel < firstLabel)
            { last.Focus(); last.SelectAll(); throw new InvalidOperationException("Last case must be at least the first case number."); }
        }
        private static int ReadCaseNumber(TextBox input, string label)
        {
            int value;
            if (!Int32.TryParse(input.Text.Trim(), NumberStyles.None, CultureInfo.InvariantCulture, out value) || value < 1 || value > 1000000)
            { input.Focus(); input.SelectAll(); throw new InvalidOperationException(label + " must be a whole number from 1 to 1000000."); }
            return value;
        }
        private void OpenComparisonFile()
        {
            if (lastOutput == null) return;
            try { Process.Start("notepad.exe", "\"" + lastOutput + ".for-comparison.txt\""); }
            catch (Exception error) { ShowError("Comparison file did not open", error.Message); }
        }
        protected override bool ShowWithoutActivation { get { return previewMode; } }

        private static Control Row(string left, Control a, string right, Control b)
        {
            var row = new FlowLayoutPanel { AutoSize = true, MaximumSize = new Size(590, 100), WrapContents = false };
            row.Controls.Add(new Label { Text = left, AutoSize = true, Padding = new Padding(0, 5, 0, 0) }); row.Controls.Add(a);
            row.Controls.Add(new Label { Text = right, AutoSize = true, Padding = new Padding(12, 5, 0, 0) }); row.Controls.Add(b);
            return row;
        }

        protected override void OnHandleCreated(EventArgs args)
        {
            base.OnHandleCreated(args);
            NightTheme.TitleBar(this);
            if (previewMode) { stopHotkey = true; return; }
            captureHotkey = Native.RegisterHotKey(Handle, 1, 0x4000, 0x77); // F8, no repeat
            stopHotkey = Native.RegisterHotKey(Handle, 2, 0x4000, 0x6A); // Numpad multiply
            if (!stopHotkey)
            {
                stopHotkey = Native.RegisterHotKey(Handle, 2, 0x4000 | 0x0006, 0x7B); // Ctrl+Shift+F12
                stopShortcut = "Ctrl+Shift+F12";
            }
            stopHint.Text = "Stop with " + stopShortcut + ". Close the old Review Reports script\nso it does not run during this export.";
        }

        protected override void OnHandleDestroyed(EventArgs args)
        {
            if (!previewMode) { Native.UnregisterHotKey(Handle, 1); Native.UnregisterHotKey(Handle, 2); }
            base.OnHandleDestroyed(args);
        }

        protected override void WndProc(ref Message message)
        {
            if (message.Msg == 0x0312)
            {
                if (message.WParam.ToInt32() == 2) CancelExport();
                if (message.WParam.ToInt32() == 1 && captureRole != null && !running) CaptureControl();
            }
            base.WndProc(ref message);
        }

        private void CaptureControl()
        {
            try
            {
                if (captureRole == "WorklistFocus")
                {
                    IntPtr main = Native.UniqueWindow(profile.MainTitle, 0, true);
                    if (main == IntPtr.Zero || Native.GetForegroundWindow() != main)
                        throw new InvalidOperationException("Click the first case row in the main PowerScribe window, then press F8 while PowerScribe is active.");
                    uint pid; Native.GetWindowThreadProcessId(main, out pid);
                    if (Native.UniqueWindow(profile.ComparisonTitle, pid, true) != IntPtr.Zero)
                        throw new InvalidOperationException("Close Compare Report Revisions, click the first case row, then press F8.");
                    string diagnostic = "";
                    IntPtr child = Native.NavigationFocus(main, text => diagnostic = text);
                    if (child == IntPtr.Zero) throw new InvalidOperationException(diagnostic + " No worklist was remembered. This version cannot automatically navigate a grid without a separate usable control.");
                    lockedWorklistMain = main; lockedWorklistChild = child; captureRole = null;
                    status.Text = "Worklist remembered for this exporter session. Return here and export. If PowerScribe is restarted or its layout changes, remember the worklist again.";
                    return;
                }
                if (captureRole == "KeyboardPoint")
                {
                    Native.Point point; Native.Rect rectangle;
                    if (!Native.GetCursorPos(out point)) throw new InvalidOperationException("Could not read the pointer position.");
                    IntPtr window = Native.GetAncestor(Native.WindowFromPoint(point), 2);
                    if (!Native.Title(window).StartsWith(profile.ComparisonTitle, StringComparison.Ordinal) || !Native.GetWindowRect(window, out rectangle))
                        throw new InvalidOperationException("Point inside the attending report body in Compare Report Revisions, then press F8.");
                    clickX.Value = point.X - rectangle.Left; clickY.Value = point.Y - rectangle.Top;
                    profile.ClickX = (int)clickX.Value; profile.ClickY = (int)clickY.Value;
                    SaveProfile(); captureRole = null;
                    status.Text = "Report click saved at " + profile.ClickX + ", " + profile.ClickY + ". Close the comparison, select the first case, then export. No other capture is needed.";
                    return;
                }
                System.Windows.Automation.AutomationElement root;
                var element = WindowsSession.CaptureTarget(captureRole,
                    captureRole == "CaseList" ? profile.MainTitle : profile.ComparisonTitle, out root);
                var locator = Locator.Capture(root, element);
                switch (captureRole)
                {
                    case "CaseList": profile.CaseList = locator; break;
                    case "Attending": profile.Attending = locator; break;
                    case "Resident": profile.Resident = locator; break;
                    case "Close": profile.Close = locator; break;
                }
                SaveProfile();
                status.Text = captureRole + " captured. Close the comparison window before starting an export.";
                captureRole = null;
                RefreshCaptured();
            }
            catch (Exception error) { ShowError("Control capture did not finish", error.Message); }
        }

        private void RefreshCaptured()
        {
            captured.Text = "Captured: list " + Mark(profile.CaseList) + " | attending " + Mark(profile.Attending) +
                " | resident " + Mark(profile.Resident) + " | OK " + Mark(profile.Close);
        }
        private static string Mark(Locator locator) { return locator == null ? "—" : "✓"; }

        private void LoadProfile()
        {
            string path = Path.Combine(settingsDirectory, "controls.json");
            if (!File.Exists(path)) return;
            try
            {
                using (var file = File.OpenRead(path)) profile = (Profile)new DataContractJsonSerializer(typeof(Profile)).ReadObject(file);
                if (profile.Version < 3) { profile.KeyboardWorkflow = true; profile.Version = 3; }
                timeout.Value = Math.Max(timeout.Minimum, Math.Min(timeout.Maximum, profile.TimeoutMs / 1000));
                comparisonWait.Value = Math.Max(comparisonWait.Minimum, Math.Min(comparisonWait.Maximum, profile.ComparisonWaitMs / 1000));
                poll.Value = Math.Max(poll.Minimum, Math.Min(poll.Maximum, profile.PollMs));
                stable.Value = Math.Max(stable.Minimum, Math.Min(stable.Maximum, profile.StableMs));
                clipboard.Checked = profile.ClipboardOnly;
                findingsOnly.Checked = profile.FindingsOnly;
                keyboard.Checked = profile.KeyboardWorkflow;
                website.Checked = profile.OpenWebsite; openText.Checked = profile.OpenTextFile;
                speed.SelectedIndex = profile.TimingMode == "Fast" ? 1 : profile.TimingMode == "Conservative" ? 2 : profile.TimingMode == "Custom" ? 3 : 0;
                if (!String.IsNullOrWhiteSpace(profile.OutputDirectory)) outputFolder.Text = profile.OutputDirectory;
                autoFocus.Checked = profile.AutoRestoreFocus;
                clickX.Value = Math.Max(clickX.Minimum, Math.Min(clickX.Maximum, profile.ClickX));
                clickY.Value = Math.Max(clickY.Minimum, Math.Min(clickY.Maximum, profile.ClickY));
                keyPause.Value = Math.Max(keyPause.Minimum, Math.Min(keyPause.Maximum, profile.KeyDelayMs));
                casePause.Value = Math.Max(casePause.Minimum, Math.Min(casePause.Maximum, profile.CaseDelayMs));
            }
            catch (Exception error) { profile = new Profile(); status.Text = "Saved settings could not be loaded: " + error.Message; }
        }

        private void SaveProfile()
        {
            Directory.CreateDirectory(settingsDirectory);
            string path = Path.Combine(settingsDirectory, "controls.json");
            string temporary = path + ".tmp";
            using (var file = File.Create(temporary)) new DataContractJsonSerializer(typeof(Profile)).WriteObject(file, profile);
            if (File.Exists(path)) File.Replace(temporary, path, null);
            else File.Move(temporary, path);
        }

        private void CancelExport()
        {
            if (cancellation != null)
            {
                cancellation.Cancel();
                if (overlay != null) overlay.SetPhase("Stopping; completed cases are already saved.", -1, 0);
            }
        }

        private void Post(Action action)
        {
            if (IsDisposed || !IsHandleCreated) return;
            try { BeginInvoke(action); }
            catch (ObjectDisposedException) { }
            catch (InvalidOperationException) { }
        }

        internal void ApplyProgress(string text, int completed, int total)
        {
            // Keep the compact launcher steady. Only the external progress
            // window receives live step/count updates; final results stay here.
            if (overlay != null && !overlay.IsDisposed) overlay.SetPhase(text, completed, total);
        }

        private void UpdateStatus(string text, int completed, int total)
        {
            Post(() => ApplyProgress(text, completed, total));
        }

        private void ShowError(string title, string message)
        {
            status.Text = message;
            MessageBox.Show(this, message, title, MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        private void StartExport()
        {
            string output;
            int firstLabel, lastLabel;
            try
            {
                if (!stopHotkey) throw new InvalidOperationException("Both stop shortcuts are in use. Close the programs using Numpad * / Ctrl+Shift+F12, then reopen this exporter.");
                ReadCaseRange(out firstLabel, out lastLabel);
                profile.TimeoutMs = (int)timeout.Value * 1000; profile.PollMs = (int)poll.Value;
                profile.ComparisonWaitMs = (int)comparisonWait.Value * 1000;
                profile.StableMs = (int)stable.Value; profile.ClipboardOnly = clipboard.Checked;
                profile.FindingsOnly = findingsOnly.Checked;
                profile.Version = 7; profile.KeyboardWorkflow = keyboard.Checked; profile.AutoRestoreFocus = autoFocus.Checked;
                profile.ClickX = (int)clickX.Value; profile.ClickY = (int)clickY.Value;
                profile.KeyDelayMs = (int)keyPause.Value; profile.CaseDelayMs = (int)casePause.Value;
                profile.TimingMode = new string[] { "Automatic", "Fast", "Conservative", "Custom" }[Math.Max(0, speed.SelectedIndex)];
                profile.OutputDirectory = outputFolder.Text; profile.OpenWebsite = website.Checked; profile.OpenTextFile = openText.Checked;
                InputTiming.Configure(profile);
                profile.Validate(); SaveProfile();
                output = ExportFiles.NewOutput(profile.OutputDirectory, DateTime.Now);
            }
            catch (Exception error) { ShowError("Export has not started", error.Message); return; }
            bool openWebsite = website.Checked;
            bool openTextFile = openText.Checked;
            lastOutput = output; resumeCase = null; resultActions.Visible = false; details.Visible = false;
            SetCopiedTextVisible(false);
            SetOptionsVisible(false);
            captureRole = null; running = true; cancellation = new CancellationTokenSource();
            start.Enabled = false; stop.Enabled = true;
            foreach (Control control in body.Controls) if (control != status && control != start.Parent) control.Enabled = false;
            status.Text = "Exporting. Follow the progress window.\n" + stopShortcut + " stops the run.";
            overlay = new ProgressOverlay(stopShortcut);
            overlay.StopRequested += (sender, args) => CancelExport();
            var screen = Screen.FromControl(this).WorkingArea;
            overlay.Location = new Point(Math.Max(screen.Left, screen.Right - overlay.Width - 16), screen.Top + 16);
            overlay.SetPhase("Starting export...", 0, lastLabel - firstLabel + 1);
            overlay.Show(this);
            var runner = new ExportRunner(profile.FindingsOnly);
            var worker = new Thread(() => {
                string result = "";
                bool success = false;
                bool failed = false;
                string outcome = "Stopped", nextStep = "", diagnostic = "", availableText = null;
                AsyncProgressLog progressLog = null;
                Action<string> reportProgress = text => {
                    if (progressLog != null)
                    {
                        progressLog.WriteLine(DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff") + " " + text);
                    }
                    UpdateStatus(text, runner.Saved, lastLabel - firstLabel + 1);
                };
                try
                {
                    progressLog = new AsyncProgressLog(output + ".progress.log");
                    reportProgress("Initializing native exporter v0.17...");
                    IReportSession session = profile.KeyboardWorkflow ?
                        (IReportSession)new KeyboardSession(profile, new Win32Desktop(lockedWorklistMain, lockedWorklistChild, reportProgress), reportProgress) :
                        (IReportSession)new WindowsSession(profile, reportProgress);
                    runner.Run(session, firstLabel, lastLabel, output, cancellation.Token, reportProgress);
                    success = true; outcome = "Done"; result = "Done. " + runner.Completed + " complete pairs ready to paste.";
                    if (runner.Pending + runner.Skipped > 0) result += " " + (runner.Pending + runner.Skipped) + " entries need review; see Details.";
                    diagnostic = "Only complete pairs go into the comparison file. Unconfirmed pending and unavailable entries remain in the original capture.\r\n" + runner.OutcomeSummary;
                    try
                    {
                        availableText = ExportDelivery.ReadCompleted(output, runner.Completed);
                        if (availableText != null)
                        {
                            ClipboardWriter(availableText);
                            result += " Copied. On the website: Paste, then Analyze reports.";
                        }
                    }
                    catch (Exception)
                    {
                        result += " Clipboard copy failed; use Copied text > Copy again or Open comparison file.";
                    }
                }
                catch (OperationCanceledException) { result = "Stopped. " + runner.Completed + " complete pairs saved. See Details to continue from the stopping point."; diagnostic = "Cancelled by the user. Saved captures were kept."; }
                catch (Exception error) { failed = true; nextStep = RunSummary.NextStep(error, runner, firstLabel, lastLabel); result = "Export stopped. " + runner.Completed + " complete pairs saved. " + nextStep; diagnostic = error.Message; }
                finally
                {
                    // This also exposes already saved complete pairs after a stopped run.
                    // Reading failure does not erase the previous in-app export or its file.
                    if (availableText == null && runner.Completed > 0)
                    {
                        try { availableText = ExportDelivery.ReadCompleted(output, runner.Completed); }
                        catch (Exception) { result += " The saved text could not be loaded here; check Open save folder."; }
                    }
                    diagnostic = RunSummary.Build(runner, firstLabel, lastLabel, outcome, nextStep + "\r\n" + diagnostic, output);
                    try { File.WriteAllText(output + ".run-summary.txt", diagnostic); }
                    catch (Exception) { result += " The run summary could not be saved; Details still has it."; }
                    if (progressLog != null)
                    {
                        try { progressLog.WriteLine(DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff") + " " + result); progressLog.Dispose(); if (progressLog.Failed) result += " Progress log could not be fully written."; }
                        catch (IOException) { }
                    }
                }
                Post(() => {
                    if (overlay != null) { overlay.Close(); overlay.Dispose(); overlay = null; }
                    running = false; cancellation.Dispose(); cancellation = null;
                    foreach (Control control in body.Controls) control.Enabled = true;
                    start.Enabled = true; stop.Enabled = false;
                    status.Text = result;
                    SetCopiedText(availableText, "Saved export " + DateTime.Now.ToString("g") + " - case labels " + firstLabel + "-" + lastLabel + ", " + runner.Completed + " complete pairs.\r\n" + Path.GetFileName(output));
                    details.Text = diagnostic; detailsButton.Text = "Details"; details.Visible = false; resultActions.Visible = true;
                    openComparison.Enabled = runner.Completed > 0;
                    resumeCase = success ? null : RunSummary.ResumeAt(runner, firstLabel, lastLabel); resume.Visible = resumeCase.HasValue;
                    ResizeForContent();
                    if (openTextFile && runner.Completed > 0) OpenComparisonFile();
                    if (success && openWebsite && runner.Completed > 0)
                    {
                        try { Process.Start("https://compare-revisions-646439009049.us-central1.run.app/"); }
                        catch (Exception error) { status.Text += " Website could not be opened: " + error.Message; }
                    }
                    if (failed) detailsButton.Font = new Font(detailsButton.Font, FontStyle.Bold);
                });
            });
            worker.IsBackground = true;
            worker.SetApartmentState(ApartmentState.STA); // Required for Windows clipboard access.
            worker.Start();
        }
    }

    public sealed class ProgressOverlay : Form
    {
        private readonly Label phase = new Label { Dock = DockStyle.Top, Height = 64, Padding = new Padding(10), AutoEllipsis = true };
        private readonly Label count = new Label { Dock = DockStyle.Top, Height = 24, Padding = new Padding(10, 0, 0, 0) };
        private readonly Label elapsed = new Label { Dock = DockStyle.Top, Height = 24, Padding = new Padding(10, 0, 0, 0) };
        private readonly System.Windows.Forms.Timer heartbeat = new System.Windows.Forms.Timer { Interval = 100 };
        private readonly Stopwatch totalTime = Stopwatch.StartNew();
        private readonly Stopwatch phaseTime = Stopwatch.StartNew();
        public event EventHandler StopRequested;
        protected override bool ShowWithoutActivation { get { return true; } }
        protected override CreateParams CreateParams
        {
            get { var parameters = base.CreateParams; parameters.ExStyle |= 0x08000000 | 0x80; return parameters; }
        }
        public ProgressOverlay(string stopShortcut)
        {
            Text = "Export progress — " + stopShortcut + " stops";
            ClientSize = new Size(470, 180);
            FormBorderStyle = FormBorderStyle.FixedToolWindow;
            ControlBox = false;
            TopMost = true;
            StartPosition = FormStartPosition.Manual;
            Font = new Font("Segoe UI", 10);
            var stopButton = new NightButton { Text = "Stop export", Dock = DockStyle.Bottom, Height = 42 };
            stopButton.Click += (sender, args) => { if (StopRequested != null) StopRequested(this, EventArgs.Empty); };
            Controls.Add(stopButton); Controls.Add(elapsed); Controls.Add(count); Controls.Add(phase);
            heartbeat.Tick += (sender, args) => {
                elapsed.Text = "Elapsed " + totalTime.Elapsed.TotalSeconds.ToString("F1") + " s  |  current step " + phaseTime.Elapsed.TotalSeconds.ToString("F1") + " s";
            };
            elapsed.Text = "Elapsed 0 s  |  current step 0 s";
            NightTheme.Apply(this); phase.Font = new Font(Font, FontStyle.Bold);
            count.ForeColor = NightTheme.Accent; elapsed.ForeColor = NightTheme.Muted;
            heartbeat.Start();
        }
        protected override void OnHandleCreated(EventArgs args)
        { base.OnHandleCreated(args); NightTheme.TitleBar(this); }
        public void SetPhase(string text, int completed, int total)
        {
            if (phase.Text != text) phaseTime.Restart();
            phase.Text = text;
            if (completed >= 0) count.Text = completed + " / " + total + " case entries saved";
        }
        protected override void Dispose(bool disposing)
        {
            if (disposing) { heartbeat.Stop(); heartbeat.Dispose(); }
            base.Dispose(disposing);
        }
    }
}
