"""
LLM Service - Standalone FastAPI service for AI Q&A using llama.cpp.

This service runs LiquidAI LFM2.5-1.2B-Instruct model (GGUF format)
in a separate container with dedicated resources and monitoring.

llama.cpp provides:
- Efficient CPU inference with quantization (4-bit, 8-bit)
- Low memory footprint (~700MB for Q4_K_M)
- Fast inference without GPU
"""
import os
import time
import logging
import threading
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import psutil
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
from starlette.responses import Response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use a custom registry to avoid conflicts
CUSTOM_REGISTRY = CollectorRegistry(auto_describe=True)

# Prometheus metrics with custom registry
REQUEST_COUNT = Counter('llm_requests_total', 'Total LLM requests', registry=CUSTOM_REGISTRY)
REQUEST_LATENCY = Histogram('llm_request_latency_seconds', 'LLM request latency', registry=CUSTOM_REGISTRY)
TOKENS_GENERATED = Counter('llm_tokens_generated_total', 'Total tokens generated', registry=CUSTOM_REGISTRY)
MODEL_LOADED = Gauge('llm_model_loaded', 'Whether the model is loaded (1=yes, 0=no)', registry=CUSTOM_REGISTRY)
MEMORY_USAGE_MB = Gauge('llm_memory_usage_mb', 'Current memory usage in MB', registry=CUSTOM_REGISTRY)
CPU_PERCENT = Gauge('llm_cpu_percent', 'Current CPU usage percentage', registry=CUSTOM_REGISTRY)

# Model configuration - LiquidAI LFM2.5-1.2B (supported by llama.cpp 0.3.x)
MODEL_DIR = Path(os.getenv("MODEL_DIR", "/models"))
MODEL_REPO = os.getenv("MODEL_REPO", "LiquidAI/LFM2.5-1.2B-Instruct-GGUF")
MODEL_FILE = os.getenv("MODEL_FILE", "LFM2.5-1.2B-Instruct-Q4_K_M.gguf")
CONTEXT_SIZE = int(os.getenv("CONTEXT_SIZE", "4096"))  # Reduced for memory efficiency
N_THREADS = int(os.getenv("N_THREADS", "4"))

# Global model state
_llm = None
_model_lock = threading.Lock()
_model_loaded = False

# System prompt for building code Q&A - optimized for LFM2.5 (good at RAG/extraction)
SYSTEM_PROMPT = """You are a building code expert for Alberta/Calgary. Extract and cite information from the provided sources.

RULES:
1. State the specific requirement FIRST (number, measurement, rating)
2. Cite with [1], [2] immediately after each fact
3. Use ONLY information from the numbered sources
4. If not found, say "Not specifically addressed in sources"
5. Maximum 2 sentences
6. No bullet points, no source descriptions

EXAMPLE:
Q: What is the minimum stair width?
A: The minimum stair width is 900 mm [2]. This applies to Part 9 residential buildings [1]."""


