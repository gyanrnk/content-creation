@echo off
cd /d "%~dp0"
env\Scripts\python.exe gemini_build.py prompts > gemini_prompts.txt 2>&1
notepad gemini_prompts.txt
