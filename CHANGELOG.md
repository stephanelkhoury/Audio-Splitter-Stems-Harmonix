# Changelog

All notable changes to Harmonix Audio Splitter will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2025-12-30

### Added

#### Documentation
- **DOCUMENTATION.md** - Comprehensive project documentation covering all aspects of the application
- **docs/API_REFERENCE.md** - Complete API documentation with all endpoints, request/response formats, and code examples
- **docs/DEVELOPER_GUIDE.md** - Developer guide for contributing to the project
- **docs/DESIGN_SYSTEM.md** - Complete design system documentation with colors, typography, spacing, and components

#### Frontend Improvements
- Unified form input styling across all pages (login, register, account, contact)
- Light theme support for all form elements
- Focus states with purple glow effect on inputs
- Improved textarea and select styling
- Consistent `.form-control` and `.form-input` class support
- Dashboard standalone backup (dashboard_standalone.html)

#### Design System
- CSS custom properties for all design tokens
- Complete color palette documentation
- Typography scale (xs to 4xl)
- Spacing scale based on 4px grid
- Shadow and effect tokens
- Border radius scale
- Animation timing functions and duration tokens

### Changed
- **components.css** - Extended form styling to support both `.form-control` and `.form-input` classes
- **login.html** - Updated form styling with proper background colors and focus states
- **register.html** - Updated form styling to match login page
- **account.html** - Added comprehensive form styles in extra_styles block

### Fixed
- Form input fields appearing transparent/invisible on account and contact pages
- Inconsistent form styling between authentication and account management pages
- Missing light theme support for form inputs
- Placeholder text color visibility issues

---

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
