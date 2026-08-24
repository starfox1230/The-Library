param(
    [string]$OutputCsv = "",
    [double]$WarmupSeconds = 3,
    [double]$MeasureSeconds = 6,
    [int]$Repetitions = 2,
    [string]$ModeFilter = "",
    [int[]]$Streaks = @(50, 500)
)

$ErrorActionPreference = "Stop"
$toolRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $toolRoot
$repoRoot = (Resolve-Path (Join-Path $projectRoot "..\..")).Path
$harness = Join-Path $toolRoot "speed_streak_visual_benchmark.py"
$ankiPython = Join-Path $env:LOCALAPPDATA "AnkiProgramFiles\.venv\Scripts\python.exe"
$installedRoot = Join-Path $env:APPDATA "Anki2\addons21\1237336370"
$currentRoot = Join-Path $projectRoot "speed-streak-addon-v1.36"
$logicalProcessors = [Math]::Max(1, [int]$env:NUMBER_OF_PROCESSORS)
if (-not $OutputCsv) {
    $OutputCsv = Join-Path $toolRoot "speed_streak_visual_benchmark_results.csv"
}

function Get-DescendantProcessIds {
    param([int]$RootPid)
    $all = @(Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId)
    $ids = [System.Collections.Generic.HashSet[int]]::new()
    [void]$ids.Add($RootPid)
    $changed = $true
    while ($changed) {
        $changed = $false
        foreach ($process in $all) {
            if ($ids.Contains([int]$process.ParentProcessId) -and -not $ids.Contains([int]$process.ProcessId)) {
                [void]$ids.Add([int]$process.ProcessId)
                $changed = $true
            }
        }
    }
    return @($ids)
}

function Get-ProcessCpuSeconds {
    param([int[]]$ProcessIds)
    $sum = 0.0
    foreach ($processId in $ProcessIds) {
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) { $sum += [double]$process.CPU }
    }
    return $sum
}

function Get-ProcessWorkingSetMb {
    param([int[]]$ProcessIds)
    $sum = 0.0
    foreach ($processId in $ProcessIds) {
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) { $sum += [double]$process.WorkingSet64 / 1MB }
    }
    return $sum
}

function Get-GpuSamples {
    param([int[]]$ProcessIds, [int]$SampleCount)
    $wanted = [System.Collections.Generic.HashSet[int]]::new()
    foreach ($processId in $ProcessIds) { [void]$wanted.Add($processId) }
    $perSample = [System.Collections.Generic.List[double]]::new()
    foreach ($sampleIndex in 1..$SampleCount) {
        $sum = 0.0
        $engines = Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine -ErrorAction SilentlyContinue
        foreach ($engine in $engines) {
            if ([string]$engine.Name -match 'pid_(\d+)_') {
                $samplePid = [int]$Matches[1]
                if ($wanted.Contains($samplePid)) {
                    $sum += [Math]::Max(0.0, [double]$engine.UtilizationPercentage)
                }
            }
        }
        $perSample.Add($sum)
        if ($sampleIndex -lt $SampleCount) { Start-Sleep -Milliseconds 750 }
    }
    return [pscustomobject]@{
        Average = [double](($perSample | Measure-Object -Average).Average)
        Peak = [double](($perSample | Measure-Object -Maximum).Maximum)
    }
}

