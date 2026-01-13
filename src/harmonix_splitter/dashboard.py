"""
Harmonix Web Dashboard
Flask-based web interface for audio stem separation
"""

import os
import uuid
import json
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, url_for, session, redirect, flash
from werkzeug.utils import secure_filename
import threading
import logging

# Optional imports - may not be available in lite deployment
try:
    import librosa
    import numpy as np
    import soundfile as sf
    AUDIO_LIBS_AVAILABLE = True
except ImportError:
    AUDIO_LIBS_AVAILABLE = False
    librosa = None
    np = None
    sf = None

# ML-dependent imports - only load if available
try:
    from harmonix_splitter.core.orchestrator import create_orchestrator
    from harmonix_splitter.analysis.music_analyzer import MusicAnalyzer, estimate_processing_time
    from harmonix_splitter.audio.processor import AudioProcessor
    from harmonix_splitter.audio.lyrics import LyricsExtractor, LyricsResult
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    create_orchestrator = None
    MusicAnalyzer = None
    estimate_processing_time = None
    AudioProcessor = None
    LyricsExtractor = None
    LyricsResult = None

from harmonix_splitter.config.settings import Settings

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'harmonix-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)


@app.context_processor
def inject_user():
    """Inject current_user into all templates"""
    if 'user_id' in session:
        return {
            'current_user': {
                'id': session.get('user_id'),
                'username': session.get('user_id'),
                'name': session.get('user_name'),
                'email': session.get('user_email'),
                'role': session.get('user_role'),
                'plan': session.get('user_plan', 'free'),
                'avatar': session.get('user_avatar'),
                'bio': session.get('user_bio'),
            }
        }
    return {'current_user': None}


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize settings
settings = Settings()

# Define directories
UPLOAD_DIR = settings.get_temp_dir() / "uploads"
OUTPUT_DIR = settings.get_output_dir()

# Create directories
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Job storage (in-memory for now)
jobs_storage = {}
jobs_lock = threading.Lock()

# Allowed extensions
ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac'}


def get_user_output_dir(username: str | None) -> Path:
    """Get user-specific output directory"""
    if username:
        user_dir = OUTPUT_DIR / "users" / username
    else:
        user_dir = OUTPUT_DIR / "anonymous"
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_user_upload_dir(username: str | None) -> Path:
    """Get user-specific upload directory"""
    if username:
        user_dir = UPLOAD_DIR / username
    else:
        user_dir = UPLOAD_DIR / "anonymous"
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def scan_existing_outputs(username: str | None = None):
    """Scan the output directory for existing processed jobs for a specific user"""
    logger.info(f"Scanning for existing outputs for user: {username or 'all'}...")
    
    # Determine which directories to scan
    if username:
        # Only scan user's directory
        user_output_dir = get_user_output_dir(username)
        scan_dirs = [user_output_dir] if user_output_dir.exists() else []
    else:
        # Scan all user directories (for admin or legacy)
        scan_dirs = []
        users_dir = OUTPUT_DIR / "users"
        if users_dir.exists():
            scan_dirs.extend([d for d in users_dir.iterdir() if d.is_dir()])
        anon_dir = OUTPUT_DIR / "anonymous"
        if anon_dir.exists():
            scan_dirs.append(anon_dir)
        # Also scan legacy root output dir for backwards compatibility
        scan_dirs.append(OUTPUT_DIR)
    
    for base_dir in scan_dirs:
        for job_dir in base_dir.iterdir():
            if not job_dir.is_dir() or job_dir.name.startswith('.') or job_dir.name in ['users', 'anonymous']:
                continue
                
            job_id = job_dir.name
            
            # Skip if already in storage AND has stems populated
            if job_id in jobs_storage and jobs_storage[job_id].get('stems'):
                continue
            
            # Find stem files (exclude pitch-shifted cache files and lyrics files)
            # Look for both MP3 and WAV files
            stem_files = [f for f in job_dir.glob("*.mp3") 
                          if '_pitch' not in f.stem 
                          and '_lyrics' not in f.stem
                          and not f.stem.startswith('pitch')]
            
            # Also include WAV files
            wav_files = [f for f in job_dir.glob("*.wav") 
                          if '_pitch' not in f.stem 
                          and '_lyrics' not in f.stem
                          and not f.stem.startswith('pitch')]
            stem_files.extend(wav_files)
            
            if not stem_files:
                continue
            
            # Valid stem types - include all possible Demucs output stems + original for URL downloads
            valid_stem_types = {'vocals', 'drums', 'bass', 'guitar', 'piano', 'other', 'instrumental', 'synth', 'strings', 'melody', 'accompaniment', 'percussion', 'lead', 'background', 'original'}
            
            # Extract base name and stems from files
            stems = {}
            base_name = None
            
            for stem_file in stem_files:
                filename = stem_file.stem  # e.g., "Aal_Ein_Molayeten_vocals"
                parts = filename.rsplit('_', 1)
                if len(parts) == 2:
                    name, stem_type = parts
                    # Only add valid stem types
                    if stem_type.lower() in valid_stem_types:
                        if base_name is None:
                            base_name = name
                        stems[stem_type] = f"/download/{job_id}/{stem_type}"
            
            if stems and base_name:
                # Get modification time
                mod_time = datetime.fromtimestamp(job_dir.stat().st_mtime)
                
                # Check if lyrics exist
                lyrics_files = list(job_dir.glob("*_lyrics.json"))
                has_lyrics = len(lyrics_files) > 0
                
                # Update existing job or create new record
                if job_id in jobs_storage:
                    # Update stems for existing job with empty stems
                    jobs_storage[job_id]['stems'] = stems
                    jobs_storage[job_id]['has_lyrics'] = has_lyrics
                    logger.info(f"Updated job: {job_id} ({base_name}) with {len(stems)} stems")
                else:
                    # Determine owner from directory structure
                    owner = None
                    if 'users' in str(job_dir):
                        # Extract username from path like /outputs/users/username/job_id
                        parts = str(job_dir).split('/users/')
                        if len(parts) > 1:
                            owner = parts[1].split('/')[0]
                    elif 'anonymous' in str(job_dir):
                        owner = None
                    
                    # Create new job record
                    jobs_storage[job_id] = {
                        'job_id': job_id,
                        'filename': f"{base_name}.wav",
                        'display_name': base_name,
                        'status': 'completed',
                        'progress': 100,
                        'stems': stems,
                        'has_lyrics': has_lyrics,
                        'user': owner,
                        'created_at': mod_time.isoformat(),
                        'completed_at': mod_time.isoformat()
                    }
                    logger.info(f"Found existing job: {job_id} ({base_name}) for user: {owner or 'unknown'} with {len(stems)} stems")
    
    logger.info(f"Scan complete. Found {len(jobs_storage)} existing jobs.")


def allowed_file(filename):
    """Check if file extension is allowed"""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def process_audio_async(job_id, audio_path, quality, mode, instruments, display_name=None, username=None):
    """Background task to process audio"""
    try:
        # Get user-specific output directory
        user_output_dir = get_user_output_dir(username)
        
        with jobs_lock:
            jobs_storage[job_id]['status'] = 'analyzing'
            jobs_storage[job_id]['progress'] = 5
            jobs_storage[job_id]['stage'] = 'Analyzing audio...'
        
        logger.info(f"Job {job_id}: Starting analysis")
        
        # Step 1: Analyze audio for tempo/key
        try:
            analyzer = MusicAnalyzer()
            analysis = analyzer.analyze(Path(audio_path))
            
            music_info = {
                'tempo': {
                    'bpm': analysis.tempo.bpm,
                    'confidence': analysis.tempo.bpm_confidence
                },
                'key': {
                    'key': analysis.key.key,
                    'scale': analysis.key.scale,
                    'confidence': analysis.key.confidence,
                    'camelot': analyzer.get_camelot_wheel(analysis.key.key, analysis.key.scale)
                },
                'duration': analysis.duration
            }
            
            with jobs_lock:
                jobs_storage[job_id]['music_info'] = music_info
                jobs_storage[job_id]['progress'] = 15
                jobs_storage[job_id]['stage'] = f'Detected: {analysis.tempo.bpm} BPM, {analysis.key.key} {analysis.key.scale}'
            
            logger.info(f"Job {job_id}: Detected {analysis.tempo.bpm} BPM, {analysis.key.key} {analysis.key.scale}")
        except Exception as e:
            logger.warning(f"Job {job_id}: Music analysis failed - {e}")
        
        # Step 2: Start separation
        with jobs_lock:
            jobs_storage[job_id]['status'] = 'processing'
            jobs_storage[job_id]['progress'] = 20
            jobs_storage[job_id]['stage'] = f'Separating stems ({quality} quality)...'
        
        logger.info(f"Job {job_id}: Starting {quality} quality separation")
        
        # Create orchestrator
        orchestrator = create_orchestrator(auto_route=True)
        
        with jobs_lock:
            jobs_storage[job_id]['progress'] = 30
        
        # Process audio - use user-specific output directory
        result = orchestrator.process(
            audio_path=audio_path,
            job_id=job_id,
            quality=quality,
            mode=mode,
            target_instruments=instruments if instruments else None,
            output_dir=str(user_output_dir),
            custom_name=display_name
        )
        
        with jobs_lock:
            jobs_storage[job_id]['progress'] = 90
            jobs_storage[job_id]['stage'] = 'Finalizing...'
        
        if result.status == "completed":
            # Prepare stem URLs - use display_name if provided, else original filename
            base_name = display_name if display_name else Path(audio_path).stem
            stem_urls = {}
            for stem_name in result.stems.keys():
                # Check for MP3 first, then WAV
                stem_file = user_output_dir / job_id / f"{base_name}_{stem_name}.mp3"
                if not stem_file.exists():
                    stem_file = user_output_dir / job_id / f"{base_name}_{stem_name}.wav"
                if stem_file.exists():
                    stem_urls[stem_name] = f"/download/{job_id}/{stem_name}"
            
            # If no stems found with display_name, try original filename
            if not stem_urls:
                original_base = Path(audio_path).stem
                for stem_name in result.stems.keys():
                    stem_file = user_output_dir / job_id / f"{original_base}_{stem_name}.mp3"
                    if not stem_file.exists():
                        stem_file = user_output_dir / job_id / f"{original_base}_{stem_name}.wav"
                    if stem_file.exists():
                        stem_urls[stem_name] = f"/download/{job_id}/{stem_name}"
            
            with jobs_lock:
                jobs_storage[job_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'stage': 'Complete',
                    'stems': stem_urls,
                    'detected_instruments': result.detected_instruments,
                    'processing_time': result.processing_time,
                    'completed_at': datetime.now().isoformat()
                })
            
            logger.info(f"Job {job_id}: Completed successfully in {result.processing_time:.1f}s")
        else:
            raise Exception(result.metadata.get('error', 'Unknown error'))
            
    except Exception as e:
        logger.error(f"Job {job_id}: Failed - {e}")
        with jobs_lock:
            jobs_storage[job_id].update({
                'status': 'failed',
                'error': str(e),
                'stage': 'Failed',
                'completed_at': datetime.now().isoformat()
            })


