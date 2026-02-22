<#
bootstrap_dev.ps1

PowerShell bootstrap for offline-first development.

Usage (online machine):
  # create vendor wheel cache
  pip download -r requirements.txt -d vendor_wheels

Usage (offline machine):
  .\scripts\bootstrap_dev.ps1

#>

param(
    [int]$PythonMajor = 3,
    [string]$VenvDir = ".venv"
)

Set-StrictMode -Version Latest

function Write-Log {
    param([string]$m)
    $ts = Get-Date -Format o
    Write-Host "[$ts] $m"
}

Write-Log "Starting bootstrap_dev.ps1"

if (-not (Test-Path -Path $VenvDir)) {
    Write-Log "Creating virtual environment: $VenvDir"
    python -m venv $VenvDir
} else {
    Write-Log "Virtual environment already exists: $VenvDir"
}

Write-Log "Activate the venv and install dependencies"
$activate = Join-Path $VenvDir "Scripts\Activate.ps1"
Write-Host "Run: `& $activate` to activate the venv in this session"

if (Test-Path -Path "vendor_wheels") {
    Write-Log "Found vendor_wheels directory — installing from cache"
    & $activate; pip install --no-index --find-links=vendor_wheels -r requirements.txt
} elseif (Test-Path -Path "requirements.txt") {
    Write-Log "No vendor cache found. Attempting online install from PyPI (requires network)"
    & $activate; pip install -r requirements.txt
    Write-Log "If you have network access and want offline installs later, run on a connected machine: `pip download -r requirements.txt -d vendor_wheels`"
} else {
    Write-Log "No requirements.txt found — skipping Python package install"
}

# Prepare .env from example if present
if ((Test-Path -Path ".env.example") -and -not (Test-Path -Path ".env")) {
    Copy-Item -Path .env.example -Destination .env
    Write-Log "Copied .env.example to .env (please edit and add real secrets as needed)"
}

Write-Log "Bootstrap complete. Next steps (copyable):"
Write-Host "  . $activate  # activate the venv"
Write-Host "  # (optional) start local emulators if available, e.g. Azurite or Functions Core Tools"
Write-Host "  # azurite --location ./azurite_db --silent"
Write-Host "  # func start"
