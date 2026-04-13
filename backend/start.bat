@echo off
cd /d "%~dp0"
set NO_COLOR=1
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000 --no-access-log
pause
