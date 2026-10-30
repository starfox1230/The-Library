// Windows WASAPI shared-mode output capture. Built with the Windows .NET compiler.
// Analysis only: no audio files, microphone input, network, or playback changes.
using System;
using System.Globalization;
using System.Runtime.InteropServices;
using System.Threading;

[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class Enumerator { }
[ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IDevices {
    void EnumAudioEndpoints(int flow, uint mask, out IntPtr devices);
    void GetDefaultAudioEndpoint(int flow, int role, out IDevice device);
    void GetDevice([MarshalAs(UnmanagedType.LPWStr)] string id, out IDevice device);
    void RegisterEndpointNotificationCallback(IntPtr callback);
    void UnregisterEndpointNotificationCallback(IntPtr callback);
}
[ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IDevice {
    void Activate(ref Guid id, uint context, IntPtr parameters, [MarshalAs(UnmanagedType.IUnknown)] out object result);
    void OpenPropertyStore(uint access, out IntPtr store);
    void GetId([MarshalAs(UnmanagedType.LPWStr)] out string id);
    void GetState(out uint state);
}
[ComImport, Guid("1CB9AD4C-DBFA-4C32-B178-C2F568A703B2"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IClient {
    void Initialize(int mode, uint flags, long duration, long periodicity, IntPtr format, IntPtr session);
    void GetBufferSize(out uint size);
    void GetStreamLatency(out long latency);
    void GetCurrentPadding(out uint padding);
    [PreserveSig] int IsFormatSupported(int mode, IntPtr format, out IntPtr closest);
    void GetMixFormat(out IntPtr format);
    void GetDevicePeriod(out long normal, out long minimum);
    void Start(); void Stop(); void Reset(); void SetEventHandle(IntPtr handle);
    void GetService(ref Guid id, [MarshalAs(UnmanagedType.IUnknown)] out object service);
}
[ComImport, Guid("C8ADBD64-E71E-48A0-A4DE-185C395CD317"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface ICapture {
    void GetBuffer(out IntPtr data, out uint frames, out uint flags, out ulong position, out ulong qpc);
    void ReleaseBuffer(uint frames);
    void GetNextPacketSize(out uint frames);
}
class Loopback {
    static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
    static string F(double x) { return x.ToString("0.000000", Inv); }
    [MTAThread] static int Main() {
        try { Run(); return 0; }
        catch (Exception e) {
            Console.WriteLine("{\"error\":\"Windows audio unavailable (" + e.HResult.ToString("X") + "). Retrying.\"}");
            return 1;
        }
    }
    static void Run() {
        IDevices devices = (IDevices)new Enumerator();
        IDevice device; devices.GetDefaultAudioEndpoint(0, 0, out device);
        string original; device.GetId(out original);
        Guid clientId = typeof(IClient).GUID; object raw;
        device.Activate(ref clientId, 23, IntPtr.Zero, out raw);
        IClient client = (IClient)raw;
        IntPtr format; client.GetMixFormat(out format);
        int tag = (ushort)Marshal.ReadInt16(format, 0);
        int channels = (ushort)Marshal.ReadInt16(format, 2);
        int rate = Marshal.ReadInt32(format, 4);
        int align = (ushort)Marshal.ReadInt16(format, 12);
        int bits = (ushort)Marshal.ReadInt16(format, 14);
        if (tag == 65534) tag = Marshal.ReadInt32(format, 24); // subformat PCM/float
        if (!((tag == 3 && bits == 32) || (tag == 1 && (bits == 16 || bits == 24 || bits == 32))))
            throw new NotSupportedException("Output format");
        try { client.Initialize(0, 0x20000, 1000000, 0, format, IntPtr.Zero); }
        finally { Marshal.FreeCoTaskMem(format); }
        Guid captureId = typeof(ICapture).GUID; object service;
        client.GetService(ref captureId, out service); ICapture capture = (ICapture)service;
        double low = 0, energy = 0, bass = 0, alpha = 1 - Math.Exp(-2 * Math.PI * 160 / rate);
        int samples = 0, window = rate / 50;
        DateTime check = DateTime.UtcNow, emit = DateTime.UtcNow;
        byte[] bytes = new byte[0];
        client.Start();
        try {
            while (true) {
                uint pending; capture.GetNextPacketSize(out pending);
                while (pending > 0) {
                    IntPtr data; uint count, flags; ulong pos, qpc;
                    capture.GetBuffer(out data, out count, out flags, out pos, out qpc);
                    try {
                        int size = checked((int)count * align);
                        if (bytes.Length < size) bytes = new byte[size];
                        bool silent = (flags & 2) != 0;
                        if (!silent) Marshal.Copy(data, bytes, 0, size);
                        for (int frame = 0; frame < count; frame++) {
                            double sample = 0;
                            if (!silent) for (int c = 0; c < channels; c++) {
                                int i = frame * align + c * (bits / 8);
                                if (tag == 3) sample += BitConverter.ToSingle(bytes, i);
                                else if (bits == 16) sample += BitConverter.ToInt16(bytes, i) / 32768.0;
                                else if (bits == 32) sample += BitConverter.ToInt32(bytes, i) / 2147483648.0;
                                else sample += ((bytes[i] | bytes[i+1] << 8 | bytes[i+2] << 16) << 8) / 2147483648.0;
                            }
                            sample /= channels;
                            if (Double.IsNaN(sample) || Double.IsInfinity(sample)) sample = 0;
                            low += alpha * (sample - low);
                            energy += sample * sample; bass += low * low; samples++;
                            if (samples >= window) {
                                Console.WriteLine("{\"energy\":" + F(Math.Sqrt(energy / samples)) + ",\"bass\":" + F(Math.Sqrt(bass / samples)) + "}");
                                energy = bass = 0; samples = 0; emit = DateTime.UtcNow;
                            }
                        }
                    } finally { capture.ReleaseBuffer(count); }
                    capture.GetNextPacketSize(out pending);
                }
                if ((DateTime.UtcNow - emit).TotalMilliseconds > 100) {
                    Console.WriteLine("{\"energy\":0,\"bass\":0}"); emit = DateTime.UtcNow;
                }
                if ((DateTime.UtcNow - check).TotalSeconds > 2) {
                    IDevice current; devices.GetDefaultAudioEndpoint(0, 0, out current);
                    string id; current.GetId(out id); Marshal.ReleaseComObject(current);
                    if (id != original) return; // Python restarts against the new device.
                    check = DateTime.UtcNow;
                }
                Thread.Sleep(5);
            }
        } finally { client.Stop(); }
    }
}
