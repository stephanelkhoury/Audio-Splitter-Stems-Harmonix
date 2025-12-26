# Harmonix DAW Workspace - Technical Specification

**Version:** 1.0  
**Date:** December 18, 2025  
**Author:** Stephan El Khoury

---

## Executive Summary

This document outlines the complete technical architecture for transforming Harmonix into a **professional DAW-like audio workstation** with advanced stem mixing, effects processing, reverb/de-reverb, mastering, normalization, and comprehensive waveform/spectral visualization.

**Core Philosophy:** Build incrementally in phases, following industry-standard DAW patterns from **Adobe Audition**, **Logic Pro**, and **Pro Tools**.

---

## Current Stack

- **Frontend:** HTML5, CSS3, JavaScript (vanilla), WaveSurfer.js 7.0
- **Backend:** Python 3.10+, Flask 3.0+ (Dashboard), FastAPI (API)
- **Audio Engine:** Demucs v4 (separation), librosa, soundfile
- **Storage:** Local file system (data/outputs/)
- **Processing:** Background threading for async jobs

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Timeline    │  │   Mixer      │  │  FX Rack     │      │
│  │  Waveforms   │  │  Strips      │  │  Controls    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Transport   │  │  Meters      │  │  Analysis    │      │
│  │  Controls    │  │  LUFS/Peak   │  │  Spectrum    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (Flask/FastAPI)                │
│  /project/create    /mixer/render    /fx/apply             │
│  /stems/load        /master/process  /export/mix           │
└─────────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Processing Engine                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Audio DSP   │  │  FX Chain    │  │  Renderer    │      │
│  │  Core        │  │  Processor   │  │  Engine      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Storage Layer                              │
│  Projects: .hxproj (JSON metadata)                          │
│  Audio: .wav stems + processed files                        │
│  Cache: Waveform peaks, analysis data                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase A: DAW MVP (Weeks 1-3)

### 1. Multitrack Timeline + Waveform Viewer

**Goal:** Build the foundation for all subsequent features.

#### 1.1 UI Components

**Timeline Ruler:**
```javascript
// Component: TimelineRuler
- Displays time markers (00:00, 00:05, 00:10...)
- Zoom levels: 1x, 2x, 5x, 10x, 20x
- Playhead cursor (red vertical line)
- Selection range (highlighted region)
```

**Track Lanes:**
```javascript
// Component: TrackLane
- Vertical stack of tracks
- Each track contains:
  - Header (name, color, controls)
  - Waveform canvas
  - Clip regions
- Scrollable vertically
```

**Waveform Rendering:**
```javascript
// Tech: WaveSurfer.js + Custom Canvas
- Use WaveSurfer for each track
- Precompute peaks (decimated data)
- Render: Canvas 2D or WebGL for performance
- Colors: Track-specific waveform colors
```

#### 1.2 Backend Support

**Endpoints:**
```python
# POST /project/create
# Create new DAW project
{
  "name": "My Mix",
  "stems": ["job_id_1", "job_id_2"],
  "sample_rate": 44100
}

# GET /project/{project_id}/waveforms
# Return peak data for all tracks
{
  "tracks": [
    {
      "track_id": "track_1",
      "stem_name": "vocals",
      "peaks": [...],  # Decimated amplitude values
      "duration": 245.3
    }
  ]
}
```

**Peak Generation:**
```python
# Use librosa or custom decimation
def generate_peaks(audio_file, samples_per_pixel=512):
    """Generate waveform peaks for efficient rendering"""
    y, sr = librosa.load(audio_file, sr=None)
    hop = samples_per_pixel
    peaks = []
    for i in range(0, len(y), hop):
        chunk = y[i:i+hop]
        peaks.append({
            'min': float(np.min(chunk)),
            'max': float(np.max(chunk))
        })
    return peaks
```

#### 1.3 Zoom & Navigation

**Controls:**
- Horizontal zoom: Timeline scale (samples per pixel)
- Vertical zoom: Amplitude scale per track
- Pan: Click and drag timeline
- Scroll: Mouse wheel for zoom, shift+wheel for pan

---

### 2. Channel Strips (Mixer)

