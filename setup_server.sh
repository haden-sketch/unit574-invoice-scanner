#!/bin/bash
# Server Setup Script for Gmail Invoice Scanner
# Run this on a fresh Ubuntu/Debian server

set -e

echo "=========================================="
echo "Setting up Gmail Invoice Scanner Server"
echo "Unit 574 - VIN: 3AKJHHDR7KSKE1598"
echo "=========================================="

# Update system
echo "[1/6] Updating system..."
apt-get update && apt-get upgrade -y

# Install Docker
echo "[2/6] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

# Install Docker Compose
echo "[3/6] Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    apt-get install -y docker-compose
fi

# Create application directory
echo "[4/6] Setting up application directory..."
APP_DIR="/opt/invoice-scanner"
mkdir -p $APP_DIR
mkdir -p $APP_DIR/credentials
mkdir -p /var/invoices/unit_574

# Copy files (assumes you've uploaded them)
echo "[5/6] Preparing application..."
cd $APP_DIR

# Create the files if not present
if [ ! -f "scanner.py" ]; then
    echo "Please upload scanner.py, config.py, requirements.txt to $APP_DIR"
fi

# Setup cron for scheduled runs
echo "[6/6] Setting up scheduled scans..."
CRON_CMD="0 */4 * * * cd $APP_DIR && /usr/bin/python3 scanner.py >> /var/log/invoice-scanner.log 2>&1"

# Add to crontab if not exists
(crontab -l 2>/dev/null | grep -v "invoice-scanner" ; echo "$CRON_CMD") | crontab -

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Upload your credentials.json to: $APP_DIR/credentials/"
echo "2. Run: cd $APP_DIR && python3 scanner.py"
echo "3. Complete the OAuth flow in browser"
echo "4. Scanner will auto-run every 4 hours"
echo ""
echo "Logs: /var/log/invoice-scanner.log"
echo "Downloads: /var/invoices/unit_574/"
echo ""

