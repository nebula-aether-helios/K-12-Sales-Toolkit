<#
start_docker_desktop.ps1

Attempts to start Docker Desktop (user session) and report service status.
Run as an elevated user if you want to start/stop services; starting the GUI does not require elevation.
#>

Set-StrictMode -Version Latest

function Now { Get-Date -Format o }

Write-Host "Starting Docker Desktop (GUI) if installed..."
$exePath1 = "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
$exePath2 = "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
if (Test-Path $exePath1) {
    Start-Process -FilePath $exePath1 -ArgumentList @() -WindowStyle Normal
    Write-Host "Launched: $exePath1"
} else {
    Write-Host "Docker Desktop executable not found at $exePath1. If installed elsewhere, start Docker Desktop manually." -ForegroundColor Yellow
}

try {
    $svc = Get-Service -Name com.docker.service -ErrorAction Stop
    Write-Host "Docker service status: $($svc.Status)"
    if ($svc.Status -ne 'Running') {
        Write-Host "Attempting to start Docker service (requires elevation)..."
        Start-Service -Name com.docker.service -ErrorAction Stop
        Start-Sleep -Seconds 5
        $svc = Get-Service -Name com.docker.service
        Write-Host "Docker service status after start attempt: $($svc.Status)"
    }
} catch {
    Write-Host "Docker service not found or cannot be controlled without elevation: $_" -ForegroundColor Yellow
}

Write-Host "Next: open Docker Desktop and check Settings → General → Use the WSL 2 based engine, then Settings → Resources → WSL Integration to enable your distro(s)."
