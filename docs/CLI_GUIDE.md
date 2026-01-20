# 💻 CLI Reference Guide

**Complete command-line interface documentation**

---

## Table of Contents

- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Commands and Options](#commands-and-options)
- [Examples](#examples)
- [Output Structure](#output-structure)
- [Advanced Usage](#advanced-usage)
- [Exit Codes](#exit-codes)

---

## Installation

The CLI is installed automatically with the package:

```bash
# Install from source
pip install -e .

# Verify installation
harmonix-split --version
```

Or run directly with Python:

```bash
python -m harmonix_splitter.cli --help
```

---

## Basic Usage

### Simplest Command

```bash
# Process a single file with defaults
harmonix-split song.mp3
```

### With Output Directory

```bash
harmonix-split song.mp3 --output ./my_stems
```

### With Quality Setting

```bash
harmonix-split song.mp3 --quality studio
```

---

## Commands and Options

### Synopsis

```
harmonix-split [OPTIONS] INPUT_FILES...
```

### Input Files

| Argument | Description |
|----------|-------------|
| `INPUT_FILES` | One or more audio files to process |

**Supported formats:** MP3, WAV, FLAC, M4A, OGG, AAC

### Options

#### Output Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output PATH` | `-o` | `./harmonix_output` | Output directory for stems |

#### Quality Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--quality MODE` | `-q` | `balanced` | Processing quality |

**Quality Modes:**
- `fast` - Quick processing, good quality
- `balanced` - Best balance of speed/quality
- `studio` - Maximum quality, slower

#### Separation Mode

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--mode MODE` | `-m` | `grouped` | Separation granularity |

**Separation Modes:**
- `grouped` - 4 stems (vocals, drums, bass, other)
- `per_instrument` - Individual instruments
- `karaoke` - 2 stems (vocals, instrumental)

#### Instrument Selection

| Option | Short | Description |
|--------|-------|-------------|
| `--instruments LIST` | `-i` | Comma-separated list of instruments |

**Available instruments:**
- `vocals`, `drums`, `bass`, `guitar`, `piano`
- `strings`, `synth`, `brass`, `woodwinds`, `fx`

#### Processing Options

| Option | Description |
|--------|-------------|
| `--cpu-only` | Force CPU processing (disable GPU) |
| `--analyze-only` | Only analyze audio, no separation |
| `--no-auto-route` | Disable automatic routing |

#### Other Options

| Option | Short | Description |
|--------|-------|-------------|
| `--verbose` | `-v` | Enable verbose/debug logging |
| `--version` | | Show version number |
| `--help` | `-h` | Show help message |

---

## Examples

### Basic Separation

```bash
# Default 4-stem separation
harmonix-split song.mp3

# Output:
# harmonix_output/
# ├── song_vocals.mp3
# ├── song_drums.mp3
# ├── song_bass.mp3
# └── song_other.mp3
```

### Quality Modes

```bash
# Fast (for testing)
harmonix-split song.mp3 --quality fast

# Balanced (recommended)
harmonix-split song.mp3 --quality balanced

# Studio (highest quality)
harmonix-split song.mp3 --quality studio
```

### Separation Modes

```bash
# Standard 4-stem
harmonix-split song.mp3 --mode grouped

# Per-instrument separation
harmonix-split song.mp3 --mode per_instrument

# Karaoke (vocals + instrumental)
harmonix-split song.mp3 --mode karaoke
```

### Select Specific Instruments

```bash
# Only vocals and drums
harmonix-split song.mp3 --instruments vocals,drums

# Vocals, bass, and guitar
harmonix-split song.mp3 --instruments vocals,bass,guitar

# Everything except vocals
harmonix-split song.mp3 --instruments drums,bass,guitar,piano,other
```

### Custom Output Directory

```bash
# Specify output location
harmonix-split song.mp3 --output ./my_project/stems

# With full path
harmonix-split song.mp3 -o /Users/music/stems/
```

### Batch Processing

```bash
# Process all MP3s in a folder
harmonix-split ./music/*.mp3 --output ./batch_stems

# Process multiple specific files
harmonix-split song1.mp3 song2.wav song3.flac --output ./all_stems

# Process with quality setting
harmonix-split ./music/*.mp3 --quality fast --output ./quick_stems
```

### Analysis Only

```bash
# Analyze without separation
harmonix-split song.mp3 --analyze-only

# Output:
# ============================================================
# Analyzing: song.mp3
# ============================================================
#
# Detected Instruments:
#   • Vocals: 92.3% confidence
#   • Drums: 88.7% confidence
#   • Bass: 75.2% confidence
#   • Guitar: 63.1% confidence
#
# Recommendations:
#   Mode: per_instrument
#   Complexity: 4 instruments detected
```

### CPU-Only Processing

```bash
# Force CPU (no GPU)
harmonix-split song.mp3 --cpu-only

# Useful when:
# - GPU has insufficient memory
# - Running on systems without GPU
# - Debugging GPU-related issues
```

### Verbose Output

```bash
# Enable debug logging
harmonix-split song.mp3 --verbose

# Shows:
# - Detailed progress
# - Model loading info
# - Memory usage
# - Timing information
```

### Combined Options

```bash
# Studio quality, per-instrument, specific instruments
harmonix-split song.mp3 \
  --quality studio \
  --mode per_instrument \
  --instruments vocals,drums,bass,guitar \
  --output ./studio_stems \
  --verbose
```

---

## Output Structure

### Grouped Mode

```
output_directory/
├── song_vocals.mp3
├── song_drums.mp3
├── song_bass.mp3
└── song_other.mp3
```

### Per-Instrument Mode

```
output_directory/
├── song_vocals.mp3
├── song_drums.mp3
├── song_bass.mp3
├── song_guitar.mp3
├── song_piano.mp3
├── song_strings.mp3
├── song_synth.mp3
└── song_other.mp3
```

### Karaoke Mode

```
output_directory/
├── song_vocals.mp3
└── song_instrumental.mp3
```

### Batch Processing

```
output_directory/
├── song1_vocals.mp3
├── song1_drums.mp3
├── song1_bass.mp3
├── song1_other.mp3
├── song2_vocals.mp3
├── song2_drums.mp3
├── song2_bass.mp3
└── song2_other.mp3
```

---

## Advanced Usage

### Scripting with CLI

```bash
#!/bin/bash
# process_album.sh

ALBUM_DIR="./album"
OUTPUT_DIR="./stems"
QUALITY="balanced"

for file in "$ALBUM_DIR"/*.mp3; do
    echo "Processing: $(basename "$file")"
    harmonix-split "$file" --quality $QUALITY --output "$OUTPUT_DIR"
done

echo "Done! Processed $(ls "$ALBUM_DIR"/*.mp3 | wc -l) files"
```

### With Find Command

```bash
# Find and process all audio files recursively
find . -name "*.mp3" -exec harmonix-split {} --output ./all_stems \;

# Process only files larger than 1MB
find . -name "*.mp3" -size +1M -exec harmonix-split {} \;
```

### Conditional Processing

```bash
# Analyze first, then decide
harmonix-split song.mp3 --analyze-only

# Based on analysis, process accordingly
if [ $COMPLEXITY -gt 4 ]; then
    harmonix-split song.mp3 --mode per_instrument
else
    harmonix-split song.mp3 --mode grouped
fi
```

### Pipeline Integration

```bash
# Chain with other tools
harmonix-split song.mp3 --mode karaoke && \
  ffmpeg -i ./harmonix_output/song_instrumental.mp3 -ar 44100 instrumental.wav

# Process and archive
harmonix-split song.mp3 && \
  tar -czf stems.tar.gz ./harmonix_output/
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | File not found |
| 4 | Unsupported format |
| 5 | Processing error |
| 130 | Interrupted (Ctrl+C) |

### Using Exit Codes

```bash
# Check for success
harmonix-split song.mp3
if [ $? -eq 0 ]; then
    echo "Success!"
else
    echo "Failed with code: $?"
fi
```

---

## Environment Variables

The CLI respects these environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `HARMONIX_USE_GPU` | Enable GPU processing | `true` |
| `HARMONIX_DEFAULT_QUALITY` | Default quality mode | `balanced` |
| `HARMONIX_DEFAULT_MODE` | Default separation mode | `grouped` |
| `HARMONIX_OUTPUT_DIR` | Default output directory | `./harmonix_output` |

```bash
# Set environment variables
export HARMONIX_USE_GPU=false
export HARMONIX_DEFAULT_QUALITY=fast

# Then run CLI
harmonix-split song.mp3  # Uses env var settings
```

---

## Performance Tips

### 1. Use Appropriate Quality

```bash
# Testing: use fast
harmonix-split song.mp3 --quality fast

# Final output: use studio
harmonix-split song.mp3 --quality studio
```

### 2. Batch Similar Files

```bash
# Process similar duration files together
harmonix-split short/*.mp3 --quality fast
harmonix-split long/*.mp3 --quality balanced
```

### 3. Monitor Memory

```bash
# For long files on limited RAM, use CPU mode
harmonix-split long_file.mp3 --cpu-only
```

### 4. Parallel Processing

```bash
# Use GNU parallel for multiple files
ls *.mp3 | parallel harmonix-split {} --output ./stems
```

---

## Troubleshooting

### "File not found"

```bash
# Check file exists
ls -la song.mp3

# Use absolute path
harmonix-split /full/path/to/song.mp3
```

### "Out of memory"

```bash
# Use CPU mode
harmonix-split song.mp3 --cpu-only

# Or use fast quality
harmonix-split song.mp3 --quality fast
```

### "CUDA error"

```bash
# Disable GPU
harmonix-split song.mp3 --cpu-only

# Or set environment
export HARMONIX_USE_GPU=false
harmonix-split song.mp3
```

### "Permission denied"

```bash
# Check output directory permissions
chmod 755 ./output_directory

# Or use a different output
harmonix-split song.mp3 --output ~/Desktop/stems
```

---

## Related Documentation

- [Quickstart Guide](./QUICKSTART.md) - Getting started
- [Stem Separation](./STEM_SEPARATION.md) - Understanding separation
- [Configuration](./CONFIGURATION.md) - Full configuration options

---

*CLI documentation last updated: January 2026*
