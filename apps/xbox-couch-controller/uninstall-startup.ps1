$ErrorActionPreference = "Stop"
$ShortcutPath = Join-Path ([Environment]::GetFolderPath("Startup")) "Xbox Couch Controller.lnk"
if (Test-Path $ShortcutPath) {
    Remove-Item -LiteralPath $ShortcutPath
    Write-Host "Removed startup shortcut:"
    Write-Host $ShortcutPath
} else {
    Write-Host "Startup shortcut was not installed."
}
