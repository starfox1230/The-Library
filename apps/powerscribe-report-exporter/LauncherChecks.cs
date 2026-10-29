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
