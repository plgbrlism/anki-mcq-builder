$ErrorActionPreference = "Stop"

$Python = "python"
if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python not found. Install Python 3.11+ first." -ForegroundColor Red
    exit 1
}

$PyMajor = & $Python -c "import sys; print(sys.version_info.major)"
$PyMinor = & $Python -c "import sys; print(sys.version_info.minor)"

if ([int]$PyMajor -lt 3 -or ([int]$PyMajor -eq 3 -and [int]$PyMinor -lt 11)) {
    $PyVersion = & $Python --version
    Write-Host "Error: Python 3.11+ required, found $PyVersion" -ForegroundColor Red
    exit 1
}

$VersionOutput = & $Python --version
Write-Host "Using $VersionOutput" -ForegroundColor Green

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    & $Python -m venv .venv
}

Write-Host "Installing anki-mcq-builder..." -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -e .

Write-Host ""
Write-Host "Done! Run the following commands to get started:" -ForegroundColor Green
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host "  anki-mcq-builder --help" -ForegroundColor Yellow
