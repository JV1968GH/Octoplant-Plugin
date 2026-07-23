<#
.SYNOPSIS
    Octoplant installatie-script.
    Eenmalig uitvoeren op een nieuw toestel om alles te configureren.

.DESCRIPTION
    1. Controleert of conda aanwezig is
    2. Maakt de conda omgeving "mcp-op" aan (of updatet die)
    3. Installeert Python-dependencies
    4. Bouwt VDogCheckOut.exe (.NET)
    5. Maakt een leeg .env-bestand aan (als nog niet aanwezig)

.NOTES
    Vereisten:
    - Anaconda of Miniconda (https://www.anaconda.com)
    - .NET SDK 10+ (https://dotnet.microsoft.com)
    - Git (https://git-scm.com)
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
        "$env:USERPROFILE\miniconda3\Scripts\conda.exe",
        "$env:USERPROFILE\AppData\Local\anaconda3\Scripts\conda.exe",
        "$env:USERPROFILE\AppData\Local\miniconda3\Scripts\conda.exe",
        "C:\ProgramData\anaconda3\Scripts\conda.exe",
        "C:\ProgramData\miniconda3\Scripts\conda.exe",
        "C:\tools\anaconda3\Scripts\conda.exe",
        "C:\tools\miniconda3\Scripts\conda.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { return $candidate }
    }

    return $null
}

# --- 1. Conda ---
Write-Step "Conda controleren"
$CondaExe = Find-CondaExe
if (-not $CondaExe) {
    Abort "conda niet gevonden in PATH.`nInstalleer Anaconda of Miniconda en herstart dit script."
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

# --- 4. VDogCheckOut.exe bouwen ---
Write-Step "VDogCheckOut.exe bouwen"
$csprojDir = Join-Path $Root "binaryTools\VDogCheckOut"
$publishDir = Join-Path $csprojDir "publish"

if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    Write-Warn ".NET SDK niet gevonden. VDogCheckOut.exe wordt niet gebouwd."
    Write-Warn "Installeer .NET SDK 10+: https://dotnet.microsoft.com/download"
} else {
    Push-Location $csprojDir
    dotnet publish VDogCheckOut.csproj `
        --configuration Release `
        --runtime win-x64 `
        --self-contained true `
        -p:PublishSingleFile=true `
        -p:EnableCompressionInSingleFile=true `
        --output publish `
        --nologo
    Pop-Location
    if ($LASTEXITCODE -ne 0) { Abort "Bouwen VDogCheckOut.exe mislukt." }
    Write-OK "VDogCheckOut.exe gebouwd: $publishDir\VDogCheckOut.exe"
}

# --- 5. .env aanmaken ---
Write-Step ".env configuratie"
$envFile  = Join-Path $Root ".env"
if (Test-Path $envFile) {
    Write-OK ".env bestaat al (niet overschreven)."
} else {
    New-Item -ItemType File -Path $envFile | Out-Null
    Write-Warn "Leeg .env-bestand aangemaakt."
    Write-Warn "Pas .env aan met de correcte waarden voor dit toestel:"
    Write-Warn "  - OCTOPLANT_SERVER"
    Write-Warn "  - OCTOPLANT_ARCHIVE_PATH"
    Write-Warn "  - OCTOPLANT_SERVER_ARCHIVE_PATH (optioneel; gedeelde read-only archive)"
    Write-Warn "  - OCTOPLANT_VDOG_CLIENT_PATH (alleen indien auto-discover niet werkt)"
}

# --- Klaar ---
Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "  Installatie voltooid." -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Volgende stappen:" -ForegroundColor White
Write-Host "  1. Pas .env aan voor dit toestel (als nog niet gedaan)"
Write-Host "  2. Voorzie credentials volgens interne procedure"
Write-Host "  3. Test: .\binaryTools\VDogCheckOut\publish\VDogCheckOut.exe login"
Write-Host "  4. Open de workspace in VS Code -- de MCP-server start automatisch"
Write-Host ""