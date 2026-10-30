$ErrorActionPreference='Stop'
$python=Get-Command pythonw.exe -ErrorAction SilentlyContinue
$executable=if($python){$python.Source}else{Join-Path $env:LOCALAPPDATA 'AnkiProgramFiles\.venv\Scripts\pythonw.exe'}
if(-not(Test-Path -LiteralPath $executable)){throw 'Python was not found. Run standalone.py with Python 3.'}
$script=Join-Path $PSScriptRoot 'standalone.py'
Start-Process -FilePath $executable -ArgumentList @(('"{0}"' -f $script)) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
