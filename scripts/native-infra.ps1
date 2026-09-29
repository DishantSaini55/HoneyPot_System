[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("setup", "start", "stop", "status")]
    [string]$Action = "status"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$RuntimeDir = Join-Path $RepoRoot ".runtime"
$EnvFile = Join-Path $RuntimeDir "native.env"
$PostgresTool = Join-Path $RepoRoot "tools\native-runtime\postgres.mjs"

function New-LocalSecret {
    $bytes = New-Object byte[] 36
    $generator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $generator.GetBytes($bytes) } finally { $generator.Dispose() }
    return [Convert]::ToBase64String($bytes).TrimEnd("=").Replace("+", "-").Replace("/", "_")
}

function Import-NativeEnvironment {
    if (-not (Test-Path -LiteralPath $EnvFile)) {
        throw "Native environment is missing. Run: .\scripts\native-infra.ps1 setup"
    }
    foreach ($line in Get-Content -LiteralPath $EnvFile) {
        if ($line -and -not $line.StartsWith("#")) {
            $name, $value = $line.Split("=", 2)
            Set-Item -Path "Env:$name" -Value $value
        }
    }
}

function Find-RedisExecutable([string]$Name) {
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    foreach ($pathEntry in ([Environment]::GetEnvironmentVariable("Path", "User") -split ";")) {
        if ($pathEntry) {
            $candidate = Join-Path $pathEntry "$Name.exe"
            if (Test-Path -LiteralPath $candidate) { return $candidate }
        }
    }
    $packageRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
    $package = Get-ChildItem -LiteralPath $packageRoot -Directory -Filter "taizod1024.redis-windows-fork_*" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($package) {
        $match = Get-ChildItem -LiteralPath $package.FullName -Recurse -Filter "$Name.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($match) { return $match.FullName }
    }
    throw "$Name was not found. Install it with: winget install --id taizod1024.redis-windows-fork"
}

function Test-TcpPort([int]$Port) {
    $client = [Net.Sockets.TcpClient]::new()
    try {
        $task = $client.ConnectAsync("127.0.0.1", $Port)
        return $task.Wait(750) -and $client.Connected
    } catch { return $false } finally { $client.Dispose() }
}

function Start-Redis {
    if (Test-TcpPort 56379) { return }
    $redisServer = Find-RedisExecutable "redis-server"
    $redisDir = Join-Path $RuntimeDir "redis"
    New-Item -ItemType Directory -Force -Path $redisDir | Out-Null
    $arguments = @(
        "--bind", "127.0.0.1", "--port", "56379", "--protected-mode", "yes",
        "--dir", $redisDir, "--dbfilename", "dump.rdb", "--appendonly", "yes",
        "--logfile", (Join-Path $RuntimeDir "redis.log")
    )
    $process = Start-Process -FilePath $redisServer -ArgumentList $arguments -WindowStyle Hidden -PassThru
    Set-Content -LiteralPath (Join-Path $RuntimeDir "redis.pid") -Value $process.Id
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        if (Test-TcpPort 56379) { return }
        Start-Sleep -Milliseconds 250
    }
    throw "Redis failed to start; inspect .runtime/redis.log."
}

function Stop-Redis {
    if (-not (Test-TcpPort 56379)) { return }
    $redisCli = Find-RedisExecutable "redis-cli"
    & $redisCli -h 127.0.0.1 -p 56379 shutdown
}

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

if ($Action -eq "setup") {
    if (-not (Test-Path -LiteralPath $EnvFile)) {
        $postgresPassword = New-LocalSecret
        $jwtSecret = New-LocalSecret
        $sensorKey = New-LocalSecret
        @(
            "ENVIRONMENT=development"
            "DATABASE_URL=postgresql+psycopg://honeypot:${postgresPassword}@127.0.0.1:55432/honeypot"
            "POSTGRES_PASSWORD=$postgresPassword"
            "REDIS_URL=redis://127.0.0.1:56379/0"
            "JWT_SECRET=$jwtSecret"
            "SENSOR_API_KEY=$sensorKey"
            "BOOTSTRAP_ADMIN_EMAIL=admin@example.com"
            "CORS_ORIGINS=http://127.0.0.1:3000,http://localhost:3000"
            "COOKIE_SECURE=false"
            "INGESTION_URL=http://127.0.0.1:8000/api/v1/ingest/events"
            "SSH_HOST_KEY_PATH=$($RuntimeDir.Replace('\', '/'))/ssh_host_key"
            "ML_MODEL_PATH=$($RepoRoot.Replace('\', '/'))/ml/model/baseline.joblib"
        ) | Set-Content -LiteralPath $EnvFile
    }
    Import-NativeEnvironment
    Set-Content -LiteralPath (Join-Path $RuntimeDir "postgres-password") -Value $env:POSTGRES_PASSWORD
    Push-Location (Join-Path $RepoRoot "tools\native-runtime")
    try { npm install } finally { Pop-Location }
    node $PostgresTool init
    Remove-Item -LiteralPath (Join-Path $RuntimeDir "postgres-password") -ErrorAction SilentlyContinue
    Write-Host "Native runtime initialized. Secrets are stored in ignored .runtime/native.env."
    exit 0
}

Import-NativeEnvironment
if ($Action -eq "start") {
    node $PostgresTool start
    Start-Redis
    Write-Host "Redis is ready on 127.0.0.1:56379."
} elseif ($Action -eq "stop") {
    Stop-Redis
    node $PostgresTool stop
} else {
    node $PostgresTool status
    $redisState = if (Test-TcpPort 56379) { "running" } else { "stopped" }
    Write-Host "Redis: $redisState"
}
