# Harmonix Audio Splitter - Complete Documentation

**Version:** 1.0.0  
**Last Updated:** December 30, 2025  
**Author:** Stephane El Khoury  
**Repository:** Audio-Splitter-Stems-Harmonix

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Requirements](#2-system-requirements)
3. [Installation Guide](#3-installation-guide)
4. [Architecture](#4-architecture)
5. [Project Structure](#5-project-structure)
6. [Configuration](#6-configuration)
7. [Authentication System](#7-authentication-system)
8. [API Reference](#8-api-reference)
9. [Frontend Design System](#9-frontend-design-system)
10. [Dashboard Application](#10-dashboard-application)
11. [Audio Processing](#11-audio-processing)
12. [Database Schema](#12-database-schema)
13. [Deployment](#13-deployment)
14. [Troubleshooting](#14-troubleshooting)
15. [Changelog](#15-changelog)

---

## 1. Project Overview

### 1.1 Description

Harmonix Audio Splitter is a professional AI-powered audio stem separation application. It uses advanced machine learning models (Demucs) to separate audio tracks into individual stems (vocals, drums, bass, guitar, piano, other instruments).

### 1.2 Key Features

- **AI-Powered Stem Separation**: Uses Facebook's Demucs model for high-quality audio separation
- **Multiple Separation Modes**:
  - Grouped (4 stems): Vocals, Drums, Bass, Other
  - Karaoke (2 stems): Vocals, Instrumental
  - Per-Instrument (6+ stems): Detailed separation including guitar, piano
- **Quality Modes**:
  - Fast: Quick processing for previews
  - Balanced: Recommended for most use cases
  - Studio: Highest quality, multiple processing passes
- **Lyrics Extraction**: AI-powered lyrics transcription with word-level timing
- **Music Analysis**: BPM detection, key detection, time signature analysis
- **Real-time Pitch Shifting**: Transpose audio in real-time using Tone.js
- **Multi-track Player**: Synchronized playback with individual stem controls
- **User Authentication**: Secure login system with role-based access
- **Subscription Plans**: Free, Creator, and Studio tiers

### 1.3 Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.13, Flask 3.0+ |
| Frontend | HTML5, CSS3, JavaScript (ES6+) |
| AI/ML | Demucs, Whisper (lyrics) |
| Audio Libraries | WaveSurfer.js, Tone.js |
| Authentication | PBKDF2 password hashing |
| Data Storage | JSON file-based |
| Containerization | Docker, Docker Compose |

---

## 2. System Requirements

### 2.1 Minimum Requirements

- **OS**: macOS 10.15+, Ubuntu 20.04+, Windows 10+
- **Python**: 3.10 or higher (3.13 recommended)
- **RAM**: 8GB minimum
- **Storage**: 10GB free space
- **CPU**: Multi-core processor (4+ cores recommended)

### 2.2 Recommended Requirements

- **RAM**: 16GB or more
- **GPU**: NVIDIA GPU with CUDA support (for faster processing)
- **Storage**: SSD with 50GB+ free space
- **CPU**: 8+ cores

### 2.3 Dependencies

```
Flask>=3.0.0
Werkzeug>=3.0.0
demucs>=4.0.0
torch>=2.0.0
torchaudio>=2.0.0
openai-whisper>=20231117
yt-dlp>=2023.11.16
librosa>=0.10.0
soundfile>=0.12.1
numpy>=1.24.0
pyyaml>=6.0
```

---

## 3. Installation Guide

### 3.1 Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/Audio-Splitter-Stems-Harmonix.git
cd Audio-Splitter-Stems-Harmonix

# Run the quickstart script
chmod +x quickstart.sh
./quickstart.sh
```

### 3.2 Manual Installation

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .

# Run the application
python run_dashboard.py
```

### 3.3 Docker Installation

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t harmonix-splitter .
docker run -p 5001:5001 harmonix-splitter
```

### 3.4 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment mode | `development` |
| `PORT` | Server port | `5001` |
| `SECRET_KEY` | Session secret key | Auto-generated |
| `UPLOAD_FOLDER` | Upload directory | `data/uploads` |
| `OUTPUT_FOLDER` | Output directory | `data/outputs` |

---

## 4. Architecture

### 4.1 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Landing   │  │    Auth     │  │     Dashboard       │ │
│  │   Pages     │  │   Pages     │  │   (Stem Player)     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Flask Backend                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Routes    │  │    Auth     │  │   Audio Processor   │ │
│  │  (API)      │  │  Service    │  │     (Demucs)        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Data Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  users.json │  │   Uploads   │  │   Processed Stems   │ │
│  │  (Auth DB)  │  │   Storage   │  │      Storage        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Request Flow

1. User uploads audio file or provides URL
2. Backend validates and stores the file
3. Demucs processes the audio and separates stems
4. Stems are saved to user's output directory
5. Frontend fetches job status and stem data
6. User plays/downloads individual stems

---

## 5. Project Structure

```
Audio-Splitter-Stems-Harmonix/
├── src/
│   └── harmonix_splitter/
│       ├── __init__.py              # Package initialization
│       ├── auth.py                  # Authentication module
│       ├── cli.py                   # Command-line interface
│       ├── dashboard.py             # Main Flask application
│       │
│       ├── analysis/                # Audio analysis modules
│       │   ├── __init__.py
│       │   ├── detector.py          # Music feature detection
│       │   └── music_analyzer.py    # BPM, key analysis
│       │
│       ├── api/                     # API endpoints
│       │   ├── __init__.py
│       │   └── main.py              # REST API routes
│       │
│       ├── audio/                   # Audio processing
│       │   ├── __init__.py
│       │   ├── lyrics.py            # Lyrics extraction
│       │   └── processor.py         # Audio file processing
│       │
│       ├── config/                  # Configuration
│       │   └── settings.py          # App settings
│       │
│       ├── core/                    # Core functionality
│       │   ├── __init__.py
│       │   ├── orchestrator.py      # Job orchestration
│       │   ├── preprocessor.py      # Audio preprocessing
│       │   └── separator.py         # Stem separation
│       │
│       ├── static/                  # Static assets
│       │   ├── css/
│       │   │   ├── variables.css    # CSS variables
│       │   │   ├── base.css         # Base styles
│       │   │   ├── layout.css       # Layout styles
│       │   │   ├── components.css   # UI components
│       │   │   ├── animations.css   # Animations
│       │   │   └── pages/
│       │   │       ├── landing.css  # Landing page
│       │   │       └── dashboard.css # Dashboard styles
│       │   ├── js/
│       │   │   ├── main.js          # Main JavaScript
│       │   │   ├── theme.js         # Theme switching
│       │   │   ├── navigation.js    # Navigation
│       │   │   └── animations.js    # Animations
│       │   └── images/              # Image assets
│       │
│       └── templates/               # Jinja2 templates
│           ├── base.html            # Base template
│           ├── landing.html         # Home page
│           ├── dashboard.html       # Main app dashboard
│           ├── login.html           # Login page
│           ├── register.html        # Registration page
│           ├── account.html         # Account settings
│           ├── admin.html           # Admin panel
│           ├── features.html        # Features page
│           ├── pricing.html         # Pricing page
│           ├── docs.html            # Documentation
│           ├── tutorials.html       # Tutorials
│           ├── about.html           # About page
│           ├── contact.html         # Contact page
│           ├── blog.html            # Blog page
│           ├── community.html       # Community page
│           ├── privacy.html         # Privacy policy
│           └── terms.html           # Terms of service
│
├── config/
│   └── config.yaml                  # Application configuration
│
├── data/
│   ├── users.json                   # User database
│   ├── uploads/                     # Uploaded files
│   ├── outputs/                     # Processed stems
│   │   └── users/                   # Per-user output
│   └── temp/                        # Temporary files
│
├── logs/                            # Application logs
├── models/                          # ML model cache
├── tests/                           # Test suite
│
├── docker-compose.yml               # Docker Compose config
├── Dockerfile                       # Docker image definition
├── pyproject.toml                   # Python project config
├── requirements.txt                 # Python dependencies
├── run_dashboard.py                 # Application entry point
├── quickstart.sh                    # Quick start script
├── start.sh                         # Start script
└── README.md                        # Project readme
```

---

## 6. Configuration

### 6.1 config/config.yaml

```yaml
# Application Configuration
app:
  name: "Harmonix Audio Splitter"
  version: "1.0.0"
  debug: false
  secret_key: "your-secret-key-here"

# Server Configuration
server:
  host: "0.0.0.0"
  port: 5001
  workers: 4

# Audio Processing
audio:
  max_file_size: 524288000  # 500MB
  allowed_extensions:
    - mp3
    - wav
    - flac
    - m4a
    - ogg
    - aac
  
  # Demucs settings
  demucs:
    model: "htdemucs"
    device: "auto"  # auto, cpu, cuda
    shifts: 1
    overlap: 0.25

# Storage
storage:
  upload_folder: "data/uploads"
  output_folder: "data/outputs"
  temp_folder: "data/temp"
  max_storage_per_user: 10737418240  # 10GB

# Authentication
auth:
  session_lifetime: 86400  # 24 hours
  password_min_length: 8
  max_login_attempts: 5

# Plans
plans:
  free:
    name: "Free"
    songs_per_month: 3
    max_file_size: 52428800  # 50MB
    stems: 4
    
  creator:
    name: "Creator"
    songs_per_month: 50
    max_file_size: 209715200  # 200MB
    stems: 6
    price: 9.99
    
  studio:
    name: "Studio"
    songs_per_month: -1  # Unlimited
    max_file_size: 524288000  # 500MB
    stems: 6
    price: 19.99
```

### 6.2 Environment-Specific Settings

Development settings are automatically applied when `FLASK_ENV=development`.

---

## 7. Authentication System

### 7.1 Overview

The authentication system uses a JSON file-based storage with PBKDF2 password hashing.

### 7.2 User Data Structure

**Location:** `data/users.json`

```json
{
  "users": {
    "user_id_hash": {
      "id": "unique_user_id",
      "username": "johndoe",
      "email": "john@example.com",
      "name": "John Doe",
      "password_hash": "pbkdf2:sha256:...",
      "role": "user",
      "plan": "free",
      "created_at": "2025-12-30T10:00:00Z",
      "last_login": "2025-12-30T15:30:00Z",
      "usage": {
        "songs_this_month": 2,
        "month_start": "2025-12-01"
      }
    }
  }
}
```

### 7.3 Password Hashing

```python
from werkzeug.security import generate_password_hash, check_password_hash

# Hash password
hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

# Verify password
is_valid = check_password_hash(stored_hash, provided_password)
```

### 7.4 Session Management

Sessions are managed using Flask's built-in session with secure cookies.

```python
from flask import session

# Set session
session['user_id'] = user.id
session['user_email'] = user.email

# Check authentication
@login_required
def protected_route():
    user = get_current_user()
    ...
```

### 7.5 Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@harmonix.app | admin123 |

---

## 8. API Reference

### 8.1 Authentication Endpoints

#### POST /login
Authenticate user and create session.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Login successful",
  "redirect": "/dashboard"
}
```

#### POST /register
Create new user account.

**Request:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword"
}
```

#### GET /logout
End user session.

---

### 8.2 Audio Processing Endpoints

#### POST /upload
Upload audio file for processing.

**Request (multipart/form-data):**
- `file`: Audio file (mp3, wav, flac, m4a, ogg)
- `quality`: "fast" | "balanced" | "studio"
- `mode`: "grouped" | "karaoke" | "per_instrument"
- `output_name`: Optional custom name

**Response (200):**
```json
{
  "job_id": "uuid-string",
  "status": "processing",
  "message": "Upload successful"
}
```

#### POST /upload-url
Process audio from URL (YouTube, SoundCloud, etc.)

**Request:**
```json
{
  "url": "https://youtube.com/watch?v=...",
  "quality": "balanced",
  "mode": "grouped",
  "output_name": "My Track"
}
```

#### GET /status/{job_id}
Get processing status.

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "processing",
  "progress": 65,
  "message": "Separating stems..."
}
```

#### GET /jobs
List all user's jobs.

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "uuid-string",
      "filename": "song.mp3",
      "display_name": "My Song",
      "status": "completed",
      "created_at": "2025-12-30T15:00:00Z",
      "stems": {
        "vocals": "/path/to/vocals.wav",
        "drums": "/path/to/drums.wav",
        "bass": "/path/to/bass.wav",
        "other": "/path/to/other.wav"
      },
      "has_lyrics": true
    }
  ]
}
```

#### GET /download/{job_id}/{stem_name}
Download a specific stem.

**Response:** Audio file (WAV)

#### DELETE /delete/{job_id}
Delete a job and all associated files.

---

### 8.3 Lyrics & Analysis Endpoints

#### POST /extract-lyrics/{job_id}
Extract lyrics from vocals stem.

**Request:**
```json
{
  "language": "auto"  // or "en", "ar", "fr", "es"
}
```

**Response:**
```json
{
  "available": true,
  "language": "en",
  "lines": [
    {
      "start": 0.5,
      "end": 2.3,
      "text": "Hello world",
      "words": [
        {"word": "Hello", "start": 0.5, "end": 1.2},
        {"word": "world", "start": 1.3, "end": 2.3}
      ]
    }
  ]
}
```

#### GET /lyrics/{job_id}
Get cached lyrics for a job.

#### GET /analyze/{job_id}
Get music analysis (BPM, key, time signature).

**Response:**
```json
{
  "tempo": {
    "bpm": 120,
    "confidence": 0.95
  },
  "key": {
    "key": "C",
    "mode": "major",
    "confidence": 0.87
  },
  "time_signature": {
    "time_signature": "4/4"
  }
}
```

---

### 8.4 User & Plan Endpoints

#### GET /api/plan-info
Get current user's plan and usage.

**Response:**
```json
{
  "plan": "creator",
  "plan_details": {
    "name": "Creator",
    "songs_per_month": 50,
    "max_file_size": 209715200
  },
  "usage": {
    "used": 12,
    "limit": 50,
    "reset_date": "2026-01-01"
  },
  "is_admin": false
}
```

---

## 9. Frontend Design System

### 9.1 CSS Architecture

The design system follows a modular approach with separation of concerns:

```
static/css/
├── variables.css    # Design tokens (colors, spacing, etc.)
├── base.css         # Reset and base styles
├── layout.css       # Layout components (navbar, footer, grid)
├── components.css   # Reusable UI components
├── animations.css   # Animation definitions
└── pages/
    ├── landing.css  # Landing page specific
    └── dashboard.css # Dashboard specific
```

### 9.2 Design Tokens (variables.css)

#### Color Palette

```css
:root {
    /* Primary Colors */
    --primary: #7c3aed;        /* Purple */
    --primary-light: #a78bfa;
    --primary-dark: #6d28d9;
    
    /* Secondary Colors */
    --secondary: #06b6d4;      /* Cyan */
    --secondary-light: #22d3ee;
    --secondary-dark: #0891b2;
    
    /* Accent Colors */
    --accent: #10b981;         /* Green */
    --accent-light: #34d399;
    --accent-dark: #059669;
    
    /* Status Colors */
    --success: #10b981;
    --warning: #f59e0b;
    --error: #ef4444;
    --info: #3b82f6;
    
    /* Stem Colors */
    --stem-vocals: #ef4444;
    --stem-drums: #f59e0b;
    --stem-bass: #8b5cf6;
    --stem-other: #06b6d4;
    --stem-guitar: #10b981;
    --stem-piano: #ec4899;
}
```

#### Dark Theme (Default)

```css
:root {
    --bg-dark: #0a0a0f;
    --bg-darker: #050508;
    --bg-card: #12121a;
    --bg-input: #0d0d12;
    
    --text: #ffffff;
    --text-muted: #a1a1aa;
    --text-dim: #71717a;
    
    --border: rgba(255, 255, 255, 0.1);
}
```

#### Light Theme

```css
[data-theme="light"] {
    --bg-dark: #ffffff;
    --bg-darker: #f1f5f9;
    --bg-card: #ffffff;
    --bg-input: #f8fafc;
    
    --text: #0f172a;
    --text-muted: #475569;
    --text-dim: #64748b;
    
    --border: rgba(0, 0, 0, 0.1);
}
```

### 9.3 Typography

```css
:root {
    --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
    
    --font-size-xs: 11px;
    --font-size-sm: 13px;
    --font-size-base: 15px;
    --font-size-lg: 18px;
    --font-size-xl: 22px;
    --font-size-2xl: 28px;
    --font-size-3xl: 36px;
    --font-size-4xl: 48px;
}
```

### 9.4 Spacing Scale

```css
:root {
    --space-xs: 4px;
    --space-sm: 8px;
    --space-md: 16px;
    --space-lg: 24px;
    --space-xl: 32px;
    --space-2xl: 48px;
    --space-3xl: 64px;
    --space-4xl: 96px;
}
```

### 9.5 Component Classes

#### Buttons

```html
<button class="btn btn-primary">Primary Button</button>
<button class="btn btn-secondary">Secondary Button</button>
<button class="btn btn-ghost">Ghost Button</button>
<button class="btn btn-primary btn-lg">Large Button</button>
```

#### Cards

```html
<div class="card">
    <div class="card-header">
        <h3 class="card-title">Title</h3>
        <p class="card-description">Description</p>
    </div>
    <!-- Content -->
</div>
```

#### Forms

```html
<div class="form-group">
    <label class="form-label">Email</label>
    <input type="email" class="form-control" placeholder="Enter email">
</div>
```

#### Badges

```html
<span class="badge badge-primary">New</span>
<span class="badge badge-success">Active</span>
<span class="badge badge-warning">Pending</span>
```

---

## 10. Dashboard Application

### 10.1 Overview

The dashboard is a single-page application with four main sections:
1. **Library**: View and manage processed tracks
2. **Upload & Process**: Upload new audio files
3. **Player**: Multi-track stem player
4. **Statistics**: Usage statistics

### 10.2 Stem Player Features

- **Synchronized Playback**: All stems play in perfect sync
- **Individual Controls**: Mute, solo, volume per stem
- **Global Timeline**: Click/drag to seek
- **Waveform Display**: Visual waveform for each stem
- **Real-time Pitch Shifting**: -4 to +4 semitones
- **Lyrics Display**: Synced lyrics with word highlighting
- **Music Info**: BPM, key, time signature display

### 10.3 Player State Management

```javascript
// State variables
let wavesurfers = {};      // WaveSurfer instances per stem
let isPlaying = false;     // Playback state
let masterTime = 0;        // Current playback time
let masterDuration = 0;    // Total duration
let soloStems = new Set(); // Soloed stems
let mutedStems = new Set(); // Muted stems
let currentPitch = 0;      // Pitch shift in semitones
```

### 10.4 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Play/Pause |
| Escape | Close modals |

---

## 11. Audio Processing

### 11.1 Demucs Integration

The application uses Facebook's Demucs model for stem separation.

#### Available Models

| Model | Stems | Quality | Speed |
|-------|-------|---------|-------|
| htdemucs | 4 | High | Medium |
| htdemucs_ft | 4 | Higher | Slow |
| htdemucs_6s | 6 | High | Medium |

#### Processing Pipeline

1. **Upload/Download**: Audio file received
2. **Preprocessing**: Convert to compatible format
3. **Separation**: Demucs separates stems
4. **Post-processing**: Normalize and save stems
5. **Analysis**: Extract BPM, key (optional)
6. **Cleanup**: Remove temporary files

### 11.2 Quality Modes

| Mode | Shifts | Overlap | Description |
|------|--------|---------|-------------|
| Fast | 0 | 0.1 | Quick preview |
| Balanced | 1 | 0.25 | Recommended |
| Studio | 5 | 0.5 | Best quality |

### 11.3 Lyrics Extraction

Uses OpenAI's Whisper model for speech-to-text:

```python
import whisper

model = whisper.load_model("base")
result = model.transcribe(
    vocals_path,
    language=language,
    word_timestamps=True
)
```

---

## 12. Database Schema

### 12.1 Users (data/users.json)

```json
{
  "users": {
    "<user_id>": {
      "id": "string",
      "username": "string",
      "email": "string",
      "name": "string",
      "password_hash": "string",
      "role": "user | admin",
      "plan": "free | creator | studio",
      "created_at": "ISO 8601 datetime",
      "last_login": "ISO 8601 datetime",
      "usage": {
        "songs_this_month": "integer",
        "month_start": "ISO 8601 date"
      }
    }
  }
}
```

### 12.2 Job Metadata

Job data is stored in the filesystem:

```
data/outputs/users/<user_id>/<job_id>/
├── metadata.json
├── vocals.wav
├── drums.wav
├── bass.wav
├── other.wav
├── lyrics.json (optional)
└── analysis.json (optional)
```

**metadata.json:**
```json
{
  "job_id": "uuid",
  "user_id": "string",
  "filename": "original.mp3",
  "display_name": "Custom Name",
  "status": "completed",
  "created_at": "ISO 8601",
  "quality": "balanced",
  "mode": "grouped",
  "stems": ["vocals", "drums", "bass", "other"],
  "has_lyrics": true,
  "duration": 180.5
}
```

---

## 13. Deployment

### 13.1 Docker Deployment

```bash
# Build image
docker build -t harmonix-splitter:latest .

# Run container
docker run -d \
  --name harmonix \
  -p 5001:5001 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  harmonix-splitter:latest
```

### 13.2 Docker Compose

```yaml
version: '3.8'
services:
  harmonix:
    build: .
    ports:
      - "5001:5001"
    volumes:
      - ./data:/app/data
      - ./models:/app/models
      - ./logs:/app/logs
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
    restart: unless-stopped
```

### 13.3 Production Considerations

1. **Use a production WSGI server** (gunicorn, uWSGI)
2. **Enable HTTPS** with SSL certificates
3. **Set secure session cookies**
4. **Configure proper logging**
5. **Set up backup for user data**
6. **Monitor disk space** (audio files are large)

### 13.4 Nginx Configuration

```nginx
server {
    listen 80;
    server_name harmonix.app;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name harmonix.app;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    client_max_body_size 500M;
    
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /app/src/harmonix_splitter/static;
        expires 1d;
    }
}
```

---

## 14. Troubleshooting

### 14.1 Common Issues

#### Login Not Working

**Symptom:** "Invalid email or password" error

**Solutions:**
1. Check that the email field name is `email` (not `username`)
2. Verify user exists in `data/users.json`
3. Reset password:
```python
from werkzeug.security import generate_password_hash
hash = generate_password_hash('newpassword')
# Update in users.json
```

#### CSS Not Loading / Form Inputs Invisible

**Symptom:** Form fields appear transparent or have no styling

**Solutions:**
1. Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+R)
2. Clear browser cache
3. Check that CSS files are being served (check Network tab)
4. Verify `--bg-input` variable is defined in variables.css

#### Audio Processing Fails

**Symptom:** Job stuck at "processing" or fails

**Solutions:**
1. Check available disk space
2. Verify Demucs is installed: `python -c "import demucs"`
3. Check logs: `tail -f logs/harmonix.log`
4. Ensure sufficient RAM (8GB minimum)

#### Out of Memory

**Symptom:** Python process killed during separation

**Solutions:**
1. Use `fast` quality mode for large files
2. Increase swap space
3. Process shorter audio clips
4. Use GPU if available

### 14.2 Debug Mode

Enable debug logging:

```python
# In dashboard.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 14.3 Log Files

- Application logs: `logs/harmonix.log`
- Flask debug: Console output when `debug=True`

---

## 15. Changelog

### Version 1.0.0 (December 30, 2025)

#### Features
- Initial release of Harmonix Audio Splitter
- AI-powered stem separation using Demucs
- Multi-track synchronized player with WaveSurfer.js
- Real-time pitch shifting with Tone.js
- Lyrics extraction with word-level timing
- Music analysis (BPM, key, time signature)
- User authentication with role-based access
- Subscription plans (Free, Creator, Studio)
- Dark/Light theme support
- Responsive design for all devices

#### Design System
- Modular CSS architecture
- Consistent color palette (Purple/Cyan theme)
- Unified form input styling across all pages
- Smooth animations and transitions

#### Pages
- Landing page with hero section
- Features showcase
- Pricing plans
- Documentation
- Tutorials
- Blog
- Community
- About
- Contact with form
- Privacy Policy
- Terms of Service
- Login/Register
- Account Management
- Admin Panel
- Dashboard (stem separation app)

#### Known Issues
- Dashboard is currently a standalone page (not integrated with base template)
- GPU acceleration requires manual configuration
- Large files (>300MB) may timeout on slower systems

---

## Support

For issues and feature requests, please contact:
- **Email:** support@harmonix.app
- **GitHub Issues:** [Repository Issues](https://github.com/yourusername/Audio-Splitter-Stems-Harmonix/issues)

---

**© 2025 Harmonix. All rights reserved.**
