$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Resolve-Python {
    try {
        & py -3 --version | Out-Null
        return @{
            Command = "py"
            Args = @("-3")
        }
    } catch {
        & python --version | Out-Null
        return @{
            Command = "python"
            Args = @()
        }
    }
}

$Python = Resolve-Python
$VenvDir = Join-Path $Root ".venv-win"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    & $Python.Command @($Python.Args) -m venv $VenvDir
}

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r requirements.txt pyinstaller

if (Test-Path "build") {
    Remove-Item "build" -Recurse -Force
}
if (Test-Path "dist") {
    Remove-Item "dist" -Recurse -Force
}
if (Test-Path "release") {
    Remove-Item "release" -Recurse -Force
}

& $VenvPython -m PyInstaller --clean --noconfirm DesktopPet.spec

$IsccCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
)
$Iscc = $IsccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $Iscc) {
    Write-Host ""
    Write-Host "PyInstaller build finished: $Root\dist\DesktopPet\DesktopPet.exe"
    Write-Host "Inno Setup 6 was not found, so installer generation was skipped."
    Write-Host "Install Inno Setup 6, then rerun this script to create release\DesktopPetSetup.exe."
    exit 0
}

& $Iscc "installer\DesktopPet.iss"

Write-Host ""
Write-Host "Windows installer created:"
Write-Host "$Root\release\DesktopPetSetup.exe"
