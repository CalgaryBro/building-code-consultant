#!/usr/bin/env python3
"""
VLM Extraction Script for Calgary Building Codes

Uses Qwen3-VL 30B via Ollama to extract clean, properly-formatted text from
building code PDFs. Produces structured JSON ready for database import.

Usage:
    python vlm_extract_all.py --code nbc_part1     # Extract NBC Division A Part 1
    python vlm_extract_all.py --code nbc_part9     # Extract NBC Part 9 (all sections)
    python vlm_extract_all.py --code necb          # Extract NECB 2020
    python vlm_extract_all.py --all                # Extract everything
    python vlm_extract_all.py --test               # Test extraction on single page
"""

import argparse
import base64
import json
import os
import re
import sys
import tempfile
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

import fitz  # PyMuPDF
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('vlm_extraction.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = Path("/Users/mohmmadhanafy/Building-code-consultant")
DATA_DIR = BASE_DIR / "data"
CODES_DIR = DATA_DIR / "codes"
VLM_OUTPUT_DIR = CODES_DIR / "vlm"

# LM Studio server (OpenAI-compatible API)
LM_STUDIO_URL = "http://10.0.0.133:8080/v1/chat/completions"
MODEL_NAME = "qwen/qwen3-vl-30b"  # Model ID as shown in LM Studio

# PDF configurations with page ranges
PDF_CONFIGS = {
    "nbc_part1": {
        "pdf_path": CODES_DIR / "NBC-AE-2023.pdf",
        "output_file": VLM_OUTPUT_DIR / "nbc_ae_2023_part1_vlm.json",
        "code_name": "NBC(AE) 2023",
        "description": "Division A - Compliance, Objectives, Functional Statements",
        "page_ranges": [(30, 70)],  # Division A pages
        "division": "A",
        "parts": [1, 2, 3],
    },
    "nbc_part9_general": {
        "pdf_path": CODES_DIR / "NBC-AE-2023.pdf",
        "output_file": VLM_OUTPUT_DIR / "nbc_ae_2023_part9_general_vlm.json",
        "code_name": "NBC(AE) 2023",
        "description": "Part 9 - Sections 9.1-9.4 General Provisions",
        "page_ranges": [(838, 860)],  # Part 9.1-9.4 pages (approximate)
        "division": "B",
        "parts": [9],
    },
    "nbc_part9": {
        "pdf_path": CODES_DIR / "NBC-AE-2023.pdf",
        "output_file": VLM_OUTPUT_DIR / "nbc_ae_2023_part9_vlm.json",
        "code_name": "NBC(AE) 2023",
        "description": "Part 9 - Housing and Small Buildings (9.5-9.36)",
        "page_ranges": [(860, 1150)],  # Part 9.5-9.36 pages (approximate)
        "division": "B",
        "parts": [9],
    },
    "necb": {
        "pdf_path": CODES_DIR / "NECB-2020.pdf",
        "output_file": VLM_OUTPUT_DIR / "necb_2020_vlm.json",
        "code_name": "NECB 2020",
        "description": "National Energy Code of Canada for Buildings",
        "page_ranges": [(1, -1)],  # All pages (-1 means to end)
        "division": "B",
        "parts": [3, 4, 5, 6, 7, 8],
    },
    "nfc": {
        "pdf_path": CODES_DIR / "NFC-AE-2023.pdf",
        "output_file": VLM_OUTPUT_DIR / "nfc_ae_2023_vlm.json",
        "code_name": "NFC(AE) 2023",
        "description": "National Fire Code - Alberta Edition",
        "page_ranges": [(1, -1)],
        "division": "B",
        "parts": [1, 2, 3, 4, 5, 6, 7, 8],
    },
    "npc": {
        "pdf_path": CODES_DIR / "NPC-2020.pdf",
        "output_file": VLM_OUTPUT_DIR / "npc_2020_vlm.json",
        "code_name": "NPC 2020",
        "description": "National Plumbing Code of Canada",
        "page_ranges": [(1, -1)],
        "division": "B",
        "parts": [1, 2, 3, 4, 5, 6, 7],
    },
    "land_use_bylaw": {
        "pdf_path": CODES_DIR / "Land-Use-Bylaw-1P2007.pdf",
        "output_file": VLM_OUTPUT_DIR / "land_use_bylaw_vlm.json",
        "code_name": "LUB 1P2007",
        "description": "City of Calgary Land Use Bylaw 1P2007 (amended 2025-01-01)",
        "page_ranges": [(1, -1)],  # All 1053 pages - full legal text
        "division": None,
        "parts": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],  # All 13 parts
    },
}


