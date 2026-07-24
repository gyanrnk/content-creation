@echo off
cd /d "%~dp0"
env\Scripts\python.exe gemini_build.py build
pause
