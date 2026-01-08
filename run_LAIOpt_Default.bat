@echo off
echo Starting LAIOpt Floorplanner...

REM Move to project directory
cd /d "%~dp0"

REM Set Python path
set PYTHONPATH=.

REM Launch Streamlit
python -m streamlit run laiopt/frontend/app.py

pause
