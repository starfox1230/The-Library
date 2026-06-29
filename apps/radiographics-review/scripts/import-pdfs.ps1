param(
    [Parameter(Mandatory = $true, ValueFromRemainingArguments = $true)]
    [string[]]$PdfPath
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$appRoot = Split-Path -Parent $scriptDir
$repoRoot = Split-Path -Parent (Split-Path -Parent $appRoot)
$bundledRoot = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies"
$bundledPython = Join-Path $bundledRoot "python\python.exe"
$bundledPdftoppm = Join-Path $bundledRoot "native\poppler\Library\bin\pdftoppm.exe"

if (Test-Path $bundledPython) {
    $env:RADIOGRAPHICS_PDF_PYTHON = $bundledPython
}

if (Test-Path $bundledPdftoppm) {
    $env:RADIOGRAPHICS_PDFTOPPM = $bundledPdftoppm
}

Push-Location $appRoot
try {
    node .\src\importPdfArticles.js @PdfPath
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
finally {
    Pop-Location
}