**Goal:** Implement per-track mixing controls like Logic/Audition.

#### 2.1 Channel Strip UI

**Per-Track Controls:**
```html
<div class="channel-strip">
  <!-- Input Section -->
  <div class="strip-input">
    <span class="track-name">Vocals</span>
  </div>
  
  <!-- Inserts Section (FX Rack) -->
  <div class="strip-inserts">
    <div class="insert-slot">Insert 1: EQ</div>
    <div class="insert-slot">Insert 2: Comp</div>
    <div class="insert-slot empty">Insert 3</div>
  </div>
  
  <!-- Sends Section -->
  <div class="strip-sends">
    <div class="send">
      <label>Reverb</label>
      <input type="range" class="send-level" min="-inf" max="0">
    </div>
  </div>
  
  <!-- Fader Section -->
  <div class="strip-fader">
    <input type="range" orient="vertical" class="volume-fader" 
           min="-60" max="12" value="0">
    <span class="fader-value">0.0 dB</span>
  </div>
  
  <!-- Pan -->
  <div class="strip-pan">
    <input type="range" class="pan-knob" min="-100" max="100" value="0">
    <span>C</span>
  </div>
  
  <!-- Meters -->
  <canvas class="level-meter" width="20" height="200"></canvas>
  
  <!-- Buttons -->
  <button class="mute-btn">M</button>
  <button class="solo-btn">S</button>
  <button class="record-btn">R</button>
</div>
```

#### 2.2 Backend Audio Mixing

**Real-time Mixing:**
```python
# Use Web Audio API on frontend for low-latency mixing
# Backend handles:
# 1. Offline rendering
# 2. FX processing
# 3. Bouncing/exporting

class MixEngine:
    def mix_tracks(self, tracks, master_config):
        """
        Mix multiple tracks with volume/pan
        """
        mixed = np.zeros(max_length)
        
        for track in tracks:
            audio = track.audio
            
            # Apply volume (dB to linear)
            gain = 10 ** (track.volume_db / 20.0)
            audio *= gain
            
            # Apply pan (constant power)
            if track.pan != 0:
                left, right = self.apply_pan(audio, track.pan)
                audio = (left + right) / 2  # Stereo to mono or keep stereo
            
            # Sum to mix
            mixed += audio
        
        return mixed
    
    def apply_pan(self, audio, pan):
        """Pan: -100 (left) to +100 (right)"""
        angle = (pan / 100.0) * (np.pi / 4)  # -45° to +45°
        left_gain = np.cos(angle)
        right_gain = np.sin(angle)
        return audio * left_gain, audio * right_gain
```

---

### 3. Master Bus + Meters

**Master Channel Strip:**
- Same as track strips but designated as final output
- Contains master FX chain
- Master fader
- Master meters (L/R or stereo)

**Metering:**
```javascript
// Real-time level metering using Web Audio API
class LevelMeter {
  constructor(audioContext, source) {
    this.analyser = audioContext.createAnalyser();
    this.analyser.fftSize = 2048;
    source.connect(this.analyser);
    
    this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
  }
  
  getLevel() {
    this.analyser.getByteTimeDomainData(this.dataArray);
    
    let sum = 0;
    for (let i = 0; i < this.dataArray.length; i++) {
      const normalized = (this.dataArray[i] - 128) / 128;
      sum += normalized * normalized;
    }
    
    const rms = Math.sqrt(sum / this.dataArray.length);
    const db = 20 * Math.log10(rms);
    
    return db;
  }
}
```

---

### 4. Basic Export

**Export Dialog:**
```javascript
// Export options
{
  "format": "wav",          // wav, mp3
  "sample_rate": 44100,     // 44100, 48000
  "bit_depth": 24,          // 16, 24, 32
  "dither": false,
  "normalize": false,
  "time_range": "all"       // all, selection
}
```

**Backend Renderer:**
```python
# POST /export/mix
def export_mix(project_id, export_config):
    """Offline render and export"""
    project = load_project(project_id)
    
    # Mix all tracks
    mixed_audio = mix_engine.mix_tracks(
        project.tracks,
        project.master_config
    )
    
    # Apply master FX chain
    processed = fx_chain.process(mixed_audio, project.master_fx)
    
    # Normalize if requested
    if export_config['normalize']:
        processed = normalize_audio(processed, target_db=-1.0)
    
    # Export
    output_file = f"{project.name}_master.wav"
    sf.write(output_file, processed, export_config['sample_rate'])
    
    return {"file": output_file}
```

