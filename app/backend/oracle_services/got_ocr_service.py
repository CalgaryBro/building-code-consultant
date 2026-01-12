#!/usr/bin/env python3
"""
GOT-OCR2 FastAPI Service for Document OCR

This service runs on Oracle server and provides:
1. /ocr - Extract raw text from images using GOT-OCR2
2. /structure - Use Qwen2.5-7B to structure extracted text into JSON
3. /extract - Combined pipeline: OCR + structuring

Designed for accurate building code extraction without hallucinations.
"""

import base64
import io
import json
import logging
import os
import tempfile
import time
from typing import Optional

import requests
import torch
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel
from transformers import AutoProcessor, AutoModelForImageTextToText

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="GOT-OCR2 Service",
    description="Accurate document OCR for building code extraction",
    version="1.0.0"
)

# CORS for external access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instances (lazy loaded)
_got_processor = None
_got_model = None
_model_loading = False

# Ollama URL for Qwen2.5-7B
OLLAMA_URL = "http://localhost:11434/api/generate"

# Request/Response models
class OCRRequest(BaseModel):
    image_base64: str
    format_type: str = "plain"  # plain, ocr, or format

class StructureRequest(BaseModel):
    raw_text: str
    code_name: str = "NBC(AE) 2023"
    page_number: int = 1

class ExtractRequest(BaseModel):
    image_base64: str
    code_name: str = "NBC(AE) 2023"
    page_number: int = 1

class OCRResponse(BaseModel):
    text: str
    extraction_time_seconds: float
    model: str = "GOT-OCR2"

class StructuredResponse(BaseModel):
    articles: list
    raw_text: str
    page_number: int
    extraction_confidence: str
    extraction_time_seconds: float


def load_got_model():
    """Lazy load GOT-OCR2 model."""
    global _got_processor, _got_model, _model_loading

    if _got_model is not None:
        return _got_processor, _got_model

    if _model_loading:
        # Wait for model to load
        while _model_loading:
            time.sleep(1)
        return _got_processor, _got_model

    _model_loading = True
    logger.info("Loading GOT-OCR2 model...")
    start = time.time()

    try:
        _got_processor = AutoProcessor.from_pretrained(
            "stepfun-ai/GOT-OCR-2.0-hf",
            trust_remote_code=True
        )
        _got_model = AutoModelForImageTextToText.from_pretrained(
            "stepfun-ai/GOT-OCR-2.0-hf",
            torch_dtype=torch.float32,
            device_map="cpu",
            trust_remote_code=True
        )
        elapsed = time.time() - start
        logger.info(f"GOT-OCR2 model loaded in {elapsed:.1f}s")
    except Exception as e:
        logger.error(f"Failed to load GOT-OCR2: {e}")
        _model_loading = False
        raise

    _model_loading = False
    return _got_processor, _got_model


def extract_text_got_ocr(image: Image.Image, format_type: str = "plain") -> str:
    """Extract text from image using GOT-OCR2."""
    processor, model = load_got_model()

    # Convert to RGB if needed
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Process image
    inputs = processor(images=image, return_tensors="pt", format=True)

    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=4096,
            do_sample=False
        )

    # Decode
    text = processor.batch_decode(outputs, skip_special_tokens=True)[0]
    return text


