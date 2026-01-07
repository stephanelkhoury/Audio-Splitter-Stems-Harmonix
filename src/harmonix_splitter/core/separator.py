"""
Harmonix Audio Stem Separator
Core separation engine using Demucs v4 with GPU acceleration
"""

import torch
import torchaudio
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class QualityMode(Enum):
    """Processing quality presets"""
    FAST = "fast"
    BALANCED = "balanced"
    STUDIO = "studio"


class SeparationMode(Enum):
    """Separation granularity modes"""
    GROUPED = "grouped"  # Standard 4-stem
    PER_INSTRUMENT = "per_instrument"  # Individual instrument stems
    KARAOKE = "karaoke"  # 2-stem: Vocals + Instrumental


@dataclass
class SeparationConfig:
    """Configuration for separation process"""
    quality: QualityMode = QualityMode.BALANCED
    mode: SeparationMode = SeparationMode.GROUPED
    target_instruments: Optional[List[str]] = None
    use_gpu: bool = True
    sample_rate: int = 44100
    preserve_sample_rate: bool = True  # Keep original sample rate if possible
    segment_duration: Optional[int] = None  # Auto-segment for long files
    overlap: float = 0.25  # Overlap ratio for segments
    
    # Output format settings - MP3 by default for smaller files
    output_format: str = "mp3"  # "mp3" (compressed) or "wav" (lossless)
    bit_depth: int = 24  # 16, 24, or 32 for WAV
    mp3_bitrate: int = 320  # kbps for MP3 (320 = highest quality)
    
    # Studio quality settings
    shifts: int = 1  # Number of random shifts for TTA (test-time augmentation)
    split: bool = True  # Split audio into segments
    jobs: int = 0  # Number of parallel jobs (0=auto)


@dataclass
class StemOutput:
    """Container for separated stem"""
    name: str
    audio: np.ndarray
    sample_rate: int
    confidence: float = 1.0
    metadata: Optional[Dict] = None


