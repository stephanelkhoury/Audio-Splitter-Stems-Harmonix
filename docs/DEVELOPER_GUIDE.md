# Developer Guide

**Version:** 1.0.0  
**Last Updated:** December 30, 2025  
**Author:** Stephane El Khoury

---

## Table of Contents

1. [Development Setup](#1-development-setup)
2. [Code Architecture](#2-code-architecture)
3. [Adding New Features](#3-adding-new-features)
4. [Frontend Development](#4-frontend-development)
5. [Backend Development](#5-backend-development)
6. [Testing](#6-testing)
7. [Code Style Guide](#7-code-style-guide)
8. [Git Workflow](#8-git-workflow)
9. [Debugging](#9-debugging)
10. [Performance Optimization](#10-performance-optimization)

---

## 1. Development Setup

### 1.1 Prerequisites

- Python 3.10+ (3.13 recommended)
- Node.js 18+ (optional, for frontend tooling)
- Git
- VS Code (recommended) with extensions:
  - Python
  - Pylance
  - GitLens
  - Live Server

### 1.2 Clone and Setup

```bash
# Clone repository
git clone https://github.com/yourusername/Audio-Splitter-Stems-Harmonix.git
cd Audio-Splitter-Stems-Harmonix

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Install package in editable mode
pip install -e .

# Download ML models (first run will auto-download)
python -c "import demucs; import whisper"
```

### 1.3 Environment Configuration

Create a `.env` file in the project root:

```env
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-secret-key-change-in-production
PORT=5001
```

### 1.4 Running the Development Server

```bash
# Method 1: Direct run
python run_dashboard.py

# Method 2: Flask CLI
export FLASK_APP=src/harmonix_splitter/dashboard.py
flask run --port 5001 --debug

# Method 3: Use the start script
./start_dashboard.sh
```

The server will be available at: `http://localhost:5001`

### 1.5 VS Code Configuration

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.analysis.typeCheckingMode": "basic",
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "files.associations": {
        "*.html": "jinja-html"
    },
    "emmet.includeLanguages": {
        "jinja-html": "html"
    }
}
```

---

## 2. Code Architecture

### 2.1 Module Overview

```
src/harmonix_splitter/
├── __init__.py          # Package init, version info
├── auth.py              # Authentication logic
├── cli.py               # Command-line interface
├── dashboard.py         # Main Flask app & routes
│
├── analysis/            # Audio analysis
│   ├── detector.py      # Feature detection
│   └── music_analyzer.py # BPM, key detection
│
├── api/                 # REST API
│   └── main.py          # API routes
│
├── audio/               # Audio processing
│   ├── lyrics.py        # Whisper integration
│   └── processor.py     # Audio file handling
│
├── config/              # Configuration
│   └── settings.py      # Settings management
│
└── core/                # Core functionality
    ├── orchestrator.py  # Job orchestration
    ├── preprocessor.py  # Audio preprocessing
    └── separator.py     # Demucs wrapper
```

### 2.2 Request Flow

```
Request → Flask Route → Service Layer → Data Layer → Response
             ↓
    dashboard.py     auth.py/processor.py    users.json/filesystem
```

### 2.3 Key Classes

#### DashboardApp (dashboard.py)

Main Flask application class handling routes and configuration.

```python
class DashboardApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_routes()
        self.setup_auth()
        
    def setup_routes(self):
        # Define all routes
        pass
```

#### AudioProcessor (audio/processor.py)

Handles audio file operations.

```python
class AudioProcessor:
    def validate_file(self, file) -> bool
    def save_upload(self, file, user_id) -> str
    def get_audio_info(self, file_path) -> dict
```

#### StemSeparator (core/separator.py)

Wraps Demucs for stem separation.

```python
class StemSeparator:
    def __init__(self, model="htdemucs", device="auto"):
        self.model = model
        self.device = device
        
    def separate(self, input_path, output_dir, quality="balanced"):
        # Run Demucs separation
        pass
```

---

## 3. Adding New Features

### 3.1 Adding a New Page

1. **Create the template** in `templates/`:

```html
<!-- templates/newpage.html -->
{% extends "base.html" %}

{% block title %}New Page - Harmonix{% endblock %}

{% block content %}
<main class="page-content">
    <h1>New Page</h1>
</main>
{% endblock %}
```

2. **Add the route** in `dashboard.py`:

```python
@app.route('/newpage')
def newpage():
    return render_template('newpage.html')
```

3. **Add navigation link** in `base.html`:

```html
<a href="{{ url_for('newpage') }}" class="nav-link">New Page</a>
```

### 3.2 Adding a New API Endpoint

1. **Define the route** in `dashboard.py`:

```python
@app.route('/api/new-endpoint', methods=['POST'])
@login_required
def new_endpoint():
    data = request.get_json()
    
    # Validate input
    if not data.get('required_field'):
        return jsonify({'error': 'Missing field'}), 400
    
    # Process request
    result = process_data(data)
    
    return jsonify({
        'success': True,
        'data': result
    })
```

2. **Document the endpoint** in `docs/API_REFERENCE.md`

### 3.3 Adding a New CSS Component

1. **Add to `components.css`**:

```css
/* New Card Variant */
.card-highlight {
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
    border-radius: var(--radius-xl);
    padding: var(--space-xl);
    color: white;
}

.card-highlight .card-title {
    font-size: var(--font-size-2xl);
    font-weight: 700;
}
```

2. **Add light theme variant**:

```css
[data-theme="light"] .card-highlight {
    box-shadow: 0 4px 20px rgba(124, 58, 237, 0.2);
}
```

### 3.4 Adding a New Stem Type

1. **Update separator.py**:

```python
STEM_COLORS = {
    'vocals': '#ef4444',
    'drums': '#f59e0b',
    'bass': '#8b5cf6',
    'other': '#06b6d4',
    'guitar': '#10b981',
    'piano': '#ec4899',
    'newtype': '#ff6b6b',  # Add new stem
}
```

2. **Update frontend stem handling** in `dashboard.html`:

```javascript
const STEM_CONFIG = {
    // ... existing stems
    newtype: {
        icon: 'fa-music',
        color: '#ff6b6b',
        label: 'New Type'
    }
};
```

3. **Update CSS variables**:

```css
:root {
    --stem-newtype: #ff6b6b;
}
```

---

## 4. Frontend Development

### 4.1 CSS Architecture

We use a modular CSS approach:

| File | Purpose |
|------|---------|
| `variables.css` | Design tokens (colors, spacing, fonts) |
| `base.css` | Reset, typography, global styles |
| `layout.css` | Navbar, footer, grid, containers |
| `components.css` | Buttons, cards, forms, badges |
| `animations.css` | Keyframes and transitions |
| `pages/*.css` | Page-specific styles |

### 4.2 CSS Naming Convention

We use a simplified BEM-like approach:

```css
/* Block */
.card { }

/* Element */
.card-header { }
.card-title { }
.card-body { }

/* Modifier */
.card-primary { }
.card-lg { }
```

### 4.3 JavaScript Organization

```javascript
// Theme management (theme.js)
function initTheme() { }
function toggleTheme() { }

// Navigation (navigation.js)
function initNavigation() { }
function setupMobileMenu() { }

// Main functionality (main.js)
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initNavigation();
    initAnimations();
});
```

### 4.4 Adding JavaScript Features

```javascript
// Use vanilla JS, no frameworks required
// Follow this pattern:

class NewFeature {
    constructor(options) {
        this.options = options;
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.render();
    }
    
    bindEvents() {
        document.addEventListener('click', this.handleClick.bind(this));
    }
    
    handleClick(e) {
        // Handle event
    }
    
    render() {
        // Update DOM
    }
}

// Initialize
new NewFeature({ container: '#my-container' });
```

### 4.5 Working with Jinja2 Templates

**Template Inheritance:**

```html
<!-- base.html -->
<!DOCTYPE html>
<html>
<head>
    {% block head %}
    <title>{% block title %}Harmonix{% endblock %}</title>
    {% endblock %}
</head>
<body>
    {% block content %}{% endblock %}
    {% block scripts %}{% endblock %}
</body>
</html>

<!-- child.html -->
{% extends "base.html" %}

{% block title %}Child Page{% endblock %}

{% block content %}
<main>Content here</main>
{% endblock %}
```

**Passing Data:**

```python
# Route
@app.route('/page')
def page():
    return render_template('page.html', 
        user=current_user,
        items=get_items()
    )
```

```html
<!-- Template -->
<h1>Hello, {{ user.name }}</h1>
{% for item in items %}
    <div class="item">{{ item.title }}</div>
{% endfor %}
```

---

## 5. Backend Development

### 5.1 Route Decorators

```python
from functools import wraps
from flask import session, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_admin():
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated
```

### 5.2 Error Handling

```python
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    app.logger.error(f'Server Error: {error}')
    return jsonify({'error': 'Internal server error'}), 500
```

### 5.3 Background Jobs

For long-running tasks like stem separation:

```python
import threading
import queue

job_queue = queue.Queue()

def process_job(job_id, file_path, options):
    """Run in background thread"""
    try:
        update_status(job_id, 'processing', 0)
        
        # Separation
        separator = StemSeparator()
        separator.separate(file_path, get_output_dir(job_id))
        
        update_status(job_id, 'completed', 100)
    except Exception as e:
        update_status(job_id, 'failed', 0, str(e))

def queue_job(job_id, file_path, options):
    thread = threading.Thread(
        target=process_job,
        args=(job_id, file_path, options)
    )
    thread.start()
```

### 5.4 Database Operations

Currently using JSON files. For operations:

```python
import json
from pathlib import Path

DATA_DIR = Path('data')
USERS_FILE = DATA_DIR / 'users.json'

def load_users():
    if USERS_FILE.exists():
        return json.loads(USERS_FILE.read_text())
    return {'users': {}}

def save_users(data):
    USERS_FILE.write_text(json.dumps(data, indent=2))

def get_user(user_id):
    users = load_users()
    return users['users'].get(user_id)

def update_user(user_id, updates):
    users = load_users()
    if user_id in users['users']:
        users['users'][user_id].update(updates)
        save_users(users)
```

---

## 6. Testing

### 6.1 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/harmonix_splitter

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::test_upload_file

# Verbose output
pytest -v
```

### 6.2 Test Structure

```python
# tests/test_api.py
import pytest
from harmonix_splitter.dashboard import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    """Test home page loads"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Harmonix' in response.data

def test_login_required(client):
    """Test dashboard requires login"""
    response = client.get('/dashboard')
    assert response.status_code == 302  # Redirect to login

def test_upload_no_file(client):
    """Test upload without file returns error"""
    # Login first
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    response = client.post('/upload')
    assert response.status_code == 400
    assert b'No file' in response.data
```

### 6.3 Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
import tempfile
import shutil
from pathlib import Path

@pytest.fixture(scope='session')
def test_data_dir():
    """Create temporary test data directory"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_audio(test_data_dir):
    """Create sample audio file for testing"""
    import numpy as np
    import soundfile as sf
    
    # Generate 1 second of silence
    audio = np.zeros(44100)
    path = test_data_dir / 'sample.wav'
    sf.write(path, audio, 44100)
    return path
```

---

## 7. Code Style Guide

### 7.1 Python Style

We follow PEP 8 with these additions:

```python
# Imports: stdlib, third-party, local
import os
import json
from pathlib import Path

import flask
from werkzeug.security import generate_password_hash

from harmonix_splitter.auth import login_required
from harmonix_splitter.config import settings

# Constants: UPPER_SNAKE_CASE
MAX_FILE_SIZE = 500 * 1024 * 1024
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac'}

# Classes: PascalCase
class AudioProcessor:
    """Process audio files for stem separation."""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
    
    def process(self, file_path: str) -> dict:
        """
        Process an audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            dict with processing results
        """
        pass

# Functions: snake_case
def validate_audio_file(file_path: str) -> bool:
    """Validate that file is a supported audio format."""
    pass
```

### 7.2 CSS Style

```css
/* Use CSS custom properties */
:root {
    --color-primary: #7c3aed;
}

/* Component-based organization */
/* =============================
   Button Component
   ============================= */

.btn {
    display: inline-flex;
    align-items: center;
    gap: var(--space-sm);
}

/* State modifiers */
.btn:hover { }
.btn:active { }
.btn:disabled { }

/* Size variants */
.btn-sm { }
.btn-lg { }

/* Color variants */
.btn-primary { }
.btn-secondary { }
```

### 7.3 JavaScript Style

```javascript
// Use const/let, not var
const MAX_FILE_SIZE = 500 * 1024 * 1024;
let currentState = null;

// Use arrow functions for callbacks
items.forEach(item => processItem(item));

// Use template literals
const message = `Processing ${filename}...`;

// Use async/await
async function fetchData() {
    try {
        const response = await fetch('/api/data');
        return await response.json();
    } catch (error) {
        console.error('Fetch failed:', error);
        throw error;
    }
}

// Document functions
/**
 * Process an audio file
 * @param {File} file - The audio file to process
 * @param {Object} options - Processing options
 * @returns {Promise<Object>} Processing result
 */
async function processAudio(file, options = {}) {
    // ...
}
```

---

## 8. Git Workflow

### 8.1 Branch Naming

```
feature/add-youtube-download
bugfix/fix-login-redirect
hotfix/security-patch
docs/update-api-reference
refactor/cleanup-auth-module
```

### 8.2 Commit Messages

Follow conventional commits:

```
feat: add YouTube URL download support
fix: resolve login redirect issue on Safari
docs: update API documentation
style: format CSS files with prettier
refactor: extract audio validation to separate module
test: add tests for stem separation
chore: update dependencies
```

### 8.3 Pull Request Process

1. Create feature branch from `main`
2. Make changes with clear commits
3. Run tests locally: `pytest`
4. Push and create PR
5. Fill in PR template
6. Request review
7. Address feedback
8. Squash and merge

### 8.4 Pre-commit Hooks

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
```

Install: `pip install pre-commit && pre-commit install`

---

## 9. Debugging

### 9.1 Flask Debug Mode

```python
# Enable debug mode
app.run(debug=True)

# Or via environment
export FLASK_DEBUG=1
```

### 9.2 Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Usage
logger.debug('Processing file: %s', filename)
logger.info('Job completed: %s', job_id)
logger.error('Failed to process: %s', error)
```

### 9.3 Browser DevTools

- **Network tab**: Check API requests/responses
- **Console**: View JavaScript errors
- **Elements**: Inspect DOM and styles
- **Application**: Check cookies and session

### 9.4 VS Code Debugging

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Flask",
            "type": "python",
            "request": "launch",
            "module": "flask",
            "env": {
                "FLASK_APP": "src/harmonix_splitter/dashboard.py",
                "FLASK_DEBUG": "1"
            },
            "args": ["run", "--port", "5001"],
            "jinja": true
        },
        {
            "name": "Pytest",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["-v"]
        }
    ]
}
```

---

## 10. Performance Optimization

### 10.1 Audio Processing

```python
# Use GPU if available
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# Batch process smaller chunks
def process_large_file(file_path, chunk_duration=300):
    """Process files in 5-minute chunks"""
    pass

# Use multiprocessing for analysis
from multiprocessing import Pool

def analyze_parallel(files):
    with Pool() as pool:
        results = pool.map(analyze_file, files)
    return results
```

### 10.2 Frontend Performance

```javascript
// Debounce expensive operations
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
    };
}

// Lazy load images
<img loading="lazy" src="image.jpg" alt="...">

// Use requestAnimationFrame for animations
function animate() {
    requestAnimationFrame(animate);
    // Update animation
}
```

### 10.3 Caching

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_audio_info(file_path):
    """Cache audio metadata"""
    pass

# HTTP caching for static files
@app.after_request
def add_cache_headers(response):
    if request.path.startswith('/static/'):
        response.cache_control.max_age = 86400  # 1 day
    return response
```

---

## Quick Reference

### Common Commands

```bash
# Start dev server
python run_dashboard.py

# Run tests
pytest -v

# Format code
black src/

# Check types
mypy src/

# Build package
pip install build
python -m build
```

### File Locations

| What | Where |
|------|-------|
| Routes | `src/harmonix_splitter/dashboard.py` |
| Templates | `src/harmonix_splitter/templates/` |
| CSS | `src/harmonix_splitter/static/css/` |
| JS | `src/harmonix_splitter/static/js/` |
| Config | `config/config.yaml` |
| User data | `data/users.json` |
| Uploads | `data/uploads/` |
| Outputs | `data/outputs/` |
| Logs | `logs/` |

---

**Last Updated:** December 30, 2025  
**© 2025 Harmonix. All rights reserved.**
