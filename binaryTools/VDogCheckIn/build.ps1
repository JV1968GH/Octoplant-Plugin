$ErrorActionPreference = "Stop"
$projectDir = $PSScriptRoot
$publishDir = Join-Path $projectDir "publish"
$checkoutDir = Split-Path -Parent $projectDir
$credentialsDir = Join-Path $checkoutDir "VDogCheckOut\publish"

& (Join-Path $checkoutDir "VDogCheckOut\build.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

dotnet publish (Join-Path $projectDir "VDogCheckIn.csproj") --configuration Release --runtime win-x64 --self-contained true -p:PublishSingleFile=true -p:EnableCompressionInSingleFile=true --output $publishDir --nologo
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Copy-Item (Join-Path $credentialsDir "CredentialsManager.exe"), (Join-Path $credentialsDir "CredentialsManager.preferences.json"), (Join-Path $credentialsDir "e_sqlite3.dll") -Destination $publishDir -Force
