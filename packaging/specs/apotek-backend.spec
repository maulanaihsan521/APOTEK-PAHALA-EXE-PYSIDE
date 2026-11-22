# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec backend Apotek Pahala untuk Windows 7 (x64, Python 3.8)."""
import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

PROJECT = Path(SPECPATH).resolve().parents[1]
STAGE = Path(os.environ.get("APOTEK_WIN7_STAGE", PROJECT / "build" / "win7" / "stage")).resolve()
ICON = str(PROJECT / "packaging" / "assets" / "apotek-pahala.ico")
VERSION = str(PROJECT / "packaging" / "version_info.txt")

if str(STAGE / "backend") not in sys.path:
    sys.path.insert(0, str(STAGE / "backend"))

datas = [
    (str(STAGE / "mobile-web" / "dist"), "mobile-web/dist"),
    (str(STAGE / "datasets"), "datasets"),
]
for name in ("apotek_pahala.db",):
    candidate = STAGE / "storage" / name
    if candidate.exists():
        datas.append((str(candidate), "storage"))

hiddenimports = sorted(
    set(
        collect_submodules("app")
        + collect_submodules("uvicorn")
        + [
            "anyio._backends._asyncio",
            "sqlalchemy.dialects.sqlite",
            "sqlalchemy.dialects.sqlite.pysqlite",
        ]
    )
)

a = Analysis(
    [str(STAGE / "backend" / "run.py")],
    pathex=[str(STAGE / "backend")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "PySide2",
        "PyQt5",
        "IPython",
        "notebook",
        "pytest",
        "sphinx",
        "pandas.tests",
        "numpy.tests",
        "sklearn.tests",
        "scipy.tests",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

console = os.environ.get("APOTEK_BACKEND_CONSOLE", "0") == "1"
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="apotek-backend",
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
    name="apotek-backend",
)
