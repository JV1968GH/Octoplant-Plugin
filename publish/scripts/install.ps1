<#
.SYNOPSIS
    Octoplant installatie-script.
    Eenmalig uitvoeren op een nieuw toestel om alles te configureren.

.DESCRIPTION
    1. Zoekt een geschikte Python 3.11+-runtime
    2. Maakt of hergebruikt de gebruiker-lokale runtime-venv
    3. Installeert Python-dependencies
    4. Controleert de meegeleverde release-builds

.NOTES
    Vereisten:
    - Python 3.11 of hoger, beschikbaar als "py -3" of "python"
#>

[CmdletBinding()]
param(
    [string]$PythonPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$PluginId = "octoplant"
if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    throw "LOCALAPPDATA is unavailable. Start PowerShell in a normal user session and run the installer again."
}

$RuntimeRoot = Join-Path $env:LOCALAPPDATA "AI\Plugins\$PluginId\runtime"
$VenvPath = Join-Path $RuntimeRoot "venv"
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"

function Write-Step([string]$msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

function Write-OK([string]$msg) {
    Write-Host "    [OK] $msg" -ForegroundColor Green
}

function Write-Warn([string]$msg) {
    Write-Host "    [!]  $msg" -ForegroundColor Yellow
}

function Abort([string]$msg) {
    Write-Host ""
    Write-Host "[FOUT] $msg" -ForegroundColor Red
    exit 1
}

function Test-PythonRuntime([string]$Command, [string[]]$Arguments) {
    try {
        & $Command @Arguments -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Find-PythonRuntime {
    if (-not [string]::IsNullOrWhiteSpace($PythonPath)) {
        $resolvedPython = Resolve-Path -LiteralPath $PythonPath -ErrorAction SilentlyContinue
        if (-not $resolvedPython -or -not (Test-PythonRuntime $resolvedPython.Path @())) {
            Abort "De opgegeven Python-runtime is niet bruikbaar: $PythonPath. Gebruik Python 3.11 of hoger."
        }
        return @{
            Command = $resolvedPython.Path
            Arguments = @()
        }
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py -and (Test-PythonRuntime $py.Source @("-3"))) {
        return @{
            Command = $py.Source
            Arguments = @("-3")
        }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python -and (Test-PythonRuntime $python.Source @())) {
        return @{
            Command = $python.Source
            Arguments = @()
        }
    }

    return $null
}

# --- 1. Python en gebruiker-lokale virtuele omgeving ---
Write-Step "Python 3.11+ controleren"
$PythonRuntime = Find-PythonRuntime
if (-not $PythonRuntime) {
    Abort "Python 3.11+ niet gevonden. Installeer Python voor de huidige gebruiker en maak 'py -3' of 'python' beschikbaar."
}
Write-OK "Python runtime gevonden: $($PythonRuntime.Command) $($PythonRuntime.Arguments -join ' ')"

if (-not (Test-Path $VenvPython -PathType Leaf)) {
    Write-Step "Gebruiker-lokale MCP-runtime aanmaken"
    New-Item -ItemType Directory -Path $RuntimeRoot -Force | Out-Null
    & $PythonRuntime.Command @($PythonRuntime.Arguments) -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) { Abort "Aanmaken van de gebruiker-lokale runtime mislukt: $VenvPath" }
    Write-OK "Gebruiker-lokale runtime aangemaakt: $VenvPath"
} else {
    Write-OK "Gebruiker-lokale runtime bestaat al: $VenvPath"
}

# --- 2. Python dependencies ---
Write-Step "Python-dependencies installeren"
& $VenvPython -m pip install --disable-pip-version-check --upgrade "$Root" --quiet
if ($LASTEXITCODE -ne 0) {
    Abort "pip install mislukt. Controleer de netwerk- of proxytoegang en voer het script opnieuw uit."
}
& $VenvPython -c "from mcp.server.fastmcp import FastMCP"
if ($LASTEXITCODE -ne 0) {
    Abort "FastMCP kon niet uit de gebruiker-lokale runtime worden geladen. Voer het script opnieuw uit."
}
Write-OK "Dependencies geinstalleerd."

# --- 3. Runtimepakket ---
$wrapperExe = Join-Path $Root "binaryTools\VDogCheckOut\publish\VDogCheckOut.exe"
$credentialsExe = Join-Path $Root "binaryTools\VDogCheckOut\publish\CredentialsManager.exe"
$credentialsPreferences = Join-Path $Root "binaryTools\VDogCheckOut\publish\CredentialsManager.preferences.json"
$credentialsSqliteNative = Join-Path $Root "binaryTools\VDogCheckOut\publish\e_sqlite3.dll"
if (
    -not (Test-Path $wrapperExe -PathType Leaf) -or
    -not (Test-Path $credentialsExe -PathType Leaf) -or
    -not (Test-Path $credentialsPreferences -PathType Leaf) -or
    -not (Test-Path $credentialsSqliteNative -PathType Leaf)
) {
    Abort "Runtimepakket onvolledig. Installeer de plugin opnieuw via de marketplace; de installatiemap blijft read-only."
}

Write-Step "Runtimepakket controleren"
if (
    -not (Test-Path $wrapperExe -PathType Leaf) -or
    -not (Test-Path $credentialsExe -PathType Leaf) -or
    -not (Test-Path $credentialsPreferences -PathType Leaf) -or
    -not (Test-Path $credentialsSqliteNative -PathType Leaf)
) {
    Abort "Runtimepakket is onvolledig. Installeer de plugin opnieuw via de marketplace."
}
Write-OK "VDogCheckOut.exe aanwezig: $wrapperExe"
Write-OK "CredentialsManager.exe aanwezig: $credentialsExe"
Write-OK "CredentialsManager-instellingen aanwezig: $credentialsPreferences"
Write-OK "SQLite native library aanwezig: $credentialsSqliteNative"

# --- Klaar ---
Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "  Installatie voltooid." -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host ""
Write-Host "MCP-runtime: $VenvPath"
Write-Host "Volgende stappen:" -ForegroundColor White
Write-Host "  1. Maak de Windows-referentie en Octoplant-instellingen aan volgens de interne procedure"
Write-Host "  2. Test: .\binaryTools\VDogCheckOut\publish\VDogCheckOut.exe login"
Write-Host "  3. Open GitHub Copilot Desktop en schakel de plugin in"
Write-Host ""