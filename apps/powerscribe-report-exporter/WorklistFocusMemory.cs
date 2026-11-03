using System;

namespace ReportExporter
{
    // Observe while PowerScribe owns focus, rather than asking it which child
    // used to own focus after Go/Continue has activated the exporter dialog.
    public sealed class WorklistFocusMemory
    {
        private readonly IKeyboardDesktop desktop;
        private readonly object gate = new object();
        private IntPtr main, child;
        public WorklistFocusMemory(IKeyboardDesktop source) { desktop = source; }
        public bool Observe(string mainTitle)
        {
            IntPtr target;
            try { target = desktop.FindWindow(mainTitle, 0); }
            catch (InvalidOperationException) { Clear(); return false; }
            if (target == IntPtr.Zero) { Clear(); return false; }
            lock (gate) { if (main != IntPtr.Zero && main != target) main = child = IntPtr.Zero; }
            try
            {
                if (desktop.Foreground != target || !desktop.VisibleEnabled(target) || desktop.MenuActive(target)) return false;
                return Remember(target, desktop.NavigationFocus(target));
            }
            catch (InvalidOperationException) { return false; }
        }
        public bool Remember(IntPtr window, IntPtr control)
        {
            if (window == IntPtr.Zero || control == IntPtr.Zero || !desktop.IsNavigationControl(window, control)) return false;
            lock (gate) { main = window; child = control; }
            return true;
        }
        public bool TryGet(out IntPtr window, out IntPtr control)
        {
            lock (gate) { window = main; control = child; }
            if (window == IntPtr.Zero || control == IntPtr.Zero || !desktop.VisibleEnabled(window)) return false;
            if (desktop.IsNavigationControl(window, control)) return true;
            lock (gate) { if (main == window && child == control) main = child = IntPtr.Zero; }
            window = control = IntPtr.Zero; return false;
        }
        public void Clear() { lock (gate) main = child = IntPtr.Zero; }
    }
}
