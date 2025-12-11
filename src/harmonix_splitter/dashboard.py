"""
Harmonix Web Dashboard
Flask-based web interface for audio stem separation
"""

import os
import uuid
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, url_for
from werkzeug.utils import secure_filename
import threading
import logging

from harmonix_splitter.core.orchestrator import create_orchestrator
from harmonix_splitter.config.settings import Settings

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'harmonix-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize settings
settings = Settings()

# Job storage (in-memory for now)
jobs_storage = {}
jobs_lock = threading.Lock()

# Allowed extensions
ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def process_audio_async(job_id, audio_path, quality, mode, instruments):
    """Background task to process audio"""
    try:
        with jobs_lock:
            jobs_storage[job_id]['status'] = 'processing'
            jobs_storage[job_id]['progress'] = 10
        
        logger.info(f"Job {job_id}: Starting processing")
        
        # Create orchestrator
        orchestrator = create_orchestrator(auto_route=True)
        
        with jobs_lock:
            jobs_storage[job_id]['progress'] = 30
        
        # Process audio
        result = orchestrator.process(
            audio_path=audio_path,
            job_id=job_id,
            quality=quality,
            mode=mode,
            target_instruments=instruments if instruments else None,
            output_dir=settings.output_dir
        )
        
        with jobs_lock:
            jobs_storage[job_id]['progress'] = 90
        
        if result.status == "completed":
            # Prepare stem URLs
            stem_urls = {}
            for stem_name in result.stems.keys():
                stem_file = Path(settings.output_dir) / job_id / f"{Path(audio_path).stem}_{stem_name}.wav"
                if stem_file.exists():
                    stem_urls[stem_name] = f"/download/{job_id}/{stem_name}"
            
            with jobs_lock:
                jobs_storage[job_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'stems': stem_urls,
                    'detected_instruments': result.detected_instruments,
                    'processing_time': result.processing_time,
                    'completed_at': datetime.now().isoformat()
                })
            
            logger.info(f"Job {job_id}: Completed successfully")
        else:
            raise Exception(result.metadata.get('error', 'Unknown error'))
            
    except Exception as e:
        logger.error(f"Job {job_id}: Failed - {e}")
        with jobs_lock:
            jobs_storage[job_id].update({
                'status': 'failed',
                'error': str(e),
                'completed_at': datetime.now().isoformat()
            })


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and start processing"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # Get parameters
        quality = request.form.get('quality', 'balanced')
        mode = request.form.get('mode', 'grouped')
        instruments_str = request.form.get('instruments', '')
        
        # Parse instruments
        instruments = None
        if instruments_str:
            instruments = [i.strip() for i in instruments_str.split(',') if i.strip()]
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        upload_path = Path(settings.upload_dir) / f"{job_id}_{filename}"
        file.save(str(upload_path))
        
        logger.info(f"Job {job_id}: File uploaded - {filename}")
        
        # Create job record
        with jobs_lock:
            jobs_storage[job_id] = {
                'job_id': job_id,
                'filename': filename,
                'status': 'queued',
                'progress': 0,
                'quality': quality,
                'mode': mode,
                'instruments': instruments,
                'created_at': datetime.now().isoformat()
            }
        
        # Start background processing
        thread = threading.Thread(
            target=process_audio_async,
            args=(job_id, upload_path, quality, mode, instruments)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'queued',
            'message': 'File uploaded successfully. Processing started.'
        })
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/status/<job_id>')
def get_status(job_id):
    """Get job status"""
    with jobs_lock:
        job = jobs_storage.get(job_id)
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(job)


@app.route('/download/<job_id>/<stem_name>')
def download_stem(job_id, stem_name):
    """Download a specific stem"""
    with jobs_lock:
        job = jobs_storage.get(job_id)
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    if job['status'] != 'completed':
        return jsonify({'error': 'Job not completed'}), 400
    
    # Find the stem file
    upload_filename = job['filename']
    base_name = Path(upload_filename).stem
    stem_file = Path(settings.output_dir) / job_id / f"{base_name}_{stem_name}.wav"
    
    if not stem_file.exists():
        return jsonify({'error': 'Stem file not found'}), 404
    
    return send_file(
        stem_file,
        as_attachment=True,
        download_name=f"{base_name}_{stem_name}.wav",
        mimetype='audio/wav'
    )


@app.route('/jobs')
def list_jobs():
    """List all jobs"""
    with jobs_lock:
        jobs = list(jobs_storage.values())
    
    # Sort by creation time (newest first)
    jobs.sort(key=lambda x: x['created_at'], reverse=True)
    
    return jsonify({'jobs': jobs[:50]})  # Limit to 50 most recent


@app.route('/delete/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a job and its files"""
    with jobs_lock:
        job = jobs_storage.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Delete output files
        output_dir = Path(settings.output_dir) / job_id
        if output_dir.exists():
            import shutil
            shutil.rmtree(output_dir)
        
        # Delete from storage
        del jobs_storage[job_id]
    
    return jsonify({'message': 'Job deleted successfully'})


if __name__ == '__main__':
    # Create necessary directories
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.output_dir).mkdir(parents=True, exist_ok=True)
    
    # Run the app
    print("=" * 60)
    print("  Harmonix Audio Splitter - Web Dashboard")
    print("=" * 60)
    print(f"\n  🌐 Open your browser to: http://localhost:5000")
    print(f"\n  Press Ctrl+C to stop the server\n")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