---

## Phase B: Routing & FX (Weeks 4-6)

### 5. FX Rack (Insert Chain)

**Goal:** Per-track effect processing with insert slots.

#### 5.1 FX Rack UI

**Insert Slots:**
```html
<div class="fx-rack">
  <div class="fx-slot" data-slot="1">
    <select class="fx-selector">
      <option value="">Empty</option>
      <option value="eq">EQ</option>
      <option value="compressor">Compressor</option>
      <option value="reverb">Reverb</option>
      <option value="delay">Delay</option>
    </select>
    <button class="fx-bypass">Bypass</button>
    <button class="fx-settings">Settings</button>
  </div>
  <!-- Repeat for slots 2-16 -->
</div>
```

**FX Settings Panel:**
```javascript
// Modal for effect parameters
{
  "effect_type": "eq",
  "parameters": {
    "low_freq": 80,
    "low_gain": 0,
    "mid_freq": 1000,
    "mid_gain": 0,
    "high_freq": 8000,
    "high_gain": 0
  }
}
```

#### 5.2 Backend FX Processing

**Effect Plugins:**
```python
# Base FX class
class AudioEffect:
    def __init__(self, params):
        self.params = params
        self.bypassed = False
    
    def process(self, audio, sample_rate):
        raise NotImplementedError

# Example: EQ
class ParametricEQ(AudioEffect):
    def process(self, audio, sample_rate):
        from scipy.signal import butter, sosfilt
        
        # Low shelf
        sos = butter(2, self.params['low_freq'], 
                     btype='lowshelf', fs=sample_rate)
        audio = sosfilt(sos, audio)
        
        # Mid peak/notch
        # ... implementation
        
        # High shelf
        # ... implementation
        
        return audio

# Example: Compressor
class Compressor(AudioEffect):
    def process(self, audio, sample_rate):
        threshold = self.params['threshold']  # dB
        ratio = self.params['ratio']
        attack = self.params['attack_ms'] / 1000.0
        release = self.params['release_ms'] / 1000.0
        
        # Envelope follower + gain reduction
        # ... implementation using librosa or custom
        
        return compressed_audio
```

**FX Chain Processor:**
```python
class FXChain:
    def __init__(self, effects_list):
        self.effects = effects_list  # List of AudioEffect instances
    
    def process(self, audio, sample_rate):
        """Process audio through entire FX chain"""
        output = audio.copy()
        
        for effect in self.effects:
            if not effect.bypassed:
                output = effect.process(output, sample_rate)
        
        return output
```

---

### 6. Buses + Sends Routing

**Goal:** Implement auxiliary sends to shared effect buses (e.g., reverb bus).

#### 6.1 Routing Architecture

**Bus Structure:**
```javascript
{
  "buses": [
    {
      "bus_id": "bus_reverb_1",
      "name": "Reverb Hall",
      "type": "aux",
      "fx_chain": [
        {"type": "reverb", "params": {...}}
      ],
      "volume": 0.0,
      "pan": 0,
      "output": "master"
    }
  ],
  "tracks": [
    {
      "track_id": "track_1",
      "sends": [
        {
          "bus_id": "bus_reverb_1",
          "level": -12.0,  // dB
          "pre_fader": false
        }
      ]
    }
  ]
}
```

#### 6.2 Send Processing

