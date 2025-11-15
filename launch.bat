@echo off
REM Launch script for Speech-to-Text Dictation Tool
REM
REM This script starts the Python dictation tool with proper error handling
REM and keeps the window open if there's an error.

echo ========================================
echo Speech-to-Text Dictation Tool
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    echo.
    pause
    exit /b 1
)

REM Check if run.py exists
if not exist "run.py" (
    echo ERROR: run.py not found
    echo Please make sure you're running this from the project directory
    echo.
    pause
    exit /b 1
)

echo Starting dictation tool...
echo.
echo Press Ctrl+C to stop the application
echo ========================================
echo.

REM Run the dictation tool using run.py (new entry point)
python run.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR: The application exited with an error
    echo Check the logs above for details
    echo ========================================
    echo.
    pause
)
