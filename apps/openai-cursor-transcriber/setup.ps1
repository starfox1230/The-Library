$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvDir = Join-Path $scriptDir ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$envFile = Join-Path $scriptDir ".env"
$exampleFile = Join-Path $scriptDir ".env.example"

if (-not (Test-Path $venvPython)) {
  python -m venv $venvDir
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to create the virtual environment."
  }
}

if (-not (Test-Path $envFile) -and (Test-Path $exampleFile)) {
  Copy-Item -LiteralPath $exampleFile -Destination $envFile
}

& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
  throw "Failed to upgrade pip."
}

& $venvPython -m pip install -r (Join-Path $scriptDir "requirements.txt")
if ($LASTEXITCODE -ne 0) {
  throw "Failed to install the Python dependencies."
}

Write-Host ""
Write-Host "Setup complete."
Write-Host "Add your OpenAI API key to $envFile"
Write-Host "Then run .\\run.ps1"