$cases = @(
    # Current AnkiWeb v1.28B modes.
    @{ Version="AnkiWeb v1.28B"; Root=$installedRoot; Name="Visuals Off"; Visual="sphere"; Sphere="classic"; Render="webgl"; Crystal=1; Visuals=0 },
    @{ Version="AnkiWeb v1.28B"; Root=$installedRoot; Name="Satellite Number Only"; Visual="sphere"; Sphere="classic"; Render="webgl"; Crystal=1; Orbit=0 },
    @{ Version="AnkiWeb v1.28B"; Root=$installedRoot; Name="Satellite Ultra"; Visual="sphere"; Sphere="classic"; Render="ultra_low_resource"; Crystal=1 },
    @{ Version="AnkiWeb v1.28B"; Root=$installedRoot; Name="Satellite Consolidate"; Visual="sphere"; Sphere="consolidate"; Render="webgl"; Crystal=1 },
    @{ Version="AnkiWeb v1.28B"; Root=$installedRoot; Name="Satellite Full"; Visual="sphere"; Sphere="classic"; Render="webgl"; Crystal=1 },
    @{ Version="AnkiWeb v1.28B"; Root=$installedRoot; Name="Brick"; Visual="lightweight_rows"; Sphere="classic"; Render="ultra_low_resource"; Crystal=1 },

    # Current local v1.36 modes.
    @{ Version="Local v1.36"; Root=$currentRoot; Name="Visuals Off"; Visual="sphere"; Sphere="classic"; Render="webgl"; Crystal=1; Visuals=0 },
    @{ Version="Local v1.36"; Root=$currentRoot; Name="Satellite Number Only"; Visual="sphere"; Sphere="classic"; Render="webgl"; Crystal=1; Orbit=0 },
    @{ Version="Local v1.36"; Root=$currentRoot; Name="Satellite Ultra"; Visual="sphere"; Sphere="classic"; Render="ultra_low_resource"; Crystal=1 },
    @{ Version="Local v1.36"; Root=$currentRoot; Name="Satellite Balanced"; Visual="sphere"; Sphere="consolidate"; Render="webgl"; Crystal=1 },
    @{ Version="Local v1.36"; Root=$currentRoot; Name="Satellite Full"; Visual="sphere"; Sphere="classic"; Render="webgl"; Crystal=1 },
    @{ Version="Local v1.36"; Root=$currentRoot; Name="Milestone Rings"; Visual="sphere"; Sphere="milestone"; Render="webgl"; Crystal=1 },
    @{ Version="Local v1.36"; Root=$currentRoot; Name="Fusion Rings"; Visual="sphere"; Sphere="fusion"; Render="webgl"; Crystal=1 },
    @{ Version="Local v1.36"; Root=$currentRoot; Name="Singularity Efficient"; Visual="singularity"; Sphere="classic"; Render="ultra_low_resource"; Crystal=1 },
    @{ Version="Local v1.36"; Root=$currentRoot; Name="Singularity Balanced"; Visual="singularity"; Sphere="classic"; Render="low_resource"; Crystal=1 },
    @{ Version="Local v1.36"; Root=$currentRoot; Name="Singularity Full"; Visual="singularity"; Sphere="classic"; Render="webgl"; Crystal=1 },
    @{ Version="Local v1.36"; Root=$currentRoot; Name="Crystal Still"; Visual="crystal_reactor"; Sphere="classic"; Render="webgl"; Crystal=0 },
    @{ Version="Local v1.36"; Root=$currentRoot; Name="Crystal Animated"; Visual="crystal_reactor"; Sphere="classic"; Render="webgl"; Crystal=1 },
    @{ Version="Local v1.36"; Root=$currentRoot; Name="Brick"; Visual="lightweight_rows"; Sphere="classic"; Render="ultra_low_resource"; Crystal=1 },

    # Representative real-review combinations with the circular timer active.
    @{ Version="AnkiWeb v1.28B review load"; Root=$installedRoot; Name="Satellite Consolidate + Timer"; Visual="sphere"; Sphere="consolidate"; Render="webgl"; Crystal=1; Timer=1 },
    @{ Version="AnkiWeb v1.28B review load"; Root=$installedRoot; Name="Satellite Full + Timer"; Visual="sphere"; Sphere="classic"; Render="webgl"; Crystal=1; Timer=1 },
    @{ Version="Local v1.36 review load"; Root=$currentRoot; Name="Satellite Full + Timer"; Visual="sphere"; Sphere="classic"; Render="webgl"; Crystal=1; Timer=1 },
    @{ Version="Local v1.36 review load"; Root=$currentRoot; Name="Milestone Rings + Timer"; Visual="sphere"; Sphere="milestone"; Render="webgl"; Crystal=1; Timer=1 },
    @{ Version="Local v1.36 review load"; Root=$currentRoot; Name="Fusion Rings + Timer"; Visual="sphere"; Sphere="fusion"; Render="webgl"; Crystal=1; Timer=1 },
    @{ Version="Local v1.36 review load"; Root=$currentRoot; Name="Singularity Efficient + Timer"; Visual="singularity"; Sphere="classic"; Render="ultra_low_resource"; Crystal=1; Timer=1 },
    @{ Version="Local v1.36 review load"; Root=$currentRoot; Name="Singularity Full + Timer"; Visual="singularity"; Sphere="classic"; Render="webgl"; Crystal=1; Timer=1 },
    @{ Version="Local v1.36 review load"; Root=$currentRoot; Name="Crystal Animated + Timer"; Visual="crystal_reactor"; Sphere="classic"; Render="webgl"; Crystal=1; Timer=1 },

    # Isolated gameplay/timer comparisons; select these with ModeFilter="toggle".
    @{ Version="Local v1.36 toggles"; Root=$currentRoot; Name="Number Only + Time Boost"; Visual="sphere"; Sphere="classic"; Render="webgl"; Crystal=1; Orbit=0; Gameplay="time_boost" },
    @{ Version="Local v1.36 toggles"; Root=$currentRoot; Name="Number Only + Legacy Points"; Visual="sphere"; Sphere="classic"; Render="webgl"; Crystal=1; Orbit=0; Gameplay="legacy_points" },
    @{ Version="Local v1.36 toggles"; Root=$currentRoot; Name="Active Timer + Time Boost"; Visual="sphere"; Sphere="classic"; Render="webgl"; Crystal=1; Orbit=0; Timer=1; Gameplay="time_boost" },
    @{ Version="Local v1.36 toggles"; Root=$currentRoot; Name="Active Timer + Legacy Points"; Visual="sphere"; Sphere="classic"; Render="webgl"; Crystal=1; Orbit=0; Timer=1; Gameplay="legacy_points" },

    # Short-lived effects; select these with ModeFilter="transitions" and Streaks=49.
    @{ Version="Local v1.36 transitions"; Root=$currentRoot; Name="Milestone 50 Lock"; Visual="sphere"; Sphere="milestone"; Render="webgl"; Crystal=1; Effect="milestone" },
    @{ Version="Local v1.36 transitions"; Root=$currentRoot; Name="Fusion 50 Lock"; Visual="sphere"; Sphere="fusion"; Render="webgl"; Crystal=1; Effect="milestone" },
    @{ Version="Local v1.36 transitions"; Root=$currentRoot; Name="Time Boost Use"; Visual="sphere"; Sphere="classic"; Render="webgl"; Crystal=1; Orbit=0; Effect="charge" }
)
foreach ($case in $cases) {
    if (-not $case.ContainsKey('Orbit')) { $case['Orbit'] = 1 }
    if (-not $case.ContainsKey('Visuals')) { $case['Visuals'] = 1 }
    if (-not $case.ContainsKey('Timer')) { $case['Timer'] = 0 }
    if (-not $case.ContainsKey('Gameplay')) { $case['Gameplay'] = 'time_boost' }
    if (-not $case.ContainsKey('Effect')) { $case['Effect'] = 'none' }
}
if ($ModeFilter) {
    $cases = @($cases | Where-Object { "$($_.Version) / $($_.Name)" -match $ModeFilter })
}
if (-not $cases.Count) { throw "No benchmark cases matched ModeFilter '$ModeFilter'." }

