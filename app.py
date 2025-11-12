import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from config import Config
from utils.file_helper import (
    allowed_file, validate_file_content, get_safe_filename,
    cleanup_old_files, ensure_upload_folder_exists, get_file_size_mb
)
from utils.cups_helper import (
    submit_print_job, get_print_queue, get_job_status,
    cancel_print_job, check_cups_available
)
from utils.db_helper import (
    init_database, add_print_job, update_job_status,
    get_recent_jobs, delete_old_records, get_job_by_id
)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
init_database()

# Ensure upload folder exists
ensure_upload_folder_exists(app.config['UPLOAD_FOLDER'])


def scheduled_cleanup():
    """Background task to clean up old files and records."""
    print(f"[{datetime.now()}] Running scheduled cleanup...")

    # Delete old files
    deleted_files = cleanup_old_files(
        app.config['UPLOAD_FOLDER'],
        app.config['FILE_RETENTION_DAYS']
    )

    # Delete old database records
    deleted_records = delete_old_records(app.config['FILE_RETENTION_DAYS'])

    print(f"Cleanup complete: {deleted_files} files, {deleted_records} records deleted")


# Set up background scheduler for cleanup
scheduler = BackgroundScheduler()
scheduler.add_job(
    scheduled_cleanup,
    'interval',
    hours=6,  # Run every 6 hours
    id='cleanup_job'
)
scheduler.start()


@app.route('/')
def index():
    """Redirect root to /print"""
    return render_template('index.html')


@app.route('/print')
def print_page():
    """Main print interface"""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_files():
    """
    Handle file upload and print job submission.

    Accepts multiple files with print options (copies, duplex).
    Returns job IDs and status for each file.
    """
    # Check if CUPS is available
    if not check_cups_available():
        return jsonify({
            'success': False,
            'error': 'Print server is not available. Please contact administrator.'
        }), 503

    # Check if files were provided
    if 'files' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No files provided'
        }), 400

    files = request.files.getlist('files')

    if not files or all(f.filename == '' for f in files):
        return jsonify({
            'success': False,
            'error': 'No files selected'
        }), 400

    # Get print options
    copies = int(request.form.get('copies', 1))
    duplex = request.form.get('duplex', 'false').lower() == 'true'

    # Validate copies
    if copies < 1 or copies > 10:
        return jsonify({
            'success': False,
            'error': 'Number of copies must be between 1 and 10'
        }), 400

    results = []

    for file in files:
        if file.filename == '':
            continue

        # Check if file type is allowed
        if not allowed_file(file.filename):
            results.append({
                'filename': file.filename,
                'success': False,
                'error': f'File type not allowed. Allowed types: {", ".join(app.config["ALLOWED_EXTENSIONS"])}'
            })
            continue

        # Generate safe filename
        original_filename = file.filename
        safe_name = get_safe_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)

        try:
            # Save file
            file.save(filepath)

            # Validate file content matches extension
            extension = original_filename.rsplit('.', 1)[1].lower()
            if not validate_file_content(filepath, extension):
                os.remove(filepath)
                results.append({
                    'filename': original_filename,
                    'success': False,
                    'error': 'File content does not match extension'
                })
                continue

            # Get file size
            file_size_mb = get_file_size_mb(filepath)

            # Submit print job
            success, message = submit_print_job(filepath, copies, duplex)

            if success:
                job_id = message  # message contains job ID on success

                # Add to database
                add_print_job(
                    job_id=job_id,
                    filename=safe_name,
                    original_filename=original_filename,
                    filepath=filepath,
                    file_size_mb=file_size_mb,
                    copies=copies,
                    duplex=duplex
                )

                results.append({
                    'filename': original_filename,
                    'success': True,
                    'job_id': job_id,
                    'message': f'Print job submitted (Job ID: {job_id})'
                })
            else:
                # Remove file if print submission failed
                os.remove(filepath)
                results.append({
                    'filename': original_filename,
                    'success': False,
                    'error': message
                })

        except Exception as e:
            # Clean up file if it was saved
            if os.path.exists(filepath):
                os.remove(filepath)

            results.append({
                'filename': original_filename,
                'success': False,
                'error': f'Error processing file: {str(e)}'
            })

    # Determine overall success
    overall_success = any(r['success'] for r in results)

    return jsonify({
        'success': overall_success,
        'results': results
    })


