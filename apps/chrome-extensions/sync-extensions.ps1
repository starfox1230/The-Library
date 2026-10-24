[CmdletBinding()]
param(
    [string]$Slug = "all",
    [string]$DestinationRoot = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Chrome Extensions')
)
$ErrorActionPreference = 'Stop'
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$installRoot = [IO.Path]::GetFullPath($DestinationRoot)
$catalog = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $PSScriptRoot 'registry.json') | ConvertFrom-Json
$selected = @($catalog | Where-Object { $Slug -eq 'all' -or $_.slug -eq $Slug })
if ($selected.Count -eq 0) { throw "Unknown extension slug: $Slug" }
New-Item -ItemType Directory -Path $installRoot -Force | Out-Null
foreach ($extension in $selected) {
    $source = [IO.Path]::GetFullPath((Join-Path $repositoryRoot $extension.source))
    $destination = [IO.Path]::GetFullPath((Join-Path $installRoot $extension.folder))
    if (-not $source.StartsWith($repositoryRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Source must stay inside the repository: $source"
    }
    if (-not $destination.StartsWith($installRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
        [IO.Path]::GetDirectoryName($destination) -ne $installRoot) {
        throw "Extension folder must be a direct child of the installation home."
    }
    $manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $source 'manifest.json') | ConvertFrom-Json
    if ($manifest.manifest_version -ne 3) { throw "Expected a Manifest V3 extension at $source" }
    if ($source -eq $destination) { throw "Source and destination must differ." }
    if ((Test-Path -LiteralPath $destination) -and ((Get-Item -LiteralPath $destination).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Destination must be a real folder, not a junction: $destination"
    }
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    $count = 0
    Get-ChildItem -LiteralPath $source -File -Recurse | ForEach-Object {
        $relative = $_.FullName.Substring($source.Length + 1)
        if ($relative -match '(^|[\\/])(node_modules|tests|dist|scripts|\.git|__pycache__|helper)([\\/]|$)' -or
            $relative -match '(^|[\\/])\.env' -or $_.Extension -in @('.zip','.crx','.pyc','.log')) { return }
        $target = Join-Path $destination $relative
        if ($extension.preserve -contains $relative -and (Test-Path -LiteralPath $target)) { return }
        New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($target)) -Force | Out-Null
        Copy-Item -LiteralPath $_.FullName -Destination $target -Force
        $count++
    }
    Write-Output ("Ready: {0} v{1} ({2} files) -> {3}" -f $extension.name, $manifest.version, $count, $destination)
}
Write-Output 'In Chrome: chrome://extensions > Reload for updates, or Developer mode > Load unpacked for a new extension.'
