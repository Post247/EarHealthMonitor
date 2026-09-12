@echo off
title Ear Health Monitor
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
    echo Python is not installed or not on PATH.
    echo Install it from https://www.python.org/downloads/
    pause
    exit /b 1
)
start "" pythonw app.py