param(
    [string]$SourceWorkspace = "G:\My Drive\Codex Automations",
    [string]$StageWorkspace = "",
    [switch]$IncludeSeen,
    [int]$Limit
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($StageWorkspace)) {
    $StageWorkspace = Join-Path $env:LOCALAPPDATA "RadiographicsReview\stage-workspace"
}

function Invoke-RobocopyMirror {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [string[]]$ExtraArgs = @()
    )

    if (-not (Test-Path $Source)) {
        return
    }

    New-Item -ItemType Directory -Force -Path $Destination | Out-Null

    $arguments = @(
        $Source,
        $Destination,
        "/MIR",
        "/R:1",
        "/W:1",
        "/FFT",
        "/NFL",
        "/NDL",
        "/NP",
        "/NJH",
        "/NJS"
    ) + $ExtraArgs

    & robocopy @arguments | Out-Null
    $code = $LASTEXITCODE
    if ($code -ge 8) {
        throw "Robocopy failed with exit code $code while copying '$Source' to '$Destination'."
    }
}

function Copy-WorkspaceToStage {
    param(
        [Parameter(Mandatory = $true)][string]$SourceRoot,
        [Parameter(Mandatory = $true)][string]$StageRoot
    )

    New-Item -ItemType Directory -Force -Path $StageRoot | Out-Null

    foreach ($dir in @("src", "scripts", "data", "digests", "articles")) {
        Invoke-RobocopyMirror `
            -Source (Join-Path $SourceRoot $dir) `
            -Destination (Join-Path $StageRoot $dir)
    }

    foreach ($file in @("package.json", "README.md", ".gitignore")) {
        $sourceFile = Join-Path $SourceRoot $file
        if (Test-Path $sourceFile) {
            Copy-Item -LiteralPath $sourceFile -Destination (Join-Path $StageRoot $file) -Force
        }
    }
}

function Copy-OutputsBack {
    param(
        [Parameter(Mandatory = $true)][string]$StageRoot,
        [Parameter(Mandatory = $true)][string]$SourceRoot
    )

    foreach ($dir in @("data", "digests", "articles")) {
        Invoke-RobocopyMirror `
            -Source (Join-Path $StageRoot $dir) `
            -Destination (Join-Path $SourceRoot $dir)
    }
}

Copy-WorkspaceToStage -SourceRoot $SourceWorkspace -StageRoot $StageWorkspace

$runReviewPath = Join-Path $StageWorkspace "scripts\run-review.ps1"
$arguments = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $runReviewPath
)

if ($IncludeSeen) {
    $arguments += "-IncludeSeen"
}

if ($Limit -gt 0) {
    $arguments += @("-Limit", "$Limit")
}

Push-Location $StageWorkspace
try {
    & powershell.exe @arguments
    $runExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

if ($runExitCode -ne 0) {
    throw "Stage run failed with exit code $runExitCode."
}

Copy-OutputsBack -StageRoot $StageWorkspace -SourceRoot $SourceWorkspace

Write-Host "Automation run completed through local stage workspace."
Write-Host "Stage workspace: $StageWorkspace"
Write-Host "Source workspace: $SourceWorkspace"
