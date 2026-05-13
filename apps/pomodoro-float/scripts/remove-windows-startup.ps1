$ErrorActionPreference = "Stop"

$startupFolder = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupFolder "Pomodoro Float.lnk"

if (Test-Path $shortcutPath) {
  Remove-Item -LiteralPath $shortcutPath
  Write-Host "Removed startup shortcut:"
  Write-Host $shortcutPath
} else {
  Write-Host "No Pomodoro Float startup shortcut was found."
}
