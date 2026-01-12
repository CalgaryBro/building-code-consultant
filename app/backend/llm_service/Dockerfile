# LLM Service Dockerfile - llama.cpp version
# Lightweight container for running quantized LFM model

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install build and runtime dependencies
# Build tools needed for llama-cpp-python compilation on ARM64
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libopenblas0 \
    libopenblas-dev \
    build-essential \
    cmake \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install other dependencies first
RUN pip install --no-cache-dir -r requirements.txt

# Install llama-cpp-python (latest version with LFM2 support)
# CMAKE_ARGS:
# - GGML_NATIVE=OFF disables native CPU detection (avoids ARM instruction issues in Docker)
# - GGML_BLAS=ON enables OpenBLAS for better performance
# - GGML_CPU_ALL_VARIANTS=OFF disables multiple CPU variants
ENV CMAKE_ARGS="-DGGML_NATIVE=OFF -DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS -DGGML_CPU_ALL_VARIANTS=OFF"
RUN pip install --no-cache-dir llama-cpp-python==0.3.16

# Add huggingface_hub for model download
RUN pip install --no-cache-dir huggingface_hub

# Copy application code
COPY main.py .

# Create directories
RUN mkdir -p /models /root/.cache/huggingface

# Expose ports
EXPOSE 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV LLM_SERVICE_PORT=8081
ENV PRELOAD_MODEL=true
ENV MODEL_DIR=/models
ENV CONTEXT_SIZE=4096
ENV N_THREADS=4

# Run the service
CMD ["python", "main.py"]
