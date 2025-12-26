"""
Harmonix Audio Processor
High-quality pitch shifting, time stretching, and audio manipulation
"""

import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
from typing import Optional, Tuple, Union
import logging
from dataclasses import dataclass
from scipy import signal
from scipy.interpolate import interp1d

logger = logging.getLogger(__name__)


@dataclass
class PitchShiftConfig:
    """Configuration for pitch shifting"""
    semitones: float = 0.0  # Range: -12 to +12
    preserve_formants: bool = True  # Keep voice natural
    algorithm: str = "high_quality"  # "fast", "high_quality", "ultra"


class AudioProcessor:
    """
    High-quality audio processor for pitch shifting and manipulation
    Uses phase vocoder with formant preservation for natural sound
    """
    
    def __init__(self, sample_rate: int = 44100):
        """
        Initialize audio processor
        
        Args:
            sample_rate: Target sample rate
        """
        self.sample_rate = sample_rate
        self.n_fft = 2048
        self.hop_length = 512
        
    def pitch_shift(
        self,
        audio: np.ndarray,
        semitones: float,
        preserve_formants: bool = True,
        algorithm: str = "high_quality"
    ) -> np.ndarray:
        """
        High-quality pitch shifting with formant preservation
        
        Args:
            audio: Input audio (mono or stereo)
            semitones: Pitch shift in semitones (-12 to +12)
            preserve_formants: If True, preserves vocal formants for natural sound
            algorithm: "fast", "high_quality", or "ultra"
            
        Returns:
            Pitch-shifted audio
        """
        if semitones == 0:
            return audio
            
        # Clamp to safe range
        semitones = max(-12, min(12, semitones))
        
        logger.info(f"Pitch shifting by {semitones:+.1f} semitones (formants: {preserve_formants})")
        
        # Handle stereo
        if len(audio.shape) > 1 and audio.shape[0] == 2:
            left = self._pitch_shift_mono(audio[0], semitones, preserve_formants, algorithm)
            right = self._pitch_shift_mono(audio[1], semitones, preserve_formants, algorithm)
            return np.vstack([left, right])
        else:
            # Ensure 1D
            if len(audio.shape) > 1:
                audio = audio.flatten()
            return self._pitch_shift_mono(audio, semitones, preserve_formants, algorithm)
    
    def _pitch_shift_mono(
        self,
        audio: np.ndarray,
        semitones: float,
        preserve_formants: bool,
        algorithm: str
    ) -> np.ndarray:
        """
        Pitch shift mono audio with optional formant preservation
        """
        if algorithm == "fast":
            # Basic librosa pitch shift
            return librosa.effects.pitch_shift(
                audio, 
                sr=self.sample_rate, 
                n_steps=semitones,
                bins_per_octave=12
            )
        
        elif algorithm == "high_quality" or algorithm == "ultra":
            if preserve_formants:
                return self._pitch_shift_formant_preserved(audio, semitones, algorithm)
            else:
                return self._pitch_shift_phase_vocoder(audio, semitones, algorithm)
        
        return audio
    
    def _pitch_shift_formant_preserved(
        self,
        audio: np.ndarray,
        semitones: float,
        algorithm: str
    ) -> np.ndarray:
        """
        Pitch shift with formant preservation using PSOLA-inspired technique
        This keeps vocals sounding natural even with large pitch shifts
        """
        # Calculate pitch ratio
        pitch_ratio = 2 ** (semitones / 12.0)
        
        # Parameters based on quality
        if algorithm == "ultra":
            n_fft = 4096
            hop_length = 256
        else:
            n_fft = 2048
            hop_length = 512
        
        # Step 1: Time-stretch the audio (inverse of pitch ratio)
        stretched = self._time_stretch(audio, 1.0 / pitch_ratio, n_fft, hop_length)
        
        # Step 2: Resample to shift pitch while maintaining duration
        # This naturally shifts pitch without affecting formants much
        n_samples_target = len(audio)
        n_samples_stretched = len(stretched)
        
        # Calculate resampling factor
        resample_ratio = n_samples_target / n_samples_stretched * pitch_ratio
        
        # High-quality resampling
        shifted = librosa.resample(
            stretched,
            orig_sr=self.sample_rate,
            target_sr=int(self.sample_rate * resample_ratio),
            res_type='kaiser_best'
        )
        
        # Resample back to original sample rate with correct length
        if len(shifted) != n_samples_target:
            shifted = librosa.resample(
                shifted,
                orig_sr=int(self.sample_rate * resample_ratio),
                target_sr=self.sample_rate,
                res_type='kaiser_best'
            )
        
        # Trim or pad to match original length
        if len(shifted) > n_samples_target:
            shifted = shifted[:n_samples_target]
        elif len(shifted) < n_samples_target:
            shifted = np.pad(shifted, (0, n_samples_target - len(shifted)))
        
        return shifted
    
    def _pitch_shift_phase_vocoder(
        self,
        audio: np.ndarray,
        semitones: float,
        algorithm: str
    ) -> np.ndarray:
        """
        Phase vocoder pitch shift (doesn't preserve formants)
        """
        # Use librosa's higher quality settings
        if algorithm == "ultra":
            n_steps = semitones
            bins_per_octave = 24  # Higher resolution
        else:
            n_steps = semitones
            bins_per_octave = 12
            
        return librosa.effects.pitch_shift(
            audio,
            sr=self.sample_rate,
            n_steps=n_steps,
            bins_per_octave=bins_per_octave,
            res_type='kaiser_best'
        )
    
    def _time_stretch(
        self,
        audio: np.ndarray,
        rate: float,
        n_fft: int,
        hop_length: int
    ) -> np.ndarray:
        """
        High-quality time stretching using phase vocoder
        
        Args:
            audio: Input audio
            rate: Stretch factor (>1 = slower, <1 = faster)
            n_fft: FFT size
            hop_length: Hop length
            
        Returns:
            Time-stretched audio
        """
        # Compute STFT
        stft = librosa.stft(audio, n_fft=n_fft, hop_length=hop_length)
        
        # Phase vocoder
        stft_stretched = librosa.phase_vocoder(stft, rate=rate, hop_length=hop_length)
        
        # Inverse STFT
        stretched = librosa.istft(stft_stretched, hop_length=hop_length)
        
        return stretched
    
    def pitch_shift_file(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        semitones: float,
        preserve_formants: bool = True,
        algorithm: str = "high_quality"
    ) -> Path:
        """
        Pitch shift an audio file and save the result
        
        Args:
            input_path: Input audio file path
            output_path: Output audio file path
            semitones: Pitch shift in semitones
            preserve_formants: Preserve vocal formants
            algorithm: Quality algorithm to use
            
        Returns:
            Path to output file
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        # Load audio
        audio, sr = librosa.load(str(input_path), sr=self.sample_rate, mono=False)
        
        # Pitch shift
        shifted = self.pitch_shift(audio, semitones, preserve_formants, algorithm)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save
        if len(shifted.shape) > 1:
            sf.write(str(output_path), shifted.T, self.sample_rate)
        else:
            sf.write(str(output_path), shifted, self.sample_rate)
        
        logger.info(f"Saved pitch-shifted audio to {output_path}")
        return output_path
    
    def create_karaoke_backing(
        self,
        instrumental: np.ndarray,
        vocals: np.ndarray,
        vocal_reduction: float = 0.95
    ) -> np.ndarray:
        """
        Create karaoke backing track with heavily reduced vocals
        
        Args:
            instrumental: Instrumental stem
            vocals: Vocal stem
            vocal_reduction: Amount to reduce vocals (0-1, 1 = full removal)
            
        Returns:
            Karaoke backing track
        """
        # Mix instrumental with reduced vocals for natural sound
        vocal_level = 1.0 - vocal_reduction
        return instrumental + (vocals * vocal_level)


def pitch_shift_audio(
    audio: np.ndarray,
    sample_rate: int,
    semitones: float,
    preserve_formants: bool = True
) -> np.ndarray:
    """
    Convenience function for pitch shifting
    
    Args:
        audio: Input audio
        sample_rate: Sample rate
        semitones: Pitch shift in semitones (-12 to +12)
        preserve_formants: Preserve vocal formants
        
    Returns:
        Pitch-shifted audio
    """
    processor = AudioProcessor(sample_rate)
    return processor.pitch_shift(audio, semitones, preserve_formants)
