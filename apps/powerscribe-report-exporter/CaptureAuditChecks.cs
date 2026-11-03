using System;
using System.IO;
using System.Text;
using System.Linq;
using System.Threading;

namespace ReportExporter
{
    public static class CaptureAuditChecks
    {
        private static void Require(bool value, string message) { if (!value) throw new Exception(message); }
        private static void Reject(Action action) { try { action(); } catch (IOException) { return; } throw new Exception("Expected an integrity failure"); }
        private static ReportPair Pair(string marker)
        { return new ReportPair { Attending = "SYNTHETIC HEADER\r\nFINDINGS: attending " + marker, Resident = "SYNTHETIC HEADER\r\nFINDINGS: resident " + marker }; }
        private sealed class Sequence : IReportSession
        {
            private int row;
            public bool CanVerifySelectedRow { get { return true; } }
            public string SelectedCase() { return "row:" + row; }
            public void OpenComparison(CancellationToken token) { }
            public ReportPair ReadReports(CancellationToken token) { return Pair(row + " café →"); }
            public void CloseComparison(CancellationToken token) { }
            public void Advance(string previous, CancellationToken token) { row++; }
        }
        private sealed class ReplacingWriter : StreamWriter
        {
            public bool Replace;
            public ReplacingWriter(FileStream file) : base(file, new UTF8Encoding(true)) { }
            public override void Write(string text) { base.Write(Replace ? text.Replace("SECOND", "FIRST!") : text); }
        }
        public static void VerifyRecords(string path)
        {
            var runner = new ExportRunner(); runner.Run(new Sequence(), 11, 13, path, CancellationToken.None, m => { });
            var lines = File.ReadAllLines(path + ".capture-checks.csv").Skip(1).Select(s => s.Split(',')).ToArray();
            var captures = lines.Where(s => s[0] == "captured").ToArray();
            Require(captures.Length == 3 && captures.Select(s => s[3]).Distinct().Count() == 3, "Capture identities or distinct reports were lost");
            for (int i = 0; i < 3; i++)
            {
                var capture = captures[i]; Require(capture[1] == (11 + i).ToString() && capture[2] == (i + 1).ToString(), "Source labels or attempt IDs shifted");
                var writes = lines.Where(s => s[2] == capture[2] && s[0] != "captured").ToArray();
                Require(writes.Length == 2 && writes.All(s => s[3] == capture[3] && s[4] == capture[4] && s[5].Length == 32 && Int32.Parse(s[6]) > 0), "Saved records do not match their capture tokens");
            }
            string log = File.ReadAllText(path + ".capture-checks.csv");
            Require(!log.Contains("SYNTHETIC HEADER") && !log.Contains("FINDINGS:") && !log.Contains("café"), "Report text leaked into capture diagnostics");
            Require(runner.VerifiedComparisonBytes == new FileInfo(path + ".for-comparison.txt").Length, "Verified byte boundary differs from output");
            Require(ExportDelivery.ReadCompleted(path, 3, runner.VerifiedComparisonBytes) == File.ReadAllText(path + ".for-comparison.txt"), "Verified delivery changed the reports");
        }
        public static void VerifySnapshotAndKey(string path)
        {
            string firstToken;
            using (var audit = new CaptureAudit(path))
            {
                var original = Pair("ORIGINAL"); var capture = audit.Capture(11, original); firstToken = capture.AttendingToken;
                original.Attending = "FINDINGS: MUTATED";
                capture.Pair.Attending = "FINDINGS: ANOTHER MUTATION";
                Require(capture.FormattedText.Contains("attending ORIGINAL") && !capture.FormattedText.Contains("MUTATION") && !capture.FormattedText.Contains("MUTATED"), "Returned capture object was reused during serialization");
            }
            using (var audit = new CaptureAudit(path + ".second")) Require(audit.Capture(11, Pair("ORIGINAL")).AttendingToken != firstToken, "Equality tokens are reused across runs");
        }
        public static void VerifyReadback(string path)
        {
            long verified;
            using (var audit = new CaptureAudit(path + ".checks"))
            using (var file = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.Read))
            using (var writer = new ReplacingWriter(file))
            {
                var first = audit.Capture(11, Pair("FIRST!"));
                verified = audit.WriteVerified("comparison", first, writer, file, first.FormattedText);
                Reject(() => audit.WriteVerified("comparison", first, writer, file, first.FormattedText));
                var second = audit.Capture(12, Pair("SECOND"));
                Reject(() => audit.WriteVerified("comparison", second, writer, file, first.FormattedText));
                Reject(() => audit.WriteVerified("comparison", second, writer, file, second.FormattedText.Replace("SECOND", "FIRST!")));
                writer.Replace = true;
                Reject(() => audit.WriteVerified("comparison", second, writer, file, second.FormattedText));
                Require(file.Length == verified, "Failed record was not rolled back to the verified prefix");
            }
            string saved = File.ReadAllText(path);
            Require(saved == ReportText.Format(11, Pair("FIRST!")), "Previously verified record changed");
            Require(File.ReadAllText(path + ".checks").Contains("comparison-failed,12,"), "Readback failure was not recorded");
        }
        public static void VerifyDeliveryBoundary(string path)
        {
            var runner = new ExportRunner(); runner.Run(new Sequence(), 11, 13, path, CancellationToken.None, m => { });
            string expected = File.ReadAllText(path + ".for-comparison.txt");
            File.AppendAllText(path + ".for-comparison.txt", "UNVERIFIED TAIL");
            Require(ExportDelivery.ReadCompleted(path, 3, runner.VerifiedComparisonBytes) == expected, "Unverified appended data was delivered");
            using (var file = new FileStream(path + ".for-comparison.txt", FileMode.Open, FileAccess.Write)) file.SetLength(runner.VerifiedComparisonBytes - 1);
            Reject(() => ExportDelivery.ReadCompleted(path, 3, runner.VerifiedComparisonBytes));
        }
    }
}
