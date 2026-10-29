using System;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Collections.Concurrent;
using System.Collections.Generic;

namespace ReportExporter
{
    public sealed class ReportPair
    {
        // An observed empty attending copy plus a valid resident copy is not proof
        // of signature status. Such records belong only in the archival output.
        public bool AttendingEmptyUnconfirmed;
        public string Attending;
        public string Resident;
        public string Method;
        public long AttendingCopyMs, ResidentCopyMs;
        public int CopyRetries;
        public long ClipboardReadMs, ClipboardReadMaxMs, ClipboardClearMs;
        public int ClipboardLockMisses;
    }
    public interface ISessionTelemetry { int FocusRecoveries { get; } }

    // Only throw after confirming that no comparison exists and the main window is ready.
    public sealed class ComparisonUnavailableException : Exception
    {
        public ComparisonUnavailableException(string message) : base(message) { }
    }

    public interface IReportSession
    {
        bool CanVerifySelectedRow { get; }
        string SelectedCase();
        void OpenComparison(CancellationToken token);
        ReportPair ReadReports(CancellationToken token);
        void CloseComparison(CancellationToken token);
        void Advance(string previousCase, CancellationToken token);
    }

    public static class ReportText
    {
        private static readonly Regex FindingsHeading = new Regex(@"^[\t ]*(?<heading>(?:(?:impressions?|conclusions?)[\t ]*(?:/|&|and|[-\u2013\u2014])[\t ]*)?findings(?:[\t ]*(?:/|&|and|[-\u2013\u2014])[\t ]*(?:impressions?|conclusions?))*)[\t ]*(?::|(?=\r?$))", RegexOptions.IgnoreCase | RegexOptions.Multiline | RegexOptions.CultureInvariant);
        private static readonly Regex OtherHeading = new Regex(@"^[\t ]*(?<heading>impressions?|conclusions?)[\t ]*(?::|(?=\r?$))", RegexOptions.IgnoreCase | RegexOptions.Multiline | RegexOptions.CultureInvariant);
        // Prefer Findings as before, but preserve reports that only have Impression/Conclusion.
        // Match section headings rather than mentions of findings inside patient/history text.
        public static string ExtractBody(string text)
        {
            if (String.IsNullOrWhiteSpace(text)) return null;
            Match match = FindingsHeading.Match(text);
            if (!match.Success) match = OtherHeading.Match(text);
            return !match.Success ? null : text.Substring(match.Groups["heading"].Index).TrimEnd('\0', '\r', '\n', ' ');
        }

        public static string Format(int number, ReportPair pair, bool findingsOnly = false)
        {
            if (pair.AttendingEmptyUnconfirmed)
                throw new InvalidOperationException("An unconfirmed empty attending capture cannot be formatted as a complete pair.");
            string attending = ExtractBody(pair.Attending);
            string resident = ExtractBody(pair.Resident);
            if (attending == null || resident == null)
                throw new InvalidOperationException("Both reports must contain a Findings, Impression, or Conclusion heading. No partial case was saved.");
            if (!findingsOnly)
            {
                attending = pair.Attending.TrimEnd('\0', '\r', '\n', ' ');
                resident = pair.Resident.TrimEnd('\0', '\r', '\n', ' ');
            }
            return "Case " + number.ToString(CultureInfo.InvariantCulture) + "\r\nAttending Report:\r\n" +
                attending + "\r\n\r\nResident Report:\r\n" + resident + "\r\n\r\n";
        }

        public static string FormatUnavailable(int number)
        {
            const string marker = "[REPORT UNAVAILABLE: Compare Report Revisions did not open within the configured wait. Revisions may be unavailable for this case. This is a placeholder, not report text.]";
            return "Case " + number.ToString(CultureInfo.InvariantCulture) + "\r\nAttending Report:\r\n" + marker +
                "\r\n\r\nResident Report:\r\n" + marker + "\r\n\r\n";
        }

