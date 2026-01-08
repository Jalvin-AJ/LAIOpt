@echo off
echo Starting LAIOpt Floorplanner...

set PYTHONPATH=.
python -m streamlit run laiopt/frontend/app.py

pause
