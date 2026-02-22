<#
cache_dependencies.ps1

Create a vendor_wheels directory with wheels for offline installation.
Run this on a machine with internet access.
#>

param(
    [string]$requirements = "requirements.txt",
    [string]$outputDir = "vendor_wheels"
)

Set-StrictMode -Version Latest

if (-not (Test-Path $requirements)) {
    Write-Host "Requirements file not found: $requirements" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $outputDir)) { New-Item -ItemType Directory -Path $outputDir | Out-Null }

Write-Host "Downloading wheels to $outputDir..."
python -m pip download -r $requirements -d $outputDir

# Also download model_mock requirements if present
$mockReq = ".devcontainer/model_mock/requirements.txt"
if (Test-Path $mockReq) {
    Write-Host "Downloading model mock requirements..."
    python -m pip download -r $mockReq -d $outputDir
}

Write-Host "Vendor wheel cache created at: $outputDir"
