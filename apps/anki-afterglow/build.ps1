$ErrorActionPreference = 'Stop'
$source = $PSScriptRoot
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $compiler)) { throw 'Windows .NET Framework C# compiler was not found.' }
& $compiler /nologo /optimize+ /platform:anycpu /target:exe "/out:$source\loopback.exe" "$source\Loopback.cs"
if ($LASTEXITCODE -ne 0) { throw 'Audio helper compilation failed.' }
$package = Join-Path $source 'afterglow.ankiaddon'
$zip = Join-Path $source 'afterglow.zip'
if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip }
$files=@('__init__.py','audio.py','beat.py','motion.py','backdrop.py','config.json','cloud-v0.5.json','manifest.json','loopback.exe','standalone.py','standalone.html','start_preview.ps1','web') | ForEach-Object {Join-Path $source $_}
Compress-Archive -LiteralPath $files -DestinationPath $zip
Move-Item -LiteralPath $zip -Destination $package -Force
Write-Host "Built $package"
