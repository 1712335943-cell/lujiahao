$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,

        [Parameter(Mandatory = $false)]
        [string[]]$Arguments = @()
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Command $($Arguments -join ' ')"
    }
}

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
    Invoke-Checked $Python.Command ($Python.Args + @("-m", "venv", $VenvDir))
}

Invoke-Checked $VenvPython @("-m", "pip", "install", "--upgrade", "pip")
Invoke-Checked $VenvPython @("-m", "pip", "install", "-r", "requirements.txt", "pyinstaller")

if (Test-Path "build") {
    Remove-Item "build" -Recurse -Force
}
if (Test-Path "dist") {
    Remove-Item "dist" -Recurse -Force
}
if (Test-Path "release") {
    Remove-Item "release" -Recurse -Force
}

Invoke-Checked $VenvPython @("-m", "PyInstaller", "--clean", "--noconfirm", "DesktopPet.spec")

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

Invoke-Checked $Iscc @("installer\DesktopPet.iss")

$InstallerPath = Join-Path $Root "release\DesktopPetSetup.exe"
if (-not (Test-Path $InstallerPath)) {
    throw "Installer was not created: $InstallerPath"
}

Write-Host ""
Write-Host "Windows installer created:"
Write-Host $InstallerPath
