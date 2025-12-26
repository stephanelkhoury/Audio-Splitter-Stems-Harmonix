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
import librosa
import numpy as np
import soundfile as sf

from harmonix_splitter.core.orchestrator import create_orchestrator
from harmonix_splitter.config.settings import Settings
from harmonix_splitter.analysis.music_analyzer import MusicAnalyzer, estimate_processing_time
from harmonix_splitter.audio.processor import AudioProcessor
from harmonix_splitter.audio.lyrics import LyricsExtractor, LyricsResult

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'harmonix-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

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


def scan_existing_outputs():
    """Scan the output directory for existing processed jobs"""
    logger.info("Scanning for existing outputs...")
    
    for job_dir in OUTPUT_DIR.iterdir():
        if job_dir.is_dir() and not job_dir.name.startswith('.'):
            job_id = job_dir.name
            
            # Skip if already in storage
            if job_id in jobs_storage:
                continue
            
            # Find stem files (exclude pitch-shifted cache files and lyrics files)
            stem_files = [f for f in job_dir.glob("*.wav") 
                          if '_pitch' not in f.stem 
                          and '_lyrics' not in f.stem
                          and not f.stem.startswith('pitch')]
            if not stem_files:
                continue
            
            # Valid stem types (filter out any invalid stems)
            valid_stem_types = {'vocals', 'drums', 'bass', 'guitar', 'piano', 'other', 'instrumental'}
            
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
                
                # Create job record
                jobs_storage[job_id] = {
                    'job_id': job_id,
                    'filename': f"{base_name}.wav",
                    'display_name': base_name,
                    'status': 'completed',
                    'progress': 100,
                    'stems': stems,
                    'has_lyrics': has_lyrics,
                    'created_at': mod_time.isoformat(),
                    'completed_at': mod_time.isoformat()
                }
                logger.info(f"Found existing job: {job_id} ({base_name}) with {len(stems)} stems")
    
    logger.info(f"Scan complete. Found {len(jobs_storage)} existing jobs.")


