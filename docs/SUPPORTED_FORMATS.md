# 📁 Supported Formats

**Complete guide to input and output audio formats**

---

## Table of Contents

- [Overview](#overview)
- [Input Formats](#input-formats)
- [Output Formats](#output-formats)
- [Format Conversion](#format-conversion)
- [Quality Considerations](#quality-considerations)
- [Sample Rate and Bit Depth](#sample-rate-and-bit-depth)

---

## Overview

Harmonix supports a wide range of audio formats for maximum compatibility:

| Category | Formats |
|----------|---------|
| **Input** | MP3, WAV, FLAC, M4A, AAC, OGG, WMA, AIFF |
| **Output** | MP3, WAV, FLAC |

---

## Input Formats

### Fully Supported

| Format | Extension | Notes |
|--------|-----------|-------|
| **MP3** | `.mp3` | Most common, all bitrates |
| **WAV** | `.wav` | Uncompressed, best quality |
| **FLAC** | `.flac` | Lossless compression |
| **M4A** | `.m4a` | Apple format, AAC codec |
| **AAC** | `.aac` | Advanced Audio Coding |
| **OGG** | `.ogg` | Vorbis codec |
| **AIFF** | `.aiff`, `.aif` | Apple lossless |
| **WMA** | `.wma` | Windows Media Audio |

### Format Details

#### MP3 (MPEG Audio Layer III)

```
Supported:
✅ All bitrates (64-320 kbps)
✅ CBR (Constant Bit Rate)
✅ VBR (Variable Bit Rate)
✅ ID3 tags preserved

Recommended input: 256-320 kbps
```

#### WAV (Waveform Audio)

```
Supported:
✅ 16-bit PCM
✅ 24-bit PCM
✅ 32-bit float
✅ All sample rates (44.1kHz, 48kHz, 96kHz, etc.)

Best for: Maximum quality source
```

#### FLAC (Free Lossless Audio Codec)

```
Supported:
✅ All compression levels (0-8)
✅ 16-bit and 24-bit
✅ All sample rates
✅ Metadata preserved

Best for: Archival quality source
```

#### M4A/AAC

```
Supported:
✅ AAC-LC (Low Complexity)
✅ HE-AAC (High Efficiency)
✅ iTunes downloads
✅ Apple Music files

Note: DRM-protected files not supported
```

#### OGG Vorbis

```
Supported:
✅ All quality levels
✅ Variable bitrate
✅ Open format

Common with: YouTube downloads, games
```

---

## Output Formats

### Available Output Formats

| Format | Extension | Type | Size | Quality |
|--------|-----------|------|------|---------|
| **WAV** | `.wav` | Lossless | Large | Best |
| **FLAC** | `.flac` | Lossless | Medium | Best |
| **MP3** | `.mp3` | Lossy | Small | Very Good |

### Setting Output Format

```bash
# CLI
harmonix process song.mp3 --output-format wav
harmonix process song.mp3 --output-format flac
harmonix process song.mp3 --output-format mp3

# Environment variable
export HARMONIX_OUTPUT_FORMAT=wav
```

```yaml
# config/config.yaml
output:
  format: wav  # wav, flac, mp3
  mp3_bitrate: 320  # kbps for MP3
```

### Output Format Comparison

#### WAV Output

```
Pros:
✅ Maximum quality (no compression)
✅ Wide compatibility
✅ Good for further editing

Cons:
❌ Large file sizes (~10MB per minute)
❌ No metadata support

Use when: Quality is paramount
File size: ~180MB for 4 stems (3-min song)
```

#### FLAC Output

```
Pros:
✅ Lossless compression
✅ 50-70% size of WAV
✅ Metadata support
✅ Bit-perfect quality

Cons:
❌ Less DAW compatibility
❌ Requires decoding

Use when: Archival, quality + smaller size
File size: ~90MB for 4 stems (3-min song)
```

#### MP3 Output

```
Pros:
✅ Smallest file size
✅ Universal compatibility
✅ Good quality at 320kbps
✅ Metadata support

Cons:
❌ Lossy compression
❌ Generation loss if re-encoded

Use when: Sharing, streaming, storage
File size: ~30MB for 4 stems (3-min song)
```

---

## Format Conversion

### Pre-Processing Conversion

Harmonix automatically converts input to internal format:

```
Input (any format)
       ↓
  [librosa load]
       ↓
Internal (float32, mono/stereo, 44.1kHz)
       ↓
  [Demucs processing]
       ↓
Output (selected format)
```

### Manual Conversion

Convert files before processing:

```bash
# Convert to WAV (best quality)
ffmpeg -i input.m4a -acodec pcm_s16le -ar 44100 output.wav

# Convert to high-quality MP3
ffmpeg -i input.wma -acodec libmp3lame -b:a 320k output.mp3

# Convert to FLAC
ffmpeg -i input.aiff -acodec flac output.flac
```

### Batch Conversion

```bash
# Convert all M4A files to WAV
for f in *.m4a; do
    ffmpeg -i "$f" -acodec pcm_s16le "${f%.m4a}.wav"
done
```

---

## Quality Considerations

### Input Quality Recommendations

| Purpose | Minimum | Recommended |
|---------|---------|-------------|
| Testing | 128 kbps MP3 | Any |
| General use | 256 kbps MP3 | WAV/FLAC |
| Professional | WAV/FLAC | 24-bit WAV |

### Quality Chain

```
Rule: Output can never be better than input

Low quality input → Low quality output
High quality input → High quality output

Example:
128 kbps MP3 input → Even studio mode can't recover lost data
WAV input → Best possible separation quality
```

### Recommended Workflow

```
For best results:

1. Start with highest quality source
   • Original WAV/FLAC if available
   • CD rip (16-bit/44.1kHz WAV)
   • High-bitrate stream (320 kbps)

2. Process with appropriate quality mode
   • Studio mode for best results
   • Balanced for general use

3. Export in needed format
   • WAV for further editing
   • FLAC for archival
   • MP3 for sharing
```

---

## Sample Rate and Bit Depth

### Sample Rates

| Sample Rate | Usage | Support |
|-------------|-------|---------|
| 44.1 kHz | CD standard, most music | ✅ Native |
| 48 kHz | Video standard | ✅ Resampled |
| 96 kHz | High-res audio | ✅ Resampled |
| 192 kHz | Studio master | ✅ Resampled |

### Bit Depth

| Bit Depth | Dynamic Range | Support |
|-----------|---------------|---------|
| 16-bit | 96 dB | ✅ Full |
| 24-bit | 144 dB | ✅ Full |
| 32-bit float | 1528 dB | ✅ Full |

### Internal Processing

```
All audio is processed internally as:
• Sample rate: 44.1 kHz (Demucs requirement)
• Bit depth: 32-bit float
• Channels: Stereo

High-resolution audio is:
1. Resampled to 44.1 kHz
2. Processed
3. Resampled back to original rate (if requested)
```

---

## Mono vs Stereo

### Input Handling

```
Stereo input → Processed as stereo → Stereo output
Mono input → Converted to stereo → Stereo output
```

### Channel Configuration

```python
# Demucs processes stereo
# Mono files are converted automatically

# Force mono output (not recommended)
# Use audio editing software after processing
```

---

## File Size Reference

### Input File Sizes (3-minute song)

| Format | Size |
|--------|------|
| WAV 16-bit | ~30 MB |
| WAV 24-bit | ~45 MB |
| FLAC | ~15-20 MB |
| MP3 320 | ~7 MB |
| MP3 128 | ~3 MB |

### Output File Sizes (4 stems, 3 minutes)

| Format | Total Size |
|--------|------------|
| WAV 16-bit | ~120 MB |
| FLAC | ~60-80 MB |
| MP3 320 | ~28 MB |

---

## Troubleshooting Format Issues

### "Unsupported format" Error

```bash
# Convert using FFmpeg
ffmpeg -i problem_file.xyz output.wav

# Or use libav
avconv -i problem_file.xyz output.wav
```

### "Codec not found" Error

```bash
# Install FFmpeg with all codecs
# Ubuntu
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from ffmpeg.org
```

### Corrupted Output

```bash
# Check input file
ffprobe input.mp3

# Re-encode input
ffmpeg -i input.mp3 -acodec libmp3lame -b:a 320k clean.mp3
```

---

## Related Documentation

- [Installation](./INSTALLATION.md) - FFmpeg setup
- [Configuration](./CONFIGURATION.md) - Format settings
- [Quality Modes](./QUALITY_MODES.md) - Processing quality
- [Troubleshooting](./TROUBLESHOOTING.md) - Common issues

---

*Supported formats documentation last updated: January 2026*
