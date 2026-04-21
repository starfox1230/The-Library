param(
    [string]$CommitMessage = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$appRoot = Split-Path -Parent $scriptDir
$repoRoot = Split-Path -Parent (Split-Path -Parent $appRoot)
$appPathSpec = "apps/radiographics-review"

function Assert-LastExitCode {
    param(
        [string]$Step
    )

    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE."
    }
}

if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
    $CommitMessage = "Update Radiographics review library $timestamp"
}

$statusLines = git -C $repoRoot status --porcelain -- $appPathSpec
Assert-LastExitCode "git status"
if (-not $statusLines) {
    Write-Host "No changes detected under $appPathSpec"
    exit 0
}

git -C $repoRoot add -- $appPathSpec
Assert-LastExitCode "git add"
git -C $repoRoot diff --cached --quiet -- $appPathSpec
if ($LASTEXITCODE -eq 0) {
    Write-Host "No staged changes detected under $appPathSpec"
    exit 0
}
if ($LASTEXITCODE -ne 1) {
    throw "git diff --cached --quiet failed with exit code $LASTEXITCODE."
}

git -C $repoRoot commit -m $CommitMessage -- $appPathSpec
Assert-LastExitCode "git commit"
git -C $repoRoot push origin main
Assert-LastExitCode "git push"

Write-Host "Published $appPathSpec"
