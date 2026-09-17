@echo off
REM change working dir to the batch file folder
cd /d "%~dp0"

REM Optional: set Postgres DATABASE_URL (remove or change if using sqlite)
set DATABASE_URL=postgresql://appt_user:strongpassword@localhost:5432/appointmentdb

REM Activate venv (adjust path if your venv folder name differs)
call "%~dp0venv\Scripts\activate.bat"

REM Start Flask app in a new window (so this window returns)
start "" "%~dp0venv\Scripts\python.exe" "%~dp0app.py"

REM Wait a moment and open browser to app
timeout /t 2 >nul
start "" "http://127.0.0.1:5000"
exit /b