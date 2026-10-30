$ErrorActionPreference = 'Stop'
$source = $PSScriptRoot
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $compiler)) { throw 'Windows .NET Framework C# compiler was not found.' }
& $compiler /nologo /optimize+ /platform:anycpu /target:exe "/out:$source\loopback.exe" "$source\Loopback.cs"
if ($LASTEXITCODE -ne 0) { throw 'Audio helper compilation failed.' }
$package = Join-Path $source 'afterglow.ankiaddon'
$zip = Join-Path $source 'afterglow.zip'
if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip }
Compress-Archive -LiteralPath @((Join-Path $source '__init__.py'),(Join-Path $source 'audio.py'),(Join-Path $source 'beat.py'),(Join-Path $source 'config.json'),(Join-Path $source 'manifest.json'),(Join-Path $source 'loopback.exe'),(Join-Path $source 'web')) -DestinationPath $zip
Move-Item -LiteralPath $zip -Destination $package -Force
Write-Host "Built $package"
