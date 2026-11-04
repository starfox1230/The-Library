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
    public interface ISameStudyRestart { IReportSession RestartForSameStudy(); }

    public enum RecoveryChoice { Stop, Continue, AcceptLinkedStudies, RetryCapture }

    public sealed class RecoveryRequest
    {
        public readonly int CaseNumber, LastCase;
        public readonly int? LastSavedCase, RepeatedFromCase;
        public readonly string Reason;
        public bool FinishOnly { get { return CaseNumber > LastCase; } }
        public RecoveryRequest(int number, int last, int? saved, string reason, int? repeatedFrom = null)
        { CaseNumber = number; LastCase = last; LastSavedCase = saved; Reason = reason; RepeatedFromCase = repeatedFrom; }
    }

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
        public static string ReadCompleted(string path, int completed, long? verifiedBytes = null)
        {
            if (completed <= 0) return null;
            string text;
            if (verifiedBytes.HasValue)
            {
                if (verifiedBytes.Value < 0 || verifiedBytes.Value > Int32.MaxValue) throw new IOException("Invalid verified comparison length.");
                using (var file = new FileStream(path + ".for-comparison.txt", FileMode.Open, FileAccess.Read, FileShare.Read))
                {
                    if (file.Length < verifiedBytes.Value) throw new IOException("The verified comparison file is incomplete.");
                    byte[] bytes = new byte[(int)verifiedBytes.Value]; int offset = 0;
                    while (offset < bytes.Length) { int count = file.Read(bytes, offset, bytes.Length - offset); if (count == 0) throw new IOException("The verified comparison file ended early."); offset += count; }
                    using (var reader = new StreamReader(new MemoryStream(bytes), Encoding.UTF8, true)) text = reader.ReadToEnd();
                }
            }
            else text = File.ReadAllText(path + ".for-comparison.txt");
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
        public Func<RecoveryRequest, CancellationToken, RecoveryChoice> Recovery;
        public Func<IReportSession> RestartSession;
        private readonly bool findingsOnly;
        public ExportRunner(bool findingsOnly = false) { this.findingsOnly = findingsOnly; }
        public int Completed { get; private set; }
        public int Skipped { get; private set; }
        public int Pending { get; private set; }
        public int? LastAttemptedCase { get; private set; }
        public int? LastSavedCase { get; private set; }
        public long VerifiedComparisonBytes { get; private set; }
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
            LastAttemptedCase = LastSavedCase = null; VerifiedComparisonBytes = 0;
            // CreateNew prevents replacing an existing report export.
            using (FileStream file = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.Read))
            using (StreamWriter output = new StreamWriter(file, new UTF8Encoding(true)))
            using (FileStream comparisonFile = new FileStream(path + ".for-comparison.txt", FileMode.CreateNew, FileAccess.Write, FileShare.Read))
            using (StreamWriter comparisonOutput = new StreamWriter(comparisonFile, new UTF8Encoding(true)))
            using (FileStream timingFile = new FileStream(path + ".timings.csv", FileMode.CreateNew, FileAccess.Write, FileShare.Read))
            using (StreamWriter timings = new StreamWriter(timingFile, Encoding.UTF8))
            using (StreamWriter outcomes = new StreamWriter(new FileStream(path + ".outcomes.csv", FileMode.CreateNew, FileAccess.Write, FileShare.Read), Encoding.UTF8))
            using (var captureAudit = new CaptureAudit(path + ".capture-checks.csv"))
            {
                // Append-only event ledger: a saved outcome is retained even if close or
                // navigation subsequently fails. Contains source numbers, never report text.
                outcomes.WriteLine("case,event"); outcomes.Flush();
                timings.WriteLine("case,open_ms,capture_ms,save_close_ms,next_ms,read_method,attending_copy_ms,resident_copy_ms,save_ms,close_ms,total_ms,focus_recoveries,copy_retries,clipboard_read_ms,clipboard_read_max_ms,clipboard_clear_ms,clipboard_lock_misses");
                timings.Flush();
                string previous = null;
                ReportPair firstPair = null;
                int firstPairNumber = 0;
                var reopenedCases = new HashSet<int>();
                for (int number = first; number <= last; number++)
                {
                    token.ThrowIfCancellationRequested();
                    LastAttemptedCase = number;
                    outcomes.WriteLine(number + ",started"); outcomes.Flush();
                    string stage = "selection";
                    try
                    {
                        if (session == null)
                        {
                            if (RestartSession == null) throw new InvalidOperationException("No capture session is available.");
                            session = RestartSession();
                        }
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
                        CapturedPair captured = captureAudit.Capture(number, session.ReadReports(token), findingsOnly);
                        ReportPair pair = captured.Pair;
                        if (Completed == 1 && number == firstPairNumber + 1 && SamePair(firstPair, pair) && reopenedCases.Add(number))
                        {
                            // Match the recovery demonstrated on the workstation: close
                            // the comparison, create a fresh session, reopen the SAME
                            // selected study. Never Advance or commit the suspect pair.
                            outcomes.WriteLine(number + ",same_case_reopen_started"); outcomes.Flush();
                            progress("Case " + number + ": the previous pair repeated; closing and reopening this SAME study once. No Down or case change...");
                            session.CloseComparison(token);
                            if (token.WaitHandle.WaitOne(1000)) token.ThrowIfCancellationRequested();
                            if (session.CanVerifySelectedRow && session.SelectedCase() != selected)
                                throw new InvalidOperationException("The selected study changed before the same-case retry. No repeated pair was saved.");
                            var retained = session as ISameStudyRestart;
                            if (retained != null) session = retained.RestartForSameStudy();
                            else if (RestartSession != null) session = RestartSession();
                            if (session.CanVerifySelectedRow && session.SelectedCase() != selected)
                                throw new InvalidOperationException("The selected study changed while restarting the same-case retry. No repeated pair was saved.");
                            try { session.OpenComparison(token); }
                            catch (ComparisonUnavailableException error)
                            { throw new InvalidOperationException("The same-case comparison could not be reopened. No repeated pair was saved.", error); }
                            captured = captureAudit.Capture(number, session.ReadReports(token), findingsOnly);
                            pair = captured.Pair;
                            bool repeated = SamePair(firstPair, pair);
                            outcomes.WriteLine(number + (repeated ? ",same_case_reopen_still_matching" : ",same_case_reopen_resolved")); outcomes.Flush();
                            progress("Case " + number + (repeated ? ": the reopened reports still match; verification is needed before saving." : ": fresh reports captured after same-case reopen; continuing."));
                        }
                        // An independently updated clipboard can still contain PowerScribe's
                        // previously loaded report. Never silently relabel that first repeat.
                        bool reselect = false;
                        while (Completed == 1 && number == firstPairNumber + 1 && SamePair(firstPair, pair))
                        {
                            if (Recovery == null) throw new InvalidOperationException("The first report pair repeated after advancing. Verify the next study before exporting it under another case number.");
                            outcomes.WriteLine(number + ",paused_first_pair_repeat"); outcomes.Flush();
                            var request = new RecoveryRequest(number, last, LastSavedCase,
                                "The comparison was closed and reopened once without moving the worklist, but its captured text still matches case " + firstPairNumber + ". This checks captured text, not the identity of the study on screen. If the open reports are different, choose Retry open reports. Nothing from this case has been saved yet.", firstPairNumber);
                            RecoveryChoice choice = Recovery(request, token); token.ThrowIfCancellationRequested();
                            if (choice == RecoveryChoice.Stop) throw new OperationCanceledException("Stopped while checking the repeated first pair.", token);
                            if (choice == RecoveryChoice.Continue)
                            {
                                if (RestartSession == null) throw new InvalidOperationException("A fresh capture session is required to continue.");
                                session = null; previous = null; reselect = true; break;
                            }
                            if (choice == RecoveryChoice.RetryCapture)
                            {
                                progress("Case " + number + ": retrying the open comparison without reopening or moving the worklist...");
                                captured = captureAudit.Capture(number, session.ReadReports(token), findingsOnly);
                                pair = captured.Pair; continue;
                            }
                            if (choice != RecoveryChoice.AcceptLinkedStudies) throw new InvalidOperationException("Invalid recovery choice.");
                            outcomes.WriteLine(number + ",distinct_linked_studies_confirmed"); outcomes.Flush();
                            break;
                        }
                        if (reselect) { number--; continue; }
                        bool pending = pair.AttendingEmptyUnconfirmed;
                        string formatted = captured.FormattedText;
                        if (session.CanVerifySelectedRow && session.SelectedCase() != selected)
                            throw new InvalidOperationException("The selected case changed during capture. No pair was saved.");
                        long capture = clock.ElapsedMilliseconds - open;
                        token.ThrowIfCancellationRequested();
                        progress("Case " + number + (pending ? ": possibly awaiting attending; saving resident text to archive only, not comparison output..." : ": saving the complete pair while closing the comparison..."));
                        // Report strings are captured and validated before concurrent work starts.
                        // No UI/clipboard operations run on the saving worker. Join before advancing
                        // or disposing streams, including close errors and cancellation.
                        long saveMs, closeMs, comparisonEnd = VerifiedComparisonBytes;
                        stage = "save_or_close";
                        CaseCommit.SaveAndClose(() => { captureAudit.WriteVerified("archive", captured, output, file, formatted);
                                if (!pending) comparisonEnd = captureAudit.WriteVerified("comparison", captured, comparisonOutput, comparisonFile, formatted); },
                            () => session.CloseComparison(token), () => {
                                if (pending) { Pending++; pendingCases.Add(number.ToString(CultureInfo.InvariantCulture)); } else Completed++;
                                LastSavedCase = number;
                                VerifiedComparisonBytes = comparisonEnd;
                                if (!pending && firstPair == null) { firstPair = pair; firstPairNumber = number; }
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
                    catch (Exception error)
                    {
                        // A saved pair must never be appended a second time after a close
                        // or navigation timeout. Disk/save failures are not retried here.
                        if (Recovery != null && RestartSession != null && (stage != "save_or_close" || LastSavedCase == number) &&
                                (error is TimeoutException || error is InvalidOperationException))
                        {
                            int next = LastSavedCase.HasValue && LastSavedCase.Value >= number ? LastSavedCase.Value + 1 : number;
                            outcomes.WriteLine(number + ",paused_" + stage); outcomes.Flush();
                            progress("Paused. Saved reports are kept; waiting for study selection and Continue.");
                            var choice = Recovery(new RecoveryRequest(next, last, LastSavedCase, error.Message), token);
                            token.ThrowIfCancellationRequested();
                            if (choice != RecoveryChoice.Continue) throw new OperationCanceledException("Stopped during recovery.", token);
                            session = null; previous = null; number = next - 1;
                            outcomes.WriteLine(next + ",manual_recovery"); outcomes.Flush();
                            continue;
                        }
                        outcomes.WriteLine(number + ",stopped_" + stage); outcomes.Flush(); throw;
                    }
                }
                progress(OutcomeSummary);
            }
        }

        private static bool SamePair(ReportPair first, ReportPair next)
        {
            return first != null && next != null && !first.AttendingEmptyUnconfirmed && !next.AttendingEmptyUnconfirmed &&
                String.Equals(first.Attending, next.Attending, StringComparison.Ordinal) &&
                String.Equals(first.Resident, next.Resident, StringComparison.Ordinal);
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