        public static string FormatPending(int number, ReportPair pair)
        {
            if (!pair.AttendingEmptyUnconfirmed || !String.IsNullOrWhiteSpace(pair.Attending) || ExtractBody(pair.Resident) == null)
                throw new InvalidOperationException("An empty-attending record requires a validated resident report and no attending text.");
            return "Case " + number.ToString(CultureInfo.InvariantCulture) +
                "\r\nCapture status: POSSIBLY AWAITING ATTENDING — NOT ANALYZED.\r\n" +
                "A fresh empty attending clipboard update was observed. An unsigned report is possible, but capture failure is not ruled out.\r\n" +
                "Attending Report:\r\n[NO ATTENDING TEXT CAPTURED — NOT A REPORT]\r\n\r\nResident Report:\r\n" +
                pair.Resident + "\r\n\r\n";
        }
    }

    public static class ExportDelivery
    {
        public static string ReadCompleted(string path, int completed)
        {
            if (completed <= 0) return null;
            string text = File.ReadAllText(path + ".for-comparison.txt");
            return String.IsNullOrWhiteSpace(text) ? null : text;
        }
        // Called only after a successful run. Copy complete pairs, never archival
        // placeholders/pending records. Injectable writer keeps tests off clipboard.
        public static bool CopyCompleted(string path, int completed, Action<string> copy)
        {
            string text = ReadCompleted(path, completed);
            if (text == null) return false;
            copy(text);
            return true;
        }
    }

