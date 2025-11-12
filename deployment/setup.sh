#!/bin/bash

# Setup script for Acres of ice Printer Web App
# Run with: bash deployment/setup.sh

set -e  # Exit on error

echo "================================================"
echo "Acres of ice - Printer Web App Setup"
echo "================================================"
echo ""

# Check if running on Raspberry Pi/Linux
if [ ! -f /etc/os-release ]; then
    echo "Error: This script is designed for Linux systems"
    exit 1
fi

# Get the current user
CURRENT_USER=${SUDO_USER:-$USER}
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Project directory: $PROJECT_DIR"
echo "Current user: $CURRENT_USER"
echo ""

# Install system dependencies
echo "Step 1: Installing system dependencies..."
sudo apt update
sudo apt install -y cups python3-pip python3-venv libmagic1

# Ensure CUPS is running
echo "Step 2: Enabling CUPS..."
sudo systemctl enable cups
sudo systemctl start cups

# Add user to lp group (for printing permissions)
echo "Step 3: Adding user to lp group..."
sudo usermod -a -G lp $CURRENT_USER

# Create virtual environment
echo "Step 4: Creating Python virtual environment..."
cd "$PROJECT_DIR"
python3 -m venv venv

# Activate venv and install dependencies
echo "Step 5: Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Ensure print directory exists and has correct permissions
echo "Step 6: Setting up print directory..."
chmod 755 "$PROJECT_DIR/print"

# Check for default printer
echo ""
echo "Step 7: Checking CUPS printer configuration..."
if lpstat -p -d &>/dev/null; then
    echo "CUPS printers found:"
    lpstat -p -d
else
    echo "WARNING: No printers configured in CUPS!"
    echo "Please configure a printer using the CUPS web interface:"
    echo "  http://localhost:631"
fi

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. For development/testing:"
echo "   cd $PROJECT_DIR"
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "2. For production (systemd service):"
echo "   - Edit deployment/printer-webapp.service"
echo "   - Update User, WorkingDirectory, and ExecStart paths"
echo "   - Run: sudo cp deployment/printer-webapp.service /etc/systemd/system/"
echo "   - Run: sudo systemctl daemon-reload"
echo "   - Run: sudo systemctl enable printer-webapp"
echo "   - Run: sudo systemctl start printer-webapp"
echo ""
echo "3. For production with Nginx:"
echo "   - Install nginx: sudo apt install nginx"
echo "   - Copy config: sudo cp deployment/nginx.conf /etc/nginx/sites-available/printer"
echo "   - Enable site: sudo ln -s /etc/nginx/sites-available/printer /etc/nginx/sites-enabled/"
echo "   - Remove default: sudo rm /etc/nginx/sites-enabled/default"
echo "   - Restart nginx: sudo systemctl restart nginx"
echo ""
echo "Access the app at: http://printerpi.local:5000/print"
echo "                or http://printerpi.local/print (with nginx)"
echo ""
