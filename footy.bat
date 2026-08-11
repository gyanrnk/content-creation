@echo off
REM Footy Studio — review + approve + upload. Double-click karo.
cd /d "%~dp0"
streamlit run footy_studio.py
pause
