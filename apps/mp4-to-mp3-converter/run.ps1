param(
  [Parameter(Position = 0)]
  [string]$SourcePath
)

$ErrorActionPreference = "Stop"

function Get-RequiredCommandPath {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Name
  )

  $command = Get-Command $Name -ErrorAction SilentlyContinue
  if (-not $command) {
    throw "Required dependency '$Name' was not found on PATH."
  }

  return $command.Source
}

function Get-OptionalCommandPath {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Name
  )

  $command = Get-Command $Name -ErrorAction SilentlyContinue
  if ($command) {
    return $command.Source
  }

  return $null
}

function ConvertTo-QuotedArgumentString {
  param(
    [Parameter(Mandatory = $true)]
    [string[]]$Arguments
  )

  return (($Arguments | ForEach-Object {
    if ($_ -notmatch '[\s"]') {
      $_
    }
    else {
      '"' + ($_ -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
    }
  }) -join ' ')
}

function Resolve-AvailableOutputPath {
  param(
    [Parameter(Mandatory = $true)]
    [string]$SourcePath
  )

  $directory = Split-Path -Path $SourcePath -Parent
  $baseName = [System.IO.Path]::GetFileNameWithoutExtension($SourcePath)
  $candidate = Join-Path $directory ($baseName + ".mp3")
  $suffix = 1

  while (Test-Path -LiteralPath $candidate) {
    $candidate = Join-Path $directory ("{0} ({1}).mp3" -f $baseName, $suffix)
    $suffix += 1
  }

  return $candidate
}

function Test-InputPath {
  param(
    [Parameter(Mandatory = $true)]
    [string]$SourcePath
  )

  if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) {
    throw "The selected file does not exist."
  }

  $resolvedPath = (Resolve-Path -LiteralPath $SourcePath).Path
  $extension = [System.IO.Path]::GetExtension($resolvedPath)
  if ($extension -notmatch '^(?i)\.mp4$') {
    throw "Please choose an MP4 file."
  }

  return $resolvedPath
}

function Test-HasAudioStream {
  param(
    [Parameter(Mandatory = $true)]
    [string]$SourcePath,
    [string]$FfprobePath
  )

  if ([string]::IsNullOrWhiteSpace($FfprobePath)) {
    return $true
  }

  $probeOutput = & $FfprobePath "-v" "error" "-select_streams" "a:0" "-show_entries" "stream=index" "-of" "csv=p=0" $SourcePath 2>$null
  return -not [string]::IsNullOrWhiteSpace(($probeOutput | Out-String))
}

function Get-MediaDurationSeconds {
  param(
    [Parameter(Mandatory = $true)]
    [string]$SourcePath,
    [string]$FfprobePath
  )

  if ([string]::IsNullOrWhiteSpace($FfprobePath)) {
    return $null
  }

  $durationText = & $FfprobePath "-v" "error" "-show_entries" "format=duration" "-of" "default=nw=1:nk=1" $SourcePath 2>$null
  $durationText = ($durationText | Out-String).Trim()
  $durationSeconds = 0.0

  if ([double]::TryParse($durationText, [System.Globalization.NumberStyles]::Float, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$durationSeconds) -and $durationSeconds -gt 0) {
    return $durationSeconds
  }

  return $null
}

function Get-FormattedTimeLabel {
  param(
    [double]$Seconds
  )

  if (-not [double]::IsFinite($Seconds) -or $Seconds -lt 0) {
    return "--:--"
  }

  $span = [System.TimeSpan]::FromSeconds($Seconds)
  if ($span.TotalHours -ge 1) {
    return "{0:00}:{1:00}:{2:00}" -f [int]$span.TotalHours, $span.Minutes, $span.Seconds
  }

  return "{0:00}:{1:00}" -f $span.Minutes, $span.Seconds
}

