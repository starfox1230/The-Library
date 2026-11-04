"""Compare the published v0.22 and current assemblies on delayed source loading.

The synthetic worklist selects the next row immediately and remains enabled, but
the underlying report takes 350 ms to load. Opening the comparison snapshots
whatever report is loaded at that instant. The old version's recovery closes
and reopens WITHOUT clicking a row or sending Down, matching the user report.
This tests a concrete timing gap, not PowerScribe's actual private implementation.
No desktop input, real clipboard access, or patient text is used.
"""
from pathlib import Path
import os
import subprocess
import tempfile
import zipfile

APP = Path(__file__).resolve().parents[1]
scratch = Path(tempfile.mkdtemp(prefix="compare-study-switch-"))
tests = (APP / "Tests.cs").read_text(encoding="utf-8")
fake = tests[tests.index("        private class FakeKeyboardDesktop"):tests.index("        private sealed class FakeReportPaneDesktop")]
fake = fake.replace("private class FakeKeyboardDesktop", "public sealed class FakeKeyboardDesktop", 1)
harness = r'''
using System;using System.IO;using System.Threading;using System.Collections.Generic;using ReportExporter;
namespace StudyAudit {
FAKE
public static class Audit {
 [STAThread] public static void Main(string[] args) {
  foreach(int first in new int[]{1,10}) {
   var desktop=new FakeKeyboardDesktop{StudyLoadDelayMs=350,RememberedFocus=new IntPtr(10),NativeRowSupported=true};
   var settings=new Profile{TimingMode="Automatic",KeyboardWorkflow=true,TimeoutMs=1000,ComparisonWaitMs=1000};
   InputTiming.Configure(settings);
   var runner=new ExportRunner(); IReportSession active=null; int manualRecoveries=0;
   runner.RestartSession=()=>active=new KeyboardSession(settings,desktop,m=>{});
   runner.Recovery=(request,token)=>{
    manualRecoveries++;
    if(request.RepeatedFromCase!=first)throw new Exception("Unexpected recovery: "+request.Reason);
    active.CloseComparison(token); Thread.Sleep(1000); // Human closes; no row click.
    return RecoveryChoice.Continue;
   };
   string path=Path.Combine(args[0],"source-"+first+".txt");
   runner.Run(active=runner.RestartSession(),first,first+1,path,CancellationToken.None,m=>{});
   string output=File.ReadAllText(path+".for-comparison.txt");
   bool correct=output.Contains("Case "+(first+1)+"\r\nAttending Report:\r\nHEADER 1\r\nFINDINGS: attending 1");
   int opens=desktop.Events.FindAll(e=>e=="key:49").Count, downs=desktop.Events.FindAll(e=>e=="key:28").Count;
   Console.WriteLine("Start="+first+"; manual close/reopen="+manualRecoveries+"; comparison opens="+opens+"; Down="+downs+"; complete="+runner.Completed+"; second report correct="+correct);
   if(runner.Completed!=2||downs!=1||!correct)throw new Exception("Wrong study/label after source transition");
   if(args[1]=="old"&&(manualRecoveries!=1||opens!=3))throw new Exception("Published binary did not reproduce the delayed-source scenario");
   if(args[1]=="new"&&(manualRecoveries!=0||opens!=2))throw new Exception("Current binary still opened a comparison before the source study settled");
  }
 }
}
}
'''.replace("FAKE", fake)
csc = Path(os.environ["WINDIR"]) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
for version, mode in [("0.22", "old"), ("current", "new")]:
    dest = scratch / version
    dest.mkdir()
    if mode == "old":
        with zipfile.ZipFile(APP / "dist/PowerScribeReportExporter-v0.22.zip") as archive:
            binary = archive.read("PowerScribeReportExporter.exe")
    else:
        binary = (APP / "dist/PowerScribeReportExporter.exe").read_bytes()
    (dest / "PowerScribeReportExporter.exe").write_bytes(binary)
    source = dest / "Audit.cs"
    source.write_text(harness, encoding="utf-8-sig")
    build = subprocess.run([str(csc), "/nologo", "/target:exe", "/main:StudyAudit.Audit", f'/out:{dest / "Audit.exe"}',
        f'/reference:{dest / "PowerScribeReportExporter.exe"}', "/reference:System.dll", "/reference:System.Core.dll", str(source)], capture_output=True, text=True, timeout=30)
    if build.returncode:
        raise RuntimeError(build.stdout + build.stderr)
    replay = subprocess.run([str(dest / "Audit.exe"), str(dest), mode], capture_output=True, text=True, timeout=30)
    print(f"{version}:\n{replay.stdout}", flush=True)
    if replay.returncode:
        raise RuntimeError(replay.stderr)
print(f"Synthetic replay artifacts: {scratch}")
