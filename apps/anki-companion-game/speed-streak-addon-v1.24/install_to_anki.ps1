param(
    [string]$AddonFolderName = "speed_streak_v1_24",
    [string[]]$PreviousAddonFolderNames = @(
        "speed_streak",
        "speed_streak_v1_1",
        "speed_streak_v1_11",
        "speed_streak_v1_12",
        "speed_streak_v1_13",
        "speed_streak_v1_14",
        "speed_streak_v1_15",
        "speed_streak_v1_16",
        "speed_streak_v1_17",
        "speed_streak_v1_20",
        "speed_streak_v1_21",
        "speed_streak_v1_22",
        "speed_streak_v1_23",
        "speed_streak_v2_0",
        "1237336370"
    )
)

$source = Split-Path -Parent $MyInvocation.MyCommand.Path
$ankiAddonsRoot = Join-Path $env:APPDATA "Anki2\addons21"
$target = Join-Path $ankiAddonsRoot $AddonFolderName
$preserveDirectories = @("user_files")
$preserveFiles = @("meta.json")
$generator = Join-Path $source "generate_web_assets.py"
$requiredPaths = @(
    "reviewer_overlay.py",
    "web_assets.py",
    "web\\overlay.css",
    "web\\overlay.js",
    "web\\card_timer.css",
    "web\\card_timer.js"
)

if (-not (Test-Path $ankiAddonsRoot)) {
    Write-Error "Could not find Anki add-ons folder at $ankiAddonsRoot. Open Anki once and verify it is installed."
    exit 1
}

if (-not (Test-Path $generator)) {
    Write-Error "Cannot install because the asset generator is missing: $generator"
    exit 1
}

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCommand) {
    $pythonExe = $pythonCommand.Source
    $pythonArgs = @()
} else {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if (-not $pyLauncher) {
        Write-Error "Cannot install because Python was not found to generate web_assets.py."
        exit 1
    }
    $pythonExe = $pyLauncher.Source
    $pythonArgs = @("-3")
}

& $pythonExe @pythonArgs $generator

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to generate web_assets.py before install."
    exit 1
}

$missing = $requiredPaths | Where-Object { -not (Test-Path (Join-Path $source $_)) }
if ($missing.Count -gt 0) {
    Write-Error "Cannot install because required add-on files are missing: $($missing -join ', ')"
    exit 1
}

if (-not (Test-Path $target)) {
    New-Item -ItemType Directory -Path $target | Out-Null
}

foreach ($previousFolderName in $PreviousAddonFolderNames) {
    if ([string]::IsNullOrWhiteSpace($previousFolderName) -or $previousFolderName -eq $AddonFolderName) {
        continue
    }
    $previousTarget = Join-Path $ankiAddonsRoot $previousFolderName
    if (-not (Test-Path $previousTarget)) {
        continue
    }
    foreach ($preserveDirectory in $preserveDirectories) {
        $previousPreservedPath = Join-Path $previousTarget $preserveDirectory
        $nextPreservedPath = Join-Path $target $preserveDirectory
        if ((Test-Path $previousPreservedPath) -and -not (Test-Path $nextPreservedPath)) {
            Copy-Item -Path $previousPreservedPath -Destination $nextPreservedPath -Recurse -Force
        }
    }
    foreach ($preserveFile in $preserveFiles) {
        $previousPreservedPath = Join-Path $previousTarget $preserveFile
        $nextPreservedPath = Join-Path $target $preserveFile
        if ((Test-Path $previousPreservedPath) -and -not (Test-Path $nextPreservedPath)) {
            Copy-Item -LiteralPath $previousPreservedPath -Destination $nextPreservedPath -Force
        }
    }
    Remove-Item -LiteralPath $previousTarget -Recurse -Force
}

Get-ChildItem -Path $target -Force | Where-Object {
    $preserveDirectories -notcontains $_.Name -and
    $preserveFiles -notcontains $_.Name -and
    -not (Test-Path (Join-Path $source $_.Name))
} | ForEach-Object {
    Remove-Item -LiteralPath $_.FullName -Recurse -Force
}

Get-ChildItem -Path $source -Force | Where-Object {
    $_.Name -notin @("install_to_anki.ps1", "generate_web_assets.py", ".DS_Store") -and
    $_.Name -notlike "*.ankiaddon" -and
    $_.Name -notlike "*.zip"
} | ForEach-Object {
    $destination = Join-Path $target $_.Name
    if ($_.PSIsContainer -and $preserveDirectories -contains $_.Name) {
        if (-not (Test-Path $destination)) {
            Copy-Item -Path $_.FullName -Destination $destination -Recurse -Force
        }
        return
    }
    if (-not $_.PSIsContainer -and $preserveFiles -contains $_.Name -and (Test-Path $destination)) {
        return
    }
    if ($_.PSIsContainer) {
        Copy-Item -Path $_.FullName -Destination $destination -Recurse -Force
    } else {
        Copy-Item -Path $_.FullName -Destination $destination -Force
    }
}

$metaBootstrap = @'
import json
import sys
import time
from pathlib import Path

target = Path(sys.argv[1])
meta_path = target / "meta.json"

def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

manifest = read_json(target / "manifest.json")
default_config = read_json(target / "config.json")
existing_meta = read_json(meta_path)
existing_config = existing_meta.get("config") if isinstance(existing_meta.get("config"), dict) else {}
merged_config = dict(default_config) if isinstance(default_config, dict) else {}
merged_config.update(existing_config)
payload = dict(existing_meta) if isinstance(existing_meta, dict) else {}
payload.update(
    {
        "name": str(manifest.get("name") or target.name),
        "mod": int(time.time()),
        "branch_index": int(manifest.get("branch_index", 1) or 1),
        "disabled": bool(manifest.get("disabled", False)),
    }
)
conflicts = manifest.get("conflicts")
if isinstance(conflicts, list):
    payload["conflicts"] = conflicts
if merged_config:
    payload["config"] = merged_config
meta_path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")
'@

$metaBootstrap | & $pythonExe @pythonArgs - $target

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to create meta.json in the installed add-on folder."
    exit 1
}

Write-Host "Installed add-on to: $target"
if ($PreviousAddonFolderNames.Count -gt 0) {
    Write-Host "Removed previous add-on folders if present: $($PreviousAddonFolderNames -join ', ')"
}
Write-Host "Preserved add-on data folders: $($preserveDirectories -join ', ')"
Write-Host "Preserved add-on settings files: $($preserveFiles -join ', ')"
Write-Host "Restart Anki to load the add-on."
