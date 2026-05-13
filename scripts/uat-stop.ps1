$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$stateFile = Join-Path (Join-Path $root ".local") "uat-processes.json"

if (-not (Test-Path $stateFile)) {
  Write-Host "No UAT process state found."
  exit 0
}

$services = Get-Content $stateFile | ConvertFrom-Json

foreach ($service in $services) {
  if ($service.Pid) {
    $process = Get-Process -Id $service.Pid -ErrorAction SilentlyContinue
    if ($process) {
      Stop-Process -Id $service.Pid -Force
      Write-Host ("Stopped {0} (PID {1})" -f $service.Name, $service.Pid)
    }
  }
}

Remove-Item $stateFile -Force -ErrorAction SilentlyContinue
