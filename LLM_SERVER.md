# LLM/VLM Server Information

## Server Details

| Property | Value |
|----------|-------|
| **IP Address** | 129.153.97.27 |
| **Provider** | Oracle Cloud Infrastructure (OCI) |
| **OS** | Oracle Linux Server 8.10 |
| **Architecture** | ARM64 (aarch64) |
| **Kernel** | 5.15.0-308.179.6.3.el8uek.aarch64 |
| **Hostname** | instance-20250511-2010 |

## Hardware Specs

| Resource | Value |
|----------|-------|
| **CPU** | 4 cores (ARM64) |
| **RAM** | 23 GB total |
| **RAM Available** | ~20 GB (after cleanup) |
| **Swap** | 4 GB |
| **Disk** | 36 GB total, ~25 GB free |
| **GPU** | None (CPU-only inference) |

## SSH Connection

### Primary User (opc - admin)
```bash
ssh -i ~/Oracle_data/ssh-key-2025-05-12.key opc@129.153.97.27
```

### SSH Key Location
```
Private Key: ~/Oracle_data/ssh-key-2025-05-12.key
Public Key:  ~/Oracle_data/ssh-key-2025-05-12.key.pub
```

---

## Current Status (as of 2026-01-12)

### Installed Components
| Component | Version | Status |
|-----------|---------|--------|
| Docker | 26.1.3 | Installed |
| Ollama | latest | **Running (systemd service)** |
| Qwen3-VL-8B | Q4_K_M (6.1GB) | **Active via Ollama** |
| Qwen2.5-7B-Instruct | 4.7GB | **Active via Ollama** (text structuring) |
| Python | 3.9.25 | Installed |
| GCC Toolset | 10.3.1 | Installed |

### Cleaned Up (Removed)
- Phi-3 LLM service (`phi3-api.service`) - was using 15GB RAM
- Phi-3 model files (`/opt/phi3-api`) - 683MB
- Gemma API service file
- Old log files - 848MB

---

## Qwen3-VL-8B via Ollama (Current Setup)

### Configuration
- **Service**: systemd (`ollama.service`)
- **Port**: 11434 (localhost only by default)
- **Model**: qwen3-vl:latest (8.8B params, Q4_K_M, 6.1GB)
- **RAM Usage**: ~12GB (model + KV cache)
- **Inference Time**: ~2 minutes per query (CPU)

### Service Management
```bash
# Check status
sudo systemctl status ollama

# Start/stop/restart
sudo systemctl start ollama
sudo systemctl stop ollama
sudo systemctl restart ollama

# View logs
sudo journalctl -u ollama -f
```

### API Endpoints
```bash
# List models
curl http://localhost:11434/api/tags

# Generate response (text)
curl http://localhost:11434/api/generate -d '{
  "model": "qwen3-vl",
  "prompt": "Hello, what is 2+2?",
  "stream": false
}'

# Chat completion
curl http://localhost:11434/api/chat -d '{
  "model": "qwen3-vl",
  "messages": [{"role": "user", "content": "Hello"}],
  "stream": false
}'

# Vision (with image)
curl http://localhost:11434/api/generate -d '{
  "model": "qwen3-vl",
  "prompt": "Describe this image",
  "images": ["base64_encoded_image_here"],
  "stream": false
}'
```

### Expose API Externally
To access Ollama from outside (port 8083):
```bash
# Option 1: SSH tunnel (recommended for security)
ssh -L 8083:localhost:11434 opc@129.153.97.27

# Option 2: Modify ollama.service to bind to 0.0.0.0
# Edit /etc/systemd/system/ollama.service and add:
# Environment="OLLAMA_HOST=0.0.0.0:8083"
```

---

## Legacy: Qwen3-VL-4B Files (Not in Use)

The 4B model files were downloaded but not used because llama-cpp-python 0.3.16
doesn't support Qwen3-VL architecture. Ollama uses the 8B model instead.

```
/opt/qwen3vl4b/
├── Qwen3VL-4B-Instruct-Q4_K_M.gguf    # 2.4 GB - Not used
├── mmproj-Qwen3VL-4B-Instruct-F16.gguf # 798 MB - Not used
└── server.py                           # FastAPI script (deprecated)
```

---

## Setup History (2026-01-11)

### 1. Server Cleanup
```bash
# Stopped and removed Phi-3 service
sudo systemctl stop phi3-api
sudo systemctl disable phi3-api
sudo rm /etc/systemd/system/phi3-api.service
sudo rm -rf /opt/phi3-api

# Cleaned old logs
sudo journalctl --vacuum-time=1d  # Removed 848MB

# Removed Gemma service file
sudo rm /etc/systemd/system/gemma-api.service
```

### 2. Docker Installation
```bash
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl enable --now docker
```

### 3. Python 3.9 + GCC 10 Installation
```bash
# Python 3.9 (llama-cpp-python requires 3.8+)
sudo dnf module enable python39 -y
sudo dnf install -y python39 python39-pip python39-devel

# GCC 10 (fixes std::filesystem linking issues on Oracle Linux 8)
sudo dnf install -y gcc-toolset-10
```

