@echo off
REM Build script for SSH Log Collector
REM Creates a standalone Windows executable using PyInstaller

echo Building SSH Log Collector for Windows...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7 or later from https://python.org
    pause
    exit /b 1
)

REM Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: pip is not available
    pause
    exit /b 1
)

REM Install required packages
echo Installing required packages...
pip install paramiko rich click pyyaml keyboard pyinstaller
if %errorlevel% neq 0 (
    echo Error: Failed to install required packages
    pause
    exit /b 1
)

REM Create executable
echo.
echo Creating executable with PyInstaller...
pyinstaller --onefile --console --name "ssh-log-collector" main.py
if %errorlevel% neq 0 (
    echo Error: Failed to create executable
    pause
    exit /b 1
)

REM Copy config file to dist directory
echo.
echo Copying configuration file...
if not exist "dist" mkdir dist
copy "config.yaml" "dist\config.yaml"

echo.
echo Build completed successfully!
echo.
echo Executable location: dist\ssh-log-collector.exe
echo Configuration file: dist\config.yaml
echo.
echo To run the application:
echo 1. Edit dist\config.yaml with your server details
echo 2. Run dist\ssh-log-collector.exe
echo.
pause
