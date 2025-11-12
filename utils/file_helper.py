import os
import magic
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from config import Config


def allowed_file(filename: str) -> bool:
    """
    Check if a file has an allowed extension.

    Args:
        filename: The filename to check

    Returns:
        True if the file extension is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def validate_file_content(filepath: str, expected_extension: str) -> bool:
    """
    Validate that a file's content matches its extension using python-magic.

    Args:
        filepath: Path to the file to validate
        expected_extension: The expected file extension (without dot)

    Returns:
        True if file content matches extension, False otherwise
    """
    try:
        mime = magic.Magic(mime=True)
        file_mime = mime.from_file(filepath)

        # Map extensions to expected MIME types
        mime_map = {
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png'
        }

        expected_mime = mime_map.get(expected_extension.lower())
        if not expected_mime:
            return False

        return file_mime == expected_mime

    except Exception:
        # If validation fails, err on the side of caution
        return False


def get_safe_filename(filename: str) -> str:
    """
    Generate a safe filename with timestamp to avoid conflicts.

    Args:
        filename: Original filename

    Returns:
        Safe filename with timestamp prefix
    """
    # Secure the filename
    safe_name = secure_filename(filename)

    # Add timestamp prefix
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(safe_name)

    return f"{timestamp}_{name}{ext}"


def cleanup_old_files(upload_folder: str, retention_days: int) -> int:
    """
    Remove files older than the retention period.

    Args:
        upload_folder: Path to the upload folder
        retention_days: Number of days to retain files

    Returns:
        Number of files deleted
    """
    if not os.path.exists(upload_folder):
        return 0

    cutoff_time = datetime.now() - timedelta(days=retention_days)
    deleted_count = 0

    try:
        for filename in os.listdir(upload_folder):
            filepath = os.path.join(upload_folder, filename)

            # Skip if not a file
            if not os.path.isfile(filepath):
                continue

            # Check file modification time
            file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))

            if file_mtime < cutoff_time:
                try:
                    os.remove(filepath)
                    deleted_count += 1
                except Exception:
                    # Continue even if we can't delete a file
                    pass

    except Exception:
        pass

    return deleted_count


def ensure_upload_folder_exists(upload_folder: str) -> bool:
    """
    Ensure the upload folder exists and is writable.

    Args:
        upload_folder: Path to the upload folder

    Returns:
        True if folder exists and is writable, False otherwise
    """
    try:
        os.makedirs(upload_folder, exist_ok=True)
        return os.access(upload_folder, os.W_OK)
    except Exception:
        return False


def get_file_size_mb(filepath: str) -> float:
    """
    Get file size in megabytes.

    Args:
        filepath: Path to the file

    Returns:
        File size in MB
    """
    try:
        size_bytes = os.path.getsize(filepath)
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0