function Get-ConversionProgressState {
  param(
    [Parameter(Mandatory = $true)]
    [string]$ProgressPath,
    [Nullable[double]]$DurationSeconds
  )

  if (-not (Test-Path -LiteralPath $ProgressPath -PathType Leaf)) {
    return $null
  }

  try {
    $lines = Get-Content -LiteralPath $ProgressPath -ErrorAction Stop
  }
  catch {
    return $null
  }

  $values = @{}
  foreach ($line in $lines) {
    $separatorIndex = $line.IndexOf("=")
    if ($separatorIndex -lt 1) {
      continue
    }

    $key = $line.Substring(0, $separatorIndex)
    $value = $line.Substring($separatorIndex + 1)
    $values[$key] = $value
  }

  $processedSeconds = 0.0
  $rawMicroseconds = 0.0
  if ($values.ContainsKey("out_time_us") -and [double]::TryParse($values["out_time_us"], [System.Globalization.NumberStyles]::Float, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$rawMicroseconds)) {
    $processedSeconds = $rawMicroseconds / 1000000.0
  }
  elseif ($values.ContainsKey("out_time_ms") -and [double]::TryParse($values["out_time_ms"], [System.Globalization.NumberStyles]::Float, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$rawMicroseconds)) {
    $processedSeconds = $rawMicroseconds / 1000000.0
  }
  elseif ($values.ContainsKey("out_time")) {
    $parsedSpan = [System.TimeSpan]::Zero
    if ([System.TimeSpan]::TryParse($values["out_time"], [ref]$parsedSpan)) {
      $processedSeconds = $parsedSpan.TotalSeconds
    }
  }

  $fraction = $null
  if ($DurationSeconds -and $DurationSeconds.Value -gt 0) {
    $fraction = [Math]::Min(1.0, [Math]::Max(0.0, $processedSeconds / $DurationSeconds.Value))
  }

  if ($values["progress"] -eq "end") {
    $fraction = 1.0
    if ($DurationSeconds -and $DurationSeconds.Value -gt 0) {
      $processedSeconds = $DurationSeconds.Value
    }
  }

  [pscustomobject]@{
    ProcessedSeconds = $processedSeconds
    Fraction = $fraction
    State = $values["progress"]
  }
}

function Invoke-FfmpegConversion {
  param(
    [Parameter(Mandatory = $true)]
    [string]$FfmpegPath,
    [Parameter(Mandatory = $true)]
    [string]$SourcePath,
    [Parameter(Mandatory = $true)]
    [string]$OutputPath,
    [Nullable[double]]$DurationSeconds,
    [scriptblock]$OnProgress,
    [switch]$PumpMessages
  )

  $progressPath = Join-Path ([System.IO.Path]::GetTempPath()) ("mp4-to-mp3-progress-" + [System.Guid]::NewGuid().ToString("N") + ".txt")
  $process = $null

  try {
    $arguments = @(
      "-hide_banner",
      "-loglevel", "error",
      "-nostats",
      "-progress", $progressPath,
      "-y",
      "-i", $SourcePath,
      "-map", "0:a:0",
      "-vn",
      "-codec:a", "libmp3lame",
      "-q:a", "2",
      $OutputPath
    )

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $FfmpegPath
    $startInfo.Arguments = ConvertTo-QuotedArgumentString -Arguments $arguments
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardError = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    [void]$process.Start()

    while (-not $process.HasExited) {
      if ($OnProgress) {
        $progress = Get-ConversionProgressState -ProgressPath $progressPath -DurationSeconds $DurationSeconds
        if ($progress) {
          & $OnProgress $progress
        }
      }

      if ($PumpMessages) {
        [System.Windows.Forms.Application]::DoEvents()
      }

      Start-Sleep -Milliseconds 120
    }

    $stderr = $process.StandardError.ReadToEnd()

    if ($OnProgress) {
      $finalProgress = Get-ConversionProgressState -ProgressPath $progressPath -DurationSeconds $DurationSeconds
      if ($finalProgress) {
        & $OnProgress $finalProgress
      }
    }

    if ($process.ExitCode -ne 0) {
      if (Test-Path -LiteralPath $OutputPath) {
        Remove-Item -LiteralPath $OutputPath -Force -ErrorAction SilentlyContinue
      }

      if ([string]::IsNullOrWhiteSpace($stderr)) {
        $stderr = "ffmpeg exited with code $($process.ExitCode)."
      }

      throw $stderr.Trim()
    }

    if (-not (Test-Path -LiteralPath $OutputPath)) {
      throw "The conversion finished without creating an MP3 file."
    }

    if ($OnProgress) {
      & $OnProgress ([pscustomobject]@{
        ProcessedSeconds = if ($DurationSeconds) { $DurationSeconds.Value } else { 0.0 }
        Fraction = 1.0
        State = "end"
      })
    }

    [pscustomobject]@{
      InputPath = $SourcePath
      OutputPath = $OutputPath
      DurationSeconds = $DurationSeconds
    }
  }
  finally {
    if ($process) {
      $process.Dispose()
    }

    Remove-Item -LiteralPath $progressPath -Force -ErrorAction SilentlyContinue
  }
}

