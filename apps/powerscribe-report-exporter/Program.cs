using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Runtime.Serialization.Json;
using System.Threading;
using System.Windows.Forms;

[assembly: AssemblyVersion("0.13.0.0")]
[assembly: AssemblyFileVersion("0.13.0.0")]

namespace ReportExporter
{
    public static class Program
    {
        [STAThread]
        public static void Main(string[] args)
        {
            if (args.Length == 2 && (args[0] == "--preview" || args[0] == "--preview-options" || args[0] == "--preview-progress"))
            {
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                using (Form form = args[0] == "--preview-progress" ? (Form)new ProgressOverlay("Numpad *") : new ExportForm(true))
                {
                    if (args[0] == "--preview-options") ((ExportForm)form).SetOptionsVisible(true);
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
        private readonly NumericUpDown first = Number(1, 1000000, 1);
        private readonly NumericUpDown last = Number(1, 1000000, 1);
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
        private readonly Button start = new Button { Name = "Go", Text = "Go", Width = 110, Height = 36, BackColor = Color.FromArgb(32, 89, 155), ForeColor = Color.White, FlatStyle = FlatStyle.Flat };
        private readonly Button stop = new Button { Text = "Stop", AutoSize = true, Enabled = false };
        private FlowLayoutPanel body;
        private string captureRole;
        // Session-only native handles: never serialize them to controls.json.
        private IntPtr lockedWorklistMain, lockedWorklistChild;
        private CancellationTokenSource cancellation;
        private bool running;
        private bool captureHotkey, stopHotkey;
        private ProgressOverlay overlay;
        private FlowLayoutPanel keyboardSettings, accessibilitySettings;
        private FlowLayoutPanel optionsPanel, resultActions, customTiming;
        private readonly Button optionsButton = new Button { Name = "Options", Text = "Options >", AutoSize = true, FlatStyle = FlatStyle.Flat };
        private readonly ComboBox speed = new ComboBox { Name = "Speed", DropDownStyle = ComboBoxStyle.DropDownList, Width = 230 };
        private readonly TextBox outputFolder = new TextBox { Width = 390, ReadOnly = true };
        private readonly CheckBox openText = new CheckBox { Text = "Also open the comparison file in Notepad", AutoSize = true };
        private readonly TextBox details = new TextBox { Name = "RunDetails", Width = 570, Height = 180, Multiline = true, ReadOnly = true, ScrollBars = ScrollBars.Vertical, Visible = false };
        private readonly Button detailsButton = new Button { Text = "Details", AutoSize = true };
        private readonly Button openComparison = new Button { Text = "Open comparison file", AutoSize = true };
        private readonly Button resume = new Button { Text = "Prepare remaining cases", AutoSize = true, Visible = false };
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
            Text = "PowerScribe Report Exporter v0.13";
            ClientSize = new Size(620, 280);
            MinimumSize = new Size(640, 310);
            Font = new Font("Segoe UI", 10);
            body = new FlowLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(15), FlowDirection = FlowDirection.TopDown, WrapContents = false, AutoScroll = true };
            Controls.Add(body);
            var feedback = new Panel { Dock = DockStyle.Top, Height = 94, Padding = new Padding(15), BackColor = Color.FromArgb(230, 240, 250) };
            status.Dock = DockStyle.Fill;
            status.Font = new Font(Font, FontStyle.Bold);
            feedback.Controls.Add(status);
            Controls.Add(feedback);
            first.Name = "FirstCase"; last.Name = "LastCase";
            body.Controls.Add(Row("First case", first, "Last case", last));
            body.Controls.Add(new Label { Text = "Numbers label the export; PowerScribe starts from the row you selected.", AutoSize = true, MaximumSize = new Size(570, 0), ForeColor = Color.DimGray });
            optionsButton.FlatAppearance.BorderSize = 0;
            body.Controls.Add(optionsButton);
            optionsPanel = new FlowLayoutPanel { Name = "OptionsPanel", AutoSize = true, FlowDirection = FlowDirection.TopDown, WrapContents = false, Visible = false };
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
            var rememberWorklist = new Button { Text = "Remember worklist (F8)", AutoSize = true };
            rememberWorklist.Click += (sender, args) => {
                if (!captureHotkey) { ShowError("F8 is in use", "Close the other program using F8 and reopen this exporter."); return; }
                lockedWorklistMain = lockedWorklistChild = IntPtr.Zero;
                captureRole = "WorklistFocus";
                status.Text = "Click the FIRST CASE ROW in PowerScribe, then press F8 while PowerScribe is active. This remembers keyboard focus; no accessibility capture is used.";
            };
            var clearWorklist = new Button { Text = "Clear remembered worklist", AutoSize = true };
            clearWorklist.Click += (sender, args) => {
                lockedWorklistMain = lockedWorklistChild = IntPtr.Zero; captureRole = null;
                status.Text = "Remembered worklist cleared. The next export will detect focus automatically.";
            };
            worklistButtons.Controls.Add(rememberWorklist); worklistButtons.Controls.Add(clearWorklist);
            keyboardSettings.Controls.Add(worklistButtons);
            keyboardSettings.Controls.Add(Row("Report click X", clickX, "Y", clickY));
            var captureClick = new Button { Text = "Capture report click (optional)", AutoSize = true };
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
                var button = new Button { Text = role == "Close" ? "Capture OK button" : "Capture " + role, AutoSize = true };
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
            outputFolder.Text = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "Report comparisons");
            var chooseFolder = new Button { Text = "Save folder...", AutoSize = true };
            chooseFolder.Click += (sender, args) => { using (var picker = new FolderBrowserDialog { Description = "Choose where reports are saved", SelectedPath = outputFolder.Text }) { if (picker.ShowDialog(this) == DialogResult.OK) outputFolder.Text = picker.SelectedPath; } };
            var folderRow = new FlowLayoutPanel { AutoSize = true }; folderRow.Controls.Add(outputFolder); folderRow.Controls.Add(chooseFolder); optionsPanel.Controls.Add(folderRow);
            stopHint.Text = "Stop with " + stopShortcut + ". Close the old Review Reports script\nso it does not run during this export.";
            optionsPanel.Controls.Add(stopHint);
            resultActions = new FlowLayoutPanel { Name = "ResultActions", AutoSize = true, MaximumSize = new Size(570, 0), Visible = false };
            var openFolder = new Button { Text = "Open save folder", AutoSize = true };
            openComparison.Click += (sender, args) => OpenComparisonFile();
            openFolder.Click += (sender, args) => { try { Process.Start(Path.GetDirectoryName(lastOutput)); } catch (Exception error) { ShowError("Folder did not open", error.Message); } };
            detailsButton.Click += (sender, args) => { details.Visible = !details.Visible; detailsButton.Text = details.Visible ? "Hide details" : "Details"; ResizeForContent(); };
            resume.Click += (sender, args) => { if (resumeCase.HasValue) { first.Value = resumeCase.Value; status.Text = "Select case " + resumeCase.Value + " in PowerScribe, then Go. This button only sets the range here."; } };
            resultActions.Controls.Add(openComparison); resultActions.Controls.Add(openFolder); resultActions.Controls.Add(detailsButton); resultActions.Controls.Add(resume);
            body.Controls.Add(resultActions); body.Controls.Add(details);
            var actionRow = new FlowLayoutPanel { Dock = DockStyle.Bottom, Height = 48, Padding = new Padding(12, 4, 12, 4) };
            actionRow.Controls.Add(start); actionRow.Controls.Add(stop); Controls.Add(actionRow);
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
            optionsExpanded = visible; optionsPanel.Visible = visible; optionsButton.Text = visible ? "Options v" : "Options >";
            ResizeForContent();
        }
        private void ResizeForContent()
        {
            int desired = optionsExpanded ? 720 : details.Visible ? 620 : resultActions.Visible ? 410 : 280;
            ClientSize = new Size(ClientSize.Width, Math.Min(desired, Screen.FromControl(this).WorkingArea.Height - 80));
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
                cancellation.Cancel(); status.Text = "Stopping; completed cases are already saved.";
                if (overlay != null) overlay.SetPhase(status.Text, -1, 0);
            }
        }

