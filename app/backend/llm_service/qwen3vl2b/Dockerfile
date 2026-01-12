# Dockerfile for Qwen3-VL-2B Vision-Language Model
# Uses llama.cpp server for CPU inference

FROM ghcr.io/ggml-org/llama.cpp:server

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    wget \
    && pip3 install huggingface_hub \
    && rm -rf /var/lib/apt/lists/*

# Create model directory
WORKDIR /models

# Download Qwen3-VL-2B GGUF files (Q4_K_M for CPU efficiency)
# Note: File names use "Qwen3VL" not "Qwen3-VL"
RUN python3 -c "\
from huggingface_hub import hf_hub_download; \
hf_hub_download('Qwen/Qwen3-VL-2B-Instruct-GGUF', 'Qwen3VL-2B-Instruct-Q4_K_M.gguf', local_dir='/models'); \
hf_hub_download('Qwen/Qwen3-VL-2B-Instruct-GGUF', 'mmproj-Qwen3VL-2B-Instruct-F16.gguf', local_dir='/models')"

EXPOSE 8083

# Run llama-server with vision support
# -t 8 = 8 threads for CPU
# -c 4096 = 4K context
CMD ["llama-server", \
     "-m", "/models/Qwen3VL-2B-Instruct-Q4_K_M.gguf", \
     "--mmproj", "/models/mmproj-Qwen3VL-2B-Instruct-F16.gguf", \
     "-c", "4096", \
     "--host", "0.0.0.0", \
     "--port", "8083", \
     "-t", "8"]
