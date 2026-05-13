$ErrorActionPreference = "Stop"

$appRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$startupFolder = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupFolder "Pomodoro Float.lnk"
$npmCommand = (Get-Command npm.cmd -ErrorAction SilentlyContinue)

if (-not $npmCommand) {
  throw "npm.cmd was not found on PATH. Install Node.js or add npm to PATH, then run this script again."
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $npmCommand.Source
$shortcut.Arguments = "start"
$shortcut.WorkingDirectory = $appRoot.Path
$shortcut.WindowStyle = 7
$shortcut.Description = "Start Pomodoro Float"
$shortcut.Save()

Write-Host "Created startup shortcut:"
Write-Host $shortcutPath
Write-Host ""
Write-Host "Pomodoro Float will start automatically after the next Windows sign-in."
