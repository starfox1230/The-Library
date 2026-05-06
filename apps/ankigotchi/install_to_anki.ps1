param(
    [string]$AddonFolderName
)

$source = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestPath = Join-Path $source "manifest.json"
$ankiAddonsRoot = Join-Path $env:APPDATA "Anki2\addons21"
$excludeNames = @(
    ".DS_Store",
    ".ankiaddon-build",
    "__pycache__",
    "README.md",
    "index.html",
    "install_to_anki.ps1",
    "build_ankiaddon.ps1",
    "install_to_anki.sh",
    "build_ankiaddon.sh"
)
$preserveDirectories = @("user_files")

if (-not (Test-Path $manifestPath)) {
    Write-Error "Could not find manifest.json at $manifestPath."
    exit 1
}

$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json

if (-not $AddonFolderName) {
    $AddonFolderName = [string]$manifest.package
}

if (-not $AddonFolderName) {
    Write-Error "Could not determine the add-on folder name."
    exit 1
}

if (-not (Test-Path $ankiAddonsRoot)) {
    Write-Error "Could not find Anki add-ons folder at $ankiAddonsRoot. Open Anki once and verify it is installed."
    exit 1
}

$target = Join-Path $ankiAddonsRoot $AddonFolderName

if (-not (Test-Path $target)) {
    New-Item -ItemType Directory -Path $target | Out-Null
}

Get-ChildItem -Path $source -Force | Where-Object {
    $excludeNames -notcontains $_.Name -and
    $_.Name -notlike "*.ankiaddon"
} | ForEach-Object {
    $destination = Join-Path $target $_.Name

    if ($_.PSIsContainer -and $preserveDirectories -contains $_.Name) {
        if (-not (Test-Path $destination)) {
            Copy-Item -Path $_.FullName -Destination $destination -Recurse -Force
        }
        return
    }

    if ($_.PSIsContainer) {
        if (Test-Path $destination) {
            Remove-Item -Path $destination -Recurse -Force
        }
        Copy-Item -Path $_.FullName -Destination $destination -Recurse -Force
    } else {
        Copy-Item -Path $_.FullName -Destination $destination -Force
    }
}

Write-Host "Installed add-on to: $target"
Write-Host "Preserved add-on data folders: $($preserveDirectories -join ', ')"
Write-Host "Restart Anki to load the add-on."
