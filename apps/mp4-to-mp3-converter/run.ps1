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

$script:ConversionWorker = {
  param(
    [string]$FfmpegPath,
    [string]$SourcePath,
    [string]$OutputPath
  )

  $ErrorActionPreference = "Stop"
  try {
    $arguments = @(
      "-hide_banner",
      "-loglevel", "error",
      "-y",
      "-i", $SourcePath,
      "-map", "0:a:0",
      "-vn",
      "-codec:a", "libmp3lame",
      "-q:a", "2",
      $OutputPath
    )

    $escapedArguments = ($arguments | ForEach-Object {
      if ($_ -notmatch '[\s"]') {
        $_
      }
      else {
        '"' + ($_ -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
      }
    }) -join ' '

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $FfmpegPath
    $startInfo.Arguments = $escapedArguments
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardError = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    [void]$process.Start()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()

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

    [pscustomobject]@{
      InputPath = $SourcePath
      OutputPath = $OutputPath
    }
  }
  finally {
    if ($process) {
      $process.Dispose()
    }
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
  }
}

function Convert-Direct {
  param(
    [Parameter(Mandatory = $true)]
    [string]$SourcePath
  )

  $conversion = Prepare-Conversion -SourcePath $SourcePath
  return & $script:ConversionWorker $conversion.FfmpegPath $conversion.SourcePath $conversion.OutputPath
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
  Border = [System.Drawing.Color]::FromArgb(43, 60, 87)
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
$form.ClientSize = New-Object System.Drawing.Size(640, 340)
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
$form.MaximizeBox = $false
$form.BackColor = $palette.Background
$form.ForeColor = $palette.Text
$form.Font = $fontBody

$card = New-Object System.Windows.Forms.Panel
$card.Location = New-Object System.Drawing.Point(20, 20)
$card.Size = New-Object System.Drawing.Size(600, 300)
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
$subtitleLabel.Text = "Choose an MP4, wait for the short conversion, and the MP3 lands beside the original file."
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
$detailLabel.Size = New-Object System.Drawing.Size(552, 40)
$detailLabel.ForeColor = $palette.Muted
$detailLabel.Text = "The app opens a file picker immediately when it launches."
$card.Controls.Add($detailLabel)

$progressBar = New-Object System.Windows.Forms.ProgressBar
$progressBar.Location = New-Object System.Drawing.Point(24, 248)
$progressBar.Size = New-Object System.Drawing.Size(552, 12)
$progressBar.Style = [System.Windows.Forms.ProgressBarStyle]::Marquee
$progressBar.MarqueeAnimationSpeed = 30
$progressBar.Visible = $false
$card.Controls.Add($progressBar)

$chooseButton = New-Object System.Windows.Forms.Button
$chooseButton.Location = New-Object System.Drawing.Point(24, 270)
$chooseButton.Size = New-Object System.Drawing.Size(150, 34)
$chooseButton.Text = "Choose MP4"
$card.Controls.Add($chooseButton)

$openFolderButton = New-Object System.Windows.Forms.Button
$openFolderButton.Location = New-Object System.Drawing.Point(188, 270)
$openFolderButton.Size = New-Object System.Drawing.Size(150, 34)
$openFolderButton.Text = "Open Folder"
$openFolderButton.Visible = $false
$card.Controls.Add($openFolderButton)

$closeButton = New-Object System.Windows.Forms.Button
$closeButton.Location = New-Object System.Drawing.Point(426, 270)
$closeButton.Size = New-Object System.Drawing.Size(150, 34)
$closeButton.Text = "Close"
$card.Controls.Add($closeButton)

$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Filter = "MP4 files (*.mp4)|*.mp4"
$dialog.Title = "Choose an MP4 file"
$dialog.Multiselect = $false

$script:IsBusy = $false
$script:LastOutputPath = $null
$script:AutoPrompted = $false

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

function Set-BusyState {
  param(
    [string]$SourcePath,
    [string]$OutputPath
  )

  $script:IsBusy = $true
  $script:LastOutputPath = $null
  $pathTextBox.Text = $SourcePath
  $chooseButton.Enabled = $false
  $openFolderButton.Visible = $false
  $progressBar.Visible = $true
  $form.UseWaitCursor = $true
  Set-StatusText -Headline "Converting..." -Details ("Creating " + [System.IO.Path]::GetFileName($OutputPath) + " in the same folder.") -Color $palette.Accent
  $form.Refresh()
}

function Set-IdleState {
  $script:IsBusy = $false
  $chooseButton.Enabled = $true
  $progressBar.Visible = $false
  $form.UseWaitCursor = $false
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
    [string]$OutputPath
  )

  Set-IdleState
  $script:LastOutputPath = $OutputPath
  $pathTextBox.Text = $SourcePath
  $chooseButton.Text = "Convert Another"
  $openFolderButton.Visible = $true
  Set-StatusText -Headline "Finished." -Details ("Created " + [System.IO.Path]::GetFileName($OutputPath) + " next to the original video.") -Color $palette.Success
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

  Set-BusyState -SourcePath $conversion.SourcePath -OutputPath $conversion.OutputPath

  $job = Start-Job -ScriptBlock $script:ConversionWorker -ArgumentList $conversion.FfmpegPath, $conversion.SourcePath, $conversion.OutputPath
  try {
    while ($job.State -eq "NotStarted" -or $job.State -eq "Running") {
      [System.Windows.Forms.Application]::DoEvents()
      Start-Sleep -Milliseconds 150
    }

    if ($job.State -eq "Completed") {
      $result = Receive-Job -Job $job -ErrorAction Stop
      Show-ConversionSuccess -SourcePath $result.InputPath -OutputPath $result.OutputPath
      return
    }

    $reason = $job.ChildJobs[0].JobStateInfo.Reason
    if ($reason -and -not [string]::IsNullOrWhiteSpace($reason.Message)) {
      Show-ConversionError -MessageText $reason.Message
    }
    else {
      Show-ConversionError -MessageText "ffmpeg did not complete successfully."
    }
  }
  finally {
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
  }
}

function Choose-And-Convert {
  if ($script:IsBusy) {
    return
  }

  if (-not [string]::IsNullOrWhiteSpace($pathTextBox.Text)) {
    $dialog.InitialDirectory = Split-Path -Path $pathTextBox.Text -Parent
  }

  if ($dialog.ShowDialog($form) -ne [System.Windows.Forms.DialogResult]::OK) {
    if ([string]::IsNullOrWhiteSpace($pathTextBox.Text)) {
      Set-StatusText -Headline "Select an MP4 to begin." -Details "Choose a file and the app will write the MP3 beside it." -Color $palette.Accent
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
$form.Add_Shown({
  if (-not $script:AutoPrompted) {
    $script:AutoPrompted = $true
    Choose-And-Convert
  }
})

[void]$form.ShowDialog()