def structure_with_llm(raw_text: str, code_name: str, page_number: int) -> dict:
    """Use Qwen2.5-7B to structure extracted text into JSON."""

    prompt = f"""You are a building code expert. Structure the following text extracted from page {page_number} of {code_name} into JSON format.

EXTRACTED TEXT:
{raw_text}

TASK: Identify all code articles and structure them. Articles are numbered like "1.3.3.3" or "9.8.4.1".

Return ONLY valid JSON in this exact format:
{{"articles": [{{"article_number": "X.X.X.X", "title": "Article Title", "full_text": "Complete article text with all sentences"}}]}}

Important:
- Extract the EXACT article numbers as shown in the text
- Include ALL sentences under each article
- Preserve all technical values (dimensions, percentages, etc.)
- If no articles found, return {{"articles": []}}"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "qwen2.5:7b-instruct",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 4096
                }
            },
            timeout=300
        )

        if response.status_code != 200:
            logger.error(f"Ollama error: {response.status_code}")
            return {"articles": [], "error": "LLM structuring failed"}

        result = response.json()
        llm_response = result.get("response", "")

        # Parse JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', llm_response)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return parsed
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM JSON response")
                return {"articles": [], "raw_response": llm_response}

        return {"articles": [], "raw_response": llm_response}

    except Exception as e:
        logger.error(f"LLM structuring error: {e}")
        return {"articles": [], "error": str(e)}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": _got_model is not None,
        "ollama_available": True  # TODO: Actually check
    }


@app.get("/model-info")
async def model_info():
    """Get model information."""
    return {
        "ocr_model": "GOT-OCR2 (stepfun-ai/GOT-OCR-2.0-hf)",
        "ocr_params": "580M",
        "structuring_model": "Qwen2.5-7B-Instruct (via Ollama)",
        "device": "CPU",
        "loaded": _got_model is not None
    }


@app.post("/ocr", response_model=OCRResponse)
async def ocr(request: OCRRequest):
    """Extract text from image using GOT-OCR2."""
    start_time = time.time()

    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image_base64)
        image = Image.open(io.BytesIO(image_data))

        # Extract text
        text = extract_text_got_ocr(image, request.format_type)

        elapsed = time.time() - start_time
        logger.info(f"OCR completed in {elapsed:.1f}s, {len(text)} chars")

        return OCRResponse(
            text=text,
            extraction_time_seconds=round(elapsed, 2)
        )

    except Exception as e:
        logger.error(f"OCR error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/structure")
async def structure(request: StructureRequest):
    """Structure raw text into JSON using Qwen2.5-7B."""
    start_time = time.time()

    try:
        result = structure_with_llm(
            request.raw_text,
            request.code_name,
            request.page_number
        )

        elapsed = time.time() - start_time

        return {
            **result,
            "page_number": request.page_number,
            "structuring_time_seconds": round(elapsed, 2)
        }

    except Exception as e:
        logger.error(f"Structuring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract", response_model=StructuredResponse)
async def extract(request: ExtractRequest):
    """Combined pipeline: OCR + structuring."""
    start_time = time.time()

    try:
        # Step 1: OCR
        image_data = base64.b64decode(request.image_base64)
        image = Image.open(io.BytesIO(image_data))

        ocr_start = time.time()
        raw_text = extract_text_got_ocr(image)
        ocr_time = time.time() - ocr_start
        logger.info(f"OCR: {ocr_time:.1f}s, {len(raw_text)} chars")

        # Step 2: Structure with LLM
        struct_start = time.time()
        structured = structure_with_llm(
            raw_text,
            request.code_name,
            request.page_number
        )
        struct_time = time.time() - struct_start
        logger.info(f"Structuring: {struct_time:.1f}s")

        total_time = time.time() - start_time
        articles = structured.get("articles", [])

        return StructuredResponse(
            articles=articles,
            raw_text=raw_text,
            page_number=request.page_number,
            extraction_confidence="HIGH" if articles else "LOW",
            extraction_time_seconds=round(total_time, 2)
        )

    except Exception as e:
        logger.error(f"Extract error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract-file")
async def extract_file(
    file: UploadFile = File(...),
    code_name: str = Form("NBC(AE) 2023"),
    page_number: int = Form(1)
):
    """Extract from uploaded file."""
    start_time = time.time()

    try:
        # Read file
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # OCR
        raw_text = extract_text_got_ocr(image)

        # Structure
        structured = structure_with_llm(raw_text, code_name, page_number)

        total_time = time.time() - start_time

        return {
            "articles": structured.get("articles", []),
            "raw_text": raw_text,
            "page_number": page_number,
            "extraction_time_seconds": round(total_time, 2)
        }

    except Exception as e:
        logger.error(f"Extract file error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Preload model on startup
@app.on_event("startup")
async def startup():
    """Preload model on startup."""
    logger.info("Starting GOT-OCR2 service...")
    try:
        load_got_model()
    except Exception as e:
        logger.warning(f"Model preload failed (will retry on first request): {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)