@app.route('/')
def landing():
    """Landing page / marketing homepage"""
    return render_template('landing.html')


@app.route('/robots.txt')
def robots():
    """Serve robots.txt for search engines"""
    return send_from_directory(app.static_folder, 'robots.txt', mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap():
    """Generate dynamic sitemap for SEO"""
    from datetime import datetime
    
    pages = [
        {'url': '/', 'priority': '1.0', 'changefreq': 'weekly'},
        {'url': '/features', 'priority': '0.8', 'changefreq': 'monthly'},
        {'url': '/pricing', 'priority': '0.8', 'changefreq': 'monthly'},
        {'url': '/tutorials', 'priority': '0.7', 'changefreq': 'weekly'},
        {'url': '/docs', 'priority': '0.7', 'changefreq': 'monthly'},
        {'url': '/about', 'priority': '0.6', 'changefreq': 'monthly'},
        {'url': '/contact', 'priority': '0.5', 'changefreq': 'monthly'},
        {'url': '/blog', 'priority': '0.7', 'changefreq': 'daily'},
        {'url': '/login', 'priority': '0.5', 'changefreq': 'yearly'},
        {'url': '/register', 'priority': '0.6', 'changefreq': 'yearly'},
        {'url': '/tuner', 'priority': '0.6', 'changefreq': 'monthly'},
        {'url': '/transposer', 'priority': '0.6', 'changefreq': 'monthly'},
    ]
    
    base_url = request.url_root.rstrip('/')
    if 'localhost' in base_url or '127.0.0.1' in base_url:
        base_url = 'https://harmonix.audio'
    
    lastmod = datetime.now().strftime('%Y-%m-%d')
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for page in pages:
        xml += '  <url>\n'
        xml += f'    <loc>{base_url}{page["url"]}</loc>\n'
        xml += f'    <lastmod>{lastmod}</lastmod>\n'
        xml += f'    <changefreq>{page["changefreq"]}</changefreq>\n'
        xml += f'    <priority>{page["priority"]}</priority>\n'
        xml += '  </url>\n'
    
    xml += '</urlset>'
    
    return Response(xml, mimetype='application/xml')


# ==================== HEALTH CHECK ====================

@app.route('/health')
def health_check():
    """Health check endpoint for container orchestration and load balancers"""
    return jsonify({
        "status": "healthy",
        "service": "harmonix-dashboard",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.route('/dashboard')
@app.route('/app')
@app.route('/studio')
def index():
    """Main dashboard / studio page"""
    return render_template('dashboard.html')


# ==================== AUTHENTICATION ROUTES ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    from harmonix_splitter.auth import authenticate_user
    
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        # Debug logging
        import logging
        logging.info(f"Login attempt - email: '{email}', password length: {len(password)}")
        
        user = authenticate_user(email, password)
        logging.info(f"Auth result: {user is not None}")
        
        if user:
            session['user_id'] = user.get('username')
            session['user_email'] = user.get('email')
            session['user_name'] = user.get('name')
            session['user_role'] = user.get('role')
            session['user_plan'] = user.get('plan', 'free')
            session['user_avatar'] = user.get('avatar')
            session['user_bio'] = user.get('bio')
            
            if remember:
                session.permanent = True
            
            flash('Welcome back!', 'success')
            
            # Redirect admin to admin dashboard
            if user.get('role') == 'admin':
                return redirect('/admin')
            return redirect('/dashboard')
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    from harmonix_splitter.auth import create_user, get_user_by_email
    
    if request.method == 'POST':
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('register.html')
        
        if get_user_by_email(email):
            flash('An account with this email already exists', 'error')
            return render_template('register.html')
        
        try:
            # Use email as username, with name as display name
            username = email.split('@')[0] + '_' + secrets.token_hex(4)
            user = create_user(username, email, password, name)
            if user:
                session['user_id'] = username
                session['user_email'] = email
                session['user_name'] = name
                session['user_role'] = user.get('role', 'user')
                session['user_plan'] = user.get('plan', 'free')
                
                flash('Account created successfully!', 'success')
                return redirect('/dashboard')
        except Exception as e:
            flash(f'Failed to create account: {str(e)}', 'error')
    
    return render_template('register.html')


@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect('/')


@app.route('/admin')
def admin_dashboard():
    """Admin dashboard"""
    from harmonix_splitter.auth import get_all_users, get_all_contacts, get_admin_stats
    
    # Check if user is logged in and is admin
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect('/login')
    
    users = get_all_users()
    contacts = get_all_contacts()
    stats = get_admin_stats()
    
    return render_template('admin.html', 
                          users=users, 
                          contacts=contacts,
                          stats=stats,
                          current_user={
                              'name': session.get('user_name'),
                              'email': session.get('user_email'),
                              'role': session.get('user_role')
                          })


@app.route('/admin/users', methods=['GET', 'POST', 'PUT', 'DELETE'])
def admin_users():
    """Admin user management API"""
    from harmonix_splitter.auth import (get_all_users, get_user_by_id, create_user, 
                                        update_user, delete_user)
    
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        user_id = request.args.get('id')
        if user_id:
            user = get_user_by_id(user_id)
            if user:
                return jsonify(user)
            return jsonify({'error': 'User not found'}), 404
        return jsonify(get_all_users())
    
    elif request.method == 'POST':
        data = request.get_json()
        try:
            # Generate a username from email
            email = data.get('email')
            username = email.split('@')[0] + '_' + secrets.token_hex(4)
            user = create_user(
                username,
                email,
                data.get('password'),
                data.get('name', ''),
                data.get('role', 'user')
            )
            return jsonify({'success': True, 'user': user})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    elif request.method == 'PUT':
        data = request.get_json()
        user_id = data.get('id')
        updates = {k: v for k, v in data.items() if k != 'id'}
        result = update_user(user_id, updates)
        if result:
            return jsonify({'success': True})
        return jsonify({'error': 'Failed to update user'}), 400
    
    elif request.method == 'DELETE':
        user_id = request.args.get('id')
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        if delete_user(user_id):
            return jsonify({'success': True})
        return jsonify({'error': 'Failed to delete user'}), 400
    
    return jsonify({'error': 'Method not allowed'}), 405


@app.route('/admin/users/add', methods=['POST'])
def admin_add_user():
    """Add new user from admin panel"""
    from harmonix_splitter.auth import create_user
    
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        user = create_user(
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password'),
            name=data.get('name', ''),
            role=data.get('role', 'user')
        )
        # Set plan if specified
        if data.get('plan'):
            from harmonix_splitter.auth import upgrade_plan
            upgrade_plan(data.get('username'), data.get('plan'))
        return jsonify({'success': True, 'user': user})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/admin/users/update', methods=['POST'])
def admin_update_user():
    """Update user from admin panel"""
    from harmonix_splitter.auth import update_user
    
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        username = data.get('username')
        updates = {}
        
        if 'name' in data:
            updates['name'] = data['name']
        if 'email' in data:
            updates['email'] = data['email']
        if 'role' in data:
            updates['role'] = data['role']
        if 'plan' in data:
            updates['plan'] = data['plan']
        if 'is_active' in data:
            updates['is_active'] = data['is_active']
        if 'password' in data and data['password']:
            from harmonix_splitter.auth import hash_password
            pw_hash, salt = hash_password(data['password'])
            updates['password_hash'] = pw_hash
            updates['salt'] = salt
        
        result = update_user(username, updates)
        if result:
            return jsonify({'success': True})
        return jsonify({'error': 'Failed to update user'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/admin/users/delete/<username>', methods=['DELETE'])
def admin_delete_user(username):
    """Delete user from admin panel"""
    from harmonix_splitter.auth import delete_user
    
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if username == 'admin':
        return jsonify({'error': 'Cannot delete admin user'}), 400
    
    if delete_user(username):
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to delete user'}), 400


@app.route('/admin/contacts', methods=['GET', 'POST'])
def admin_contacts():
    """Admin contact management API"""
    from harmonix_splitter.auth import get_all_contacts, get_contact_by_id, reply_to_contact
    
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        contact_id = request.args.get('id')
        if contact_id:
            contact = get_contact_by_id(contact_id)
            if contact:
                return jsonify(contact)
            return jsonify({'error': 'Contact not found'}), 404
        return jsonify(get_all_contacts())
    
    elif request.method == 'POST':
        data = request.get_json()
        contact_id = data.get('id')
        reply_message = data.get('reply')
        if reply_to_contact(contact_id, reply_message):
            return jsonify({'success': True})
        return jsonify({'error': 'Failed to reply'}), 400
    
    return jsonify({'error': 'Method not allowed'}), 405


@app.route('/admin/contacts/reply/<contact_id>', methods=['POST'])
def admin_reply_contact(contact_id):
    """Reply to contact message"""
    from harmonix_splitter.auth import reply_to_contact
    
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    reply_message = data.get('reply')
    
    if reply_to_contact(contact_id, reply_message):
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to reply'}), 400


@app.route('/admin/contacts/delete/<contact_id>', methods=['DELETE'])
def admin_delete_contact(contact_id):
    """Delete contact message"""
    from harmonix_splitter.auth import delete_contact
    
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if delete_contact(contact_id):
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to delete contact'}), 400


@app.route('/admin/backup', methods=['POST'])
def admin_backup():
    """Create and download backup ZIP file"""
    import zipfile
    import io
    from datetime import datetime
    
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json() or {}
    backup_type = data.get('type', 'full')
    
    try:
        # Create ZIP in memory
        memory_file = io.BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add users.json
            users_file = DATA_DIR / 'users.json'
            if users_file.exists():
                zf.write(users_file, 'data/users.json')
            
            # Add config
            config_dir = BASE_DIR.parent.parent.parent / 'config'
            if config_dir.exists():
                for f in config_dir.glob('*'):
                    if f.is_file():
                        zf.write(f, f'config/{f.name}')
            
            if backup_type == 'full':
                # Add user outputs (audio files)
                outputs_dir = DATA_DIR / 'outputs' / 'users'
                if outputs_dir.exists():
                    for user_dir in outputs_dir.iterdir():
                        if user_dir.is_dir():
                            for job_dir in user_dir.iterdir():
                                if job_dir.is_dir():
                                    for f in job_dir.glob('*'):
                                        if f.is_file():
                                            arcname = f'data/outputs/users/{user_dir.name}/{job_dir.name}/{f.name}'
                                            zf.write(f, arcname)
                
                # Add recent logs (last 5)
                logs_dir = BASE_DIR.parent.parent.parent / 'logs'
                if logs_dir.exists():
                    log_files = sorted(logs_dir.glob('*.log'), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
                    for log_file in log_files:
                        zf.write(log_file, f'logs/{log_file.name}')
            
            # Add backup metadata
            metadata = {
                'backup_type': backup_type,
                'created_at': datetime.now().isoformat(),
                'version': '1.1.0',
                'created_by': session.get('user_email', 'admin')
            }
            zf.writestr('backup_info.json', json.dumps(metadata, indent=2))
        
        memory_file.seek(0)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'harmonix_{backup_type}_backup_{timestamp}.zip'
        
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Backup error: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== STATIC PAGES ====================

@app.route('/features')
def features():
    """Features page"""
    return render_template('features.html')


@app.route('/pricing')
def pricing():
    """Pricing page"""
    return render_template('pricing.html')


@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    from harmonix_splitter.auth import add_contact_submission
    
    if request.method == 'POST':
        try:
            result = add_contact_submission(
                name=request.form.get('name', ''),
                email=request.form.get('email', ''),
                subject=request.form.get('subject', ''),
                message=request.form.get('message', ''),
                category=request.form.get('category', 'general')
            )
            if result:
                flash('Thank you for your message! We will get back to you soon.', 'success')
                return redirect('/contact')
        except Exception as e:
            flash(f'Failed to submit message: {str(e)}', 'error')
    
    return render_template('contact.html')


@app.route('/docs')
@app.route('/documentation')
def docs():
    """Documentation page"""
    return render_template('docs.html')


@app.route('/tutorials')
def tutorials():
    """Tutorials page"""
    return render_template('tutorials.html')


@app.route('/blog')
def blog():
    """Blog page"""
    return render_template('blog.html')


@app.route('/community')
def community():
    """Community page"""
    return render_template('community.html')


@app.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')


@app.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html')


# ==================== MUSICIAN CORNER ====================

@app.route('/tuner')
def tuner():
    """Instrument tuner page"""
    return render_template('tuner.html')


@app.route('/transposer')
def transposer():
    """Chord transposer page"""
    return render_template('transposer.html')


@app.route('/account')
def account():
    """User account page"""
    if 'user_id' not in session:
        return redirect('/login')
    
    # Get user stats from auth module
    from harmonix_splitter.auth import get_user_stats, get_user
    
    username = session.get('user_id')
    if not username:
        return redirect('/login')
    user_stats = get_user_stats(username)
    user_data = get_user(username)
    
    # Include avatar and bio from user_data (or session fallback)
    return render_template('account.html',
                          current_user={
                              'id': session.get('user_id'),
                              'username': username,
                              'name': session.get('user_name'),
                              'email': session.get('user_email'),
                              'role': session.get('user_role'),
                              'plan': session.get('user_plan', 'free'),
                              'avatar': user_data.get('avatar') if user_data else session.get('user_avatar'),
                              'bio': user_data.get('bio', '') if user_data else session.get('user_bio', ''),
                          },
                          user_stats=user_stats)


@app.route('/account/update', methods=['POST'])
def update_account():
    """Update user profile information"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    from harmonix_splitter.auth import update_user
    
    username = session.get('user_id')
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    # Build updates dict from allowed fields
    updates = {}
    if 'name' in data:
        updates['name'] = data['name'].strip()
    if 'email' in data:
        updates['email'] = data['email'].strip()
    if 'bio' in data:
        updates['bio'] = data['bio'].strip() if data['bio'] else ''
    
    if not updates:
        return jsonify({'success': False, 'error': 'No valid fields to update'}), 400
    
    result = update_user(username, updates)
    
    if result:
        # Update session with new values
        if 'name' in updates:
            session['user_name'] = updates['name']
        if 'email' in updates:
            session['user_email'] = updates['email']
        if 'bio' in updates:
            session['user_bio'] = updates['bio']
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
    else:
        return jsonify({'success': False, 'error': 'Failed to update profile'}), 500


@app.route('/account/upload-avatar', methods=['POST'])
def upload_avatar():
    """Upload and update user avatar"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    from harmonix_splitter.auth import update_user
    from PIL import Image
    import uuid
    import io
    
    username = session.get('user_id')
    
    if 'avatar' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['avatar']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Check file extension (default to jpg for cropped images from frontend)
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    file_ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'jpg'
    
    if file_ext not in allowed_extensions:
        return jsonify({'success': False, 'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP'}), 400
    
    # Create avatars directory if it doesn't exist
    avatars_dir = Path(__file__).parent.parent.parent / 'data' / 'avatars'
    avatars_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename (always save as jpg for consistency)
    unique_filename = f"{username}_{uuid.uuid4().hex[:8]}.jpg"
    avatar_path = avatars_dir / unique_filename
    
    try:
        # Delete old avatar if exists
        from harmonix_splitter.auth import load_users
        users = load_users()
        if username in users and 'avatar' in users[username]:
            old_avatar = avatars_dir / users[username]['avatar'].split('/')[-1]
            if old_avatar.exists():
                old_avatar.unlink()
        
        # Open image with PIL and crop to square
        img = Image.open(file)
        
        # Convert to RGB if necessary (for PNG with transparency)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Crop to square (center crop)
        width, height = img.size
        min_dimension = min(width, height)
        left = (width - min_dimension) // 2
        top = (height - min_dimension) // 2
        right = left + min_dimension
        bottom = top + min_dimension
        img = img.crop((left, top, right, bottom))
        
        # Resize to standard avatar size (256x256)
        img = img.resize((256, 256), Image.LANCZOS)
        
        # Save the cropped image
        img.save(str(avatar_path), quality=90)
        
        # Update user record
        avatar_url = f'/avatars/{unique_filename}'
        result = update_user(username, {'avatar': avatar_url})
        
        if result:
            session['user_avatar'] = avatar_url
            return jsonify({'success': True, 'message': 'Avatar updated successfully', 'avatar_url': avatar_url})
        else:
            return jsonify({'success': False, 'error': 'Failed to update user record'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/avatars/<filename>')
def serve_avatar(filename):
    """Serve avatar files"""
    avatars_dir = Path(__file__).parent.parent.parent / 'data' / 'avatars'
    return send_from_directory(str(avatars_dir), filename)


@app.route('/account/change-password', methods=['POST'])
def change_user_password():
    """Change user password"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    from harmonix_splitter.auth import change_password
    
    username = session.get('user_id')
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')
    
    if not current_password or not new_password:
        return jsonify({'success': False, 'error': 'Current and new passwords are required'}), 400
    
    if new_password != confirm_password:
        return jsonify({'success': False, 'error': 'New passwords do not match'}), 400
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
    
    result = change_password(username, current_password, new_password)
    
    if result:
        return jsonify({'success': True, 'message': 'Password changed successfully'})
    else:
        return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400


@app.route('/account/delete', methods=['POST'])
def delete_account():
    """Delete user account"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    from harmonix_splitter.auth import delete_user
    
    username = session.get('user_id')
    data = request.get_json()
    
    # Require password confirmation
    password = data.get('password', '') if data else ''
    
    if not password:
        return jsonify({'success': False, 'error': 'Password confirmation required'}), 400
    
    # Verify password first
    from harmonix_splitter.auth import authenticate_user
    if not authenticate_user(username, password):
        return jsonify({'success': False, 'error': 'Incorrect password'}), 400
    
    result = delete_user(username)
    
    if result:
        session.clear()
        return jsonify({'success': True, 'message': 'Account deleted successfully'})
    else:
        return jsonify({'success': False, 'error': 'Cannot delete this account'}), 400


# ==================== API ROUTES ====================

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
        
        # ===== PLAN LIMIT ENFORCEMENT =====
        from harmonix_splitter.auth import check_usage_limit, get_plan, increment_song_usage
        
        username = session.get('user_id')
        user_plan = session.get('user_plan', 'free')
        plan_info = get_plan(user_plan)
        
        if username:
            # Check usage limit
            usage_check = check_usage_limit(username)
            if not usage_check['allowed']:
                return jsonify({
                    'error': f"Monthly limit reached! You've processed {usage_check['used']} of {usage_check['limit']} songs this month.",
                    'limit_reached': True,
                    'upgrade_url': '/#pricing'
                }), 403
        
        # Get parameters
        quality = request.form.get('quality', 'balanced')
        mode = request.form.get('mode', 'grouped')
        instruments_str = request.form.get('instruments', '')
        output_name = request.form.get('output_name', '').strip()
        
        # Parse instruments and validate against plan
        instruments = None
        if instruments_str:
            requested_instruments = [i.strip() for i in instruments_str.split(',') if i.strip()]
            # Filter to allowed stems for the user's plan
            allowed_stems = plan_info.get('stem_types', ['vocals', 'drums', 'bass', 'other'])
            instruments = [i for i in requested_instruments if i in allowed_stems]
            
            # Warn if some stems were filtered
            filtered_out = set(requested_instruments) - set(instruments)
            if filtered_out:
                logger.warning(f"User {username} requested stems not in their plan: {filtered_out}")
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded file with proper extension
        # Extract extension BEFORE secure_filename to preserve the dot
        original_filename = file.filename or 'unknown.wav'
        file_ext = Path(original_filename).suffix.lower()  # e.g., ".mp3"
        base_name = secure_filename(Path(original_filename).stem)  # secure only the name part
        
        # Use custom output name if provided, otherwise use original filename
        display_name = secure_filename(output_name) if output_name else base_name
        
        # Create the upload path in user-specific directory
        user_upload_dir = get_user_upload_dir(username)
        upload_path = user_upload_dir / f"{job_id}_{base_name}{file_ext}"
        file.save(str(upload_path))
        
        logger.info(f"Job {job_id}: File uploaded by {username or 'anonymous'} - {base_name}{file_ext} (output as: {display_name})")
        
        # Increment usage counter for logged-in users
        if username:
            increment_song_usage(username)
        
        # Create job record
        with jobs_lock:
            jobs_storage[job_id] = {
                'job_id': job_id,
                'filename': f"{base_name}{file_ext}",
                'display_name': display_name,
                'status': 'queued',
                'progress': 0,
                'quality': quality,
                'mode': mode,
                'instruments': instruments,
                'user': username,
                'user_plan': user_plan,
                'created_at': datetime.now().isoformat()
            }
        
        # Start background processing with username for user-specific output
        thread = threading.Thread(
            target=process_audio_async,
            args=(job_id, upload_path, quality, mode, instruments, display_name, username)
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


@app.route('/api/convert-to-midi', methods=['POST'])
def convert_to_midi():
    """Convert audio file to MIDI using Basic Pitch"""
    try:
        from basic_pitch.inference import predict, Model
        from basic_pitch import ICASSP_2022_MODEL_PATH
        import os
        import yt_dlp
        
        username = session.get('user_id', 'anonymous')
        
        # Get audio file from upload, stem URL, or YouTube URL
        audio_file = request.files.get('audio')
        stem_url = request.form.get('stem_url')
        youtube_url = request.form.get('youtube_url')
        
        temp_audio_path = None
        original_name = 'audio'
        cleanup_temp = False
        
        if audio_file:
            # Save uploaded file temporarily
            original_name = Path(audio_file.filename).stem
            temp_audio_path = UPLOAD_DIR / f"midi_temp_{uuid.uuid4().hex}{Path(audio_file.filename).suffix}"
            audio_file.save(str(temp_audio_path))
            cleanup_temp = True
        elif youtube_url:
            # Download from YouTube/URL
            logger.info(f"Downloading from URL for MIDI conversion: {youtube_url}")
            
            # Create temp file for download
            temp_filename = f"midi_url_{uuid.uuid4().hex}"
            temp_audio_path = UPLOAD_DIR / temp_filename
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(temp_audio_path),
                'quiet': True,
                'no_warnings': True,
                'extract_audio': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(youtube_url, download=True)
                    original_name = info.get('title', 'audio')
                    # Clean filename
                    original_name = "".join(c for c in original_name if c.isalnum() or c in (' ', '-', '_')).strip()
                    
                # Find the downloaded file (might have .mp3 extension added)
                for ext in ['.mp3', '.m4a', '.webm', '.opus', '']:
                    check_path = Path(str(temp_audio_path) + ext)
                    if check_path.exists():
                        temp_audio_path = check_path
                        break
                        
                if not temp_audio_path.exists():
                    return jsonify({'success': False, 'error': 'Failed to download audio from URL'}), 500
                    
                cleanup_temp = True
                logger.info(f"Downloaded: {original_name}")
                
            except Exception as e:
                logger.error(f"URL download failed: {e}")
                return jsonify({'success': False, 'error': f'Failed to download: {str(e)}'}), 500
                
        elif stem_url:
            # Use existing stem file
            # stem_url is like /output/job_id/stem.mp3
            stem_path = Path(__file__).parent.parent.parent / stem_url.lstrip('/')
            if stem_path.exists():
                temp_audio_path = stem_path
                original_name = stem_path.stem
            else:
                return jsonify({'success': False, 'error': 'Stem file not found'}), 404
        else:
            return jsonify({'success': False, 'error': 'No audio file provided'}), 400
        
        # Create output directory for MIDI files - unified under user folder
        midi_output_dir = Path(__file__).parent.parent.parent / 'data' / 'outputs' / 'users' / username / 'midi'
        midi_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        midi_filename = f"{original_name}_{uuid.uuid4().hex[:8]}.mid"
        midi_path = midi_output_dir / midi_filename
        
        # Use ONNX model for better compatibility with Python 3.13
        onnx_model_path = os.path.join(os.path.dirname(ICASSP_2022_MODEL_PATH), 'nmp.onnx')
        
        # Convert to MIDI using Basic Pitch with ONNX model
        logger.info(f"Converting {temp_audio_path} to MIDI using ONNX model...")
        model_output, midi_data, note_events = predict(str(temp_audio_path), model_or_model_path=onnx_model_path)
        
        # Save MIDI file
        midi_data.write(str(midi_path))
        
        # Get duration and note count
        duration = midi_data.get_end_time() if midi_data.instruments else 0
        notes_count = sum(len(inst.notes) for inst in midi_data.instruments) if midi_data.instruments else 0
        
        # Cleanup temp file if we created one
        if cleanup_temp and temp_audio_path and temp_audio_path.exists():
            temp_audio_path.unlink()
        
        logger.info(f"MIDI conversion complete: {midi_path} ({notes_count} notes)")
        
        return jsonify({
            'success': True,
            'filename': midi_filename,
            'download_url': f'/download-midi/{username}/{midi_filename}',
            'notes_count': notes_count,
            'duration': duration
        })
        
    except ImportError as e:
        logger.error(f"Basic Pitch not installed: {e}")
        return jsonify({'success': False, 'error': 'MIDI conversion not available. Basic Pitch not installed.'}), 500
    except Exception as e:
        logger.error(f"MIDI conversion failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/download-midi/<username>/<filename>')
def download_midi(username, filename):
    """Download a MIDI file"""
    midi_dir = Path(__file__).parent.parent.parent / 'data' / 'outputs' / 'users' / username / 'midi'
    return send_from_directory(str(midi_dir), filename, as_attachment=True)


@app.route('/api/midi-library', methods=['GET'])
def get_midi_library():
    """Get list of user's MIDI files"""
    try:
        username = session.get('user_id', 'anonymous')
        midi_dir = Path(__file__).parent.parent.parent / 'data' / 'outputs' / 'users' / username / 'midi'
        
        files = []
        if midi_dir.exists():
            for midi_file in sorted(midi_dir.glob('*.mid'), key=lambda x: x.stat().st_mtime, reverse=True):
                stat = midi_file.stat()
                
                # Try to get note count and duration from the file
                notes_count = 0
                duration = 0
                try:
                    import pretty_midi
                    pm = pretty_midi.PrettyMIDI(str(midi_file))
                    duration = pm.get_end_time()
                    notes_count = sum(len(inst.notes) for inst in pm.instruments)
                except:
                    pass
                
                files.append({
                    'filename': midi_file.name,
                    'download_url': f'/download-midi/{username}/{midi_file.name}',
                    'size': stat.st_size,
                    'date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                    'notes': notes_count,
                    'duration': duration
                })
        
        return jsonify({
            'success': True,
            'files': files
        })
        
    except Exception as e:
        logger.error(f"Failed to get MIDI library: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/midi-library/delete', methods=['POST'])
def delete_midi_file():
    """Delete a MIDI file"""
    try:
        username = session.get('user_id', 'anonymous')
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'success': False, 'error': 'No filename provided'}), 400
        
        midi_path = Path(__file__).parent.parent.parent / 'data' / 'outputs' / 'users' / username / 'midi' / filename
        
        if midi_path.exists():
            midi_path.unlink()
            logger.info(f"Deleted MIDI file: {midi_path}")
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
            
    except Exception as e:
        logger.error(f"Failed to delete MIDI file: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/midi-parse', methods=['GET'])
def parse_midi_file():
    """Parse a MIDI file and return note data for playback"""
    try:
        import pretty_midi
        
        url = request.args.get('url')
        if not url:
            return jsonify({'success': False, 'error': 'No URL provided'}), 400
        
        # Parse the URL to get the file path
        # URL format: /download-midi/username/filename
        parts = url.strip('/').split('/')
        if len(parts) >= 3 and parts[0] == 'download-midi':
            username = parts[1]
            filename = parts[2]
            # Check in users folder first (main location)
            midi_path = Path(__file__).parent.parent.parent / 'data' / 'outputs' / 'users' / username / 'midi' / filename
            # Fallback to old location
            if not midi_path.exists():
                midi_path = Path(__file__).parent.parent.parent / 'data' / 'outputs' / 'midi' / username / filename
        else:
            return jsonify({'success': False, 'error': 'Invalid URL format'}), 400
        
        if not midi_path.exists():
            return jsonify({'success': False, 'error': f'File not found: {filename}'}), 404
        
        # Parse MIDI file
        pm = pretty_midi.PrettyMIDI(str(midi_path))
        
        # Extract all notes
        notes = []
        for instrument in pm.instruments:
            for note in instrument.notes:
                notes.append({
                    'pitch': note.pitch,
                    'start': note.start,
                    'duration': note.end - note.start,
                    'velocity': note.velocity
                })
        
        # Sort by start time
        notes.sort(key=lambda x: x['start'])
        
        return jsonify({
            'success': True,
            'notes': notes,
            'duration': pm.get_end_time(),
            'tracks': len(pm.instruments),
            'tempo': pm.estimate_tempo()
        })
        
    except ImportError:
        return jsonify({'success': False, 'error': 'pretty_midi not installed'}), 500
    except Exception as e:
        logger.error(f"Failed to parse MIDI file: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/plan-info', methods=['GET'])
def get_plan_info():
    """Get current user's plan information and usage"""
    from harmonix_splitter.auth import get_user_stats, get_plan, check_usage_limit, get_all_plans
    
    username = session.get('user_id')
    user_plan = session.get('user_plan', 'free')
    user_role = session.get('user_role', 'user')
    user_name = session.get('user_name', '')
    
    # Get plan details
    plan_info = get_plan(user_plan)
    
    # Get usage if logged in
    usage_info = None
    if username:
        usage_info = check_usage_limit(username)
        user_stats = get_user_stats(username)
    else:
        user_stats = None
    
    return jsonify({
        'logged_in': username is not None,
        'username': username,
        'name': user_name,
        'role': user_role,
        'is_admin': user_role == 'admin',
        'plan': user_plan,
        'plan_details': plan_info,
        'usage': usage_info,
        'stats': user_stats,
        'all_plans': get_all_plans()
    })


@app.route('/api/upgrade-plan', methods=['POST'])
def upgrade_plan_api():
    """Upgrade user's plan (would integrate with payment in production)"""
    from harmonix_splitter.auth import upgrade_plan
    
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    new_plan = data.get('plan')
    
    if new_plan not in ['free', 'creator', 'studio']:
        return jsonify({'error': 'Invalid plan'}), 400
    
    username = session.get('user_id')
    if not username:
        return jsonify({'error': 'Not logged in'}), 401
    
    # In production, this would handle payment verification
    # For now, just upgrade the plan directly
    success = upgrade_plan(username, new_plan)
    
    if success:
        session['user_plan'] = new_plan
        return jsonify({
            'success': True,
            'message': f'Successfully upgraded to {new_plan} plan',
            'new_plan': new_plan
        })
    else:
        return jsonify({'error': 'Failed to upgrade plan'}), 500


@app.route('/validate-url', methods=['POST'])
def validate_url():
    """Validate a URL and get video/audio info without downloading"""
    try:
        import yt_dlp
        
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'valid': False, 'error': 'No URL provided'}), 400
        
        # Supported patterns
        supported_patterns = [
            'youtube.com', 'youtu.be', 'soundcloud.com', 
            'vimeo.com', 'bandcamp.com'
        ]
        
        is_supported = any(pattern in url.lower() for pattern in supported_patterns)
        if not is_supported:
            return jsonify({
                'valid': False, 
                'error': 'Unsupported URL. Supported: YouTube, SoundCloud, Vimeo, Bandcamp'
            }), 400
        
        # Try to get info without downloading - use extract_flat for speed
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',  # Faster extraction
            'skip_download': True,
            'socket_timeout': 10,  # 10 second timeout
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
                info = ydl.extract_info(url, download=False)
                
                if info:
                    title = info.get('title', 'Unknown')
                    duration = info.get('duration', 0)
                    uploader = info.get('uploader', info.get('channel', info.get('uploader_id', '')))
                    
                    # Determine source
                    source = 'Unknown'
                    if 'youtube' in url.lower() or 'youtu.be' in url.lower():
                        source = 'YouTube'
                    elif 'soundcloud' in url.lower():
                        source = 'SoundCloud'
                    elif 'vimeo' in url.lower():
                        source = 'Vimeo'
                    elif 'bandcamp' in url.lower():
                        source = 'Bandcamp'
                    
                    return jsonify({
                        'valid': True,
                        'title': title,
                        'duration': duration,
                        'uploader': uploader,
                        'source': source
                    })
                else:
                    return jsonify({
                        'valid': False,
                        'error': 'Could not extract info from URL'
                    }), 400
                    
        except Exception as download_error:
            error_msg = str(download_error)
            logger.error(f"yt-dlp error: {error_msg}")
            if 'Private video' in error_msg:
                error_msg = 'This video is private'
            elif 'Video unavailable' in error_msg or 'unavailable' in error_msg.lower():
                error_msg = 'Video unavailable or removed'
            elif 'age' in error_msg.lower():
                error_msg = 'Age-restricted content cannot be downloaded'
            elif 'Sign in' in error_msg or 'sign in' in error_msg.lower():
                error_msg = 'This video requires sign-in'
            elif 'timed out' in error_msg.lower():
                error_msg = 'Request timed out. Please try again.'
            else:
                error_msg = f'Could not fetch video info: {error_msg[:100]}'
            return jsonify({'valid': False, 'error': error_msg}), 400
            
    except ImportError:
        return jsonify({
            'valid': False, 
            'error': 'yt-dlp not installed. Run: pip install yt-dlp'
        }), 500
    except Exception as e:
        logger.error(f"URL validation failed: {e}")
        return jsonify({'valid': False, 'error': str(e)}), 500
        return jsonify({'valid': False, 'error': str(e)}), 500


@app.route('/upload-url', methods=['POST'])
def upload_from_url():
    """Download audio from YouTube/URL and start processing"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        
        # Validate URL (YouTube, SoundCloud, etc.)
        supported_patterns = [
            'youtube.com', 'youtu.be', 'soundcloud.com', 
            'vimeo.com', 'bandcamp.com', 'spotify.com'
        ]
        
        is_supported = any(pattern in url.lower() for pattern in supported_patterns)
        if not is_supported:
            return jsonify({'error': 'Unsupported URL. Supported: YouTube, SoundCloud, Vimeo, Bandcamp'}), 400
        
        # ===== PLAN LIMIT ENFORCEMENT =====
        from harmonix_splitter.auth import check_usage_limit, get_plan, increment_song_usage
        
        username = session.get('user_id')
        user_plan = session.get('user_plan', 'free')
        plan_info = get_plan(user_plan)
        
        if username:
            # Check usage limit
            usage_check = check_usage_limit(username)
            if not usage_check['allowed']:
                return jsonify({
                    'error': f"Monthly limit reached! You've processed {usage_check['used']} of {usage_check['limit']} songs this month.",
                    'limit_reached': True,
                    'upgrade_url': '/#pricing'
                }), 403
        
        # Get parameters
        quality = data.get('quality', 'balanced')
        mode = data.get('mode', 'grouped')
        instruments_str = data.get('instruments', '')
        output_name = data.get('output_name', '').strip()
        
        # Parse instruments and validate against plan
        instruments = None
        if instruments_str:
            requested_instruments = [i.strip() for i in instruments_str.split(',') if i.strip()]
            # Filter to allowed stems for the user's plan
            allowed_stems = plan_info.get('stem_types', ['vocals', 'drums', 'bass', 'other'])
            instruments = [i for i in requested_instruments if i in allowed_stems]
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Create job output directory in user-specific location
        user_output_dir = get_user_output_dir(username)
        job_output_dir = user_output_dir / job_id
        job_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Increment usage counter for logged-in users
        if username:
            increment_song_usage(username)
        
        # Create job record with downloading status
        with jobs_lock:
            jobs_storage[job_id] = {
                'job_id': job_id,
                'filename': url,
                'display_name': output_name or 'Downloading...',
                'status': 'downloading',
                'progress': 0,
                'stage': 'Downloading from URL...',
                'quality': quality,
                'mode': mode,
                'instruments': instruments,
                'source_url': url,
                'user': username,
                'user_plan': user_plan,
                'created_at': datetime.now().isoformat()
            }
        
        # Start background download and processing with username
        thread = threading.Thread(
            target=download_and_process_url,
            args=(job_id, url, quality, mode, instruments, output_name, username)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'downloading',
            'message': 'Download started. Processing will begin automatically.'
        })
        
    except Exception as e:
        logger.error(f"URL upload failed: {e}")
        return jsonify({'error': str(e)}), 500


def download_and_process_url(job_id, url, quality, mode, instruments, output_name, username=None):
    """Background task to download audio from URL and process it"""
    try:
        import yt_dlp
        
        # Use user-specific output directory
        user_output_dir = get_user_output_dir(username)
        job_output_dir = user_output_dir / job_id
        job_output_dir.mkdir(parents=True, exist_ok=True)
        
        with jobs_lock:
            jobs_storage[job_id]['progress'] = 5
            jobs_storage[job_id]['stage'] = 'Fetching video info...'
        
        # Configure yt-dlp for best audio quality as MP3
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(job_output_dir / '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',  # MP3 format
                'preferredquality': '320',  # 320kbps
            }],
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'noplaylist': True,  # Download only single video, not playlist
        }
        
        # Download the audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
            # Get video info first
            with jobs_lock:
                jobs_storage[job_id]['progress'] = 10
                jobs_storage[job_id]['stage'] = 'Extracting audio...'
            
            info = ydl.extract_info(url, download=True)
            video_title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            logger.info(f"Job {job_id}: Downloaded '{video_title}' ({duration}s)")
        
        # Find the downloaded MP3 file (or other formats as fallback)
        audio_files = list(job_output_dir.glob('*.mp3'))
        if not audio_files:
            # Try other formats as fallback
            for ext in ['*.wav', '*.m4a', '*.webm', '*.opus']:
                audio_files = list(job_output_dir.glob(ext))
                if audio_files:
                    break
        
        if not audio_files:
            raise Exception("Failed to download audio file")
        
        audio_path = audio_files[0]
        
        # Use custom output name or video title
        display_name = secure_filename(output_name) if output_name else secure_filename(video_title or 'Unknown')
        
        # Rename to use display_name as "original" audio
        original_audio_path = job_output_dir / f"{display_name}_original{audio_path.suffix}"
        audio_path.rename(original_audio_path)
        audio_path = original_audio_path
        
        with jobs_lock:
            jobs_storage[job_id]['filename'] = audio_path.name
            jobs_storage[job_id]['display_name'] = display_name
            jobs_storage[job_id]['duration'] = duration
            jobs_storage[job_id]['video_title'] = video_title
            jobs_storage[job_id]['progress'] = 15
            jobs_storage[job_id]['status'] = 'analyzing'
            jobs_storage[job_id]['stage'] = 'Analyzing audio...'
        
        logger.info(f"Job {job_id}: Audio saved as {original_audio_path.name}")
        
        # Now process the audio (reuse existing function logic)
        process_downloaded_audio(job_id, audio_path, quality, mode, instruments, display_name, username)
        
    except Exception as e:
        logger.error(f"Job {job_id}: URL download failed - {e}")
        with jobs_lock:
            jobs_storage[job_id].update({
                'status': 'failed',
                'error': str(e),
                'stage': f'Download failed: {str(e)}'
            })


def process_downloaded_audio(job_id, audio_path, quality, mode, instruments, display_name, username=None):
    """Process audio that was downloaded from URL (similar to process_audio_async)"""
    # Get user-specific output directory
    user_output_dir = get_user_output_dir(username)
    
    try:
        # Step 1: Analyze audio for tempo/key
        try:
            analyzer = MusicAnalyzer()
            analysis = analyzer.analyze(Path(audio_path))
            
            music_info = {
                'tempo': {
                    'bpm': analysis.tempo.bpm,
                    'confidence': analysis.tempo.bpm_confidence
                },
                'key': {
                    'key': analysis.key.key,
                    'scale': analysis.key.scale,
                    'confidence': analysis.key.confidence,
                    'camelot': analyzer.get_camelot_wheel(analysis.key.key, analysis.key.scale)
                },
                'duration': analysis.duration
            }
            
            with jobs_lock:
                jobs_storage[job_id]['music_info'] = music_info
                jobs_storage[job_id]['progress'] = 20
                jobs_storage[job_id]['stage'] = f'Detected: {analysis.tempo.bpm} BPM, {analysis.key.key} {analysis.key.scale}'
            
            logger.info(f"Job {job_id}: Detected {analysis.tempo.bpm} BPM, {analysis.key.key} {analysis.key.scale}")
        except Exception as e:
            logger.warning(f"Job {job_id}: Music analysis failed - {e}")
        
        # Step 2: Start separation
        with jobs_lock:
            jobs_storage[job_id]['status'] = 'processing'
            jobs_storage[job_id]['progress'] = 25
            jobs_storage[job_id]['stage'] = f'Separating stems ({quality} quality)...'
        
        logger.info(f"Job {job_id}: Starting {quality} quality separation")
        
        # Create orchestrator
        orchestrator = create_orchestrator(auto_route=True)
        
        with jobs_lock:
            jobs_storage[job_id]['progress'] = 30
        
        # Process audio - output to the user-specific job directory
        result = orchestrator.process(
            audio_path=str(audio_path),
            job_id=job_id,
            quality=quality,
            mode=mode,
            target_instruments=instruments if instruments else None,
            output_dir=str(user_output_dir),
            custom_name=display_name
        )
        
        with jobs_lock:
            jobs_storage[job_id]['progress'] = 90
            jobs_storage[job_id]['stage'] = 'Finalizing...'
        
        if result.status == "completed":
            # Prepare stem URLs
            stem_urls = {}
            job_dir = user_output_dir / job_id
            
            for stem_name in result.stems.keys():
                # Check for WAV first (lossless), then MP3
                stem_file = job_dir / f"{display_name}_{stem_name}.wav"
                if not stem_file.exists():
                    stem_file = job_dir / f"{display_name}_{stem_name}.mp3"
                if stem_file.exists():
                    stem_urls[stem_name] = f"/download/{job_id}/{stem_name}"
            
            # Add original audio as a "stem"
            original_files = list(job_dir.glob(f"*_original.*"))
            if original_files:
                stem_urls['original'] = f"/download/{job_id}/original"
            
            with jobs_lock:
                jobs_storage[job_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'stage': 'Complete',
                    'stems': stem_urls,
                    'detected_instruments': result.detected_instruments,
                    'processing_time': result.processing_time,
                    'completed_at': datetime.now().isoformat()
                })
            
            logger.info(f"Job {job_id}: Completed successfully in {result.processing_time:.1f}s")
        else:
            raise Exception(result.metadata.get('error', 'Unknown error'))
            
    except Exception as e:
        logger.error(f"Job {job_id}: Processing failed - {e}")
        with jobs_lock:
            jobs_storage[job_id].update({
                'status': 'failed',
                'error': str(e),
                'stage': f'Processing failed: {str(e)}'
            })


@app.route('/status/<job_id>')
def get_status(job_id):
    """Get job status - only owner can access"""
    username = session.get('user_id')
    user_role = session.get('user_role')
    
    with jobs_lock:
        job = jobs_storage.get(job_id)
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    # Check ownership (admin can view any)
    if user_role != 'admin' and job.get('user') != username:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(job)


@app.route('/download/<job_id>/<stem_name>')
def download_stem(job_id, stem_name):
    """Download a specific stem - serves MP3 by default for smaller files"""
    username = session.get('user_id')
    user_role = session.get('user_role')
    
    # Get job info to determine owner
    with jobs_lock:
        job = jobs_storage.get(job_id)
    
    # Check ownership if job exists in storage (admin can access any)
    if job and user_role != 'admin' and job.get('user') != username:
        return jsonify({'error': 'Access denied'}), 403
    
    # Determine which directory to look in
    job_owner = job.get('user') if job else username
    user_output_dir = get_user_output_dir(job_owner)
    
    # First check user-specific directory
    job_dir = user_output_dir / job_id
    
    # Fallback to legacy location for backward compatibility
    if not job_dir.exists():
        job_dir = OUTPUT_DIR / job_id
        
    if not job_dir.exists():
        return jsonify({'error': 'Job not found'}), 404
    
    # Handle "original" stem (the downloaded source audio)
    if stem_name == 'original':
        original_files = list(job_dir.glob('*_original.*'))
        if original_files:
            stem_file = original_files[0]
            ext = stem_file.suffix.lower()
            mimetype = 'audio/mpeg' if ext == '.mp3' else 'audio/wav' if ext == '.wav' else 'audio/mp4'
            return send_file(
                stem_file,
                as_attachment=False,
                download_name=stem_file.name,
                mimetype=mimetype
            )
        return jsonify({'error': 'Original audio not found'}), 404
    
    # Find stem file - prefer MP3 (compressed, faster to load) over WAV
    stem_files = list(job_dir.glob(f"*_{stem_name}.mp3"))
    mimetype = 'audio/mpeg'
    
    if not stem_files:
        # Fallback to WAV if MP3 not found
        stem_files = list(job_dir.glob(f"*_{stem_name}.wav"))
        mimetype = 'audio/wav'
    
    if not stem_files:
        return jsonify({'error': f'Stem file not found: {stem_name}'}), 404
    
    stem_file = stem_files[0]
    
    # Log the file being served for debugging
    logger.debug(f"Serving stem: {stem_file.name} ({stem_file.stat().st_size / 1024 / 1024:.1f} MB)")
    
    return send_file(
        stem_file,
        as_attachment=False,  # Allow streaming for player
        download_name=stem_file.name,
        mimetype=mimetype
    )


@app.route('/jobs')
def list_jobs():
    """List jobs for the current user only"""
    username = session.get('user_id')
    user_role = session.get('user_role')
    
    # Re-scan outputs for current user to catch any new files
    scan_existing_outputs(username)
    
    with jobs_lock:
        # Filter jobs to only show user's own jobs (admin sees all)
        if user_role == 'admin':
            jobs = list(jobs_storage.values())
        else:
            jobs = [job for job in jobs_storage.values() 
                    if job.get('user') == username or 
                    (job.get('user') is None and username is None)]
    
    # Sort by creation time (newest first)
    jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return jsonify({'jobs': jobs[:50]})  # Limit to 50 most recent


@app.route('/delete/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a job and its files - only owner can delete"""
    username = session.get('user_id')
    user_role = session.get('user_role')
    
    with jobs_lock:
        job = jobs_storage.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Check ownership (admin can delete any)
        if user_role != 'admin' and job.get('user') != username:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get user-specific output directory
        job_owner = job.get('user')
        user_output_dir = get_user_output_dir(job_owner)
        
        # Delete output files from user's directory
        output_dir = user_output_dir / job_id
        if output_dir.exists():
            import shutil
            shutil.rmtree(output_dir)
        
        # Also check legacy location for backward compatibility
        legacy_dir = OUTPUT_DIR / job_id
        if legacy_dir.exists():
            import shutil
            shutil.rmtree(legacy_dir)
        
        # Delete from storage
        del jobs_storage[job_id]
    
    return jsonify({'message': 'Job deleted successfully'})


@app.route('/rename/<job_id>', methods=['PUT'])
def rename_job(job_id):
    """Rename a job/track"""
    try:
        data = request.get_json()
        new_name = data.get('name', '').strip()
        
        if not new_name:
            return jsonify({'error': 'Name is required'}), 400
        
        # Get current user
        current_user = session.get('user_id')
        is_admin = session.get('user_role') == 'admin'
        
        with jobs_lock:
            job = jobs_storage.get(job_id)
            if not job:
                return jsonify({'error': 'Job not found'}), 404
            
            # Check ownership - only owner or admin can rename
            job_owner = job.get('user')  # Job stores username as 'user'
            if not is_admin and job_owner != current_user:
                return jsonify({'error': 'You do not have permission to rename this job'}), 403
            
            old_name = job.get('display_name', job.get('filename', ''))
            
            # Update display name in storage
            jobs_storage[job_id]['display_name'] = new_name
            
            # Get the user-specific output directory for file operations
            user_output_dir = get_user_output_dir(job_owner)
            job_dir = user_output_dir / job_id
            
            if job_dir.exists():
                # Find old base name from files
                old_base = None
                for f in job_dir.glob("*.mp3"):
                    parts = f.stem.rsplit('_', 1)
                    if len(parts) == 2:
                        old_base = parts[0]
                        break
                
                # If no mp3, check wav
                if not old_base:
                    for f in job_dir.glob("*.wav"):
                        if '_pitch' not in f.stem and '_lyrics' not in f.stem:
                            parts = f.stem.rsplit('_', 1)
                            if len(parts) == 2:
                                old_base = parts[0]
                                break
                
                if old_base:
                    # Rename all stem files
                    for ext in ['*.mp3', '*.wav']:
                        for f in job_dir.glob(ext):
                            if '_pitch' in f.stem or '_lyrics' in f.stem:
                                continue
                            parts = f.stem.rsplit('_', 1)
                            if len(parts) == 2:
                                stem_type = parts[1]
                                new_filename = f"{new_name}_{stem_type}{f.suffix}"
                                new_path = job_dir / new_filename
                                f.rename(new_path)
                    
                    # Rename lyrics files if they exist
                    for lrc in job_dir.glob("*_lyrics.*"):
                        new_lrc_name = f"{new_name}_vocals_lyrics{lrc.suffix}"
                        lrc.rename(job_dir / new_lrc_name)
        
        logger.info(f"Renamed job {job_id}: '{old_name}' -> '{new_name}'")
        return jsonify({'message': 'Track renamed successfully', 'new_name': new_name})
        
    except Exception as e:
        logger.error(f"Failed to rename job: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/analyze', methods=['POST'])
def analyze_audio():
    """Analyze audio file for tempo, key, and processing time estimate"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        quality = request.form.get('quality', 'balanced')
        mode = request.form.get('mode', 'grouped')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save temporarily for analysis
        filename = file.filename or 'unknown.wav'
        temp_path = UPLOAD_DIR / f"analyze_{uuid.uuid4()}{Path(filename).suffix}"
        file.save(str(temp_path))
        
        try:
            # Get audio duration
            duration = librosa.get_duration(path=str(temp_path))
            
            # Check if GPU available
            try:
                import torch
                has_gpu = torch.cuda.is_available()
            except:
                has_gpu = False
            
            # Estimate processing time
            time_estimate = estimate_processing_time(
                duration_seconds=duration,
                quality=quality,
                has_gpu=has_gpu,
                mode=mode
            )
            
            # Perform music analysis
            analyzer = MusicAnalyzer()
            analysis = analyzer.analyze(temp_path)
            
            # Get Camelot notation
            camelot = analyzer.get_camelot_wheel(analysis.key.key, analysis.key.scale)
            
            result = {
                'duration': round(duration, 2),
                'duration_formatted': format_duration(duration),
                'tempo': {
                    'bpm': analysis.tempo.bpm,
                    'confidence': analysis.tempo.bpm_confidence,
                    'stability': analysis.tempo.tempo_stability,
                    'time_signature': f"{analysis.tempo.time_signature[0]}/{analysis.tempo.time_signature[1]}"
                },
                'key': {
                    'key': analysis.key.key,
                    'scale': analysis.key.scale,
                    'confidence': analysis.key.confidence,
                    'camelot': camelot,
                    'alternatives': [
                        {'key': k, 'scale': s, 'confidence': round(c, 2)}
                        for k, s, c in analysis.key.alternative_keys[:3]
                    ]
                },
                'sections': len(analysis.sections),
                'estimate': time_estimate
            }
            
            return jsonify(result)
            
        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
                
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/estimate', methods=['POST'])
@app.route('/estimate-time', methods=['POST'])
def estimate_time():
    """Quick estimate without full analysis"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            duration = float(data.get('duration', 180))
            quality = data.get('quality', 'balanced')
            mode = data.get('mode', 'grouped')
        else:
            duration = float(request.form.get('duration', 180))
            quality = request.form.get('quality', 'balanced')
            mode = request.form.get('mode', 'grouped')
        
        try:
            import torch
            has_gpu = torch.cuda.is_available()
        except:
            has_gpu = False
        
        estimate = estimate_processing_time(
            duration_seconds=duration,
            quality=quality,
            has_gpu=has_gpu,
            mode=mode
        )
        
        return jsonify(estimate)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/analyze/<job_id>')
def analyze_job(job_id):
    """Get music analysis for an existing job"""
    try:
        # Check if job has cached analysis
        with jobs_lock:
            job = jobs_storage.get(job_id)
            if job and 'music_info' in job:
                # Return cached analysis
                music_info = job['music_info']
                return jsonify({
                    'tempo': music_info.get('tempo'),
                    'key': music_info.get('key'),
                    'time_signature': {'time_signature': '4/4'}  # Default for cached
                })
        
        # Find audio file in job directory
        job_dir = OUTPUT_DIR / job_id
        if not job_dir.exists():
            return jsonify({'error': 'Job not found'}), 404
        
        # Find any stem file to analyze (vocals is usually best for key detection)
        stem_files = list(job_dir.glob("*_vocals.wav"))
        if not stem_files:
            stem_files = list(job_dir.glob("*.wav"))
        
        if not stem_files:
            return jsonify({'error': 'No audio files found'}), 404
        
        audio_path = stem_files[0]
        
        # Quick analysis - just tempo and key, skip sections for speed
        analyzer = MusicAnalyzer()
        y, sr = librosa.load(str(audio_path), sr=analyzer.sample_rate, mono=True)
        duration = len(y) / sr
        
        # Get tempo
        tempo_analysis = analyzer.analyze_tempo(y, int(sr))
        
        # Get key
        key_analysis = analyzer.analyze_key(y, int(sr))
        
        # Get Camelot notation
        camelot = analyzer.get_camelot_wheel(key_analysis.key, key_analysis.scale)
        
        result = {
            'tempo': {
                'bpm': tempo_analysis.bpm,
                'confidence': tempo_analysis.bpm_confidence,
                'beat_times': tempo_analysis.beat_positions.tolist()[:20] if len(tempo_analysis.beat_positions) > 0 else []
            },
            'key': {
                'key': key_analysis.key,
                'mode': key_analysis.scale,
                'confidence': key_analysis.confidence,
                'camelot': camelot
            },
            'time_signature': {
                'time_signature': f"{tempo_analysis.time_signature[0]}/{tempo_analysis.time_signature[1]}"
            },
            'duration': duration
        }
        
        # Cache in job storage
        with jobs_lock:
            if job_id in jobs_storage:
                jobs_storage[job_id]['music_info'] = {
                    'tempo': result['tempo'],
                    'key': result['key'],
                    'duration': result['duration']
                }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Analysis for job {job_id} failed: {e}")
        return jsonify({'error': str(e)}), 500


def format_duration(seconds: float) -> str:
    """Format duration in human readable format"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    if mins > 0:
        return f"{mins}m {secs}s"
    return f"{secs}s"


@app.route('/pitch-shift/<job_id>/<stem_name>', methods=['POST'])
def pitch_shift_stem(job_id, stem_name):
    """
    Apply pitch shift to a stem and stream the result
    
    POST body: {"semitones": -2}  (range: -4 to +4)
    """
    try:
        # Get parameters
        data = request.get_json() or {}
        semitones = float(data.get('semitones', 0))
        
        # Clamp to safe range
        semitones = max(-4, min(4, semitones))
        
        if semitones == 0:
            # No pitch shift, serve original file
            return download_stem(job_id, stem_name)
        
        # Find stem file (MP3 first, then WAV)
        job_dir = OUTPUT_DIR / job_id
        if not job_dir.exists():
            return jsonify({'error': 'Job not found'}), 404
        
        stem_files = list(job_dir.glob(f"*_{stem_name}.mp3"))
        if not stem_files:
            stem_files = list(job_dir.glob(f"*_{stem_name}.wav"))
        if not stem_files:
            return jsonify({'error': f'Stem not found: {stem_name}'}), 404
        
        stem_file = stem_files[0]
        
        # Check for cached pitch-shifted version
        cache_key = f"{stem_name}_pitch_{semitones:+.1f}"
        cache_file = job_dir / f"{stem_file.stem}_pitch{semitones:+.1f}.wav"
        
        if cache_file.exists():
            logger.info(f"Serving cached pitch-shifted file: {cache_file}")
            return send_file(
                cache_file,
                as_attachment=False,
                download_name=cache_file.name,
                mimetype='audio/wav'
            )
        
        # Perform pitch shift
        logger.info(f"Pitch shifting {stem_name} by {semitones:+.1f} semitones")
        
        processor = AudioProcessor()
        processor.pitch_shift_file(
            stem_file,
            cache_file,
            semitones=semitones,
            preserve_formants=True,
            algorithm="high_quality"
        )
        
        return send_file(
            cache_file,
            as_attachment=False,
            download_name=cache_file.name,
            mimetype='audio/wav'
        )
        
    except Exception as e:
        logger.error(f"Pitch shift failed: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/extract-lyrics/<job_id>', methods=['POST'])
def extract_lyrics(job_id):
    """
    Extract lyrics from original audio track (better quality than vocals stem)
    
    POST body: {"language": "auto"}  (auto, en, ar, fr)
    """
    try:
        # Get current user and check ownership
        current_user = session.get('user_id')
        is_admin = session.get('user_role') == 'admin'
        
        with jobs_lock:
            job = jobs_storage.get(job_id)
            if not job:
                return jsonify({'error': 'Job not found'}), 404
            
            job_owner = job.get('user')  # Job stores username as 'user'
            if not is_admin and job_owner != current_user:
                return jsonify({'error': 'You do not have permission to extract lyrics for this job'}), 403
        
        # Get parameters
        data = request.get_json() or {}
        language = data.get('language', 'auto')
        
        # Use user-specific output directory
        user_output_dir = get_user_output_dir(job_owner)
        job_dir = user_output_dir / job_id
        
        if not job_dir.exists():
            return jsonify({'error': 'Job directory not found'}), 404
        
        # First try to find original audio file (from URL downloads)
        audio_files = list(job_dir.glob("*_original.mp3"))
        if not audio_files:
            audio_files = list(job_dir.glob("*_original.wav"))
        
        # Fallback to vocals stem if no original exists
        if not audio_files:
            audio_files = list(job_dir.glob("*_vocals.mp3"))
        if not audio_files:
            audio_files = list(job_dir.glob("*_vocals.wav"))
        
        if not audio_files:
            return jsonify({'error': 'No audio file found for lyrics extraction'}), 404
        
        audio_file = audio_files[0]
        logger.info(f"Using {audio_file.name} for lyrics extraction")
        
        # Check for cached lyrics (use base name without stem type for cache)
        base_name = audio_file.stem.rsplit('_', 1)[0]  # Remove _original or _vocals suffix
        lyrics_cache = job_dir / f"{base_name}_lyrics.json"
        if lyrics_cache.exists():
            # Check if language matches
            with open(lyrics_cache, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                if language == 'auto' or cached.get('language') == language:
                    logger.info(f"Serving cached lyrics for job {job_id}")
                    return jsonify(cached)
        
        # Extract lyrics
        logger.info(f"Extracting lyrics from {audio_file} (language: {language})")
        
        try:
            # Use "large" model for highest accuracy lyrics detection
            # Download size ~2.9GB but provides best transcription quality
            extractor = LyricsExtractor(model_size="large")
            result = extractor.extract(audio_file, language=language)
            
            # Save to cache
            result_dict = result.to_dict()
            with open(lyrics_cache, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2)
            
            # Also save LRC format for karaoke
            lrc_file = job_dir / f"{base_name}_lyrics.lrc"
            with open(lrc_file, 'w', encoding='utf-8') as f:
                f.write(result.to_lrc())
            
            return jsonify(result_dict)
            
        except ImportError:
            return jsonify({
                'error': 'Whisper not installed. Install with: pip install openai-whisper',
                'install_command': 'pip install openai-whisper'
            }), 500
        
    except Exception as e:
        logger.error(f"Lyrics extraction failed: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/lyrics/<job_id>')
def get_lyrics(job_id):
    """Get cached lyrics for a job"""
    try:
        # Get current user and check ownership
        current_user = session.get('user_id')
        is_admin = session.get('user_role') == 'admin'
        
        with jobs_lock:
            job = jobs_storage.get(job_id)
            if not job:
                return jsonify({'error': 'Job not found', 'available': False}), 404
            
            job_owner = job.get('user')  # Job stores username as 'user'
            if not is_admin and job_owner != current_user:
                return jsonify({'error': 'Permission denied', 'available': False}), 403
        
        # Use user-specific output directory
        user_output_dir = get_user_output_dir(job_owner)
        job_dir = user_output_dir / job_id
        
        if not job_dir.exists():
            return jsonify({'error': 'Job not found', 'available': False}), 404
        
        # Find lyrics file
        lyrics_files = list(job_dir.glob("*_lyrics.json"))
        if not lyrics_files:
            # Return 200 with available=false so frontend doesn't see console error
            return jsonify({'available': False, 'message': 'Lyrics not extracted yet'})
        
        with open(lyrics_files[0], 'r', encoding='utf-8') as f:
            lyrics = json.load(f)
        
        lyrics['available'] = True
        return jsonify(lyrics)
        
    except Exception as e:
        logger.error(f"Failed to get lyrics: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/lyrics/<job_id>/lrc')
def get_lyrics_lrc(job_id):
    """Get lyrics in LRC format for karaoke"""
    try:
        # Get current user and check ownership
        current_user = session.get('user_id')
        is_admin = session.get('user_role') == 'admin'
        
        with jobs_lock:
            job = jobs_storage.get(job_id)
            if not job:
                return jsonify({'error': 'Job not found'}), 404
            
            job_owner = job.get('user')  # Job stores username as 'user'
            if not is_admin and job_owner != current_user:
                return jsonify({'error': 'Permission denied'}), 403
        
        # Use user-specific output directory
        user_output_dir = get_user_output_dir(job_owner)
        job_dir = user_output_dir / job_id
        
        if not job_dir.exists():
            return jsonify({'error': 'Job not found'}), 404
        
        lrc_files = list(job_dir.glob("*_lyrics.lrc"))
        if not lrc_files:
            return jsonify({'error': 'Lyrics not extracted yet'}), 404
        
        return send_file(
            lrc_files[0],
            as_attachment=False,
            download_name=lrc_files[0].name,
            mimetype='text/plain'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/lyrics/<job_id>/save', methods=['POST'])
def save_lyrics(job_id):
    """Save edited lyrics to both JSON and LRC files"""
    try:
        # Get current user and check ownership
        current_user = session.get('user_id')
        is_admin = session.get('user_role') == 'admin'
        
        with jobs_lock:
            job = jobs_storage.get(job_id)
            if not job:
                return jsonify({'error': 'Job not found'}), 404
            
            job_owner = job.get('user')
            if not is_admin and job_owner != current_user:
                return jsonify({'error': 'Permission denied'}), 403
        
        # Get the lyrics data from request
        data = request.get_json()
        if not data or 'lines' not in data:
            return jsonify({'error': 'Invalid lyrics data'}), 400
        
        # Get job directory
        user_output_dir = get_user_output_dir(job_owner)
        job_dir = user_output_dir / job_id
        
        if not job_dir.exists():
            return jsonify({'error': 'Job directory not found'}), 404
        
        # Find existing lyrics files
        json_files = list(job_dir.glob("*_lyrics.json"))
        lrc_files = list(job_dir.glob("*_lyrics.lrc"))
        
        if not json_files:
            # Create new filename based on job
            base_name = job.get('original_name', 'audio').replace(' ', '_')
            json_file = job_dir / f"{base_name}_lyrics.json"
            lrc_file = job_dir / f"{base_name}_lyrics.lrc"
        else:
            json_file = json_files[0]
            lrc_file = job_dir / json_files[0].name.replace('.json', '.lrc')
        
        # Build the full lyrics data
        lyrics_data = {
            'text': data.get('text', ''),
            'lines': data['lines'],
            'language': data.get('language', 'unknown'),
            'language_confidence': data.get('language_confidence', 1.0),
            'duration': data.get('duration', 0),
            'edited': True,
            'edit_timestamp': datetime.now().isoformat()
        }
        
        # Save JSON file
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(lyrics_data, f, ensure_ascii=False, indent=2)
        
        # Generate and save LRC file
        lrc_content = generate_lrc_from_lines(data['lines'])
        with open(lrc_file, 'w', encoding='utf-8') as f:
            f.write(lrc_content)
        
        logger.info(f"Saved edited lyrics for job {job_id}")
        
        return jsonify({
            'success': True,
            'message': 'Lyrics saved successfully',
            'json_file': str(json_file),
            'lrc_file': str(lrc_file)
        })
        
    except Exception as e:
        logger.error(f"Failed to save lyrics: {e}")
        return jsonify({'error': str(e)}), 500


def generate_lrc_from_lines(lines):
    """Generate LRC format from lyrics lines"""
    lrc_lines = []
    for line in lines:
        start = line.get('start', 0)
        mins = int(start // 60)
        secs = start % 60
        
        # Build text from words if available
        if line.get('words'):
            text = ' '.join(w.get('word', w.get('text', '')) for w in line['words'])
        else:
            text = line.get('text', '')
        
        lrc_lines.append(f"[{mins:02d}:{secs:05.2f}]{text}")
    
    return '\n'.join(lrc_lines)


@app.route('/karaoke/<job_id>')
def karaoke_page(job_id):
    """Karaoke display page - full screen lyrics for singers"""
    try:
        # Get current user and check ownership
        current_user = session.get('user_id')
        is_admin = session.get('user_role') == 'admin'
        
        with jobs_lock:
            job = jobs_storage.get(job_id)
            if not job:
                return "Job not found", 404
            
            job_owner = job.get('user')
            if not is_admin and job_owner != current_user:
                return "Permission denied", 403
        
        # Get job details for display - try multiple fields for name
        job_name = job.get('original_name') or job.get('display_name') or job.get('filename', 'Unknown Track')
        # Clean up the name (remove extension if present)
        if job_name.endswith(('.mp3', '.wav', '.flac', '.m4a', '.ogg')):
            job_name = job_name.rsplit('.', 1)[0]
        
        return render_template('karaoke.html', 
                               job_id=job_id, 
                               job_name=job_name,
                               job_owner=job_owner)
        
    except Exception as e:
        logger.error(f"Failed to load karaoke page: {e}")
        return f"Error: {str(e)}", 500


if __name__ == '__main__':
    # Scan for existing outputs on startup
    scan_existing_outputs()
    
    # Get port from environment (Railway uses PORT env var)
    port = int(os.environ.get('PORT', 5001))
    
    # Run the app
    print("=" * 60)
    print("  Harmonix Audio Splitter - Web Dashboard")
    print("=" * 60)
    print(f"\n  🌐 Open your browser to: http://localhost:{port}")
    print(f"\n  Press Ctrl+C to stop the server\n")
    print("=" * 60)
    
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
