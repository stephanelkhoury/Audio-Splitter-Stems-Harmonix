# 🚀 Deployment Guide - Harmonix Audio Splitter

This guide covers deploying Harmonix with **minimum cost** and **maximum performance**.

---

## 📊 Quick Comparison

| Platform | GPU? | Monthly Cost | Processing Speed | Setup Time |
|----------|------|--------------|------------------|------------|
| **RunPod Serverless** | ✅ RTX 3090 | $5-30 (pay per use) | ⚡ 30s/song | 30 min |
| **Vast.ai** | ✅ Various | $10-40 | ⚡ 30s/song | 45 min |
| **Hetzner GPU** | ✅ A100 | €1.10/hr | ⚡ 20s/song | 1 hour |
| **Railway** | ❌ CPU | $20-50 | 🐢 5-10min/song | 15 min |
| **DigitalOcean** | ❌ CPU | $24-96 | 🐢 5-10min/song | 30 min |

---

## 🏆 Option 1: RunPod (RECOMMENDED - Best Value)

### Why RunPod?
- **Serverless GPU**: Pay only when processing audio
- **$0.00025/second** on RTX 3090 (~$0.01 per song)
- **Pre-built PyTorch templates**
- **Auto-scaling**: Handles traffic spikes

### Step-by-Step Setup

#### 1. Create RunPod Account
```bash
# Go to https://runpod.io and sign up
# Add $10 credit to start (lasts a long time with serverless)
```

