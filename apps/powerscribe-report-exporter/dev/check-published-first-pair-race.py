"""Replay one controlled clipboard race against old/new real release assemblies.

Windows/.NET Framework only. All reports and desktop events are synthetic; this
does not control PowerScribe, use the real clipboard, or prove which race occurred
on a hospital workstation. Run build.ps1 first and retain the v0.18 release ZIP in
dist. Generated harnesses and synthetic exports stay in a unique temp directory.
"""
from pathlib import Path
import os
import subprocess
import tempfile
import zipfile

APP = Path(__file__).resolve().parents[1]
scratch = Path(tempfile.mkdtemp(prefix="compare-first-pair-race-"))
tests = (APP / "Tests.cs").read_text(encoding="utf-8")
fake = tests[tests.index("        private sealed class FakeKeyboardDesktop"):tests.index("        private static Profile KeyboardSettings")]
fake = fake.replace("private sealed class FakeKeyboardDesktop", "public sealed class FakeKeyboardDesktop", 1)
harness = r'''
using System;using System.IO;using System.Threading;using System.Collections.Generic;using ReportExporter;
namespace RaceAudit {
FAKE
public static class Audit {
 [STAThread] public static void Main(string[] args) {
  foreach(int first in new int[]{1,11}) {
   var desktop=new FakeKeyboardDesktop{ChangeClipboardDuringRead=true};
   var settings=new Profile{TimingMode="Custom",KeyboardWorkflow=true,KeyDelayMs=0,CaseDelayMs=0,PollMs=1,TimeoutMs=250,ComparisonWaitMs=250};
   var runner=new ExportRunner();string path=Path.Combine(args[0],"case-"+first+".txt");
   runner.Run(new KeyboardSession(settings,desktop,m=>{}),first,first+2,path,CancellationToken.None,m=>{});
   string output=File.ReadAllText(path+".for-comparison.txt");
   bool duplicate=output.Contains("Case "+(first+1)+"\r\nAttending Report:\r\nHEADER 0\r\nFINDINGS: attending 0");
   bool correct=output.Contains("Case "+(first+1)+"\r\nAttending Report:\r\nHEADER 1\r\nFINDINGS: attending 1");
   Console.WriteLine("Start="+first+"; row advances="+desktop.Row+"; copies="+desktop.CopyCount+"; first pair repeated="+duplicate+"; correct second pair="+correct);
   if(desktop.Row!=2||desktop.CopyCount!=6||desktop.UnstableReads!=2)throw new Exception("Fixture changed normal navigation/copy commands");
   if(args[1]=="old"&&!duplicate)throw new Exception("Old binary did not reproduce the controlled race");
   if(args[1]=="new"&&(!correct||duplicate))throw new Exception("Stable snapshot fix failed");
  }
 }
}
}
'''.replace("FAKE", fake)
csc = Path(os.environ["WINDIR"]) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
for version, mode in [("0.18", "old"), ("current", "new")]:
    dest = scratch / version
    dest.mkdir()
    if mode == "old":
        with zipfile.ZipFile(APP / "dist/PowerScribeReportExporter-v0.18.zip") as archive:
            binary = archive.read("PowerScribeReportExporter.exe")
    else:
        binary = (APP / "dist/PowerScribeReportExporter.exe").read_bytes()
    (dest / "PowerScribeReportExporter.exe").write_bytes(binary)
    source = dest / "Audit.cs"
    source.write_text(harness, encoding="utf-8-sig")
    build = subprocess.run([str(csc), "/nologo", "/target:exe", "/main:RaceAudit.Audit", f'/out:{dest / "Audit.exe"}',
        f'/reference:{dest / "PowerScribeReportExporter.exe"}', "/reference:System.dll", "/reference:System.Core.dll", str(source)], capture_output=True, text=True)
    if build.returncode:
        raise RuntimeError(build.stdout + build.stderr)
    replay = subprocess.run([str(dest / "Audit.exe"), str(dest), mode], capture_output=True, text=True)
    print(f"{version}:\n{replay.stdout}", flush=True)
    if replay.returncode:
        raise RuntimeError(replay.stderr)
print(f"Synthetic replay artifacts: {scratch}")
