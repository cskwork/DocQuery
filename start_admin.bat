@echo off
setlocal

echo Setting up Python virtual environment...

:: Set environment variable to allow conda to bypass permission issues
set CONDA_YES=1

:: Use --system-site-packages to avoid permission issues
python -m venv .venv_admin --system-site-packages

if %ERRORLEVEL% NEQ 0 (
    echo Virtual environment creation failed. Trying with administrator privileges...
    echo Please run the script as administrator if this doesn't work.
    pause
    exit /b 1
)

:: Activate the virtual environment
call .venv_admin\Scripts\activate.bat

if %ERRORLEVEL% NEQ 0 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

:: Install dependencies with --user flag to avoid permission issues
echo Installing dependencies...
pip install --user -r requirements.txt

:: Create directories
if not exist input mkdir input
if not exist output mkdir output

:: Start the application
echo Starting the application...
set FLASK_APP=app.py
set FLASK_ENV=development
flask run

pause
