using System;
using System.Runtime.InteropServices;
using System.Text;

namespace ReportExporter
{
    public interface IClipboardAccess
    {
        bool Open();
        bool Empty();
        void Close();
        bool HasFormat(uint format);
        IntPtr Data(uint format);
        ulong Size(IntPtr data);
        IntPtr Lock(IntPtr data);
        void Unlock(IntPtr data);
    }

    public sealed class WindowsClipboardAccess : IClipboardAccess
    {
        [DllImport("user32.dll")] private static extern bool OpenClipboard(IntPtr window);
        [DllImport("user32.dll")] private static extern bool EmptyClipboard();
        [DllImport("user32.dll")] private static extern bool CloseClipboard();
        [DllImport("user32.dll")] private static extern bool IsClipboardFormatAvailable(uint format);
        [DllImport("user32.dll")] private static extern IntPtr GetClipboardData(uint format);
        [DllImport("kernel32.dll")] private static extern UIntPtr GlobalSize(IntPtr data);
        [DllImport("kernel32.dll")] private static extern IntPtr GlobalLock(IntPtr data);
        [DllImport("kernel32.dll")] private static extern bool GlobalUnlock(IntPtr data);
        public bool Open() { return OpenClipboard(IntPtr.Zero); }
        public bool Empty() { return EmptyClipboard(); }
        public void Close() { CloseClipboard(); }
        public bool HasFormat(uint format) { return IsClipboardFormatAvailable(format); }
        public IntPtr Data(uint format) { return GetClipboardData(format); }
        public ulong Size(IntPtr data) { return GlobalSize(data).ToUInt64(); }
        public IntPtr Lock(IntPtr data) { return GlobalLock(data); }
        public void Unlock(IntPtr data) { GlobalUnlock(data); }
    }

    public sealed class NativeClipboard
    {
        public const int MaximumBytes = 8 * 1024 * 1024;
        private readonly IClipboardAccess access;
        private static readonly Encoding StrictUnicode = new UnicodeEncoding(false, false, true);
        public NativeClipboard(IClipboardAccess access) { this.access = access; }
        // One attempt only. The session's readiness loop owns retry timing and cancellation.
        public bool Clear()
        {
            if (!access.Open()) return false;
            try { return access.Empty(); }
            finally { access.Close(); }
        }
        public bool Read(out string text)
        {
            text = null;
            if (!access.Open()) return false;
            try
            {
                // Requesting data also triggers delayed rendering; do not wait for sequence first.
                bool unicodeReadable = true;
                if (access.HasFormat(13))
                {
                    unicodeReadable = ReadFormat(13, true, out text); // CF_UNICODETEXT
                    if (unicodeReadable && !String.IsNullOrEmpty(text)) return true;
                }
                if (access.HasFormat(1)) return ReadFormat(1, false, out text); // CF_TEXT
                return unicodeReadable; // Clipboard was readable but text is not present yet.
            }
            finally { access.Close(); }
        }
        private bool ReadFormat(uint format, bool unicode, out string text)
        {
            text = null;
            IntPtr data = access.Data(format);
            if (data == IntPtr.Zero) return false;
            ulong size = access.Size(data);
            if (size == 0 || size > MaximumBytes) return false;
            IntPtr memory = access.Lock(data);
            if (memory == IntPtr.Zero) return false;
            try
            {
                byte[] bytes = new byte[(int)size];
                Marshal.Copy(memory, bytes, 0, bytes.Length);
                return Decode(bytes, unicode, out text);
            }
            finally { access.Unlock(data); }
        }
        public static bool Decode(byte[] bytes, bool unicode, out string text)
        {
            text = null;
            if (bytes == null || bytes.Length == 0 || bytes.Length > MaximumBytes) return false;
            int end = -1;
            if (unicode)
            {
                for (int index = 0; index + 1 < bytes.Length; index += 2)
                    if (bytes[index] == 0 && bytes[index + 1] == 0) { end = index; break; }
            }
            else end = Array.IndexOf(bytes, (byte)0);
            if (end < 0) return false; // Never silently accept an unterminated/truncated report.
            try { text = (unicode ? StrictUnicode : Encoding.Default).GetString(bytes, 0, end); return true; }
            catch (DecoderFallbackException) { return false; }
        }
    }
}
