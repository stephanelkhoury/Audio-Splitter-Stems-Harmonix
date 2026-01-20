# 🎵 Stem Separation Guide

**Understanding how Harmonix separates audio into individual stems**

---

## Table of Contents

- [What is Stem Separation?](#what-is-stem-separation)
- [How It Works](#how-it-works)
- [Separation Modes](#separation-modes)
- [Quality Presets](#quality-presets)
- [Available Stems](#available-stems)
- [Technical Details](#technical-details)
- [Best Practices](#best-practices)

---

## What is Stem Separation?

**Stem separation** (also called source separation) is the process of isolating individual audio sources from a mixed audio track. For example, taking a song and extracting:

- 🎤 Vocals (singer's voice)
- 🥁 Drums (percussion)
- 🎸 Bass (bass guitar/synth bass)
- 🎹 Other instruments (guitars, keys, etc.)

### Use Cases

| Use Case | Description |
|----------|-------------|
| **Karaoke** | Remove vocals to sing along |
| **Remixing** | Isolate elements for new arrangements |
| **Practice** | Play along with specific instruments |
| **Transcription** | Isolate parts for accurate notation |
| **Sampling** | Extract clean samples |
| **Mastering** | Fix problems in individual stems |

---

## How It Works

Harmonix uses **Demucs v4** by Meta Research, a state-of-the-art deep learning model for audio source separation.

### Processing Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                     Input Audio File                         │
│              (MP3, WAV, FLAC, M4A, OGG, AAC)                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 1: Preprocessing                                      │
│  • Audio loading and validation                              │
│  • Sample rate conversion (to 44.1kHz)                       │
│  • Stereo conversion if needed                               │
│  • Normalization                                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 2: Instrument Detection (Optional)                   │
│  • Analyze audio content                                     │
│  • Detect which instruments are present                      │
│  • Calculate confidence scores                               │
│  • Recommend optimal processing mode                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 3: Demucs Neural Network                             │
│  • Hybrid transformer architecture                           │
│  • Waveform + spectrogram processing                         │
│  • GPU accelerated inference                                 │
│  • Test-time augmentation (TTA) for quality                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 4: Post-processing                                   │
│  • Output format conversion                                  │
│  • Sample rate restoration                                   │
│  • File export (MP3/WAV)                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Output: Separated Stem Files                               │
│  • vocals.mp3, drums.mp3, bass.mp3, etc.                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Separation Modes

### 1. Grouped Mode (Default)

Standard 4-stem separation. Best for most use cases.

**Output:**
- `vocals` - All vocal content
- `drums` - Drums and percussion
- `bass` - Bass instruments
- `other` - Everything else (guitars, synths, keys)

```bash
# CLI usage
python -m harmonix_splitter.cli song.mp3 --mode grouped
```

```python
# Python SDK
separator = create_separator(mode="grouped")
stems = separator.separate("song.mp3")
```

### 2. Per-Instrument Mode

Advanced separation with more individual instruments.

**Output:**
- `vocals` - Vocals
- `drums` - Drums
- `bass` - Bass
- `guitar` - Guitars
- `piano` - Piano/Keys
- `strings` - Orchestral strings
- `synth` - Synthesizers
- `other` - Remaining content

```bash
# CLI usage
python -m harmonix_splitter.cli song.mp3 --mode per_instrument
```

```python
# Python SDK
separator = create_separator(mode="per_instrument")
stems = separator.separate("song.mp3")
```

### 3. Karaoke Mode

2-stem separation optimized for karaoke.

**Output:**
- `vocals` - Isolated vocals
- `instrumental` - Full instrumental backing

```bash
# CLI usage
python -m harmonix_splitter.cli song.mp3 --mode karaoke
```

```python
# Python SDK
separator = create_separator(mode="karaoke")
stems = separator.separate("song.mp3")
```

### 4. Custom Instrument Selection

Select specific instruments to extract.

```bash
# CLI: Extract only vocals and drums
python -m harmonix_splitter.cli song.mp3 --instruments vocals,drums

# CLI: Extract vocals, bass, and guitar
python -m harmonix_splitter.cli song.mp3 --instruments vocals,bass,guitar
```

```python
# Python SDK
separator = create_separator(
    mode="per_instrument",
    target_instruments=["vocals", "drums", "bass"]
)
stems = separator.separate("song.mp3")
```

---

## Quality Presets

### Draft Quality (New!)

Ultra-fast processing for quick previews.

| Setting | Value |
|---------|-------|
| Model | htdemucs |
| Shifts | 0 |
| Overlap | 0.05 |
| Speed | ~5x faster than Fast |

### Fast Quality

Optimized for speed with good quality.

| Setting | Value |
|---------|-------|
| Model | htdemucs |
| Shifts | 0 |
| Overlap | 0.1 |
| Use Case | Quick tests, previews |

### Balanced Quality (Default)

Best balance of speed and quality.

| Setting | Value |
|---------|-------|
| Model | htdemucs_ft (fine-tuned) |
| Shifts | 1 |
| Overlap | 0.25 |
| Use Case | Most production work |

### Studio Quality

Maximum quality for professional use.

| Setting | Value |
|---------|-------|
| Model | htdemucs_6s (6-source) |
| Shifts | 5 |
| Overlap | 0.5 |
| Use Case | Final masters, critical work |

### Quality Comparison

| Quality | Speed (3min song) | SDR Improvement | Best For |
|---------|-------------------|-----------------|----------|
| Draft | ~10-15 sec | Baseline | Quick checks |
| Fast | ~20-30 sec | +0.5 dB | Testing, demos |
| Balanced | ~1-2 min | +1.0 dB | Most work |
| Studio | ~3-5 min | +1.5 dB | Professional |

*SDR = Signal-to-Distortion Ratio. Higher is better.*

---

## Available Stems

### Core Stems (Always Available)

| Stem | Description | Typical Content |
|------|-------------|-----------------|
| **vocals** | Human voices | Lead vocals, backing vocals, harmonies |
| **drums** | Percussion | Kicks, snares, hi-hats, cymbals, toms |
| **bass** | Low-frequency | Bass guitar, synth bass, sub bass |
| **other** | Remaining | Guitars, keys, synths, effects |

### Extended Stems (Per-Instrument Mode)

| Stem | Description | Typical Content |
|------|-------------|-----------------|
| **guitar** | String guitars | Electric, acoustic, clean, distorted |
| **piano** | Keys | Piano, electric piano, organ |
| **strings** | Orchestral | Violins, violas, cellos, orchestral |
| **synth** | Electronic | Synthesizers, pads, electronic leads |
| **brass** | Wind brass | Trumpets, saxophones, trombones |
| **woodwinds** | Wind wood | Flutes, clarinets, oboes |

---

## Technical Details

### Demucs Architecture

Harmonix uses the **Hybrid Transformer Demucs (HTDemucs)** model:

```
Input Waveform
      │
      ├──────────────────────────┐
      │                          │
      ▼                          ▼
┌───────────┐              ┌───────────┐
│  Waveform │              │ Spectrogram│
│  Encoder  │              │  Encoder   │
│  (1D CNN) │              │  (2D CNN)  │
└─────┬─────┘              └─────┬─────┘
      │                          │
      │    ┌─────────────────┐   │
      └───►│   Transformer    │◄──┘
           │  Cross-Attention │
           └────────┬────────┘
                    │
           ┌────────┴────────┐
           │                 │
      ┌────▼────┐      ┌────▼────┐
      │ Waveform│      │Spectrogram│
      │ Decoder │      │ Decoder  │
      └────┬────┘      └────┬────┘
           │                │
           └────────┬───────┘
                    │
                    ▼
           Separated Sources
```

### Model Variants

| Model | Sources | Description |
|-------|---------|-------------|
| htdemucs | 4 | Standard hybrid transformer |
| htdemucs_ft | 4 | Fine-tuned on more data |
| htdemucs_6s | 6 | 6-source: vocals, drums, bass, guitar, piano, other |

### Test-Time Augmentation (TTA)

TTA improves quality by:
1. Processing multiple shifted versions
2. Averaging results
3. Reducing artifacts and noise

The `shifts` parameter controls how many versions are processed:
- 0 shifts: No TTA (fastest)
- 1 shift: Minimal TTA (balanced)
- 5+ shifts: Maximum quality (slowest)

### Memory Usage

| Configuration | VRAM Required |
|--------------|---------------|
| Fast mode | ~4 GB |
| Balanced mode | ~6 GB |
| Studio mode | ~8 GB |
| Long files (>10 min) | ~12 GB |

---

## Best Practices

### 1. Choose the Right Quality

```python
# For testing/previews
separator = create_separator(quality="fast")

# For production
separator = create_separator(quality="balanced")

# For final masters
separator = create_separator(quality="studio")
```

### 2. Use GPU When Available

GPU processing is 5-10x faster than CPU.

```python
# Check GPU availability
import torch
if torch.cuda.is_available():
    print("CUDA GPU available")
elif torch.backends.mps.is_available():
    print("Apple Silicon GPU available")
else:
    print("CPU only - processing will be slower")
```

### 3. Optimize for Long Files

For files > 5 minutes, use segmentation:

```python
config = SeparationConfig(
    segment_duration=30,  # Process in 30-second chunks
    overlap=0.25          # 25% overlap between segments
)
separator = HarmonixSeparator(config)
```

### 4. Input Quality Matters

- Higher quality input = better separation
- Avoid heavily compressed audio (low bitrate MP3)
- Lossless formats (WAV, FLAC) give best results

### 5. Post-Processing Tips

- Some bleed between stems is normal
- Use EQ to further clean stems if needed
- Combine stems for custom mixes:

```python
import numpy as np

# Create custom instrumental
instrumental = stems['drums'].audio + stems['bass'].audio + stems['other'].audio
```

---

## Code Examples

### Complete Separation Workflow

```python
from harmonix_splitter import create_orchestrator
from pathlib import Path

# Create orchestrator
orchestrator = create_orchestrator(auto_route=True)

# Process with full pipeline
result = orchestrator.process(
    audio_path="song.mp3",
    job_id="my_song",
    quality="balanced",
    mode="per_instrument",
    output_dir="./output"
)

# Check results
if result.status == "completed":
    print(f"✅ Completed in {result.processing_time:.1f}s")
    print(f"Detected: {result.detected_instruments}")
    
    for stem_name, stem in result.stems.items():
        print(f"  - {stem_name}: {stem.audio.shape}")
else:
    print(f"❌ Failed: {result.metadata.get('error')}")
```

### Batch Processing

```python
from harmonix_splitter import create_orchestrator
from pathlib import Path

orchestrator = create_orchestrator()

# Process multiple files
audio_files = list(Path("./songs").glob("*.mp3"))

results = orchestrator.batch_process(
    audio_paths=audio_files,
    base_job_id="batch",
    quality="fast",
    mode="grouped"
)

# Summary
completed = sum(1 for r in results if r.status == "completed")
print(f"Processed {completed}/{len(results)} files")
```

---

## Related Documentation

- [Instrument Detection](./INSTRUMENT_DETECTION.md) - How detection works
- [Quality Modes](./QUALITY_MODES.md) - Detailed quality comparison
- [Audio Processing](./AUDIO_PROCESSING.md) - Pitch shifting, effects
- [CLI Guide](./CLI_GUIDE.md) - Command-line reference

---

*Stem separation documentation last updated: January 2026*