**Mixing with Sends:**
```python
class MixEngine:
    def mix_with_sends(self, project):
        """
        Mix tracks with send routing
        """
        # 1. Process all tracks (dry signal + inserts)
        track_outputs = {}
        for track in project.tracks:
            audio = track.audio.copy()
            
            # Apply track inserts
            audio = track.fx_chain.process(audio, project.sample_rate)
            
            # Apply volume/pan
            audio = self.apply_volume_pan(audio, track.volume, track.pan)
            
            track_outputs[track.id] = audio
        
        # 2. Process sends to buses
        bus_inputs = {bus.id: np.zeros(max_length) for bus in project.buses}
        
        for track in project.tracks:
            for send in track.sends:
                send_audio = track_outputs[track.id].copy()
                
                # Apply send level
                gain = 10 ** (send.level / 20.0)
                send_audio *= gain
                
                # Sum to bus input
                bus_inputs[send.bus_id] += send_audio
        
        # 3. Process buses
        bus_outputs = {}
        for bus in project.buses:
            bus_audio = bus_inputs[bus.id]
            
            # Apply bus FX chain
            bus_audio = bus.fx_chain.process(bus_audio, project.sample_rate)
            
            # Apply bus volume/pan
            bus_audio = self.apply_volume_pan(bus_audio, bus.volume, bus.pan)
            
            bus_outputs[bus.id] = bus_audio
        
        # 4. Mix to master
        master_input = np.zeros(max_length)
        
        # Sum all tracks
        for audio in track_outputs.values():
            master_input += audio
        
        # Sum all bus returns
        for audio in bus_outputs.values():
            master_input += audio
        
        # 5. Process master FX chain
        master_output = project.master_fx_chain.process(
            master_input, 
            project.sample_rate
        )
        
        return master_output
```

---

### 7. Reverb Bus System

**Reverb Implementation:**
```python
class ConvolutionReverb(AudioEffect):
    """High-quality convolution reverb"""
    def __init__(self, params):
        super().__init__(params)
        self.load_impulse_response(params['ir_file'])
    
    def load_impulse_response(self, ir_file):
        self.ir, self.ir_sr = librosa.load(ir_file, sr=None)
    
    def process(self, audio, sample_rate):
        from scipy.signal import fftconvolve
        
        # Resample IR if needed
        if self.ir_sr != sample_rate:
            self.ir = librosa.resample(
                self.ir, 
                orig_sr=self.ir_sr, 
                target_sr=sample_rate
            )
        
        # Convolve
        wet = fftconvolve(audio, self.ir, mode='same')
        
        # Mix dry/wet
        wet_amount = self.params['wet'] / 100.0
        output = audio * (1 - wet_amount) + wet * wet_amount
        
        return output

# Or algorithmic reverb
class AlgorithmicReverb(AudioEffect):
    """Faster algorithmic reverb (Freeverb-style)"""
    def process(self, audio, sample_rate):
        # Implement comb filters + allpass filters
        # Parameters: room size, damping, width
        # ... implementation
        return reverb_audio
```

**Reverb Bus Preset:**
```python
# Create default reverb buses
def create_default_buses():
    return [
        {
            "id": "reverb_room",
            "name": "Room Reverb",
            "fx_chain": [
                {
                    "type": "reverb",
                    "params": {
                        "type": "algorithmic",
                        "room_size": 0.5,
                        "decay_time": 1.2,
                        "pre_delay": 20,
                        "damping": 0.5,
                        "wet": 100
                    }
                }
            ]
        },
        {
            "id": "reverb_hall",
            "name": "Hall Reverb",
            "fx_chain": [
                {
                    "type": "reverb",
                    "params": {
                        "type": "algorithmic",
                        "room_size": 0.9,
                        "decay_time": 2.5,
                        "pre_delay": 40,
                        "damping": 0.3,
                        "wet": 100
                    }
                }
            ]
        }
    ]
```

---

## Phase C: Pro Audio (Weeks 7-12)

### 8. De-Reverb (Restoration)

**Goal:** Remove unwanted room reflections from vocals/dialogue.

#### 8.1 De-Reverb Algorithm

