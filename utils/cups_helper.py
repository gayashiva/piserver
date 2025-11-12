import subprocess
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple


def submit_print_job(filepath: str, copies: int = 1, duplex: bool = False) -> Tuple[bool, str]:
    """
    Submit a print job to CUPS using the lp command.

    Args:
        filepath: Full path to the PDF file
        copies: Number of copies to print (1-10)
        duplex: Whether to enable duplex (double-sided) printing

    Returns:
        Tuple of (success: bool, message: str)
        If successful, message contains the job ID
        If failed, message contains the error description
    """
    try:
        # Build lp command
        cmd = ['lp']

        # Add number of copies
        if copies > 1:
            cmd.extend(['-n', str(copies)])

        # Add duplex option
        if duplex:
            cmd.extend(['-o', 'sides=two-sided-long-edge'])
        else:
            cmd.extend(['-o', 'sides=one-sided'])

        # Add file to print
        cmd.append(filepath)

        # Execute command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            # Parse job ID from output (format: "request id is printer-123 (1 file(s))")
            match = re.search(r'request id is \S+-(\d+)', result.stdout)
            if match:
                job_id = match.group(1)
                return True, job_id
            else:
                return True, result.stdout.strip()
        else:
            return False, result.stderr.strip() or 'Unknown error submitting print job'

    except subprocess.TimeoutExpired:
        return False, 'Print command timed out'
    except FileNotFoundError:
        return False, 'CUPS lp command not found. Is CUPS installed?'
    except Exception as e:
        return False, f'Error submitting print job: {str(e)}'


def get_print_queue() -> List[Dict[str, str]]:
    """
    Get the current print queue status from CUPS.

    Returns:
        List of dictionaries containing job information:
        - job_id: Job ID number
        - user: User who submitted the job
        - filename: Name of the file
        - size: File size
        - status: Job status (pending, processing, etc.)
    """
    try:
        # Use lpstat -o to get current jobs
        result = subprocess.run(
            ['lpstat', '-o'],
            capture_output=True,
            text=True,
            timeout=5
        )

        jobs = []
        if result.returncode == 0 and result.stdout.strip():
            # Parse lpstat output
            # Format: printer-123 user 1024 Mon Nov 12 10:30:00 2025
            for line in result.stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 5:
                    # Extract job ID from printer-123 format
                    job_match = re.search(r'-(\d+)$', parts[0])
                    job_id = job_match.group(1) if job_match else parts[0]

                    jobs.append({
                        'job_id': job_id,
                        'user': parts[1],
                        'size': parts[2],
                        'status': 'pending',
                        'full_id': parts[0]
                    })

        return jobs

    except subprocess.TimeoutExpired:
        return []
    except FileNotFoundError:
        return []
    except Exception:
        return []


def get_job_status(job_id: str) -> Optional[str]:
    """
    Get the status of a specific print job.

    Args:
        job_id: The job ID to check

    Returns:
        Status string ('pending', 'processing', 'completed', 'failed') or None if not found
    """
    try:
        # Check if job is in current queue
        queue = get_print_queue()
        for job in queue:
            if job['job_id'] == job_id:
                return 'pending'

        # Check completed jobs (last 24 hours)
        result = subprocess.run(
            ['lpstat', '-W', 'completed', '-o'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if f'-{job_id}' in line:
                    return 'completed'

        # If not in queue or completed, might be processing or failed
        # For now, return None to indicate job not found
        return None

    except Exception:
        return None


def cancel_print_job(job_id: str) -> Tuple[bool, str]:
    """
    Cancel a print job.

    Args:
        job_id: The job ID to cancel

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        result = subprocess.run(
            ['cancel', job_id],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            return True, f'Job {job_id} cancelled successfully'
        else:
            return False, result.stderr.strip() or 'Failed to cancel job'

    except subprocess.TimeoutExpired:
        return False, 'Cancel command timed out'
    except FileNotFoundError:
        return False, 'CUPS cancel command not found'
    except Exception as e:
        return False, f'Error cancelling job: {str(e)}'


def check_cups_available() -> bool:
    """
    Check if CUPS is available and responsive.

    Returns:
        True if CUPS is available, False otherwise
    """
    try:
        result = subprocess.run(
            ['lpstat', '-r'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False
