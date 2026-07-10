@echo off
REM Double-click karo -> latest cloud videos 'videos/' folder me aa jaayengi.
cd /d "%~dp0"
env\Scripts\python.exe get_videos.py
echo.
pause
