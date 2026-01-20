# ⚙️ Configuration Guide

**Complete configuration reference for Harmonix Audio Splitter**

---

## Table of Contents

- [Configuration Methods](#configuration-methods)
- [Environment Variables](#environment-variables)
- [YAML Configuration](#yaml-configuration)
- [Python Settings](#python-settings)
- [Configuration Precedence](#configuration-precedence)
- [Common Configurations](#common-configurations)

---

## Configuration Methods

Harmonix supports multiple configuration methods:

1. **Environment Variables** - Best for deployment/containers
2. **YAML File** - Best for project settings
3. **Python Code** - Best for programmatic control
4. **.env File** - Best for local development

---

## Environment Variables

### Server Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `ENV` | `development` | Environment (development/production) |
| `DEBUG` | `false` | Enable debug mode |
| `SECRET_KEY` | `dev-secret-key` | Session secret key |

### Processing Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `HARMONIX_USE_GPU` | `true` | Enable GPU acceleration |
| `HARMONIX_DEFAULT_QUALITY` | `balanced` | Default quality mode |
| `HARMONIX_DEFAULT_MODE` | `grouped` | Default separation mode |
| `SAMPLE_RATE` | `44100` | Target sample rate |

### Path Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `HARMONIX_UPLOAD_DIR` | `data/uploads` | Upload directory |
| `HARMONIX_OUTPUT_DIR` | `data/outputs` | Output directory |
| `HARMONIX_TEMP_DIR` | `data/temp` | Temporary files |
| `DEMUCS_CACHE_DIR` | `models/weights` | Model cache |

### Limits

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_FILE_SIZE_MB` | `500` | Maximum file size (MB) |
| `MAX_DURATION` | `600` | Maximum duration (seconds) |

### GPU Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `CUDA_VISIBLE_DEVICES` | *(all)* | Visible CUDA devices |
| `TORCH_DEVICE` | `auto` | Torch device (auto/cuda/cpu) |

### Storage Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `STORAGE_TYPE` | `local` | Storage type (local/s3) |
| `S3_BUCKET_NAME` | | S3 bucket name |
| `AWS_ACCESS_KEY_ID` | | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | | AWS secret key |
| `AWS_REGION` | `us-east-1` | AWS region |

### Redis/Cache Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_PASSWORD` | | Redis password |

### Example .env File

```bash
# .env file
ENV=production
DEBUG=false
SECRET_KEY=your-secure-secret-key-here

# Processing
HARMONIX_USE_GPU=true
HARMONIX_DEFAULT_QUALITY=balanced
SAMPLE_RATE=44100

# Paths
HARMONIX_UPLOAD_DIR=./data/uploads
HARMONIX_OUTPUT_DIR=./data/outputs
DEMUCS_CACHE_DIR=./models/weights

# Limits
MAX_FILE_SIZE_MB=500
MAX_DURATION=600

# Storage (for production with S3)
STORAGE_TYPE=s3
S3_BUCKET_NAME=my-harmonix-bucket
AWS_ACCESS_KEY_ID=AKIAXXXXXXXX
AWS_SECRET_ACCESS_KEY=xxxxxxxx
AWS_REGION=us-east-1

# Redis (for production job queue)
REDIS_HOST=redis.example.com
REDIS_PORT=6379
REDIS_PASSWORD=redis-password
```

---

## YAML Configuration

### File Location

Default: `config/config.yaml`

### Complete Configuration File

```yaml
# config/config.yaml

# Server settings
server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  reload: false
  log_level: "info"

# Processing settings
processing:
  max_file_size_mb: 500
  max_duration_seconds: 1200
  temp_dir: "data/temp"
  output_dir: "data/outputs"
  cleanup_after_hours: 24
  
  # Quality modes
  quality_modes:
    draft:
      model: "htdemucs"
      shifts: 0
      overlap: 0.05
      split: true
    fast:
      model: "htdemucs"
      shifts: 0
      overlap: 0.1
      split: true
    balanced:
      model: "htdemucs_ft"
      shifts: 1
      overlap: 0.25
      split: true
    studio:
      model: "htdemucs_6s"
      shifts: 5
      overlap: 0.5
      split: true
  
  # Default settings
  default_mode: "balanced"
  default_sample_rate: 44100
  default_format: "mp3"
  export_mp3: true
  mp3_bitrate: 320

# Instrument detection
instrument_detection:
  enabled: true
  
  # Confidence thresholds (0-1)
  thresholds:
    vocals: 0.5
    drums: 0.5
    bass: 0.5
    guitar: 0.5
    piano: 0.5
    strings: 0.6
    synth: 0.7
    brass: 0.65
    woodwinds: 0.65
    fx: 0.7
  
  # Processing modes
  modes:
    default: "grouped"
    advanced: "per_instrument"
  
  # Supported instruments
  supported_instruments:
    - vocals
    - drums
    - bass
    - guitar
    - piano
    - strings
    - synth
    - brass
    - woodwinds
    - fx

# Model settings
models:
  demucs:
    device: "auto"  # auto, cuda, cpu, mps
    num_workers: 4
    cache_dir: "models/weights"
    
  instrument_detector:
    model_path: "models/instrument_classifier.h5"
    input_duration: 30
    hop_length: 512

# Storage settings
storage:
  type: "local"  # local, s3
  
  local:
    base_path: "data"
  
  s3:
    bucket_name: "harmonix-stems"
    region: "us-east-1"
    endpoint_url: null
    presigned_url_expiry: 3600

# Redis/Celery (for async processing)
redis:
  host: "localhost"
  port: 6379
  db: 0
  password: null

# Logging
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/harmonix.log"
  max_size: 10485760  # 10MB
  backup_count: 5

# Monitoring
monitoring:
  enabled: false
  prometheus_port: 9090
  health_check_interval: 30
```

---

## Python Settings

### Settings Class

```python
from harmonix_splitter.config.settings import Settings

# Load settings
settings = Settings()

# Access settings
print(settings.use_gpu)
print(settings.output_dir)
print(settings.max_duration)
```

### Settings Properties

```python
class Settings(BaseSettings):
    """Main application settings."""
    
    # Environment
    env: str = "development"
    debug: bool = False
    secret_key: str = "dev-secret-key"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Processing
    max_file_size_mb: int = 500
    max_duration: int = 600
    sample_rate: int = 44100
    temp_dir: str = "data/temp"
    output_dir: str = "data/outputs"
    
    # Detection thresholds
    detection_thresholds: Dict[str, float] = {
        "drums": 0.5,
        "bass": 0.5,
        "vocals": 0.5,
        "guitar": 0.5,
        "piano": 0.5,
        "other": 0.5
    }
    
    # GPU
    use_gpu: bool = True
    cuda_visible_devices: Optional[str] = None
    torch_device: str = "auto"
```

### Helper Methods

```python
settings = Settings()

# Get directories (creates if needed)
temp_dir = settings.get_temp_dir()      # Returns Path
output_dir = settings.get_output_dir()  # Returns Path
models_dir = settings.get_models_dir()  # Returns Path

# Load YAML config
yaml_config = settings.load_yaml_config()
```

### Creating Custom Settings

```python
from harmonix_splitter.config.settings import Settings

# Custom settings instance
custom_settings = Settings(
    use_gpu=False,
    max_duration=1200,
    output_dir="./custom_output"
)

# Use with orchestrator
from harmonix_splitter import create_orchestrator
orchestrator = create_orchestrator(settings=custom_settings)
```

---

## Configuration Precedence

Settings are loaded in this order (later overrides earlier):

1. **Default values** (in code)
2. **YAML file** (`config/config.yaml`)
3. **.env file** (in project root)
4. **Environment variables**
5. **Explicit code parameters**

### Example

```python
# 1. Default: use_gpu = True
# 2. YAML: (not set)
# 3. .env: HARMONIX_USE_GPU=false  ← This takes effect
# 4. Env var: (not set)
# 5. Code: (not set)

# Final value: use_gpu = False
```

---

## Common Configurations

### Development Configuration

```yaml
# config/config.yaml (development)
server:
  host: "127.0.0.1"
  port: 5000
  reload: true
  log_level: "debug"

processing:
  quality_modes:
    default: fast
  temp_dir: "data/temp"
  output_dir: "data/outputs"
  cleanup_after_hours: 1
```

```bash
# .env (development)
ENV=development
DEBUG=true
HARMONIX_USE_GPU=true
```

### Production Configuration

```yaml
# config/config.yaml (production)
server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  reload: false
  log_level: "warning"

processing:
  quality_modes:
    default: balanced
  cleanup_after_hours: 24

storage:
  type: "s3"
  s3:
    bucket_name: "harmonix-production"
    region: "us-east-1"

redis:
  host: "redis.internal"
  port: 6379
```

```bash
# .env (production)
ENV=production
DEBUG=false
SECRET_KEY=super-secure-production-key-12345

STORAGE_TYPE=s3
S3_BUCKET_NAME=harmonix-production
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxx
AWS_REGION=us-east-1

REDIS_HOST=redis.internal
REDIS_PASSWORD=redis-secure-password
```

### Docker Configuration

```yaml
# docker-compose.yml environment
environment:
  - ENV=production
  - HOST=0.0.0.0
  - PORT=8000
  - HARMONIX_USE_GPU=true
  - CUDA_VISIBLE_DEVICES=0
  - STORAGE_TYPE=local
  - REDIS_HOST=redis
```

### CPU-Only Configuration

```bash
# .env (CPU-only)
HARMONIX_USE_GPU=false
TORCH_DEVICE=cpu
CUDA_VISIBLE_DEVICES=""
```

### High-Performance Configuration

```yaml
# config/config.yaml (high-performance)
processing:
  quality_modes:
    fast:
      shifts: 0
      overlap: 0.1
    balanced:
      shifts: 2
      overlap: 0.3
    studio:
      shifts: 10
      overlap: 0.5

models:
  demucs:
    device: "cuda"
    num_workers: 8
```

---

## Validation

### Validate Configuration

```python
from harmonix_splitter.config.settings import Settings
from pydantic import ValidationError

try:
    settings = Settings()
    print("Configuration valid!")
except ValidationError as e:
    print(f"Configuration error: {e}")
```

### Required Settings for Production

Ensure these are set in production:

- [ ] `SECRET_KEY` - Unique secure key
- [ ] `ENV=production`
- [ ] `DEBUG=false`
- [ ] Storage configuration (local or S3)
- [ ] Redis configuration (if using job queue)

---

## Related Documentation

- [Installation](./INSTALLATION.md) - Setup guide
- [Deployment](./DEPLOYMENT.md) - Production deployment
- [Docker](./DOCKER.md) - Container configuration

---

*Configuration documentation last updated: January 2026*
