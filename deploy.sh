#!/bin/bash

# Exit on error
set -e

echo "Starting deployment..."
e
# Create necessary directories if they don't exist
mkdir -p input output logs

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Set environment variables
export FLASK_APP=wsgi.py
export FLASK_ENV=production

# Install Gunicorn in virtual environment
echo "Installing Gunicorn..."
pip install gunicorn

# Create a systemd service file
SERVICE_FILE="/etc/systemd/system/docquery.service"
if [ ! -f "$SERVICE_FILE" ]; then
    echo "Creating systemd service..."
    cat > /tmp/docquery.service <<EOL
[Unit]
Description=DocQuery Application
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin:/usr/local/bin"
ExecStart=$(pwd)/venv/bin/gunicorn --workers 4 --worker-class gevent --bind 0.0.0.0:5000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
EOL

    sudo mv /tmp/docquery.service "$SERVICE_FILE"
    sudo systemctl daemon-reload
    sudo systemctl enable docquery.service
    echo "Systemd service created and enabled."
fi

# Start/Restart the service
echo "Starting DocQuery service..."
sudo systemctl restart docquery.service

echo "Deployment completed successfully!"
echo "The application should now be running on http://your-server-ip:5000"
echo "You can check the status with: sudo systemctl status docquery.service"
