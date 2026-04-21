param()

$ErrorActionPreference = "Stop"

$nodeRuntimeRoot = if ($env:RADIOGRAPHICS_RUNTIME_DIR) {
    $env:RADIOGRAPHICS_RUNTIME_DIR
} else {
    Join-Path $env:LOCALAPPDATA "RadiographicsReview\\runtime"
}
$pythonRuntimeRoot = if ($env:RADIOGRAPHICS_PYTHON_RUNTIME_DIR) {
    $env:RADIOGRAPHICS_PYTHON_RUNTIME_DIR
} else {
    Join-Path $env:LOCALAPPDATA "RadiographicsReview\\python-runtime"
}

New-Item -ItemType Directory -Force -Path $nodeRuntimeRoot | Out-Null
New-Item -ItemType Directory -Force -Path $pythonRuntimeRoot | Out-Null

Push-Location $nodeRuntimeRoot
try {
    npm install playwright-core
}
finally {
    Pop-Location
}

py -m pip install --target $pythonRuntimeRoot genanki

Write-Host "Installed Node runtime in $nodeRuntimeRoot"
Write-Host "Installed Python runtime in $pythonRuntimeRoot"
