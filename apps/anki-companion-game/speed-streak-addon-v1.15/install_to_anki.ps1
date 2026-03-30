param(
    [string]$AddonFolderName = "speed_streak_v1_15"
)

$source = Split-Path -Parent $MyInvocation.MyCommand.Path
$ankiAddonsRoot = Join-Path $env:APPDATA "Anki2\addons21"
$target = Join-Path $ankiAddonsRoot $AddonFolderName
$preserveDirectories = @("user_files")
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

Get-ChildItem -Path $target -Force | Where-Object {
    $preserveDirectories -notcontains $_.Name -and
    -not (Test-Path (Join-Path $source $_.Name))
} | ForEach-Object {
    Remove-Item -LiteralPath $_.FullName -Recurse -Force
}

Get-ChildItem -Path $source -Force | Where-Object {
    $_.Name -notin @("install_to_anki.ps1", "generate_web_assets.py", ".DS_Store") -and
    $_.Name -notlike "*.ankiaddon" -and
    $_.Name -notlike "*.zip"
} | ForEach-Object {
    if ($_.PSIsContainer -and $preserveDirectories -contains $_.Name) {
        $destination = Join-Path $target $_.Name
        if (-not (Test-Path $destination)) {
            Copy-Item -Path $_.FullName -Destination $destination -Recurse -Force
        }
        return
    }
    $destination = Join-Path $target $_.Name
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
if not meta_path.exists():
    def read_json(path: Path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    manifest = read_json(target / "manifest.json")
    config = read_json(target / "config.json")
    payload = {
        "name": str(manifest.get("name") or target.name),
        "mod": int(time.time()),
        "branch_index": int(manifest.get("branch_index", 1) or 1),
        "disabled": bool(manifest.get("disabled", False)),
    }
    conflicts = manifest.get("conflicts")
    if isinstance(conflicts, list):
        payload["conflicts"] = conflicts
    if isinstance(config, dict) and config:
        payload["config"] = config
    meta_path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")
'@

$metaBootstrap | & $pythonExe @pythonArgs - $target

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to create meta.json in the installed add-on folder."
    exit 1
}

Write-Host "Installed add-on to: $target"
Write-Host "Preserved add-on data folders: $($preserveDirectories -join ', ')"
Write-Host "Restart Anki to load the add-on."
