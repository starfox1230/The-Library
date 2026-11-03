using System;
using System.Drawing;
using System.Threading;
using System.Windows.Forms;

namespace ReportExporter
{
    public sealed class RecoveryDialog : Form
    {
        private readonly System.Windows.Forms.Timer cancelTimer;
        private readonly bool allowLinked;
        private readonly bool finishOnly;
        private readonly Func<bool> continueReady;
        private readonly Button proceed;
        private readonly Label readiness;
        private readonly int sourceCase;
        private bool decided;
        internal RecoveryChoice Choice { get; private set; }

        public RecoveryDialog(RecoveryRequest request, CancellationToken token, Func<bool> worklistReady = null)
        {
            Choice = RecoveryChoice.Stop; allowLinked = request.RepeatedFromCase.HasValue;
            finishOnly = request.FinishOnly; sourceCase = request.CaseNumber; continueReady = worklistReady;
            Text = "Paused — PowerScribe Report Exporter v0.21";
            ClientSize = new Size(620, 380); FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = MinimizeBox = false; StartPosition = FormStartPosition.CenterScreen;
            TopMost = true; Font = new Font("Segoe UI", 10); Padding = new Padding(18);
            var heading = new Label { Name = "RecoveryHeading", AutoSize = false, Dock = DockStyle.Top, Height = 55,
                Font = new Font(Font, FontStyle.Bold), Text = request.FinishOnly ? "All requested entries are saved." : "Paused at case " + request.CaseNumber + ". Saved reports are kept." };
            var instructions = new Label { Name = "RecoveryInstructions", AutoSize = false, Dock = DockStyle.Top, Height = 115,
                Text = request.FinishOnly ? "Close Compare Report Revisions in PowerScribe, then click Finish. Nothing will be copied or advanced again." :
                    "1. Close Compare Report Revisions in PowerScribe.\r\n2. Select case " + request.CaseNumber + " in the SAME worklist/order.\r\n3. Click Continue. PowerScribe will be brought forward and this case will be read again." +
                    (allowLinked ? "\r\n\r\nIf these are separate linked studies with identical reports, confirm that below instead." : "") };
            var reason = new TextBox { Name = "RecoveryReason", Dock = DockStyle.Fill, Multiline = true, ReadOnly = true, ScrollBars = ScrollBars.Vertical, Text = request.Reason };
            var buttons = new FlowLayoutPanel { Dock = DockStyle.Bottom, Height = 52, FlowDirection = FlowDirection.RightToLeft, Padding = new Padding(0, 10, 0, 0), WrapContents = false };
            proceed = new NightButton { Name = "RecoveryContinue", Text = request.FinishOnly ? "Finish" : "Continue", Width = 100, Height = 34 };
            readiness = new Label { Name = "RecoveryReadiness", Dock = DockStyle.Top, Height = 30, AutoSize = false, ForeColor = Color.DimGray };
            var stop = new NightButton { Name = "RecoveryStop", Text = "Stop", Width = 85, Height = 34 };
            var linked = new NightButton { Name = "RecoveryLinked", Text = "These are linked studies", Width = 220, Height = 34, Visible = allowLinked };
            proceed.Click += (s, e) => ChooseRecovery(RecoveryChoice.Continue);
            stop.Click += (s, e) => ChooseRecovery(RecoveryChoice.Stop);
            linked.Click += (s, e) => ChooseRecovery(RecoveryChoice.AcceptLinkedStudies);
            buttons.Controls.Add(proceed); buttons.Controls.Add(stop); buttons.Controls.Add(linked);
            Controls.Add(reason); Controls.Add(readiness); Controls.Add(instructions); Controls.Add(heading); Controls.Add(buttons);
            AcceptButton = proceed; CancelButton = stop; NightTheme.Apply(this);
            ActiveControl = proceed;
            cancelTimer = new System.Windows.Forms.Timer { Interval = 100 };
            cancelTimer.Tick += (s, e) => { if (token.IsCancellationRequested) ChooseRecovery(RecoveryChoice.Stop); else RefreshReadiness(); };
            RefreshReadiness();
            cancelTimer.Start();
        }

        internal void ChooseRecovery(RecoveryChoice choice)
        {
            if (decided) return;
            if (choice == RecoveryChoice.Continue && !RefreshReadiness()) return;
            if (choice == RecoveryChoice.AcceptLinkedStudies && !allowLinked) throw new InvalidOperationException("Linked-study confirmation is not available for this interruption.");
            decided = true; foreach (Control button in proceed.Parent.Controls) button.Enabled = false;
            Choice = choice; DialogResult = choice == RecoveryChoice.Stop ? DialogResult.Cancel : DialogResult.OK; Close();
        }

        internal bool RefreshReadiness()
        {
            if (decided) return false;
            bool ready = finishOnly || continueReady == null || continueReady();
            proceed.Enabled = ready;
            readiness.Text = finishOnly || continueReady == null ? "" : ready ?
                "Worklist control remembered. Select case " + sourceCase + ", then Continue." :
                "Click case " + sourceCase + " in PowerScribe's worklist. Continue enables when its control is detected.";
            return ready;
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing && cancelTimer != null) cancelTimer.Dispose();
            base.Dispose(disposing);
        }
    }
}
