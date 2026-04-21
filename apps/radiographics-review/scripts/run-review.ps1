param(
    [switch]$NoEnrich,
    [switch]$IncludeSeen,
    [int]$Limit
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspaceRoot = Split-Path -Parent $scriptDir

Set-Location $workspaceRoot

$arguments = @(".\src\runDigest.js")
if ($NoEnrich) {
    $arguments += "--no-enrich"
}
if ($IncludeSeen) {
    $arguments += "--include-seen"
}
if ($Limit -gt 0) {
    $arguments += "--limit=$Limit"
}

node @arguments
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
