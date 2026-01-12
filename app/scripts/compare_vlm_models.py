#!/usr/bin/env python3
"""
Compare VLM extraction quality between:
1. Qwen3-VL 30B (via LM Studio)
2. LFM2.5-VL-1.6B (via llama.cpp locally)

Tests on complex NBC Part 9 pages with tables.
"""
import os
import sys
import json
import time
import base64
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

import fitz  # PyMuPDF
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent.parent / "data"
CODES_DIR = DATA_DIR / "codes"
OUTPUT_DIR = DATA_DIR / "extraction_comparison"
MODEL_DIR = Path.home() / ".cache" / "lfm-vl"

# LM Studio (Qwen3-VL 30B)
LM_STUDIO_URL = "http://10.0.0.133:8080/v1/chat/completions"
QWEN_MODEL = "qwen/qwen3-vl-30b"

# Complex pages with tables (from Part 9)
TEST_PAGES = [873, 888, 890, 894, 906, 918, 920, 862, 868, 907]

# Extraction prompt
EXTRACTION_PROMPT = """You are a building code document extraction expert. Extract ALL text content from this PDF page image with perfect accuracy.

CRITICAL REQUIREMENTS:
1. Extract EVERY article number (e.g., 9.10.8.1, 9.15.3.4)
2. Extract ALL table data with proper structure
3. Preserve exact numeric values (dimensions, ratings, percentages)
4. Maintain hierarchical structure (articles, sentences, clauses)
5. Include table headers and all cell values

OUTPUT FORMAT (JSON):
{
  "page": <page_number>,
  "articles": [
    {
      "article_number": "X.X.X.X",
      "title": "Article Title",
      "full_text": "Complete verbatim text..."
    }
  ],
  "tables": [
    {
      "title": "Table X.X.X.X",
      "headers": ["Col1", "Col2", ...],
      "rows": [["val1", "val2", ...], ...]
    }
  ],
  "raw_text": "Full page text for reference"
}

Extract the content from the image now:"""


def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def convert_page_to_base64(pdf_path: Path, page_num: int, dpi: int = 300) -> str:
    """Convert a PDF page to base64-encoded PNG."""
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]  # 0-indexed

    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)

    img_bytes = pix.tobytes("png")
    doc.close()

    return base64.standard_b64encode(img_bytes).decode("utf-8")


def extract_with_qwen(image_base64: str, page_num: int) -> Dict[str, Any]:
    """Extract using Qwen3-VL 30B via LM Studio."""
    logger.info(f"Extracting page {page_num} with Qwen3-VL 30B...")

    start_time = time.time()

    payload = {
        "model": QWEN_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": EXTRACTION_PROMPT
                    }
                ]
            }
        ],
        "max_tokens": 8192,
        "temperature": 0.7,
        "top_p": 0.8,
    }

    try:
        with httpx.Client(timeout=300.0) as client:
            response = client.post(LM_STUDIO_URL, json=payload)
            response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]
        elapsed = time.time() - start_time

        return {
            "model": "qwen3-vl-30b",
            "page": page_num,
            "content": content,
            "time_seconds": elapsed,
            "tokens": result.get("usage", {}).get("completion_tokens", 0),
            "success": True
        }

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Qwen extraction failed: {e}")
        return {
            "model": "qwen3-vl-30b",
            "page": page_num,
            "content": str(e),
            "time_seconds": elapsed,
            "success": False
        }


