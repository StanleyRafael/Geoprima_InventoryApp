@echo off
REM Change to the directory where the batch file resides
cd %~dp0

REM Start the MySQL server via XAMPP
start /B C:\xampp\mysql_start.bat
timeout /t 5 >nul  :: Wait for MySQL to initialize

REM Activate the virtual environment
call .\venv\Scripts\activate

REM Run the Flask application
python app.py

REM Open the localhost URL in the default web browser
start http://127.0.0.1:5000

pause
