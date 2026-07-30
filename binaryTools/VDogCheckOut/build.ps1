<#
.SYNOPSIS
    Bouw VDogCheckOut.exe als self-contained Windows x64 binary.

.DESCRIPTION
    Ontwikkelaarstool. Vereist: .NET SDK 10 of hoger
    Uitvoer: binaryTools\VDogCheckOut\publish\VDogCheckOut.exe

.EXAMPLE
    Vanuit de Octoplant projectroot:
        .\binaryTools\VDogCheckOut\build.ps1
#>

$ErrorActionPreference = "Stop"

$projectDir = $PSScriptRoot
$publishDir = Join-Path $projectDir "publish"
$binaryToolsDir = Split-Path -Parent $projectDir
$credentialsProjectDir = Join-Path $binaryToolsDir "CredentialsManager"
$credentialsProject = Join-Path $credentialsProjectDir "CredentialsManager.csproj"
$credentialsPublishDir = Join-Path $credentialsProjectDir "publish"
$credentialsExe = Join-Path $credentialsPublishDir "CredentialsManager.exe"

if (-not (Test-Path $credentialsProject -PathType Leaf)) {
    $root = Split-Path -Parent $binaryToolsDir
    if (-not (Test-Path (Join-Path $root ".git") -PathType Container)) {
        Write-Host "CredentialsManager-submodule ontbreekt. Installeer de plugin opnieuw via de marketplace." -ForegroundColor Red
        exit 1
    }

    $git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $git) {
        Write-Host "Git is nodig om de CredentialsManager-submodule te initialiseren." -ForegroundColor Red
        exit 1
    }

    Write-Host "CredentialsManager-submodule initialiseren..." -ForegroundColor Cyan
    & $git.Source -C $root submodule update --init --recursive
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $credentialsProject -PathType Leaf)) {
        Write-Host "Initialiseren van de CredentialsManager-submodule mislukt." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Bouwen van CredentialsManager (Release, win-x64, self-contained)..." -ForegroundColor Cyan

dotnet publish $credentialsProject `
    --configuration Release `
    --runtime win-x64 `
    --self-contained true `
    -p:PublishSingleFile=true `
    -p:EnableCompressionInSingleFile=true `
    --output $credentialsPublishDir `
    --nologo

if ($LASTEXITCODE -ne 0 -or -not (Test-Path $credentialsExe -PathType Leaf)) {
    Write-Host "Build van CredentialsManager mislukt." -ForegroundColor Red
    exit 1
}

Write-Host "Bouwen van VDogCheckOut (Release, win-x64, self-contained)..." -ForegroundColor Cyan

dotnet publish "$projectDir\VDogCheckOut.csproj" `
    --configuration Release `
    --runtime win-x64 `
    --self-contained true `
    -p:PublishSingleFile=true `
    -p:EnableCompressionInSingleFile=true `
    --output $publishDir `
    --nologo

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build mislukt (exit code $LASTEXITCODE)." -ForegroundColor Red
    exit $LASTEXITCODE
}

$exe = Join-Path $publishDir "VDogCheckOut.exe"
if ((Test-Path $exe -PathType Leaf) -and (Test-Path $credentialsExe -PathType Leaf)) {
    Copy-Item $credentialsExe (Join-Path $publishDir "CredentialsManager.exe") -Force
    $size = [math]::Round((Get-Item $exe).Length / 1MB, 1)
    Write-Host ""
    Write-Host "Klaar: $exe  ($size MB) met CredentialsManager.exe" -ForegroundColor Green
    Write-Host ""
    Write-Host "Gebruik (vanuit de Octoplant projectroot, zodat .env gevonden wordt):" -ForegroundColor Yellow
    Write-Host "  .\binaryTools\VDogCheckOut\publish\VDogCheckOut.exe --help"
    Write-Host "  .\binaryTools\VDogCheckOut\publish\VDogCheckOut.exe login"
    Write-Host "  .\binaryTools\VDogCheckOut\publish\VDogCheckOut.exe `"RWZI's\100026 - Dendermonde\..`""
    Write-Host "  .\binaryTools\VDogCheckOut\publish\VDogCheckOut.exe --all"
    Write-Host ""
    Write-Host "Zorg dat credentials beschikbaar zijn op dit toestel." -ForegroundColor Yellow
} else {
    Write-Host "Release-executables ontbreken na build. Controleer de uitvoer hierboven." -ForegroundColor Red
    exit 1
}