def download_lfm_model():
    """Download LFM2.5-VL-1.6B GGUF model if not present."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_DIR / "LFM2.5-VL-1.6B-Q8_0.gguf"

    if model_path.exists():
        logger.info(f"LFM model already exists at {model_path}")
        return model_path

    logger.info("Downloading LFM2.5-VL-1.6B-Q8_0.gguf...")
    from huggingface_hub import hf_hub_download

    downloaded = hf_hub_download(
        repo_id="LiquidAI/LFM2.5-VL-1.6B-GGUF",
        filename="LFM2.5-VL-1.6B-Q8_0.gguf",
        local_dir=MODEL_DIR,
        local_dir_use_symlinks=False
    )

    logger.info(f"Model downloaded to {downloaded}")
    return Path(downloaded)


def extract_with_lfm(image_base64: str, page_num: int, llm) -> Dict[str, Any]:
    """Extract using LFM2.5-VL-1.6B via llama.cpp."""
    logger.info(f"Extracting page {page_num} with LFM2.5-VL-1.6B...")

    start_time = time.time()

    try:
        # LFM uses ChatML format with image support
        # The image needs to be passed differently for llama-cpp-python

        # Create chat completion with image
        response = llm.create_chat_completion(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": EXTRACTION_PROMPT
                        }
                    ]
                }
            ],
            max_tokens=4096,
            temperature=0.1,
            top_k=50,
            top_p=0.1,
        )

        content = response["choices"][0]["message"]["content"]
        elapsed = time.time() - start_time
        tokens = response.get("usage", {}).get("completion_tokens", 0)

        return {
            "model": "lfm2.5-vl-1.6b",
            "page": page_num,
            "content": content,
            "time_seconds": elapsed,
            "tokens": tokens,
            "success": True
        }

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"LFM extraction failed: {e}")
        return {
            "model": "lfm2.5-vl-1.6b",
            "page": page_num,
            "content": str(e),
            "time_seconds": elapsed,
            "success": False
        }


def analyze_extraction_quality(result: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the quality of an extraction result."""
    content = result.get("content", "")

    # Quality metrics
    metrics = {
        "char_count": len(content),
        "has_json": content.strip().startswith("{") or "```json" in content,
        "article_count": content.count("article_number"),
        "table_count": content.count("table") + content.count("Table"),
        "numeric_values": len([w for w in content.split() if any(c.isdigit() for c in w)]),
        "article_refs": len([w for w in content.split() if w.count('.') >= 2 and any(c.isdigit() for c in w)]),
    }

    # Try to parse JSON
    try:
        # Extract JSON from markdown code blocks if present
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0]
        else:
            json_str = content

        parsed = json.loads(json_str)
        metrics["json_valid"] = True
        metrics["parsed_articles"] = len(parsed.get("articles", []))
        metrics["parsed_tables"] = len(parsed.get("tables", []))
    except:
        metrics["json_valid"] = False
        metrics["parsed_articles"] = 0
        metrics["parsed_tables"] = 0

    return metrics


