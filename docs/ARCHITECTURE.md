# 🏗️ System Architecture

**Deep dive into Harmonix's modular architecture**

---

## Table of Contents

- [Overview](#overview)
- [High-Level Architecture](#high-level-architecture)
- [Module Structure](#module-structure)
- [Core Components](#core-components)
- [Data Flow](#data-flow)
- [Processing Pipeline](#processing-pipeline)
- [Storage Architecture](#storage-architecture)
- [Dependency Graph](#dependency-graph)

---

## Overview

Harmonix follows a **modular, layered architecture** with clear separation of concerns:

```
┌───────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                       │
│           Dashboard (Flask)    API (FastAPI)    CLI           │
├───────────────────────────────────────────────────────────────┤
│                      ORCHESTRATION LAYER                      │
│                       HarmonixOrchestrator                    │
├───────────────────────────────────────────────────────────────┤
│                         CORE LAYER                            │
│    Separator    Preprocessor    Detector    Analyzer          │
├───────────────────────────────────────────────────────────────┤
│                         AUDIO LAYER                           │
│         LyricsExtractor    AudioProcessor    Encoder          │
├───────────────────────────────────────────────────────────────┤
│                       SUPPORT LAYER                           │
│       Config    Auth    Library    Utils    Storage           │
├───────────────────────────────────────────────────────────────┤
│                      EXTERNAL LAYER                           │
│       Demucs    Whisper    PyTorch    FFmpeg    yt-dlp        │
└───────────────────────────────────────────────────────────────┘
```

---

## High-Level Architecture

### System Diagram

```
                    ┌──────────────┐
                    │    Users     │
                    └──────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐      ┌─────▼────┐      ┌────▼────┐
    │   Web   │      │   REST   │      │   CLI   │
    │Dashboard│      │   API    │      │ Command │
    │ (Flask) │      │(FastAPI) │      │  Line   │
    │  :5000  │      │  :8000   │      │         │
    └────┬────┘      └────┬─────┘      └────┬────┘
         │                │                  │
         └────────────────┼──────────────────┘
                          │
                  ┌───────▼───────┐
                  │ Orchestrator  │
                  │   (Router)    │
                  └───────┬───────┘
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
┌───▼───┐           ┌─────▼─────┐         ┌────▼────┐
│Preproc│──────────▶│ Separator │──────────│Detector │
│       │           │ (Demucs)  │          │         │
└───────┘           └─────┬─────┘          └─────────┘
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
┌───▼────┐          ┌─────▼─────┐         ┌────▼────┐
│Lyrics  │          │  Music    │         │ Audio   │
│Extract │          │ Analyzer  │         │Processor│
│(Whisper)│         │           │         │         │
└────────┘          └───────────┘         └─────────┘
```

---

## Module Structure

### Package Layout

```
src/harmonix_splitter/
├── __init__.py              # Package exports
├── __main__.py              # Python -m entry point
│
├── core/                    # Core processing
│   ├── __init__.py
│   ├── separator.py         # HarmonixSeparator (Demucs wrapper)
│   ├── orchestrator.py      # HarmonixOrchestrator (pipeline)
│   └── preprocessor.py      # AudioPreprocessor
│
├── analysis/                # Audio analysis
│   ├── __init__.py
│   ├── detector.py          # InstrumentDetector
│   └── music_analyzer.py    # MusicAnalyzer (BPM, key)
│
├── audio/                   # Audio utilities
│   ├── __init__.py
│   ├── processor.py         # AudioProcessor (pitch shift)
│   └── lyrics.py            # LyricsExtractor (Whisper)
│
├── api/                     # REST API
│   ├── __init__.py
│   └── main.py              # FastAPI application
│
├── config/                  # Configuration
│   ├── __init__.py
│   └── settings.py          # Pydantic settings
│
├── utils/                   # Utilities
│   └── __init__.py
│
├── cli.py                   # CLI application
├── dashboard.py             # Flask web app
├── auth.py                  # User authentication
└── library.py               # Shared content library
```

### Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `core/separator.py` | Stem separation using Demucs |
| `core/orchestrator.py` | Pipeline coordination |
| `core/preprocessor.py` | Audio validation & prep |
| `analysis/detector.py` | Instrument detection |
| `analysis/music_analyzer.py` | BPM/key analysis |
| `audio/lyrics.py` | Lyrics extraction |
| `audio/processor.py` | Pitch/tempo modification |
| `api/main.py` | REST API endpoints |
| `dashboard.py` | Web interface |
| `auth.py` | User management |
| `library.py` | Content caching |

---

## Core Components

### HarmonixSeparator

**Purpose:** Wrap Demucs for stem separation

```python
class HarmonixSeparator:
    """
    Main class for audio stem separation using Demucs.
    
    Attributes:
        device: torch.device (cuda/mps/cpu)
        model: Demucs model instance
        quality_mode: Current quality setting
        
    Methods:
        separate(audio_path) -> Dict[str, Path]
        separate_stems(audio, sr) -> Dict[str, np.ndarray]
    """
```

**Key Features:**
- GPU acceleration (CUDA/MPS)
- Multiple quality modes
- Model caching
- Memory optimization

### HarmonixOrchestrator

**Purpose:** Route and coordinate processing pipeline

```python
class HarmonixOrchestrator:
    """
    Orchestrates the complete audio processing pipeline.
    
    Components:
        - preprocessor: AudioPreprocessor
        - separator: HarmonixSeparator
        - detector: InstrumentDetector
        - analyzer: MusicAnalyzer
        - lyrics_extractor: LyricsExtractor
        
    Methods:
        process(input_path) -> ProcessingResult
        analyze_only(input_path) -> AnalysisResult
        batch_process(paths) -> List[ProcessingResult]
    """
```

**Pipeline Stages:**
1. Preprocessing (validation, normalization)
2. Analysis (BPM, key, instruments)
3. Separation (Demucs inference)
4. Post-processing (naming, export)

### InstrumentDetector

**Purpose:** Detect instruments in audio

```python
class InstrumentDetector:
    """
    Detect instruments present in audio.
    
    Methods:
        detect(audio_path) -> Dict[str, float]
        detect_from_array(audio, sr) -> Dict[str, float]
    
    Returns:
        Dictionary of instrument -> confidence (0.0-1.0)
    """
```

**Detection Methods:**
- ML-based classification (primary)
- Spectral heuristics (fallback)
- Frequency band analysis

### MusicAnalyzer

**Purpose:** Analyze musical properties

```python
class MusicAnalyzer:
    """
    Analyze tempo, key, and musical characteristics.
    
    Methods:
        analyze_tempo(audio, sr) -> TempoAnalysis
        analyze_key(audio, sr) -> KeyAnalysis
        full_analysis(audio_path) -> MusicAnalysis
    """
```

**Analysis Features:**
- Beat tracking (librosa)
- Key detection (Krumhansl-Kessler)
- Camelot wheel mapping

---

## Data Flow

### Request Flow

```
┌─────────┐     ┌─────────┐     ┌──────────────┐     ┌─────────┐
│  Input  │────▶│  Route  │────▶│   Process    │────▶│  Output │
│         │     │         │     │              │     │         │
│ - File  │     │ - API   │     │ - Preprocess │     │ - Stems │
│ - URL   │     │ - CLI   │     │ - Separate   │     │ - JSON  │
│ - Stream│     │ - Dash  │     │ - Analyze    │     │ - Lyrics│
└─────────┘     └─────────┘     └──────────────┘     └─────────┘
```

### Data Transformation

```
Input Audio (mp3/wav/flac)
         │
         ▼
    ┌────────────────┐
    │ Load & Decode  │  librosa / soundfile
    │ (44.1kHz, mono)│
    └───────┬────────┘
            │
            ▼
    ┌────────────────┐
    │  Normalize     │  Peak normalization
    │  (-1.0 to 1.0) │
    └───────┬────────┘
            │
            ▼
    ┌────────────────┐
    │  Resample      │  Match model requirements
    │  (44100 Hz)    │
    └───────┬────────┘
            │
            ▼
    ┌────────────────┐
    │  Demucs Model  │  Neural network inference
    │  (htdemucs_6s) │
    └───────┬────────┘
            │
            ▼
    ┌────────────────┐
    │  Post-process  │  Denormalize, format
    │  (per stem)    │
    └───────┬────────┘
            │
            ▼
Output Stems (wav/mp3)
```

---

## Processing Pipeline

### Complete Pipeline

```python
def process_full_pipeline(input_path: Path) -> ProcessingResult:
    """
    Complete processing pipeline.
    """
    # 1. PREPROCESSING
    preprocessor = AudioPreprocessor()
    audio, sr = preprocessor.load_and_validate(input_path)
    audio = preprocessor.normalize(audio)
    
    # 2. ANALYSIS (parallel)
    analyzer = MusicAnalyzer()
    detector = InstrumentDetector()
    
    with ThreadPoolExecutor() as executor:
        tempo_future = executor.submit(analyzer.analyze_tempo, audio, sr)
        key_future = executor.submit(analyzer.analyze_key, audio, sr)
        inst_future = executor.submit(detector.detect, audio, sr)
        
        tempo = tempo_future.result()
        key = key_future.result()
        instruments = inst_future.result()
    
    # 3. SEPARATION
    separator = HarmonixSeparator(quality_mode=QualityMode.STUDIO)
    stems = separator.separate(audio, sr)
    
    # 4. POST-PROCESSING
    results = {}
    for stem_name, stem_audio in stems.items():
        output_path = save_stem(stem_audio, stem_name)
        results[stem_name] = output_path
    
    # 5. OPTIONAL: LYRICS
    if "vocals" in results:
        lyrics_extractor = LyricsExtractor()
        lyrics = lyrics_extractor.extract(results["vocals"])
    
    return ProcessingResult(
        stems=results,
        analysis=Analysis(tempo=tempo, key=key, instruments=instruments),
        lyrics=lyrics
    )
```

### Pipeline Modes

**Full Pipeline:**
```
Input → Preprocess → Analyze → Separate → Post-process → Output
```

**Analysis Only:**
```
Input → Preprocess → Analyze → Output (JSON)
```

**Batch Processing:**
```
[Input1, Input2, ...] → Queue → Parallel Processing → [Output1, Output2, ...]
```

---

## Storage Architecture

### Directory Structure

```
data/
├── uploads/              # Temporary uploads
│   └── {session_id}/
│       └── {filename}
│
├── temp/                 # Processing temp files
│   └── {job_id}/
│       ├── audio.wav
│       └── stems/
│
├── outputs/              # Processed results
│   └── {user_id}/
│       └── {job_id}/
│           ├── metadata.json
│           ├── vocals.mp3
│           ├── drums.mp3
│           └── ...
│
├── library/              # Shared content cache
│   └── {video_id}/
│       ├── metadata.json
│       └── stems/
│
├── users.json            # User database
├── activities.json       # Activity log
│
└── avatars/              # User profile images
    └── {user_id}.jpg
```

### Data Models

```python
# Job metadata
job_metadata = {
    "id": "job_abc123",
    "user_id": "user_xyz",
    "input_file": "song.mp3",
    "status": "completed",
    "created_at": "2025-12-30T10:00:00Z",
    "completed_at": "2025-12-30T10:02:30Z",
    "settings": {
        "quality": "studio",
        "mode": "grouped"
    },
    "results": {
        "stems": ["vocals", "drums", "bass", "other"],
        "analysis": {
            "bpm": 128,
            "key": "A Minor"
        }
    }
}
```

---

## Dependency Graph

### Internal Dependencies

```
dashboard.py
    ├── orchestrator.py
    │   ├── separator.py
    │   │   └── (torch, demucs)
    │   ├── preprocessor.py
    │   │   └── (librosa, soundfile)
    │   ├── detector.py
    │   │   └── (librosa, numpy)
    │   └── music_analyzer.py
    │       └── (librosa, numpy)
    ├── lyrics.py
    │   └── (whisper, torch)
    ├── processor.py
    │   └── (librosa, soundfile)
    ├── auth.py
    │   └── (bcrypt)
    └── library.py
        └── (yt-dlp)
```

### External Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                    Harmonix Application                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   PyTorch   │  │   Demucs    │  │      Whisper        │ │
│  │  (ML Core)  │  │ (Separator) │  │ (Speech-to-Text)    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   librosa   │  │  soundfile  │  │      FFmpeg         │ │
│  │  (Analysis) │  │  (Audio I/O)│  │   (Conversion)      │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Flask     │  │   FastAPI   │  │      yt-dlp         │ │
│  │ (Dashboard) │  │  (REST API) │  │   (YouTube DL)      │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Threading Model

### Concurrent Processing

```python
# Dashboard uses thread pool for jobs
from concurrent.futures import ThreadPoolExecutor

class JobProcessor:
    def __init__(self, max_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.jobs = {}
    
    def submit_job(self, job_id, input_path, settings):
        future = self.executor.submit(
            self.process_job,
            job_id, input_path, settings
        )
        self.jobs[job_id] = future
        return job_id
    
    def get_status(self, job_id):
        if job_id not in self.jobs:
            return "not_found"
        future = self.jobs[job_id]
        if future.running():
            return "processing"
        elif future.done():
            return "completed"
        return "queued"
```

### GPU Concurrency

```python
# GPU operations are serialized
import threading

class GPULock:
    _lock = threading.Lock()
    
    @classmethod
    def acquire(cls):
        cls._lock.acquire()
    
    @classmethod
    def release(cls):
        cls._lock.release()
    
    @classmethod
    def context(cls):
        return cls._lock
```

---

## Error Handling

### Error Hierarchy

```python
class HarmonixError(Exception):
    """Base exception for Harmonix."""
    pass

class AudioLoadError(HarmonixError):
    """Failed to load audio file."""
    pass

class SeparationError(HarmonixError):
    """Stem separation failed."""
    pass

class AnalysisError(HarmonixError):
    """Audio analysis failed."""
    pass

class ConfigError(HarmonixError):
    """Configuration error."""
    pass
```

### Error Recovery

```python
def process_with_recovery(input_path: Path) -> ProcessingResult:
    """Process with automatic error recovery."""
    try:
        return process_full(input_path)
    except torch.cuda.OutOfMemoryError:
        # Fall back to CPU
        logger.warning("GPU OOM, falling back to CPU")
        return process_full(input_path, device="cpu")
    except AudioLoadError:
        # Try conversion
        logger.warning("Audio load failed, attempting conversion")
        converted = convert_audio(input_path)
        return process_full(converted)
```

---

## Related Documentation

- [Installation](./INSTALLATION.md) - Setup guide
- [Configuration](./CONFIGURATION.md) - Settings
- [API Reference](./API_REFERENCE.md) - REST API
- [Developer Guide](./DEVELOPER_GUIDE.md) - Contributing

---

*Architecture documentation last updated: January 2026*
