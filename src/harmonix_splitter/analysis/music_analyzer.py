"""
Music Analysis Module
Advanced audio analysis for tempo, key/scale detection, and music structure
"""

import logging
import numpy as np
import librosa
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class MusicalKey(Enum):
    """Musical keys"""
    C = "C"
    C_SHARP = "C#"
    D = "D"
    D_SHARP = "D#"
    E = "E"
    F = "F"
    F_SHARP = "F#"
    G = "G"
    G_SHARP = "G#"
    A = "A"
    A_SHARP = "A#"
    B = "B"


class ScaleType(Enum):
    """Musical scale types"""
    MAJOR = "Major"
    MINOR = "Minor"
    DORIAN = "Dorian"
    PHRYGIAN = "Phrygian"
    LYDIAN = "Lydian"
    MIXOLYDIAN = "Mixolydian"
    LOCRIAN = "Locrian"
    HARMONIC_MINOR = "Harmonic Minor"
    MELODIC_MINOR = "Melodic Minor"


@dataclass
class TempoAnalysis:
    """Container for tempo analysis results"""
    bpm: float
    bpm_confidence: float
    beat_positions: np.ndarray = field(default_factory=lambda: np.array([]))
    downbeat_positions: np.ndarray = field(default_factory=lambda: np.array([]))
    time_signature: Tuple[int, int] = (4, 4)
    tempo_stability: float = 1.0  # 0-1, how stable the tempo is


@dataclass
class KeyAnalysis:
    """Container for key/scale analysis results"""
    key: str
    scale: str
    confidence: float
    key_profile: np.ndarray = field(default_factory=lambda: np.array([]))
    alternative_keys: List[Tuple[str, str, float]] = field(default_factory=list)
    chroma_features: np.ndarray = field(default_factory=lambda: np.array([]))


@dataclass
class MusicAnalysis:
    """Complete music analysis results"""
    tempo: TempoAnalysis
    key: KeyAnalysis
    duration: float
    sample_rate: int
    energy_profile: np.ndarray = field(default_factory=lambda: np.array([]))
    sections: List[Dict] = field(default_factory=list)


