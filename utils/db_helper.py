import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from contextlib import contextmanager


DATABASE_FILE = 'print_history.db'


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Initialize the database with required tables."""
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS print_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                file_size_mb REAL,
                copies INTEGER DEFAULT 1,
                duplex BOOLEAN DEFAULT 0,
                status TEXT DEFAULT 'pending',
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT
            )
        ''')

        # Create index on job_id for faster lookups
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_job_id ON print_jobs(job_id)
        ''')

        # Create index on submitted_at for cleanup queries
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_submitted_at ON print_jobs(submitted_at)
        ''')


def add_print_job(
    job_id: str,
    filename: str,
    original_filename: str,
    filepath: str,
    file_size_mb: float,
    copies: int = 1,
    duplex: bool = False
) -> int:
    """
    Add a new print job to the database.

    Args:
        job_id: CUPS job ID
        filename: Stored filename (with timestamp)
        original_filename: Original filename from upload
        filepath: Full path to the file
        file_size_mb: File size in megabytes
        copies: Number of copies
        duplex: Whether duplex printing is enabled

    Returns:
        Database record ID
    """
    with get_db_connection() as conn:
        cursor = conn.execute('''
            INSERT INTO print_jobs
            (job_id, filename, original_filename, filepath, file_size_mb, copies, duplex, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (job_id, filename, original_filename, filepath, file_size_mb, copies, duplex))
        return cursor.lastrowid


def update_job_status(job_id: str, status: str, error_message: Optional[str] = None):
    """
    Update the status of a print job.

    Args:
        job_id: CUPS job ID
        status: New status (pending, completed, failed, cancelled)
        error_message: Optional error message if status is failed
    """
    with get_db_connection() as conn:
        if status == 'completed':
            conn.execute('''
                UPDATE print_jobs
                SET status = ?, completed_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
            ''', (status, job_id))
        else:
            conn.execute('''
                UPDATE print_jobs
                SET status = ?, error_message = ?
                WHERE job_id = ?
            ''', (status, error_message, job_id))


def get_recent_jobs(days: int = 7) -> List[Dict]:
    """
    Get print jobs from the last N days.

    Args:
        days: Number of days to look back

    Returns:
        List of job dictionaries
    """
    with get_db_connection() as conn:
        cutoff_date = datetime.now() - timedelta(days=days)
        cursor = conn.execute('''
            SELECT * FROM print_jobs
            WHERE submitted_at > ?
            ORDER BY submitted_at DESC
        ''', (cutoff_date,))

        return [dict(row) for row in cursor.fetchall()]


def get_job_by_id(job_id: str) -> Optional[Dict]:
    """
    Get a specific print job by its CUPS job ID.

    Args:
        job_id: CUPS job ID

    Returns:
        Job dictionary or None if not found
    """
    with get_db_connection() as conn:
        cursor = conn.execute('''
            SELECT * FROM print_jobs
            WHERE job_id = ?
        ''', (job_id,))

        row = cursor.fetchone()
        return dict(row) if row else None


def delete_old_records(days: int = 7) -> int:
    """
    Delete print job records older than N days.

    Args:
        days: Number of days to retain records

    Returns:
        Number of records deleted
    """
    with get_db_connection() as conn:
        cutoff_date = datetime.now() - timedelta(days=days)
        cursor = conn.execute('''
            DELETE FROM print_jobs
            WHERE submitted_at < ?
        ''', (cutoff_date,))

        return cursor.rowcount


def get_pending_jobs() -> List[Dict]:
    """
    Get all pending print jobs.

    Returns:
        List of pending job dictionaries
    """
    with get_db_connection() as conn:
        cursor = conn.execute('''
            SELECT * FROM print_jobs
            WHERE status = 'pending'
            ORDER BY submitted_at ASC
        ''')

        return [dict(row) for row in cursor.fetchall()]
