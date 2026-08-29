<#
.SYNOPSIS
    Octoplant installatie-script.
    Eenmalig uitvoeren op een nieuw toestel om alles te configureren.

.DESCRIPTION
    1. Zoekt een geschikte Python 3.11+-runtime
    2. Maakt of hergebruikt de plugin-lokale .venv
    3. Installeert Python-dependencies
    4. Controleert de meegeleverde release-builds

.NOTES
    Vereisten:
    - Python 3.11 of hoger, beschikbaar als "py -3" of "python"
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"

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

# --- 1. Python en lokale virtuele omgeving ---
Write-Step "Python 3.11+ controleren"
$PythonRuntime = Find-PythonRuntime
if (-not $PythonRuntime) {
    Abort "Python 3.11+ niet gevonden. Installeer Python en maak 'py -3' of 'python' beschikbaar."
}
Write-OK "Python runtime gevonden: $($PythonRuntime.Command) $($PythonRuntime.Arguments -join ' ')"

if (-not (Test-Path $VenvPython -PathType Leaf)) {
    Write-Step "Plugin-lokale .venv aanmaken"
    & $PythonRuntime.Command @($PythonRuntime.Arguments) -m venv (Join-Path $Root ".venv")
    if ($LASTEXITCODE -ne 0) { Abort "Aanmaken van de plugin-lokale .venv mislukt." }
    Write-OK "Plugin-lokale .venv aangemaakt."
} else {
    Write-OK "Plugin-lokale .venv bestaat al."
}

# --- 2. Python dependencies ---
Write-Step "Python-dependencies installeren"
& $VenvPython -m pip install -e "$Root" --quiet
if ($LASTEXITCODE -ne 0) { Abort "pip install mislukt." }
Write-OK "Dependencies geinstalleerd."

# --- 3. Runtimepakket ---
$buildScript = Join-Path $Root "binaryTools\VDogCheckOut\build.ps1"
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
    if (-not (Test-Path (Join-Path $Root ".git") -PathType Container)) {
        Abort "Runtimepakket onvolledig. Installeer de plugin opnieuw via de marketplace."
    }

    Write-Step "Runtimepakket vanuit broncode bouwen"
    & $buildScript
    if ($LASTEXITCODE -ne 0) {
        Abort "Build van het runtimepakket mislukt."
    }
}

Write-Step "Runtimepakket controleren"
if (
    -not (Test-Path $wrapperExe -PathType Leaf) -or
    -not (Test-Path $credentialsExe -PathType Leaf) -or
    -not (Test-Path $credentialsPreferences -PathType Leaf) -or
    -not (Test-Path $credentialsSqliteNative -PathType Leaf)
) {
    Abort "Runtimepakket is onvolledig na installatie."
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
Write-Host "Volgende stappen:" -ForegroundColor White
Write-Host "  1. Maak de Windows-referentie en Octoplant-instellingen aan volgens de interne procedure"
Write-Host "  2. Test: .\binaryTools\VDogCheckOut\publish\VDogCheckOut.exe login"
Write-Host "  3. Open GitHub Copilot Desktop en schakel de plugin in"
Write-Host ""