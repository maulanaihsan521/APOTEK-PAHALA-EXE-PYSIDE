# Build paket Windows 7 (x64) untuk Apotek Pahala.
#
# Prasyarat:
#   - Python 3.8.10 x64 + packaging/requirements-win7.txt
#   - Python tooling modern dengan libcst (untuk prepare_win7.py)
#   - Inno Setup 6.2.2 (opsional; tanpa ini hanya folder portabel yang dibuat)
#
# Contoh:
#   $env:APOTEK_PY38 = "C:\build\.venv-win7\Scripts\python.exe"
#   $env:APOTEK_ISCC = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
#   powershell -ExecutionPolicy Bypass -File packaging\build_win7.ps1

param(
    [string]$Python38 = $env:APOTEK_PY38,
    [string]$ToolPython = "python",
    [string]$InnoCompiler = $env:APOTEK_ISCC,
    [switch]$SkipPrepare,
    [switch]$ConsoleBackend,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$Project = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BuildRoot = Join-Path $Project "build\win7"
$Stage = Join-Path $BuildRoot "stage"
$Dist = Join-Path $BuildRoot "dist"
$Work = Join-Path $BuildRoot "work"
$Portable = Join-Path $BuildRoot "ApotekPahala"
$InstallerDir = Join-Path $BuildRoot "installer"

function Invoke-Checked {
    param([string]$Description, [scriptblock]$Command)
    Write-Host "==> $Description"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Description gagal (exit code $LASTEXITCODE)."
    }
}

if ([string]::IsNullOrWhiteSpace($Python38)) {
    throw "Tentukan path Python 3.8.10 melalui -Python38 atau environment variable APOTEK_PY38."
}
if (-not (Test-Path $Python38)) {
    throw "Python 3.8 tidak ditemukan: $Python38"
}
if ([string]::IsNullOrWhiteSpace($InnoCompiler)) {
    $candidates = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe",
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            $InnoCompiler = $candidate
            break
        }
    }
}

Invoke-Checked "Memeriksa Python 3.8" {
    & $Python38 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 8) else 1)"
}
Invoke-Checked "Memeriksa PySide2, PyInstaller, dan dependensi backend" {
    & $Python38 -c "import PySide2, PyInstaller, fastapi, pandas, sklearn, scipy, reportlab; print('dependensi build OK')"
}
Invoke-Checked "Memeriksa libcst pada Python tooling" {
    & $ToolPython -c "import libcst; print('libcst OK')"
}

Write-Host "==> Menyiapkan staging"
if (-not $SkipPrepare) {
    & $ToolPython (Join-Path $PSScriptRoot "prepare_win7.py") --project $Project --out $Stage
    if ($LASTEXITCODE -ne 0) {
        throw "prepare_win7.py gagal (exit code $LASTEXITCODE)."
    }
} elseif (-not (Test-Path (Join-Path $Stage "desktop"))) {
    throw "Staging belum ada. Jalankan tanpa -SkipPrepare."
}

New-Item -ItemType Directory -Path $BuildRoot -Force | Out-Null
New-Item -ItemType Directory -Path $Dist -Force | Out-Null
New-Item -ItemType Directory -Path $Work -Force | Out-Null
$env:APOTEK_WIN7_STAGE = $Stage
$env:APOTEK_BACKEND_CONSOLE = if ($ConsoleBackend) { "1" } else { "0" }
$env:APOTEK_DESKTOP_CONSOLE = "0"

Invoke-Checked "Membangun backend (PyInstaller)" {
    & $Python38 -m PyInstaller --noconfirm --clean `
        --distpath $Dist --workpath $Work `
        (Join-Path $PSScriptRoot "specs\apotek-backend.spec")
}
Invoke-Checked "Membangun desktop (PyInstaller)" {
    & $Python38 -m PyInstaller --noconfirm --clean `
        --distpath $Dist --workpath $Work `
        (Join-Path $PSScriptRoot "specs\apotek-desktop.spec")
}

Write-Host "==> Menyusun folder portabel"
if (Test-Path $Portable) {
    Remove-Item $Portable -Recurse -Force
}
New-Item -ItemType Directory -Path $Portable | Out-Null
Copy-Item (Join-Path $Dist "ApotekPahala\*") $Portable -Recurse
Copy-Item (Join-Path $Dist "apotek-backend") (Join-Path $Portable "backend") -Recurse

$DocsTarget = Join-Path $Portable "docs"
New-Item -ItemType Directory -Path $DocsTarget -Force | Out-Null
foreach ($doc in @("WINDOWS7.md", "PANDUAN_PENGGUNA.md", "PENGUJIAN.md", "ARSITEKTUR.md", "WORK_LOG.md")) {
    $source = Join-Path $Project "docs\$doc"
    if (Test-Path $source) {
        Copy-Item $source $DocsTarget
    }
}
Copy-Item (Join-Path $Project "README.md") (Join-Path $Portable "README.md")
Copy-Item (Join-Path $Project "docs\WINDOWS7.md") (Join-Path $Portable "PANDUAN-WINDOWS7.txt")

$Zip = Join-Path $BuildRoot "ApotekPahala-1.0.0-win7-x64-portable.zip"
if (Test-Path $Zip) {
    Remove-Item $Zip -Force
}
Write-Host "==> Membuat arsip portabel"
# Compress-Archive gagal di sebagian mesin build dengan "user-mapped section
# open" saat file EXE/DLL baru saja disalin. ZipFile.CreateFromDirectory lebih
# andal dan tetap menghasilkan struktur arsip yang sama (isi folder di root).
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $Portable,
    $Zip,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $false
)
if (-not (Test-Path $Zip)) {
    throw "Arsip portabel gagal dibuat."
}

if ($SkipInstaller) {
    Write-Host "==> Installer dilewati (-SkipInstaller)."
} elseif ([string]::IsNullOrWhiteSpace($InnoCompiler) -or -not (Test-Path $InnoCompiler)) {
    Write-Warning "ISCC.exe tidak ditemukan. Folder portabel dan ZIP sudah dibuat, installer dilewati."
    Write-Warning "Pasang Inno Setup 6.2.2 atau set APOTEK_ISCC."
} else {
    New-Item -ItemType Directory -Path $InstallerDir -Force | Out-Null
    Invoke-Checked "Membuat installer (Inno Setup)" {
        & $InnoCompiler (Join-Path $PSScriptRoot "installer.iss")
    }
}

Write-Host ""
Write-Host "Selesai."
Write-Host "  Portabel : $Portable"
Write-Host "  ZIP      : $Zip"
if (Test-Path (Join-Path $InstallerDir "ApotekPahala-Setup-1.0.0-win7-x64.exe")) {
    Write-Host "  Installer: $(Join-Path $InstallerDir 'ApotekPahala-Setup-1.0.0-win7-x64.exe')"
}
