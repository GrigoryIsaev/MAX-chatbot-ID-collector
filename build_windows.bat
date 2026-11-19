@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo Building MAX ID Collector
echo ==========================================

py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name MAX_ID_Collector max_id_collector.py
if errorlevel 1 (
    echo.
    echo Build failed. Check the error messages above.
    pause
    exit /b 1
)

echo.
echo Build completed successfully.
echo Output: dist\MAX_ID_Collector.exe
pause
