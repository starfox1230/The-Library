using System;
using System.IO;

namespace ReportExporter
{
    public sealed class SetupCaptureCountdown
    {
        private readonly Func<double> clock;
        private readonly Action<string> capture;
        private double due;
        public string Role { get; private set; }
        public bool Active { get { return Role != null; } }
        public int SecondsRemaining { get { return Active ? Math.Max(0, (int)Math.Ceiling((due - clock()) / 1000)) : 0; } }
        public SetupCaptureCountdown(Func<double> clock, Action<string> capture)
        { this.clock = clock; this.capture = capture; }
        public void Start(string role)
        { if (String.IsNullOrEmpty(role)) throw new ArgumentException("Choose a setup target."); Role = role; due = clock() + 5000; }
        public void Cancel() { Role = null; }
        public void Tick()
        {
            if (!Active || clock() < due) return;
            string role = Role; Role = null; // Exactly once, even if capture throws or reenters.
            capture(role);
        }
    }

    public sealed class InputTiming
    {
        private readonly bool automatic;
        private readonly string mode;
        private readonly int caseDelay;
        public int KeyDelayMs { get; private set; }
        public InputTiming(Profile profile)
        { mode = profile.TimingMode; automatic = mode == "Automatic"; caseDelay = profile.CaseDelayMs; KeyDelayMs = automatic ? 10 : profile.KeyDelayMs; }
        public int StudySwitchDelay(bool firstSwitch)
        {
            if (mode == "Custom") return caseDelay;
            // A selected row/enabled parent is not evidence that the report model
            // has loaded. Keep key delays short, but allow the source-study switch
            // to settle BEFORE opening a comparison (which may snapshot old text).
            int floor = mode == "Conservative" ? (firstSwitch ? 1000 : 750) : firstSwitch ? 750 : 500;
            return Math.Max(caseDelay, floor);
        }
        public bool CopyRetry()
        {
            if (!automatic || KeyDelayMs >= 100) return false;
            KeyDelayMs = KeyDelayMs < 25 ? 25 : 100;
            return true;
        }
        public static void Configure(Profile profile)
        {
            if (profile.TimingMode == "Automatic" || profile.TimingMode == "Fast")
            { profile.KeyDelayMs = 10; profile.CaseDelayMs = 500; profile.PollMs = 5; }
            if (profile.TimingMode == "Conservative")
            { profile.KeyDelayMs = 100; profile.CaseDelayMs = 750; profile.PollMs = 10; }
        }
    }

    public static class ExportFiles
    {
        public static string NewOutput(string folder, DateTime now)
        {
            if (String.IsNullOrWhiteSpace(folder)) throw new IOException("Choose a save folder in Options.");
            Directory.CreateDirectory(folder);
            // A unique run never overwrites a previous export or its sidecars.
            return Path.Combine(folder, "Report comparison " + now.ToString("yyyy-MM-dd HHmmss-fff") + "-" + Guid.NewGuid().ToString("N").Substring(0, 8) + ".txt");
        }
    }

    public static class RunSummary
    {
        public static int? ResumeAt(ExportRunner runner, int first, int last)
        {
            int next = runner.LastAttemptedCase ?? first;
            if (runner.LastSavedCase.HasValue && runner.LastSavedCase.Value >= next) next = runner.LastSavedCase.Value + 1;
            return next <= last ? (int?)next : null;
        }
        public static string NextStep(Exception error, ExportRunner runner, int first, int last)
        {
            string message = error == null ? "" : error.Message;
            int? next = ResumeAt(runner, first, last);
            if (!next.HasValue) return "The requested entries were saved. Close any comparison before starting another run.";
            if (message.IndexOf("worklist", StringComparison.OrdinalIgnoreCase) >= 0)
                return "Close any comparison and select case " + next.Value + " in the same PowerScribe worklist before continuing.";
            if (message.IndexOf("report body", StringComparison.OrdinalIgnoreCase) >= 0 || message.IndexOf("not copied", StringComparison.OrdinalIgnoreCase) >= 0)
                return "Check that both report panes are ready. Use Options > Capture report click if the click lands outside the report body. Copying has already been retried where safe.";
            if (message.IndexOf("not found", StringComparison.OrdinalIgnoreCase) >= 0)
                return "Open PowerScribe and select case " + next.Value + " before continuing.";
            return "Check the last step in Details. Close any comparison before selecting the resume case in PowerScribe. Saved results are kept.";
        }
        public static string Build(ExportRunner runner, int first, int last, string outcome, string detail, string output)
        {
            int? resume = ResumeAt(runner, first, last);
            return "PowerScribe Report Exporter v0.25\r\n" + outcome + "\r\n" +
                "Requested case labels: " + first + "–" + last + "\r\n" +
                "Complete report pairs: " + runner.Completed + "\r\n" +
                "Unconfirmed pending: " + runner.Pending + "\r\nUnavailable comparisons: " + runner.Skipped + "\r\n" +
                "Last attempted case: " + (runner.LastAttemptedCase.HasValue ? runner.LastAttemptedCase.Value.ToString() : "None") + "\r\n" +
                "Last saved source entry: " + (runner.LastSavedCase.HasValue ? runner.LastSavedCase.Value.ToString() : "None") + "\r\n" +
                runner.OutcomeSummary + "\r\n\r\n" + detail + "\r\n\r\n" +
                (outcome == "Done" ? "" : resume.HasValue ? "To resume: select case " + resume.Value + " in PowerScribe, set First case to " + resume.Value + ", then Go. The exporter does not select this row for you.\r\n" : "No remaining source entries are suggested.\r\n") +
                "\r\nComparison file: " + output + ".for-comparison.txt\r\nVerified comparison bytes: " + runner.VerifiedComparisonBytes + "\r\n" +
                "Capture checks (no report text): " + output + ".capture-checks.csv\r\n" +
                "Original capture: " + output + "\r\nProgress log: " + output + ".progress.log\r\n" +
                "Outcomes: " + output + ".outcomes.csv\r\nTimings: " + output + ".timings.csv\r\n";
        }
    }
}
