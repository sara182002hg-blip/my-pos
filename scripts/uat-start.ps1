$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$stateDir = Join-Path $root ".local"
$stateFile = Join-Path $stateDir "uat-processes.json"

New-Item -ItemType Directory -Path $stateDir -Force | Out-Null

if (Test-Path $stateFile) {
  $existing = Get-Content $stateFile | ConvertFrom-Json
  $active = @($existing | Where-Object { $_.Pid -and (Get-Process -Id $_.Pid -ErrorAction SilentlyContinue) })
  if ($active.Count -gt 0) {
    Write-Host "UAT services are already running."
    exit 0
  }
}

$services = @(
  @{ Name = "api"; Command = "npm run dev:api"; Url = "http://127.0.0.1:4000/health" },
  @{ Name = "pos"; Command = "npm run dev:pos"; Url = "http://127.0.0.1:5173" },
  @{ Name = "kds"; Command = "npm run dev:kds"; Url = "http://127.0.0.1:5174" },
  @{ Name = "qr"; Command = "npm run dev:qr"; Url = "http://127.0.0.1:3000" }
)

$started = @()

foreach ($service in $services) {
  $command = "Set-Location '$root'; $($service.Command)"
  $process = Start-Process -FilePath "powershell" -ArgumentList @("-NoExit", "-Command", $command) -PassThru -WindowStyle Minimized
  $started += [PSCustomObject]@{
    Name = $service.Name
    Pid = $process.Id
    Url = $service.Url
    Command = $service.Command
    StartedAt = (Get-Date).ToString("o")
  }
}

$started | ConvertTo-Json | Set-Content $stateFile

Write-Host "Started UAT services:"
$started | ForEach-Object {
  Write-Host ("- {0} (PID {1}) -> {2}" -f $_.Name, $_.Pid, $_.Url)
}
Write-Host "Run 'npm run uat:health' to verify readiness."
