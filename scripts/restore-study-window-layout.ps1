param(
  [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

Add-Type @'
using System;
using System.Text;
using System.Runtime.InteropServices;

public class StudyLayoutWin32 {
  public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
  [DllImport("user32.dll")] public static extern int GetWindowTextLength(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern IntPtr GetShellWindow();
  [DllImport("user32.dll")] public static extern IntPtr GetWindow(IntPtr hWnd, uint uCmd);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

  public const uint GW_OWNER = 4;
  public const int SW_RESTORE = 9;
  public static readonly IntPtr HWND_TOP = new IntPtr(0);
  public static readonly IntPtr HWND_TOPMOST = new IntPtr(-1);
  public static readonly IntPtr HWND_NOTOPMOST = new IntPtr(-2);
  public const uint SWP_NOACTIVATE = 0x0010;
  public const uint SWP_NOMOVE = 0x0002;
  public const uint SWP_NOSIZE = 0x0001;
  public const uint SWP_SHOWWINDOW = 0x0040;

  [StructLayout(LayoutKind.Sequential)]
  public struct RECT {
    public int Left;
    public int Top;
    public int Right;
    public int Bottom;
  }
}
'@

function Get-DesktopWindows {
  $windows = New-Object System.Collections.Generic.List[object]
  $shell = [StudyLayoutWin32]::GetShellWindow()
  $z = 0

  [StudyLayoutWin32]::EnumWindows({
    param($hWnd, $lParam)

    if ($hWnd -eq $shell) { return $true }
    if (-not [StudyLayoutWin32]::IsWindowVisible($hWnd)) { return $true }
    if ([StudyLayoutWin32]::GetWindow($hWnd, [StudyLayoutWin32]::GW_OWNER) -ne [IntPtr]::Zero) { return $true }

    $length = [StudyLayoutWin32]::GetWindowTextLength($hWnd)
    if ($length -le 0) { return $true }

    $titleBuilder = New-Object System.Text.StringBuilder ($length + 1)
    [void][StudyLayoutWin32]::GetWindowText($hWnd, $titleBuilder, $titleBuilder.Capacity)
    $title = $titleBuilder.ToString().Trim()
    if ([string]::IsNullOrWhiteSpace($title)) { return $true }

    $rect = New-Object StudyLayoutWin32+RECT
    if (-not [StudyLayoutWin32]::GetWindowRect($hWnd, [ref]$rect)) { return $true }

    $pidValue = 0
    [void][StudyLayoutWin32]::GetWindowThreadProcessId($hWnd, [ref]$pidValue)
    $processName = $null
    try {
      $processName = (Get-Process -Id $pidValue -ErrorAction Stop).ProcessName
    } catch {
      $processName = ""
    }

    $script:z++
    $windows.Add([pscustomobject]@{
      Handle = $hWnd
      ZOrder = $script:z
      Process = $processName
      PID = $pidValue
      Title = $title
      Minimized = [StudyLayoutWin32]::IsIconic($hWnd)
      X = $rect.Left
      Y = $rect.Top
      Width = $rect.Right - $rect.Left
      Height = $rect.Bottom - $rect.Top
    })

    return $true
  }, [IntPtr]::Zero) | Out-Null

  return $windows
}

function Get-ScreenByName([string]$deviceName) {
  $screen = [System.Windows.Forms.Screen]::AllScreens | Where-Object { $_.DeviceName -eq $deviceName } | Select-Object -First 1
  if (-not $screen) {
    throw "Required monitor $deviceName was not found."
  }
  return $screen
}

function Get-ChromeWindowByTabTitle($windows, [string]$titleRegex, [string]$label) {
  $chromeWindows = @($windows | Where-Object { $_.Process -eq "chrome" })
  if ($chromeWindows.Count -eq 0) {
    return $null
  }

  $root = [System.Windows.Automation.AutomationElement]::RootElement
  $chromeCondition = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::ClassNameProperty,
    "Chrome_WidgetWin_1"
  )
  $uiWindows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $chromeCondition)

  for ($i = 0; $i -lt $uiWindows.Count; $i++) {
    $uiWindow = $uiWindows.Item($i)
    $nativeHandle = [IntPtr]::new($uiWindow.Current.NativeWindowHandle)
    $desktopWindow = $chromeWindows | Where-Object { $_.Handle -eq $nativeHandle } | Select-Object -First 1
    if (-not $desktopWindow) {
      continue
    }

    $tabCondition = New-Object System.Windows.Automation.PropertyCondition(
      [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
      [System.Windows.Automation.ControlType]::TabItem
    )
    $tabs = $uiWindow.FindAll([System.Windows.Automation.TreeScope]::Descendants, $tabCondition)

    for ($j = 0; $j -lt $tabs.Count; $j++) {
      $tab = $tabs.Item($j)
      if ($tab.Current.Name -notmatch $titleRegex) {
        continue
      }

      if ($WhatIf) {
        Write-Host "Would activate Chrome tab for ${label}: $($tab.Current.Name)"
      } else {
        try {
          $selectionPattern = $tab.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)
          $selectionPattern.Select()
          Start-Sleep -Milliseconds 150
          Write-Host "Activated Chrome tab for ${label}: $($tab.Current.Name)"
        } catch {
          Write-Warning "Found Chrome tab for ${label}, but could not activate it: $($tab.Current.Name)"
        }
      }

      return $desktopWindow
    }
  }

  return $null
}

function Move-DesktopWindow($window, [int]$x, [int]$y, [int]$width, [int]$height, [string]$label) {
  if (-not $window) {
    Write-Host "Skip: $label was not found."
    return
  }

  if ($WhatIf) {
    Write-Host "Would move: $label -> X=$x Y=$y W=$width H=$height [$($window.Process): $($window.Title)]"
    return
  }

  [void][StudyLayoutWin32]::ShowWindow($window.Handle, [StudyLayoutWin32]::SW_RESTORE)
  Start-Sleep -Milliseconds 100

  [void][StudyLayoutWin32]::SetWindowPos(
    $window.Handle,
    [StudyLayoutWin32]::HWND_TOP,
    $x,
    $y,
    $width,
    $height,
    [StudyLayoutWin32]::SWP_SHOWWINDOW -bor [StudyLayoutWin32]::SWP_NOACTIVATE
  )
  Write-Host "Moved: $label -> X=$x Y=$y W=$width H=$height [$($window.Process): $($window.Title)]"
}

function Get-WindowBounds($window) {
  if (-not $window) {
    return $null
  }

  $rect = New-Object StudyLayoutWin32+RECT
  if (-not [StudyLayoutWin32]::GetWindowRect($window.Handle, [ref]$rect)) {
    return $null
  }

  return [pscustomobject]@{
    X = $rect.Left
    Y = $rect.Top
    Width = $rect.Right - $rect.Left
    Height = $rect.Bottom - $rect.Top
  }
}

function Test-WindowBounds($window, [int]$x, [int]$y, [int]$width, [int]$height, [int]$tolerance = 12) {
  $actual = Get-WindowBounds $window
  if (-not $actual) {
    return $false
  }

  return (
    [Math]::Abs($actual.X - $x) -le $tolerance -and
    [Math]::Abs($actual.Y - $y) -le $tolerance -and
    [Math]::Abs($actual.Width - $width) -le $tolerance -and
    [Math]::Abs($actual.Height - $height) -le $tolerance
  )
}

function Bring-ToFront($window, [string]$label) {
  if (-not $window) {
    Write-Host "Skip front: $label was not found."
    return
  }

  if ($WhatIf) {
    Write-Host "Would bring front: $label [$($window.Process): $($window.Title)]"
    return
  }

  if ($window.Minimized) {
    [void][StudyLayoutWin32]::ShowWindow($window.Handle, [StudyLayoutWin32]::SW_RESTORE)
    Start-Sleep -Milliseconds 100
  }

  [void][StudyLayoutWin32]::SetWindowPos(
    $window.Handle,
    [StudyLayoutWin32]::HWND_TOPMOST,
    0,
    0,
    0,
    0,
    [StudyLayoutWin32]::SWP_SHOWWINDOW -bor [StudyLayoutWin32]::SWP_NOMOVE -bor [StudyLayoutWin32]::SWP_NOSIZE
  )
  Start-Sleep -Milliseconds 75
  [void][StudyLayoutWin32]::SetWindowPos(
    $window.Handle,
    [StudyLayoutWin32]::HWND_NOTOPMOST,
    0,
    0,
    0,
    0,
    [StudyLayoutWin32]::SWP_SHOWWINDOW -bor [StudyLayoutWin32]::SWP_NOMOVE -bor [StudyLayoutWin32]::SWP_NOSIZE
  )
  [void][StudyLayoutWin32]::SetForegroundWindow($window.Handle)
  Write-Host "Front: $label [$($window.Process): $($window.Title)]"
}

function Get-LayoutTargets {
  $windows = @(Get-DesktopWindows)
  $chromeWindows = @($windows | Where-Object { $_.Process -eq "chrome" } | Sort-Object ZOrder)
  $chatGptChrome = Get-ChromeWindowByTabTitle $windows "(?i)(ChatGPT|OpenAI|Codex)" "ChatGPT"
  $quizChrome = Get-ChromeWindowByTabTitle $windows "(?i)Quiz" "Quiz"

  if (-not $chatGptChrome) {
    $chatGptChrome = $windows |
      Where-Object { $_.Process -eq "chrome" -and ($_.Title -like "*ChatGPT*" -or $_.Title -like "*OpenAI*" -or $_.Title -like "*Codex*") } |
      Sort-Object ZOrder |
      Select-Object -First 1
  }

  if (-not $quizChrome) {
    $quizChrome = $windows |
      Where-Object { $_.Process -eq "chrome" -and $_.Title -like "*Quiz*" } |
      Sort-Object ZOrder |
      Select-Object -First 1
  }

  if (-not $chatGptChrome) {
    $chatGptChrome = $chromeWindows |
      Where-Object {
        -not $_.Minimized -and
        ($_.X + ($_.Width / 2)) -ge $display3.Bounds.X -and
        ($_.X + ($_.Width / 2)) -lt ($display3.Bounds.X + $display3.Bounds.Width) -and
        ($_.Y + ($_.Height / 2)) -ge $display3.Bounds.Y -and
        ($_.Y + ($_.Height / 2)) -lt ($display3.Bounds.Y + $display3.Bounds.Height)
      } |
      Sort-Object ZOrder |
      Select-Object -First 1
  }

  if (-not $chatGptChrome -and $chromeWindows.Count -eq 1) {
    $chatGptChrome = $chromeWindows[0]
  }

  return [pscustomobject]@{
    Notion = $windows | Where-Object { $_.Process -eq "Notion" } | Sort-Object ZOrder | Select-Object -First 1
    AnkiBrowse = $windows | Where-Object { $_.Process -eq "pythonw" -and $_.Title -like "Browse*" } | Sort-Object ZOrder | Select-Object -First 1
    AnkiAdd = $windows | Where-Object { $_.Process -eq "pythonw" -and $_.Title -eq "Add" } | Sort-Object ZOrder | Select-Object -First 1
    AnkiMain = $windows | Where-Object { $_.Process -eq "pythonw" -and $_.Title -like "*Anki*" -and $_.Title -notlike "Browse*" } | Sort-Object ZOrder | Select-Object -First 1
    Acrobat = $windows | Where-Object { $_.Process -eq "Acrobat" } | Sort-Object ZOrder | Select-Object -First 1
    QuizChrome = $quizChrome
    ChromeWindows = $chromeWindows
    ChatGptChrome = $chatGptChrome
  }
}

function Show-LayoutAlert([string]$message, [string]$title = "Study Window Layout") {
  Write-Warning $message
  if (-not $WhatIf) {
    [void][System.Windows.Forms.MessageBox]::Show(
      $message,
      $title,
      [System.Windows.Forms.MessageBoxButtons]::OK,
      [System.Windows.Forms.MessageBoxIcon]::Warning
    )
  }
}

function Get-MissingRequiredTargetNames($targets) {
  $missing = New-Object System.Collections.Generic.List[string]

  if (-not $targets.Acrobat -and -not $targets.QuizChrome) { $missing.Add("Adobe Acrobat window or Chrome Quiz window") }
  if (-not $targets.AnkiAdd) { $missing.Add("Anki Add window") }
  if (-not $targets.AnkiBrowse) { $missing.Add("Anki Browse window") }
  if (-not $targets.AnkiMain) { $missing.Add("Anki main window") }
  if (-not $targets.Notion) { $missing.Add("Notion window") }
  if (-not $targets.ChatGptChrome) { $missing.Add("Chrome window for ChatGPT") }
  if ($targets.ChatGptChrome -and $targets.QuizChrome -and $targets.ChatGptChrome.Handle -eq $targets.QuizChrome.Handle) {
    $missing.Add("separate Chrome windows for ChatGPT and Quiz; they are tabs in the same Chrome window")
  }

  return @($missing)
}

function Apply-LayoutPass([int]$passNumber) {
  $targets = Get-LayoutTargets

  if (-not $WhatIf) {
    Write-Host "Layout pass $passNumber"
  }

  Move-DesktopWindow $targets.AnkiMain $display2.Bounds.X $display2.Bounds.Y $display2.Bounds.Width ($display2.Bounds.Height - 32) "Anki main, primary display background"

  foreach ($chrome in $targets.ChromeWindows | Where-Object { $_.Handle -ne $(if ($targets.ChatGptChrome) { $targets.ChatGptChrome.Handle } else { [IntPtr]::Zero }) -and $_.Handle -ne $(if ($targets.QuizChrome) { $targets.QuizChrome.Handle } else { [IntPtr]::Zero }) }) {
    Move-DesktopWindow $chrome $d3.X $d3.Y $d3.Width $d3.Height "Chrome on portrait display"
  }

  Move-DesktopWindow $targets.AnkiBrowse ($d1.X - 6) $d1.Y 811 ($d1.Height + 6) "Anki Browse, DISPLAY1 left"
  Move-DesktopWindow $targets.Notion ($d1.X + [int]($d1.Width / 2)) $d1.Y ([int]($d1.Width / 2)) $d1.Height "Notion tracker, DISPLAY1 right"
  Move-DesktopWindow $targets.AnkiAdd ($d2.X + $primaryAddX) $d2.Y $primaryAddWidth $d2.Height "Anki Add, primary display right"
  Move-DesktopWindow $targets.Acrobat $d2.X $d2.Y $primaryAcrobatWidth $d2.Height "Adobe Acrobat, primary display left"
  Move-DesktopWindow $targets.QuizChrome $d2.X $d2.Y $primaryAcrobatWidth $d2.Height "Quiz Chrome, primary display left"

  if ($targets.ChatGptChrome) {
    Move-DesktopWindow $targets.ChatGptChrome $d3.X $d3.Y $d3.Width $d3.Height "ChatGPT Chrome, portrait display"
  }
}

function Repair-LayoutBounds {
  if ($WhatIf) {
    return
  }

  for ($attempt = 1; $attempt -le 3; $attempt++) {
    $targets = Get-LayoutTargets
    $repairs = 0

    $checks = @(
      [pscustomobject]@{ Window = $targets.AnkiMain; X = $display2.Bounds.X; Y = $display2.Bounds.Y; Width = $display2.Bounds.Width; Height = ($display2.Bounds.Height - 32); Label = "Anki main, primary display background" },
      [pscustomobject]@{ Window = $targets.AnkiBrowse; X = ($d1.X - 6); Y = $d1.Y; Width = 811; Height = ($d1.Height + 6); Label = "Anki Browse, DISPLAY1 left" },
      [pscustomobject]@{ Window = $targets.Notion; X = ($d1.X + [int]($d1.Width / 2)); Y = $d1.Y; Width = ([int]($d1.Width / 2)); Height = $d1.Height; Label = "Notion, DISPLAY1 right" },
      [pscustomobject]@{ Window = $targets.AnkiAdd; X = ($d2.X + $primaryAddX); Y = $d2.Y; Width = $primaryAddWidth; Height = $d2.Height; Label = "Anki Add, primary display right" },
      [pscustomobject]@{ Window = $targets.Acrobat; X = $d2.X; Y = $d2.Y; Width = $primaryAcrobatWidth; Height = $d2.Height; Label = "Adobe Acrobat, primary display left" },
      [pscustomobject]@{ Window = $targets.QuizChrome; X = $d2.X; Y = $d2.Y; Width = $primaryAcrobatWidth; Height = $d2.Height; Label = "Quiz Chrome, primary display left" },
      [pscustomobject]@{ Window = $targets.ChatGptChrome; X = $d3.X; Y = $d3.Y; Width = $d3.Width; Height = $d3.Height; Label = "ChatGPT Chrome, portrait display" }
    )

    foreach ($check in $checks) {
      if (-not $check.Window) {
        continue
      }

      if (-not (Test-WindowBounds $check.Window $check.X $check.Y $check.Width $check.Height)) {
        $repairs++
        Move-DesktopWindow $check.Window $check.X $check.Y $check.Width $check.Height $check.Label
      }
    }

    foreach ($chrome in $targets.ChromeWindows | Where-Object { $_.Handle -ne $(if ($targets.ChatGptChrome) { $targets.ChatGptChrome.Handle } else { [IntPtr]::Zero }) -and $_.Handle -ne $(if ($targets.QuizChrome) { $targets.QuizChrome.Handle } else { [IntPtr]::Zero }) }) {
      if (-not (Test-WindowBounds $chrome $d3.X $d3.Y $d3.Width $d3.Height)) {
        $repairs++
        Move-DesktopWindow $chrome $d3.X $d3.Y $d3.Width $d3.Height "Chrome on portrait display"
      }
    }

    if ($repairs -eq 0) {
      Write-Host "Layout bounds verified."
      return
    }

    Write-Host "Repaired $repairs window(s) on verification attempt $attempt."
    Start-Sleep -Milliseconds 250
  }
}

function Apply-FrontOrder {
  $targets = Get-LayoutTargets

  # Apply per-monitor front order after all move/restore work has settled.
  Bring-ToFront $targets.AnkiBrowse "Anki Browse"
  Bring-ToFront $targets.Notion "Notion tracker"
  Bring-ToFront $targets.AnkiAdd "Anki Add"
  Bring-ToFront $targets.Acrobat "Adobe Acrobat"
  Bring-ToFront $targets.QuizChrome "Quiz Chrome"

  foreach ($chrome in $targets.ChromeWindows | Where-Object { $_.Handle -ne $(if ($targets.ChatGptChrome) { $targets.ChatGptChrome.Handle } else { [IntPtr]::Zero }) -and $_.Handle -ne $(if ($targets.QuizChrome) { $targets.QuizChrome.Handle } else { [IntPtr]::Zero }) }) {
    Bring-ToFront $chrome "Chrome"
  }

  Bring-ToFront $targets.ChatGptChrome "ChatGPT Chrome"
}

function Ensure-QuizAboveAcrobat {
  if ($WhatIf) {
    return
  }

  for ($attempt = 1; $attempt -le 3; $attempt++) {
    $targets = Get-LayoutTargets
    if (-not $targets.QuizChrome -or -not $targets.Acrobat) {
      return
    }

    if ($targets.QuizChrome.ZOrder -lt $targets.Acrobat.ZOrder) {
      Write-Host "Quiz Chrome is above Adobe Acrobat."
      return
    }

    Bring-ToFront $targets.QuizChrome "Quiz Chrome"
    Start-Sleep -Milliseconds 150
  }

  $finalTargets = Get-LayoutTargets
  if ($finalTargets.QuizChrome -and $finalTargets.Acrobat -and $finalTargets.QuizChrome.ZOrder -gt $finalTargets.Acrobat.ZOrder) {
    Show-LayoutAlert "The layout ran, but Windows did not keep the Quiz Chrome window in front of Adobe Acrobat. Click the Quiz window or run the shortcut again."
  }
}

$display1 = Get-ScreenByName "\\.\DISPLAY1"
$display2 = Get-ScreenByName "\\.\DISPLAY2"
$display3 = Get-ScreenByName "\\.\DISPLAY3"

$d1 = $display1.WorkingArea
$d2 = $display2.WorkingArea
$d3 = $display3.WorkingArea
$primaryAcrobatWidth = 1022
$primaryAddX = 1013
$primaryAddWidth = $d2.Width - $primaryAddX

Apply-LayoutPass 1
Start-Sleep -Milliseconds 250
Apply-LayoutPass 2
Start-Sleep -Milliseconds 150
Repair-LayoutBounds
Start-Sleep -Milliseconds 150
Apply-FrontOrder
Ensure-QuizAboveAcrobat

$finalTargets = Get-LayoutTargets
$missingTargets = @(Get-MissingRequiredTargetNames $finalTargets)
if ($missingTargets.Count -gt 0) {
  $message = "The study layout ran, but these required windows were missing:`r`n`r`n- " + ($missingTargets -join "`r`n- ") + "`r`n`r`nOpen the missing window(s), then run the shortcut again."
  Show-LayoutAlert $message
  exit 1
}
