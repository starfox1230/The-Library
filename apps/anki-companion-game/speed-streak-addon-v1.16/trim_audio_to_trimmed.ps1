param(
    [string]$SourceDir = "Audio",
    [string]$OutputDir = "Audio_trimmed",
    [double]$StartDurationSeconds = 0.02,
    [double]$WindowSeconds = 0.02,
    [double]$StartThresholdDb = -38.0,
    [switch]$SkipExisting
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceRoot = Join-Path $scriptRoot $SourceDir
$outputRoot = Join-Path $scriptRoot $OutputDir

if (-not (Test-Path $sourceRoot)) {
    throw "Source audio folder not found: $sourceRoot"
}

$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ffmpeg) {
    throw "ffmpeg was not found on PATH. Install ffmpeg first."
}

$supportedExtensions = @(".aac", ".flac", ".m4a", ".mp3", ".oga", ".ogg", ".opus", ".wav")
$filter = "silenceremove=start_periods=1:start_duration=$($StartDurationSeconds):start_threshold=$($StartThresholdDb)dB:detection=peak:window=$($WindowSeconds)"

function Get-EncoderArgs {
    param([string]$Extension)

    switch ($Extension.ToLowerInvariant()) {
        ".aac"  { return @("-c:a", "aac", "-b:a", "192k") }
        ".flac" { return @("-c:a", "flac") }
        ".m4a"  { return @("-c:a", "aac", "-b:a", "192k") }
        ".mp3"  { return @("-c:a", "libmp3lame", "-q:a", "2") }
        ".oga"  { return @("-c:a", "libvorbis", "-q:a", "6") }
        ".ogg"  { return @("-c:a", "libvorbis", "-q:a", "6") }
        ".opus" { return @("-c:a", "libopus", "-b:a", "128k") }
        ".wav"  { return @("-c:a", "pcm_s16le") }
        default { throw "Unsupported extension: $Extension" }
    }
}

$audioFiles = Get-ChildItem -Path $sourceRoot -Recurse -File | Where-Object { $supportedExtensions -contains $_.Extension.ToLowerInvariant() }
if (-not $audioFiles) {
    Write-Host "No supported audio files found under $sourceRoot"
    exit 0
}

$processed = 0
$skipped = 0
$failed = 0

foreach ($file in $audioFiles) {
    $relativePath = $file.FullName.Substring($sourceRoot.Length).TrimStart('\')
    $outputPath = Join-Path $outputRoot $relativePath
    $tempOutputPath = "$outputPath.tmp$($file.Extension)"

    if ($SkipExisting -and (Test-Path $outputPath)) {
        $skipped += 1
        continue
    }

    $outputDirectory = Split-Path -Parent $outputPath
    if (-not (Test-Path $outputDirectory)) {
        New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
    }

    $encoderArgs = Get-EncoderArgs -Extension $file.Extension
    $arguments = @(
        "-nostdin",
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-i", $file.FullName,
        "-af", $filter
    ) + $encoderArgs + @($tempOutputPath)

    try {
        if (Test-Path $tempOutputPath) {
            Remove-Item -Force $tempOutputPath
        }
        if (Test-Path $outputPath) {
            Remove-Item -Force $outputPath
        }
        & $ffmpeg.Source @arguments
        if ($LASTEXITCODE -ne 0) {
            throw "ffmpeg exited with code $LASTEXITCODE"
        }
        Move-Item -Force $tempOutputPath $outputPath
        $processed += 1
    } catch {
        if (Test-Path $tempOutputPath) {
            Remove-Item -Force $tempOutputPath
        }
        $failed += 1
        Write-Warning "Failed to trim $relativePath : $($_.Exception.Message)"
    }
}

Write-Host "Trimmed audio complete."
Write-Host "Processed: $processed"
Write-Host "Skipped:   $skipped"
Write-Host "Failed:    $failed"
Write-Host "Output:    $outputRoot"
Write-Host "Filter:    $filter"
