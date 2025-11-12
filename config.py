import os

# Base directory of the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Application configuration"""

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # File upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'print')
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 MB limit
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'jpg', 'jpeg', 'png'}

    # Print settings
    FILE_RETENTION_DAYS = 7

    # Application settings
    APP_NAME = 'Acres of ice'
    HOSTNAME = 'printerpi.local'

    # Queue refresh interval (milliseconds)
    QUEUE_REFRESH_INTERVAL = 5000  # 5 seconds
