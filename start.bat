@echo off
setlocal

echo Installing dependencies directly...
pip install docling flask python-dotenv click jinja2

echo Creating necessary directories...
if not exist input mkdir input
if not exist output mkdir output

echo Starting the application...
set FLASK_APP=app.py
set FLASK_ENV=development
python -m flask run

pause
