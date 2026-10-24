@echo off
cd /d "%~dp0"
setlocal
if exist "c:\python314\python.exe" (
    set "PYTHON_EXE=c:\python314\python.exe"
) else (
    set "PYTHON_EXE=python"
)
set "DATABASE_URL=sqlite:///automation_scripts.db"
"%PYTHON_EXE%" -m flask --app app run --host 127.0.0.1 --port 5000
