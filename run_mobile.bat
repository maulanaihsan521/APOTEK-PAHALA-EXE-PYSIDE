@echo off
setlocal
title Apotek Pahala - Mobile Dev Server
cd /d "%~dp0mobile-web"
if not exist "node_modules" (
    echo Memasang dependensi mobile...
    call npm install
    if errorlevel 1 goto :error
)
echo ============================================
echo  Mobile dev server: http://localhost:5173
echo  Dari ponsel gunakan alamat LAN yang tampil.
echo ============================================
call npm run dev
goto :eof
:error
echo Gagal memasang dependensi.
pause
endlocal