        private void Post(Action action)
        {
            if (IsDisposed || !IsHandleCreated) return;
            try { BeginInvoke(action); }
            catch (ObjectDisposedException) { }
            catch (InvalidOperationException) { }
        }

        private void UpdateStatus(string text, int completed, int total)
        {
            Post(() => {
                status.Text = completed + " / " + total + " cases saved.\r\n" + text;
                if (overlay != null && !overlay.IsDisposed) overlay.SetPhase(text, completed, total);
            });
        }

        private void ShowError(string title, string message)
        {
            status.Text = message;
            MessageBox.Show(this, message, title, MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        private void StartExport()
        {
            string output;
            try
            {
                if (!stopHotkey) throw new InvalidOperationException("Both stop shortcuts are in use. Close the programs using Numpad * / Ctrl+Shift+F12, then reopen this exporter.");
                if (last.Value < first.Value) throw new InvalidOperationException("Last case must be at least the first case number.");
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
            int firstLabel = (int)first.Value, lastLabel = (int)last.Value;
            bool openWebsite = website.Checked;
            bool openTextFile = openText.Checked;
            lastOutput = output; resumeCase = null; resultActions.Visible = false; details.Visible = false;
            SetOptionsVisible(false);
            captureRole = null; running = true; cancellation = new CancellationTokenSource();
            start.Enabled = false; stop.Enabled = true;
            foreach (Control control in body.Controls) if (control != status && control != start.Parent) control.Enabled = false;
            status.Text = "Exporting. " + stopShortcut + " stops the run.";
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
                string outcome = "Stopped", nextStep = "", diagnostic = "";
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
                    reportProgress("Initializing native exporter v0.13...");
                    IReportSession session = profile.KeyboardWorkflow ?
                        (IReportSession)new KeyboardSession(profile, new Win32Desktop(lockedWorklistMain, lockedWorklistChild, reportProgress), reportProgress) :
                        (IReportSession)new WindowsSession(profile, reportProgress);
                    runner.Run(session, firstLabel, lastLabel, output, cancellation.Token, reportProgress);
                    success = true; outcome = "Done"; result = "Done. " + runner.Completed + " complete pairs ready to paste.";
                    if (runner.Pending + runner.Skipped > 0) result += " " + (runner.Pending + runner.Skipped) + " entries need review; see Details.";
                    diagnostic = "Only complete pairs go into the comparison file. Unconfirmed pending and unavailable entries remain in the original capture.\r\n" + runner.OutcomeSummary;
                    try
                    {
                        if (ExportDelivery.CopyCompleted(output, runner.Completed,
                            text => Clipboard.SetDataObject(text, true, 3, 100)))
                            result += " Copied. On the website: Paste, then Analyze reports.";
                    }
                    catch (Exception)
                    {
                        result += " Clipboard copy failed; use Open comparison file to copy the saved text.";
                    }
                }
                catch (OperationCanceledException) { result = "Stopped. " + runner.Completed + " complete pairs saved. See Details to continue from the stopping point."; diagnostic = "Cancelled by the user. Saved captures were kept."; }
                catch (Exception error) { failed = true; nextStep = RunSummary.NextStep(error, runner, firstLabel, lastLabel); result = "Export stopped. " + runner.Completed + " complete pairs saved. " + nextStep; diagnostic = error.Message; }
                finally
                {
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
            ClientSize = new Size(430, 152);
            FormBorderStyle = FormBorderStyle.FixedToolWindow;
            ControlBox = false;
            TopMost = true;
            StartPosition = FormStartPosition.Manual;
            Font = new Font("Segoe UI", 10);
            var stopButton = new Button { Text = "Stop export", Dock = DockStyle.Bottom, Height = 34 };
            stopButton.Click += (sender, args) => { if (StopRequested != null) StopRequested(this, EventArgs.Empty); };
            Controls.Add(stopButton); Controls.Add(elapsed); Controls.Add(count); Controls.Add(phase);
            heartbeat.Tick += (sender, args) => {
                elapsed.Text = "Elapsed " + totalTime.Elapsed.TotalSeconds.ToString("F1") + " s  |  current step " + phaseTime.Elapsed.TotalSeconds.ToString("F1") + " s";
            };
            elapsed.Text = "Elapsed 0 s  |  current step 0 s";
            heartbeat.Start();
        }
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
