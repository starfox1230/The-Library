param([switch]$Test)
$ErrorActionPreference = 'Stop'
$compilerPath = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $compilerPath)) {
    $compilerPath = Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe'
}
if (-not (Test-Path -LiteralPath $compilerPath)) { throw '.NET Framework 4 compiler was not found.' }
$frameworkPath = Split-Path -Parent $compilerPath
$outputPath = Join-Path $PSScriptRoot 'dist'
New-Item -ItemType Directory -Path $outputPath -Force | Out-Null
$refs = @('System.dll', 'System.Core.dll', 'System.Windows.Forms.dll', 'System.Drawing.dll', 'System.Runtime.Serialization.dll')
$refs += @('WPF\UIAutomationClient.dll', 'WPF\UIAutomationTypes.dll', 'WPF\WindowsBase.dll')
$arguments = @('/nologo', '/optimize+', '/platform:anycpu', '/target:winexe', '/main:ReportExporter.Program')
$arguments += '/out:' + (Join-Path $outputPath 'PowerScribeReportExporter.exe')
$arguments += $refs | ForEach-Object { '/reference:' + (Join-Path $frameworkPath $_) }
$arguments += @((Join-Path $PSScriptRoot 'Core.cs'), (Join-Path $PSScriptRoot 'LauncherSupport.cs'), (Join-Path $PSScriptRoot 'WindowsSession.cs'), (Join-Path $PSScriptRoot 'NativeClipboard.cs'), (Join-Path $PSScriptRoot 'KeyboardSession.cs'), (Join-Path $PSScriptRoot 'NightTheme.cs'), (Join-Path $PSScriptRoot 'Program.cs'))
& $compilerPath @arguments
if ($LASTEXITCODE -ne 0) { throw 'Executable compilation failed.' }
if ($Test) {
    $testArguments = @('/nologo', '/optimize+', '/platform:anycpu', '/target:exe', '/main:ReportExporter.Tests')
    $testArguments += '/out:' + (Join-Path $outputPath 'ExporterTests.exe')
    $testArguments += $refs | ForEach-Object { '/reference:' + (Join-Path $frameworkPath $_) }
    $testArguments += @((Join-Path $PSScriptRoot 'Core.cs'), (Join-Path $PSScriptRoot 'LauncherSupport.cs'), (Join-Path $PSScriptRoot 'WindowsSession.cs'), (Join-Path $PSScriptRoot 'NativeClipboard.cs'), (Join-Path $PSScriptRoot 'KeyboardSession.cs'), (Join-Path $PSScriptRoot 'NightTheme.cs'), (Join-Path $PSScriptRoot 'Program.cs'), (Join-Path $PSScriptRoot 'LauncherChecks.cs'), (Join-Path $PSScriptRoot 'Tests.cs'))
    & $compilerPath @testArguments
    if ($LASTEXITCODE -ne 0) { throw 'Test compilation failed.' }
    & (Join-Path $outputPath 'ExporterTests.exe')
    if ($LASTEXITCODE -ne 0) { throw 'Exporter tests failed.' }
}
Write-Output (Join-Path $outputPath 'PowerScribeReportExporter.exe')
