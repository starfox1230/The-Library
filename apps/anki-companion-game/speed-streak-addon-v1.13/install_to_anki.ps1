param(
    [string]$AddonFolderName = "speed_streak_v1_13"
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
    & $pythonCommand.Source $generator
} else {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if (-not $pyLauncher) {
        Write-Error "Cannot install because Python was not found to generate web_assets.py."
        exit 1
    }
    & $pyLauncher.Source -3 $generator
}

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

Write-Host "Installed add-on to: $target"
Write-Host "Preserved add-on data folders: $($preserveDirectories -join ', ')"
Write-Host "Restart Anki to load the add-on."
