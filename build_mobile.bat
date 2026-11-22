@echo off
setlocal
title Apotek Pahala - Build Mobile
cd /d "%~dp0mobile-web"
if not exist "node_modules" (
    echo Memasang dependensi mobile...
    call npm install
    if errorlevel 1 goto :error
)
echo Membangun mobile web...
call npm run build
if errorlevel 1 goto :error
echo.
echo Build selesai. Hasil ada di mobile-web\dist dan disajikan backend
echo pada http://127.0.0.1:8000/
goto :eof
:error
echo Build gagal. Periksa pesan di atas.
pause
endlocal
