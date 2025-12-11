"""
Tests for Harmonix Separator
"""

import pytest
import torch
import numpy as np
from pathlib import Path

from harmonix_splitter.core.separator import (
    HarmonixSeparator,
    SeparationConfig,
    QualityMode,
    SeparationMode,
    create_separator
)


class TestSeparationConfig:
    """Test separation configuration"""
    
    def test_default_config(self):
        config = SeparationConfig()
        assert config.quality == QualityMode.BALANCED
        assert config.mode == SeparationMode.GROUPED
        assert config.use_gpu == True
        assert config.sample_rate == 44100
    
    def test_custom_config(self):
        config = SeparationConfig(
            quality=QualityMode.STUDIO,
            mode=SeparationMode.PER_INSTRUMENT,
            use_gpu=False,
            target_instruments=["vocals", "drums"]
        )
        assert config.quality == QualityMode.STUDIO
        assert config.mode == SeparationMode.PER_INSTRUMENT
        assert config.use_gpu == False
        assert config.target_instruments == ["vocals", "drums"]


class TestHarmonixSeparator:
    """Test main separator class"""
    
    @pytest.fixture
    def separator(self):
        """Create test separator with CPU"""
        config = SeparationConfig(use_gpu=False, quality=QualityMode.FAST)
        return HarmonixSeparator(config)
    
    def test_initialization(self, separator):
        """Test separator initialization"""
        assert separator.device.type == "cpu"
        assert separator.config.quality == QualityMode.FAST
        assert "primary" in separator.models
    
    def test_device_setup_cpu(self):
        """Test CPU device setup"""
        config = SeparationConfig(use_gpu=False)
        sep = HarmonixSeparator(config)
        assert sep.device.type == "cpu"
    
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_device_setup_gpu(self):
        """Test GPU device setup"""
        config = SeparationConfig(use_gpu=True)
        sep = HarmonixSeparator(config)
        assert sep.device.type == "cuda"
    
    def test_model_name_selection(self, separator):
        """Test model name selection based on quality"""
        assert separator._get_model_name() == "htdemucs_ft"
        
        separator.config.quality = QualityMode.STUDIO
        assert separator._get_model_name() == "htdemucs_6s"
    
    def test_get_available_models(self, separator):
        """Test getting available models info"""
        info = separator.get_available_models()
        
        assert "quality_modes" in info
        assert "separation_modes" in info
        assert "core_stems" in info
        assert "fast" in info["quality_modes"]
        assert "vocals" in info["core_stems"]
    
    def test_estimate_processing_time(self, separator):
        """Test processing time estimation"""
        time_estimate = separator.estimate_processing_time(180.0)  # 3 minutes
        
        assert time_estimate > 0
        assert isinstance(time_estimate, float)


class TestFactoryFunction:
    """Test factory function"""
    
    def test_create_separator_defaults(self):
        """Test creating separator with defaults"""
        sep = create_separator()
        
        assert sep.config.quality == QualityMode("balanced")
        assert sep.config.mode == SeparationMode("grouped")
        assert sep.config.use_gpu == True
    
    def test_create_separator_custom(self):
        """Test creating separator with custom settings"""
        sep = create_separator(
            quality="studio",
            mode="per_instrument",
            use_gpu=False,
            target_instruments=["vocals", "guitar"]
        )
        
        assert sep.config.quality == QualityMode.STUDIO
        assert sep.config.mode == SeparationMode.PER_INSTRUMENT
        assert sep.config.use_gpu == False
        assert sep.config.target_instruments == ["vocals", "guitar"]


@pytest.mark.integration
class TestSeparationIntegration:
    """Integration tests requiring audio files"""
    
    @pytest.fixture
    def test_audio_path(self, tmp_path):
        """Create a test audio file"""
        # Generate simple test audio
        import soundfile as sf
        
        sample_rate = 44100
        duration = 5
        t = np.linspace(0, duration, sample_rate * duration)
        audio = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
        
        # Make stereo
        audio_stereo = np.stack([audio, audio])
        
        test_file = tmp_path / "test.wav"
        sf.write(test_file, audio_stereo.T, sample_rate)
        
        return test_file
    
    def test_separation_pipeline(self, test_audio_path, tmp_path):
        """Test complete separation pipeline"""
        separator = create_separator(quality="fast", use_gpu=False)
        
        output_dir = tmp_path / "output"
        stems = separator.separate(test_audio_path, output_dir)
        
        # Check stems were created
        assert len(stems) > 0
        assert "vocals" in stems
        assert "drums" in stems
        
        # Check output files exist
        for stem_name in stems:
            stem_file = output_dir / f"test_{stem_name}.wav"
            assert stem_file.exists()
