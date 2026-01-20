# 🎼 Music Analysis Guide

**Understanding BPM, Key, Scale, and Music Structure Analysis**

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tempo Analysis](#tempo-analysis)
- [Key Detection](#key-detection)
- [Using Music Analysis](#using-music-analysis)
- [API Reference](#api-reference)
- [Advanced Features](#advanced-features)

---

## Overview

Harmonix includes a powerful **Music Analysis** module that extracts musical information from audio:

- **Tempo (BPM)** - Beats per minute
- **Key & Scale** - Musical key (C, D, E...) and mode (Major/Minor)
- **Time Signature** - 4/4, 3/4, 6/8, etc.
- **Beat Positions** - Precise timing of beats
- **Energy Profile** - Loudness over time
- **Section Detection** - Verse, chorus, bridge identification

This information is useful for:
- DJ mixing and beatmatching
- Music production and remixing
- Playlist organization
- Intelligent audio processing
- Automatic music tagging

---

## Features

### Tempo Analysis

```
┌─────────────────────────────────────────────────────────────┐
│  Tempo Detection Methods                                     │
│                                                              │
│  1. Beat Tracking (librosa)                                 │
│     - Onset envelope analysis                               │
│     - Dynamic programming for beat tracking                 │
│                                                              │
│  2. Onset-Based Tempo                                       │
│     - Onset strength envelope                               │
│     - Autocorrelation analysis                              │
│                                                              │
│  3. Autocorrelation Method                                  │
│     - Periodicity detection                                 │
│     - Multiple tempo hypothesis testing                     │
│                                                              │
│  Final Result: Weighted average of all methods              │
└─────────────────────────────────────────────────────────────┘
```

### Key Detection

Uses the **Krumhansl-Kessler** key-finding algorithm:

```
┌─────────────────────────────────────────────────────────────┐
│  Key Detection Pipeline                                      │
│                                                              │
│  1. Chroma Feature Extraction                               │
│     - 12-bin pitch class distribution                       │
│     - Energy per pitch class (C, C#, D, D#, E, F...)       │
│                                                              │
│  2. Key Profile Correlation                                 │
│     - Compare against major/minor profiles                  │
│     - Test all 24 key/mode combinations                     │
│                                                              │
│  3. Best Match Selection                                    │
│     - Highest correlation = detected key                    │
│     - Confidence from correlation strength                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Tempo Analysis

### BPM Range

| Genre | Typical BPM |
|-------|-------------|
| Hip-Hop | 85-115 |
| Pop | 100-130 |
| House | 120-130 |
| Techno | 130-150 |
| Drum & Bass | 160-180 |
| Rock | 90-140 |
| Classical | Variable |

### Detection Accuracy

| Condition | Accuracy |
|-----------|----------|
| Clear beat (electronic) | 95%+ |
| Acoustic music | 90%+ |
| Complex rhythm | 85%+ |
| Tempo changes | 70-80% |
| Rubato/free tempo | Variable |

### Confidence Score

The confidence score indicates reliability:

| Confidence | Meaning |
|------------|---------|
| 0.9 - 1.0 | Very confident |
| 0.7 - 0.9 | Reliable |
| 0.5 - 0.7 | Moderate |
| 0.3 - 0.5 | Uncertain |
| < 0.3 | Low confidence |

---

## Key Detection

### Supported Keys

All 12 keys with Major and Minor modes:

| Key | Major | Minor |
|-----|-------|-------|
| C | C Major | C Minor (Am) |
| C# | C# Major | C# Minor |
| D | D Major | D Minor |
| D# | D# Major | D# Minor |
| E | E Major | E Minor |
| F | F Major | F Minor |
| F# | F# Major | F# Minor |
| G | G Major | G Minor |
| G# | G# Major | G# Minor |
| A | A Major | A Minor |
| A# | A# Major | A# Minor |
| B | B Major | B Minor |

### Camelot Wheel

The analyzer includes **Camelot Wheel** notation for DJ mixing:

```
       11A ── 12A ── 1A
      /              \
    10A               2A
    |                  |
    9A                3A
    |                  |
    8A                4A
      \              /
        7A ── 6A ── 5A
        
       11B ── 12B ── 1B
      /              \
    10B               2B
    |                  |
    9B                3B
    |                  |
    8B                4B
      \              /
        7B ── 6B ── 5B
```

**Mixing Rules:**
- Same number (8A ↔ 8A): Perfect match
- Adjacent numbers (8A ↔ 7A, 8A ↔ 9A): Harmonic
- Same letter swap (8A ↔ 8B): Relative key

### Key Profile Weights

Krumhansl-Kessler profiles (normalized):

**Major Profile:**
```python
[6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
#  C    C#    D    D#    E     F    F#    G    G#    A    A#    B
```

**Minor Profile:**
```python
[6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
#  C    C#    D    D#    E     F    F#    G    G#    A    A#    B
```

---

## Using Music Analysis

### Basic Usage

```python
from harmonix_splitter.analysis.music_analyzer import MusicAnalyzer

# Create analyzer
analyzer = MusicAnalyzer()

# Analyze audio
analysis = analyzer.analyze("song.mp3")

# Access results
print(f"Tempo: {analysis.tempo.bpm:.1f} BPM")
print(f"Confidence: {analysis.tempo.bpm_confidence:.1%}")
print(f"Key: {analysis.key.key} {analysis.key.scale}")
print(f"Key Confidence: {analysis.key.confidence:.1%}")
print(f"Duration: {analysis.duration:.2f} seconds")
```

### Tempo Analysis Only

```python
from harmonix_splitter.analysis.music_analyzer import MusicAnalyzer
import librosa

# Load audio
y, sr = librosa.load("song.mp3", sr=44100, mono=True)

# Analyze tempo
analyzer = MusicAnalyzer()
tempo = analyzer.analyze_tempo(y, sr)

print(f"BPM: {tempo.bpm:.1f}")
print(f"Confidence: {tempo.bpm_confidence:.1%}")
print(f"Time Signature: {tempo.time_signature[0]}/{tempo.time_signature[1]}")
print(f"Tempo Stability: {tempo.tempo_stability:.1%}")
print(f"Beat Positions: {len(tempo.beat_positions)} beats detected")
```

### Key Analysis Only

```python
from harmonix_splitter.analysis.music_analyzer import MusicAnalyzer
import librosa

# Load audio
y, sr = librosa.load("song.mp3", sr=44100, mono=True)

# Analyze key
analyzer = MusicAnalyzer()
key = analyzer.analyze_key(y, sr)

print(f"Key: {key.key} {key.scale}")
print(f"Confidence: {key.confidence:.1%}")
print(f"Camelot: {analyzer.get_camelot_wheel(key.key, key.scale)}")

# Alternative keys (for modulation)
print("\nAlternative keys:")
for alt_key, alt_scale, alt_confidence in key.alternative_keys[:3]:
    print(f"  {alt_key} {alt_scale}: {alt_confidence:.1%}")
```

### Dashboard Integration

In the web dashboard, music analysis is automatically performed when processing:

```python
# Analysis shown in dashboard UI
music_info = {
    'tempo': {
        'bpm': 128.5,
        'confidence': 0.95
    },
    'key': {
        'key': 'A',
        'scale': 'Minor',
        'confidence': 0.87,
        'camelot': '8A'
    },
    'time_signature': '4/4',
    'duration': 215.3
}
```

---

## API Reference

### MusicAnalyzer Class

```python
class MusicAnalyzer:
    """
    Advanced music analysis for tempo, key detection and structure.
    """
    
    def __init__(
        self,
        sample_rate: int = 44100,
        hop_length: int = 512,
        n_fft: int = 2048
    ):
        """
        Initialize music analyzer.
        
        Args:
            sample_rate: Target sample rate for analysis
            hop_length: Hop length for STFT
            n_fft: FFT size
        """
    
    def analyze(self, audio_path: Path) -> MusicAnalysis:
        """
        Perform complete music analysis.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            MusicAnalysis with tempo, key, and structure
        """
    
    def analyze_tempo(self, y: np.ndarray, sr: int) -> TempoAnalysis:
        """
        Analyze tempo with multiple methods for accuracy.
        
        Args:
            y: Audio signal (mono)
            sr: Sample rate
            
        Returns:
            TempoAnalysis with BPM and beat positions
        """
    
    def analyze_key(self, y: np.ndarray, sr: int) -> KeyAnalysis:
        """
        Detect musical key using Krumhansl-Kessler algorithm.
        
        Args:
            y: Audio signal (mono)
            sr: Sample rate
            
        Returns:
            KeyAnalysis with key, scale, and confidence
        """
    
    def get_camelot_wheel(self, key: str, scale: str) -> str:
        """
        Convert key to Camelot wheel notation.
        
        Args:
            key: Musical key (C, C#, D, etc.)
            scale: Scale type (Major, Minor)
            
        Returns:
            Camelot notation (e.g., "8A", "11B")
        """
    
    def detect_sections(self, y: np.ndarray, sr: int) -> List[Dict]:
        """
        Detect song sections (verse, chorus, etc.).
        
        Args:
            y: Audio signal
            sr: Sample rate
            
        Returns:
            List of section dictionaries with start/end times
        """
```

### Data Classes

```python
@dataclass
class TempoAnalysis:
    """Container for tempo analysis results."""
    bpm: float                           # Beats per minute
    bpm_confidence: float                # Confidence (0-1)
    beat_positions: np.ndarray           # Beat times in seconds
    downbeat_positions: np.ndarray       # Downbeat times
    time_signature: Tuple[int, int]      # e.g., (4, 4)
    tempo_stability: float               # How stable tempo is (0-1)


@dataclass
class KeyAnalysis:
    """Container for key/scale analysis results."""
    key: str                             # Key name (C, C#, D, etc.)
    scale: str                           # Scale (Major, Minor)
    confidence: float                    # Confidence (0-1)
    key_profile: np.ndarray             # 12-bin chroma profile
    alternative_keys: List[Tuple]        # [(key, scale, confidence), ...]
    chroma_features: np.ndarray         # Raw chroma features


@dataclass
class MusicAnalysis:
    """Complete music analysis results."""
    tempo: TempoAnalysis
    key: KeyAnalysis
    duration: float                      # Song duration in seconds
    sample_rate: int
    energy_profile: np.ndarray          # RMS energy over time
    sections: List[Dict]                # Detected sections
```

---

## Advanced Features

### Processing Time Estimation

```python
from harmonix_splitter.analysis.music_analyzer import estimate_processing_time

# Estimate how long separation will take
duration_seconds = 180  # 3-minute song
quality = "balanced"

estimated_time = estimate_processing_time(duration_seconds, quality)
print(f"Estimated processing time: {estimated_time:.1f} seconds")
```

### Section Detection

```python
analyzer = MusicAnalyzer()
analysis = analyzer.analyze("song.mp3")

for section in analysis.sections:
    print(f"{section['type']}: {section['start']:.1f}s - {section['end']:.1f}s")
```

**Output:**
```
intro: 0.0s - 15.2s
verse: 15.2s - 45.8s
chorus: 45.8s - 75.3s
verse: 75.3s - 105.1s
chorus: 105.1s - 134.8s
bridge: 134.8s - 150.2s
chorus: 150.2s - 195.0s
outro: 195.0s - 210.5s
```

### Beat Grid Export

```python
# Export beat positions for DAW import
tempo = analyzer.analyze_tempo(y, sr)

# Export as markers
with open("beats.txt", "w") as f:
    for i, beat_time in enumerate(tempo.beat_positions):
        f.write(f"{beat_time:.3f}\t{i+1}\n")
```

---

## Best Practices

### 1. Use Full Songs for Accuracy

```python
# Analyze entire song for best results
analysis = analyzer.analyze("full_song.mp3")
```

### 2. Handle Tempo Changes

```python
# For songs with tempo changes, check stability
if analysis.tempo.tempo_stability < 0.5:
    print("Warning: Song may have tempo changes")
```

### 3. Consider Alternative Keys

```python
# If main key confidence is low, check alternatives
if analysis.key.confidence < 0.6:
    print("Main key uncertain, consider alternatives:")
    for alt in analysis.key.alternative_keys[:3]:
        print(f"  {alt[0]} {alt[1]}: {alt[2]:.1%}")
```

### 4. Validate with Camelot

```python
# Use Camelot for DJ mixing
camelot = analyzer.get_camelot_wheel(analysis.key.key, analysis.key.scale)
print(f"For mixing, look for: {camelot} or adjacent keys")
```

---

## Troubleshooting

### Wrong BPM Detected

**Double/Half Time Issue:**
```python
# BPM might be double or half
if detected_bpm > 160:
    actual_bpm = detected_bpm / 2
elif detected_bpm < 70:
    actual_bpm = detected_bpm * 2
```

### Wrong Key Detected

**Check relative key:**
- Am is relative to C Major
- If one is wrong, the other might be correct

**Modal confusion:**
- Dorian mode can confuse major/minor detection
- Consider the overall feel of the song

### Low Confidence Scores

1. Check audio quality
2. Ensure song has clear musical content
3. Try longer analysis duration
4. Consider genre-specific challenges

---

## Related Documentation

- [Instrument Detection](./INSTRUMENT_DETECTION.md) - Instrument analysis
- [Audio Processing](./AUDIO_PROCESSING.md) - Pitch shifting, time stretching
- [Stem Separation](./STEM_SEPARATION.md) - Audio separation

---

*Music analysis documentation last updated: January 2026*
