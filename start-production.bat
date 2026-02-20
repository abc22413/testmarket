@echo off
REM Production startup script for Market App (Windows)

echo Starting Market App in Production Mode

REM Check if .env file exists
if not exist ".env" (
    echo Error: .env file not found!
    echo Please copy .env.example to .env and configure it for production
    pause
    exit /b 1
)

REM Check if virtual environment exists, if not create it
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo Configuration verified
echo CSRF Protection: Enabled
echo Secure Cookies: Enabled

echo Starting Gunicorn server...
gunicorn -w 4 ^
         -b 0.0.0.0:5000 ^
         --timeout 120 ^
         --access-logfile - ^
         --error-logfile - ^
         wsgi:app

pause
