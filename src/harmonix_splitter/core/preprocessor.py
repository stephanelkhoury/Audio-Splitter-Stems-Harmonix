"""Audio preprocessing utilities."""

import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple

import librosa
import soundfile as sf
import numpy as np

logger = logging.getLogger(__name__)


class AudioPreprocessor:
    """Handles audio file validation, format conversion, and preprocessing."""
    
    SUPPORTED_FORMATS = [".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac"]
    
    def __init__(
        self,
        target_sr: int = 44100,
        max_duration: Optional[int] = None,
        normalize: bool = True
    ):
        """
        Initialize audio preprocessor.
        
        Args:
            target_sr: Target sample rate
            max_duration: Maximum duration in seconds
            normalize: Whether to normalize audio
        """
        self.target_sr = target_sr
        self.max_duration = max_duration
        self.normalize = normalize
    
    def validate_audio(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate audio file.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file exists
        if not file_path.exists():
            return False, "File does not exist"
        
        # Check file extension
        if file_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            return False, f"Unsupported format. Supported: {self.SUPPORTED_FORMATS}"
        
        # Try to load and get info
        try:
            info = sf.info(str(file_path))
            
            # Check duration
            if self.max_duration and info.duration > self.max_duration:
                return False, f"Duration {info.duration}s exceeds max {self.max_duration}s"
            
            # Check channels
            if info.channels > 2:
                return False, f"Too many channels: {info.channels}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating audio: {e}")
            return False, f"Invalid audio file: {str(e)}"
    
    def preprocess(
        self,
        input_path: Path,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Preprocess audio file to standard format.
        
        Args:
            input_path: Input audio file
            output_path: Optional output path
            
        Returns:
            Path to preprocessed file
        """
        logger.info(f"Preprocessing: {input_path}")
        
        # Validate
        is_valid, error = self.validate_audio(input_path)
        if not is_valid:
            raise ValueError(f"Invalid audio: {error}")
        
        # Load audio
        y, sr = librosa.load(input_path, sr=self.target_sr, mono=False)
        
        # Convert to stereo if mono
        if y.ndim == 1:
            y = np.stack([y, y])
        
        # Normalize
        if self.normalize:
            y = self._normalize_audio(y)
        
        # Determine output path
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_preprocessed.wav"
        
        # Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(output_path, y.T, self.target_sr)
        
        logger.info(f"Preprocessed audio saved to: {output_path}")
        return output_path
    
    def convert_with_ffmpeg(
        self,
        input_path: Path,
        output_path: Path,
        format: str = "wav",
        bitrate: Optional[str] = None
    ) -> Path:
        """
        Convert audio using ffmpeg.
        
        Args:
            input_path: Input file
            output_path: Output file
            format: Output format
            bitrate: Bitrate for lossy formats (e.g., "320k")
            
        Returns:
            Path to converted file
        """
        cmd = ["ffmpeg", "-i", str(input_path), "-y"]
        
        if format == "mp3":
            cmd.extend(["-codec:a", "libmp3lame"])
            if bitrate:
                cmd.extend(["-b:a", bitrate])
        elif format == "wav":
            cmd.extend(["-codec:a", "pcm_s16le"])
        
        cmd.extend(["-ar", str(self.target_sr)])
        cmd.append(str(output_path))
        
        logger.info(f"Converting with ffmpeg: {' '.join(cmd)}")
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg conversion failed: {e.stderr.decode()}")
            raise
    
    def get_audio_info(self, file_path: Path) -> dict:
        """
        Get audio file information.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary with audio metadata
        """
        try:
            info = sf.info(str(file_path))
            
            return {
                "duration": info.duration,
                "sample_rate": info.samplerate,
                "channels": info.channels,
                "format": info.format,
                "subtype": info.subtype,
                "frames": info.frames
            }
        except Exception as e:
            logger.error(f"Error getting audio info: {e}")
            return {}
    
    @staticmethod
    def _normalize_audio(y: np.ndarray, target_db: float = -3.0) -> np.ndarray:
        """
        Normalize audio to target peak level.
        
        Args:
            y: Audio array
            target_db: Target peak level in dB
            
        Returns:
            Normalized audio
        """
        # Calculate current peak
        peak = np.abs(y).max()
        
        if peak == 0:
            return y
        
        # Calculate target peak
        target_peak = 10 ** (target_db / 20.0)
        
        # Normalize
        return y * (target_peak / peak)
