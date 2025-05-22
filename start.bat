@echo off
setlocal

echo Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH. Please install Python 3.7 or higher.
    pause
    exit /b 1
)

echo Setting up Python virtual environment...

:: Check if virtual environment exists, if not create it
if not exist .venv_admin (
    echo Creating new virtual environment...
    python -m venv .venv_admin
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to create virtual environment.
        echo Please ensure you have Python installed and in your PATH.
        pause
        exit /b 1
    )
)

:: Activate the virtual environment
call .venv_admin\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo Failed to activate virtual environment.
    echo Please try running this script as administrator.
    pause
    exit /b 1
)

:: Upgrade pip to latest version
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

:: Create necessary directories
if not exist input mkdir input
if not exist output mkdir output

:: Start the application
echo Starting the application...
set FLASK_APP=app.py
set FLASK_ENV=development
set FLASK_DEBUG=1

for /f "tokens=1,2 delims==" %%a in (.env) do (
    if "%%a"=="PORT" set PORT=%%b
)
if not defined PORT set PORT=5000

echo [DocQuery] Starting application on http://127.0.0.1:%PORT% (Debug: True)
flask run --host=0.0.0.0 --port=%PORT% --debug

:: Keep the window open if there's an error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application failed to start. Press any key to exit...
    pause >nul
)

exit /b 0
