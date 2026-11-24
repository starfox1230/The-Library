param(
    [double]$FadeInSeconds = 0.003
)

$ErrorActionPreference = "Stop"
$scriptRoot = [System.IO.Path]::GetFullPath((Split-Path -Parent $MyInvocation.MyCommand.Path))
$audioRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptRoot "Audio_trimmed"))
$audioPrefix = $audioRoot.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
$ffmpeg = Get-Command ffmpeg -ErrorAction Stop

if (-not (Test-Path -LiteralPath $audioRoot -PathType Container)) {
    throw "Audio folder not found: $audioRoot"
}

$files = Get-ChildItem -LiteralPath $audioRoot -Recurse -File -Filter "*.wav" | Where-Object {
    $_.FullName -notlike "*\countdown-cues\*"
}

foreach ($file in $files) {
    $target = [System.IO.Path]::GetFullPath($file.FullName)
    if (-not $target.StartsWith($audioPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to modify a path outside Audio_trimmed: $target"
    }

    $temporary = "$target.fade.tmp.wav"
    if (Test-Path -LiteralPath $temporary) {
        Remove-Item -LiteralPath $temporary -Force
    }

    & $ffmpeg.Source `
        -nostdin `
        -hide_banner `
        -loglevel error `
        -y `
        -i $target `
        -af "afade=t=in:st=0:d=$FadeInSeconds" `
        -c:a pcm_s16le `
        $temporary

    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $temporary -PathType Leaf)) {
        throw "ffmpeg failed to process: $target"
    }
    if ((Get-Item -LiteralPath $temporary).Length -le 44) {
        throw "ffmpeg produced an invalid WAV: $temporary"
    }

    Move-Item -LiteralPath $temporary -Destination $target -Force
    Write-Host "Faded: $($target.Substring($audioPrefix.Length))"
}

Write-Host "Processed $($files.Count) event WAV files with a $FadeInSeconds-second fade-in."
