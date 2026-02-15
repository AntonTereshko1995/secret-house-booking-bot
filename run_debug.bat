@echo off
cd /d %~dp0
set ENV=debug
python src/main.py
pause
