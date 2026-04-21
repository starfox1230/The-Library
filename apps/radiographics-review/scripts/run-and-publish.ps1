param(
    [switch]$IncludeSeen,
    [int]$Limit
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$appRoot = Split-Path -Parent $scriptDir

$runArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", (Join-Path $scriptDir "run-review.ps1")
)

if ($IncludeSeen) {
    $runArgs += "-IncludeSeen"
}

if ($Limit -gt 0) {
    $runArgs += @("-Limit", "$Limit")
}

Push-Location $appRoot
try {
    & powershell.exe @runArgs
    if ($LASTEXITCODE -ne 0) {
        throw "run-review.ps1 failed with exit code $LASTEXITCODE."
    }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $scriptDir "publish-site.ps1")
    if ($LASTEXITCODE -ne 0) {
        throw "publish-site.ps1 failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
