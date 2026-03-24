param(
    [ValidateSet("game", "lan")]
    [string]$Mode = "game"
)

$ErrorActionPreference = "Stop"
$global:PSNativeCommandUseErrorActionPreference = $false
$LauncherStatePath = Join-Path $PSScriptRoot ".launcher_state.json"

function Write-Section {
    param([string]$Text)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " $Text" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Test-PythonCandidate {
    param(
        [string]$Command,
        [string[]]$PrefixArgs = @()
    )

    try {
        & $Command @PrefixArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" | Out-Null
        if ($LASTEXITCODE -eq 0) {
            return @{
                Command = $Command
                PrefixArgs = $PrefixArgs
            }
        }
    } catch {
        return $null
    }

    return $null
}

function Get-PythonCandidate {
    $candidates = @(
        @{ Command = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"; PrefixArgs = @() },
        @{ Command = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"; PrefixArgs = @() },
        @{ Command = "$env:LOCALAPPDATA\Python312\python.exe"; PrefixArgs = @() },
        @{ Command = "$env:LOCALAPPDATA\Python311\python.exe"; PrefixArgs = @() },
        @{ Command = "py"; PrefixArgs = @("-3.12") },
        @{ Command = "py"; PrefixArgs = @("-3.11") },
        @{ Command = "py"; PrefixArgs = @("-3.10") },
        @{ Command = "python"; PrefixArgs = @() },
        @{ Command = "py"; PrefixArgs = @() }
    )

    foreach ($candidate in $candidates) {
        if ($candidate.Command -like "*.exe" -and -not (Test-Path $candidate.Command)) {
            continue
        }

        $result = Test-PythonCandidate -Command $candidate.Command -PrefixArgs $candidate.PrefixArgs
        if ($null -ne $result) {
            return $result
        }
    }

    return $null
}

function Install-PythonWithWinget {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($null -eq $winget) {
        return $false
    }

    Write-Host "Python 3.10+ was not found. Installing Python 3.12 with winget..."
    & $winget.Source install --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements --scope user
    return ($LASTEXITCODE -eq 0)
}

function Ensure-Python {
    $python = Get-PythonCandidate
    if ($null -ne $python) {
        return $python
    }

    if (Install-PythonWithWinget) {
        $python = Get-PythonCandidate
        if ($null -ne $python) {
            return $python
        }
    }

    throw "Python 3.10 or newer is required. Install it from https://www.python.org/downloads/windows/ and rerun this launcher."
}

function Invoke-Python {
    param(
        [hashtable]$Python,
        [string[]]$PythonArgs
    )

    $allArgs = @($Python.PrefixArgs + $PythonArgs)
    $quotedArgs = $allArgs | ForEach-Object {
        if ($_ -match '[\s"]') {
            '"' + ($_ -replace '"', '\"') + '"'
        } else {
            $_
        }
    }
    $process = Start-Process -FilePath $Python.Command -ArgumentList ($quotedArgs -join " ") -Wait -NoNewWindow -PassThru
    return $process.ExitCode
}

function Ensure-Dependencies {
    param([hashtable]$Python)

    $requirementsPath = Join-Path $PSScriptRoot "requirements.txt"
    $requirementsHash = (Get-FileHash $requirementsPath -Algorithm SHA256).Hash
    $pythonVersion = & $Python.Command @($Python.PrefixArgs + @("-c", "import sys; print(sys.version.split()[0])"))
    $state = $null

    if (Test-Path $LauncherStatePath) {
        try {
            $state = Get-Content $LauncherStatePath -Raw | ConvertFrom-Json
        } catch {
            $state = $null
        }
    }

    $needsInstall = $true
    if ($null -ne $state) {
        if (
            $state.requirements_hash -eq $requirementsHash -and
            $state.python_version -eq $pythonVersion
        ) {
            $checkExit = Invoke-Python -Python $Python -PythonArgs @(
                "-c",
                "import importlib.util, sys; modules = ('pygame', 'pytest'); raise SystemExit(0 if all(importlib.util.find_spec(m) for m in modules) else 1)"
            )
            if ($checkExit -eq 0) {
                $needsInstall = $false
            }
        }
    }

    if (-not $needsInstall) {
        Write-Host "Dependencies already verified. Skipping pip install."
        return
    }

    Write-Host "Installing or updating Python packages..."
    Invoke-Python -Python $Python -PythonArgs @("-m", "pip", "install", "--upgrade", "pip", "--user") | Out-Null
    $pipExit = Invoke-Python -Python $Python -PythonArgs @("-m", "pip", "install", "-r", "requirements.txt", "--user")
    if ($pipExit -ne 0) {
        throw "Failed to install requirements from requirements.txt."
    }

    @{
        requirements_hash = $requirementsHash
        python_version = $pythonVersion
        verified_at = (Get-Date).ToString("s")
    } | ConvertTo-Json | Set-Content $LauncherStatePath
}

function Get-LocalIPv4Addresses {
    $addresses = [System.Net.Dns]::GetHostAddresses([System.Net.Dns]::GetHostName()) |
        Where-Object { $_.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork } |
        ForEach-Object { $_.IPAddressToString } |
        Where-Object { $_ -notlike "127.*" } |
        Select-Object -Unique
    return @($addresses)
}

function Reset-NetworkEnvironment {
    Remove-Item Env:\BOSS_RUSH_NETWORK_MODE -ErrorAction SilentlyContinue
    Remove-Item Env:\BOSS_RUSH_HOST -ErrorAction SilentlyContinue
    Remove-Item Env:\BOSS_RUSH_PORT -ErrorAction SilentlyContinue
    Remove-Item Env:\BOSS_RUSH_PLAYER_SLOT -ErrorAction SilentlyContinue
    Remove-Item Env:\BOSS_RUSH_PLAYERS -ErrorAction SilentlyContinue
}

function Start-Game {
    param([hashtable]$Python)

    Reset-NetworkEnvironment
    Write-Section "Starting Boss Rush Game"
    Write-Host "Launching game window..."
    return (Invoke-Python -Python $Python -PythonArgs @("main.py"))
}

function Start-LanSession {
    param([hashtable]$Python)

    Write-Section "Boss Rush Multiplayer"
    Write-Host "1) Host a game"
    Write-Host "2) Join as Player 2"
    Write-Host "3) Join as Player 3"
    Write-Host "4) Join as Player 4"
    Write-Host "5) Join with automatic slot"
    Write-Host ""

    $choice = Read-Host "Enter choice (1-5)"
    Reset-NetworkEnvironment

    switch ($choice) {
        "1" {
            $ips = Get-LocalIPv4Addresses
            if ($ips.Count -gt 0) {
                Write-Host ""
                Write-Host "Share one of these IP addresses with other players:"
                foreach ($ip in $ips) {
                    Write-Host " - $ip"
                }
            }

            $bind = Read-Host "Host bind IP [0.0.0.0]"
            if ([string]::IsNullOrWhiteSpace($bind)) {
                $bind = "0.0.0.0"
            }

            $port = Read-Host "Port [50000]"
            if ([string]::IsNullOrWhiteSpace($port)) {
                $port = "50000"
            }

            $env:BOSS_RUSH_NETWORK_MODE = "host"
            $env:BOSS_RUSH_HOST = $bind
            $env:BOSS_RUSH_PORT = $port
            $env:BOSS_RUSH_PLAYERS = "1"

            Write-Host ""
            Write-Host "Hosting on $bind`:$port"
            Write-Host "If Windows Firewall prompts you, allow Python on Private networks."
            Write-Host "Launching host window..."
            return (Invoke-Python -Python $Python -PythonArgs @("main.py"))
        }
        "2" {
            $env:BOSS_RUSH_PLAYER_SLOT = "2"
        }
        "3" {
            $env:BOSS_RUSH_PLAYER_SLOT = "3"
        }
        "4" {
            $env:BOSS_RUSH_PLAYER_SLOT = "4"
        }
        "5" {
            $env:BOSS_RUSH_PLAYER_SLOT = "auto"
        }
        default {
            throw "Invalid selection."
        }
    }

    $host = Read-Host "Host IP address"
    if ([string]::IsNullOrWhiteSpace($host)) {
        throw "Host IP is required for client mode."
    }

    $port = Read-Host "Port [50000]"
    if ([string]::IsNullOrWhiteSpace($port)) {
        $port = "50000"
    }

    $env:BOSS_RUSH_NETWORK_MODE = "client"
    $env:BOSS_RUSH_HOST = $host
    $env:BOSS_RUSH_PORT = $port

    Write-Host ""
    Write-Host "Connecting to $host`:$port"
    Write-Host "Launching client window..."
    return (Invoke-Python -Python $Python -PythonArgs @("main.py"))
}

Set-Location $PSScriptRoot
Write-Section "Boss Rush Bootstrap"

try {
    $python = Ensure-Python
    $versionText = & $python.Command @($python.PrefixArgs + @("--version"))
    Write-Host "Using $versionText"
    Ensure-Dependencies -Python $python

    if ($Mode -eq "lan") {
        $exitCode = Start-LanSession -Python $python
    } else {
        $exitCode = Start-Game -Python $python
    }
} catch {
    Write-Host ""
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Session ended."
if ($null -ne $exitCode) {
    exit $exitCode
}
