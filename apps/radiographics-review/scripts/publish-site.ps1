param(
    [string]$CommitMessage = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$appRoot = Split-Path -Parent $scriptDir
$repoRoot = Split-Path -Parent (Split-Path -Parent $appRoot)
$appPathSpec = "apps/radiographics-review"

if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
    $CommitMessage = "Update Radiographics review library $timestamp"
}

$statusLines = git -C $repoRoot status --porcelain -- $appPathSpec
if (-not $statusLines) {
    Write-Host "No changes detected under $appPathSpec"
    exit 0
}

git -C $repoRoot add -- $appPathSpec
git -C $repoRoot diff --cached --quiet -- $appPathSpec
if ($LASTEXITCODE -eq 0) {
    Write-Host "No staged changes detected under $appPathSpec"
    exit 0
}

git -C $repoRoot commit -m $CommitMessage -- $appPathSpec
git -C $repoRoot push origin main

Write-Host "Published $appPathSpec"
