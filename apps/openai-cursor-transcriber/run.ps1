$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPythonw = Join-Path $scriptDir ".venv\Scripts\pythonw.exe"
$venvPython = Join-Path $scriptDir ".venv\Scripts\python.exe"

if (Test-Path $venvPythonw) {
  $python = $venvPythonw
} elseif (Test-Path $venvPython) {
  $python = $venvPython
} else {
  $pythonCommand = (Get-Command python -ErrorAction Stop).Source
  $candidatePythonw = Join-Path (Split-Path -Parent $pythonCommand) "pythonw.exe"
  if (Test-Path $candidatePythonw) {
    $python = $candidatePythonw
  } else {
    $python = $pythonCommand
  }
}

Start-Process -FilePath $python -WorkingDirectory $scriptDir -ArgumentList "-m", "cursor_transcriber"
