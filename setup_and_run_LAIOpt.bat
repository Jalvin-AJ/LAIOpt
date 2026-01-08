@echo off
echo ======================================
echo LAIOpt Setup and Launch
echo ======================================

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit
)

echo Python detected.

REM Upgrade pip
python -m pip install --upgrade pip

REM Install requirements
echo Installing required packages...
python -m pip install streamlit matplotlib pandas numpy

REM Set project path
set PYTHONPATH=.

echo Launching LAIOpt...
python -m streamlit run laiopt/frontend/app.py

pause