**Spectral Gating Approach:**
```python
class DeReverb(AudioEffect):
    """
    Remove reverb using spectral subtraction and gating
    """
    def __init__(self, params):
        super().__init__(params)
        self.amount = params['amount']  # 0-100
        self.smoothness = params['smoothness']  # 0-100
    
    def process(self, audio, sample_rate):
        # STFT
        D = librosa.stft(audio, n_fft=2048, hop_length=512)
        mag, phase = np.abs(D), np.angle(D)
        
        # Estimate reverb tail (statistical model)
        reverb_profile = self.estimate_reverb_profile(mag)
        
        # Spectral subtraction
        clean_mag = mag - (reverb_profile * self.amount / 100.0)
        clean_mag = np.maximum(clean_mag, 0)  # No negative
        
        # Smooth with median filter to reduce artifacts
        if self.smoothness > 0:
            from scipy.ndimage import median_filter
            kernel = int(self.smoothness / 10) + 1
            clean_mag = median_filter(clean_mag, size=(kernel, kernel))
        
        # Reconstruct
        clean_D = clean_mag * np.exp(1j * phase)
        clean_audio = librosa.istft(clean_D, hop_length=512)
        
        return clean_audio
    
    def estimate_reverb_profile(self, magnitude):
        """
        Estimate reverb spectral profile
        Using minimum statistics over time frames
        """
        # For each frequency bin, take minimum over sliding window
        window_frames = 50
        reverb_estimate = np.zeros_like(magnitude)
        
        for i in range(magnitude.shape[0]):
            for j in range(magnitude.shape[1]):
                start = max(0, j - window_frames)
                end = j + 1
                reverb_estimate[i, j] = np.min(magnitude[i, start:end])
        
        return reverb_estimate
```

**UI Controls:**
```html
<div class="dereverb-panel">
  <h3>De-Reverb</h3>
  
  <label>Amount</label>
  <input type="range" id="dereverb-amount" min="0" max="100" value="50">
  
  <label>Smoothness (Artifact Control)</label>
  <input type="range" id="dereverb-smooth" min="0" max="100" value="50">
  
  <label>Focus Band</label>
  <select id="dereverb-focus">
    <option value="all">Full Spectrum</option>
    <option value="mid">Mid (500-4000 Hz)</option>
    <option value="high">High (2000-8000 Hz)</option>
  </select>
  
  <label>Output Gain Compensation</label>
  <input type="range" id="dereverb-gain" min="-12" max="12" value="0">
  
  <button id="dereverb-preview">Preview (Real-time)</button>
  <button id="dereverb-render">Render (High Quality)</button>
</div>
```

**Processing Modes:**
```python
# Real-time preview (lower quality, faster)
def preview_dereverb(audio, params):
    """Lower resolution for real-time"""
    dereverb = DeReverb(params)
    return dereverb.process(audio, sample_rate, n_fft=1024)

# Offline render (highest quality)
def render_dereverb(audio, params):
    """High resolution for final output"""
    dereverb = DeReverb(params)
    return dereverb.process(audio, sample_rate, n_fft=4096)
```

---

### 9. Mastering Chain

**Goal:** Professional mastering with EQ, compression, limiting, and loudness control.

#### 9.1 Mastering FX Chain

**Typical Master Chain:**
```python
def create_mastering_chain(preset="streaming"):
    """
    Create mastering FX chain based on preset
    """
    if preset == "streaming":
        return [
            {
                "type": "eq",
                "name": "Tonal Balance",
                "params": {
                    "low_shelf": {"freq": 80, "gain": -1.0},
                    "mid_peak": {"freq": 2000, "gain": 0.5, "q": 1.0},
                    "high_shelf": {"freq": 10000, "gain": 1.0}
                }
            },
            {
                "type": "multiband_compressor",
                "name": "Glue",
                "params": {
                    "low": {"threshold": -20, "ratio": 2.0, "freq": 120},
                    "mid": {"threshold": -15, "ratio": 1.5, "freq": 2500},
                    "high": {"threshold": -12, "ratio": 2.0}
                }
            },
            {
                "type": "limiter",
                "name": "True Peak Limiter",
                "params": {
                    "threshold": -1.0,
                    "ceiling": -0.3,
                    "release": 50
                }
            }
        ]
    elif preset == "broadcast":
        # Different chain for broadcast standards
        return [...]
```

#### 9.2 Limiter Implementation

