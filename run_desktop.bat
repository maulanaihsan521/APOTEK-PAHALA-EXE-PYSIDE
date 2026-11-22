@echo off
setlocal
title Apotek Pahala - Desktop
cd /d "%~dp0desktop"
echo Menjalankan aplikasi desktop Apotek Pahala...
if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" run.py %*
) else (
    python run.py %*
)
endlocal