class MusicAnalyzer:
    """
    Advanced music analysis for tempo, key detection and structure
    Uses multiple algorithms for high accuracy
    """
    
    # Krumhansl-Kessler key profiles (normalized)
    MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    
    # Note names for key detection
    NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    def __init__(
        self,
        sample_rate: int = 44100,
        hop_length: int = 512,
        n_fft: int = 2048
    ):
        """
        Initialize music analyzer
        
        Args:
            sample_rate: Target sample rate for analysis
            hop_length: Hop length for STFT
            n_fft: FFT size
        """
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self.n_fft = n_fft
        
        # Normalize key profiles
        self.major_profile = self.MAJOR_PROFILE / np.sum(self.MAJOR_PROFILE)
        self.minor_profile = self.MINOR_PROFILE / np.sum(self.MINOR_PROFILE)
    
    def analyze(self, audio_path: Path) -> MusicAnalysis:
        """
        Perform complete music analysis
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            MusicAnalysis with tempo, key, and structure
        """
        logger.info(f"Analyzing music: {audio_path}")
        
        # Load audio
        y, sr = librosa.load(str(audio_path), sr=self.sample_rate, mono=True)
        duration = len(y) / sr
        
        # Perform tempo analysis
        tempo_analysis = self.analyze_tempo(y, sr)
        logger.info(f"Detected tempo: {tempo_analysis.bpm:.1f} BPM (confidence: {tempo_analysis.bpm_confidence:.2f})")
        
        # Perform key analysis
        key_analysis = self.analyze_key(y, sr)
        logger.info(f"Detected key: {key_analysis.key} {key_analysis.scale} (confidence: {key_analysis.confidence:.2f})")
        
        # Calculate energy profile
        energy = librosa.feature.rms(y=y, hop_length=self.hop_length)[0]
        
        # Detect sections (verse, chorus, etc.)
        sections = self.detect_sections(y, sr)
        
        return MusicAnalysis(
            tempo=tempo_analysis,
            key=key_analysis,
            duration=duration,
            sample_rate=sr,
            energy_profile=energy,
            sections=sections
        )
    
    def analyze_tempo(self, y: np.ndarray, sr: int) -> TempoAnalysis:
        """
        Analyze tempo with multiple methods for accuracy
        
        Args:
            y: Audio signal
            sr: Sample rate
            
        Returns:
            TempoAnalysis with BPM and beat positions
        """
        # Method 1: librosa beat tracking
        tempo_librosa, beat_frames = librosa.beat.beat_track(
            y=y, sr=sr, hop_length=self.hop_length
        )
        
        # Handle scalar or array tempo
        if isinstance(tempo_librosa, np.ndarray):
            tempo_librosa = float(tempo_librosa[0]) if len(tempo_librosa) > 0 else 120.0
        else:
            tempo_librosa = float(tempo_librosa)
        
        # Method 2: Onset-based tempo estimation
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=self.hop_length)
        tempo_onset = librosa.feature.tempo(
            onset_envelope=onset_env, sr=sr, hop_length=self.hop_length
        )
        if isinstance(tempo_onset, np.ndarray):
            tempo_onset = float(tempo_onset[0]) if len(tempo_onset) > 0 else tempo_librosa
        
        # Method 3: Autocorrelation-based tempo
        tempo_ac = self._autocorrelation_tempo(onset_env, sr)
        
        # Combine estimates (weighted average)
        tempos = [tempo_librosa, tempo_onset, tempo_ac]
        tempos = [t for t in tempos if 40 < t < 220]  # Filter outliers
        
        if tempos:
            # Weight towards the mode
            final_tempo = np.median(tempos)
        else:
            final_tempo = tempo_librosa
        
        # Calculate confidence based on agreement
        if len(tempos) > 1:
            tempo_std = np.std(tempos)
            confidence = max(0.0, 1.0 - (tempo_std / 20.0))  # Higher std = lower confidence
        else:
            confidence = 0.7
        
        # Get beat times
        beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=self.hop_length)
        
        # Estimate tempo stability
        if len(beat_times) > 2:
            inter_beat_intervals = np.diff(beat_times)
            expected_ibi = 60.0 / final_tempo
            ibi_variance = np.var(inter_beat_intervals) / (expected_ibi ** 2)
            tempo_stability = max(0.0, 1.0 - ibi_variance * 10)
        else:
            tempo_stability = 0.5
        
        # Estimate downbeats (every 4 beats for 4/4)
        downbeat_positions = beat_times[::4] if len(beat_times) >= 4 else beat_times
        
        return TempoAnalysis(
            bpm=round(final_tempo, 1),
            bpm_confidence=round(confidence, 2),
            beat_positions=beat_times,
            downbeat_positions=downbeat_positions,
            time_signature=(4, 4),  # Default, could be detected
            tempo_stability=round(tempo_stability, 2)
        )
    
    def _autocorrelation_tempo(self, onset_env: np.ndarray, sr: int) -> float:
        """
        Estimate tempo using autocorrelation
        
        Args:
            onset_env: Onset strength envelope
            sr: Sample rate
            
        Returns:
            Estimated tempo in BPM
        """
        # Compute autocorrelation
        ac = librosa.autocorrelate(onset_env, max_size=len(onset_env) // 2)
        
        # Find peaks in autocorrelation (corresponding to tempo)
        # Convert frame indices to BPM
        min_lag = int(sr / self.hop_length * 60 / 200)  # 200 BPM max
        max_lag = int(sr / self.hop_length * 60 / 40)   # 40 BPM min
        
        if max_lag > len(ac):
            max_lag = len(ac) - 1
        
        ac_segment = ac[min_lag:max_lag]
        if len(ac_segment) > 0:
            peak_idx = np.argmax(ac_segment) + min_lag
            tempo = 60.0 * sr / self.hop_length / peak_idx
        else:
            tempo = 120.0
        
        return tempo
    
    def analyze_key(self, y: np.ndarray, sr: int) -> KeyAnalysis:
        """
        Analyze musical key using chroma features and key profiles
        
        Args:
            y: Audio signal
            sr: Sample rate
            
        Returns:
            KeyAnalysis with detected key and scale
        """
        # Extract chroma features (pitch class energy distribution)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=self.hop_length)
        
        # Average chroma across time
        chroma_avg = np.mean(chroma, axis=1)
        chroma_avg = chroma_avg / (np.sum(chroma_avg) + 1e-8)  # Normalize
        
        # Compare against all 24 major/minor key profiles
        correlations = []
        
        for i in range(12):
            # Rotate profiles to each key
            major_rotated = np.roll(self.major_profile, i)
            minor_rotated = np.roll(self.minor_profile, i)
            
            # Compute correlation
            major_corr = np.corrcoef(chroma_avg, major_rotated)[0, 1]
            minor_corr = np.corrcoef(chroma_avg, minor_rotated)[0, 1]
            
            correlations.append((self.NOTE_NAMES[i], 'Major', major_corr))
            correlations.append((self.NOTE_NAMES[i], 'Minor', minor_corr))
        
        # Sort by correlation
        correlations.sort(key=lambda x: x[2], reverse=True)
        
        # Best match
        best_key, best_scale, best_corr = correlations[0]
        
        # Calculate confidence
        if len(correlations) > 1:
            second_best_corr = correlations[1][2]
            confidence = (best_corr - second_best_corr) / (best_corr + 0.01)
            confidence = max(0.0, min(1.0, (best_corr + 1) / 2))  # Normalize -1 to 1 -> 0 to 1
        else:
            confidence = 0.5
        
        # Get alternative keys
        alternatives = correlations[1:4]
        
        return KeyAnalysis(
            key=best_key,
            scale=best_scale,
            confidence=round(confidence, 2),
            key_profile=chroma_avg,
            alternative_keys=alternatives,
            chroma_features=chroma
        )
    
    def detect_sections(self, y: np.ndarray, sr: int) -> List[Dict]:
        """
        Detect song sections (verse, chorus, etc.) using self-similarity
        
        Args:
            y: Audio signal
            sr: Sample rate
            
        Returns:
            List of section dictionaries with start/end times
        """
        # Use structural segmentation
        try:
            # Compute chroma for structure analysis
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=self.hop_length)
            
            # Compute MFCC for timbre
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=self.hop_length)
            
            # Combine features
            features = np.vstack([chroma, mfcc])
            
            # Compute self-similarity matrix
            rec = librosa.segment.recurrence_matrix(
                features, 
                mode='affinity',
                metric='cosine',
                sym=True
            )
            
            # Find boundaries
            bounds = librosa.segment.agglomerative(features, k=8)
            bound_times = librosa.frames_to_time(bounds, sr=sr, hop_length=self.hop_length)
            
            # Create section list
            sections = []
            for i in range(len(bound_times) - 1):
                sections.append({
                    'start': float(bound_times[i]),
                    'end': float(bound_times[i + 1]),
                    'duration': float(bound_times[i + 1] - bound_times[i]),
                    'label': f'Section {i + 1}'
                })
            
            return sections
            
        except Exception as e:
            logger.warning(f"Section detection failed: {e}")
            return []
    
    def get_camelot_wheel(self, key: str, scale: str) -> str:
        """
        Convert key/scale to Camelot wheel notation for DJ mixing
        
        Args:
            key: Musical key (e.g., 'C', 'F#')
            scale: Scale type ('Major' or 'Minor')
            
        Returns:
            Camelot notation (e.g., '8B', '5A')
        """
        major_wheel = {
            'B': '1B', 'F#': '2B', 'C#': '3B', 'G#': '4B',
            'D#': '5B', 'A#': '6B', 'F': '7B', 'C': '8B',
            'G': '9B', 'D': '10B', 'A': '11B', 'E': '12B'
        }
        
        minor_wheel = {
            'G#': '1A', 'D#': '2A', 'A#': '3A', 'F': '4A',
            'C': '5A', 'G': '6A', 'D': '7A', 'A': '8A',
            'E': '9A', 'B': '10A', 'F#': '11A', 'C#': '12A'
        }
        
        if scale == 'Major':
            return major_wheel.get(key, 'N/A')
        else:
            return minor_wheel.get(key, 'N/A')


