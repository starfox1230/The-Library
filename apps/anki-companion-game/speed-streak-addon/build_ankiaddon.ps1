param(
    [string]$OutputName = "speed_streak.ankiaddon"
)

$source = Split-Path -Parent $MyInvocation.MyCommand.Path
$output = Join-Path $source $OutputName
$staging = Join-Path $source ".ankiaddon-build"
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

if (Test-Path $staging) {
    Remove-Item -Path $staging -Recurse -Force
}

if (Test-Path $output) {
    Remove-Item -Path $output -Force
}

New-Item -ItemType Directory -Path $staging | Out-Null

Get-ChildItem -Path $source -Force | Where-Object { $excludeNames -notcontains $_.Name } | ForEach-Object {
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
