using System;
using System.IO;
using System.Text;
using System.Security.Cryptography;
using System.Collections.Generic;

namespace ReportExporter
{
    public sealed class CapturedPair
    {
        public readonly int Number, CaptureId;
        private readonly ReportPair pair;
        public ReportPair Pair { get { return Copy(pair); } }
        public readonly string FormattedText;
        public readonly string AttendingToken, ResidentToken;
        internal CapturedPair(int number, int id, ReportPair source, string attending, string resident, bool findingsOnly)
        {
            Number = number; CaptureId = id; pair = source; AttendingToken = attending; ResidentToken = resident;
            FormattedText = source.AttendingEmptyUnconfirmed ? ReportText.FormatPending(number, source) : ReportText.Format(number, source, findingsOnly);
        }
        internal static ReportPair Copy(ReportPair source)
        {
            return new ReportPair { Attending = source.Attending, Resident = source.Resident,
                AttendingEmptyUnconfirmed = source.AttendingEmptyUnconfirmed, Method = source.Method,
                AttendingCopyMs = source.AttendingCopyMs, ResidentCopyMs = source.ResidentCopyMs,
                CopyRetries = source.CopyRetries, ClipboardReadMs = source.ClipboardReadMs,
                ClipboardReadMaxMs = source.ClipboardReadMaxMs, ClipboardClearMs = source.ClipboardClearMs,
                ClipboardLockMisses = source.ClipboardLockMisses };
        }
    }

    // This ledger contains only source labels, attempt IDs, lengths and opaque
    // within-run equality tokens. The random HMAC key is never persisted.
    public sealed class CaptureAudit : IDisposable
    {
        private readonly HMACSHA256 hmac = new HMACSHA256();
        private readonly StreamWriter log;
        private readonly HashSet<string> saved = new HashSet<string>();
        private int nextId;
        public CaptureAudit(string path)
        {
            log = new StreamWriter(new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.Read), new UTF8Encoding(false));
            log.WriteLine("stage,case,capture_id,attending_token,resident_token,record_token,bytes"); log.Flush();
        }
        private string Token(string kind, string text)
        {
            byte[] bytes = hmac.ComputeHash(Encoding.UTF8.GetBytes(kind + "\0" + (text ?? "")));
            return BitConverter.ToString(bytes, 0, 16).Replace("-", "").ToLowerInvariant();
        }
        public CapturedPair Capture(int number, ReportPair source, bool findingsOnly = false)
        {
            // Copy the returned values before formatting, saving or closing the UI.
            var pair = CapturedPair.Copy(source);
            var capture = new CapturedPair(number, ++nextId, pair, Token("attending", pair.Attending), Token("resident", pair.Resident), findingsOnly);
            Record("captured", capture, "", 0); return capture;
        }
        private void Record(string stage, CapturedPair capture, string record, int bytes)
        {
            log.WriteLine(stage + "," + capture.Number + "," + capture.CaptureId + "," + capture.AttendingToken + "," + capture.ResidentToken + "," + record + "," + bytes); log.Flush();
        }
        public long WriteVerified(string target, CapturedPair capture, StreamWriter writer, FileStream file, string text)
        {
            string key = target + ":" + capture.Number;
            if (!String.Equals(text, capture.FormattedText, StringComparison.Ordinal)) throw new IOException("Serialized record differs from its captured source pair or label.");
            if (!saved.Add(key)) throw new IOException("A second save of the same source case was blocked. Check the capture-checks log.");
            // Flush the UTF-8 preamble before locating this exact record.
            writer.Flush(); long start = file.Position;
            byte[] expected = writer.Encoding.GetBytes(text);
            try
            {
                writer.Write(text); writer.Flush(); file.Flush(true);
                if (file.Position - start != expected.Length) throw new IOException("Saved record length differs from its capture.");
                using (var reading = new FileStream(file.Name, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                {
                    reading.Position = start; byte[] buffer = new byte[16384]; int offset = 0;
                    while (offset < expected.Length)
                    {
                        int count = reading.Read(buffer, 0, Math.Min(buffer.Length, expected.Length - offset));
                        if (count == 0) throw new IOException("Saved record ended before its capture.");
                        for (int i = 0; i < count; i++) if (buffer[i] != expected[offset + i]) throw new IOException("Saved record differs from its capture.");
                        offset += count;
                    }
                }
                Record(target + "-verified", capture, Token("record", text), expected.Length);
                return file.Position;
            }
            catch
            {
                // Retain earlier verified records if a save/readback fails. Delivery
                // is separately limited to the last committed verified byte offset.
                try { writer.Flush(); file.SetLength(start); file.Position = start; file.Flush(true); } catch { }
                Record(target + "-failed", capture, "", 0); throw;
            }
        }
        public void Dispose() { try { log.Dispose(); } finally { hmac.Dispose(); } }
    }
}
