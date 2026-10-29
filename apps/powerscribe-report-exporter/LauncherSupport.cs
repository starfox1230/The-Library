using System;
using System.IO;

namespace ReportExporter
{
    public sealed class InputTiming
    {
        private readonly bool automatic;
        public int KeyDelayMs { get; private set; }
        public InputTiming(Profile profile)
        { automatic = profile.TimingMode == "Automatic"; KeyDelayMs = automatic ? 10 : profile.KeyDelayMs; }
        public bool CopyRetry()
        {
            if (!automatic || KeyDelayMs >= 100) return false;
            KeyDelayMs = KeyDelayMs < 25 ? 25 : 100;
            return true;
        }
        public static void Configure(Profile profile)
        {
            if (profile.TimingMode == "Automatic" || profile.TimingMode == "Fast")
            { profile.KeyDelayMs = 10; profile.CaseDelayMs = 100; profile.PollMs = 5; }
            if (profile.TimingMode == "Conservative")
            { profile.KeyDelayMs = 100; profile.CaseDelayMs = 100; profile.PollMs = 10; }
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
            if (message.IndexOf("worklist", StringComparison.OrdinalIgnoreCase) >= 0)
                return "Close any comparison, select the first case row in PowerScribe, and try again. If needed, use Options > Remember worklist (F8).";
            if (message.IndexOf("report body", StringComparison.OrdinalIgnoreCase) >= 0 || message.IndexOf("not copied", StringComparison.OrdinalIgnoreCase) >= 0)
                return "Check that both report panes are ready. Use Options > Capture report click if the click lands outside the report body. Copying has already been retried where safe.";
            if (message.IndexOf("not found", StringComparison.OrdinalIgnoreCase) >= 0)
                return "Open PowerScribe and select the first case row before choosing Go.";
            if (!ResumeAt(runner, first, last).HasValue)
                return "The requested entries were saved. Check the comparison window and the details before starting another run.";
            return "Check the last step in Details. Close any comparison before selecting the resume case in PowerScribe. Saved results are kept.";
        }
        public static string Build(ExportRunner runner, int first, int last, string outcome, string detail, string output)
        {
            int? resume = ResumeAt(runner, first, last);
            return "PowerScribe Report Exporter v0.13\r\n" + outcome + "\r\n" +
                "Requested case labels: " + first + "–" + last + "\r\n" +
                "Complete report pairs: " + runner.Completed + "\r\n" +
                "Unconfirmed pending: " + runner.Pending + "\r\nUnavailable comparisons: " + runner.Skipped + "\r\n" +
                "Last attempted case: " + (runner.LastAttemptedCase.HasValue ? runner.LastAttemptedCase.Value.ToString() : "None") + "\r\n" +
                "Last saved source entry: " + (runner.LastSavedCase.HasValue ? runner.LastSavedCase.Value.ToString() : "None") + "\r\n" +
                runner.OutcomeSummary + "\r\n\r\n" + detail + "\r\n\r\n" +
                (outcome == "Done" ? "" : resume.HasValue ? "To resume: select case " + resume.Value + " in PowerScribe, set First case to " + resume.Value + ", then Go. The exporter does not select this row for you.\r\n" : "No remaining source entries are suggested.\r\n") +
                "\r\nComparison file: " + output + ".for-comparison.txt\r\n" +
                "Original capture: " + output + "\r\nProgress log: " + output + ".progress.log\r\n" +
                "Outcomes: " + output + ".outcomes.csv\r\nTimings: " + output + ".timings.csv\r\n";
        }
    }
}
