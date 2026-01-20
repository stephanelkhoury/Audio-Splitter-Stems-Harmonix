# ⚡ Quickstart Guide

**Get up and running with Harmonix in 5 minutes**

---

## 🚀 Fastest Way to Start

### Option 1: Web Dashboard (Easiest)

```bash
# Clone and enter project
git clone https://github.com/stephanelkhoury-dev/Audio-Splitter-Stems-Harmonix.git
cd Audio-Splitter-Stems-Harmonix

# Run quickstart script
./quickstart.sh
```

This will:
1. Create a virtual environment
2. Install all dependencies
3. Start the web dashboard
4. Open your browser to http://localhost:5000

### Option 2: Manual Dashboard Start

```bash
# Activate virtual environment
source .venv/bin/activate

# Start dashboard
./start_dashboard.sh

# Or directly with Python
python run_dashboard.py
```

---

## 📱 Using the Web Dashboard

### Step 1: Upload Audio

1. Open http://localhost:5000 in your browser
2. Click the upload area or drag & drop your audio file
3. **Supported formats**: MP3, WAV, FLAC, M4A, OGG, AAC

### Step 2: Configure Processing

| Setting | Options | Description |
|---------|---------|-------------|
| **Quality** | Fast, Balanced, Studio | Processing quality vs speed |
| **Mode** | Grouped, Per-Instrument, Karaoke | Output stem configuration |

### Step 3: Process & Download

1. Click **"Start Processing"**
2. Watch the real-time progress bar
3. When complete, **play stems in browser** or download

---

## 💻 Command Line Interface (CLI)

### Basic Usage

```bash
# Activate environment
source .venv/bin/activate

# Basic separation (4 stems: vocals, drums, bass, other)
python -m harmonix_splitter.cli song.mp3

# Studio quality with per-instrument separation
python -m harmonix_splitter.cli song.mp3 --quality studio --mode per_instrument

# Specify output directory
python -m harmonix_splitter.cli song.mp3 --output ./my_stems
```

### CLI Options

```bash
harmonix-split [OPTIONS] INPUT_FILES...

Options:
  -o, --output PATH           Output directory (default: ./harmonix_output)
  -q, --quality [fast|balanced|studio]
                             Quality mode (default: balanced)
  -m, --mode [grouped|per_instrument|karaoke]
                             Separation mode (default: grouped)
  -i, --instruments LIST     Target instruments (comma-separated)
  --cpu-only                 Force CPU processing
  --analyze-only             Only analyze, don't separate
  -v, --verbose              Enable verbose logging
  --version                  Show version
  -h, --help                 Show help
```

### CLI Examples

```bash
# Extract only vocals and drums
python -m harmonix_splitter.cli song.mp3 --instruments vocals,drums

# Fast processing for testing
python -m harmonix_splitter.cli song.mp3 --quality fast

# Batch process multiple files
python -m harmonix_splitter.cli ./music/*.mp3 --output ./batch_stems

# Analyze without separation
python -m harmonix_splitter.cli song.mp3 --analyze-only
```

---

## 🔌 REST API

### Start the API Server

```bash
# Using uvicorn
uvicorn harmonix_splitter.api.main:app --host 0.0.0.0 --port 8000

# API documentation available at:
# http://localhost:8000/docs
```

### Quick API Example

```bash
# Submit a separation job
curl -X POST "http://localhost:8000/api/split" \
  -F "file=@song.mp3" \
  -F "quality=balanced"

# Response:
# {
#   "job_id": "abc123...",
#   "status": "queued"
# }

# Check status
curl "http://localhost:8000/api/status/{job_id}"

# Download results
curl "http://localhost:8000/api/stems/{job_id}/vocals.mp3" --output vocals.mp3
```

---

## 🐍 Python SDK

### Basic Usage

```python
from harmonix_splitter import create_separator

# Create separator
separator = create_separator(
    quality="balanced",
    mode="grouped",
    use_gpu=True
)

# Separate audio
stems = separator.separate("song.mp3", output_dir="./output")

# Access results
for name, stem in stems.items():
    print(f"{name}: {stem.audio.shape}")
```

