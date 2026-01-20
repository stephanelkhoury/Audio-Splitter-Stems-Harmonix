# 🎚️ Audio Processing Guide

**Pitch shifting, time stretching, and audio manipulation**

---

## Table of Contents

- [Overview](#overview)
- [Pitch Shifting](#pitch-shifting)
- [Time Stretching](#time-stretching)
- [Format Conversion](#format-conversion)
- [API Reference](#api-reference)
- [Best Practices](#best-practices)

---

## Overview

Harmonix includes a high-quality **Audio Processor** for manipulating audio:

- 🎹 **Pitch Shifting** - Change pitch without affecting tempo
- ⏱️ **Time Stretching** - Change speed without affecting pitch
- 🔊 **Normalization** - Consistent audio levels
- 🔄 **Format Conversion** - Convert between audio formats
- 🎛️ **Formant Preservation** - Keep vocals sounding natural

---

## Pitch Shifting

### What is Pitch Shifting?

Pitch shifting changes the musical pitch of audio without affecting the duration. For example:
- Transpose a song up 2 semitones (whole step)
- Lower vocals by 5 semitones
- Create harmonies by pitch-shifting

### Algorithms

| Algorithm | Speed | Quality | Best For |
|-----------|-------|---------|----------|
| **fast** | Very Fast | Good | Previews |
| **high_quality** | Medium | Very Good | Most uses |
| **ultra** | Slow | Excellent | Final masters |

### Formant Preservation

**Without formant preservation:**
- Shifting up → chipmunk effect
- Shifting down → monster voice

**With formant preservation:**
- Vocals sound natural at any pitch
- Maintains voice character
- Essential for realistic results

### Basic Usage

```python
from harmonix_splitter.audio.processor import AudioProcessor
import numpy as np
import soundfile as sf

# Load audio
audio, sr = sf.read("vocals.wav")

# Create processor
processor = AudioProcessor(sample_rate=sr)

# Pitch shift up 2 semitones
shifted = processor.pitch_shift(
    audio=audio,
    semitones=2.0,
    preserve_formants=True,
    algorithm="high_quality"
)

# Save result
sf.write("vocals_shifted.wav", shifted, sr)
```

### Semitone Reference

| Semitones | Musical Interval | Example |
|-----------|-----------------|---------|
| +12 | One octave up | C4 → C5 |
| +7 | Perfect fifth up | C → G |
| +5 | Perfect fourth up | C → F |
| +2 | Whole step up | C → D |
| +1 | Half step up | C → C# |
| 0 | No change | C → C |
| -1 | Half step down | C → B |
| -2 | Whole step down | C → Bb |
| -5 | Perfect fourth down | C → G |
| -12 | One octave down | C4 → C3 |

### Dashboard Pitch Shifting

The web dashboard includes real-time pitch shifting:

1. Load a processed track
2. Select a stem (e.g., vocals)
3. Use the pitch slider (-12 to +12 semitones)
4. Preview in real-time
5. Download shifted audio

```javascript
// Dashboard pitch shift API
fetch(`/pitch-shift/${jobId}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        stem: 'vocals',
        semitones: 2.0,
        preserve_formants: true
    })
});
```

---

## Time Stretching

### What is Time Stretching?

Time stretching changes the duration of audio without affecting pitch:
- Speed up a track for faster tempo
- Slow down for practice/learning
- Match tempo between songs (DJ mixing)

### Basic Usage

```python
from harmonix_splitter.audio.processor import AudioProcessor

processor = AudioProcessor(sample_rate=44100)

# Speed up by 1.5x (50% faster)
stretched = processor._time_stretch(
    audio=audio,
    rate=1.5,
    n_fft=2048,
    hop_length=512
)

# Slow down to 0.75x (25% slower)
stretched = processor._time_stretch(
    audio=audio,
    rate=0.75,
    n_fft=2048,
    hop_length=512
)
```

### Rate Values

| Rate | Effect | Use Case |
|------|--------|----------|
| 2.0 | Double speed | Quick preview |
| 1.5 | 50% faster | Tempo matching |
| 1.0 | No change | Original |
| 0.75 | 25% slower | Practice mode |
| 0.5 | Half speed | Detailed learning |

### Quality Considerations

Higher quality settings for time stretching:
- Larger `n_fft` (4096) = better quality
- Smaller `hop_length` (256) = more detail
- Trade-off: slower processing

---

## Format Conversion

### Supported Formats

**Input Formats:**
- MP3 (.mp3)
- WAV (.wav)
- FLAC (.flac)
- M4A (.m4a)
- AAC (.aac)
- OGG Vorbis (.ogg)

**Output Formats:**
- MP3 (320 kbps default)
- WAV (16/24/32-bit)
- FLAC (lossless compression)

### Using FFmpeg Conversion

```python
from harmonix_splitter.core.preprocessor import AudioPreprocessor

preprocessor = AudioPreprocessor(target_sr=44100)

# Convert to WAV
preprocessor.convert_with_ffmpeg(
    input_path="song.mp3",
    output_path="song.wav",
    format="wav"
)

# Convert to high-quality MP3
preprocessor.convert_with_ffmpeg(
    input_path="song.wav",
    output_path="song.mp3",
    format="mp3",
    bitrate="320k"
)
```

### Quality Settings

#### MP3 Bitrates

| Bitrate | Quality | File Size |
|---------|---------|-----------|
| 128 kbps | Basic | Small |
| 192 kbps | Good | Medium |
| 256 kbps | Very Good | Larger |
| 320 kbps | Excellent | Large |

#### WAV Bit Depths

| Bit Depth | Dynamic Range | File Size |
|-----------|---------------|-----------|
| 16-bit | 96 dB | Standard |
| 24-bit | 144 dB | 1.5x |
| 32-bit float | Unlimited | 2x |

---

## Normalization

### Peak Normalization

```python
from harmonix_splitter.core.preprocessor import AudioPreprocessor

# Normalize to -3 dB peak
normalized = AudioPreprocessor._normalize_audio(
    audio,
    target_db=-3.0
)
```

### Why Normalize?

1. **Consistent levels** - All stems at similar loudness
2. **Prevent clipping** - Avoid distortion
3. **Better comparison** - A/B test without volume differences
4. **Professional output** - Industry-standard levels

---

## API Reference

### AudioProcessor Class

```python
class AudioProcessor:
    """
    High-quality audio processor for pitch shifting and manipulation.
    """
    
    def __init__(self, sample_rate: int = 44100):
        """
        Initialize audio processor.
        
        Args:
            sample_rate: Target sample rate
        """
    
    def pitch_shift(
        self,
        audio: np.ndarray,
        semitones: float,
        preserve_formants: bool = True,
        algorithm: str = "high_quality"
    ) -> np.ndarray:
        """
        High-quality pitch shifting with formant preservation.
        
        Args:
            audio: Input audio (mono or stereo)
            semitones: Pitch shift (-12 to +12)
            preserve_formants: Keep vocals natural
            algorithm: "fast", "high_quality", or "ultra"
            
        Returns:
            Pitch-shifted audio
        """
```

### PitchShiftConfig

```python
@dataclass
class PitchShiftConfig:
    """Configuration for pitch shifting."""
    semitones: float = 0.0        # -12 to +12
    preserve_formants: bool = True # Keep voice natural
    algorithm: str = "high_quality"
```

---

## Best Practices

### 1. Use Formant Preservation for Vocals

```python
# GOOD - Natural sounding vocals
shifted = processor.pitch_shift(
    audio=vocals,
    semitones=3,
    preserve_formants=True
)

# BAD - Chipmunk/monster effect
shifted = processor.pitch_shift(
    audio=vocals,
    semitones=3,
    preserve_formants=False
)
```

### 2. Process Stems Individually

```python
# Process each stem separately for best quality
for stem_name, stem_audio in stems.items():
    shifted = processor.pitch_shift(stem_audio, semitones=2)
    save_audio(f"{stem_name}_shifted.wav", shifted)
```

### 3. Limit Extreme Shifts

```python
# Keep shifts reasonable for best quality
# Beyond ±5 semitones, quality degrades
if abs(semitones) > 5:
    print("Warning: Large pitch shifts may affect quality")
```

### 4. Choose Algorithm by Use Case

```python
# Preview/testing
quick_shift = processor.pitch_shift(audio, 2, algorithm="fast")

# Production
final_shift = processor.pitch_shift(audio, 2, algorithm="ultra")
```

### 5. Consider Sample Rate

```python
# Higher sample rate = better quality
processor = AudioProcessor(sample_rate=48000)

# Match output sample rate to source
source_sr = 44100
processor = AudioProcessor(sample_rate=source_sr)
```

---

## Example Workflows

### Karaoke Key Change

```python
# Change song key for easier singing
from harmonix_splitter import create_separator
from harmonix_splitter.audio.processor import AudioProcessor

# 1. Separate stems
separator = create_separator(mode="karaoke")
stems = separator.separate("song.mp3", output_dir="./output")

# 2. Pitch shift instrumental only
processor = AudioProcessor()
shifted_instrumental = processor.pitch_shift(
    stems["instrumental"].audio,
    semitones=-2,  # Lower by 2 semitones
    preserve_formants=False  # Instruments don't need formant preservation
)

# 3. Save result
import soundfile as sf
sf.write("instrumental_lowered.wav", shifted_instrumental, 44100)
```

### Harmony Creation

```python
# Create harmony vocals
processor = AudioProcessor()

# Original vocals
original = stems["vocals"].audio

# Create harmonies
harmony_3rd = processor.pitch_shift(original, semitones=4)  # Major 3rd up
harmony_5th = processor.pitch_shift(original, semitones=7)  # Perfect 5th up

# Mix together
import numpy as np
harmony_mix = original * 0.7 + harmony_3rd * 0.2 + harmony_5th * 0.1
```

### Practice Mode (Slow Down)

```python
# Slow down for learning
processor = AudioProcessor()

# Slow to 75% speed without changing pitch
slow_audio = processor._time_stretch(audio, rate=0.75, n_fft=4096, hop_length=256)
```

---

## Troubleshooting

### Artifacts in Shifted Audio

1. Use `high_quality` or `ultra` algorithm
2. Enable formant preservation for vocals
3. Keep shift within ±5 semitones

### Performance Issues

1. Use `fast` algorithm for previews
2. Process shorter segments
3. Reduce sample rate temporarily

### Phase Issues in Stereo

Process left and right channels consistently:

```python
if audio.ndim == 2 and audio.shape[0] == 2:
    # Stereo - process both channels
    left = processor.pitch_shift(audio[0], semitones)
    right = processor.pitch_shift(audio[1], semitones)
    result = np.stack([left, right])
```

---

## Related Documentation

- [Stem Separation](./STEM_SEPARATION.md) - Get individual stems
- [Music Analysis](./MUSIC_ANALYSIS.md) - BPM and key detection
- [Supported Formats](./SUPPORTED_FORMATS.md) - Audio format details

---

*Audio processing documentation last updated: January 2026*
