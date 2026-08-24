# Speed Streak visual performance comparison

Measured August 13, 2026 on this computer:

- Intel Core Ultra 9 185H (22 logical processors)
- Intel Arc integrated GPU through ANGLE/Direct3D 11
- NVIDIA RTX 4060 Laptop GPU present, but not used by Qt WebEngine in these tests
- 32 GB RAM
- Fixed 336 x 760 Speed Streak window
- Exact installed AnkiWeb package: Speed Streak v1.28B (`1237336370`)
- Current repository package: Speed Streak v1.36

Each test launched a fresh, isolated Qt WebEngine process using Anki's own Python/Qt runtime. The page was warmed up before CPU, GPU, memory, and animation callback sampling. GPU figures are average active Intel GPU-engine utilization, not percentage of the entire computer's theoretical graphics capacity. CPU is percentage of all 22 logical processors; 4.55% total CPU is approximately one logical processor fully occupied.

The figures below are deliberately rounded. GPU and memory measurements were repeatable; short CPU measurements varied more, so repeated modes are shown as ranges.

## Steady-state results

| Version and visual | GPU at 50 | GPU at 500 | Total CPU at 50 | Total CPU at 500 | Isolated memory at 500 |
|---|---:|---:|---:|---:|---:|
| AnkiWeb: Visuals Off | ~0% | ~0% | ~0% | ~0% | 0.44 GB |
| AnkiWeb: Number Only | ~0% | ~0% | ~0% | ~0% | 0.47 GB |
| AnkiWeb: Brick | ~0% | ~0% | ~0% | ~0% | 0.47 GB |
| AnkiWeb: Satellite Ultra | 15% | 13% | 1.6% | 1.6% | 1.54 GB |
| AnkiWeb: Satellite Consolidate | 11-17% | 29-36% | 1.3-2.3% | 1.9-2.2% | 2.99-3.02 GB |
| AnkiWeb: Satellite Full | 14-16% | 56-64% | 1.4-2.1% | 1.3-2.6% | 5.08-5.22 GB |
| Local: Visuals Off | ~0% | ~0% | ~0% | ~0% | 0.44 GB |
| Local: Number Only | ~0% | ~0% | ~0% | ~0% | 0.47 GB |
| Local: Brick | ~0% | ~0% | ~0% | ~0% | 0.50 GB |
| Local: Crystal Still | ~0% | ~0% | ~0% | ~0% | 0.61 GB |
| Local: Singularity Efficient | 4% | 4% | 1.0% | 0.9% | 0.51 GB |
| Local: Singularity Balanced | 7% | 7% | 1.5% | 1.5% | 0.55 GB |
| Local: Satellite Ultra | 11% | 13% | 1.6% | 2.1% | 1.56 GB |
| Local: Satellite Balanced | 13% | 14-15% | 1.7% | 2.1-2.3% | 1.73-1.80 GB |
| Local: Satellite Full | 15% | 14-15% | 1.1-2.6% | 1.3-2.6% | 1.57-1.58 GB |
| Local: Milestone Rings | 13-15% | 18-19% | 1.6-1.9% | 2.5-3.3% | 1.02-1.03 GB |
| Local: Fusion Rings | 12-14% | 16-19% | 1.2-1.6% | 2.4-3.6% | 1.01-1.03 GB |
| Local: Singularity Full | 13-14% | 16-17% | about 1.3%* | 2.4-2.7% | 0.54-0.56 GB |
| Local: Crystal Animated | 13-14% | 14-17% | 1.2-2.2% | 2.1-2.3% | 0.59-0.60 GB |

\* One Singularity Full 50-streak CPU sample was 4.0%; the repeat was 1.3% while its GPU and memory stayed stable, so it is treated as a transient/outlier rather than its normal cost.

The isolated WebEngine process itself uses about 0.44 GB with visuals off. Memory above that baseline is the more useful comparison. At 500, old Full adds roughly 4.7 GB, old Consolidate adds 2.6 GB, current Full/Balanced/Ultra add about 1.1-1.4 GB, the two ring modes add about 0.6 GB, and Singularity adds roughly 0.1 GB. An already-running Anki session shares some browser infrastructure, so these isolated totals should not be interpreted as an exact prediction of Anki's Task Manager total.

## Brief effects

