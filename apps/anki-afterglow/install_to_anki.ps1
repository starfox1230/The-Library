param([string]$AddonsRoot = (Join-Path $env:APPDATA 'Anki2\addons21'))
$ErrorActionPreference = 'Stop'
if (Get-Process anki -ErrorAction SilentlyContinue) { throw 'Close Anki before installing Afterglow, then run this command again.' }
& (Join-Path $PSScriptRoot 'build.ps1')
$root = [IO.Path]::GetFullPath($AddonsRoot).TrimEnd('\')
$target = [IO.Path]::GetFullPath((Join-Path $root 'anki_afterglow'))
if (-not $target.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid installation target.' }
New-Item -ItemType Directory -Path $target -Force | Out-Null
# Preserve the user's exact previous cloud appearance once, before replacing defaults.
$savedLook=Join-Path $target 'user_files/particle-cloud-v0.5.json'
if (-not (Test-Path -LiteralPath $savedLook)) {
    $savedSettings=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'cloud-v0.5.json') -Raw | ConvertFrom-Json
    $metaFile=Join-Path $target 'meta.json'
    if (Test-Path -LiteralPath $metaFile) {
        $previous=Get-Content -LiteralPath $metaFile -Raw | ConvertFrom-Json
        foreach($property in $previous.config.PSObject.Properties){
            $savedSettings | Add-Member -NotePropertyName $property.Name -NotePropertyValue $property.Value -Force
        }
    }
    $savedSettings.visual='particles'
    New-Item -ItemType Directory -Path (Split-Path -Parent $savedLook) -Force | Out-Null
    [IO.File]::WriteAllText($savedLook,($savedSettings | ConvertTo-Json -Depth 8),(New-Object Text.UTF8Encoding($false)))
}
# Stable folder retains Anki metadata and user settings across reinstalls.
foreach ($name in @('__init__.py','audio.py','beat.py','motion.py','backdrop.py','config.json','cloud-v0.5.json','manifest.json','loopback.exe','standalone.py','standalone.html','start_preview.ps1')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $target $name) -Force
}
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'web') -Destination $target -Recurse -Force
Write-Host "Installed Afterglow to $target. Restart Anki."
Write-Host 'Tools -> Afterglow -> Music background. Speed Streak was not modified.'
