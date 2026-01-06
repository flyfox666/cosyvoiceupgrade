# CosyVoice All-in-One Docker Image
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3.10-dev \
    ffmpeg \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY . /app/

# Create directories
RUN mkdir -p /app/custom_voices /app/pretrained_models

# Expose ports
# 50000 - WebUI (Gradio)
# 81889 - API Server (FastAPI)
EXPOSE 50000 81889

# Environment variables
ENV MODEL_DIR=/app/pretrained_models/Fun-CosyVoice3-0.5B
ENV WEBUI_PORT=50000
ENV API_PORT=81889

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:${API_PORT}/health || exit 1

# Start both services
CMD ["python3", "start_all.py"]
