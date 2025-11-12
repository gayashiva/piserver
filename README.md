# Acres of ice - Network Printer Web App

A web-based printing service for Raspberry Pi that allows users on the local network to upload and print PDF, TXT, JPG, and PNG files through a simple web interface.

## Features

- **Multi-format Support**: Upload PDF, TXT, JPG, JPEG, and PNG files
- **Print Options**: Configure number of copies (1-10) and duplex printing
- **Queue Management**: View current print queue and cancel jobs
- **Print History**: 7-day history with reprint functionality
- **Real-time Updates**: Automatic queue status refresh
- **File Management**: Automatic cleanup of files older than 7 days
- **Responsive Design**: Works on desktop and mobile devices

## Requirements

- Raspberry Pi (or any Linux system with CUPS)
- Python 3.7 or higher
- CUPS print server installed and configured
- Network printer configured in CUPS

## Installation

### 1. Install System Dependencies

```bash
# Update package list
sudo apt update

# Install CUPS and Python dependencies
sudo apt install -y cups python3-pip python3-venv libmagic1

# Ensure CUPS is running
sudo systemctl enable cups
sudo systemctl start cups
```

### 2. Clone or Download the Project

```bash
cd /home/bsurya/Projects
git clone <repository-url> piserver
cd piserver
```

### 3. Create Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure CUPS Printer

Ensure you have a default printer configured in CUPS:

```bash
# List available printers
lpstat -p -d

# If no default printer, set one
lpoptions -d <printer-name>
```

## Running the Application

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Run the Flask application
python app.py
```

The app will be available at `http://printerpi.local:5000/print`

### Production Mode with systemd

For production deployment, use the included systemd service:

1. **Copy the service file:**

```bash
sudo cp deployment/printer-webapp.service /etc/systemd/system/
```

2. **Edit the service file** to match your paths and user:

```bash
sudo nano /etc/systemd/system/printer-webapp.service
```

Update these lines:
- `User=pi` (change to your username)
- `WorkingDirectory=/home/bsurya/Projects/piserver`
- `ExecStart=/home/bsurya/Projects/piserver/venv/bin/python app.py`

3. **Enable and start the service:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable printer-webapp
sudo systemctl start printer-webapp
```

4. **Check status:**

```bash
sudo systemctl status printer-webapp
```

### Production Mode with Nginx (Optional)

For production with reverse proxy on port 80:

1. **Install Nginx:**

```bash
sudo apt install -y nginx
```

2. **Copy the Nginx configuration:**

```bash
sudo cp deployment/nginx.conf /etc/nginx/sites-available/printer
sudo ln -s /etc/nginx/sites-available/printer /etc/nginx/sites-enabled/
```

3. **Remove default site:**

```bash
sudo rm /etc/nginx/sites-enabled/default
```

4. **Test and restart Nginx:**

```bash
sudo nginx -t
sudo systemctl restart nginx
```

Now the app will be available at `http://printerpi.local/print`

## Configuration

Edit `config.py` to customize:

- `UPLOAD_FOLDER`: Where uploaded files are stored
- `MAX_CONTENT_LENGTH`: Maximum file size (default: 20 MB)
- `ALLOWED_EXTENSIONS`: Allowed file types
- `FILE_RETENTION_DAYS`: How long to keep files (default: 7 days)
- `APP_NAME`: Application display name
- `HOSTNAME`: Server hostname

## Usage

### Uploading and Printing Files

1. Open `http://printerpi.local/print` in your browser
2. Click the upload area or drag files to it
3. Select PDF, TXT, JPG, or PNG files (up to 20 MB each)
4. Configure print options:
   - Number of copies (1-10)
   - Duplex (double-sided) printing
5. Click "Print" to submit jobs
6. Monitor the print queue for status updates

### Managing Print Queue

- **View Queue**: See all pending print jobs in real-time
- **Cancel Job**: Click "Cancel" next to any job to remove it from the queue
- **Auto-refresh**: Queue updates automatically every 5 seconds

### Print History

- Click "Show" to expand the history section
- View all print jobs from the last 7 days
- Click "Reprint" to print a file again

## Troubleshooting

### Printer Not Found

```bash
# Check CUPS status
sudo systemctl status cups

# List printers
lpstat -p -d

# Test print
echo "Test" | lp
```

### Permission Errors

```bash
# Add user to lp group (allows printing)
sudo usermod -a -G lp $USER

# Set correct permissions on upload folder (in the repo)
chmod 755 print
```

### Port Already in Use

If port 5000 is in use, edit `app.py` and change:

```python
app.run(host='0.0.0.0', port=5001, debug=False)
```

### Files Not Cleaning Up

Check the background scheduler is running:

```bash
# View application logs
sudo journalctl -u printer-webapp -f
```

### Web Interface Not Accessible

```bash
# Check firewall
sudo ufw status
sudo ufw allow 5000/tcp

# Check if app is running
ps aux | grep python
netstat -tlnp | grep 5000
```

## File Structure

```
piserver/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── tasks/
│   └── prd-pdf-printer.md # Product requirements document
├── templates/
│   └── index.html         # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css      # Styles
│   └── js/
│       └── app.js         # Frontend JavaScript
├── utils/
│   ├── __init__.py
│   ├── cups_helper.py     # CUPS integration
│   ├── db_helper.py       # Database operations
│   └── file_helper.py     # File management
└── deployment/
    ├── printer-webapp.service  # Systemd service
    └── nginx.conf              # Nginx config
```

## Security Notes

- This application has no authentication by design (for easy local network access)
- Only deploy on trusted local networks
- Do not expose to the internet without adding authentication
- File validation is performed to prevent malicious uploads
- Uploaded files are automatically deleted after 7 days

## API Endpoints

- `GET /print` - Main web interface
- `POST /api/upload` - Upload and print files
- `GET /api/queue` - Get current print queue
- `GET /api/history` - Get print history
- `POST /api/cancel/<job_id>` - Cancel a print job
- `POST /api/reprint/<job_id>` - Reprint a previous job
- `GET /api/status` - Get system status

## License

This project is provided as-is for personal use.

## Support

For issues or questions, please check:
- CUPS documentation: `man lp`, `man lpstat`
- Flask documentation: https://flask.palletsprojects.com/
- Project PRD: `tasks/prd-pdf-printer.md`