    public sealed class AsyncProgressLog : IDisposable
    {
        private readonly BlockingCollection<string> lines = new BlockingCollection<string>();
        private readonly Task writing;
        private volatile bool failed;
        public bool Failed { get { return failed; } }
        public AsyncProgressLog(string path)
        {
            var output = new StreamWriter(new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.Read), new UTF8Encoding(false), 4096);
            writing = Task.Factory.StartNew(() => {
                try
                {
                    while (!lines.IsCompleted)
                    {
                        string line;
                        if (lines.TryTake(out line, 250))
                        {
                            output.WriteLine(line);
                            // Drain a bounded batch, then publish it, on this worker only.
                            int count = 0;
                            while (count++ < 200 && lines.TryTake(out line)) output.WriteLine(line);
                            output.Flush();
                        }
                    }
                }
                catch (IOException) { failed = true; }
                catch (UnauthorizedAccessException) { failed = true; }
                finally { try { output.Dispose(); } catch (IOException) { failed = true; } }
            }, CancellationToken.None, TaskCreationOptions.LongRunning, TaskScheduler.Default);
        }
        public void WriteLine(string line)
        { if (!failed && !lines.IsAddingCompleted) lines.Add(line); }
        public void Dispose()
        { lines.CompleteAdding(); writing.GetAwaiter().GetResult(); lines.Dispose(); }
    }

    public static class CaseCommit
    {
        public static void SaveAndClose(Action save, Action close, Action committed, out long saveMs, out long closeMs)
        {
            long savingDuration = 0;
            Task saving = Task.Factory.StartNew(() => {
                Stopwatch clock = Stopwatch.StartNew(); save(); savingDuration = clock.ElapsedMilliseconds;
            }, CancellationToken.None, TaskCreationOptions.None, TaskScheduler.Default);
            Exception closeError = null;
            Stopwatch closeClock = Stopwatch.StartNew();
            try { close(); } catch (Exception error) { closeError = error; }
            closeMs = closeClock.ElapsedMilliseconds;
            // Always join before any caller can advance/dispose, even on close failure.
            saving.GetAwaiter().GetResult();
            saveMs = savingDuration;
            committed();
            if (closeError != null) throw closeError;
        }
    }

    public sealed class ExportRunner
    {
        private readonly bool findingsOnly;
        public ExportRunner(bool findingsOnly = false) { this.findingsOnly = findingsOnly; }
        public int Completed { get; private set; }
        public int Skipped { get; private set; }
        public int Pending { get; private set; }
        public int? LastAttemptedCase { get; private set; }
        public int? LastSavedCase { get; private set; }
        private readonly List<string> pendingCases = new List<string>();
        private readonly List<string> unavailableCases = new List<string>();
        public int Saved { get { return Completed + Skipped + Pending; } }
        public string OutcomeSummary { get { return "Possibly awaiting attending (capture unconfirmed): " +
            (pendingCases.Count == 0 ? "none" : String.Join(", ", pendingCases.ToArray())) +
            ". Comparison unavailable: " + (unavailableCases.Count == 0 ? "none" : String.Join(", ", unavailableCases.ToArray())) + "."; } }
        public void Run(IReportSession session, int first, int last, string path,
            CancellationToken token, Action<string> progress)
        {
            if (first < 1 || last < first || last > 1000000) throw new ArgumentException("Invalid case range.");
            Completed = Skipped = Pending = 0; pendingCases.Clear(); unavailableCases.Clear();
            LastAttemptedCase = LastSavedCase = null;
            // CreateNew prevents replacing an existing report export.
            using (FileStream file = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.Read))
            using (StreamWriter output = new StreamWriter(file, new UTF8Encoding(true)))
            using (FileStream comparisonFile = new FileStream(path + ".for-comparison.txt", FileMode.CreateNew, FileAccess.Write, FileShare.Read))
            using (StreamWriter comparisonOutput = new StreamWriter(comparisonFile, new UTF8Encoding(true)))
            using (FileStream timingFile = new FileStream(path + ".timings.csv", FileMode.CreateNew, FileAccess.Write, FileShare.Read))
            using (StreamWriter timings = new StreamWriter(timingFile, Encoding.UTF8))
            using (StreamWriter outcomes = new StreamWriter(new FileStream(path + ".outcomes.csv", FileMode.CreateNew, FileAccess.Write, FileShare.Read), Encoding.UTF8))
            {
                // Append-only event ledger: a saved outcome is retained even if close or
                // navigation subsequently fails. Contains source numbers, never report text.
                outcomes.WriteLine("case,event"); outcomes.Flush();
                timings.WriteLine("case,open_ms,capture_ms,save_close_ms,next_ms,read_method,attending_copy_ms,resident_copy_ms,save_ms,close_ms,total_ms,focus_recoveries,copy_retries,clipboard_read_ms,clipboard_read_max_ms,clipboard_clear_ms,clipboard_lock_misses");
                timings.Flush();
                string previous = null;
                for (int number = first; number <= last; number++)
                {
                    token.ThrowIfCancellationRequested();
                    LastAttemptedCase = number;
                    outcomes.WriteLine(number + ",started"); outcomes.Flush();
                    string stage = "selection";
                    try
                    {
                        progress("Case " + number + (session.CanVerifySelectedRow ? ": verifying the selected row..." : ": using the AHK keyboard sequence..."));
                        string selected = session.CanVerifySelectedRow ? session.SelectedCase() : null;
                        if (session.CanVerifySelectedRow && (String.IsNullOrEmpty(selected) || selected == previous))
                            throw new InvalidOperationException("The selected case could not be verified or did not change. Stopped before copying it.");
                        progress("Case " + number + ": waiting for comparison window...");
                        Stopwatch clock = Stopwatch.StartNew();
                        stage = "opening";
                        try { session.OpenComparison(token); }
                        catch (ComparisonUnavailableException)
                        {
                            token.ThrowIfCancellationRequested();
                            long missingOpen = clock.ElapsedMilliseconds;
                            progress("Case " + number + ": comparison likely unavailable; saving a marked placeholder...");
                            output.Write(ReportText.FormatUnavailable(number)); output.Flush(); file.Flush(true); Skipped++; LastSavedCase = number;
                            unavailableCases.Add(number.ToString(CultureInfo.InvariantCulture));
                            outcomes.WriteLine(number + ",comparison_unavailable"); outcomes.Flush();
                            long placeholderSave = clock.ElapsedMilliseconds - missingOpen;
                            stage = "navigation";
                            if (number < last) session.Advance(selected, token);
                            long placeholderNext = clock.ElapsedMilliseconds - missingOpen - placeholderSave;
                            timings.WriteLine(number + "," + missingOpen + ",0," + placeholderSave + "," + placeholderNext +
                                ",comparison-unavailable,0,0," + placeholderSave + ",0," + clock.ElapsedMilliseconds + "," +
                                (session is ISessionTelemetry ? ((ISessionTelemetry)session).FocusRecoveries : 0) + ",0,0,0,0,0");
                            timings.Flush(); previous = selected;
                            continue;
                        }
                        long open = clock.ElapsedMilliseconds;
                        progress("Case " + number + ": comparison is open; reading both reports...");
                        stage = "capture";
                        ReportPair pair = session.ReadReports(token);
                        bool pending = pair.AttendingEmptyUnconfirmed;
                        string formatted = pending ? ReportText.FormatPending(number, pair) : ReportText.Format(number, pair, findingsOnly);
                        if (session.CanVerifySelectedRow && session.SelectedCase() != selected)
                            throw new InvalidOperationException("The selected case changed during capture. No pair was saved.");
                        long capture = clock.ElapsedMilliseconds - open;
                        token.ThrowIfCancellationRequested();
                        progress("Case " + number + (pending ? ": possibly awaiting attending; saving resident text to archive only, not comparison output..." : ": saving the complete pair while closing the comparison..."));
                        // Report strings are captured and validated before concurrent work starts.
                        // No UI/clipboard operations run on the saving worker. Join before advancing
                        // or disposing streams, including close errors and cancellation.
                        long saveMs, closeMs;
                        stage = "save_or_close";
                        CaseCommit.SaveAndClose(() => { output.Write(formatted); output.Flush(); file.Flush(true);
                                if (!pending) { comparisonOutput.Write(formatted); comparisonOutput.Flush(); comparisonFile.Flush(true); } },
                            () => session.CloseComparison(token), () => {
                                if (pending) { Pending++; pendingCases.Add(number.ToString(CultureInfo.InvariantCulture)); } else Completed++;
                                LastSavedCase = number;
                                outcomes.WriteLine(number + (pending ? ",pending_suspected" : ",complete")); outcomes.Flush();
                            }, out saveMs, out closeMs);
                        long close = clock.ElapsedMilliseconds - open - capture;
                        long next = 0;
                        if (number < last)
                        {
                            progress("Case " + number + " saved; moving to the next case...");
                            stage = "navigation";
                            session.Advance(selected, token);
                            next = clock.ElapsedMilliseconds - open - capture - close;
                        }
                        timings.WriteLine(String.Join(",", new string[] {
                            number.ToString(CultureInfo.InvariantCulture), open.ToString(), capture.ToString(),
                            close.ToString(), next.ToString(), pair.Method ?? "unknown", pair.AttendingCopyMs.ToString(),
                            pair.ResidentCopyMs.ToString(), saveMs.ToString(), closeMs.ToString(), clock.ElapsedMilliseconds.ToString(),
                            session is ISessionTelemetry ? ((ISessionTelemetry)session).FocusRecoveries.ToString() : "0", pair.CopyRetries.ToString(),
                            pair.ClipboardReadMs.ToString(), pair.ClipboardReadMaxMs.ToString(), pair.ClipboardClearMs.ToString(), pair.ClipboardLockMisses.ToString() }));
                        timings.Flush();
                        previous = selected;
                    }
                    catch (OperationCanceledException)
                    { outcomes.WriteLine(number + ",cancelled_" + stage); outcomes.Flush(); throw; }
                    catch (Exception)
                    { outcomes.WriteLine(number + ",stopped_" + stage); outcomes.Flush(); throw; }
                }
                progress(OutcomeSummary);
            }
        }
    }

    public static class ReadyWait
    {
        // Check before waiting, including when the previous operation already made the control ready.
        public static void Until(Func<bool> ready, int timeoutMs, int pollMs, CancellationToken token, string message)
        {
            Stopwatch clock = Stopwatch.StartNew();
            while (true)
            {
                token.ThrowIfCancellationRequested();
                if (ready()) return;
                if (clock.ElapsedMilliseconds >= timeoutMs) throw new TimeoutException(message);
                int remaining = Math.Max(1, timeoutMs - (int)clock.ElapsedMilliseconds);
                if (token.WaitHandle.WaitOne(Math.Min(pollMs, remaining))) token.ThrowIfCancellationRequested();
            }
        }
    }
}
