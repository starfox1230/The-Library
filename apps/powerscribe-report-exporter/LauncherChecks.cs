using System;
using System.Drawing;
using System.Windows.Forms;

namespace ReportExporter
{
    public static class LauncherChecks
    {
        private static Control Find(Control root, string name)
        {
            if (root.Name == name) return root;
            foreach (Control child in root.Controls) { Control result = Find(child, name); if (result != null) return result; }
            return null;
        }
        private static void Require(bool check, string message) { if (!check) throw new Exception(message); }
        private static void RequireUnclipped(Control control, Form form)
        {
            var bounds = control.RectangleToScreen(control.ClientRectangle);
            for (Control parent = control.Parent; parent != null; parent = parent.Parent)
                Require(parent.RectangleToScreen(parent.ClientRectangle).Contains(bounds), control.Name + " is clipped by " + parent.GetType().Name);
        }
        public static void VerifyTypedRange()
        {
            using (var form = new ExportForm(true))
            {
                var first = (TextBox)Find(form, "FirstCase");
                var last = (TextBox)Find(form, "LastCase");
                int lo, hi;
                first.Text = " 68 "; last.Text = "69"; form.ReadCaseRange(out lo, out hi);
                Require(lo == 68 && hi == 69, "Typed range changed source numbers");
                first.Text = last.Text = "1000000"; form.ReadCaseRange(out lo, out hi);
                Require(lo == 1000000 && hi == 1000000, "Maximum source label or single-case range rejected");
                foreach (string invalid in new string[] { "", " ", "0", "-1", "+1", "1.5", "1,000", "1e3", "case 2", "1000001", "9999999999999999999" })
                {
                    first.Text = invalid; last.Text = "1000000";
                    bool rejected = false;
                    try { form.ReadCaseRange(out lo, out hi); }
                    catch (InvalidOperationException error) { rejected = error.Message.Contains("First case"); }
                    Require(rejected, "Invalid first-case text was accepted or had no field-specific error");
                    first.Text = "1"; last.Text = invalid; rejected = false;
                    try { form.ReadCaseRange(out lo, out hi); }
                    catch (InvalidOperationException error) { rejected = error.Message.Contains("Last case"); }
                    Require(rejected, "Invalid last-case text was accepted or had no field-specific error");
                }
                first.Text = "69"; last.Text = "68";
                bool reversed = false;
                try { form.ReadCaseRange(out lo, out hi); }
                catch (InvalidOperationException error) { reversed = error.Message.Contains("at least"); }
                Require(reversed, "Reversed range was accepted");
            }
        }
        public static void VerifyCopiedText()
        {
            using (var form = new ExportForm(true))
            {
                form.StartPosition = FormStartPosition.Manual; form.Location = new Point(-20000, -20000); form.ShowInTaskbar = false;
                form.Show(); Application.DoEvents();
                var toggle = (Button)Find(form, "CopiedTextToggle");
                var panel = Find(form, "CopiedTextPanel");
                var textBox = (TextBox)Find(form, "CopiedText");
                var copy = (Button)Find(form, "CopyAgain");
                Require(!toggle.Visible && !panel.Visible, "Empty copied-text controls should be hidden");
                // Above the native edit control's usual input limit, with Unicode preserved.
                string expected = "Case 7\r\n" + new string('x', 70000) + " café →\r\nCase 8\r\n";
                form.SetCopiedText(expected, "Synthetic saved run 7-8"); Application.DoEvents();
                Require(toggle.Visible && !panel.Visible && textBox.ReadOnly, "New result was expanded or editable");
                Require(toggle.Parent.Controls.GetChildIndex(toggle) < toggle.Parent.Controls.GetChildIndex(Find(form, "Options")), "Copied text is below Options");
                toggle.PerformClick(); Application.DoEvents();
                Require(panel.Visible && textBox.Text == expected, "Expanded text was truncated or changed");
                form.ClipboardWriter = value => { throw new InvalidOperationException("Synthetic clipboard lock"); };
                copy.PerformClick();
                Require(Find(form, "CopyStatus").Text.Contains("Try Copy again") && textBox.Text == expected, "Clipboard failure erased text or has no recovery");
                string clipboard = "An unrelated later clipboard item";
                form.ClipboardWriter = value => clipboard = value;
                copy.PerformClick();
                Require(clipboard == expected, "Copy again did not restore the complete saved text");
                clipboard = "Overwritten again"; copy.PerformClick();
                Require(clipboard == expected, "Second recopy depended on previous clipboard contents");
                form.SetCopiedText(null, "Failed run without complete pairs");
                Require(textBox.Text == expected && Find(form, "CopiedSource").Text == "Synthetic saved run 7-8", "Empty run erased or relabeled previous saved text");
                form.SetCopiedText("New complete export", "Synthetic newer run"); Application.DoEvents();
                Require(!panel.Visible && textBox.Text == "New complete export", "New saved text did not replace old text and collapse");
                Require(((CheckBox)Find(form, "OpenNotepad")).Checked, "Notepad is not enabled by default for a new setup");
                form.Close();
            }
        }
        public static void Verify()
        {
            // This test-owned form has no hotkeys, profile access, PowerScribe
            // input, or clipboard access. It never invokes Go or a capture.
            using (var form = new ExportForm(true))
            {
                form.StartPosition = FormStartPosition.Manual; form.Location = new Point(-20000, -20000); form.ShowInTaskbar = false;
                form.Show(); Application.DoEvents(); form.PerformLayout();
                var options = Find(form, "OptionsPanel");
                var go = Find(form, "Go");
                var speed = (ComboBox)Find(form, "Speed");
                Require(!options.Visible && go.Visible && Find(form, "FirstCase").Visible && Find(form, "LastCase").Visible, "Simple launcher controls are not visible or Options is expanded");
                Require(form.AcceptButton == go && form.ClientSize.Height < 360 && form.ClientSize.Width < 500, "Go is not the default action or collapsed launcher is too large");
                Require(speed.SelectedIndex == 0, "Automatic is not the default speed");
                RequireUnclipped(Find(form, "FirstCase"), form); RequireUnclipped(Find(form, "LastCase"), form); RequireUnclipped(go, form);
                form.SetOptionsVisible(true); Application.DoEvents();
                Require(options.Visible && form.ClientSize.Height > 500 && go.Visible, "Options did not expand or Go disappeared");
                Require(form.ClientSize.Width >= 680, "Expanded Options did not gain width");
                RequireUnclipped(go, form);
                speed.SelectedIndex = 3; Application.DoEvents();
                Require(options.PreferredSize.Height > 300, "Custom timing did not lay out");
                form.SetOptionsVisible(false); Application.DoEvents();
                Require(!options.Visible && form.ClientSize.Height < 360 && form.ClientSize.Width < 500, "Options did not return to the compact size");
                var origin = form.PointToClient(go.PointToScreen(Point.Empty));
                Require(origin.X >= 0 && origin.Y >= 0 && origin.Y + go.Height <= form.ClientSize.Height, "Go is clipped outside the launcher");
                form.Close();
            }
        }
    }
}