### With Full Orchestration

```python
from harmonix_splitter import create_orchestrator

# Create orchestrator (with analysis)
orchestrator = create_orchestrator(auto_route=True)

# Process with analysis
result = orchestrator.process(
    audio_path="song.mp3",
    job_id="my_job",
    quality="balanced",
    mode="per_instrument",
    output_dir="./output"
)

print(f"Detected: {result.detected_instruments}")
print(f"Time: {result.processing_time:.2f}s")
```

### Analysis Only

```python
from harmonix_splitter import create_orchestrator

orchestrator = create_orchestrator()
analysis = orchestrator.analyze_only("song.mp3")

print(f"Instruments: {analysis['detected_instruments']}")
print(f"Confidence: {analysis['confidence_scores']}")
```

---

## ⚙️ Quick Configuration

### Environment Variables

Create a `.env` file:

```bash
# GPU Settings
HARMONIX_USE_GPU=true

# Default Quality
HARMONIX_DEFAULT_QUALITY=balanced
HARMONIX_DEFAULT_MODE=grouped

# Paths
HARMONIX_UPLOAD_DIR=./data/uploads
HARMONIX_OUTPUT_DIR=./data/outputs

# Limits
HARMONIX_MAX_FILE_SIZE=524288000  # 500MB
HARMONIX_MAX_DURATION=600         # 10 minutes
```

### Force CPU Mode

```bash
# Environment variable
export HARMONIX_USE_GPU=false

# CLI flag
python -m harmonix_splitter.cli song.mp3 --cpu-only
```

---

## 📊 Understanding Output

### Grouped Mode (4 Stems)

```
output/
├── song_vocals.mp3      # Isolated vocals
├── song_drums.mp3       # Drums and percussion
├── song_bass.mp3        # Bass guitar/synth bass
└── song_other.mp3       # Everything else
```

### Per-Instrument Mode

```
output/
├── song_vocals.mp3
├── song_drums.mp3
├── song_bass.mp3
├── song_guitar.mp3
├── song_piano.mp3
├── song_strings.mp3
└── song_other.mp3
```

### Karaoke Mode (2 Stems)

```
output/
├── song_vocals.mp3       # Isolated vocals
└── song_instrumental.mp3 # Full instrumental
```

---

## 🎯 Quality Mode Comparison

| Mode | Speed | Quality | Use Case |
|------|-------|---------|----------|
| **Fast** | ~30 sec/song | Good | Testing, previews |
| **Balanced** | ~1-2 min/song | Very Good | Most uses |
| **Studio** | ~3-5 min/song | Excellent | Professional work |

---

## 🎵 Supported Audio Formats

### Input Formats
- MP3 (.mp3)
- WAV (.wav)
- FLAC (.flac)
- M4A/AAC (.m4a, .aac)
- OGG Vorbis (.ogg)

### Output Formats
- MP3 (320kbps) - Default
- WAV (24-bit) - Lossless
- FLAC - Compressed lossless

---

## ❓ Common Questions

### How long does processing take?

| Audio Length | Fast | Balanced | Studio |
|--------------|------|----------|--------|
| 3 min song | ~20s | ~60s | ~3 min |
| 5 min song | ~30s | ~90s | ~5 min |
| 10 min song | ~60s | ~3 min | ~10 min |

*Times with GPU acceleration. CPU processing is 2-5x slower.*

### Where are my files saved?

Default: `data/outputs/{job_id}/`

### Can I process YouTube videos?

Yes! In the dashboard, paste a YouTube URL in the URL input tab.

### Is GPU required?

No, but GPU processing is 5-10x faster. CPU mode works but is slower.

---

## 🆘 Need Help?

- **Full Documentation**: See other files in `docs/`
- **Troubleshooting**: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **GitHub Issues**: Report bugs or request features

---

*Ready to dive deeper? Check out the [Stem Separation Guide](./STEM_SEPARATION.md)*
