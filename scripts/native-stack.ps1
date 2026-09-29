[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("start", "stop", "status")]
    [string]$Action = "status"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$RuntimeDir = Join-Path $RepoRoot ".runtime"
$EnvFile = Join-Path $RuntimeDir "native.env"
$ProcessFile = Join-Path $RuntimeDir "native-stack-processes.json"

function Import-NativeEnvironment {
    if (-not (Test-Path -LiteralPath $EnvFile)) {
        throw "Native environment is missing. Run scripts/native-infra.ps1 setup first."
    }
    foreach ($line in Get-Content -LiteralPath $EnvFile) {
        if ($line -and -not $line.StartsWith("#")) {
            $name, $value = $line.Split("=", 2)
            Set-Item -Path "Env:$name" -Value $value
        }
    }
    $env:PYTHONPATH = "$RepoRoot\apps\api;$RepoRoot\packages\sensor-sdk;$RepoRoot"
    $env:API_URL = "http://127.0.0.1:8000"
    $env:COOKIE_SECURE = "false"
    $env:HOSTNAME = "127.0.0.1"
    $env:PORT = "3000"
}

function Test-TcpPort([int]$Port) {
    $client = [Net.Sockets.TcpClient]::new()
    try {
        $task = $client.ConnectAsync("127.0.0.1", $Port)
        return $task.Wait(750) -and $client.Connected
    } catch { return $false } finally { $client.Dispose() }
}

function Start-TrackedProcess([string]$Name, [string]$FilePath, [string[]]$Arguments, [string]$WorkingDirectory) {
    $stdout = Join-Path $RuntimeDir "$Name.out.log"
    $stderr = Join-Path $RuntimeDir "$Name.err.log"
    $process = Start-Process -FilePath $FilePath -ArgumentList $Arguments -WorkingDirectory $WorkingDirectory `
        -RedirectStandardOutput $stdout -RedirectStandardError $stderr -WindowStyle Hidden -PassThru
    return [PSCustomObject]@{ name = $Name; id = $process.Id; started_at = $process.StartTime.ToUniversalTime().ToString("o") }
}

if ($Action -eq "start") {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "native-infra.ps1") start
    Import-NativeEnvironment
    Push-Location (Join-Path $RepoRoot "apps\api")
    try { & (Join-Path $RepoRoot ".venv\Scripts\python.exe") -m alembic upgrade head } finally { Pop-Location }
    if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot "apps\web\.next\BUILD_ID"))) {
        Push-Location (Join-Path $RepoRoot "apps\web")
        try { & npm.cmd run build } finally { Pop-Location }
    }
    $standaloneStatic = Join-Path $RepoRoot "apps\web\.next\standalone\.next\static"
    Copy-Item -Recurse -Force (Join-Path $RepoRoot "apps\web\.next\static") $standaloneStatic
    $python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    $entries = [System.Collections.Generic.List[object]]::new()
    if (Test-Path -LiteralPath $ProcessFile) {
        foreach ($entry in @(Get-Content -Raw -LiteralPath $ProcessFile | ConvertFrom-Json)) { [void]$entries.Add($entry) }
    }
    $trackedNames = @($entries | ForEach-Object { $_.name })
    if (-not (Test-TcpPort 8000)) { [void]$entries.Add((Start-TrackedProcess "api" $python @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000") $RepoRoot)) }
    if (-not (Test-TcpPort 8080)) { [void]$entries.Add((Start-TrackedProcess "http-honeypot" $python @("-m", "uvicorn", "main:app", "--app-dir", "apps/http-honeypot", "--host", "127.0.0.1", "--port", "8080") $RepoRoot)) }
    if (-not (Test-TcpPort 2222)) { [void]$entries.Add((Start-TrackedProcess "ssh-honeypot" $python @("apps/ssh-honeypot/main.py") $RepoRoot)) }
    if (-not (Test-TcpPort 3000)) { [void]$entries.Add((Start-TrackedProcess "web" "node.exe" @(".next/standalone/server.js") (Join-Path $RepoRoot "apps\web"))) }
    if ($trackedNames -notcontains "worker") { [void]$entries.Add((Start-TrackedProcess "worker" $python @("apps/worker/main.py") $RepoRoot)) }
    $entries | ConvertTo-Json | Set-Content -LiteralPath $ProcessFile
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        if ((Test-TcpPort 8000) -and (Test-TcpPort 8080) -and (Test-TcpPort 2222) -and (Test-TcpPort 3000)) { break }
        Start-Sleep -Milliseconds 500
    }
    if (-not ((Test-TcpPort 8000) -and (Test-TcpPort 8080) -and (Test-TcpPort 2222) -and (Test-TcpPort 3000))) {
        throw "One or more services did not start; inspect .runtime/*.err.log."
    }
    Write-Host "Native application stack is ready: web 3000, API 8000, HTTP 8080, SSH 2222."
    exit 0
}

if ($Action -eq "stop") {
    if (Test-Path -LiteralPath $ProcessFile) {
        $entries = Get-Content -Raw -LiteralPath $ProcessFile | ConvertFrom-Json
        foreach ($entry in @($entries)) {
            $process = Get-Process -Id $entry.id -ErrorAction SilentlyContinue
            if ($process -and ([datetime]$process.StartTime).ToUniversalTime().ToString("o") -eq $entry.started_at) {
                Stop-Process -Id $process.Id -Force
            }
        }
        Remove-Item -LiteralPath $ProcessFile
    }
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "native-infra.ps1") stop
    exit 0
}

foreach ($port in 3000, 8000, 8080, 2222) { Write-Host "Port $port`: $(if (Test-TcpPort $port) { 'running' } else { 'stopped' })" }
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "native-infra.ps1") status