def convert_page_to_base64(pdf_path: Path, page_num: int, dpi: int = 300) -> str:
    """Convert a PDF page to a base64-encoded PNG image."""
    doc = fitz.open(pdf_path)
    page = doc[page_num]

    # Render at 300 DPI for optimal OCR
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)

    # Save to temp file and encode
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        pix.save(f.name)
        temp_path = f.name

    doc.close()

    with open(temp_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    os.unlink(temp_path)
    return image_data


def create_extraction_prompt(code_name: str, page_num: int) -> str:
    """Create the extraction prompt for Qwen3-VL.

    Based on Qwen3-VL best practices:
    - Clear, specific instructions
    - Request verbatim text extraction
    - Simple JSON structure
    """
    return f"""You are extracting text from page {page_num + 1} of the {code_name}.

TASK: Extract ALL text from this page. Focus on code articles (numbered like 1.3.3.3 or 9.8.4.1).

INSTRUCTIONS:
1. Transcribe the EXACT text verbatim
2. Preserve all numbers, units (m², mm, storeys), and formatting
3. Include all numbered sentences (1), 2), 3) etc.)
4. Capture article numbers and their titles

Return as JSON:
{{"page": {page_num + 1}, "articles": [{{"article_number": "...", "title": "...", "full_text": "..."}}], "raw_text": "all text from page"}}

Be precise. Copy exact text without paraphrasing."""


def salvage_partial_json(raw_response: str, page_num: int) -> Dict:
    """Try to extract article data from truncated JSON response."""
    articles = []

    # Try to find article_number patterns
    article_matches = re.findall(
        r'"article_number":\s*"([^"]+)"[^}]*?"title":\s*"([^"]*)"[^}]*?"full_text":\s*"([^"]*(?:[^"\\]|\\.)*)"',
        raw_response,
        re.DOTALL
    )

    for match in article_matches:
        article_num, title, full_text = match
        # Unescape newlines
        full_text = full_text.replace('\\n', '\n')
        articles.append({
            "article_number": article_num,
            "title": title,
            "full_text": full_text,
        })

    # Also try to extract raw_text if present
    raw_text_match = re.search(r'"raw_text":\s*"([^"]*(?:[^"\\]|\\.)*)"', raw_response)
    raw_text = raw_text_match.group(1).replace('\\n', '\n') if raw_text_match else raw_response

    return {
        "articles": articles,
        "page_number": page_num,
        "raw_text": raw_text,
        "extraction_confidence": "MEDIUM" if articles else "LOW",
        "partial_parse": True,
    }


def extract_page_with_vlm(pdf_path: Path, page_num: int, code_name: str) -> Dict:
    """Extract a single page using Qwen3-VL."""
    logger.info(f"Extracting page {page_num + 1}...")

    start_time = time.time()

    # Convert page to image
    try:
        image_b64 = convert_page_to_base64(pdf_path, page_num)
    except Exception as e:
        logger.error(f"Failed to convert page {page_num}: {e}")
        return {"error": str(e), "page_number": page_num + 1}

    # Create prompt
    prompt = create_extraction_prompt(code_name, page_num)

    # Call LM Studio API (OpenAI-compatible)
    try:
        # Format image as data URL for OpenAI-compatible API
        image_url = f"data:image/png;base64,{image_b64}"

        response = requests.post(
            LM_STUDIO_URL,
            json={
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ],
                "temperature": 0.7,
                "top_p": 0.8,
                "max_tokens": 8192,
                "stream": False,
            },
            timeout=600  # 10 minutes timeout
        )

        if response.status_code != 200:
            logger.error(f"LM Studio API error: {response.status_code} - {response.text[:200]}")
            return {"error": f"API error: {response.status_code}", "page_number": page_num + 1}

        result = response.json()
        raw_response = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        elapsed = time.time() - start_time
        logger.info(f"Page {page_num + 1} extracted in {elapsed:.1f}s ({len(raw_response)} chars)")

        # Parse JSON from response
        try:
            # Find JSON in response (may have markdown code blocks)
            # Try to match complete JSON first
            json_match = re.search(r'\{[\s\S]*\}', raw_response)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                    parsed["extraction_time_seconds"] = round(elapsed, 2)
                    parsed["extraction_confidence"] = parsed.get("extraction_confidence", "HIGH")
                    return parsed
                except json.JSONDecodeError:
                    # JSON might be truncated - try to salvage partial data
                    logger.info(f"Attempting to salvage truncated JSON from page {page_num + 1}")
                    partial = salvage_partial_json(raw_response, page_num + 1)
                    partial["extraction_time_seconds"] = round(elapsed, 2)
                    return partial
            else:
                # No JSON structure found - extract raw text
                logger.warning(f"No JSON found in response for page {page_num + 1}")
                return {
                    "articles": [],
                    "page_number": page_num + 1,
                    "raw_text": raw_response,
                    "extraction_confidence": "LOW",
                    "extraction_time_seconds": round(elapsed, 2)
                }
        except Exception as e:
            logger.warning(f"Parse error on page {page_num + 1}: {e}")
            return {
                "articles": [],
                "page_number": page_num + 1,
                "raw_text": raw_response,
                "extraction_confidence": "LOW",
                "parse_error": str(e),
                "extraction_time_seconds": round(elapsed, 2)
            }

    except requests.exceptions.Timeout:
        logger.error(f"Timeout on page {page_num + 1}")
        return {"error": "Timeout", "page_number": page_num + 1}
    except Exception as e:
        logger.error(f"Error extracting page {page_num + 1}: {e}")
        return {"error": str(e), "page_number": page_num + 1}


