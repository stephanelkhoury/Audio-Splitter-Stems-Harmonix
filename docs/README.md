# 📚 Harmonix Documentation Index

**Complete Documentation for Harmonix Audio Splitter**

**Last Updated:** January 2026

---

## 🚀 Getting Started

| Document | Description |
|----------|-------------|
| [Installation](./INSTALLATION.md) | Complete installation guide for all platforms |
| [Quickstart](./QUICKSTART.md) | 5-minute getting started guide |
| [Configuration](./CONFIGURATION.md) | Configuration options and settings |

---

## 🎵 Core Features

| Document | Description |
|----------|-------------|
| [Stem Separation](./STEM_SEPARATION.md) | How audio stem separation works |
| [Quality Modes](./QUALITY_MODES.md) | Quality vs speed tradeoffs |
| [Instrument Detection](./INSTRUMENT_DETECTION.md) | AI-powered instrument detection |
| [Music Analysis](./MUSIC_ANALYSIS.md) | BPM, key detection, Camelot wheel |
| [Lyrics Extraction](./LYRICS_EXTRACTION.md) | Whisper-powered lyrics extraction |
| [Audio Processing](./AUDIO_PROCESSING.md) | Pitch shifting and audio manipulation |

---

## 🖥️ Interfaces

| Document | Description |
|----------|-------------|
| [Dashboard](./DASHBOARD.md) | Web dashboard user guide |
| [CLI Guide](./CLI_GUIDE.md) | Command-line interface reference |
| [API Reference](./API_REFERENCE.md) | REST API endpoints and usage |

---

## 👥 Users & Integration

| Document | Description |
|----------|-------------|
| [User Management](./USER_MANAGEMENT.md) | Authentication, plans, profiles |
| [YouTube Integration](./YOUTUBE_INTEGRATION.md) | Processing YouTube URLs |
| [Supported Formats](./SUPPORTED_FORMATS.md) | Input/output audio formats |

---

## 🏗️ Technical Documentation

| Document | Description |
|----------|-------------|
| [Architecture](./ARCHITECTURE.md) | System architecture deep dive |
| [Developer Guide](./DEVELOPER_GUIDE.md) | Contributing and development |
| [Design System](./DESIGN_SYSTEM.md) | UI/UX design system |

---

## 🚢 Deployment

| Document | Description |
|----------|-------------|
| [Docker](./DOCKER.md) | Docker and container deployment |
| [Deployment](../DEPLOYMENT.md) | Production deployment guide |
| [Troubleshooting](./TROUBLESHOOTING.md) | Common issues and solutions |

---

## 📋 Document Overview

### Getting Started Guides

#### 📦 [Installation](./INSTALLATION.md)
Complete installation guide covering:
- System requirements (Python, FFmpeg, GPU)
- Installation methods (pip, source, Docker)
- GPU setup (NVIDIA CUDA, Apple MPS)
- Verification and first run

#### ⚡ [Quickstart](./QUICKSTART.md)
Get running in 5 minutes:
- Quick install commands
- First stem separation
- Dashboard overview
- Next steps

#### ⚙️ [Configuration](./CONFIGURATION.md)
All configuration options:
- Environment variables
- YAML configuration
- Pydantic settings
- Runtime options

---

### Core Feature Documentation

#### 🎚️ [Stem Separation](./STEM_SEPARATION.md)
Deep dive into stem separation:
- Demucs model overview
- Separation modes (grouped, per-instrument, karaoke)
- Quality modes explained
- Output organization

#### 🎯 [Quality Modes](./QUALITY_MODES.md)
Understanding quality/speed tradeoffs:
- Draft, Fast, Balanced, Studio modes
- When to use each mode
- Technical parameters
- Benchmarks

#### 🎸 [Instrument Detection](./INSTRUMENT_DETECTION.md)
AI-powered detection system:
- Supported instruments
- Detection methods (ML, heuristic)
- Confidence scores
- API usage

#### 🎵 [Music Analysis](./MUSIC_ANALYSIS.md)
BPM and key detection:
- Tempo analysis
- Key detection (Krumhansl-Kessler)
- Camelot wheel for DJs
- API integration

#### 🎤 [Lyrics Extraction](./LYRICS_EXTRACTION.md)
Whisper-powered transcription:
- Multi-language support (99+ languages)
- Export formats (LRC, SRT, JSON)
- Synchronization options
- Accuracy optimization

#### 🔧 [Audio Processing](./AUDIO_PROCESSING.md)
Audio manipulation features:
- Pitch shifting with formant preservation
- Time stretching
- Audio normalization
- Format conversion

---

### Interface Documentation

#### 🌐 [Dashboard](./DASHBOARD.md)
Web dashboard guide:
- Interface overview
- Upload and processing
- Playback controls
- User features

#### 💻 [CLI Guide](./CLI_GUIDE.md)
Command-line reference:
- All commands and options
- Examples and workflows
- Batch processing
- Scripting

#### 🔌 [API Reference](./API_REFERENCE.md)
REST API documentation:
- Authentication
- Processing endpoints
- Analysis endpoints
- Code examples

---

### User & Integration Docs

#### 👤 [User Management](./USER_MANAGEMENT.md)
Authentication system:
- Registration and login
- Plan tiers (Free, Creator, Studio)
- Profile management
- Activity tracking

#### 📺 [YouTube Integration](./YOUTUBE_INTEGRATION.md)
YouTube URL processing:
- Supported URL formats
- Shared library system
- Cookies configuration
- Rate limiting

#### 📁 [Supported Formats](./SUPPORTED_FORMATS.md)
Audio format guide:
- Input formats (MP3, WAV, FLAC, etc.)
- Output formats and quality
- Sample rate and bit depth
- Format conversion

---

### Technical Documentation

#### 🏛️ [Architecture](./ARCHITECTURE.md)
System architecture:
- Module structure
- Data flow
- Processing pipeline
- Dependency graph

#### 👨‍💻 [Developer Guide](./DEVELOPER_GUIDE.md)
For contributors:
- Development setup
- Code architecture
- Adding features
- Testing guidelines

#### 🎨 [Design System](./DESIGN_SYSTEM.md)
UI/UX documentation:
- Color palette
- Typography
- Components
- Accessibility

---

### Deployment & Operations

#### 🐳 [Docker](./DOCKER.md)
Container deployment:
- Docker Compose options
- GPU support
- Production configuration
- Troubleshooting

#### 🚨 [Troubleshooting](./TROUBLESHOOTING.md)
Common issues:
- Installation problems
- GPU/CUDA issues
- Audio processing errors
- Memory issues

---

## Other Project Documentation

| File | Description |
|------|-------------|
| [README.md](../README.md) | Project introduction and quick start |
| [CHANGELOG.md](../CHANGELOG.md) | Version history and changes |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Contribution guidelines |
| [LICENSE](../LICENSE) | MIT License |
| [DASHBOARD.md](../DASHBOARD.md) | Dashboard-specific documentation |
| [DAW_WORKSPACE_SPEC.md](../DAW_WORKSPACE_SPEC.md) | DAW integration specifications |
| [PROJECT_SUMMARY.md](../PROJECT_SUMMARY.md) | Project summary |

---

## Version Information

| Version | Date | Notes |
|---------|------|-------|
| 1.1.0 | December 30, 2025 | Documentation overhaul, design system |
| 1.0.0 | December 10, 2025 | Initial release |

---

## Getting Help

- **Issues:** [GitHub Issues](https://github.com/yourusername/Audio-Splitter-Stems-Harmonix/issues)
- **Email:** support@harmonix.app

---

**© 2025 Harmonix. All rights reserved.**