$tempRoot = Join-Path $env:TEMP "speed-streak-visual-benchmark"
New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
$results = [System.Collections.Generic.List[object]]::new()
$sampleCount = [Math]::Max(2, [int][Math]::Ceiling($MeasureSeconds))

foreach ($streak in $Streaks) {
    foreach ($case in $cases) {
        foreach ($repetition in 1..$Repetitions) {
            $safeName = ($case.Name -replace '[^A-Za-z0-9]+', '-').Trim('-')
            $token = "{0}-{1}-{2}-{3}" -f ($case.Version -replace '[^A-Za-z0-9]+','-'), $safeName, $streak, $repetition
            $readyFile = Join-Path $tempRoot "$token-ready.json"
            $resultFile = Join-Path $tempRoot "$token-result.json"
            Remove-Item -LiteralPath $readyFile, $resultFile -Force -ErrorAction SilentlyContinue
            $arguments = @(
                "`"$harness`"",
                '--addon-root', "`"$($case.Root)`"",
                '--case', "`"$($case.Version) / $($case.Name) / streak $streak / run $repetition`"",
                '--visual-mode', $case.Visual,
                '--sphere-mode', $case.Sphere,
                '--render-mode', $case.Render,
                '--streak', $streak,
                '--crystal-rotation', $case.Crystal,
                '--orbit-animation', $case.Orbit,
                '--visuals-enabled', $case.Visuals,
                '--timer-active', $case.Timer,
                '--gameplay-mode', $case.Gameplay,
                '--effect', $case.Effect,
                '--warmup', $WarmupSeconds,
                '--duration', ($MeasureSeconds + 10),
                '--ready-file', "`"$readyFile`"",
                '--result-file', "`"$resultFile`""
            )
            Write-Host "Benchmarking $($case.Version) - $($case.Name), streak $streak, run $repetition..."
            $process = Start-Process -FilePath $ankiPython -ArgumentList $arguments -PassThru
            $deadline = (Get-Date).AddSeconds($WarmupSeconds + 20)
            while (-not (Test-Path -LiteralPath $readyFile) -and -not $process.HasExited -and (Get-Date) -lt $deadline) {
                Start-Sleep -Milliseconds 100
                $process.Refresh()
            }
            if (-not (Test-Path -LiteralPath $readyFile)) {
                if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force }
                throw "Benchmark case failed to become ready: $token"
            }

            $processIds = Get-DescendantProcessIds -RootPid $process.Id
            $cpuStart = Get-ProcessCpuSeconds -ProcessIds $processIds
            $wallStart = Get-Date
            $gpu = Get-GpuSamples -ProcessIds $processIds -SampleCount $sampleCount
            $wallSeconds = [Math]::Max(0.001, ((Get-Date) - $wallStart).TotalSeconds)
            $cpuEnd = Get-ProcessCpuSeconds -ProcessIds $processIds
            $memoryMb = Get-ProcessWorkingSetMb -ProcessIds $processIds
            $process.WaitForExit(15000) | Out-Null
            if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force }
            if (-not (Test-Path -LiteralPath $resultFile)) { throw "Benchmark did not write a result: $token" }
            $page = Get-Content -Raw -LiteralPath $resultFile | ConvertFrom-Json
            $cpuTotalPercent = (($cpuEnd - $cpuStart) / $wallSeconds / $logicalProcessors) * 100
            $results.Add([pscustomobject]@{
                Version = $case.Version
                Mode = $case.Name
                Streak = $streak
                Run = $repetition
                CpuTotalPercent = [Math]::Round($cpuTotalPercent, 3)
                GpuEngineAveragePercent = [Math]::Round($gpu.Average, 3)
                GpuEnginePeakPercent = [Math]::Round($gpu.Peak, 3)
                WorkingSetMb = [Math]::Round($memoryMb, 1)
                RafCallbacksPerSecond = [Math]::Round([double]$page.raf_callbacks_per_s, 2)
                DomSatellites = [int]$page.domSatellites
                MilestoneRings = [int]$page.milestoneRings
                FusionRows = [int]$page.fusionRows
                WebGlRenderer = [string]$page.gpu.renderer
            })
        }
    }
}

$results | Export-Csv -LiteralPath $OutputCsv -NoTypeInformation
Write-Host "Saved $($results.Count) measurements to $OutputCsv"
