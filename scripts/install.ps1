<#
.SYNOPSIS
    Octoplant installatie-script.
    Eenmalig uitvoeren op een nieuw toestel om alles te configureren.

.DESCRIPTION
    1. Initialiseert de CredentialsManager-submodule
    2. Controleert of conda aanwezig is
    3. Maakt de conda omgeving "mcp-op" aan (of updatet die)
    4. Installeert Python-dependencies
    5. Controleert de meegeleverde release-builds
    6. Maakt een leeg .env-bestand aan (als nog niet aanwezig)

.NOTES
    Vereisten:
    - Anaconda, geïnstalleerd via het bedrijfsportaal
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$CondaExe = $null

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

function Find-CondaExe {
    $cmd = Get-Command conda -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $candidates = @(
        "$env:USERPROFILE\anaconda3\Scripts\conda.exe",
        "$env:USERPROFILE\AppData\Local\anaconda3\Scripts\conda.exe",
        "C:\ProgramData\anaconda3\Scripts\conda.exe",
        "C:\tools\anaconda3\Scripts\conda.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { return $candidate }
    }

    return $null
}

# --- 0. Build dependency ---
$gitModules = Join-Path $Root ".gitmodules"
if (Test-Path $gitModules -PathType Leaf) {
    $git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $git) {
        Abort "Git is nodig om de CredentialsManager-submodule te initialiseren."
    }

    Write-Step "CredentialsManager-submodule initialiseren"
    & $git.Source -C $Root submodule update --init --recursive
    if ($LASTEXITCODE -ne 0) {
        Abort "Initialiseren van de CredentialsManager-submodule mislukt."
    }
    Write-OK "CredentialsManager-submodule is beschikbaar."
}

# --- 1. Conda ---
Write-Step "Conda controleren"
$CondaExe = Find-CondaExe
if (-not $CondaExe) {
    Abort "Anaconda niet gevonden. Installeer Anaconda via het bedrijfsportaal en herstart dit script."
}
Write-OK "conda gevonden: $CondaExe"

# --- 2. Conda omgeving ---
Write-Step "Conda omgeving 'mcp-op' controleren"
$envExists = & $CondaExe env list 2>$null | Select-String "mcp-op"
if ($envExists) {
    Write-OK "Omgeving 'mcp-op' bestaat al."
} else {
    Write-Host "    Aanmaken..." -ForegroundColor Gray
    & $CondaExe create -n mcp-op python=3.12 -y
    if ($LASTEXITCODE -ne 0) { Abort "Aanmaken conda omgeving mislukt." }
    Write-OK "Omgeving 'mcp-op' aangemaakt."
}

# --- 3. Python dependencies ---
Write-Step "Python-dependencies installeren"
& $CondaExe run -n mcp-op pip install -e "$Root" --quiet
if ($LASTEXITCODE -ne 0) { Abort "pip install mislukt." }
Write-OK "Dependencies geinstalleerd."

# --- 4. Release-wrappers ---
Write-Step "Meegeleverde release-executables controleren"
$wrapperExe = Join-Path $Root "binaryTools\VDogCheckOut\publish\VDogCheckOut.exe"
$credentialsExe = Join-Path $Root "binaryTools\VDogCheckOut\publish\CredentialsManager.exe"
if (-not (Test-Path $wrapperExe -PathType Leaf)) {
    Abort "Meegeleverde VDogCheckOut.exe ontbreekt. Installeer de plugin opnieuw via de marketplace."
}
Write-OK "VDogCheckOut.exe aanwezig: $wrapperExe"
if (-not (Test-Path $credentialsExe -PathType Leaf)) {
    Abort "Meegeleverde CredentialsManager.exe ontbreekt. Installeer de plugin opnieuw via de marketplace."
}
Write-OK "CredentialsManager.exe aanwezig: $credentialsExe"

# --- 5. .env aanmaken ---
Write-Step ".env configuratie"
$envFile  = Join-Path $Root ".env"
if (Test-Path $envFile) {
    Write-OK ".env bestaat al (niet overschreven)."
} else {
    Copy-Item (Join-Path $Root ".env.example") $envFile
    Write-Warn ".env aangemaakt vanuit .env.example."
    Write-Warn "Vul de lokale configuratie in volgens de interne procedure."
}

# --- Klaar ---
Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "  Installatie voltooid." -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Volgende stappen:" -ForegroundColor White
Write-Host "  1. Pas .env aan voor dit toestel (als nog niet gedaan)"
Write-Host "  2. Maak de Windows-referentie aan volgens de interne procedure"
Write-Host "  3. Test: .\binaryTools\VDogCheckOut\publish\VDogCheckOut.exe login"
Write-Host "  4. Open GitHub Copilot Desktop en schakel de plugin in"
Write-Host ""