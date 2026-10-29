using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Runtime.InteropServices;
using System.Windows.Forms;

namespace ReportExporter
{
    // Presentation only: no input hooks, settings, report parsing, or clipboard access.
    public static class NightTheme
    {
        public static readonly Color Canvas = Color.FromArgb(16, 21, 29);
        public static readonly Color Surface = Color.FromArgb(25, 32, 43);
        public static readonly Color Input = Color.FromArgb(33, 43, 56);
        public static readonly Color Border = Color.FromArgb(53, 66, 83);
        public static readonly Color Ink = Color.FromArgb(232, 239, 248);
        public static readonly Color Muted = Color.FromArgb(163, 178, 198);
        public static readonly Color Accent = Color.FromArgb(107, 218, 204);

        [DllImport("dwmapi.dll")] private static extern int DwmSetWindowAttribute(IntPtr window, int attribute, ref int value, int size);
        public static void TitleBar(Form form)
        {
            try { int enabled = 1; DwmSetWindowAttribute(form.Handle, 20, ref enabled, sizeof(int)); }
            catch (DllNotFoundException) { }
            catch (EntryPointNotFoundException) { }
        }
        public static GraphicsPath Rounded(Rectangle bounds, int radius)
        {
            var path = new GraphicsPath();
            int diameter = Math.Min(radius * 2, Math.Min(bounds.Width, bounds.Height));
            if (diameter <= 0) { path.AddRectangle(bounds); return path; }
            path.AddArc(bounds.Left, bounds.Top, diameter, diameter, 180, 90);
            path.AddArc(bounds.Right - diameter, bounds.Top, diameter, diameter, 270, 90);
            path.AddArc(bounds.Right - diameter, bounds.Bottom - diameter, diameter, diameter, 0, 90);
            path.AddArc(bounds.Left, bounds.Bottom - diameter, diameter, diameter, 90, 90);
            path.CloseFigure(); return path;
        }
        public static void Apply(Control root)
        {
            if (root is Form) { root.BackColor = Canvas; root.ForeColor = Ink; }
            else if (root is Label)
            {
                root.ForeColor = root.ForeColor == Color.DimGray ? Muted : Ink;
                root.BackColor = root.Parent == null ? Canvas : root.Parent.BackColor;
            }
            else if (root is TextBox)
            {
                root.BackColor = Input; root.ForeColor = Ink;
                ((TextBox)root).BorderStyle = BorderStyle.FixedSingle;
            }
            else if (root is NumericUpDown)
            {
                root.BackColor = Input; root.ForeColor = Ink;
                ((NumericUpDown)root).BorderStyle = BorderStyle.FixedSingle;
            }
            else if (root is ComboBox)
            {
                var combo = (ComboBox)root;
                combo.BackColor = Input; combo.ForeColor = Ink; combo.FlatStyle = FlatStyle.Flat;
            }
            else if (root is CheckBox)
            {
                var check = (CheckBox)root;
                check.UseVisualStyleBackColor = false; check.FlatStyle = FlatStyle.Flat;
                check.BackColor = check.Parent.BackColor; check.ForeColor = Ink;
                check.Padding = new Padding(0, 4, 0, 4);
            }
            else if (root is FlowLayoutPanel || root is TableLayoutPanel)
            { root.BackColor = root.Name == "OptionsPanel" || root.Name == "CopiedTextPanel" ? Surface : root.Parent == null ? Canvas : root.Parent.BackColor; root.ForeColor = Ink; }
            else if (root is Panel)
            { root.ForeColor = Ink; }
            foreach (Control child in root.Controls)
            {
                // NumericUpDown's native edit/spin children inherit their own colors.
                if (root is NumericUpDown) { child.BackColor = Input; child.ForeColor = Ink; }
                else Apply(child);
            }
        }
    }

    public sealed class NightComboBox : ComboBox
    {
        public NightComboBox() { DrawMode = DrawMode.OwnerDrawFixed; FlatStyle = FlatStyle.Flat; }
        protected override void OnDrawItem(DrawItemEventArgs args)
        {
            if (args.Index < 0) return;
            using (var brush = new SolidBrush((args.State & DrawItemState.Selected) != 0 ? NightTheme.Border : NightTheme.Input))
                args.Graphics.FillRectangle(brush, args.Bounds);
            TextRenderer.DrawText(args.Graphics, GetItemText(Items[args.Index]), Font, args.Bounds, NightTheme.Ink, TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.SingleLine);
            if ((args.State & DrawItemState.Focus) != 0) args.DrawFocusRectangle();
        }
    }

