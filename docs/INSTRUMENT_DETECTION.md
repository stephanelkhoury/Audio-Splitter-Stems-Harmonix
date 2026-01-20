# 🔬 Instrument Detection Guide

**Understanding Harmonix's AI-powered instrument detection system**

---

## Table of Contents

- [Overview](#overview)
- [How Detection Works](#how-detection-works)
- [Supported Instruments](#supported-instruments)
- [Detection Methods](#detection-methods)
- [Confidence Scores](#confidence-scores)
- [Using Detection](#using-detection)
- [Configuration](#configuration)
- [API Reference](#api-reference)

---

## Overview

Harmonix includes an intelligent **Instrument Detection** system that analyzes audio to identify which instruments are present in a mix. This enables:

- **Smart Routing** - Automatically choose the best separation mode
- **Targeted Extraction** - Focus processing on detected instruments
- **Analysis Reports** - Get confidence scores for each instrument
- **Optimization** - Skip processing for instruments not present

---

## How Detection Works

### Detection Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                     Audio Input                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Feature Extraction                                          │
│  • Mel Spectrogram (128 mel bands)                          │
│  • MFCCs (20 coefficients)                                   │
│  • Spectral Centroid, Bandwidth, Rolloff                     │
│  • Chroma Features                                           │
│  • Zero Crossing Rate                                        │
│  • Harmonic-Percussive Separation                            │
│  • Onset Detection                                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Classification                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  ML Model (if available)                             │    │
│  │  - CNN on mel spectrogram                           │    │
│  │  - Multi-label classification                       │    │
│  └─────────────────────────────────────────────────────┘    │
│                          OR                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Heuristic Analysis (fallback)                      │    │
│  │  - Feature-based rules                              │    │
│  │  - Spectral pattern matching                        │    │
│  └─────────────────────────────────────────────────────┘    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Output: Instrument Scores                                   │
│  • Instrument name → confidence (0.0 - 1.0)                 │
│  • List of detected instruments (above threshold)            │
│  • Routing recommendations                                   │
└─────────────────────────────────────────────────────────────┘
```

### Analysis Duration

By default, detection analyzes the first **30 seconds** of audio. This provides:
- Fast analysis time
- Representative sample of the content
- Sufficient for most songs

---

## Supported Instruments

### Primary Instruments (High Accuracy)

| Instrument | Description | Detection Accuracy |
|------------|-------------|-------------------|
| **vocals** | Human singing voice | Very High (95%+) |
| **drums** | Drums and percussion | Very High (95%+) |
| **bass** | Bass guitar, synth bass | High (90%+) |
| **guitar** | Electric/acoustic guitar | High (85%+) |
| **piano** | Piano, keyboards | High (85%+) |

### Secondary Instruments (Good Accuracy)

| Instrument | Description | Detection Accuracy |
|------------|-------------|-------------------|
| **strings** | Orchestral strings | Good (80%+) |
| **synth** | Synthesizers, pads | Good (75%+) |
| **brass** | Trumpets, saxophones | Moderate (70%+) |
| **woodwinds** | Flutes, clarinets | Moderate (70%+) |
| **fx** | Sound effects, ambience | Variable |

---

## Detection Methods

### Method 1: ML Model (Primary)

When a trained model is available, detection uses a Convolutional Neural Network:

```python
# Model architecture
Input: Mel spectrogram (128 x N frames)
    │
    ▼
Conv2D layers (feature extraction)
    │
    ▼
Global pooling
    │
    ▼
Dense layers (classification)
    │
    ▼
Sigmoid activation (multi-label)
    │
    ▼
Output: 10 instrument probabilities
```

### Method 2: Heuristic Fallback

When no model is available, detection uses spectral heuristics:

#### Vocals Detection
```python
# Vocals typically have:
# - High harmonic content (>0.6 harmonic ratio)
# - Spectral centroid between 1000-4000 Hz
if harmonic_ratio > 0.6 and 1000 < spectral_centroid < 4000:
    vocals_score = harmonic_ratio * 0.8
```

#### Drums Detection
```python
# Drums typically have:
# - High percussive content
# - High onset density (>5 onsets/second)
drums_score = percussive_ratio * 1.5
if onset_density > 5:
    drums_score *= 1.2
```

#### Bass Detection
```python
# Bass typically has:
# - High energy in low frequencies (<200 Hz)
bass_energy = mean(spectrum[low_freq_bins])
bass_score = bass_energy * 2.0
```

#### Guitar Detection
```python
# Guitar typically has:
# - Moderate spectral centroid (500-2000 Hz)
# - Good harmonic content
if harmonic_ratio > 0.5 and 500 < centroid < 2000:
    guitar_score = 0.6
```

#### Piano Detection
```python
# Piano typically has:
# - Very high harmonic content
# - High chroma variation (multiple notes)
if harmonic_ratio > 0.7 and chroma_std > 0.3:
    piano_score = 0.5
```

---

## Confidence Scores

### Score Interpretation

| Score Range | Interpretation | Action |
|-------------|----------------|--------|
| **0.8 - 1.0** | Strong presence | Definitely extract |
| **0.6 - 0.8** | Likely present | Extract |
| **0.4 - 0.6** | Possibly present | Consider extracting |
| **0.2 - 0.4** | Weak signal | May be background |
| **0.0 - 0.2** | Not detected | Skip extraction |

### Default Thresholds

```yaml
# config/config.yaml
instrument_detection:
  thresholds:
    vocals: 0.5
    drums: 0.5
    bass: 0.5
    guitar: 0.5
    piano: 0.5
    strings: 0.6    # Higher threshold (harder to detect)
    synth: 0.7      # Higher threshold
    brass: 0.65
    woodwinds: 0.65
    fx: 0.7
```

---

## Using Detection

### Standalone Analysis

```python
from harmonix_splitter.analysis.detector import InstrumentDetector

# Initialize detector
detector = InstrumentDetector()

# Analyze audio
detected, scores = detector.detect_instruments("song.mp3", mode="per_instrument")

print("Detected instruments:", detected)
print("\nConfidence scores:")
for instrument, score in scores.items():
    print(f"  {instrument}: {score:.1%}")
```

**Output:**
```
Detected instruments: ['vocals', 'drums', 'bass', 'guitar', 'piano']

Confidence scores:
  vocals: 92.3%
  drums: 88.7%
  bass: 75.2%
  guitar: 63.1%
  piano: 58.4%
  strings: 12.3%
  synth: 8.5%
  brass: 0.0%
  woodwinds: 0.0%
  fx: 0.0%
```

### With Orchestrator

```python
from harmonix_splitter import create_orchestrator

orchestrator = create_orchestrator(auto_route=True)

# Analysis only
analysis = orchestrator.analyze_only("song.mp3")

print("Analysis Results:")
print(f"  Detected: {analysis['detected_instruments']}")
print(f"  Confidence: {analysis['confidence_scores']}")
print(f"  Recommendations: {analysis['recommendations']}")
```

### CLI Analysis

```bash
# Analyze without separation
python -m harmonix_splitter.cli song.mp3 --analyze-only

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

---

## Configuration

### Custom Thresholds

```python
from harmonix_splitter.analysis.detector import InstrumentDetector

# Custom thresholds
custom_thresholds = {
    "vocals": 0.4,   # More sensitive
    "drums": 0.4,
    "bass": 0.4,
    "guitar": 0.6,   # Less sensitive
    "piano": 0.6,
    "strings": 0.7,
    "synth": 0.8,
    "brass": 0.7,
    "woodwinds": 0.7,
    "fx": 0.8
}

detector = InstrumentDetector(thresholds=custom_thresholds)
```

### Analysis Duration

```python
detector = InstrumentDetector(
    analysis_duration=60  # Analyze first 60 seconds
)
```

### Sample Rate

```python
detector = InstrumentDetector(
    sample_rate=22050  # Lower sample rate for faster analysis
)
```

---

## API Reference

### InstrumentDetector Class

```python
class InstrumentDetector:
    """
    Analyzes audio to detect instruments and route processing.
    """
    
    SUPPORTED_INSTRUMENTS = [
        "vocals", "drums", "bass", "guitar", "piano",
        "strings", "synth", "brass", "woodwinds", "fx"
    ]
    
    def __init__(
        self,
        model_path: Optional[Path] = None,
        thresholds: Optional[Dict[str, float]] = None,
        sample_rate: int = 44100,
        analysis_duration: int = 30
    ):
        """
        Initialize the instrument detector.
        
        Args:
            model_path: Path to trained classifier model
            thresholds: Confidence thresholds per instrument
            sample_rate: Target sample rate for analysis
            analysis_duration: Seconds of audio to analyze
        """
    
    def analyze(self, audio_path: Path) -> Dict[str, float]:
        """
        Analyze audio file and return instrument confidence scores.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary mapping instrument names to confidence (0-1)
        """
    
    def detect_instruments(
        self,
        audio_path: Path,
        mode: str = "grouped"
    ) -> Tuple[List[str], Dict[str, float]]:
        """
        Detect which instruments are present above threshold.
        
        Args:
            audio_path: Path to audio file
            mode: 'grouped' for 4-stem or 'per_instrument' for individual
            
        Returns:
            Tuple of (detected_instruments, confidence_scores)
        """
    
    def get_routing_plan(
        self,
        detected_instruments: List[str],
        mode: str = "grouped"
    ) -> Dict[str, Any]:
        """
        Create a processing routing plan based on detected instruments.
        
        Args:
            detected_instruments: List of detected instrument names
            mode: Processing mode
            
        Returns:
            Routing plan with stages and targets
        """
```

### Routing Plans

The detector generates routing plans for the orchestrator:

```python
# Grouped mode routing plan
{
    "mode": "grouped",
    "stages": [
        {
            "name": "primary_separation",
            "model": "htdemucs",
            "outputs": ["vocals", "drums", "bass", "other"]
        }
    ],
    "target_stems": ["vocals", "drums", "bass", "other"]
}

# Per-instrument mode routing plan
{
    "mode": "per_instrument",
    "stages": [
        {
            "name": "primary_separation",
            "model": "htdemucs",
            "outputs": ["vocals", "drums", "bass", "other"]
        },
        {
            "name": "instrument_refinement",
            "input": "other",
            "targets": ["guitar", "piano"]  # Detected instruments
        }
    ],
    "target_stems": ["vocals", "drums", "bass", "guitar", "piano"]
}
```

---

## Best Practices

### 1. Use Analysis Before Processing

```python
# Analyze first
analysis = orchestrator.analyze_only("song.mp3")

# Decide based on results
if len(analysis['detected_instruments']) <= 4:
    mode = "grouped"  # Simple mix
else:
    mode = "per_instrument"  # Complex mix
```

### 2. Adjust Thresholds for Genre

```python
# Electronic music - expect synths
electronic_thresholds = {
    "synth": 0.4,  # Lower threshold
    "drums": 0.4,
    "bass": 0.4,
    "vocals": 0.5
}

# Classical music - expect strings
classical_thresholds = {
    "strings": 0.4,  # Lower threshold
    "piano": 0.4,
    "woodwinds": 0.5,
    "vocals": 0.6  # Higher threshold
}
```

### 3. Combine with User Selection

```python
# Get AI detection
detected, scores = detector.detect_instruments(audio_path)

# Let user confirm/modify
user_selection = get_user_input(detected, scores)

# Process with user's selection
result = orchestrator.process(
    audio_path,
    target_instruments=user_selection
)
```

---

## Troubleshooting

### Detection Not Accurate

1. **Check audio quality** - Low quality audio gives poor results
2. **Try longer analysis** - Increase `analysis_duration`
3. **Adjust thresholds** - Lower thresholds for missed instruments

### Missing Instruments

```python
# Lower thresholds to detect more
detector = InstrumentDetector(
    thresholds={inst: 0.3 for inst in InstrumentDetector.SUPPORTED_INSTRUMENTS}
)
```

### False Positives

```python
# Raise thresholds to reduce false positives
detector = InstrumentDetector(
    thresholds={inst: 0.7 for inst in InstrumentDetector.SUPPORTED_INSTRUMENTS}
)
```

---

## Related Documentation

- [Stem Separation](./STEM_SEPARATION.md) - How separation works
- [Music Analysis](./MUSIC_ANALYSIS.md) - BPM and key detection
- [Configuration](./CONFIGURATION.md) - Full configuration options

---

*Instrument detection documentation last updated: January 2026*