function Prepare-Conversion {
  param(
    [Parameter(Mandatory = $true)]
    [string]$SourcePath
  )

  $resolvedSourcePath = Test-InputPath -SourcePath $SourcePath
  $ffmpegPath = Get-RequiredCommandPath -Name "ffmpeg"
  $ffprobePath = Get-OptionalCommandPath -Name "ffprobe"

  if (-not (Test-HasAudioStream -SourcePath $resolvedSourcePath -FfprobePath $ffprobePath)) {
    throw "The selected MP4 does not contain an audio stream."
  }

  [pscustomobject]@{
    SourcePath = $resolvedSourcePath
    OutputPath = Resolve-AvailableOutputPath -SourcePath $resolvedSourcePath
    FfmpegPath = $ffmpegPath
    FfprobePath = $ffprobePath
    DurationSeconds = Get-MediaDurationSeconds -SourcePath $resolvedSourcePath -FfprobePath $ffprobePath
  }
}

function Convert-Direct {
  param(
    [Parameter(Mandatory = $true)]
    [string]$SourcePath
  )

  $conversion = Prepare-Conversion -SourcePath $SourcePath
  return Invoke-FfmpegConversion -FfmpegPath $conversion.FfmpegPath -SourcePath $conversion.SourcePath -OutputPath $conversion.OutputPath -DurationSeconds $conversion.DurationSeconds
}

if ($PSBoundParameters.ContainsKey("SourcePath")) {
  try {
    $result = Convert-Direct -SourcePath $SourcePath
    Write-Output $result.OutputPath
    exit 0
  }
  catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
  }
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

$palette = @{
  Background = [System.Drawing.Color]::FromArgb(11, 15, 24)
  Panel = [System.Drawing.Color]::FromArgb(20, 28, 43)
  Text = [System.Drawing.Color]::FromArgb(240, 244, 250)
  Muted = [System.Drawing.Color]::FromArgb(162, 176, 198)
  Accent = [System.Drawing.Color]::FromArgb(89, 214, 255)
  Success = [System.Drawing.Color]::FromArgb(113, 214, 154)
  Error = [System.Drawing.Color]::FromArgb(255, 132, 132)
}

$fontBody = New-Object System.Drawing.Font("Segoe UI", 10)
$fontTitle = New-Object System.Drawing.Font("Segoe UI Semibold", 18)
$fontStatus = New-Object System.Drawing.Font("Segoe UI Semibold", 11)

$form = New-Object System.Windows.Forms.Form
$form.Text = "MP4 to MP3 Converter"
$form.StartPosition = "CenterScreen"
$form.ClientSize = New-Object System.Drawing.Size(640, 360)
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
$form.MaximizeBox = $false
$form.BackColor = $palette.Background
$form.ForeColor = $palette.Text
$form.Font = $fontBody

$card = New-Object System.Windows.Forms.Panel
$card.Location = New-Object System.Drawing.Point(20, 20)
$card.Size = New-Object System.Drawing.Size(600, 320)
$card.BackColor = $palette.Panel
$card.BorderStyle = [System.Windows.Forms.BorderStyle]::FixedSingle
$form.Controls.Add($card)

$titleLabel = New-Object System.Windows.Forms.Label
$titleLabel.Location = New-Object System.Drawing.Point(24, 22)
$titleLabel.Size = New-Object System.Drawing.Size(360, 34)
$titleLabel.Font = $fontTitle
$titleLabel.ForeColor = $palette.Text
$titleLabel.Text = "MP4 to MP3 Converter"
$card.Controls.Add($titleLabel)

$subtitleLabel = New-Object System.Windows.Forms.Label
$subtitleLabel.Location = New-Object System.Drawing.Point(24, 62)
$subtitleLabel.Size = New-Object System.Drawing.Size(540, 34)
$subtitleLabel.ForeColor = $palette.Muted
$subtitleLabel.Text = "Choose an MP4, then watch the progress until the MP3 is finished in the same folder."
$card.Controls.Add($subtitleLabel)