def merge_articles(all_pages: List[Dict]) -> List[Dict]:
    """Merge articles that span multiple pages."""
    articles = []
    pending_article = None

    for page_data in all_pages:
        page_articles = page_data.get("articles", [])

        for article in page_articles:
            article_num = article.get("article_number", "")
            full_text = article.get("full_text", "")

            # Check if this continues a previous article
            if full_text.startswith("...") and pending_article:
                # Merge with pending article
                pending_article["full_text"] += " " + full_text.lstrip(".")
                if "sentences" in article:
                    pending_article.setdefault("sentences", []).extend(article["sentences"])
                pending_article["pages"].append(page_data.get("page_number"))
            else:
                # Save pending article if exists
                if pending_article:
                    articles.append(pending_article)

                # Start new article
                pending_article = article.copy()
                pending_article["pages"] = [page_data.get("page_number")]

            # Check if article continues to next page
            if not full_text.endswith("..."):
                if pending_article:
                    articles.append(pending_article)
                    pending_article = None

    # Don't forget last pending article
    if pending_article:
        articles.append(pending_article)

    return articles


def extract_code(config_name: str, resume_from_page: int = 0) -> Dict:
    """Extract a complete code using VLM."""
    config = PDF_CONFIGS.get(config_name)
    if not config:
        raise ValueError(f"Unknown config: {config_name}")

    pdf_path = config["pdf_path"]
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    logger.info(f"=" * 60)
    logger.info(f"Extracting: {config['description']}")
    logger.info(f"PDF: {pdf_path}")
    logger.info(f"=" * 60)

    # Get total pages
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    doc.close()

    # Calculate pages to extract
    pages_to_extract = []
    for start, end in config["page_ranges"]:
        if end == -1:
            end = total_pages
        pages_to_extract.extend(range(start - 1, min(end, total_pages)))  # 0-indexed

    logger.info(f"Total pages to extract: {len(pages_to_extract)}")

    # Resume support
    if resume_from_page > 0:
        pages_to_extract = [p for p in pages_to_extract if p >= resume_from_page - 1]
        logger.info(f"Resuming from page {resume_from_page}, {len(pages_to_extract)} pages remaining")

    # Extract each page
    all_pages = []
    start_time = time.time()

    for i, page_num in enumerate(pages_to_extract):
        logger.info(f"Progress: {i + 1}/{len(pages_to_extract)} (page {page_num + 1})")

        page_data = extract_page_with_vlm(pdf_path, page_num, config["code_name"])
        page_data["page_number"] = page_num + 1
        all_pages.append(page_data)

        # Save progress periodically
        if (i + 1) % 10 == 0:
            save_progress(config, all_pages)
            logger.info(f"Progress saved at page {page_num + 1}")

        # Rest every 20 pages to avoid overwhelming the server
        if (i + 1) % 20 == 0:
            logger.info(f"Taking 1-minute rest after {i + 1} pages...")
            time.sleep(60)
            logger.info("Resuming extraction...")
        else:
            # Brief pause between pages
            time.sleep(1)

    elapsed = time.time() - start_time
    logger.info(f"Extraction complete in {elapsed / 60:.1f} minutes")

    # Merge articles across pages
    merged_articles = merge_articles(all_pages)

    # Create final output
    result = {
        "metadata": {
            "code_name": config["code_name"],
            "description": config["description"],
            "extraction_method": "vlm",
            "extraction_model": MODEL_NAME,
            "extraction_date": datetime.now().isoformat(),
            "source_pdf": str(pdf_path.name),
            "pages_extracted": [p + 1 for p in pages_to_extract],
            "total_pages_extracted": len(pages_to_extract),
            "extraction_time_minutes": round(elapsed / 60, 2),
            "division": config.get("division"),
            "parts": config.get("parts"),
        },
        "articles": merged_articles,
        "raw_pages": all_pages,  # Keep raw page data for debugging
        "summary": {
            "total_articles": len(merged_articles),
            "pages_with_errors": len([p for p in all_pages if "error" in p]),
            "low_confidence_pages": len([p for p in all_pages if p.get("extraction_confidence") == "LOW"]),
        }
    }

    # Save final output
    output_path = config["output_file"]
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved to: {output_path}")
    logger.info(f"Total articles extracted: {len(merged_articles)}")

    return result