def download_model() -> Optional[Path]:
    """Download the GGUF model if not present."""
    model_path = MODEL_DIR / MODEL_FILE

    if model_path.exists():
        logger.info(f"Model already exists at {model_path}")
        return model_path

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Download from HuggingFace
    try:
        from huggingface_hub import hf_hub_download

        logger.info(f"Downloading model from {MODEL_REPO}/{MODEL_FILE}...")
        downloaded_path = hf_hub_download(
            repo_id=MODEL_REPO,
            filename=MODEL_FILE,
            local_dir=MODEL_DIR,
            local_dir_use_symlinks=False,
        )
        logger.info(f"Model downloaded to {downloaded_path}")
        return Path(downloaded_path)
    except ImportError:
        # Fallback: use httpx to download directly
        import httpx

        url = f"https://huggingface.co/{MODEL_REPO}/resolve/main/{MODEL_FILE}"
        logger.info(f"Downloading model from {url}...")

        with httpx.stream("GET", url, follow_redirects=True, timeout=600) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(model_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = (downloaded / total) * 100
                        if downloaded % (50 * 1024 * 1024) < 8192:  # Log every ~50MB
                            logger.info(f"Download progress: {pct:.1f}%")

        logger.info(f"Model downloaded to {model_path}")
        return model_path
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        return None


def load_model():
    """Load the LLM model using llama.cpp."""
    global _llm, _model_loaded

    if _model_loaded:
        return True

    with _model_lock:
        if _model_loaded:
            return True

        try:
            from llama_cpp import Llama

            # Download model if needed
            model_path = download_model()
            if model_path is None:
                logger.error("Model not available")
                return False

            logger.info(f"Loading LFM model from {model_path}...")
            logger.info(f"Config: context_size={CONTEXT_SIZE}, n_threads={N_THREADS}")

            _llm = Llama(
                model_path=str(model_path),
                n_ctx=CONTEXT_SIZE,
                n_threads=N_THREADS,
                n_gpu_layers=0,  # CPU only for Docker
                verbose=False,
            )

            _model_loaded = True
            MODEL_LOADED.set(1)
            logger.info("LFM model loaded successfully with llama.cpp")
            return True

        except Exception as e:
            logger.error(f"Failed to load LFM model: {e}")
            MODEL_LOADED.set(0)
            return False


def update_resource_metrics():
    """Update resource usage metrics."""
    try:
        process = psutil.Process()
        MEMORY_USAGE_MB.set(process.memory_info().rss / 1024 / 1024)
        CPU_PERCENT.set(process.cpu_percent(interval=0.1))
    except Exception as e:
        logger.warning(f"Failed to update metrics: {e}")


# Request/Response models
class GenerateRequest(BaseModel):
    """Request to generate a response."""
    question: str = Field(..., min_length=3, max_length=2000)
    context: str = Field(..., max_length=10000)
    max_new_tokens: int = Field(default=512, ge=64, le=2048)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)


class GenerateResponse(BaseModel):
    """Response from generation."""
    response: str
    tokens_generated: int
    latency_ms: float
    model_info: Dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    backend: str
    memory_mb: float
    cpu_percent: float


class ResourceStats(BaseModel):
    """Resource usage statistics."""
    memory_mb: float
    memory_percent: float
    cpu_percent: float
    model_loaded: bool
    backend: str
    context_size: int
    n_threads: int
    uptime_seconds: float


# Track service start time
_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("LLM Service (llama.cpp) starting up...")

    # Preload model in background
    if os.getenv("PRELOAD_MODEL", "true").lower() == "true":
        threading.Thread(target=load_model, daemon=True).start()

    yield

    logger.info("LLM Service shutting down...")


