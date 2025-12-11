# 🎵 Harmonix Audio Splitter

**AI-powered audio stem separation with instrument-level precision**

Harmonix Audio Splitter is a production-ready module that isolates vocals, drums, bass, and individual instrumental stems from any audio file using state-of-the-art deep learning models. Built with PyTorch and FastAPI, it provides fast, scalable processing with support for local, API, and containerized deployment.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌟 Key Features

- **🎯 Studio-Quality Separation** - Powered by Demucs v4 hybrid transformer models
- **🔬 Instrument Detection** - Multi-label AI classification detects what's in your mix
- **⚡ GPU Accelerated** - CUDA support for near real-time processing
- **🎚️ Quality Presets** - Fast, Balanced, or Studio modes
- **🎼 Per-Instrument Stems** - Extract vocals, drums, bass, guitar, piano, strings, synth, and more
- **🔄 Smart Routing** - Automatic pipeline optimization based on content analysis
- **🚀 REST API** - Production-ready FastAPI with async job processing
- **💻 CLI Tool** - Standalone command-line interface
- **🐳 Docker Ready** - Full containerization with GPU support
- **📊 Batch Processing** - Handle multiple files efficiently

---

## 📋 Table of Contents

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
  - [CLI](#cli-usage)
  - [API](#api-usage)
  - [Python SDK](#python-sdk)
- [Configuration](#-configuration)
- [Docker Deployment](#-docker-deployment)
- [Architecture](#-architecture)
- [API Reference](#-api-reference)
- [Development](#-development)

---

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- ffmpeg (`brew install ffmpeg` on macOS, `apt-get install ffmpeg` on Linux)
- (Optional) CUDA-capable GPU for acceleration

### From Source

```bash
# Clone the repository
git clone https://github.com/stephanelkhoury-dev/Audio-Splitter-Stems-Harmonix.git
cd Audio-Splitter-Stems-Harmonix

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### With Docker

```bash
# Build and run with docker-compose
docker-compose up -d

# Access API at http://localhost:8000
```

---

## ⚡ Quick Start

### Web Dashboard (Easiest!)

```bash
# Start the web interface
./start_dashboard.sh

# Open browser to http://localhost:5000
# Upload audio, select options, listen to results!
```

See [DASHBOARD.md](DASHBOARD.md) for full dashboard guide.

### CLI - Process a Song

```bash
# Basic usage (4-stem separation)
python -m harmonix_splitter.cli song.mp3

# High-quality per-instrument separation
python -m harmonix_splitter.cli song.mp3 --quality studio --mode per_instrument

# Extract specific instruments
python -m harmonix_splitter.cli song.mp3 --instruments vocals,drums,bass,guitar

# Analysis only (detect instruments without separation)
python -m harmonix_splitter.cli song.mp3 --analyze-only
```

### API - Start Server

```bash
# Start FastAPI server
uvicorn harmonix_splitter.api.main:app --reload

# Or use the included script
python -m uvicorn harmonix_splitter.api.main:app --host 0.0.0.0 --port 8000
```

### Python SDK

```python
from harmonix_splitter import create_separator

# Initialize separator
separator = create_separator(quality="studio", mode="per_instrument")

# Separate stems
stems = separator.separate("song.mp3", output_dir="./output")

# Access stems
for name, stem in stems.items():
    print(f"{name}: {stem.audio.shape}, confidence: {stem.confidence}")
```

---

## 📖 Usage

### CLI Usage

The Harmonix CLI provides a complete command-line interface:

```bash
harmonix-split [OPTIONS] INPUT_FILES...

Options:
  -o, --output PATH            Output directory (default: ./harmonix_output)
  -q, --quality [fast|balanced|studio]  
                              Quality mode (default: balanced)
  -m, --mode [grouped|per_instrument]
                              Separation mode (default: grouped)
  -i, --instruments LIST      Target instruments (comma-separated)
  --cpu-only                  Force CPU processing
  --analyze-only              Only analyze, don't separate
  --no-auto-route            Disable automatic routing
  -v, --verbose               Enable verbose logging
  --version                   Show version
  -h, --help                  Show help
```

#### Examples

**Standard 4-stem separation:**
```bash
harmonix-split song.mp3 --output ./stems
```

**Per-instrument with studio quality:**
```bash
harmonix-split song.mp3 \
  --quality studio \
  --mode per_instrument \
  --output ./stems
```

**Extract vocals and drums only:**
```bash
harmonix-split song.mp3 \
  --instruments vocals,drums \
  --output ./vocals_drums
```

**Batch process folder:**
```bash
harmonix-split ./music/*.mp3 --output ./batch_stems
```

**Analyze before processing:**
```bash
# First analyze
harmonix-split song.mp3 --analyze-only

# Then process based on results
harmonix-split song.mp3 --mode per_instrument
```

### API Usage

#### Start the API Server

```bash
uvicorn harmonix_splitter.api.main:app --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs` for interactive API documentation.

#### Submit a Separation Job

```bash
curl -X POST "http://localhost:8000/api/split" \
  -F "file=@song.mp3" \
  -F "quality=studio" \
  -F "mode=per_instrument"
```

Response:
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "queued",
  "progress": 0.0,
  "message": "Job queued for processing",
  "created_at": "2025-12-10T10:30:00"
}
```

#### Check Job Status

```bash
curl "http://localhost:8000/api/status/{job_id}"
```

#### Get Results

```bash
curl "http://localhost:8000/api/result/{job_id}"
```

#### Download Stems

```bash
curl "http://localhost:8000/api/stems/{job_id}/vocals.wav" --output vocals.wav
```

#### Analyze Audio

```bash
curl -X POST "http://localhost:8000/api/analysis" \
  -F "file=@song.mp3"
```

### Python SDK

```python
from pathlib import Path
from harmonix_splitter import create_separator, create_orchestrator

# Method 1: Direct Separator
separator = create_separator(
    quality="studio",
    mode="per_instrument",
    use_gpu=True,
    target_instruments=["vocals", "drums", "bass", "guitar"]
)

stems = separator.separate("song.mp3", output_dir="./output")

# Method 2: Full Orchestrator (with analysis)
orchestrator = create_orchestrator(auto_route=True)

result = orchestrator.process(
    audio_path="song.mp3",
    job_id="my_job",
    quality="balanced",
    mode="per_instrument",
    output_dir="./output"
)

print(f"Detected: {result.detected_instruments}")
print(f"Processing time: {result.processing_time:.2f}s")

# Method 3: Analysis Only
analysis = orchestrator.analyze_only("song.mp3")
print(f"Instruments: {analysis['detected_instruments']}")
print(f"Recommendations: {analysis['recommendations']}")
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Processing
HARMONIX_USE_GPU=true
HARMONIX_DEFAULT_QUALITY=balanced
HARMONIX_DEFAULT_MODE=grouped

# Paths
HARMONIX_UPLOAD_DIR=./data/uploads
HARMONIX_OUTPUT_DIR=./data/outputs
HARMONIX_MODELS_DIR=./models

# API
HARMONIX_API_HOST=0.0.0.0
HARMONIX_API_PORT=8000

# Limits
HARMONIX_MAX_FILE_SIZE=524288000  # 500MB
HARMONIX_MAX_DURATION=600  # 10 minutes

# Storage (Production)
HARMONIX_USE_S3=false
HARMONIX_S3_BUCKET=my-harmonix-bucket
HARMONIX_S3_REGION=us-east-1

# Job Queue (Production)
HARMONIX_USE_REDIS=true
HARMONIX_REDIS_URL=redis://localhost:6379

# Logging
HARMONIX_LOG_LEVEL=INFO
HARMONIX_LOG_FILE=./logs/harmonix.log
```

### Configuration File

Alternatively, use `config/config.yaml`:

```yaml
processing:
  use_gpu: true
  default_quality: balanced
  default_mode: grouped
  sample_rate: 44100

detection:
  thresholds:
    vocals: 0.5
    drums: 0.5
    bass: 0.5
    guitar: 0.5
    piano: 0.5
    strings: 0.6
    synth: 0.7

limits:
  max_file_size: 524288000
  max_duration: 600
  min_duration: 1.0
```

---

## 🐳 Docker Deployment

### Basic Deployment

```bash
# Build
docker build -t harmonix:latest .

# Run
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  --gpus all \
  --name harmonix-api \
  harmonix:latest
```

### Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f harmonix-api

# Stop services
docker-compose down

# With monitoring stack
docker-compose --profile monitoring up -d
```

Services included:
- **harmonix-api**: Main API service with GPU support
- **redis**: Job queue and caching
- **minio**: S3-compatible object storage
- **prometheus** (optional): Metrics collection
- **grafana** (optional): Monitoring dashboards

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Input Audio File                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 1: Preprocessing & Validation (preprocessor.py)      │
│  • Format validation                                         │
│  • Audio normalization                                       │
│  • Resampling to 44.1kHz                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 2: Instrument Detection (detector.py)                │
│  • Multi-label classification                                │
│  • Confidence scoring                                        │
│  • Feature extraction (mel-spec, MFCC, etc.)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 3: Routing & Planning (orchestrator.py)              │
│  • Select quality preset                                     │
│  • Choose separation mode                                    │
│  • Optimize pipeline                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 4: Stem Separation (separator.py)                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Primary: Demucs 4-stem (vocals/drums/bass/other)  │    │
│  └────────────────────┬────────────────────────────────┘    │
│                       │                                      │
│                       ▼                                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Refinement: Instrument-level separation            │    │
│  │  (guitar, piano, strings, synth, brass, etc.)       │    │
│  └─────────────────────────────────────────────────────┘    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Output: Individual Stem Files (WAV/MP3)                    │
│  • vocals.wav, drums.wav, bass.wav, guitar.wav, piano.wav...│
└─────────────────────────────────────────────────────────────┘
```

### Core Modules

- **`separator.py`** - Demucs integration, GPU acceleration, stem extraction
- **`detector.py`** - Instrument detection, multi-label classification
- **`orchestrator.py`** - Pipeline routing, end-to-end processing
- **`preprocessor.py`** - Audio validation, format conversion (ffmpeg)
- **`api/main.py`** - FastAPI endpoints, job management
- **`cli.py`** - Command-line interface

---

## 📚 API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API root information |
| GET | `/health` | Health check |
| POST | `/api/split` | Submit separation job |
| GET | `/api/status/{job_id}` | Get job status |
| GET | `/api/result/{job_id}` | Get job results |
| GET | `/api/stems/{job_id}/{stem}` | Download stem file |
| POST | `/api/analysis` | Analyze audio (no separation) |
| GET | `/api/models` | Available models info |
| GET | `/api/jobs` | List all jobs |
| DELETE | `/api/jobs/{job_id}` | Delete job and files |

Full interactive documentation at `/docs` when server is running.

---

## 🛠️ Development

### Setup Development Environment

```bash
# Clone and install
git clone https://github.com/stephanelkhoury-dev/Audio-Splitter-Stems-Harmonix.git
cd Audio-Splitter-Stems-Harmonix
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting
black src/
flake8 src/

# Type checking
mypy src/
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=harmonix_splitter tests/

# Specific test
pytest tests/test_separator.py -v
```

### Project Structure

```
Audio-Splitter-Stems-Harmonix/
├── src/
│   └── harmonix_splitter/
│       ├── api/
│       │   ├── __init__.py
│       │   └── main.py           # FastAPI application
│       ├── analysis/
│       │   ├── __init__.py
│       │   └── detector.py       # Instrument detection
│       ├── core/
│       │   ├── __init__.py
│       │   ├── separator.py      # Stem separation engine
│       │   ├── preprocessor.py   # Audio preprocessing
│       │   └── orchestrator.py   # Pipeline routing
│       ├── config/
│       │   └── settings.py       # Configuration management
│       └── cli.py                # CLI interface
├── config/
│   └── config.yaml               # Default configuration
├── tests/
├── docs/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 🎯 Roadmap

### Phase 1: Core Features (Complete)
- [x] 4-stem separation (vocals/drums/bass/other)
- [x] GPU acceleration
- [x] Quality presets
- [x] FastAPI implementation
- [x] CLI tool
- [x] Docker support

### Phase 2: Advanced Features (In Progress)
- [ ] Trained instrument detection model
- [ ] Per-instrument specialized models
- [ ] Real-time/streaming separation
- [ ] Batch queue with Celery
- [ ] S3 storage integration
- [ ] Monitoring & metrics

### Phase 3: Enhancement (Planned)
- [ ] Web UI
- [ ] Plugin architecture
- [ ] Custom model training
- [ ] Multi-language support
- [ ] Cloud deployment templates

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Demucs** - Meta Research for the incredible source separation models
- **FastAPI** - Modern, fast web framework
- **PyTorch** - Deep learning framework
- **Librosa** - Audio analysis library

---

## 📧 Contact

**Stephan El Khoury**
- GitHub: [@stephanelkhoury-dev](https://github.com/stephanelkhoury-dev)
- Email: stephan@harmonix.dev

**Project Link:** https://github.com/stephanelkhoury-dev/Audio-Splitter-Stems-Harmonix

---

<div align="center">
  
**Built with ❤️ by Stephan El Khoury**

*Harmonix - Professional AI Audio Stem Separation*

</div>
