param(
    [string]$AddonFolderName = "speed_streak_v2_07",
    [string]$AnkiBase = (Join-Path $env:APPDATA "Anki2"),
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($AddonFolderName) -or $AddonFolderName -in @(".", "..") -or $AddonFolderName -match '[\\/:]') {
    throw "Specify a simple add-on folder name."
}
if (-not $CheckOnly -and (Get-Process -Name anki -ErrorAction SilentlyContinue)) {
    throw "Close Anki before applying the Speed Streak undo patch."
}
$target = Join-Path $AnkiBase "addons21\$AddonFolderName"
if (-not (Test-Path -LiteralPath $target -PathType Container)) {
    throw "Speed Streak is not installed at $target"
}
if ((Get-Item -LiteralPath $target -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
    throw "Refusing to patch an add-on junction or symlink: $target"
}
$files = @("reviewer_overlay.py", "build_info.py", "time_drain_undo.py")
foreach ($name in $files) {
    $path = Join-Path $target $name
    if ((Test-Path -LiteralPath $path) -and ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Refusing to patch a symlink: $path"
    }
}
$python = Get-Command python -ErrorAction Stop
$tool = Join-Path $PSScriptRoot "..\tools\fix_time_drain_undo.py"
$backup = Join-Path $AnkiBase ("addons-data\speed_streak\code-backups\time-drain-undo-" + [guid]::NewGuid().ToString("N"))
$stage = Join-Path $backup "patched"
New-Item -ItemType Directory -Path $stage -Force | Out-Null
foreach ($name in $files) {
    $path = Join-Path $target $name
    if (Test-Path -LiteralPath $path) {
        Copy-Item -LiteralPath $path -Destination (Join-Path $backup $name)
        Copy-Item -LiteralPath $path -Destination (Join-Path $stage $name)
    } elseif ($name -ne "time_drain_undo.py") {
        throw "Required Speed Streak file is missing: $path"
    }
}
# The tool validates the source before changing it. It changes only these three
# code files; all visual assets, preferences, history and other add-ons stay put.
& $python.Source -B $tool --directory $stage
if ($LASTEXITCODE -ne 0) {
    throw "Patch validation failed; the installed add-on has not been changed."
}
if ($CheckOnly) {
    Write-Host "Patch validated. Installed files unchanged. Preview: $stage"
    return
}
# Recheck immediately before copying, in case Anki opened during validation.
if (Get-Process -Name anki -ErrorAction SilentlyContinue) {
    throw "Anki opened during validation. Close it and run this command again."
}
try {
    foreach ($name in $files) {
        Copy-Item -LiteralPath (Join-Path $stage $name) -Destination (Join-Path $target $name) -Force
    }
} catch {
    foreach ($name in $files) {
        $old = Join-Path $backup $name
        if (Test-Path -LiteralPath $old) {
            Copy-Item -LiteralPath $old -Destination (Join-Path $target $name) -Force
        }
    }
    throw
}
Write-Host "Installed focused undo patch: $target"
Write-Host "Original code backup: $backup"
Write-Host "Restart Anki to load the patched build."