app = FastAPI(
    title="LLM Service (llama.cpp)",
    description="AI Q&A service using LiquidAI LFM2.5-1.2B-Instruct with llama.cpp",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health and model status."""
    update_resource_metrics()

    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    cpu_percent = process.cpu_percent(interval=0.1)

    return HealthResponse(
        status="healthy" if _model_loaded else "loading",
        model_loaded=_model_loaded,
        backend="llama.cpp",
        memory_mb=memory_mb,
        cpu_percent=cpu_percent,
    )


@app.get("/stats", response_model=ResourceStats)
async def get_resource_stats():
    """Get detailed resource usage statistics."""
    update_resource_metrics()

    process = psutil.Process()
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    memory_percent = process.memory_percent()
    cpu_percent = process.cpu_percent(interval=0.1)

    return ResourceStats(
        memory_mb=memory_mb,
        memory_percent=memory_percent,
        cpu_percent=cpu_percent,
        model_loaded=_model_loaded,
        backend="llama.cpp",
        context_size=CONTEXT_SIZE,
        n_threads=N_THREADS,
        uptime_seconds=time.time() - _start_time,
    )


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    update_resource_metrics()
    return Response(content=generate_latest(CUSTOM_REGISTRY), media_type=CONTENT_TYPE_LATEST)


def reset_model():
    """Reset the model's KV cache to fix consecutive request issues."""
    global _llm
    if _llm is not None:
        try:
            # Reset KV cache - fixes "llama_decode returned -1" error
            _llm.reset()
            logger.debug("Model KV cache reset")
        except Exception as e:
            logger.warning(f"Could not reset model: {e}")


def reload_model():
    """Force reload the model (used after errors)."""
    global _llm, _model_loaded

    with _model_lock:
        try:
            if _llm is not None:
                del _llm
                _llm = None
            _model_loaded = False
            logger.info("Model unloaded, will reload on next request")
        except Exception as e:
            logger.error(f"Error unloading model: {e}")


@app.post("/generate", response_model=GenerateResponse)
async def generate_response(request: GenerateRequest):
    """Generate a response to a building code question."""
    global _llm, _model_loaded

    REQUEST_COUNT.inc()
    start_time = time.time()

    # Ensure model is loaded
    if not _model_loaded:
        if not load_model():
            raise HTTPException(
                status_code=503,
                detail="Model not available. Please try again later."
            )

    # Reset KV cache before each request to prevent consecutive request failures
    reset_model()

    try:
        # Build the prompt in ChatML format
        user_message = f"""Based on the following building code and standards information, please answer the question.

CONTEXT:
{request.context}

QUESTION: {request.question}

Provide a clear, accurate answer based on the context above. Cite specific code sections when applicable."""

        # Format as chat messages for llama.cpp
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]

        # Generate using llama.cpp chat completion
        # Parameters recommended by LiquidAI for LFM2.5
        with REQUEST_LATENCY.time():
            response = _llm.create_chat_completion(
                messages=messages,
                max_tokens=request.max_new_tokens,
                temperature=request.temperature,
                top_k=50,           # LiquidAI recommended
                top_p=0.1,          # LiquidAI recommended
                repeat_penalty=1.05, # LiquidAI recommended
                stop=["<|endoftext|>", "<|im_end|>"],
            )

        # Extract response
        response_text = response["choices"][0]["message"]["content"].strip()
        tokens_generated = response["usage"]["completion_tokens"]
        TOKENS_GENERATED.inc(tokens_generated)

        latency_ms = (time.time() - start_time) * 1000

        return GenerateResponse(
            response=response_text,
            tokens_generated=tokens_generated,
            latency_ms=latency_ms,
            model_info={
                "model_id": "LiquidAI/LFM2.5-1.2B-Instruct",
                "backend": "llama.cpp",
                "quantization": "Q4_K_M",
                "parameters": "1.2B",
            }
        )

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error generating response: {error_msg}")

        # If it's a decode error, reload the model for next request
        if "llama_decode" in error_msg or "decode" in error_msg.lower():
            logger.info("Decode error detected, scheduling model reload")
            reload_model()

        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {error_msg}"
        )


@app.get("/model-info")
async def get_model_info():
    """Get information about the loaded model."""
    model_path = MODEL_DIR / MODEL_FILE
    model_size_mb = model_path.stat().st_size / 1024 / 1024 if model_path.exists() else 0

    return {
        "model_id": "LiquidAI/LFM2.5-1.2B-Instruct",
        "model_file": MODEL_FILE,
        "model_size_mb": round(model_size_mb, 1),
        "loaded": _model_loaded,
        "backend": "llama.cpp",
        "quantization": "Q4_K_M",
        "parameters": "1.2B",
        "context_length": CONTEXT_SIZE,
        "n_threads": N_THREADS,
        "description": "LFM2.5 is a lightweight 1.2B hybrid SSM/Transformer model from LiquidAI, optimized for instruction following (GGUF Q4_K_M quantized)",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("LLM_SERVICE_PORT", "8081")),
        reload=False,
        workers=1,  # Single worker to avoid model duplication
    )
