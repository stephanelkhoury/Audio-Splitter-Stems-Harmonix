# Harmonix Audio Splitter - Production Dockerfile
# Optimized for GPU inference with minimal image size

FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libmagic1 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download models during build (optional but recommended)
RUN python -c "import torch; from demucs.pretrained import get_model; get_model('htdemucs')" || true

# Copy application code
COPY . .

# Install the package
RUN pip install -e .

# Create necessary directories
RUN mkdir -p data/uploads data/outputs data/temp logs models/weights

# Expose ports
EXPOSE 5000 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command - run dashboard
CMD ["python", "run_dashboard.py"]
