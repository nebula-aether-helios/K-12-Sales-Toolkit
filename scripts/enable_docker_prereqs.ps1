<#!
enable_docker_prereqs.ps1

PowerShell helper to check and enable Windows features required for Docker Desktop WSL2/Hyper-V backends.

IMPORTANT: This script should be run as Administrator. It will not elevate itself.

Usage:
  Open an elevated PowerShell (Run as Administrator) and run:
    .\scripts\enable_docker_prereqs.ps1

What it does (when run elevated):
- Checks virtualization support and WSL status
- Enables Windows optional features: VirtualMachinePlatform, Microsoft-Windows-Subsystem-Linux, Containers, Hyper-V (optional)
- Suggests WSL repair/install commands if WSL appears corrupted
- Prompts for restart when changes are made

#>

function Is-Administrator {
    $current = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $current.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Is-Administrator)) {
    Write-Host "This script must be run as Administrator. Please re-run in an elevated PowerShell." -ForegroundColor Yellow
    exit 2
}

Write-Host "Checking CPU virtualization support and hypervisor status..." -ForegroundColor Cyan
$sys = systeminfo | Out-String
Write-Host $sys | Select-String -Pattern "Hyper-V Requirements|A hypervisor has been detected|VM Monitor Mode Extensions" -AllMatches

Write-Host "Checking WSL status (may require repair)..." -ForegroundColor Cyan
try {
    wsl --list --verbose 2>&1 | Out-String | Write-Host
} catch {
    Write-Host "WSL reported an error. You may need to repair or reinstall WSL." -ForegroundColor Yellow
}

Write-Host "Enabling Windows optional features needed for Docker Desktop (this may take a few minutes)..." -ForegroundColor Cyan

# Enable VirtualMachinePlatform and WSL
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# Enable Containers feature (useful for some Docker setups)
dism.exe /online /enable-feature /featurename:Containers /all /norestart

# Optionally enable Hyper-V (useful for Hyper-V backend or legacy setups)
Read-Host -Prompt "Press Enter to enable Hyper-V (Microsoft-Hyper-V-All) or Ctrl-C to skip"
dism.exe /online /enable-feature /featurename:Microsoft-Hyper-V-All /all /norestart

Write-Host "Features enabled (or already present). If WSL kernel update is required, consider running:`n  wsl --update" -ForegroundColor Green

Write-Host "If WSL appears corrupted, run the following as elevated PowerShell to repair/install WSL:`n  wsl --install" -ForegroundColor Yellow

Write-Host "A restart is recommended to complete feature enablement. Reboot now? (Y/N)" -ForegroundColor Cyan
$resp = Read-Host
if ($resp -match '^[Yy]') {
    Write-Host "Restarting the system..." -ForegroundColor Cyan
    Restart-Computer
} else {
    Write-Host "Changes will take effect after you restart the machine." -ForegroundColor Yellow
}

Write-Host "Post-steps after reboot (manual):" -ForegroundColor Cyan
Write-Host " 1) If using WSL2 backend for Docker Desktop: run 'wsl --update' and 'wsl --set-default-version 2'"
Write-Host " 2) Install or start Docker Desktop, and in Settings > General enable 'Use the WSL 2 based engine' and integrate with desired WSL distros."
Write-Host ' 3) If Docker still fails, check Virtualization-based security (VBS) / HVCI settings - these can conflict with Docker; consult corporate policy if enabled.' -ForegroundColor Yellow