$pathCaptionLabel = New-Object System.Windows.Forms.Label
$pathCaptionLabel.Location = New-Object System.Drawing.Point(24, 110)
$pathCaptionLabel.Size = New-Object System.Drawing.Size(220, 20)
$pathCaptionLabel.ForeColor = $palette.Muted
$pathCaptionLabel.Text = "Selected source video"
$card.Controls.Add($pathCaptionLabel)

$pathTextBox = New-Object System.Windows.Forms.TextBox
$pathTextBox.Location = New-Object System.Drawing.Point(24, 136)
$pathTextBox.Size = New-Object System.Drawing.Size(552, 28)
$pathTextBox.ReadOnly = $true
$pathTextBox.BackColor = [System.Drawing.Color]::FromArgb(14, 20, 31)
$pathTextBox.ForeColor = $palette.Text
$pathTextBox.BorderStyle = [System.Windows.Forms.BorderStyle]::FixedSingle
$card.Controls.Add($pathTextBox)

$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Location = New-Object System.Drawing.Point(24, 184)
$statusLabel.Size = New-Object System.Drawing.Size(552, 22)
$statusLabel.Font = $fontStatus
$statusLabel.ForeColor = $palette.Accent
$statusLabel.Text = "Select an MP4 to begin."
$card.Controls.Add($statusLabel)

$detailLabel = New-Object System.Windows.Forms.Label
$detailLabel.Location = New-Object System.Drawing.Point(24, 210)
$detailLabel.Size = New-Object System.Drawing.Size(552, 34)
$detailLabel.ForeColor = $palette.Muted
$detailLabel.Text = "The app opens a file picker immediately when it launches."
$card.Controls.Add($detailLabel)

$progressLabel = New-Object System.Windows.Forms.Label
$progressLabel.Location = New-Object System.Drawing.Point(24, 246)
$progressLabel.Size = New-Object System.Drawing.Size(552, 18)
$progressLabel.ForeColor = $palette.Muted
$progressLabel.Text = "0% complete"
$progressLabel.Visible = $false
$card.Controls.Add($progressLabel)

$progressBar = New-Object System.Windows.Forms.ProgressBar
$progressBar.Location = New-Object System.Drawing.Point(24, 268)
$progressBar.Size = New-Object System.Drawing.Size(552, 14)
$progressBar.Style = [System.Windows.Forms.ProgressBarStyle]::Continuous
$progressBar.Minimum = 0
$progressBar.Maximum = 100
$progressBar.Value = 0
$progressBar.Visible = $false
$card.Controls.Add($progressBar)

$chooseButton = New-Object System.Windows.Forms.Button
$chooseButton.Location = New-Object System.Drawing.Point(24, 286)
$chooseButton.Size = New-Object System.Drawing.Size(150, 34)
$chooseButton.Text = "Choose MP4"
$card.Controls.Add($chooseButton)

$openFolderButton = New-Object System.Windows.Forms.Button
$openFolderButton.Location = New-Object System.Drawing.Point(188, 286)
$openFolderButton.Size = New-Object System.Drawing.Size(150, 34)
$openFolderButton.Text = "Open Folder"
$openFolderButton.Visible = $false
$card.Controls.Add($openFolderButton)

$closeButton = New-Object System.Windows.Forms.Button
$closeButton.Location = New-Object System.Drawing.Point(426, 286)
$closeButton.Size = New-Object System.Drawing.Size(150, 34)
$closeButton.Text = "Close"
$card.Controls.Add($closeButton)

$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Filter = "MP4 files (*.mp4)|*.mp4"
$dialog.Title = "Choose an MP4 file"
$dialog.Multiselect = $false

$startupTimer = New-Object System.Windows.Forms.Timer
$startupTimer.Interval = 150

$script:IsBusy = $false
$script:LastOutputPath = $null
$script:AutoPrompted = $false
$script:CurrentDurationSeconds = $null

function Show-AppWindow {
  $form.WindowState = [System.Windows.Forms.FormWindowState]::Normal
  $form.ShowInTaskbar = $true
  $form.Activate()
  $form.BringToFront()
  $form.TopMost = $true
  $form.TopMost = $false
}