**True Peak Limiter:**
```python
class TruePeakLimiter(AudioEffect):
    """
    Transparent true-peak limiter for mastering
    """
    def __init__(self, params):
        super().__init__(params)
        self.threshold = params['threshold']  # dB
        self.ceiling = params['ceiling']      # dB (true peak)
        self.release = params['release']      # ms
    
    def process(self, audio, sample_rate):
        # Oversample 4x to catch inter-sample peaks
        from scipy.signal import resample_poly
        
        audio_os = resample_poly(audio, 4, 1)
        
        # Detect peaks
        threshold_linear = 10 ** (self.threshold / 20.0)
        ceiling_linear = 10 ** (self.ceiling / 20.0)
        
        # Lookahead buffer (5ms)
        lookahead_samples = int(0.005 * sample_rate * 4)
        
        # Calculate gain reduction
        gain_reduction = np.ones(len(audio_os))
        
        for i in range(len(audio_os)):
            # Look ahead
            window = audio_os[i:i+lookahead_samples]
            peak = np.max(np.abs(window))
            
            if peak > threshold_linear:
                # Calculate required gain reduction
                gr = ceiling_linear / peak
                gain_reduction[i] = min(gain_reduction[i], gr)
        
        # Smooth gain reduction (release envelope)
        release_samples = int(self.release / 1000.0 * sample_rate * 4)
        gain_reduction = self.smooth_envelope(gain_reduction, release_samples)
        
        # Apply limiting
        limited = audio_os * gain_reduction
        
        # Downsample back to original rate
        limited = resample_poly(limited, 1, 4)
        
        return limited
    
    def smooth_envelope(self, envelope, release_samples):
        """Smooth release envelope"""
        smoothed = envelope.copy()
        for i in range(1, len(envelope)):
            if envelope[i] > smoothed[i-1]:
                # Attack: instant
                smoothed[i] = envelope[i]
            else:
                # Release: gradual
                coeff = np.exp(-1.0 / release_samples)
                smoothed[i] = coeff * smoothed[i-1] + (1 - coeff) * envelope[i]
        return smoothed
```

---

### 10. Match Loudness (LUFS Normalization)

**Goal:** Match audio to broadcast/streaming standards.

#### 10.1 LUFS Measurement

**Implementation:**
```python
import pyloudnorm as pyln

class LoudnessMatcher:
    def __init__(self):
        self.meter = pyln.Meter(44100)  # Sample rate
    
    def measure_loudness(self, audio, sample_rate):
        """
        Measure integrated LUFS
        """
        loudness = self.meter.integrated_loudness(audio)
        return loudness
    
    def normalize_to_target(self, audio, sample_rate, target_lufs=-14.0, 
                           max_true_peak=-1.0):
        """
        Normalize audio to target LUFS with true peak ceiling
        """
        # Measure current loudness
        current_lufs = self.measure_loudness(audio, sample_rate)
        
        # Calculate required gain
        gain_db = target_lufs - current_lufs
        gain_linear = 10 ** (gain_db / 20.0)
        
        # Apply gain
        normalized = audio * gain_linear
        
        # Check true peak
        from scipy.signal import resample_poly
        audio_os = resample_poly(normalized, 4, 1)
        true_peak = np.max(np.abs(audio_os))
        true_peak_db = 20 * np.log10(true_peak)
        
        # If exceeds ceiling, apply limiter
        if true_peak_db > max_true_peak:
            limiter = TruePeakLimiter({
                'threshold': max_true_peak - 3.0,
                'ceiling': max_true_peak,
                'release': 50
            })
            normalized = limiter.process(normalized, sample_rate)
        
        return normalized, gain_db, true_peak_db
```

#### 10.2 Match Loudness Panel

**UI:**
```html
<div class="match-loudness-panel">
  <h3>Match Loudness</h3>
  
  <div class="loudness-scan">
    <h4>Current Files</h4>
    <table>
      <tr>
        <th>Track</th>
        <th>LUFS</th>
        <th>True Peak</th>
      </tr>
      <tr id="scan-results">
        <!-- Populated after scan -->
      </tr>
    </table>
    <button id="scan-btn">Scan Loudness</button>
  </div>
  
  <div class="loudness-target">
    <h4>Target Settings</h4>
    
    <label>Standard</label>
    <select id="loudness-standard">
      <option value="spotify">Spotify (-14 LUFS)</option>
      <option value="youtube">YouTube (-13 LUFS)</option>
      <option value="ebu">EBU R128 (-23 LUFS)</option>
      <option value="atsc">ATSC A/85 (-24 LUFS)</option>
      <option value="custom">Custom</option>
    </select>
    
    <label>Target LUFS</label>
    <input type="number" id="target-lufs" value="-14.0" step="0.1">
    
    <label>Max True Peak (dBTP)</label>
    <input type="number" id="max-true-peak" value="-1.0" step="0.1">
    
    <button id="match-btn">Match Loudness</button>
  </div>
  
  <div class="loudness-results">
    <!-- Show before/after comparison -->
  </div>
</div>
```

