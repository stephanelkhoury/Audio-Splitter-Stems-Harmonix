# Harmonix Audio Splitter - GPU-enabled Dockerfile

FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Metadata
LABEL maintainer="Stephan El Khoury <stephan@harmonix.dev>"
LABEL description="Harmonix AI Audio Splitter with GPU support"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    HARMONIX_USE_GPU=true \
    HARMONIX_API_HOST=0.0.0.0 \
    HARMONIX_API_PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    libsndfile1 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .
COPY pyproject.toml .

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p /app/data/uploads \
    /app/data/outputs \
    /app/data/temp \
    /app/models \
    /app/logs

# Install the package
RUN pip3 install -e .

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: Start API server
CMD ["uvicorn", "harmonix_splitter.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