def save_progress(config: Dict, pages: List[Dict]):
    """Save extraction progress for resume capability."""
    progress_file = config["output_file"].with_suffix('.progress.json')
    with open(progress_file, 'w') as f:
        json.dump({
            "pages_extracted": len(pages),
            "last_page": pages[-1].get("page_number") if pages else 0,
            "timestamp": datetime.now().isoformat(),
            "pages": pages
        }, f, indent=2)


def test_extraction():
    """Test extraction on a single page (NBC Part 1, page 34 - Article 1.3.3.3)."""
    logger.info("Running test extraction...")

    pdf_path = CODES_DIR / "NBC-AE-2023.pdf"
    if not pdf_path.exists():
        logger.error(f"Test PDF not found: {pdf_path}")
        return

    # Page 34 contains Article 1.3.3.3 (Part 9 scope)
    test_page = 33  # 0-indexed

    result = extract_page_with_vlm(pdf_path, test_page, "NBC(AE) 2023")

    # Save test result
    test_output = VLM_OUTPUT_DIR / "test_extraction.json"
    with open(test_output, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    logger.info(f"Test result saved to: {test_output}")

    # Print summary
    articles = result.get("articles", [])
    logger.info(f"Articles found: {len(articles)}")
    for article in articles:
        logger.info(f"  - {article.get('article_number')}: {article.get('title', '')[:50]}...")

    return result


def main():
    parser = argparse.ArgumentParser(description="Extract building codes using VLM")
    parser.add_argument("--code", choices=list(PDF_CONFIGS.keys()),
                       help="Specific code to extract")
    parser.add_argument("--all", action="store_true", help="Extract all codes")
    parser.add_argument("--test", action="store_true", help="Test extraction on single page")
    parser.add_argument("--resume", type=int, default=0,
                       help="Resume from specific page number")
    parser.add_argument("--output", type=Path, default=VLM_OUTPUT_DIR,
                       help="Output directory")

    args = parser.parse_args()

    # Verify LM Studio server is running
    try:
        # Check if LM Studio server is accessible
        test_url = LM_STUDIO_URL.replace("/v1/chat/completions", "/v1/models")
        response = requests.get(test_url, timeout=10)
        if response.status_code == 200:
            models = response.json().get("data", [])
            model_ids = [m.get("id", "") for m in models]
            logger.info(f"LM Studio connected. Available models: {model_ids}")
        else:
            logger.warning(f"LM Studio responded with {response.status_code}, proceeding anyway...")
    except Exception as e:
        logger.error(f"Cannot connect to LM Studio at {LM_STUDIO_URL}: {e}")
        logger.error("Please ensure LM Studio server is running on http://10.0.0.133:8080")
        sys.exit(1)

    if args.test:
        test_extraction()
    elif args.code:
        extract_code(args.code, resume_from_page=args.resume)
    elif args.all:
        # Extract in priority order
        extraction_order = [
            "nbc_part1",        # ~30 min
            "nbc_part9_general", # ~15 min
            "nbc_part9",        # ~4 hours
            "necb",             # ~2 hours
            "nfc",              # ~3 hours
            "npc",              # ~2 hours
            "land_use_bylaw",   # ~2 hours
        ]

        for code in extraction_order:
            try:
                config = PDF_CONFIGS.get(code)
                output_file = config["output_file"]
                # Skip if already completed (output file exists and is not empty)
                if output_file.exists() and output_file.stat().st_size > 1000:
                    logger.info(f"Skipping {code} - already extracted ({output_file.name})")
                    continue
                extract_code(code)
            except Exception as e:
                logger.error(f"Failed to extract {code}: {e}")
                continue
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