function Show-CompletionDialog {
  param(
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
  )

  $fileName = [System.IO.Path]::GetFileName($OutputPath)
  $directory = Split-Path -Path $OutputPath -Parent
  $message = "Finished creating:`n`n$fileName`n`nin:`n$directory"

  Show-AppWindow
  [System.Media.SystemSounds]::Asterisk.Play()
  [void][System.Windows.Forms.MessageBox]::Show(
    $form,
    $message,
    "MP4 to MP3 Converter",
    [System.Windows.Forms.MessageBoxButtons]::OK,
    [System.Windows.Forms.MessageBoxIcon]::Information
  )
}

function Reset-ProgressDisplay {
  $progressBar.Visible = $false
  $progressBar.Style = [System.Windows.Forms.ProgressBarStyle]::Continuous
  $progressBar.Value = 0
  $progressLabel.Visible = $false
  $progressLabel.Text = "0% complete"
}

function Set-StatusText {
  param(
    [string]$Headline,
    [string]$Details,
    [System.Drawing.Color]$Color
  )

  $statusLabel.Text = $Headline
  $statusLabel.ForeColor = $Color
  $detailLabel.Text = $Details
}

function Update-ProgressDisplay {
  param(
    [pscustomobject]$ProgressState
  )

  $progressBar.Visible = $true
  $progressLabel.Visible = $true

  $durationSeconds = if ($script:CurrentDurationSeconds) { $script:CurrentDurationSeconds.Value } else { $null }
  $processedSeconds = [Math]::Max(0.0, $ProgressState.ProcessedSeconds)

  if ($durationSeconds -and $durationSeconds -gt 0 -and $ProgressState.Fraction -ne $null) {
    $clampedFraction = [Math]::Min(1.0, [Math]::Max(0.0, [double]$ProgressState.Fraction))
    $percent = [Math]::Min(100, [Math]::Max(0, [int][Math]::Round($clampedFraction * 100)))
    $displayProcessed = [Math]::Min($processedSeconds, $durationSeconds)

    $progressBar.Style = [System.Windows.Forms.ProgressBarStyle]::Continuous
    $progressBar.Value = $percent
    $progressLabel.Text = "{0}% complete ({1} of {2})" -f $percent, (Get-FormattedTimeLabel -Seconds $displayProcessed), (Get-FormattedTimeLabel -Seconds $durationSeconds)
    $statusLabel.Text = if ($percent -lt 100) { "Converting... $percent%" } else { "Finishing up..." }
    return
  }

  $progressBar.Style = [System.Windows.Forms.ProgressBarStyle]::Marquee
  $progressBar.MarqueeAnimationSpeed = 30
  $progressLabel.Text = "Conversion in progress..."
  $statusLabel.Text = "Converting..."
}

function Set-BusyState {
  param(
    [string]$SourcePath,
    [string]$OutputPath,
    [Nullable[double]]$DurationSeconds
  )

  $script:IsBusy = $true
  $script:LastOutputPath = $null
  $script:CurrentDurationSeconds = $DurationSeconds
  $pathTextBox.Text = $SourcePath
  $chooseButton.Enabled = $false
  $openFolderButton.Visible = $false
  $form.UseWaitCursor = $true

  if ($DurationSeconds -and $DurationSeconds.Value -gt 0) {
    $progressBar.Visible = $true
    $progressBar.Style = [System.Windows.Forms.ProgressBarStyle]::Continuous
    $progressBar.Value = 0
    $progressLabel.Visible = $true
    $progressLabel.Text = "0% complete (00:00 of {0})" -f (Get-FormattedTimeLabel -Seconds $DurationSeconds.Value)
    Set-StatusText -Headline "Converting... 0%" -Details ("Creating " + [System.IO.Path]::GetFileName($OutputPath) + " in the same folder.") -Color $palette.Accent
  }
  else {
    $progressBar.Visible = $true
    $progressBar.Style = [System.Windows.Forms.ProgressBarStyle]::Marquee
    $progressBar.MarqueeAnimationSpeed = 30
    $progressLabel.Visible = $true
    $progressLabel.Text = "Conversion in progress..."
    Set-StatusText -Headline "Converting..." -Details ("Creating " + [System.IO.Path]::GetFileName($OutputPath) + " in the same folder.") -Color $palette.Accent
  }

  Show-AppWindow
  $form.Refresh()
}

