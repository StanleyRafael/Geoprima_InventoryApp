@echo off
cd %~dp0
echo Setting up virtual environment..
python -m venv venv

echo Activating virtual environment..
call venv\Scripts\activate

echo Installing dependencies from requirements.txt..
pip install -r requirements.txt

echo Setup complete! You can now proceed to run database migrations.
pause