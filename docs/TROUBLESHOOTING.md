# 🚨 Troubleshooting Guide

**Solutions to common issues and error messages**

---

## Table of Contents

- [Installation Issues](#installation-issues)
- [GPU/CUDA Issues](#gpucuda-issues)
- [Audio Processing Issues](#audio-processing-issues)
- [Model Loading Issues](#model-loading-issues)
- [YouTube Download Issues](#youtube-download-issues)
- [Dashboard Issues](#dashboard-issues)
- [API Issues](#api-issues)
- [Memory Issues](#memory-issues)
- [Performance Issues](#performance-issues)
- [Error Messages Reference](#error-messages-reference)

---

## Installation Issues

### Package Installation Fails

**Error:** `pip install failed`

**Solutions:**

1. **Upgrade pip:**
   ```bash
   pip install --upgrade pip setuptools wheel
   ```

2. **Use Python 3.10:**
   ```bash
   python3.10 -m pip install -r requirements.txt
   ```

3. **Install build dependencies:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-dev build-essential
   
   # macOS
   xcode-select --install
   ```

4. **Try requirements-lite:**
   ```bash
   pip install -r requirements-lite.txt
   ```

---

### FFmpeg Not Found

**Error:** `FileNotFoundError: ffmpeg not found`

**Solutions:**

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
choco install ffmpeg
# Or download from https://ffmpeg.org/download.html

# Verify installation
ffmpeg -version
```

---

### libsndfile Missing

**Error:** `OSError: libsndfile.so not found`

**Solutions:**

```bash
# Ubuntu/Debian
sudo apt-get install libsndfile1

# macOS
brew install libsndfile

# Windows - usually included with soundfile package
pip install soundfile
```

---

## GPU/CUDA Issues

### CUDA Not Available

**Error:** `torch.cuda.is_available() returns False`

**Diagnosis:**
```python
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
```

**Solutions:**

1. **Install CUDA toolkit:**
   ```bash
   # Check NVIDIA driver version
   nvidia-smi
   
   # Install matching CUDA toolkit
   # CUDA 11.8 recommended
   ```

2. **Install correct PyTorch version:**
   ```bash
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

3. **For Apple Silicon (M1/M2/M3):**
   ```bash
   # MPS backend is used instead of CUDA
   pip install torch torchaudio
   # Set environment variable
   export HARMONIX_DEVICE=mps
   ```

---

### CUDA Out of Memory

**Error:** `RuntimeError: CUDA out of memory`

**Solutions:**

1. **Reduce quality mode:**
   ```bash
   harmonix process audio.mp3 --quality fast
   ```

2. **Reduce batch size:**
   ```bash
   export HARMONIX_BATCH_SIZE=1
   ```

3. **Clear GPU cache:**
   ```python
   import torch
   torch.cuda.empty_cache()
   ```

4. **Use CPU fallback:**
   ```bash
   export HARMONIX_DEVICE=cpu
   ```

5. **Close other GPU applications:**
   ```bash
   # Check GPU usage
   nvidia-smi
   ```

---

### MPS Backend Errors (Apple Silicon)

**Error:** `RuntimeError: MPS backend error`

**Solutions:**

1. **Update PyTorch:**
   ```bash
   pip install --upgrade torch torchaudio
   ```

2. **Fall back to CPU:**
   ```bash
   export HARMONIX_DEVICE=cpu
   ```

3. **Set environment variable:**
   ```bash
   export PYTORCH_ENABLE_MPS_FALLBACK=1
   ```

---

## Audio Processing Issues

### Unsupported Audio Format

**Error:** `AudioLoadError: Cannot load audio file`

**Solutions:**

1. **Convert to supported format:**
   ```bash
   ffmpeg -i input.xyz -acodec pcm_s16le output.wav
   ```

2. **Supported formats:**
   - MP3 (.mp3)
   - WAV (.wav)
   - FLAC (.flac)
   - M4A (.m4a)
   - OGG (.ogg)

---

### Audio Too Long

**Error:** `Audio duration exceeds maximum limit`

**Solutions:**

1. **Split audio:**
   ```bash
   ffmpeg -i long_audio.mp3 -ss 0 -t 600 part1.mp3
   ffmpeg -i long_audio.mp3 -ss 600 -t 600 part2.mp3
   ```

2. **Increase limit (if memory allows):**
   ```yaml
   # config/config.yaml
   processing:
     max_duration: 1800  # 30 minutes
   ```

---

### Corrupted Audio Output

**Error:** Output files are silent or garbled

**Solutions:**

1. **Check input file:**
   ```bash
   ffprobe input.mp3
   ```

2. **Re-encode input:**
   ```bash
   ffmpeg -i input.mp3 -acodec libmp3lame -b:a 320k clean_input.mp3
   ```

3. **Use WAV output:**
   ```bash
   harmonix process input.mp3 --output-format wav
   ```

---

## Model Loading Issues

### Model Download Fails

**Error:** `Failed to download model`

**Solutions:**

1. **Manual download:**
   ```bash
   # Models are downloaded from torch hub
   python -c "import torch; torch.hub.load('facebookresearch/demucs', 'htdemucs')"
   ```

2. **Check internet connection:**
   ```bash
   curl -I https://github.com
   ```

3. **Use proxy:**
   ```bash
   export HTTP_PROXY=http://proxy:8080
   export HTTPS_PROXY=http://proxy:8080
   ```

4. **Download manually and set path:**
   ```bash
   # Download from GitHub releases
   export HARMONIX_MODELS_DIR=./models
   ```

---

### Model Not Found

**Error:** `Model 'htdemucs_6s' not found`

**Solutions:**

1. **List available models:**
   ```python
   from demucs.pretrained import SOURCES
   print(SOURCES.keys())
   ```

2. **Use default model:**
   ```bash
   harmonix process audio.mp3 --model htdemucs
   ```

3. **Download specific model:**
   ```python
   import torch
   torch.hub.load('facebookresearch/demucs', 'htdemucs', trust_repo=True)
   ```

---

## YouTube Download Issues

### Video Unavailable

**Error:** `Video unavailable`

**Solutions:**

1. **Check URL is valid:**
   ```bash
   # Test with yt-dlp directly
   yt-dlp --simulate "https://youtube.com/watch?v=VIDEO_ID"
   ```

2. **Add cookies for restricted content:**
   ```bash
   # Export cookies from browser
   harmonix process --url "..." --cookies cookies.txt
   ```

---

### Rate Limited

**Error:** `HTTP Error 429: Too Many Requests`

**Solutions:**

1. **Wait and retry:**
   ```bash
   # Wait 1-24 hours before retrying
   ```

2. **Use cookies:**
   ```bash
   # Logged-in accounts have higher limits
   export HARMONIX_COOKIES_PATH=./cookies.txt
   ```

3. **Use VPN or different IP:**
   ```bash
   # Change network or use VPN
   ```

---

### yt-dlp Outdated

**Error:** `Unable to extract video data`

**Solution:**

```bash
pip install --upgrade yt-dlp
```

---

## Dashboard Issues

### Dashboard Won't Start

**Error:** `Address already in use`

**Solutions:**

1. **Use different port:**
   ```bash
   HARMONIX_DASHBOARD_PORT=5001 python -m harmonix_splitter.dashboard
   ```

2. **Kill existing process:**
   ```bash
   # Find process
   lsof -i :5000
   # Kill it
   kill -9 <PID>
   ```

---

### Static Files Not Loading

**Error:** CSS/JS not loading, blank page

**Solutions:**

1. **Clear browser cache:**
   ```
   Ctrl+Shift+R (or Cmd+Shift+R on Mac)
   ```

2. **Check static files path:**
   ```bash
   ls -la src/harmonix_splitter/static/
   ```

3. **Reinstall package:**
   ```bash
   pip install -e .
   ```

---

### Upload Fails

**Error:** `413 Request Entity Too Large`

**Solutions:**

1. **Increase upload limit:**
   ```python
   # In dashboard.py
   app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB
   ```

2. **For nginx:**
   ```nginx
   client_max_body_size 500M;
   ```

---

## API Issues

### API Not Responding

**Error:** `Connection refused on port 8000`

**Solutions:**

1. **Start API separately:**
   ```bash
   uvicorn harmonix_splitter.api.main:app --port 8000
   ```

2. **Check port availability:**
   ```bash
   lsof -i :8000
   ```

---

### CORS Errors

**Error:** `Access-Control-Allow-Origin` errors

**Solution:**

API has CORS enabled by default. If issues persist:

```python
# In api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Memory Issues

### Python Memory Error

**Error:** `MemoryError`

**Solutions:**

1. **Use 64-bit Python:**
   ```bash
   python --version
   # Ensure using 64-bit Python
   ```

2. **Reduce quality:**
   ```bash
   harmonix process audio.mp3 --quality fast
   ```

3. **Process shorter files:**
   ```bash
   # Split long files
   ffmpeg -i long.mp3 -ss 0 -t 300 short.mp3
   ```

4. **Increase swap:**
   ```bash
   # Linux
   sudo fallocate -l 8G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

---

### Docker Memory Issues

**Error:** Container killed (OOM)

**Solutions:**

```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      memory: 16G
    reservations:
      memory: 8G
```

---

## Performance Issues

### Processing Too Slow

**Symptoms:** Processing takes longer than expected

**Solutions:**

1. **Use GPU:**
   ```bash
   # Check if GPU is being used
   watch nvidia-smi
   ```

2. **Lower quality mode:**
   ```bash
   harmonix process audio.mp3 --quality fast
   ```

3. **Ensure using htdemucs (fastest):**
   ```bash
   harmonix process audio.mp3 --model htdemucs
   ```

4. **Disable unnecessary features:**
   ```bash
   # Skip analysis
   harmonix process audio.mp3 --skip-analysis
   ```

---

### High CPU Usage

**Solutions:**

1. **Limit threads:**
   ```bash
   export OMP_NUM_THREADS=4
   export MKL_NUM_THREADS=4
   ```

2. **Use GPU instead of CPU:**
   ```bash
   export HARMONIX_DEVICE=cuda
   ```

---

## Error Messages Reference

### Quick Reference

| Error | Solution |
|-------|----------|
| `CUDA out of memory` | Use --quality fast or CPU |
| `FileNotFoundError: ffmpeg` | Install FFmpeg |
| `Model not found` | Update Demucs/check model name |
| `Audio load error` | Convert to MP3/WAV |
| `HTTP 429` | Wait/use cookies/VPN |
| `Address in use` | Kill process on port |
| `Permission denied` | Check file/folder permissions |

### Getting Help

1. **Check logs:**
   ```bash
   cat logs/harmonix.log
   ```

2. **Enable debug mode:**
   ```bash
   export HARMONIX_LOG_LEVEL=DEBUG
   ```

3. **Run verification:**
   ```bash
   python verify_installation.py
   ```

4. **Report issues:**
   - GitHub Issues with full error message
   - Include: OS, Python version, GPU info

---

## Diagnostic Commands

### System Check

```bash
# Python version
python --version

# Package versions
pip show harmonix-splitter torch demucs

# GPU info
python -c "import torch; print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'No GPU')"

# FFmpeg
ffmpeg -version

# Disk space
df -h

# Memory
free -h
```

### Test Processing

```bash
# Quick test
python -c "
from harmonix_splitter import HarmonixOrchestrator
o = HarmonixOrchestrator()
print('Initialization successful!')
"
```

---

## Related Documentation

- [Installation](./INSTALLATION.md) - Setup guide
- [Configuration](./CONFIGURATION.md) - Settings
- [Docker](./DOCKER.md) - Container issues
- [Architecture](./ARCHITECTURE.md) - System overview

---

*Troubleshooting guide last updated: January 2026*
