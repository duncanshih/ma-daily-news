@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
pythonw src\gui.py
if errorlevel 1 (
    echo.
    echo [!] pythonw failed, trying python...
    python src\gui.py
    pause
)