@app.route('/api/queue', methods=['GET'])
def get_queue():
    """Get current print queue status."""
    try:
        # Get queue from CUPS
        cups_queue = get_print_queue()

        # Get pending jobs from database for additional info
        db_jobs = {job['job_id']: job for job in get_recent_jobs(1)}

        # Merge information
        queue = []
        for cups_job in cups_queue:
            job_id = cups_job['job_id']
            db_job = db_jobs.get(job_id, {})

            queue.append({
                'job_id': job_id,
                'filename': db_job.get('original_filename', 'Unknown'),
                'copies': db_job.get('copies', 1),
                'duplex': db_job.get('duplex', False),
                'status': cups_job['status'],
                'size': cups_job.get('size', 'Unknown')
            })

        return jsonify({
            'success': True,
            'queue': queue
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting queue: {str(e)}'
        }), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get print history for the last 7 days."""
    try:
        jobs = get_recent_jobs(app.config['FILE_RETENTION_DAYS'])

        # Format jobs for response
        history = []
        for job in jobs:
            history.append({
                'job_id': job['job_id'],
                'filename': job['original_filename'],
                'copies': job['copies'],
                'duplex': bool(job['duplex']),
                'status': job['status'],
                'submitted_at': job['submitted_at'],
                'completed_at': job.get('completed_at'),
                'file_size_mb': round(job['file_size_mb'], 2),
                'error_message': job.get('error_message')
            })

        return jsonify({
            'success': True,
            'history': history
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting history: {str(e)}'
        }), 500


@app.route('/api/cancel/<job_id>', methods=['POST'])
def cancel_job(job_id):
    """Cancel a print job."""
    try:
        success, message = cancel_print_job(job_id)

        if success:
            # Update database
            update_job_status(job_id, 'cancelled')

            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error cancelling job: {str(e)}'
        }), 500


@app.route('/api/reprint/<job_id>', methods=['POST'])
def reprint_job(job_id):
    """Reprint a job from history."""
    try:
        # Get job from database
        job = get_job_by_id(job_id)

        if not job:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404

        # Check if file still exists
        if not os.path.exists(job['filepath']):
            return jsonify({
                'success': False,
                'error': 'File no longer available'
            }), 404

        # Submit new print job
        success, message = submit_print_job(
            job['filepath'],
            job['copies'],
            bool(job['duplex'])
        )

        if success:
            new_job_id = message

            # Add new job to database
            add_print_job(
                job_id=new_job_id,
                filename=job['filename'],
                original_filename=job['original_filename'],
                filepath=job['filepath'],
                file_size_mb=job['file_size_mb'],
                copies=job['copies'],
                duplex=bool(job['duplex'])
            )

            return jsonify({
                'success': True,
                'job_id': new_job_id,
                'message': f'Reprint submitted (Job ID: {new_job_id})'
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error reprinting job: {str(e)}'
        }), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status."""
    try:
        cups_available = check_cups_available()
        upload_folder_ok = ensure_upload_folder_exists(app.config['UPLOAD_FOLDER'])

        return jsonify({
            'success': True,
            'status': {
                'cups_available': cups_available,
                'upload_folder_ok': upload_folder_ok,
                'hostname': app.config['HOSTNAME'],
                'app_name': app.config['APP_NAME']
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting status: {str(e)}'
        }), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    return jsonify({
        'success': False,
        'error': f'File too large. Maximum size is {app.config["MAX_CONTENT_LENGTH"] / (1024*1024):.0f} MB'
    }), 413


if __name__ == '__main__':
    # Run on all interfaces to be accessible via hostname
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
