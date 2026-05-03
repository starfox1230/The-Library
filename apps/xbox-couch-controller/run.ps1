$ErrorActionPreference = "Stop"
$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $AppDir ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    python -m venv (Join-Path $AppDir ".venv")
    & $Python -m pip install -r (Join-Path $AppDir "requirements.txt")
}

& $Python (Join-Path $AppDir "xbox_couch_controller.py")
