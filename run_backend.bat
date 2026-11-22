@echo off
setlocal
title Apotek Pahala - Backend
cd /d "%~dp0backend"
echo ============================================
echo  Apotek Pahala - Backend API
echo  http://127.0.0.1:8000
echo  Dokumentasi: http://127.0.0.1:8000/api/docs
echo ============================================
if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" run.py --host 0.0.0.0 --port 8000 %*
) else (
    python run.py --host 0.0.0.0 --port 8000 %*
)
endlocal
