@echo off
:: Navigate to the bot root directory
cd /d "%~dp0.."

:: Activate virtual environment and run daily scanner
call venv\Scripts\activate.bat
python -m alerts.scanner %*

echo Scan finished at %date% %time%
