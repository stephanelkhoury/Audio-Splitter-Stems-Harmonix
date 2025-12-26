"""Configuration management for Harmonix Audio Splitter."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class ServerSettings(BaseSettings):
    """Server configuration."""
    
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload: bool = False
    log_level: str = "info"


class ProcessingSettings(BaseSettings):
    """Processing configuration."""
    
    max_file_size_mb: int = 500
    max_duration_seconds: int = 600
    temp_dir: str = "data/temp"
    output_dir: str = "data/outputs"
    cleanup_after_hours: int = 24
    default_mode: str = "fast"
    default_sample_rate: int = 44100
    default_format: str = "wav"
    export_mp3: bool = True
    mp3_bitrate: int = 320


class Settings(BaseSettings):
    """Main application settings."""
    
    # Environment
    env: str = Field(default="development", alias="ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    secret_key: str = Field(default="dev-secret-key", alias="SECRET_KEY")
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent.parent
    config_file: Path = base_dir / "config" / "config.yaml"
    
    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    
    # Processing
    max_file_size_mb: int = Field(default=500, alias="MAX_FILE_SIZE_MB")
    max_duration: int = Field(default=600, alias="MAX_DURATION")
    sample_rate: int = Field(default=44100, alias="SAMPLE_RATE")
    temp_dir: str = Field(default="data/temp", alias="TEMP_DIR")
    output_dir: str = Field(default="data/outputs", alias="OUTPUT_DIR")
    
    # Detection
    detection_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "drums": 0.5,
            "bass": 0.5,
            "vocals": 0.5,
            "guitar": 0.5,
            "piano": 0.5,
            "other": 0.5
        }
    )
    
    # GPU
    use_gpu: bool = Field(default=True, alias="USE_GPU")
    cuda_visible_devices: Optional[str] = Field(default=None, alias="CUDA_VISIBLE_DEVICES")
    torch_device: str = Field(default="auto", alias="TORCH_DEVICE")
    
    # Redis
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    
    # Storage
    storage_type: str = "local"
    aws_access_key_id: Optional[str] = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    s3_bucket_name: Optional[str] = Field(default=None, alias="S3_BUCKET_NAME")
    
    # Sentry
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")
    sentry_environment: str = Field(default="development", alias="SENTRY_ENVIRONMENT")
    
    # Model paths
    demucs_cache_dir: str = Field(default="models/weights", alias="DEMUCS_CACHE_DIR")
    instrument_detector_model: str = Field(
        default="models/instrument_classifier.h5",
        alias="INSTRUMENT_DETECTOR_MODEL"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def load_yaml_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                return yaml.safe_load(f)
        return {}
    
    def get_temp_dir(self) -> Path:
        """Get temp directory path and ensure it exists."""
        path = self.base_dir / self.temp_dir
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_output_dir(self) -> Path:
        """Get output directory path and ensure it exists."""
        path = self.base_dir / self.output_dir
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_models_dir(self) -> Path:
        """Get models directory path and ensure it exists."""
        path = self.base_dir / self.demucs_cache_dir
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
