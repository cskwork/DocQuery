# DocQuery Application Deployment Guide

This guide explains how to deploy the DocQuery application to a production server.

## Prerequisites

- Linux server (Ubuntu 20.04/22.04 recommended)
- Python 3.7 or higher
- pip (Python package manager)
- Git (for cloning the repository)

## Deployment Steps

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd DocQuery
   ```

2. **Make the deployment script executable**:
   ```bash
   chmod +x deploy.sh
   ```

3. **Run the deployment script**:
   ```bash
   sudo ./deploy.sh
   ```
   This script will:
   - Install required dependencies
   - Set up a systemd service
   - Start the application

4. **Access the application**:
   The application will be available at `http://your-server-ip:5000`

## Application Management

- **Check status**: `sudo systemctl status docquery.service`
- **Start service**: `sudo systemctl start docquery.service`
- **Stop service**: `sudo systemctl stop docquery.service`
- **Restart service**: `sudo systemctl restart docquery.service`
- **View logs**: `journalctl -u docquery.service -f`

## Configuration

Environment variables can be set in the systemd service file located at:
`/etc/systemd/system/docquery.service`

After making changes to the service file, run:
```bash
sudo systemctl daemon-reload
sudo systemctl restart docquery.service
```

## Security Considerations

1. **Firewall**: Ensure your firewall allows traffic on port 5000
   ```bash
   sudo ufw allow 5000/tcp
   ```

2. **HTTPS**: For production use, set up Nginx as a reverse proxy with Let's Encrypt SSL certificates.

3. **File Permissions**: The application creates and manages files in the `input`, `output`, and `logs` directories. Ensure these directories have the correct permissions.

## Troubleshooting

- Check application logs: `journalctl -u docquery.service -f`
- Verify service status: `sudo systemctl status docquery.service`
- Check for port conflicts: `sudo lsof -i :5000`