### 4. llama-cpp-python Installation
```bash
# Must use GCC 10 to avoid std::filesystem linking errors
scl enable gcc-toolset-10 -- python3.9 -m pip install llama-cpp-python fastapi uvicorn
```

### 5. Model Download (Qwen3-VL-4B - deprecated)
```bash
sudo mkdir -p /opt/qwen3vl4b
cd /opt/qwen3vl4b

# Download from HuggingFace
sudo wget "https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct-GGUF/resolve/main/Qwen3VL-4B-Instruct-Q4_K_M.gguf"
sudo wget "https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct-GGUF/resolve/main/mmproj-Qwen3VL-4B-Instruct-F16.gguf"
```

### 6. Ollama Installation (2026-01-12 - Current Solution)
```bash
# Install Ollama (native ARM64 binary)
curl -fsSL https://ollama.com/install.sh | sh

# Pull Qwen3-VL-8B model
ollama pull qwen3-vl

# Verify
ollama list
```

**Why Ollama instead of llama-cpp-python?**
- llama-cpp-python 0.3.16 doesn't support the `qwen3vl` architecture yet
- Building from source failed due to CMake compatibility issues
- Ollama has native Qwen3-VL support out of the box

---

## Quick Commands

```bash
# Connect to server
ssh -i ~/Oracle_data/ssh-key-2025-05-12.key opc@129.153.97.27

# Check system resources
ssh -i ~/Oracle_data/ssh-key-2025-05-12.key opc@129.153.97.27 "free -h && df -h /"

# Check running services
ssh -i ~/Oracle_data/ssh-key-2025-05-12.key opc@129.153.97.27 "systemctl list-units --type=service --state=running | grep -v systemd"

# View VLM server logs
ssh -i ~/Oracle_data/ssh-key-2025-05-12.key opc@129.153.97.27 "tail -f /var/log/qwen3vl.log"

# Check Docker containers
ssh -i ~/Oracle_data/ssh-key-2025-05-12.key opc@129.153.97.27 "docker ps -a"
```

## Network Access

Required ports (configure in OCI security list):
- **22**: SSH
- **8083**: VLM API server

## Technical Notes

### Why Native Build Instead of Docker?
The official llama.cpp Docker image is AMD64-only. The ARM64 server requires native compilation.

### Why GCC 10?
Oracle Linux 8's default GCC 8 has C++ std::filesystem linking issues. GCC 10 from gcc-toolset-10 resolves this.

### Why llama-cpp-python Instead of llama.cpp Server?
Building llama.cpp from source had the same std::filesystem issues. The Python binding handles the build correctly when using GCC 10.

---

---

## GOT-OCR2 Setup (Recommended for Document OCR)

### Why GOT-OCR2?
- **580M params** vs 8.8B for Qwen3-VL (15x smaller)
- **~3 min/page** on CPU vs 27+ min for VLM
- **Specialized for documents** - better accuracy on structured text

### Installation
```bash
scl enable gcc-toolset-10 -- python3.9 -m pip install transformers accelerate tiktoken pillow torch torchvision
```

### Usage Script
```python
from transformers import AutoProcessor, AutoModelForImageTextToText
from PIL import Image
import torch

# Load model (first run downloads ~1.2GB)
processor = AutoProcessor.from_pretrained("stepfun-ai/GOT-OCR-2.0-hf", trust_remote_code=True)
model = AutoModelForImageTextToText.from_pretrained(
    "stepfun-ai/GOT-OCR-2.0-hf",
    torch_dtype=torch.float32,
    device_map="cpu",
    trust_remote_code=True
)

# Process image
image = Image.open("page.png").convert("RGB")
inputs = processor(images=image, return_tensors="pt", format=True)

with torch.no_grad():
    outputs = model.generate(**inputs, max_new_tokens=2048, do_sample=False)

text = processor.batch_decode(outputs, skip_special_tokens=True)[0]
```

### Performance (ARM64 CPU, 4 cores)
| Metric | Value |
|--------|-------|
| Model load | ~13 sec |
| Inference | ~3 min/page |
| RAM usage | ~2-3 GB |
| Output quality | Excellent (LaTeX formatted) |

### Comparison: GOT-OCR2 vs Qwen3-VL-8B
| Model | Time/Page | Quality | Use Case |
|-------|-----------|---------|----------|
| GOT-OCR2 | 3 min | Excellent | Document OCR |
| Qwen3-VL-8B | 27+ min | Failed | Not practical on CPU |

---

## Completed Tasks
- [x] Server cleanup (Phi-3, Gemma, logs removed)
- [x] Docker installation
- [x] Python 3.9 + GCC 10 installation
- [x] Ollama installation (Qwen3-VL-8B)
- [x] GOT-OCR2 installation and testing
- [x] Benchmarked OCR performance
- [x] Qwen2.5-7B-Instruct installation (4.7 GB, for text structuring)

## Pending Tasks
- [ ] Configure OCI firewall for external access
- [ ] Create FastAPI wrapper for GOT-OCR2
- [ ] Batch processing script for multiple pages
