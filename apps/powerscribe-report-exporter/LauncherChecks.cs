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
                Require(form.AcceptButton == go && form.ClientSize.Height < 400, "Go is not the default action or collapsed launcher is too tall");
                Require(speed.SelectedIndex == 0, "Automatic is not the default speed");
                form.SetOptionsVisible(true); Application.DoEvents();
                Require(options.Visible && form.ClientSize.Height > 500 && go.Visible, "Options did not expand or Go disappeared");
                speed.SelectedIndex = 3; Application.DoEvents();
                Require(options.PreferredSize.Height > 300, "Custom timing did not lay out");
                form.SetOptionsVisible(false); Application.DoEvents();
                Require(!options.Visible && form.ClientSize.Height < 400, "Options did not collapse");
                var origin = form.PointToClient(go.PointToScreen(Point.Empty));
                Require(origin.X >= 0 && origin.Y >= 0 && origin.Y + go.Height <= form.ClientSize.Height, "Go is clipped outside the launcher");
                form.Close();
            }
        }
    }
}