| Event | Average GPU during sample | Peak GPU | Total CPU |
|---|---:|---:|---:|
| Milestone ring lock/fusion | 24% | 46% | 3.0% |
| Multi-row fusion lock | 26% | 49% | 3.9% |
| Use a Time Boost charge | 5% | 14% | 1.2% |

These are short animation spikes. They are not continuously sustained after the effect ends.

## Gameplay and timer settings

With a static Number Only visual, both Time Boost and Legacy Points measured approximately 0% CPU and 0% GPU. Time Boost added no meaningful continuous computation. The extra charge controls changed isolated memory by roughly 0-0.03 GB, within normal WebEngine process variation.

The active circular timer was the meaningful cost: about 1.7-2.5% total CPU, 11-14% GPU, and 60 animation callbacks per second in either gameplay mode. Time Boost was not measurably more demanding than Legacy Points.

## Representative full review load at streak 500

These tests run the visual and circular timer together. GPU percentages should not be added arithmetically, because the workloads share a GPU and sometimes overlap.

| Version and visual with timer active | Average GPU | Observed GPU range | Highest sample | Total CPU | Isolated memory |
|---|---:|---:|---:|---:|---:|
| AnkiWeb: Satellite Consolidate | 31% | 31-31% | 33% | 1.9-2.3% | 3.13 GB |
| AnkiWeb: Satellite Full | 60% | 46-74% | 96% | 2.4% | 5.10 GB |
| Local: Satellite Full | 16% | 16-16% | 18% | 2.8% | 1.54 GB |
| Local: Milestone Rings | 18% | 17-19% | 19% | 3.4% | 0.98 GB |
| Local: Fusion Rings | 17% | 17-17% | 18% | 3.2% | 1.00 GB |
| Local: Singularity Efficient | 16% | 16-16% | 17% | 2.0% | 0.54 GB |
| Local: Singularity Full | 18% | 18-18% | 19% | 2.2-2.4% | 0.54 GB |
| Local: Crystal Animated | 18% | 17-18% | 18% | 2.0-2.6% | 0.57 GB |

The old Full mode is not merely a slightly heavier option: during one combined run its GPU sample reached 96%. The current modes clustered tightly around 16-18% GPU with the timer active. The timer and a JavaScript-animated visual currently maintain separate animation callbacks, producing about 120 callbacks per second, though this does not mean the screen displays more than the monitor's refresh rate.

No Pause, No Undo, shortcut selection, theme selection, custom colors, audio enabled, and haptics enabled have effectively no idle CPU/GPU cost. They do work only when an input or feedback event occurs. Audio playback, haptics, answer flashes, charge effects, and fusion effects cause brief event-time work rather than a sustained load.

## Interpretation

- The installed AnkiWeb v1.28B Full mode at 500 is inappropriately demanding: 56-64% integrated-GPU utilization and about 5.1 GB in the isolated test. Consolidate is also excessive at 29-36% GPU and about 3.0 GB.
- Current Full at 500 cuts GPU use by approximately 74-77% and isolated memory by about 69% compared with AnkiWeb Full.
- Current Balanced at 500 cuts GPU use by approximately 55-59% and isolated memory by about 40% compared with AnkiWeb Consolidate.
- Singularity Efficient is the least costly continuously animated mode. Singularity Balanced is the next-lowest.
- Crystal Still, Brick, Number Only, and Visuals Off are effectively free while nothing is changing.
- Milestone and Fusion replace per-card long-term growth with much slower per-50-card growth, but rotating completed rings still create a noticeable continuous GPU load. Their worst state within each 50-card block is just before the next lock, when the completed rings plus 49 live satellites are visible.
- CSS/compositor animation can use the GPU without increasing JavaScript animation-callback counts. Therefore an RAF count of zero does not prove that a visual is free.
- The resource-percentage wording currently shown in the visual selector is not supported by these measurements. Satellite Ultra was only about 10% below current Full at streak 500, not 35-55% of Full, while Crystal Still was effectively 0% during steady state rather than 70-85% of Animated. Those descriptions should be revised before release.
- These percentages are specific to this laptop and window size. Rankings and relative differences should transfer better than exact percentages to another computer.

Raw measurements are preserved in the CSV files beside this report. The test can be repeated with `run_speed_streak_visual_benchmarks.ps1` without installing or replacing either add-on version.