class HarmonixSeparator:
    """
    Main separator class for stem extraction
    Supports Demucs v4, HTDemucs, and custom refinement models
    """
    
    CORE_STEMS = ["vocals", "drums", "bass", "other"]
    INSTRUMENT_STEMS = [
        "vocals", "drums", "bass", "guitar", "piano", 
        "strings", "synth", "brass", "woodwinds", "fx"
    ]
    
    def __init__(self, config: Optional[SeparationConfig] = None):
        """
        Initialize separator with configuration
        
        Args:
            config: Separation configuration
        """
        self.config = config or SeparationConfig()
        self.device = self._setup_device()
        self.models = {}
        self._load_models()
        
        logger.info(
            f"Harmonix Separator initialized - Mode: {self.config.mode.value}, "
            f"Quality: {self.config.quality.value}, Device: {self.device}"
        )
    
    def _setup_device(self) -> torch.device:
        """Setup computation device (GPU/MPS/CPU)"""
        if self.config.use_gpu:
            # Check for NVIDIA CUDA GPU
            if torch.cuda.is_available():
                device = torch.device("cuda")
                logger.info(f"Using NVIDIA GPU: {torch.cuda.get_device_name(0)}")
                return device
            
            # Check for Apple Silicon MPS (Metal Performance Shaders)
            if torch.backends.mps.is_available():
                device = torch.device("mps")
                logger.info("Using Apple Silicon GPU (MPS) for acceleration")
                return device
        
        device = torch.device("cpu")
        logger.info("Using CPU for processing")
        return device
    
    def _load_models(self):
        """Load appropriate models based on configuration"""
        try:
            # Import demucs here to avoid import errors if not installed
            from demucs.pretrained import get_model
            from demucs.apply import apply_model
            
            # Select model based on quality
            model_name = self._get_model_name()
            logger.info(f"Loading model: {model_name}")
            
            self.models['primary'] = get_model(model_name)
            self.models['primary'].to(self.device)
            self.models['primary'].eval()
            
            # Store apply function
            self._apply_model = apply_model
            
            # Load instrument refinement models if needed
            if self.config.mode == SeparationMode.PER_INSTRUMENT:
                self._load_refinement_models()
            
            logger.info("Models loaded successfully")
            
        except ImportError:
            raise ImportError(
                "Demucs not installed. Install with: pip install demucs"
            )
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise
    
    def _get_model_name(self) -> str:
        """Get Demucs model name based on quality setting"""
        quality_map = {
            QualityMode.FAST: "htdemucs",       # Standard model, fast
            QualityMode.BALANCED: "htdemucs_ft", # Fine-tuned, better quality
            QualityMode.STUDIO: "htdemucs_6s"   # 6-source model, highest quality
        }
        return quality_map[self.config.quality]
    
    def _get_separation_params(self) -> Dict:
        """Get separation parameters based on quality mode"""
        if self.config.quality == QualityMode.FAST:
            return {
                'shifts': 0,           # No augmentation
                'overlap': 0.1,        # Minimal overlap
                'split': True,
                'segment': 7.8,        # Shorter segments
            }
        elif self.config.quality == QualityMode.BALANCED:
            return {
                'shifts': 1,           # 1 shift for TTA
                'overlap': 0.25,       # Standard overlap
                'split': True,
                'segment': None,       # Default segmentation
            }
        else:  # STUDIO
            return {
                'shifts': 5,           # Multiple shifts for best quality
                'overlap': 0.5,        # High overlap for better blending
                'split': True,
                'segment': None,       # Full processing
            }
    
    def _load_refinement_models(self):
        """Load specialized models for instrument-level separation"""
        # Placeholder for future instrument-specific models
        # Could include guitar/piano/strings specialized models
        logger.info("Refinement models will be loaded in Phase 2")
        self.models['refinement'] = {}
    
    def separate(
        self, 
        audio_path: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        custom_name: Optional[str] = None
    ) -> Dict[str, StemOutput]:
        """
        Separate audio file into stems
        
        Args:
            audio_path: Path to input audio file
            output_dir: Optional directory to save stems
            custom_name: Optional custom name for output files
            
        Returns:
            Dictionary mapping stem name to StemOutput
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        logger.info(f"Starting separation: {audio_path.name}")
        
        # Load audio
        audio, sr = self._load_audio(audio_path)
        
        # Perform primary separation
        stems = self._separate_primary(audio, sr)
        
        # Handle different separation modes
        if self.config.mode == SeparationMode.KARAOKE:
            # Create karaoke 2-stem output: vocals + instrumental
            stems = self._create_karaoke_stems(stems)
        elif self.config.mode == SeparationMode.PER_INSTRUMENT:
            stems = self._refine_instruments(stems)
        
        # Save stems if output directory specified
        if output_dir:
            # Use custom name if provided, otherwise use audio filename
            save_name = custom_name if custom_name else audio_path.stem
            self._save_stems(stems, output_dir, save_name)
        
        logger.info(f"Separation complete: {len(stems)} stems extracted")
        return stems
    
    def _load_audio(self, path: Path) -> Tuple[torch.Tensor, int]:
        """
        Load and preprocess audio file
        
        QUALITY PRESERVATION:
        - Preserves original sample rate when possible (48kHz, 96kHz, etc.)
        - No unnecessary resampling
        - Maintains full bit depth
        
        Args:
            path: Audio file path
            
        Returns:
            Tuple of (audio tensor, sample rate)
        """
        try:
            # First, get the native sample rate
            import soundfile as sf
            info = sf.info(str(path))
            native_sr = info.samplerate
            native_channels = info.channels
            
            logger.info(f"Source audio: {native_sr}Hz, {native_channels} channels, {info.subtype}")
            
            # Determine target sample rate
            if self.config.preserve_sample_rate and native_sr >= 44100:
                # Keep native rate if it's standard (44.1k, 48k, 88.2k, 96k)
                target_sr = native_sr
                logger.info(f"Preserving native sample rate: {native_sr}Hz")
            else:
                # Resample to config rate
                target_sr = self.config.sample_rate
                if target_sr != native_sr:
                    logger.info(f"Resampling from {native_sr}Hz to {target_sr}Hz")
            
            # Load audio with target sample rate (None = native rate)
            load_sr = target_sr if target_sr != native_sr else None
            audio_np, sr = librosa.load(str(path), sr=load_sr, mono=False)
            
            # Update actual sample rate
            if load_sr is None:
                sr = native_sr
            
            # Store original sample rate for output
            self._original_sample_rate = sr
            
            # Convert to tensor
            if audio_np.ndim == 1:
                audio_np = np.stack([audio_np, audio_np])  # Mono to stereo
            audio = torch.from_numpy(audio_np).float()
            
            # Convert to stereo if mono
            if audio.shape[0] == 1:
                audio = audio.repeat(2, 1)
            
            # Move to device
            audio = audio.to(self.device)
            
            duration = audio.shape[1] / sr
            logger.info(
                f"Audio loaded: {duration:.2f}s, "
                f"{sr}Hz, {audio.shape[0]} channels (NO QUALITY LOSS)"
            )
            
            return audio, sr
            
        except Exception as e:
            logger.error(f"Failed to load audio: {e}")
            raise
    
    def _separate_primary(
        self, 
        audio: torch.Tensor, 
        sr: int
    ) -> Dict[str, StemOutput]:
        """
        Perform primary 4-stem separation using Demucs
        
        Args:
            audio: Audio tensor [channels, samples]
            sr: Sample rate
            
        Returns:
            Dictionary of stem outputs
        """
        quality_name = self.config.quality.value.upper()
        logger.info(f"Running {quality_name} quality separation")
        
        # Get quality-specific parameters
        params = self._get_separation_params()
        
        with torch.no_grad():
            # Add batch dimension
            audio_batch = audio.unsqueeze(0)
            
            # Apply model with quality-specific settings
            sources = self._apply_model(
                self.models['primary'],
                audio_batch,
                device=self.device,
                shifts=params.get('shifts', 1),
                split=params.get('split', True),
                overlap=params.get('overlap', 0.25),
                segment=params.get('segment', self.config.segment_duration)
            )
            
            # Remove batch dimension
            sources = sources.squeeze(0)
        
        # Convert to stem outputs
        stems = {}
        source_names = self.models['primary'].sources
        
        for idx, name in enumerate(source_names):
            # Convert to numpy
            audio_np = sources[idx].cpu().numpy()
            
            stems[name] = StemOutput(
                name=name,
                audio=audio_np,
                sample_rate=sr,
                confidence=1.0,
                metadata={
                    'model': self._get_model_name(),
                    'quality': self.config.quality.value,
                    'shifts': params.get('shifts', 1),
                    'overlap': params.get('overlap', 0.25)
                }
            )
            
            logger.debug(f"Extracted stem: {name} - {audio_np.shape}")
        
        return stems
    
    def _create_karaoke_stems(
        self,
        stems: Dict[str, StemOutput]
    ) -> Dict[str, StemOutput]:
        """
        Create karaoke 2-stem output: Vocals + Instrumental
        
        Instrumental is created by mixing drums + bass + other for highest quality
        
        Args:
            stems: Initial 4-stem separation
            
        Returns:
            Dictionary with 'vocals' and 'instrumental' stems
        """
        logger.info("Creating karaoke stems (Vocals + Instrumental)")
        
        karaoke_stems = {}
        
        # Keep vocals as-is
        if "vocals" in stems:
            karaoke_stems["vocals"] = stems["vocals"]
        
        # Create instrumental by mixing all non-vocal stems
        # This gives better quality than using a direct 2-stem model
        instrumental_parts = []
        sr = None
        
        for key in ["drums", "bass", "other", "guitar", "piano"]:
            if key in stems:
                instrumental_parts.append(stems[key].audio)
                sr = stems[key].sample_rate
        
        if instrumental_parts and sr:
            # Mix all parts
            max_len = max(part.shape[-1] for part in instrumental_parts)
            
            # Pad if needed and sum
            instrumental_mix = np.zeros_like(instrumental_parts[0])
            if instrumental_mix.shape[-1] < max_len:
                instrumental_mix = np.zeros((instrumental_parts[0].shape[0], max_len))
            
            for part in instrumental_parts:
                if part.shape[-1] < max_len:
                    # Pad
                    padded = np.zeros((part.shape[0], max_len))
                    padded[:, :part.shape[-1]] = part
                    instrumental_mix += padded
                else:
                    instrumental_mix += part
            
            karaoke_stems["instrumental"] = StemOutput(
                name="instrumental",
                audio=instrumental_mix,
                sample_rate=sr,
                confidence=1.0,
                metadata={
                    'model': self._get_model_name(),
                    'quality': self.config.quality.value,
                    'type': 'karaoke_instrumental',
                    'components': list(stems.keys())
                }
            )
        
        logger.info(f"Karaoke stems created: {list(karaoke_stems.keys())}")
        return karaoke_stems
    
    def _refine_instruments(
        self, 
        stems: Dict[str, StemOutput]
    ) -> Dict[str, StemOutput]:
        """
        Refine 'other' stem into individual instruments
        
        Args:
            stems: Initial 4-stem separation
            
        Returns:
            Refined stems with individual instruments
        """
        logger.info("Refining instruments from 'other' stem")
        
        # Get target instruments from config or use defaults
        target_instruments = self.config.target_instruments or [
            "guitar", "piano", "strings", "synth"
        ]
        
        refined_stems = {}
        
        # Keep vocals, drums, bass as-is
        for key in ["vocals", "drums", "bass"]:
            if key in stems:
                refined_stems[key] = stems[key]
        
        # Process 'other' stem
        if "other" in stems:
            other_audio = stems["other"].audio
            other_sr = stems["other"].sample_rate
            
            # TODO: Phase 2 - Implement instrument-specific separation
            # For now, use placeholder logic
            
            # Simple spectral-based heuristics (placeholder)
            instrument_stems = self._extract_instruments_heuristic(
                other_audio, other_sr, target_instruments
            )
            
            refined_stems.update(instrument_stems)
        
        logger.info(f"Refinement complete: {len(refined_stems)} instruments")
        return refined_stems
    
    def _extract_instruments_heuristic(
        self,
        audio: np.ndarray,
        sr: int,
        target_instruments: List[str]
    ) -> Dict[str, StemOutput]:
        """
        Placeholder heuristic-based instrument extraction
        TODO: Replace with ML models in Phase 2
        
        Args:
            audio: Audio array [channels, samples]
            sr: Sample rate
            target_instruments: List of instruments to extract
            
        Returns:
            Dictionary of instrument stems
        """
        instruments = {}
        
        # Placeholder: Just duplicate 'other' for now
        # Real implementation would use specialized models
        for instrument in target_instruments:
            instruments[instrument] = StemOutput(
                name=instrument,
                audio=audio,  # TODO: actual separation
                sample_rate=sr,
                confidence=0.5,  # Low confidence for heuristic
                metadata={'method': 'heuristic_placeholder'}
            )
            logger.debug(f"Extracted (placeholder): {instrument}")
        
        return instruments
    
    def _save_stems(
        self, 
        stems: Dict[str, StemOutput],
        output_dir: Union[str, Path],
        base_name: str
    ):
        """
        Save stems to disk
        
        Args:
            stems: Dictionary of stem outputs
            output_dir: Output directory
            base_name: Base filename for stems (should be original audio filename or custom name)
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if base_name has job_id prefix (format: jobid_filename)
        # If so, extract just the filename part
        if '_' in base_name and len(base_name.split('_')[0]) > 30:  # job_id is UUID (>30 chars)
            parts = base_name.split('_', 1)
            if len(parts) > 1:
                clean_name = parts[1]  # Get everything after first underscore
            else:
                clean_name = base_name
        else:
            clean_name = base_name
        
        for name, stem in stems.items():
            # Determine output format based on config
            output_format = getattr(self.config, 'output_format', 'mp3')
            bit_depth = getattr(self.config, 'bit_depth', 24)
            mp3_bitrate = getattr(self.config, 'mp3_bitrate', 320)
            
            # Map bit depth to soundfile subtype
            bit_depth_map = {
                16: 'PCM_16',
                24: 'PCM_24',
                32: 'FLOAT'
            }
            subtype = bit_depth_map.get(bit_depth, 'PCM_24')
            
            if output_format == 'mp3':
                # Save as MP3 (compressed)
                mp3_path = output_dir / f"{clean_name}_{name}.mp3"
                
                import tempfile
                import subprocess
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                    tmp_wav_path = tmp.name
                
                # Save temporary WAV at full quality
                sf.write(
                    tmp_wav_path,
                    stem.audio.T,
                    stem.sample_rate,
                    subtype=subtype
                )
                
                # Convert to MP3 using ffmpeg
                try:
                    subprocess.run([
                        'ffmpeg', '-y', '-i', tmp_wav_path,
                        '-codec:a', 'libmp3lame',
                        '-b:a', f'{mp3_bitrate}k',
                        '-q:a', '0',
                        str(mp3_path)
                    ], check=True, capture_output=True)
                    
                    Path(tmp_wav_path).unlink()
                    logger.debug(f"Saved MP3 ({mp3_bitrate}kbps): {mp3_path}")
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    logger.warning(f"FFmpeg not available, saving as WAV: {e}")
                    wav_path = output_dir / f"{clean_name}_{name}.wav"
                    Path(tmp_wav_path).rename(wav_path)
            else:
                # Save as lossless WAV (default - best quality)
                wav_path = output_dir / f"{clean_name}_{name}.wav"
                
                # Save with full quality
                sf.write(
                    str(wav_path),
                    stem.audio.T,  # Transpose to (samples, channels)
                    stem.sample_rate,
                    subtype=subtype  # 24-bit by default for studio quality
                )
                
                logger.debug(f"Saved lossless WAV ({bit_depth}-bit, {stem.sample_rate}Hz): {wav_path}")
        
        logger.info(f"All stems saved to: {output_dir}")
    
    def get_available_models(self) -> Dict[str, any]:
        """
        Get information about available models
        
        Returns:
            Dictionary with model information
        """
        return {
            'quality_modes': [mode.value for mode in QualityMode],
            'separation_modes': [mode.value for mode in SeparationMode],
            'core_stems': self.CORE_STEMS,
            'instrument_stems': self.INSTRUMENT_STEMS,
            'current_config': {
                'quality': self.config.quality.value,
                'mode': self.config.mode.value,
                'device': str(self.device)
            }
        }
    
    def estimate_processing_time(
        self, 
        audio_duration: float
    ) -> Dict[str, any]:
        """
        Estimate processing time for given audio duration
        
        Args:
            audio_duration: Duration in seconds
            
        Returns:
            Dictionary with time estimates and breakdown
        """
        # Base ratios based on quality and device
        if self.device.type == 'cuda':
            ratios = {
                QualityMode.FAST: 0.2,      # 5x faster than realtime
                QualityMode.BALANCED: 0.5,  # 2x faster than realtime
                QualityMode.STUDIO: 2.0     # 0.5x realtime (takes 2x duration)
            }
        else:
            ratios = {
                QualityMode.FAST: 1.5,      # 1.5x audio duration
                QualityMode.BALANCED: 4.0,  # 4x audio duration
                QualityMode.STUDIO: 12.0    # 12x audio duration (very slow on CPU)
            }
        
        base_time = audio_duration * ratios[self.config.quality]
        
        # Add overhead for TTA shifts in studio mode
        params = self._get_separation_params()
        shifts = params.get('shifts', 1)
        if shifts > 1:
            base_time *= (1 + (shifts - 1) * 0.3)  # Each shift adds ~30%
        
        # Add overhead for per-instrument mode
        if self.config.mode == SeparationMode.PER_INSTRUMENT:
            base_time *= 1.5
        
        # Analysis time
        analysis_time = min(30, audio_duration * 0.05)
        
        total_time = base_time + analysis_time
        
        return {
            'separation_seconds': round(base_time, 1),
            'analysis_seconds': round(analysis_time, 1),
            'total_seconds': round(total_time, 1),
            'separation_formatted': self._format_time(base_time),
            'analysis_formatted': self._format_time(analysis_time),
            'total_formatted': self._format_time(total_time),
            'quality': self.config.quality.value,
            'device': str(self.device),
            'shifts': shifts
        }
    
    def _format_time(self, seconds: float) -> str:
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


def create_separator(
    quality: str = "balanced",
    mode: str = "grouped",
    use_gpu: bool = True,
    target_instruments: Optional[List[str]] = None
) -> HarmonixSeparator:
    """
    Factory function to create configured separator
    
    Args:
        quality: Quality mode (fast/balanced/studio)
        mode: Separation mode (grouped/per_instrument)
        use_gpu: Enable GPU acceleration
        target_instruments: Specific instruments to extract
        
    Returns:
        Configured HarmonixSeparator instance
    """
    config = SeparationConfig(
        quality=QualityMode(quality),
        mode=SeparationMode(mode),
        use_gpu=use_gpu,
        target_instruments=target_instruments
    )
    
    return HarmonixSeparator(config)
