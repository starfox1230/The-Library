param(
    [switch]$DeveloperLab,
    [string]$AddonFolderName = "speed_streak_v2_08",
    [string[]]$PreviousAddonFolderNames = @(
        "speed_streak_v2_07",
        "speed_streak_v2_06",
        "speed_streak_v2_06_diagnostic",
        "speed_streak_v2_05",
        "speed_streak_v2_04",
        "speed_streak_v2_04",
        "speed_streak",
        "speed_streak_v1_1",
        "speed_streak_v1_11",
        "speed_streak_v1_12",
        "speed_streak_v1_13",
        "speed_streak_v1_14",
        "speed_streak_v1_15",
        "speed_streak_v1_16",
        "speed_streak_v1_17",
        "speed_streak_v1_20",
        "speed_streak_v1_21",
        "speed_streak_v1_22",
        "speed_streak_v1_23",
        "speed_streak_v1_24",
        "speed_streak_v1_25",
        "speed_streak_v1_26",
        "speed_streak_v1_27",
        "speed_streak_v1_28",
        "speed_streak_v1_28b",
        "speed_streak_v1_29",
        "speed_streak_v1_30",
        "speed_streak_v1_31",
        "speed_streak_v1_32",
        "speed_streak_v1_33",
        "speed_streak_v1_34",
        "speed_streak_v1_35",
        "speed_streak_v1_36",
        "speed_streak_v2_0",
        "speed_streak_v2_01",
        "speed_streak_v2_02",
        "speed_streak_v2_03",
        "1237336370"
    )
)

$ErrorActionPreference = "Stop"
if (Get-Process -Name anki -ErrorAction SilentlyContinue) {
    throw "Close Anki before replacing Speed Streak."
}
$archive = Join-Path $PSScriptRoot "speed_streak_v2_08.ankiaddon"
$ankiRoot = Join-Path $env:APPDATA "Anki2"
$addons = Join-Path $ankiRoot "addons21"
if (-not (Test-Path -LiteralPath $addons -PathType Container)) {
    throw "Open Anki once so its addons21 directory exists."
}
$addons = (Resolve-Path -LiteralPath $addons).Path
$target = Join-Path $addons $AddonFolderName
$old = @()
foreach ($name in (@($AddonFolderName) + $PreviousAddonFolderNames | Select-Object -Unique)) {
    if ($name -notmatch '^[A-Za-z0-9_-]+$') { throw "Invalid add-on folder name." }
    $candidate = [IO.Path]::GetFullPath((Join-Path $addons $name))
    if ([IO.Path]::GetDirectoryName($candidate) -ne $addons) { throw "Invalid add-on path." }
    if (Test-Path -LiteralPath $candidate) {
        $item = Get-Item -LiteralPath $candidate -Force
        if (-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "Expected an ordinary add-on folder at $candidate."
        }
        $old += $item
    }
}

# A same-volume staging directory makes activation a single directory rename.
$backupRoot = Join-Path $ankiRoot "addons-data\speed-streak-install-backups"
$session = Join-Path $backupRoot ([guid]::NewGuid().ToString("N"))
$stage = Join-Path $session "staged"
New-Item -ItemType Directory -Path $stage -Force | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::ExtractToDirectory($archive, $stage)
$manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $stage "manifest.json") | ConvertFrom-Json
if ($manifest.package -ne "speed_streak_v2_08" -or -not (Test-Path -LiteralPath (Join-Path $stage "__init__.py"))) {
    throw "Unexpected or incomplete Speed Streak package."
}

$preserveFiles = @("meta.json")
foreach ($name in ($preserveFiles + @("user_files"))) {
    foreach ($folder in $old) {
        $source = Join-Path $folder.FullName $name
        if (Test-Path -LiteralPath $source) {
            Copy-Item -LiteralPath $source -Destination (Join-Path $stage $name) -Recurse -Force
            break
        }
    }
}
$metaPath = Join-Path $stage "meta.json"
$meta = if (Test-Path -LiteralPath $metaPath) {
    Get-Content -Raw -Encoding UTF8 -LiteralPath $metaPath | ConvertFrom-Json
} else { [PSCustomObject]@{} }
$defaults = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $stage "config.json") | ConvertFrom-Json
if ($meta.config) {
    foreach ($property in $meta.config.PSObject.Properties) {
        $defaults | Add-Member -Force NoteProperty $property.Name $property.Value
    }
}
$meta | Add-Member -Force NoteProperty config $defaults
$meta | Add-Member -Force NoteProperty name $manifest.name
$meta | Add-Member -Force NoteProperty conflicts $manifest.conflicts
$meta | Add-Member -Force NoteProperty disabled $false
$meta | Add-Member -Force NoteProperty mod ([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())
[IO.File]::WriteAllText($metaPath, ($meta | ConvertTo-Json -Depth 100), (New-Object Text.UTF8Encoding($false)))
if ($DeveloperLab) {
    $privateDir = Join-Path $stage "user_files"
    New-Item -ItemType Directory -Force -Path $privateDir | Out-Null
    New-Item -ItemType File -Force -Path (Join-Path $privateDir "enable-suggestion-lab") | Out-Null
}

$moved = @()
try {
    foreach ($folder in $old) {
        $backup = Join-Path $session $folder.Name
        [IO.Directory]::Move($folder.FullName, $backup)
        $moved += $folder
    }
    [IO.Directory]::Move($stage, $target)
} catch {
    foreach ($folder in $moved) {
        [IO.Directory]::Move((Join-Path $session $folder.Name), $folder.FullName)
    }
    throw
}
Write-Host "Speed Streak 2.08 is ready. Restart Anki."
if ($old.Count) { Write-Host "Previous installations backed up under $session" }