---

### 11. Spectral View

**Goal:** Frequency-domain visualization for detailed analysis.

#### 11.1 Spectral Display

**Implementation:**
```javascript
class SpectralView {
  constructor(canvasId, audioBuffer) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.audioBuffer = audioBuffer;
    
    this.renderSpectrogram();
  }
  
  async renderSpectrogram() {
    const audioData = this.audioBuffer.getChannelData(0);
    const sampleRate = this.audioBuffer.sampleRate;
    
    // Compute STFT
    const stft = await this.computeSTFT(audioData, sampleRate);
    
    // Convert to dB scale
    const stft_db = stft.map(frame => {
      return frame.map(bin => {
        const magnitude = Math.abs(bin);
        return 20 * Math.log10(magnitude + 1e-10);
      });
    });
    
    // Render as image
    this.renderSpectrogramImage(stft_db);
  }
  
  computeSTFT(audio, sampleRate, fftSize = 2048, hopSize = 512) {
    const numFrames = Math.floor((audio.length - fftSize) / hopSize);
    const stft = [];
    
    for (let i = 0; i < numFrames; i++) {
      const start = i * hopSize;
      const frame = audio.slice(start, start + fftSize);
      
      // Apply window (Hann)
      const windowed = frame.map((val, j) => {
        const window = 0.5 * (1 - Math.cos(2 * Math.PI * j / fftSize));
        return val * window;
      });
      
      // FFT (use Web Audio or FFT.js library)
      const spectrum = this.fft(windowed);
      stft.push(spectrum);
    }
    
    return stft;
  }
  
  renderSpectrogramImage(stft_db) {
    const width = stft_db.length;
    const height = stft_db[0].length;
    
    this.canvas.width = width;
    this.canvas.height = height;
    
    const imageData = this.ctx.createImageData(width, height);
    
    // Color mapping (dB to RGB)
    for (let t = 0; t < width; t++) {
      for (let f = 0; f < height; f++) {
        const db = stft_db[t][f];
        
        // Map dB range [-80, 0] to color
        const normalized = (db + 80) / 80;  // 0 to 1
        const color = this.dbToColor(normalized);
        
        const idx = (f * width + t) * 4;
        imageData.data[idx + 0] = color.r;
        imageData.data[idx + 1] = color.g;
        imageData.data[idx + 2] = color.b;
        imageData.data[idx + 3] = 255;
      }
    }
    
    this.ctx.putImageData(imageData, 0, 0);
  }
  
  dbToColor(normalized) {
    // Heat map: blue -> cyan -> green -> yellow -> red
    if (normalized < 0.25) {
      return { r: 0, g: 0, b: Math.floor(normalized * 4 * 255) };
    } else if (normalized < 0.5) {
      return { r: 0, g: Math.floor((normalized - 0.25) * 4 * 255), b: 255 };
    } else if (normalized < 0.75) {
      return { r: Math.floor((normalized - 0.5) * 4 * 255), g: 255, b: 0 };
    } else {
      return { r: 255, g: Math.floor((1 - normalized) * 4 * 255), b: 0 };
    }
  }
}
```

---

## Data Models

### Project File Format (.hxproj)

