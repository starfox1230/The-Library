param(
    [string]$OutputName
)

$source = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestPath = Join-Path $source "manifest.json"
$staging = Join-Path $source ".ankiaddon-build"
$excludeNames = @(
    ".ankiaddon-build",
    "__pycache__",
    ".DS_Store",
    "user_files",
    "README.md",
    "index.html",
    "install_to_anki.ps1",
    "build_ankiaddon.ps1",
    "install_to_anki.sh",
    "build_ankiaddon.sh"
)

if (-not (Test-Path $manifestPath)) {
    Write-Error "Could not find manifest.json at $manifestPath."
    exit 1
}

$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json

if (-not $OutputName) {
    $packageName = [string]$manifest.package
    if (-not $packageName) {
        Write-Error "Could not determine the package name from manifest.json."
        exit 1
    }
    $OutputName = "$packageName.ankiaddon"
}

$output = Join-Path $source $OutputName
$zipPath = [System.IO.Path]::ChangeExtension($output, ".zip")

if (Test-Path $staging) {
    Remove-Item -Path $staging -Recurse -Force
}

if (Test-Path $output) {
    Remove-Item -Path $output -Force
}

if (Test-Path $zipPath) {
    Remove-Item -Path $zipPath -Force
}

New-Item -ItemType Directory -Path $staging | Out-Null

Get-ChildItem -Path $source -Force | Where-Object {
    $excludeNames -notcontains $_.Name -and
    $_.Name -notlike "*.ankiaddon"
} | ForEach-Object {
    $destination = Join-Path $staging $_.Name
    if ($_.PSIsContainer) {
        Copy-Item -Path $_.FullName -Destination $destination -Recurse -Force
    } else {
        Copy-Item -Path $_.FullName -Destination $destination -Force
    }
}

Compress-Archive -Path (Join-Path $staging "*") -DestinationPath $zipPath -Force
Move-Item -Path $zipPath -Destination $output -Force
Remove-Item -Path $staging -Recurse -Force

Write-Host "Built package: $output"