function Set-IdleState {
  param(
    [switch]$KeepProgressVisible
  )

  $script:IsBusy = $false
  $script:CurrentDurationSeconds = $null
  $chooseButton.Enabled = $true
  $form.UseWaitCursor = $false

  if (-not $KeepProgressVisible) {
    Reset-ProgressDisplay
  }
}

function Show-ConversionError {
  param(
    [string]$MessageText
  )

  Set-IdleState
  Set-StatusText -Headline "Conversion failed." -Details $MessageText -Color $palette.Error
}

function Show-ConversionSuccess {
  param(
    [string]$SourcePath,
    [string]$OutputPath,
    [Nullable[double]]$DurationSeconds
  )

  Set-IdleState -KeepProgressVisible
  $script:LastOutputPath = $OutputPath
  $pathTextBox.Text = $SourcePath
  $chooseButton.Text = "Convert Another"
  $openFolderButton.Visible = $true
  $progressBar.Visible = $true
  $progressBar.Style = [System.Windows.Forms.ProgressBarStyle]::Continuous
  $progressBar.Value = 100
  $progressLabel.Visible = $true

  if ($DurationSeconds -and $DurationSeconds.Value -gt 0) {
    $progressLabel.Text = "100% complete ({0} of {1})" -f (Get-FormattedTimeLabel -Seconds $DurationSeconds.Value), (Get-FormattedTimeLabel -Seconds $DurationSeconds.Value)
  }
  else {
    $progressLabel.Text = "Finished"
  }

  Set-StatusText -Headline "Finished." -Details ("Created " + [System.IO.Path]::GetFileName($OutputPath) + " next to the original video.") -Color $palette.Success
  Show-CompletionDialog -OutputPath $OutputPath
}

function Start-Conversion {
  param(
    [Parameter(Mandatory = $true)]
    [string]$SourcePath
  )

  try {
    $conversion = Prepare-Conversion -SourcePath $SourcePath
  }
  catch {
    Show-ConversionError -MessageText $_.Exception.Message
    return
  }

  Set-BusyState -SourcePath $conversion.SourcePath -OutputPath $conversion.OutputPath -DurationSeconds $conversion.DurationSeconds

  try {
    $result = Invoke-FfmpegConversion -FfmpegPath $conversion.FfmpegPath -SourcePath $conversion.SourcePath -OutputPath $conversion.OutputPath -DurationSeconds $conversion.DurationSeconds -PumpMessages -OnProgress {
      param($progressState)
      Update-ProgressDisplay -ProgressState $progressState
    }

    Show-ConversionSuccess -SourcePath $result.InputPath -OutputPath $result.OutputPath -DurationSeconds $result.DurationSeconds
  }
  catch {
    Show-ConversionError -MessageText $_.Exception.Message
  }
}

function Choose-And-Convert {
  if ($script:IsBusy) {
    return
  }

  Show-AppWindow

  if (-not [string]::IsNullOrWhiteSpace($pathTextBox.Text)) {
    $dialog.InitialDirectory = Split-Path -Path $pathTextBox.Text -Parent
  }

  $dialogResult = $dialog.ShowDialog($form)
  Show-AppWindow

  if ($dialogResult -ne [System.Windows.Forms.DialogResult]::OK) {
    if ([string]::IsNullOrWhiteSpace($pathTextBox.Text)) {
      Reset-ProgressDisplay
      Set-StatusText -Headline "Select an MP4 to begin." -Details "Choose a file and the app will show percent complete while it writes the MP3 beside it." -Color $palette.Accent
    }
    return
  }

  $chooseButton.Text = "Choose MP4"
  Start-Conversion -SourcePath $dialog.FileName
}

$chooseButton.Add_Click({ Choose-And-Convert })
$openFolderButton.Add_Click({
  if ($script:LastOutputPath -and (Test-Path -LiteralPath $script:LastOutputPath)) {
    Start-Process explorer.exe -ArgumentList "/select,`"$script:LastOutputPath`""
  }
})
$closeButton.Add_Click({ $form.Close() })
$form.Add_FormClosing({
  if ($script:IsBusy) {
    $_.Cancel = $true
  }
})
$startupTimer.Add_Tick({
  $startupTimer.Stop()
  if (-not $script:AutoPrompted) {
    $script:AutoPrompted = $true
    Choose-And-Convert
  }
})
$form.Add_Shown({
  Show-AppWindow
  $startupTimer.Start()
})

[void]$form.ShowDialog()