#### 2. Create Template
1. Go to **Templates** → **New Template**
2. Use these settings:
   - **Name**: `harmonix-audio-splitter`
   - **Container Image**: `pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime`
   - **Docker Command**: Leave empty (we'll use our own)

#### 3. Deploy Serverless Endpoint

Create `runpod_handler.py`:
```python
import runpod
import torch
from harmonix_splitter.core.separator import AudioSeparator

separator = AudioSeparator()

def handler(job):
    job_input = job["input"]
    audio_url = job_input.get("audio_url")
    quality = job_input.get("quality", "fast")
    
    # Download and process
    result = separator.process(audio_url, quality=quality)
    
    return {"stems": result["stems"], "status": "complete"}

runpod.serverless.start({"handler": handler})
```

#### 4. Build & Push Docker Image
```bash
# Login to Docker Hub
docker login

# Build and push
docker build -t yourusername/harmonix:latest .
docker push yourusername/harmonix:latest

# On RunPod, create serverless endpoint with your image
```

### Monthly Cost Estimate (RunPod Serverless)
- 100 songs/month: ~$1-2
- 1,000 songs/month: ~$10-20
- 10,000 songs/month: ~$100-200

---

## 🥈 Option 2: Vast.ai (Cheapest GPU)

### Why Vast.ai?
- **Community cloud**: Rent idle GPUs
- **As low as $0.10/hr** for RTX 3080
- Great for batch processing

### Setup
```bash
# Install Vast CLI
pip install vastai

# Set API key
vastai set api-key YOUR_API_KEY

# Find cheap GPU instance
vastai search offers 'reliability > 0.95 gpu_ram >= 12 dph < 0.3'

# Create instance
vastai create instance INSTANCE_ID --image pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime \
  --disk 50 --ssh
```

### Deploy Your App
```bash
# SSH into instance
ssh -p PORT root@IP_ADDRESS

# Clone and run
git clone https://github.com/yourusername/harmonix.git
cd harmonix
pip install -r requirements.txt
python run_dashboard.py --host 0.0.0.0 --port 5000
```

---

## 🥉 Option 3: Railway (Easiest, No GPU)

### Why Railway?
- **One-click deploy** from GitHub
- **No Docker knowledge needed**
- Good for **demo/small scale** use

### Setup
1. Go to [railway.app](https://railway.app)
2. Click **New Project** → **Deploy from GitHub**
3. Select your repo
4. Add Redis: **New** → **Database** → **Redis**
5. Configure environment variables

### railway.json
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile.cpu"
  },
  "deploy": {
    "startCommand": "python run_dashboard.py",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

### Cost
- **Hobby**: $5/month + usage (~$20-50/month total)
- **Pro**: Better for production

---

## 🏗️ Option 4: DigitalOcean App Platform

### Setup
```bash
# Install doctl CLI
brew install doctl
doctl auth init

# Create app from spec
doctl apps create --spec .do/app.yaml
```

### Create `.do/app.yaml`:
```yaml
name: harmonix-audio-splitter
region: nyc
services:
  - name: web
    dockerfile_path: Dockerfile.cpu
    github:
      repo: yourusername/harmonix
      branch: main
    instance_size_slug: professional-m  # 2GB RAM, 1 vCPU
    instance_count: 1
    http_port: 5000
    health_check:
      http_path: /health
    envs:
      - key: REDIS_URL
        scope: RUN_TIME
        value: ${redis.DATABASE_URL}

databases:
  - name: redis
    engine: REDIS
    production: false
```

### Cost: ~$25-50/month

---

## 🐳 Local Docker Commands

### Build & Test Locally
```bash
# GPU version (requires nvidia-docker)
docker-compose up --build

# CPU version
docker-compose -f docker-compose.cpu.yml up --build
```

### Push to Registry
```bash
# Docker Hub
docker build -t yourusername/harmonix:latest .
docker push yourusername/harmonix:latest

# GitHub Container Registry
docker build -t ghcr.io/yourusername/harmonix:latest .
docker push ghcr.io/yourusername/harmonix:latest
```

---

## ⚡ Performance Optimization Tips

### 1. Model Caching
```bash
# Pre-download models during build (already in Dockerfile)
RUN python -c "from demucs.pretrained import get_model; get_model('htdemucs')"
```

### 2. Use Persistent Storage
```yaml
# Mount volumes for models to avoid re-downloading
volumes:
  - harmonix-models:/app/models
```

### 3. Enable GPU (when available)
```python
# In config/config.yaml
models:
  demucs:
    device: "cuda"  # or "auto"
```

### 4. Optimize Batch Size
```yaml
# For multiple files
processing:
  batch_size: 4  # Process 4 files in parallel on GPU
```

---

## 🔐 Production Security Checklist

- [ ] Enable HTTPS (use Cloudflare or Let's Encrypt)
- [ ] Set strong `SECRET_KEY` environment variable
- [ ] Enable rate limiting
- [ ] Configure CORS properly
- [ ] Set up monitoring (Sentry)
- [ ] Regular backups of user data
- [ ] Use environment variables for secrets

### Environment Variables
```bash
# Required for production
SECRET_KEY=your-super-secret-key-here
REDIS_URL=redis://localhost:6379
SENTRY_DSN=https://xxx@sentry.io/xxx

# Optional
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
S3_BUCKET=harmonix-stems
```

---

## 📈 Scaling Strategies

### Low Traffic (< 100 users/day)
- Single RunPod serverless endpoint
- Cost: ~$10-20/month

### Medium Traffic (100-1000 users/day)
- RunPod with auto-scaling (1-3 replicas)
- Cloudflare CDN for static assets
- Cost: ~$50-100/month

### High Traffic (1000+ users/day)
- Kubernetes with GPU node pool
- S3/R2 for file storage
- Redis cluster
- Cost: ~$200-500/month

---

## 🎯 Quick Start Commands

### Deploy to RunPod (Recommended)
```bash
# Build image
docker build -t harmonix:latest .

# Push to Docker Hub
docker tag harmonix:latest yourusername/harmonix:latest
docker push yourusername/harmonix:latest

# Then create serverless endpoint on RunPod dashboard
```

### Deploy to Railway
```bash
# Just push to GitHub - Railway auto-deploys!
git push origin main
```

### Local Testing
```bash
# Test GPU version
docker-compose up

# Test CPU version  
docker-compose -f docker-compose.cpu.yml up
```

---

## 💰 Cost Summary

| Usage Level | Best Platform | Monthly Cost |
|-------------|---------------|--------------|
| Hobby/Demo | Railway | $5-20 |
| Startup (1K songs) | RunPod Serverless | $15-30 |
| Growth (10K songs) | RunPod + CDN | $50-100 |
| Scale (100K songs) | Dedicated GPU | $200-500 |

**My Recommendation**: Start with **RunPod Serverless** - you pay only for actual processing time, making it perfect for starting out while maintaining professional-grade GPU performance.

---

## 🆘 Troubleshooting

### Out of Memory
```bash
# Reduce batch size in config
processing:
  quality_modes:
    fast:
      shifts: 1  # Reduce from 10
```

### Slow Processing (CPU)
- Switch to GPU platform
- Use "fast" quality mode
- Process shorter audio segments

### Model Download Issues
```bash
# Pre-download in Dockerfile
RUN python -c "import demucs; demucs.pretrained.get_model('htdemucs')"
```

---

Need help? Check the logs:
```bash
docker logs harmonix-app -f
```