def run_comparison(num_pages: int = 10):
    """Run the full comparison experiment."""
    ensure_output_dir()

    pdf_path = CODES_DIR / "NBC-AE-2023.pdf"
    if not pdf_path.exists():
        logger.error(f"PDF not found: {pdf_path}")
        return

    pages_to_test = TEST_PAGES[:num_pages]
    logger.info(f"Testing {len(pages_to_test)} pages: {pages_to_test}")

    results = {
        "experiment_date": datetime.now().isoformat(),
        "pdf": str(pdf_path),
        "pages_tested": pages_to_test,
        "qwen_results": [],
        "lfm_results": [],
        "comparison": {}
    }

    # Initialize LFM model
    logger.info("Loading LFM2.5-VL-1.6B model...")
    try:
        model_path = download_lfm_model()
        from llama_cpp import Llama

        llm = Llama(
            model_path=str(model_path),
            n_ctx=4096,
            n_threads=4,
            n_gpu_layers=0,  # CPU only
            verbose=False,
        )
        lfm_available = True
        logger.info("LFM model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load LFM model: {e}")
        lfm_available = False
        llm = None

    # Extract with both models
    for page_num in pages_to_test:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing page {page_num}")
        logger.info(f"{'='*60}")

        # Convert page to image
        try:
            image_base64 = convert_page_to_base64(pdf_path, page_num)
            logger.info(f"Page converted to image ({len(image_base64)} bytes base64)")
        except Exception as e:
            logger.error(f"Failed to convert page {page_num}: {e}")
            continue

        # Extract with Qwen3-VL 30B
        qwen_result = extract_with_qwen(image_base64, page_num)
        qwen_result["quality"] = analyze_extraction_quality(qwen_result)
        results["qwen_results"].append(qwen_result)

        if qwen_result["success"]:
            logger.info(f"Qwen3-VL: {qwen_result['time_seconds']:.1f}s, "
                       f"{qwen_result['quality']['char_count']} chars, "
                       f"JSON valid: {qwen_result['quality']['json_valid']}")

        # Extract with LFM2.5-VL
        if lfm_available:
            # Reset model between extractions
            llm.reset()

            lfm_result = extract_with_lfm(image_base64, page_num, llm)
            lfm_result["quality"] = analyze_extraction_quality(lfm_result)
            results["lfm_results"].append(lfm_result)

            if lfm_result["success"]:
                logger.info(f"LFM2.5-VL: {lfm_result['time_seconds']:.1f}s, "
                           f"{lfm_result['quality']['char_count']} chars, "
                           f"JSON valid: {lfm_result['quality']['json_valid']}")

        # Brief pause between pages
        time.sleep(2)

    # Calculate comparison metrics
    if results["qwen_results"] and results["lfm_results"]:
        qwen_times = [r["time_seconds"] for r in results["qwen_results"] if r["success"]]
        lfm_times = [r["time_seconds"] for r in results["lfm_results"] if r["success"]]

        qwen_quality = [r["quality"] for r in results["qwen_results"] if r["success"]]
        lfm_quality = [r["quality"] for r in results["lfm_results"] if r["success"]]

        results["comparison"] = {
            "qwen": {
                "avg_time_seconds": sum(qwen_times) / len(qwen_times) if qwen_times else 0,
                "success_rate": len(qwen_times) / len(results["qwen_results"]),
                "avg_char_count": sum(q["char_count"] for q in qwen_quality) / len(qwen_quality) if qwen_quality else 0,
                "json_valid_rate": sum(1 for q in qwen_quality if q["json_valid"]) / len(qwen_quality) if qwen_quality else 0,
                "avg_articles": sum(q["parsed_articles"] for q in qwen_quality) / len(qwen_quality) if qwen_quality else 0,
            },
            "lfm": {
                "avg_time_seconds": sum(lfm_times) / len(lfm_times) if lfm_times else 0,
                "success_rate": len(lfm_times) / len(results["lfm_results"]),
                "avg_char_count": sum(q["char_count"] for q in lfm_quality) / len(lfm_quality) if lfm_quality else 0,
                "json_valid_rate": sum(1 for q in lfm_quality if q["json_valid"]) / len(lfm_quality) if lfm_quality else 0,
                "avg_articles": sum(q["parsed_articles"] for q in lfm_quality) / len(lfm_quality) if lfm_quality else 0,
            },
            "speedup_factor": (sum(qwen_times) / len(qwen_times)) / (sum(lfm_times) / len(lfm_times)) if lfm_times and qwen_times else 0
        }

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"vlm_comparison_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"\nResults saved to: {output_file}")

    # Print summary
    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)

    if "comparison" in results and results["comparison"]:
        comp = results["comparison"]

        print(f"\n{'Metric':<30} {'Qwen3-VL 30B':<20} {'LFM2.5-VL 1.6B':<20}")
        print("-"*70)
        print(f"{'Avg Time (seconds)':<30} {comp['qwen']['avg_time_seconds']:<20.1f} {comp['lfm']['avg_time_seconds']:<20.1f}")
        print(f"{'Success Rate':<30} {comp['qwen']['success_rate']*100:<20.1f}% {comp['lfm']['success_rate']*100:<20.1f}%")
        print(f"{'Avg Char Count':<30} {comp['qwen']['avg_char_count']:<20.0f} {comp['lfm']['avg_char_count']:<20.0f}")
        print(f"{'JSON Valid Rate':<30} {comp['qwen']['json_valid_rate']*100:<20.1f}% {comp['lfm']['json_valid_rate']*100:<20.1f}%")
        print(f"{'Avg Articles Parsed':<30} {comp['qwen']['avg_articles']:<20.1f} {comp['lfm']['avg_articles']:<20.1f}")
        print(f"\n{'Speed Factor':<30} {comp['speedup_factor']:.1f}x faster (LFM)")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compare VLM extraction models")
    parser.add_argument("--pages", type=int, default=10, help="Number of pages to test")
    args = parser.parse_args()

    run_comparison(args.pages)
