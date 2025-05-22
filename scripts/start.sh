#!/bin/bash

echo "Setting up Python virtual environment..."
python3 -m venv .venv

if [ $? -ne 0 ]; then
    echo "Failed to create virtual environment. Please make sure Python 3 is installed."
    exit 1
fi

source .venv/bin/activate

if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment."
    exit 1
fi

echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Failed to install dependencies."
    exit 1
fi

echo "Creating necessary directories..."
mkdir -p input output

echo "Starting the application..."
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