    public sealed class NightPanel : Panel
    {
        public int CornerRadius = 12;
        public bool Outline = true;
        public NightPanel()
        {
            DoubleBuffered = true; BackColor = NightTheme.Surface;
            SetStyle(ControlStyles.ResizeRedraw, true);
        }
        protected override void OnPaintBackground(PaintEventArgs args)
        {
            args.Graphics.Clear(Parent == null ? NightTheme.Canvas : Parent.BackColor);
            if (Width < 2 || Height < 2) return;
            args.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
            using (var path = NightTheme.Rounded(new Rectangle(0, 0, Width - 1, Height - 1), CornerRadius))
            using (var brush = new SolidBrush(BackColor))
            using (var pen = new Pen(NightTheme.Border))
            { args.Graphics.FillPath(brush, path); if (Outline) args.Graphics.DrawPath(pen, path); }
        }
    }

    public sealed class NightButton : Button
    {
        public bool Primary;
        public bool Disclosure;
        public bool Expanded;
        private bool hovered;
        private bool pressed;
        public NightButton()
        {
            FlatStyle = FlatStyle.Flat; FlatAppearance.BorderSize = 0;
            BackColor = NightTheme.Surface; ForeColor = NightTheme.Ink;
            Padding = new Padding(12, 5, 12, 5); MinimumSize = new Size(0, 34);
            Margin = new Padding(3, 3, 7, 5);
            SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
        }
        public override Size GetPreferredSize(Size proposed)
        {
            var text = TextRenderer.MeasureText(Text, Font);
            return new Size(Math.Max(MinimumSize.Width, text.Width + Padding.Horizontal + (Disclosure ? 32 : 4)), Math.Max(MinimumSize.Height, text.Height + Padding.Vertical + 4));
        }
        protected override void OnMouseEnter(EventArgs args) { hovered = true; Invalidate(); base.OnMouseEnter(args); }
        protected override void OnMouseLeave(EventArgs args) { hovered = pressed = false; Invalidate(); base.OnMouseLeave(args); }
        protected override void OnMouseDown(MouseEventArgs args) { pressed = true; Invalidate(); base.OnMouseDown(args); }
        protected override void OnMouseUp(MouseEventArgs args) { pressed = false; Invalidate(); base.OnMouseUp(args); }
        protected override void OnGotFocus(EventArgs args) { base.OnGotFocus(args); Invalidate(); }
        protected override void OnLostFocus(EventArgs args) { base.OnLostFocus(args); Invalidate(); }
        protected override void OnEnabledChanged(EventArgs args) { base.OnEnabledChanged(args); Invalidate(); }
        protected override void OnPaint(PaintEventArgs args)
        {
            args.Graphics.Clear(Parent == null ? NightTheme.Canvas : Parent.BackColor);
            if (Width < 2 || Height < 2) return;
            var fill = !Enabled ? NightTheme.Surface : Primary ? (pressed ? Color.FromArgb(73, 174, 163) : hovered ? Color.FromArgb(139, 233, 220) : NightTheme.Accent) : pressed ? NightTheme.Border : hovered ? NightTheme.Input : NightTheme.Surface;
            var ink = !Enabled ? Color.FromArgb(112, 128, 147) : Primary ? NightTheme.Canvas : NightTheme.Ink;
            args.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
            using (var path = NightTheme.Rounded(new Rectangle(1, 1, Width - 3, Height - 3), 9))
            using (var brush = new SolidBrush(fill))
            using (var pen = new Pen(Focused && Enabled ? (Primary ? NightTheme.Ink : NightTheme.Accent) : Primary && Enabled ? fill : NightTheme.Border, Focused ? 2 : 1))
            { args.Graphics.FillPath(brush, path); args.Graphics.DrawPath(pen, path); }
            var bounds = new Rectangle(Padding.Left, 0, Width - Padding.Horizontal - (Disclosure ? 26 : 0), Height);
            TextRenderer.DrawText(args.Graphics, Text, Font, bounds, ink, TextFormatFlags.VerticalCenter | TextFormatFlags.SingleLine | TextFormatFlags.EndEllipsis | (Disclosure ? TextFormatFlags.Left : TextFormatFlags.HorizontalCenter));
            if (Disclosure)
            {
                int x = Width - 24, y = Height / 2;
                using (var pen = new Pen(Enabled ? NightTheme.Muted : ink, 1.6f))
                {
                    args.Graphics.DrawLines(pen, Expanded ? new Point[] { new Point(x - 4, y - 2), new Point(x, y + 2), new Point(x + 4, y - 2) } : new Point[] { new Point(x - 2, y - 4), new Point(x + 2, y), new Point(x - 2, y + 4) });
                }
            }
        }
    }
}
