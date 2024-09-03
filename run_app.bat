@echo off
REM Check if the virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate the virtual environment
call venv\Scripts\activate

REM Install required packages
pip install flask pandas openpyxl

REM Run the Flask app
python app.py

pause
