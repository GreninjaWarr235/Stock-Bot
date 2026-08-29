@echo off
:: Navigate to the bot root directory
cd /d "%~dp0.."

:: Activate virtual environment and run intraday scanner
call venv\Scripts\activate.bat
python -m alerts.intraday_scanner --force%*

echo Intraday scan finished at %date% %time%
