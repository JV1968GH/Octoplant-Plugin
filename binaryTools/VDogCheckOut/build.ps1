<#
.SYNOPSIS
    Bouw VDogCheckOut.exe als self-contained Windows x64 binary.

.DESCRIPTION
    Vereist: .NET SDK 8 of hoger (https://dotnet.microsoft.com/download)
    Uitvoer: binaryTools\VDogCheckOut\publish\VDogCheckOut.exe

.EXAMPLE
    Vanuit de Octoplant projectroot:
        .\binaryTools\VDogCheckOut\build.ps1
#>

$ErrorActionPreference = "Stop"

$projectDir = $PSScriptRoot
$publishDir = Join-Path $projectDir "publish"

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
if (Test-Path $exe) {
    $size = [math]::Round((Get-Item $exe).Length / 1MB, 1)
    Write-Host ""
    Write-Host "Klaar: $exe  ($size MB)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Gebruik (vanuit de Octoplant projectroot, zodat .env gevonden wordt):" -ForegroundColor Yellow
    Write-Host "  .\binaryTools\VDogCheckOut\publish\VDogCheckOut.exe --help"
    Write-Host "  .\binaryTools\VDogCheckOut\publish\VDogCheckOut.exe login"
    Write-Host "  .\binaryTools\VDogCheckOut\publish\VDogCheckOut.exe `"RWZI's\100026 - Dendermonde\..`""
    Write-Host "  .\binaryTools\VDogCheckOut\publish\VDogCheckOut.exe --all"
    Write-Host ""
    Write-Host "Zorg dat credentials beschikbaar zijn op dit toestel." -ForegroundColor Yellow
} else {
    Write-Host "Exe niet gevonden na build. Controleer de uitvoer hierboven." -ForegroundColor Red
    exit 1
}