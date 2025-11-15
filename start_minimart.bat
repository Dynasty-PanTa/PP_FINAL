@echo off
REM Step 1: Create virtual environment if not exists
IF NOT EXIST venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Step 2: Activate venv
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Step 3: Install requirements
echo Installing dependencies...
pip install -r requirements.txt

REM Step 4: Set Flask environment variables
set FLASK_APP=run.py
set FLASK_ENV=development

REM Step 5: Initialize migrations if not exists
IF NOT EXIST migrations (
    echo Initializing migrations...
    flask db init
)

REM Step 6: Run migrations
echo Creating migration...
flask db migrate -m "auto migration"
echo Applying migration...
flask db upgrade

REM Step 7: Create uploads folder
IF NOT EXIST uploads mkdir uploads

REM Step 8: Start Flask server
echo Starting Flask server...
flask run
pause
