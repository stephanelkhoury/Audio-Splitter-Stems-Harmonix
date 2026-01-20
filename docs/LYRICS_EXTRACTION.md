# 🎤 Lyrics Extraction Guide

**Extracting lyrics with word-level timing using OpenAI Whisper**

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Supported Languages](#supported-languages)
- [How It Works](#how-it-works)
- [Using Lyrics Extraction](#using-lyrics-extraction)
- [Output Formats](#output-formats)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Best Practices](#best-practices)

---

## Overview

Harmonix includes a powerful **Lyrics Extraction** system powered by OpenAI's Whisper model. It provides:

- 🎤 **Speech-to-Text** - Accurate transcription of vocals
- ⏱️ **Word-Level Timing** - Precise timestamps for each word
- 🌍 **Multi-Language** - Support for 99+ languages
- 🎵 **Karaoke Export** - LRC and SRT format generation
- 🧠 **Hallucination Filtering** - Removes common AI errors

---

## Features

### Transcription Capabilities

| Feature | Description |
|---------|-------------|
| **Multi-Language** | Auto-detect or specify language |
| **Word Timing** | Millisecond-accurate word positions |
| **Line Segmentation** | Intelligent line breaks |
| **Punctuation** | Automatic punctuation insertion |
| **Confidence Scores** | Per-word reliability scores |

### Export Formats

| Format | Extension | Use Case |
|--------|-----------|----------|
| **Plain Text** | .txt | General use |
| **LRC** | .lrc | Karaoke players |
| **SRT** | .srt | Video subtitles |
| **JSON** | .json | Programmatic access |
| **VTT** | .vtt | Web video subtitles |

---

## Supported Languages

### Primary Languages (Best Support)

| Code | Language | Accuracy |
|------|----------|----------|
| `en` | English | Excellent |
| `es` | Spanish | Excellent |
| `fr` | French | Excellent |
| `de` | German | Excellent |
| `it` | Italian | Excellent |
| `pt` | Portuguese | Excellent |
| `ar` | Arabic | Very Good |
| `ja` | Japanese | Very Good |
| `ko` | Korean | Very Good |
| `zh` | Chinese | Very Good |

### Language Auto-Detection

```python
# Auto-detect language
extractor = LyricsExtractor()
result = extractor.extract("song.mp3", language="auto")
print(f"Detected language: {result.language}")
```

---

## How It Works

### Processing Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│  Input Audio (or Vocals Stem)                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Audio Preprocessing                                         │
│  • Sample rate conversion (16kHz)                           │
│  • Mono conversion                                           │
│  • Normalization                                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Whisper Model Inference                                    │
│  • Language detection (if auto)                             │
│  • Speech recognition                                        │
│  • Timestamp generation                                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Post-Processing                                             │
│  • Hallucination filtering                                   │
│  • Line segmentation                                         │
│  • Punctuation normalization                                 │
│  • Timing adjustment                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Output: LyricsResult                                        │
│  • Full text                                                 │
│  • Timed lines with word-level timing                       │
│  • Language information                                      │
│  • Export to LRC/SRT/JSON                                   │
└─────────────────────────────────────────────────────────────┘
```

### Whisper Model Sizes

| Size | Parameters | VRAM | Speed | Accuracy |
|------|------------|------|-------|----------|
| tiny | 39M | ~1 GB | Very Fast | Basic |
| base | 74M | ~1 GB | Fast | Good |
| small | 244M | ~2 GB | Medium | Better |
| medium | 769M | ~5 GB | Slower | Great |
| large-v3 | 1.5B | ~10 GB | Slow | Best |

Default: **medium** (best balance of speed and accuracy)

---

## Using Lyrics Extraction

### Basic Usage

```python
from harmonix_splitter.audio.lyrics import LyricsExtractor

# Create extractor
extractor = LyricsExtractor(model_size="medium")

# Extract lyrics
result = extractor.extract("vocals.mp3")

# Get full text
print(result.text)

# Get timed lines
for line in result.lines:
    print(f"[{line.start_time:.2f}s] {line.text}")
```

### With Language Specification

```python
# Specify language for better accuracy
result = extractor.extract(
    "vocals.mp3",
    language="ar"  # Arabic
)

print(f"Language: {result.language}")
print(f"Confidence: {result.language_confidence:.1%}")
```

### Export to Formats

```python
# Extract lyrics
result = extractor.extract("vocals.mp3")

# Export to LRC (karaoke)
lrc_content = result.to_lrc()
with open("lyrics.lrc", "w") as f:
    f.write(lrc_content)

# Export to SRT (subtitles)
srt_content = result.to_srt()
with open("lyrics.srt", "w") as f:
    f.write(srt_content)

# Export to JSON
import json
json_content = result.to_dict()
with open("lyrics.json", "w") as f:
    json.dump(json_content, f, ensure_ascii=False, indent=2)
```

### Dashboard Integration

In the web dashboard:
1. Process a song
2. Click "Extract Lyrics" button
3. View synchronized lyrics
4. Download in preferred format

---

## Output Formats

### LRC Format

```
[00:05.23]Welcome to the jungle
[00:08.45]We've got fun and games
[00:12.10]We got everything you want
[00:15.80]Honey, we know the names
```

### SRT Format

```
1
00:00:05,230 --> 00:00:08,450
Welcome to the jungle

2
00:00:08,450 --> 00:00:12,100
We've got fun and games

3
00:00:12,100 --> 00:00:15,800
We got everything you want
```

### JSON Format

```json
{
  "text": "Welcome to the jungle...",
  "language": "en",
  "language_confidence": 0.98,
  "duration": 240.5,
  "lines": [
    {
      "text": "Welcome to the jungle",
      "start": 5.23,
      "end": 8.45,
      "confidence": 0.95,
      "words": [
        {"word": "Welcome", "start": 5.23, "end": 5.82},
        {"word": "to", "start": 5.82, "end": 6.01},
        {"word": "the", "start": 6.01, "end": 6.24},
        {"word": "jungle", "start": 6.24, "end": 8.45}
      ]
    }
  ]
}
```

---

## Configuration

### Model Selection

```python
# Fast transcription (lower accuracy)
extractor = LyricsExtractor(model_size="base")

# Best quality (slower)
extractor = LyricsExtractor(model_size="large")
```

### Device Selection

```python
# Force CPU
extractor = LyricsExtractor(device="cpu")

# Force CUDA
extractor = LyricsExtractor(device="cuda")

# Auto-detect (default)
extractor = LyricsExtractor(device=None)
```

### Thread Count

```python
# Maximize CPU threads
extractor = LyricsExtractor(
    model_size="medium",
    num_threads=8  # Or os.cpu_count()
)
```

---

## API Reference

### LyricsExtractor Class

```python
class LyricsExtractor:
    """
    Extract lyrics from audio using OpenAI Whisper.
    """
    
    SUPPORTED_LANGUAGES = {
        'auto': None,
        'en': 'english',
        'ar': 'arabic',
        'fr': 'french',
        'es': 'spanish',
        'de': 'german',
        # ... more languages
    }
    
    MODEL_SIZES = {
        'tiny': 'tiny',
        'base': 'base',
        'small': 'small',
        'medium': 'medium',
        'large': 'large-v3'
    }
    
    def __init__(
        self,
        model_size: str = "medium",
        device: Optional[str] = None,
        num_threads: Optional[int] = None
    ):
        """
        Initialize lyrics extractor.
        
        Args:
            model_size: Whisper model (tiny/base/small/medium/large)
            device: Device (cuda/cpu/auto)
            num_threads: CPU threads (None = auto)
        """
    
    def extract(
        self,
        audio_path: Union[str, Path],
        language: str = "auto",
        return_word_timing: bool = True
    ) -> LyricsResult:
        """
        Extract lyrics from audio file.
        
        Args:
            audio_path: Path to audio file
            language: Language code or "auto"
            return_word_timing: Include word-level timing
            
        Returns:
            LyricsResult with text, timing, and metadata
        """
```

### Data Classes

```python
@dataclass
class LyricLine:
    """Single line of lyrics with timing."""
    text: str              # Line text
    start_time: float      # Start time (seconds)
    end_time: float        # End time (seconds)
    confidence: float      # Transcription confidence (0-1)
    words: List[Dict]      # Word-level timing
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""


@dataclass
class LyricsResult:
    """Complete lyrics extraction result."""
    text: str                      # Full lyrics text
    lines: List[LyricLine]         # Timed lines
    language: str                  # Detected/specified language
    language_confidence: float     # Language detection confidence
    duration: float                # Audio duration
    
    def to_lrc(self) -> str:
        """Convert to LRC karaoke format."""
    
    def to_srt(self) -> str:
        """Convert to SRT subtitle format."""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
```

---

## Hallucination Filtering

Whisper sometimes generates "hallucinations" - text that doesn't match the audio. Harmonix filters these:

### Common Hallucinations Filtered

**English:**
- "Subscribe to the channel"
- "Thanks for watching"
- "Subtitles by..."
- "Translated by..."

**Arabic:**
- "اشتركوا في القناة" (Subscribe to the channel)
- "شكرا للمشاهدة" (Thanks for watching)
- "المترجمات من قبل" (Translations by)

**Other Languages:**
- Similar promotional/credit text in French, Spanish, Chinese, etc.

### Filtering Logic

```python
# Harmonix automatically filters hallucinations
HALLUCINATION_PATTERNS = [
    'subscribe to the channel',
    'thanks for watching',
    'subtitles by',
    # ... many more patterns
]

def filter_hallucinations(text: str) -> str:
    for pattern in HALLUCINATION_PATTERNS:
        if pattern.lower() in text.lower():
            return ""  # Remove line
    return text
```

---

## Best Practices

### 1. Use Vocals Stem

For best results, extract lyrics from the isolated vocals:

```python
# First, separate stems
stems = separator.separate("song.mp3")

# Then extract lyrics from vocals
extractor = LyricsExtractor()
result = extractor.extract(vocals_path)
```

### 2. Choose Appropriate Model Size

```python
# For real-time/quick results
extractor = LyricsExtractor(model_size="base")

# For accuracy (production)
extractor = LyricsExtractor(model_size="large")
```

### 3. Specify Language When Known

```python
# Better accuracy with known language
result = extractor.extract(
    "arabic_song_vocals.mp3",
    language="ar"  # Specify Arabic
)
```

### 4. Handle Low-Confidence Results

```python
result = extractor.extract("vocals.mp3")

# Filter low-confidence lines
confident_lines = [
    line for line in result.lines 
    if line.confidence > 0.5
]
```

### 5. Post-Process for Quality

```python
# Manual review recommended for:
# - Low language_confidence
# - Songs with heavy effects
# - Multiple overlapping voices
if result.language_confidence < 0.7:
    print("Manual review recommended")
```

---

## Troubleshooting

### Empty or Wrong Lyrics

1. **Use isolated vocals** - Background music confuses Whisper
2. **Check audio quality** - Clear audio = better results
3. **Specify correct language** - Don't rely on auto-detect for rare languages

### Timing Issues

1. **Word timing off** - Normal variance is ±100ms
2. **Line breaks wrong** - Use word timing and re-segment

### Performance Issues

```python
# Use smaller model for speed
extractor = LyricsExtractor(model_size="base")

# Or limit threads
extractor = LyricsExtractor(num_threads=4)
```

### GPU Memory Errors

```python
# Use CPU if GPU memory insufficient
extractor = LyricsExtractor(device="cpu")

# Or use smaller model
extractor = LyricsExtractor(model_size="small")
```

---

## Related Documentation

- [Stem Separation](./STEM_SEPARATION.md) - Get clean vocals first
- [Dashboard Guide](./DASHBOARD.md) - Web UI for lyrics
- [Audio Processing](./AUDIO_PROCESSING.md) - Processing capabilities

---

*Lyrics extraction documentation last updated: January 2026*
