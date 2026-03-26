param(
    [string]$OutputName = "speed_streak_v1_1.ankiaddon"
)

$source = Split-Path -Parent $MyInvocation.MyCommand.Path
$output = Join-Path $source $OutputName
$staging = Join-Path $source ".ankiaddon-build"
$requiredPaths = @(
    "reviewer_overlay.py",
    "web_assets.py",
    "web\\overlay.css",
    "web\\overlay.js",
    "web\\card_timer.css",
    "web\\card_timer.js"
)
$excludeNames = @(
    ".ankiaddon-build",
    "__pycache__",
    ".DS_Store",
    "user_files",
    "install_to_anki.ps1",
    "build_ankiaddon.ps1",
    "install_to_anki.sh",
    "build_ankiaddon.sh"
)

$missing = $requiredPaths | Where-Object { -not (Test-Path (Join-Path $source $_)) }
if ($missing.Count -gt 0) {
    Write-Error "Cannot build package because required add-on files are missing: $($missing -join ', ')"
    exit 1
}

if (Test-Path $staging) {
    Remove-Item -Path $staging -Recurse -Force
}

if (Test-Path $output) {
    Remove-Item -Path $output -Force
}

New-Item -ItemType Directory -Path $staging | Out-Null

Get-ChildItem -Path $source -Force | Where-Object {
    $excludeNames -notcontains $_.Name -and
    $_.Name -notlike "*.ankiaddon" -and
    $_.Name -notlike "*.zip"
} | ForEach-Object {
    $destination = Join-Path $staging $_.Name
    if ($_.PSIsContainer) {
        Copy-Item -Path $_.FullName -Destination $destination -Recurse -Force
    } else {
        Copy-Item -Path $_.FullName -Destination $destination -Force
    }
}

$zipPath = [System.IO.Path]::ChangeExtension($output, ".zip")
Compress-Archive -Path (Join-Path $staging "*") -DestinationPath $zipPath -Force
Move-Item -Path $zipPath -Destination $output -Force
Remove-Item -Path $staging -Recurse -Force

Write-Host "Built package: $output"
Write-Host "Upload this .ankiaddon file at https://ankiweb.net/shared/addons/"
