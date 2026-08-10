$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvDir = Join-Path $scriptDir ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$venvPip = Join-Path $venvDir "Scripts\pip.exe"
$envFile = Join-Path $scriptDir ".env"
$exampleFile = Join-Path $scriptDir ".env.example"

if (-not (Test-Path -LiteralPath $venvPython)) {
  python -m venv $venvDir
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to create the virtual environment."
  }
}

if (-not (Test-Path -LiteralPath $venvPip)) {
  & $venvPython -m ensurepip --upgrade
  if ($LASTEXITCODE -ne 0) {
    throw "The virtual environment exists but pip could not be repaired."
  }
}

if (-not (Test-Path -LiteralPath $envFile) -and (Test-Path -LiteralPath $exampleFile)) {
  Copy-Item -LiteralPath $exampleFile -Destination $envFile
}

& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
  throw "Failed to upgrade pip."
}

& $venvPython -m pip install -r (Join-Path $scriptDir "requirements.txt")
if ($LASTEXITCODE -ne 0) {
  throw "Failed to install dependencies."
}

Write-Host ""
Write-Host "Setup complete."
Write-Host "You can record immediately with .\run.ps1"
Write-Host "To enable transcription, add OPENAI_API_KEY to $envFile"
Write-Host "For linked Medality recording, load the chrome-extension folder as an unpacked Chrome extension."
