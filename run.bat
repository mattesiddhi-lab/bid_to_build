@echo off
echo ========================================================
echo Starting CampusFix - Campus Maintenance Web App
echo ========================================================
cd /d "%~dp0"

IF EXIST ".venv\Scripts\python.exe" (
    echo Using virtual environment...
    .venv\Scripts\python.exe app.py
) ELSE (
    echo Using system Python...
    python app.py
)

pause
