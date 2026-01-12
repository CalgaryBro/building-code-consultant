#!/usr/bin/env python3
"""
GOT-OCR2 Extraction Pipeline for Calgary Building Codes

Uses GOT-OCR2 on Oracle server for accurate OCR extraction.
Pipeline: PDF → Image → GOT-OCR2 (Oracle) → Qwen2.5-7B (Oracle) → Structured JSON

Advantages over VLM:
- NO hallucinations (accurate article numbers)
- Faster extraction (~3 min/page vs 30+ min for VLM)
- Better for legal/code documents

Usage:
    python got_ocr_extract.py --code nbc_part1     # Extract NBC Part 1
    python got_ocr_extract.py --code nbc_part9     # Extract NBC Part 9
    python got_ocr_extract.py --all                # Extract all codes
    python got_ocr_extract.py --test               # Test single page
"""

import argparse
import base64
import json
import logging
import os
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import fitz  # PyMuPDF
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('got_ocr_extraction.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = Path("/Users/mohmmadhanafy/Building-code-consultant")
DATA_DIR = BASE_DIR / "data"
CODES_DIR = DATA_DIR / "codes"
OUTPUT_DIR = CODES_DIR / "got_ocr"

# Oracle GOT-OCR2 service
# Use SSH tunnel for external access:
#   ssh -L 8082:localhost:8082 -i ~/Oracle_data/ssh-key-2025-05-12.key opc@129.153.97.27 -N &
# Then use: GOT_OCR_URL = "http://localhost:8082"
ORACLE_IP = os.getenv("ORACLE_IP", "localhost")  # Use localhost with SSH tunnel
GOT_OCR_PORT = os.getenv("ORACLE_PORT", "8082")
GOT_OCR_URL = f"http://{ORACLE_IP}:{GOT_OCR_PORT}"

# PDF configurations (same as vlm_extract_all.py)
PDF_CONFIGS = {
    "nbc_part1": {
        "pdf_path": CODES_DIR / "NBC-AE-2023.pdf",
        "output_file": OUTPUT_DIR / "nbc_ae_2023_part1_got.json",
        "code_name": "NBC(AE) 2023",
        "description": "Division A - Compliance, Objectives, Functional Statements",
        "page_ranges": [(30, 70)],
        "division": "A",
        "parts": [1, 2, 3],
    },
    "nbc_part9_general": {
        "pdf_path": CODES_DIR / "NBC-AE-2023.pdf",
        "output_file": OUTPUT_DIR / "nbc_ae_2023_part9_general_got.json",
        "code_name": "NBC(AE) 2023",
        "description": "Part 9 - Sections 9.1-9.4 General Provisions",
        "page_ranges": [(838, 860)],
        "division": "B",
        "parts": [9],
    },
    "nbc_part9": {
        "pdf_path": CODES_DIR / "NBC-AE-2023.pdf",
        "output_file": OUTPUT_DIR / "nbc_ae_2023_part9_got.json",
        "code_name": "NBC(AE) 2023",
        "description": "Part 9 - Housing and Small Buildings (9.5-9.36)",
        "page_ranges": [(860, 1150)],
        "division": "B",
        "parts": [9],
    },
    "necb": {
        "pdf_path": CODES_DIR / "NECB-2020.pdf",
        "output_file": OUTPUT_DIR / "necb_2020_got.json",
        "code_name": "NECB 2020",
        "description": "National Energy Code of Canada for Buildings",
        "page_ranges": [(1, -1)],
        "division": "B",
        "parts": [3, 4, 5, 6, 7, 8],
    },
    "nfc": {
        "pdf_path": CODES_DIR / "NFC-AE-2023.pdf",
        "output_file": OUTPUT_DIR / "nfc_ae_2023_got.json",
        "code_name": "NFC(AE) 2023",
        "description": "National Fire Code - Alberta Edition",
        "page_ranges": [(1, -1)],
        "division": "B",
        "parts": [1, 2, 3, 4, 5, 6, 7, 8],
    },
    "npc": {
        "pdf_path": CODES_DIR / "NPC-2020.pdf",
        "output_file": OUTPUT_DIR / "npc_2020_got.json",
        "code_name": "NPC 2020",
        "description": "National Plumbing Code of Canada",
        "page_ranges": [(1, -1)],
        "division": "B",
        "parts": [1, 2, 3, 4, 5, 6, 7],
    },
    "land_use_bylaw": {
        "pdf_path": CODES_DIR / "Land-Use-Bylaw-1P2007.pdf",
        "output_file": OUTPUT_DIR / "land_use_bylaw_got.json",
        "code_name": "LUB 1P2007",
        "description": "City of Calgary Land Use Bylaw",
        "page_ranges": [(1, -1)],
        "division": None,
        "parts": list(range(1, 14)),
    },
}


def convert_page_to_base64(pdf_path: Path, page_num: int, dpi: int = 300) -> str:
    """Convert a PDF page to base64-encoded PNG."""
    doc = fitz.open(pdf_path)
    page = doc[page_num]

    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        pix.save(f.name)
        temp_path = f.name

    doc.close()

    with open(temp_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    os.unlink(temp_path)
    return image_data


def check_oracle_service() -> bool:
    """Check if Oracle GOT-OCR2 service is running."""
    try:
        response = requests.get(f"{GOT_OCR_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("model_loaded"):
                logger.info("Oracle GOT-OCR2 service is ready")
                return True
            else:
                logger.warning("GOT-OCR2 model not loaded yet")
                return False
        return False
    except Exception as e:
        logger.error(f"Cannot connect to Oracle service: {e}")
        return False


def extract_page_remote(image_base64: str, code_name: str, page_num: int) -> Dict:
    """Extract a page using the Oracle GOT-OCR2 service."""
    try:
        response = requests.post(
            f"{GOT_OCR_URL}/extract",
            json={
                "image_base64": image_base64,
                "code_name": code_name,
                "page_number": page_num
            },
            timeout=600  # 10 minutes
        )

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Oracle service error: {response.status_code}")
            return {"error": f"HTTP {response.status_code}", "page_number": page_num}

    except requests.exceptions.Timeout:
        logger.error(f"Timeout on page {page_num}")
        return {"error": "Timeout", "page_number": page_num}
    except Exception as e:
        logger.error(f"Error extracting page {page_num}: {e}")
        return {"error": str(e), "page_number": page_num}


def extract_code(config_name: str, resume_from_page: int = 0) -> Dict:
    """Extract a complete code using GOT-OCR2."""
    config = PDF_CONFIGS.get(config_name)
    if not config:
        raise ValueError(f"Unknown config: {config_name}")

    pdf_path = config["pdf_path"]
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Check service
    if not check_oracle_service():
        logger.error("Oracle GOT-OCR2 service not available")
        logger.error("Start it with: ssh opc@129.153.97.27 'sudo systemctl start got-ocr'")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info(f"Extracting: {config['description']}")
    logger.info(f"PDF: {pdf_path}")
    logger.info("=" * 60)

    # Get total pages
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    doc.close()

    # Calculate pages to extract
    pages_to_extract = []
    for start, end in config["page_ranges"]:
        if end == -1:
            end = total_pages
        pages_to_extract.extend(range(start - 1, min(end, total_pages)))

    logger.info(f"Total pages to extract: {len(pages_to_extract)}")

    # Resume support
    if resume_from_page > 0:
        pages_to_extract = [p for p in pages_to_extract if p >= resume_from_page - 1]
        logger.info(f"Resuming from page {resume_from_page}")

    # Load existing progress if any
    progress_file = config["output_file"].with_suffix('.progress.json')
    all_pages = []
    if progress_file.exists() and resume_from_page == 0:
        try:
            with open(progress_file) as f:
                progress_data = json.load(f)
                all_pages = progress_data.get("pages", [])
                last_page = progress_data.get("last_page", 0)
                if last_page > 0:
                    pages_to_extract = [p for p in pages_to_extract if p >= last_page]
                    logger.info(f"Resuming from saved progress (page {last_page})")
        except Exception as e:
            logger.warning(f"Could not load progress: {e}")

    # Extract each page
    start_time = time.time()

    for i, page_num in enumerate(pages_to_extract):
        logger.info(f"Progress: {i + 1}/{len(pages_to_extract)} (page {page_num + 1})")

        # Convert to image
        try:
            image_b64 = convert_page_to_base64(pdf_path, page_num)
        except Exception as e:
            logger.error(f"Failed to convert page {page_num}: {e}")
            all_pages.append({"error": str(e), "page_number": page_num + 1})
            continue

        # Extract via Oracle service
        page_data = extract_page_remote(image_b64, config["code_name"], page_num + 1)
        all_pages.append(page_data)

        # Save progress every 5 pages
        if (i + 1) % 5 == 0:
            save_progress(config, all_pages)
            logger.info(f"Progress saved at page {page_num + 1}")

        # Brief pause between pages (Oracle service needs time)
        time.sleep(2)

    elapsed = time.time() - start_time
    logger.info(f"Extraction complete in {elapsed / 60:.1f} minutes")

    # Collect all articles
    all_articles = []
    for page_data in all_pages:
        articles = page_data.get("articles", [])
        for article in articles:
            article["page_number"] = page_data.get("page_number")
            all_articles.append(article)

    # Create final output
    result = {
        "metadata": {
            "code_name": config["code_name"],
            "description": config["description"],
            "extraction_method": "got_ocr",
            "extraction_model": "GOT-OCR2 + Qwen2.5-7B",
            "extraction_date": datetime.now().isoformat(),
            "source_pdf": str(pdf_path.name),
            "pages_extracted": [p + 1 for p in pages_to_extract],
            "total_pages_extracted": len(pages_to_extract),
            "extraction_time_minutes": round(elapsed / 60, 2),
            "division": config.get("division"),
            "parts": config.get("parts"),
        },
        "articles": all_articles,
        "raw_pages": all_pages,
        "summary": {
            "total_articles": len(all_articles),
            "pages_with_errors": len([p for p in all_pages if "error" in p]),
        }
    }

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save final output
    output_path = config["output_file"]
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved to: {output_path}")
    logger.info(f"Total articles extracted: {len(all_articles)}")

    return result


def save_progress(config: Dict, pages: List[Dict]):
    """Save extraction progress."""
    progress_file = config["output_file"].with_suffix('.progress.json')
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(progress_file, 'w') as f:
        json.dump({
            "pages_extracted": len(pages),
            "last_page": pages[-1].get("page_number", 0) if pages else 0,
            "timestamp": datetime.now().isoformat(),
            "pages": pages
        }, f, indent=2)


def test_extraction():
    """Test extraction on a single page."""
    logger.info("Running test extraction...")

    if not check_oracle_service():
        logger.error("Oracle service not available")
        return None

    pdf_path = CODES_DIR / "NBC-AE-2023.pdf"
    if not pdf_path.exists():
        logger.error(f"Test PDF not found: {pdf_path}")
        return None

    # Page 34 contains Article 1.3.3.3
    test_page = 33  # 0-indexed

    logger.info(f"Converting page {test_page + 1} to image...")
    image_b64 = convert_page_to_base64(pdf_path, test_page)

    logger.info("Sending to Oracle GOT-OCR2 service...")
    result = extract_page_remote(image_b64, "NBC(AE) 2023", test_page + 1)

    # Save test result
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    test_output = OUTPUT_DIR / "test_extraction.json"
    with open(test_output, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    logger.info(f"Test result saved to: {test_output}")

    # Print summary
    articles = result.get("articles", [])
    logger.info(f"Articles found: {len(articles)}")
    for article in articles:
        logger.info(f"  - {article.get('article_number')}: {article.get('title', '')[:50]}...")

    # Print raw text preview
    raw_text = result.get("raw_text", "")
    logger.info(f"Raw text preview ({len(raw_text)} chars): {raw_text[:500]}...")

    return result


def main():
    parser = argparse.ArgumentParser(description="Extract building codes using GOT-OCR2 on Oracle")
    parser.add_argument("--code", choices=list(PDF_CONFIGS.keys()),
                       help="Specific code to extract")
    parser.add_argument("--all", action="store_true", help="Extract all codes")
    parser.add_argument("--test", action="store_true", help="Test extraction on single page")
    parser.add_argument("--resume", type=int, default=0,
                       help="Resume from specific page number")

    args = parser.parse_args()

    if args.test:
        test_extraction()
    elif args.code:
        extract_code(args.code, resume_from_page=args.resume)
    elif args.all:
        extraction_order = [
            "nbc_part1",
            "nbc_part9_general",
            "nbc_part9",
            "necb",
            "nfc",
            "npc",
            "land_use_bylaw",
        ]

        for code in extraction_order:
            try:
                config = PDF_CONFIGS.get(code)
                output_file = config["output_file"]
                if output_file.exists() and output_file.stat().st_size > 1000:
                    logger.info(f"Skipping {code} - already extracted")
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