```json
{
  "version": "1.0",
  "project_id": "proj_abc123",
  "name": "My Mix",
  "created_at": "2025-12-18T10:00:00Z",
  "sample_rate": 44100,
  "bit_depth": 24,
  "tracks": [
    {
      "track_id": "track_1",
      "name": "Vocals",
      "color": "#667eea",
      "stem_source": "job_id/vocals.wav",
      "volume": 0.0,
      "pan": 0,
      "mute": false,
      "solo": false,
      "fx_chain": [
        {
          "slot": 1,
          "type": "eq",
          "bypassed": false,
          "params": {...}
        }
      ],
      "sends": [
        {
          "bus_id": "bus_reverb_1",
          "level": -12.0,
          "pre_fader": false
        }
      ]
    }
  ],
  "buses": [
    {
      "bus_id": "bus_reverb_1",
      "name": "Reverb Hall",
      "type": "aux",
      "volume": 0.0,
      "pan": 0,
      "fx_chain": [...]
    }
  ],
  "master": {
    "volume": 0.0,
    "fx_chain": [...]
  }
}
```

---

## API Endpoints

### Project Management
```
POST   /project/create              Create new project
GET    /project/{id}                Get project details
PUT    /project/{id}                Update project
DELETE /project/{id}                Delete project
GET    /project/{id}/waveforms      Get waveform peak data
```

### Mixing
```
POST   /mixer/update                Update mixer state (volume/pan/sends)
POST   /mixer/render                Offline mix render
```

### Effects
```
GET    /fx/list                     List available effects
POST   /fx/apply                    Apply effect to track/selection
POST   /fx/preview                  Real-time effect preview
```

### Processing
```
POST   /process/dereverb            Apply de-reverb
POST   /process/normalize           Normalize audio
POST   /process/match-loudness      Match loudness to standard
```

### Export
```
POST   /export/mix                  Export final mix
POST   /export/stems                Export processed stems
GET    /export/status/{job_id}      Check export progress
```

---

## Technology Stack

### Frontend
- **UI Framework:** Vanilla JS or React (for complex state)
- **Audio:** Web Audio API + WaveSurfer.js
- **Canvas:** HTML5 Canvas or WebGL (spectral view)
- **State Management:** Redux or Zustand (if React)

### Backend
- **Web Framework:** Flask (dashboard) + FastAPI (API)
- **Audio Processing:** librosa, soundfile, scipy
- **Effects:** Custom DSP + pyloudnorm (loudness)
- **Jobs:** Background threading or Celery

### Storage
- **Projects:** JSON files (.hxproj)
- **Audio:** WAV files (stems + processed)
- **Cache:** Redis (optional, for waveform peaks)

---

## Performance Considerations

1. **Waveform Rendering:**
   - Precompute peaks (decimation)
   - Use Web Workers for peak generation
   - Render with Canvas (2D) or WebGL for large files

2. **Real-time Mixing:**
   - Use Web Audio API for low-latency mixing
   - Offload heavy processing to backend (offline renders)

3. **FX Processing:**
   - Preview mode: Lower quality, faster
   - Render mode: High quality, background job

4. **File Management:**
   - Stream large audio files (chunked reading)
   - Cache intermediate results

---

## Implementation Priorities

### Must-Have (Phase A-B)
✅ Multitrack timeline with waveforms  
✅ Channel strips (volume/pan/mute/solo)  
✅ Basic mixer + master bus  
✅ FX rack (insert chain)  
✅ Buses + sends routing  
✅ Reverb bus system  
✅ Export functionality  

### High-Value (Phase C)
⭐ De-reverb processing  
⭐ Mastering chain (EQ/Comp/Limiter)  
⭐ Match Loudness panel  
⭐ Spectral view  
⭐ LUFS metering  

### Nice-to-Have (Future)
🔮 Automation envelopes  
🔮 MIDI support  
🔮 VST plugin hosting  
🔮 Collaboration features  

---

## Conclusion

This specification provides a complete roadmap for building a **professional DAW workspace** inside Harmonix. By following the phased approach (A → B → C), you'll progressively add features while maintaining a stable foundation.

**Next Steps:**
1. Implement Phase A (Timeline + Mixer MVP)
2. Test with real stems from Harmonix separation
3. Add Phase B (FX Rack + Routing)
4. Implement Phase C (De-reverb + Mastering)

**Estimated Timeline:** 12 weeks for full implementation with 1-2 developers.

---

**Document Version:** 1.0  
**Last Updated:** December 18, 2025  
**Author:** Stephan El Khoury
