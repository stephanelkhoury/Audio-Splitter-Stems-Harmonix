# 🛠️ Installation Guide

**Complete installation instructions for Harmonix Audio Splitter**

---

## Table of Contents

- [System Requirements](#system-requirements)
- [Quick Installation](#quick-installation)
- [Detailed Installation](#detailed-installation)
- [GPU Setup](#gpu-setup)
- [Docker Installation](#docker-installation)
- [Verifying Installation](#verifying-installation)
- [Troubleshooting](#troubleshooting-installation)

---

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 10+, macOS 11+, Linux (Ubuntu 20.04+) |
| **Python** | 3.10 or higher |
| **RAM** | 8 GB minimum |
| **Storage** | 10 GB free space |
| **FFmpeg** | Required for audio processing |

### Recommended Requirements

| Component | Requirement |
|-----------|-------------|
| **RAM** | 16 GB or more |
| **GPU** | NVIDIA GPU with CUDA 11.7+ or Apple Silicon |
| **VRAM** | 8 GB or more |
| **Storage** | SSD with 50 GB free space |

---

## Quick Installation

### One-Line Install (macOS/Linux)

```bash
# Clone, setup environment, install dependencies
git clone https://github.com/stephanelkhoury-dev/Audio-Splitter-Stems-Harmonix.git && \
cd Audio-Splitter-Stems-Harmonix && \
python -m venv .venv && \
source .venv/bin/activate && \
pip install -r requirements.txt
```

### Windows PowerShell

```powershell
git clone https://github.com/stephanelkhoury-dev/Audio-Splitter-Stems-Harmonix.git
cd Audio-Splitter-Stems-Harmonix
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## Detailed Installation

### Step 1: Prerequisites

#### Install Python 3.10+

**macOS:**
```bash
# Using Homebrew
brew install python@3.11
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/) and run installer.

#### Install FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**Windows:**
```bash
# Using Chocolatey
choco install ffmpeg

# Or using Scoop
scoop install ffmpeg
```

#### Install Git

```bash
# macOS
brew install git

# Ubuntu/Debian
sudo apt install git

# Windows (using Chocolatey)
choco install git
```

### Step 2: Clone the Repository

```bash
git clone https://github.com/stephanelkhoury-dev/Audio-Splitter-Stems-Harmonix.git
cd Audio-Splitter-Stems-Harmonix
```

### Step 3: Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Install in development mode (recommended)
pip install -e .
```

### Step 5: Download Models

Models are downloaded automatically on first use. To pre-download:

```bash
# Pre-download Demucs models
python -c "from demucs.pretrained import get_model; get_model('htdemucs')"
```

---

## GPU Setup

### NVIDIA GPU (CUDA)

#### 1. Install NVIDIA Drivers

Download from [NVIDIA Driver Downloads](https://www.nvidia.com/Download/index.aspx)

#### 2. Install CUDA Toolkit

```bash
# Ubuntu
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt-get update
sudo apt-get install cuda-toolkit-11-8
```

#### 3. Install PyTorch with CUDA

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### 4. Verify CUDA Installation

```python
import torch
print(f"CUDA Available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0)}")
```

### Apple Silicon (MPS)

Apple Silicon Macs automatically use Metal Performance Shaders (MPS) for GPU acceleration.

#### Verify MPS

```python
import torch
print(f"MPS Available: {torch.backends.mps.is_available()}")
```

---

## Docker Installation

### Prerequisites

- Docker Engine 20.10+
- Docker Compose v2.0+
- NVIDIA Container Toolkit (for GPU support)

### Basic Docker Setup

```bash
# Clone repository
git clone https://github.com/stephanelkhoury-dev/Audio-Splitter-Stems-Harmonix.git
cd Audio-Splitter-Stems-Harmonix

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f
```

### Docker with GPU

```bash
# Using GPU docker-compose
docker-compose -f docker-compose.yml up -d
```

### Docker CPU-Only

```bash
# Using CPU docker-compose
docker-compose -f docker-compose.cpu.yml up -d
```

### Docker Build Options

```bash
# Build with specific Dockerfile
docker build -t harmonix:latest .

# Build CPU-only image
docker build -f Dockerfile.cpu -t harmonix:cpu .

# Build slim image (no ML models pre-loaded)
docker build -f Dockerfile.slim -t harmonix:slim .
```

---

## Verifying Installation

### Run Verification Script

```bash
python verify_installation.py
```

### Manual Verification

```python
# Test imports
from harmonix_splitter.core.separator import HarmonixSeparator
from harmonix_splitter.analysis.detector import InstrumentDetector
from harmonix_splitter.core.orchestrator import create_orchestrator

# Test GPU
import torch
print(f"PyTorch Version: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
print(f"MPS Available: {torch.backends.mps.is_available()}")

# Test FFmpeg
import subprocess
result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
print(f"FFmpeg: {'OK' if result.returncode == 0 else 'NOT FOUND'}")

print("\n✅ Installation verified successfully!")
```

### Test Separation

```bash
# Test with a sample file
python -m harmonix_splitter.cli path/to/audio.mp3 --quality fast
```

---

## Troubleshooting Installation

### Common Issues

#### 1. "ModuleNotFoundError: No module named 'demucs'"

```bash
pip install demucs
```

#### 2. "torch not compiled with CUDA enabled"

```bash
# Uninstall current torch
pip uninstall torch torchvision torchaudio

# Install CUDA version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### 3. "FFmpeg not found"

Ensure FFmpeg is in your system PATH:

```bash
# Check FFmpeg
which ffmpeg  # macOS/Linux
where ffmpeg  # Windows
```

#### 4. "Permission denied" on macOS/Linux

```bash
chmod +x start_dashboard.sh
chmod +x quickstart.sh
```

#### 5. "Out of memory" errors

- Reduce batch size
- Use "fast" quality mode
- Process shorter audio files
- Use CPU mode: `--cpu-only`

#### 6. Python version issues

```bash
# Check Python version
python --version

# Use specific Python version
python3.11 -m venv .venv
```

### Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](./TROUBLESHOOTING.md)
2. Search existing [GitHub Issues](https://github.com/stephanelkhoury-dev/Audio-Splitter-Stems-Harmonix/issues)
3. Create a new issue with:
   - Operating system and version
   - Python version
   - Error message and traceback
   - Steps to reproduce

---

## Next Steps

After installation:

1. **Start the Dashboard**: `./start_dashboard.sh`
2. **Try the CLI**: `python -m harmonix_splitter.cli --help`
3. **Read the [Quickstart Guide](./QUICKSTART.md)**
4. **Explore [Features Documentation](./STEM_SEPARATION.md)**

---

*Installation guide last updated: January 2026*
