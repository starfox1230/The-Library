Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
command = "powershell -NoProfile -Sta -ExecutionPolicy Bypass -Command ""& '" & scriptDir & "\run.ps1'"""

shell.Run command, 0
