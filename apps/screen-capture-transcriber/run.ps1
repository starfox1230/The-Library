$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonw = Join-Path $scriptDir ".venv\Scripts\pythonw.exe"
$python = Join-Path $scriptDir ".venv\Scripts\python.exe"

if (Test-Path -LiteralPath $pythonw) {
  Start-Process -FilePath $pythonw -ArgumentList "-m", "screen_capture_transcriber" -WorkingDirectory $scriptDir
  exit 0
}

if (Test-Path -LiteralPath $python) {
  & $python -m screen_capture_transcriber
  exit $LASTEXITCODE
}

throw "The app is not set up. Run .\setup.ps1 first."

