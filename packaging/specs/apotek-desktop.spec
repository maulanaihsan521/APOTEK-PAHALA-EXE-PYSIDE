# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec desktop Apotek Pahala untuk Windows 7 (x64, Python 3.8)."""
import os
from pathlib import Path

PROJECT = Path(SPECPATH).resolve().parents[1]
STAGE = Path(os.environ.get("APOTEK_WIN7_STAGE", PROJECT / "build" / "win7" / "stage")).resolve()
ICON = str(PROJECT / "packaging" / "assets" / "apotek-pahala.ico")
VERSION = str(PROJECT / "packaging" / "version_info.txt")

a = Analysis(
    [str(STAGE / "desktop" / "run.py")],
    pathex=[str(STAGE / "desktop")],
    binaries=[],
    datas=[(str(STAGE / "desktop" / "app" / "assets"), "app/assets")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "pytest",
        "pandas",
        "numpy",
        "scipy",
        "sklearn",
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "reportlab",
        "openpyxl",
        "PIL",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

console = os.environ.get("APOTEK_DESKTOP_CONSOLE", "0") == "1"
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ApotekPahala",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=console,
    icon=ICON,
    version=VERSION,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ApotekPahala",
)
