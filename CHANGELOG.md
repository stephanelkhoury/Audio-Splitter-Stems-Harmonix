# Changelog

All notable changes to Harmonix Audio Splitter will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-10

### Added
- Initial release of Harmonix Audio Splitter
- Core stem separation engine using Demucs v4
- GPU acceleration support with CUDA
- Three quality presets: Fast, Balanced, Studio
- Instrument detection and analysis system
- Multi-label classification for 10+ instruments
- Smart routing and orchestration layer
- REST API with FastAPI
  - POST /api/split - Submit separation jobs
  - GET /api/status/{job_id} - Check job status
  - GET /api/result/{job_id} - Get results
  - POST /api/analysis - Analyze without separation
  - GET /api/models - Available models info
- Command-line interface (CLI)
  - harmonix-split command
  - Batch processing support
  - Analysis-only mode
- Docker support
  - GPU-enabled Dockerfile
  - Docker Compose configuration
  - Redis integration for job queue
  - Optional MinIO for S3-compatible storage
- Audio preprocessing pipeline
  - Format validation
  - ffmpeg integration
  - Automatic resampling
- Configuration system
  - Environment variables support
  - YAML configuration
  - Settings management
- Comprehensive test suite
  - Unit tests
  - Integration tests
  - API tests
- Full documentation
  - README with examples
  - API reference
  - Contributing guidelines
  - Docker deployment guide

### Features
- 4-stem separation (vocals, drums, bass, other)
- Per-instrument separation mode
- Automatic routing based on detection
- WAV and MP3 export
- Async job processing
- Job status tracking
- File validation and limits

### Technical
- Python 3.10+ support
- PyTorch and torchaudio integration
- FastAPI for REST API
- Pydantic for validation
- Comprehensive logging
- Error handling and recovery

## [Unreleased]

### Planned Features
- Trained instrument detection models
- Real-time/streaming separation
- Web UI
- Celery job queue
- S3 storage integration
- Advanced monitoring with Prometheus/Grafana
- Multi-language support
- Plugin architecture
