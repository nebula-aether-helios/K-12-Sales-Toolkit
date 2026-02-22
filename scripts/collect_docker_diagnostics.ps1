<#
collect_docker_diagnostics.ps1

Collects basic Docker, WSL, and system diagnostics for troubleshooting Dev Containers / Docker Desktop issues.
Writes output to `outputs/docker_diagnostics_<timestamp>.txt` and copies Docker Desktop logs if present.

Run without elevation; some commands may require elevation (noted in output).
#>

Set-StrictMode -Version Latest
function Now { Get-Date -Format o }
$outDir = Join-Path -Path (Get-Location) -ChildPath "outputs"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
$ts = Get-Date -Format "yyyyMMddTHHmmss"
$outFile = Join-Path $outDir "docker_diagnostics_$ts.txt"

"Diagnostics run at: $(Now)" | Out-File $outFile -Encoding utf8

function RunAndLog {
    param($label, $script)
    "`n=== $label ===`n" | Out-File $outFile -Append -Encoding utf8
    try {
        & $script 2>&1 | Out-File $outFile -Append -Encoding utf8
    } catch {
        "ERROR running ${label}: ${_}" | Out-File $outFile -Append -Encoding utf8
    }
}

RunAndLog "systeminfo (short)" { systeminfo }
RunAndLog "wsl --list --verbose" { wsl --list --verbose 2>&1 }
RunAndLog "wsl --status" { wsl --status 2>&1 }
RunAndLog "docker version" { docker version --format '{{json .}}' 2>&1 }
RunAndLog "docker info" { docker info 2>&1 }
RunAndLog "Get-Process com.docker*" { Get-Process -Name 'com.docker.*' -ErrorAction SilentlyContinue }
RunAndLog "Get-Process Docker*" { Get-Process -Name 'Docker*' -ErrorAction SilentlyContinue }
RunAndLog "Get-Service *docker*" { Get-Service -Name '*docker*' -ErrorAction SilentlyContinue }
RunAndLog "bcdedit /enum" { bcdedit /enum }
RunAndLog "Get-CimInstance Win32_DeviceGuard" { Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\cimv2 }

# Collect Docker Desktop logs if present
$localApp = "$env:LOCALAPPDATA\Docker"
if (Test-Path $localApp) {
    "\nDocker Desktop local app data found at: $localApp" | Out-File $outFile -Append -Encoding utf8
    $logFiles = Get-ChildItem -Path $localApp -Recurse -Include *.log,*.txt -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 20
    foreach ($f in $logFiles) {
        "\n--- Log: $($f.FullName) ---\n" | Out-File $outFile -Append -Encoding utf8
        Get-Content -Path $f.FullName -Tail 200 -ErrorAction SilentlyContinue | Out-File $outFile -Append -Encoding utf8
    }
} else {
    "\nNo Docker Desktop local app data found at $localApp" | Out-File $outFile -Append -Encoding utf8
}

"\nDiagnostics saved to: $outFile" | Out-File $outFile -Append -Encoding utf8
Write-Host "Diagnostics saved to: $outFile"