def estimate_processing_time(
    duration_seconds: float,
    quality: str = 'balanced',
    has_gpu: bool = False,
    mode: str = 'grouped'
) -> Dict[str, float]:
    """
    Estimate processing time for audio separation
    
    Args:
        duration_seconds: Audio duration in seconds
        quality: Quality mode (fast/balanced/studio)
        has_gpu: Whether GPU is available
        mode: Separation mode
        
    Returns:
        Dictionary with time estimates
    """
    # Base processing ratios (processing_time / audio_duration)
    if has_gpu:
        base_ratios = {
            'fast': 0.2,
            'balanced': 0.4,
            'studio': 1.5  # Studio mode is much more intensive
        }
    else:
        base_ratios = {
            'fast': 1.5,
            'balanced': 3.0,
            'studio': 8.0  # Studio on CPU takes much longer
        }
    
    ratio = base_ratios.get(quality, 3.0)
    
    # Add overhead for per-instrument mode
    if mode == 'per_instrument':
        ratio *= 1.8
    
    # Calculate estimates
    base_time = duration_seconds * ratio
    
    # Add analysis time
    analysis_time = min(30, duration_seconds * 0.1)  # ~10% or max 30s for analysis
    
    return {
        'separation_seconds': round(base_time, 1),
        'analysis_seconds': round(analysis_time, 1),
        'total_seconds': round(base_time + analysis_time, 1),
        'separation_formatted': format_time(base_time),
        'total_formatted': format_time(base_time + analysis_time),
        'quality': quality,
        'has_gpu': has_gpu
    }


def format_time(seconds: float) -> str:
    """Format seconds into human readable string"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"
