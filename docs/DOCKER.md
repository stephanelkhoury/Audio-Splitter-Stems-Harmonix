# 🐳 Docker Guide

**Complete guide to running Harmonix in containers**

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Docker Compose Options](#docker-compose-options)
- [Dockerfile Variants](#dockerfile-variants)
- [Configuration](#configuration)
- [GPU Support](#gpu-support)
- [Volumes and Data](#volumes-and-data)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

---

## Overview

Harmonix provides multiple Docker configurations:

| Configuration | Description | GPU Support |
|---------------|-------------|-------------|
| `docker-compose.yml` | Full version with GPU | ✅ NVIDIA |
| `docker-compose.cpu.yml` | CPU-only version | ❌ |
| `docker-compose.slim.yml` | Minimal version | ❌ |

---

## Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose v2.0+
- NVIDIA Container Toolkit (for GPU)

### Start with GPU (Recommended)

```bash
# Clone repository
git clone https://github.com/yourusername/harmonix.git
cd harmonix

# Start with GPU support
docker compose up -d

# View logs
docker compose logs -f
```

### Start CPU-Only

```bash
# Use CPU-only configuration
docker compose -f docker-compose.cpu.yml up -d
```

### Start Slim Version

```bash
# Minimal installation
docker compose -f docker-compose.slim.yml up -d
```

### Access the Application

- **Dashboard:** http://localhost:5000
- **API:** http://localhost:8000

---

## Docker Compose Options

### Full Version (docker-compose.yml)

```yaml
version: '3.8'

services:
  harmonix:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "5000:5000"   # Dashboard
      - "8000:8000"   # API
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./models:/app/models
    environment:
      - HARMONIX_DEVICE=cuda
      - HARMONIX_QUALITY_MODE=studio
      - SECRET_KEY=${SECRET_KEY:-change-me}
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
```

### CPU Version (docker-compose.cpu.yml)

```yaml
version: '3.8'

services:
  harmonix:
    build:
      context: .
      dockerfile: Dockerfile.cpu
    ports:
      - "5000:5000"
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    environment:
      - HARMONIX_DEVICE=cpu
      - HARMONIX_QUALITY_MODE=balanced
    restart: unless-stopped
```

### Slim Version (docker-compose.slim.yml)

```yaml
version: '3.8'

services:
  harmonix:
    build:
      context: .
      dockerfile: Dockerfile.slim
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
    environment:
      - HARMONIX_DEVICE=cpu
      - HARMONIX_QUALITY_MODE=fast
    restart: unless-stopped
```

---

## Dockerfile Variants

### Dockerfile (Full GPU)

```dockerfile
# Full version with NVIDIA GPU support
FROM nvidia/cuda:11.8-cudnn8-runtime-ubuntu22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    libsndfile1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose ports
EXPOSE 5000 8000

# Run application
CMD ["python3", "-m", "harmonix_splitter.dashboard"]
```

### Dockerfile.cpu (CPU Only)

```dockerfile
# CPU-only version
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000 8000

CMD ["python", "-m", "harmonix_splitter.dashboard"]
```

### Dockerfile.slim (Minimal)

```dockerfile
# Minimal version for basic functionality
FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-lite.txt .
RUN pip install --no-cache-dir -r requirements-lite.txt

COPY src/ ./src/
COPY config/ ./config/

EXPOSE 5000

CMD ["python", "-m", "harmonix_splitter.dashboard"]
```

---

## Configuration

### Environment Variables

```yaml
# docker-compose.yml environment section
environment:
  # Core settings
  - HARMONIX_DEVICE=cuda           # cuda, mps, cpu
  - HARMONIX_QUALITY_MODE=studio   # fast, balanced, studio
  - HARMONIX_OUTPUT_FORMAT=mp3     # mp3, wav, flac
  
  # Security
  - SECRET_KEY=your-secret-key-here
  
  # Paths
  - HARMONIX_DATA_DIR=/app/data
  - HARMONIX_OUTPUT_DIR=/app/data/outputs
  - HARMONIX_MODELS_DIR=/app/models
  
  # Performance
  - HARMONIX_MAX_WORKERS=4
  - HARMONIX_BATCH_SIZE=1
  
  # Logging
  - HARMONIX_LOG_LEVEL=INFO
```

### Using .env File

Create `.env` file:
```env
SECRET_KEY=my-super-secret-key
HARMONIX_DEVICE=cuda
HARMONIX_QUALITY_MODE=studio
```

Reference in docker-compose:
```yaml
env_file:
  - .env
```

### Config Volume

Mount configuration:
```yaml
volumes:
  - ./config:/app/config:ro  # Read-only config
```

---

## GPU Support

### NVIDIA GPU Setup

1. **Install NVIDIA Drivers**
   ```bash
   # Ubuntu
   sudo apt-get install nvidia-driver-535
   ```

2. **Install NVIDIA Container Toolkit**
   ```bash
   # Add repository
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
       sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   
   # Install
   sudo apt-get update
   sudo apt-get install -y nvidia-container-toolkit
   
   # Restart Docker
   sudo systemctl restart docker
   ```

3. **Verify GPU Access**
   ```bash
   docker run --rm --gpus all nvidia/cuda:11.8-base nvidia-smi
   ```

### GPU Compose Configuration

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1              # Number of GPUs
          capabilities: [gpu]
          # Or specific GPU:
          # device_ids: ['0']
```

### Multiple GPUs

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all            # Use all GPUs
          capabilities: [gpu]
```

---

## Volumes and Data

### Recommended Volume Structure

```yaml
volumes:
  # Persistent data
  - harmonix_data:/app/data
  
  # Pre-downloaded models (optional)
  - harmonix_models:/app/models
  
  # Configuration
  - ./config:/app/config:ro
  
  # Logs
  - ./logs:/app/logs

volumes:
  harmonix_data:
  harmonix_models:
```

### Data Persistence

```
/app/data/
├── uploads/      # Uploaded files (ephemeral)
├── outputs/      # Processed results (keep)
├── library/      # Shared library (keep)
├── temp/         # Temporary files (ephemeral)
├── users.json    # User database (keep)
└── activities.json
```

### Backup Strategy

```bash
# Backup data volume
docker run --rm \
  -v harmonix_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/harmonix-data-$(date +%Y%m%d).tar.gz /data

# Restore
docker run --rm \
  -v harmonix_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/harmonix-data-20251230.tar.gz -C /
```

---

## Production Deployment

### Production Compose File

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  harmonix:
    image: harmonix/audio-splitter:latest
    ports:
      - "127.0.0.1:5000:5000"  # Local only
    volumes:
      - harmonix_data:/app/data
      - harmonix_models:/app/models
    environment:
      - HARMONIX_DEVICE=cuda
      - SECRET_KEY=${SECRET_KEY}
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
        limits:
          memory: 16G
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - harmonix
    restart: always

volumes:
  harmonix_data:
  harmonix_models:
```

### Nginx Reverse Proxy

```nginx
# nginx.conf
server {
    listen 80;
    server_name harmonix.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name harmonix.example.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    location / {
        proxy_pass http://harmonix:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Large file uploads
        client_max_body_size 500M;
    }
    
    location /api {
        proxy_pass http://harmonix:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Health Checks

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s  # Allow model loading time
```

---

## Build and Deploy

### Building Images

```bash
# Build default image
docker compose build

# Build with no cache
docker compose build --no-cache

# Build specific service
docker compose build harmonix
```

### Pushing to Registry

```bash
# Tag image
docker tag harmonix_harmonix:latest your-registry/harmonix:v1.0.0

# Push
docker push your-registry/harmonix:v1.0.0
```

### Multi-Platform Build

```bash
# Build for multiple architectures
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t your-registry/harmonix:latest \
  --push .
```

---

## Troubleshooting

### Common Issues

**Container won't start:**
```bash
# Check logs
docker compose logs harmonix

# Check container status
docker compose ps
```

**GPU not detected:**
```bash
# Verify GPU is visible
docker run --rm --gpus all nvidia/cuda:11.8-base nvidia-smi

# Check container has GPU access
docker compose exec harmonix nvidia-smi
```

**Out of memory:**
```bash
# Reduce batch size
environment:
  - HARMONIX_BATCH_SIZE=1
  - HARMONIX_QUALITY_MODE=balanced

# Limit memory
deploy:
  resources:
    limits:
      memory: 8G
```

**Permission issues:**
```bash
# Fix ownership
sudo chown -R 1000:1000 ./data

# Or run as current user
user: "${UID}:${GID}"
```

### Debugging

```bash
# Shell into container
docker compose exec harmonix bash

# Run single command
docker compose exec harmonix python -c "import torch; print(torch.cuda.is_available())"

# View real-time logs
docker compose logs -f harmonix
```

---

## Cloud Deployments

### Docker Images for Cloud

| Platform | Dockerfile |
|----------|------------|
| Railway | `Dockerfile.railway` |
| RunPod | `Dockerfile.runpod` |
| Generic Cloud | `Dockerfile.cpu` |

### Railway Deployment

```bash
# railway.json configures the deployment
railway up
```

### RunPod Deployment

```python
# runpod_handler.py provides serverless handler
# Deploy via RunPod dashboard
```

---

## Related Documentation

- [Installation](./INSTALLATION.md) - Local setup
- [Deployment](./DEPLOYMENT.md) - Production guide
- [Configuration](./CONFIGURATION.md) - Settings
- [Troubleshooting](./TROUBLESHOOTING.md) - Common issues

---

*Docker documentation last updated: January 2026*
