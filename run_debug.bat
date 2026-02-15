@echo off
cd /d %~dp0
echo ========================================
echo Starting application in DEBUG mode
echo ========================================
echo Working directory: %CD%
echo ENV=debug
echo.
set ENV=debug
python src/main.py
echo.
echo ========================================
echo Application stopped
echo ========================================
pause
