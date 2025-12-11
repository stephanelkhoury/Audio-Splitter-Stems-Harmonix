"""
Harmonix Audio Stem Separator
Core separation engine using Demucs v4 with GPU acceleration
"""

import torch
import torchaudio
import numpy as np
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


@dataclass
class SeparationConfig:
    """Configuration for separation process"""
    quality: QualityMode = QualityMode.BALANCED
    mode: SeparationMode = SeparationMode.GROUPED
    target_instruments: Optional[List[str]] = None
    use_gpu: bool = True
    sample_rate: int = 44100
    segment_duration: Optional[int] = None  # Auto-segment for long files
    overlap: float = 0.25  # Overlap ratio for segments


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
        """Setup computation device (GPU/CPU)"""
        if self.config.use_gpu and torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info(f"GPU detected: {torch.cuda.get_device_name(0)}")
        else:
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
            QualityMode.FAST: "htdemucs_ft",
            QualityMode.BALANCED: "htdemucs",
            QualityMode.STUDIO: "htdemucs_6s"  # 6-source model for better quality
        }
        return quality_map[self.config.quality]
    
    def _load_refinement_models(self):
        """Load specialized models for instrument-level separation"""
        # Placeholder for future instrument-specific models
        # Could include guitar/piano/strings specialized models
        logger.info("Refinement models will be loaded in Phase 2")
        self.models['refinement'] = {}
    
    def separate(
        self, 
        audio_path: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None
    ) -> Dict[str, StemOutput]:
        """
        Separate audio file into stems
        
        Args:
            audio_path: Path to input audio file
            output_dir: Optional directory to save stems
            
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
        
        # Refine to instrument level if needed
        if self.config.mode == SeparationMode.PER_INSTRUMENT:
            stems = self._refine_instruments(stems)
        
        # Save stems if output directory specified
        if output_dir:
            self._save_stems(stems, output_dir, audio_path.stem)
        
        logger.info(f"Separation complete: {len(stems)} stems extracted")
        return stems
    
    def _load_audio(self, path: Path) -> Tuple[torch.Tensor, int]:
        """
        Load and preprocess audio file
        
        Args:
            path: Audio file path
            
        Returns:
            Tuple of (audio tensor, sample rate)
        """
        try:
            # Load audio with torchaudio
            audio, sr = torchaudio.load(str(path))
            
            # Resample if needed
            if sr != self.config.sample_rate:
                resampler = torchaudio.transforms.Resample(
                    sr, self.config.sample_rate
                )
                audio = resampler(audio)
                sr = self.config.sample_rate
            
            # Convert to stereo if mono
            if audio.shape[0] == 1:
                audio = audio.repeat(2, 1)
            
            # Move to device
            audio = audio.to(self.device)
            
            logger.info(
                f"Audio loaded: {audio.shape[1]/sr:.2f}s, "
                f"{sr}Hz, {audio.shape[0]} channels"
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
        logger.info("Running primary separation (4-stem)")
        
        with torch.no_grad():
            # Add batch dimension
            audio_batch = audio.unsqueeze(0)
            
            # Apply model
            sources = self._apply_model(
                self.models['primary'],
                audio_batch,
                device=self.device,
                segment=self.config.segment_duration,
                overlap=self.config.overlap
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
                    'quality': self.config.quality.value
                }
            )
            
            logger.debug(f"Extracted stem: {name} - {audio_np.shape}")
        
        return stems
    
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
            base_name: Base filename for stems
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for name, stem in stems.items():
            # Save as WAV
            wav_path = output_dir / f"{base_name}_{name}.wav"
            
            # Convert to tensor
            audio_tensor = torch.from_numpy(stem.audio).float()
            
            # Save
            torchaudio.save(
                str(wav_path),
                audio_tensor,
                stem.sample_rate,
                encoding="PCM_S",
                bits_per_sample=16
            )
            
            logger.debug(f"Saved: {wav_path}")
        
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
    ) -> float:
        """
        Estimate processing time for given audio duration
        
        Args:
            audio_duration: Duration in seconds
            
        Returns:
            Estimated processing time in seconds
        """
        # Rough estimates based on quality and device
        if self.device.type == 'cuda':
            ratios = {
                QualityMode.FAST: 0.3,
                QualityMode.BALANCED: 0.5,
                QualityMode.STUDIO: 0.8
            }
        else:
            ratios = {
                QualityMode.FAST: 2.0,
                QualityMode.BALANCED: 3.5,
                QualityMode.STUDIO: 5.0
            }
        
        base_time = audio_duration * ratios[self.config.quality]
        
        # Add overhead for per-instrument mode
        if self.config.mode == SeparationMode.PER_INSTRUMENT:
            base_time *= 1.5
        
        return base_time


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
