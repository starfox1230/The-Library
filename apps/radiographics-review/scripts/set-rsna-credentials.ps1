param(
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $localAppData = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { Join-Path $env:USERPROFILE "AppData\\Local" }
    $OutputPath = Join-Path $localAppData "RadiographicsReview\\rsna-credential.xml"
}

$targetDir = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Path $targetDir -Force | Out-Null

$username = Read-Host "RSNA username or email"
if ([string]::IsNullOrWhiteSpace($username)) {
    throw "Username is required."
}

$password = Read-Host "RSNA password" -AsSecureString
$credential = New-Object System.Management.Automation.PSCredential ($username, $password)
$credential | Export-Clixml -LiteralPath $OutputPath

Write-Host "Saved RSNA credential to $OutputPath"
Write-Host "This file is protected for your Windows user account via DPAPI."