def allowed_file(filename):
    """Check if file extension is allowed"""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def process_audio_async(job_id, audio_path, quality, mode, instruments, display_name=None):
    """Background task to process audio"""
    try:
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
        
        # Process audio
        result = orchestrator.process(
            audio_path=audio_path,
            job_id=job_id,
            quality=quality,
            mode=mode,
            target_instruments=instruments if instruments else None,
            output_dir=str(OUTPUT_DIR),
            custom_name=display_name
        )
        
        with jobs_lock:
            jobs_storage[job_id]['progress'] = 90
            jobs_storage[job_id]['stage'] = 'Finalizing...'
        
        if result.status == "completed":
            # Prepare stem URLs
            stem_urls = {}
            for stem_name in result.stems.keys():
                stem_file = OUTPUT_DIR / job_id / f"{Path(audio_path).stem}_{stem_name}.wav"
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
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


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
        output_name = request.form.get('output_name', '').strip()
        
        # Parse instruments
        instruments = None
        if instruments_str:
            instruments = [i.strip() for i in instruments_str.split(',') if i.strip()]
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded file with proper extension
        # Extract extension BEFORE secure_filename to preserve the dot
        original_filename = file.filename
        file_ext = Path(original_filename).suffix.lower()  # e.g., ".mp3"
        base_name = secure_filename(Path(original_filename).stem)  # secure only the name part
        
        # Use custom output name if provided, otherwise use original filename
        display_name = secure_filename(output_name) if output_name else base_name
        
        # Create the upload path with proper extension
        upload_path = UPLOAD_DIR / f"{job_id}_{base_name}{file_ext}"
        file.save(str(upload_path))
        
        logger.info(f"Job {job_id}: File uploaded - {base_name}{file_ext} (output as: {display_name})")
        
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
                'created_at': datetime.now().isoformat()
            }
        
        # Start background processing
        thread = threading.Thread(
            target=process_audio_async,
            args=(job_id, upload_path, quality, mode, instruments, display_name)
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
    # First check if job folder exists on disk
    job_dir = OUTPUT_DIR / job_id
    if not job_dir.exists():
        return jsonify({'error': 'Job not found'}), 404
    
    # Find stem file by searching for matching pattern
    stem_files = list(job_dir.glob(f"*_{stem_name}.wav"))
    
    if not stem_files:
        return jsonify({'error': f'Stem file not found: {stem_name}'}), 404
    
    stem_file = stem_files[0]
    
    return send_file(
        stem_file,
        as_attachment=False,  # Allow streaming for player
        download_name=stem_file.name,
        mimetype='audio/wav'
    )


@app.route('/jobs')
def list_jobs():
    """List all jobs"""
    # Re-scan outputs to catch any new files
    scan_existing_outputs()
    
    with jobs_lock:
        jobs = list(jobs_storage.values())
    
    # Sort by creation time (newest first)
    jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return jsonify({'jobs': jobs[:50]})  # Limit to 50 most recent


@app.route('/delete/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a job and its files"""
    with jobs_lock:
        job = jobs_storage.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Delete output files
        output_dir = OUTPUT_DIR / job_id
        if output_dir.exists():
            import shutil
            shutil.rmtree(output_dir)
        
        # Delete from storage
        del jobs_storage[job_id]
    
    return jsonify({'message': 'Job deleted successfully'})


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
        temp_path = UPLOAD_DIR / f"analyze_{uuid.uuid4()}{Path(file.filename).suffix}"
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
        tempo_analysis = analyzer.analyze_tempo(y, sr)
        
        # Get key
        key_analysis = analyzer.analyze_key(y, sr)
        
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
        
        # Find stem file
        job_dir = OUTPUT_DIR / job_id
        if not job_dir.exists():
            return jsonify({'error': 'Job not found'}), 404
        
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
    Extract lyrics from vocals stem
    
    POST body: {"language": "auto"}  (auto, en, ar, fr)
    """
    try:
        # Get parameters
        data = request.get_json() or {}
        language = data.get('language', 'auto')
        
        # Find vocals stem
        job_dir = OUTPUT_DIR / job_id
        if not job_dir.exists():
            return jsonify({'error': 'Job not found'}), 404
        
        vocals_files = list(job_dir.glob("*_vocals.wav"))
        if not vocals_files:
            return jsonify({'error': 'Vocals stem not found'}), 404
        
        vocals_file = vocals_files[0]
        
        # Check for cached lyrics
        lyrics_cache = job_dir / f"{vocals_file.stem}_lyrics.json"
        if lyrics_cache.exists():
            # Check if language matches
            with open(lyrics_cache, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                if language == 'auto' or cached.get('language') == language:
                    logger.info(f"Serving cached lyrics for job {job_id}")
                    return jsonify(cached)
        
        # Extract lyrics
        logger.info(f"Extracting lyrics from {vocals_file} (language: {language})")
        
        try:
            # Use "large" model for highest accuracy lyrics detection
            # Download size ~2.9GB but provides best transcription quality
            extractor = LyricsExtractor(model_size="large")
            result = extractor.extract(vocals_file, language=language)
            
            # Save to cache
            result_dict = result.to_dict()
            with open(lyrics_cache, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2)
            
            # Also save LRC format for karaoke
            lrc_file = job_dir / f"{vocals_file.stem}_lyrics.lrc"
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
        job_dir = OUTPUT_DIR / job_id
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
        job_dir = OUTPUT_DIR / job_id
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


if __name__ == '__main__':
    # Scan for existing outputs on startup
    scan_existing_outputs()
    
    # Run the app
    print("=" * 60)
    print("  Harmonix Audio Splitter - Web Dashboard")
    print("=" * 60)
    print(f"\n  🌐 Open your browser to: http://localhost:5001")
    print(f"\n  Press Ctrl+C to stop the server\n")
    print("=" * 60)
    
    app.run(debug=False, host='0.0.0.0', port=5001, threaded=True)
