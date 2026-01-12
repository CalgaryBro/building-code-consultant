#!/usr/bin/env python3
"""
Comprehensive Extraction Comparison: Pythonic vs VLM
Compares extraction quality for NBC Part 1 articles that define Part 9 scope.

Target Articles:
- 1.3.3.2 Application of Parts 3, 4, 5 and 6
- 1.3.3.3 Application of Parts 9, 10 and 11 (KEY - Part 9 scope)
- 1.3.3.4 Building Size Determination
"""

import json
import os
import re
import time
import base64
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
import subprocess

import pdfplumber
import fitz  # PyMuPDF
from PIL import Image
import requests

# Configuration
BASE_DIR = Path("/Users/mohmmadhanafy/Building-code-consultant")
PDF_PATH = BASE_DIR / "data/codes/NBC-AE-2023.pdf"
OUTPUT_DIR = BASE_DIR / "data/extraction_comparison"
OUTPUT_DIR.mkdir(exist_ok=True)

# Target pages for Part 9 scope articles (0-indexed)
TARGET_PAGES = [32, 33, 34]  # Pages 33-35 in PDF

# Ground truth for validation (manually verified from NBC)
GROUND_TRUTH = {
    "1.3.3.3": {
        "title": "Application of Parts 9, 10 and 11",
        "key_requirements": [
            "3 storeys or less in building height",
            "building area not exceeding 600 m²",
            "Group B, Division 4, home-type care occupancies",
            "Group C, residential occupancies",
            "Group D, business and personal services occupancies",
            "Group E, mercantile occupancies",
            "Group F, Divisions 2 and 3, medium- and low-hazard industrial occupancies",
        ],
        "numeric_values": {
            "max_storeys": 3,
            "max_building_area_m2": 600,
            "part_10_1storey_no_sleeping": 1200,
            "part_10_1storey_sleeping": 600,
            "part_10_1storey_sprinklered_no_sleeping": 2400,
            "part_10_1storey_sprinklered_sleeping": 1200,
        }
    }
}


@dataclass
class ExtractionResult:
    method: str
    time_seconds: float
    article_number: str
    title: str
    full_text: str
    subsections: List[Dict]
    numeric_values: Dict[str, Any]
    quality_score: float
    issues: List[str]


def fix_spacing(text: str) -> str:
    """Fix common spacing issues in PDF extracted text."""
    if not text:
        return ""

    # Fix camelCase-like joined words (lowercase followed by uppercase)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

    # Fix specific patterns
    patterns = [
        (r'(\d+)m2', r'\1 m²'),
        (r'(\d+)m(?!\d)', r'\1 m'),
        (r'storeys', r'storeys'),
        (r'Part(\d+)', r'Part \1'),
        (r'Group([A-F])', r'Group \1'),
        (r'Division(\d+)', r'Division \1'),
        (r'Article(\d)', r'Article \1'),
        (r'Sentence\(', r'Sentence ('),
    ]

    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)

    # Normalize multiple spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def extract_with_pdfplumber(pages: List[int]) -> ExtractionResult:
    """Extract using pdfplumber library."""
    start = time.time()
    issues = []

    all_text = []
    with pdfplumber.open(PDF_PATH) as pdf:
        for page_num in pages:
            if page_num < len(pdf.pages):
                page = pdf.pages[page_num]
                text = page.extract_text()
                if text:
                    all_text.append(f"--- Page {page_num + 1} ---\n{text}")

    raw_text = "\n\n".join(all_text)

    # Extract article 1.3.3.3
    article_match = re.search(
        r'1\.3\.3\.3\.\s*Application of Parts 9,\s*10 and 11(.*?)(?=1\.3\.3\.4\.|$)',
        raw_text.replace('\n', ' '),
        re.DOTALL | re.IGNORECASE
    )

    article_text = ""
    title = "Application of Parts 9, 10 and 11"
    if article_match:
        article_text = fix_spacing(article_match.group(1))
    else:
        issues.append("Could not locate Article 1.3.3.3 in text")
        article_text = fix_spacing(raw_text)

    # Extract subsections
    subsections = []
    sentence_matches = re.findall(r'(\d+)\)\s*([^()]+?)(?=\d+\)|$)', article_text)
    for num, content in sentence_matches:
        subsections.append({"sentence": int(num), "content": content.strip()[:500]})

    # Extract numeric values
    numeric_values = {}

    # Try to find key numeric values
    storey_match = re.search(r'(\d+)\s*storey', article_text, re.IGNORECASE)
    if storey_match:
        numeric_values["max_storeys"] = int(storey_match.group(1))

    area_matches = re.findall(r'(\d+)\s*m[²2]', article_text)
    if area_matches:
        numeric_values["building_areas_m2"] = [int(x) for x in area_matches]

    elapsed = time.time() - start

    # Calculate quality score
    quality = calculate_quality_score(article_text, numeric_values, subsections, "1.3.3.3")

    return ExtractionResult(
        method="pdfplumber",
        time_seconds=round(elapsed, 3),
        article_number="1.3.3.3",
        title=title,
        full_text=article_text,
        subsections=subsections,
        numeric_values=numeric_values,
        quality_score=quality,
        issues=issues
    )


def extract_with_pymupdf(pages: List[int]) -> ExtractionResult:
    """Extract using PyMuPDF with text extraction."""
    start = time.time()
    issues = []

    all_text = []
    doc = fitz.open(PDF_PATH)

    for page_num in pages:
        if page_num < len(doc):
            page = doc[page_num]
            # Use "text" mode for better layout preservation
            text = page.get_text("text")
            if text:
                all_text.append(f"--- Page {page_num + 1} ---\n{text}")

    doc.close()

    raw_text = "\n\n".join(all_text)

    # Extract article 1.3.3.3
    article_match = re.search(
        r'1\.3\.3\.3\.\s*Application of Parts 9,?\s*10 and 11(.*?)(?=1\.3\.3\.4\.|$)',
        raw_text.replace('\n', ' '),
        re.DOTALL | re.IGNORECASE
    )

    article_text = ""
    title = "Application of Parts 9, 10 and 11"
    if article_match:
        article_text = fix_spacing(article_match.group(1))
    else:
        issues.append("Could not locate Article 1.3.3.3 in text")
        article_text = fix_spacing(raw_text)

    # Extract subsections
    subsections = []
    sentence_matches = re.findall(r'(\d+)\)\s*([^()]+?)(?=\d+\)|$)', article_text)
    for num, content in sentence_matches:
        subsections.append({"sentence": int(num), "content": content.strip()[:500]})

    # Extract numeric values
    numeric_values = {}
    storey_match = re.search(r'(\d+)\s*storey', article_text, re.IGNORECASE)
    if storey_match:
        numeric_values["max_storeys"] = int(storey_match.group(1))

    area_matches = re.findall(r'(\d+)\s*m[²2]', article_text)
    if area_matches:
        numeric_values["building_areas_m2"] = [int(x) for x in area_matches]

    elapsed = time.time() - start
    quality = calculate_quality_score(article_text, numeric_values, subsections, "1.3.3.3")

    return ExtractionResult(
        method="pymupdf",
        time_seconds=round(elapsed, 3),
        article_number="1.3.3.3",
        title=title,
        full_text=article_text,
        subsections=subsections,
        numeric_values=numeric_values,
        quality_score=quality,
        issues=issues
    )


def extract_with_pymupdf_blocks(pages: List[int]) -> ExtractionResult:
    """Extract using PyMuPDF with block-level extraction for better structure."""
    start = time.time()
    issues = []

    all_text = []
    doc = fitz.open(PDF_PATH)

    for page_num in pages:
        if page_num < len(doc):
            page = doc[page_num]
            # Get text blocks with position info
            blocks = page.get_text("dict")["blocks"]
            page_text = []
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = " ".join([span["text"] for span in line["spans"]])
                        page_text.append(line_text)
            all_text.append(f"--- Page {page_num + 1} ---\n" + "\n".join(page_text))

    doc.close()

    raw_text = "\n\n".join(all_text)

    # Extract article 1.3.3.3
    article_match = re.search(
        r'1\.3\.3\.3\.\s*Application of Parts 9,?\s*10 and 11(.*?)(?=1\.3\.3\.4\.|$)',
        raw_text.replace('\n', ' '),
        re.DOTALL | re.IGNORECASE
    )

    article_text = ""
    title = "Application of Parts 9, 10 and 11"
    if article_match:
        article_text = fix_spacing(article_match.group(1))
    else:
        issues.append("Could not locate Article 1.3.3.3")
        article_text = fix_spacing(raw_text)

    subsections = []
    sentence_matches = re.findall(r'(\d+)\)\s*([^()]+?)(?=\d+\)|$)', article_text)
    for num, content in sentence_matches:
        subsections.append({"sentence": int(num), "content": content.strip()[:500]})

    numeric_values = {}
    storey_match = re.search(r'(\d+)\s*storey', article_text, re.IGNORECASE)
    if storey_match:
        numeric_values["max_storeys"] = int(storey_match.group(1))

    area_matches = re.findall(r'(\d+)\s*m[²2]', article_text)
    if area_matches:
        numeric_values["building_areas_m2"] = [int(x) for x in area_matches]

    elapsed = time.time() - start
    quality = calculate_quality_score(article_text, numeric_values, subsections, "1.3.3.3")

    return ExtractionResult(
        method="pymupdf_blocks",
        time_seconds=round(elapsed, 3),
        article_number="1.3.3.3",
        title=title,
        full_text=article_text,
        subsections=subsections,
        numeric_values=numeric_values,
        quality_score=quality,
        issues=issues
    )


def convert_pdf_page_to_image(page_num: int, dpi: int = 300) -> str:
    """Convert PDF page to base64-encoded image for VLM.

    Uses 300 DPI for optimal OCR quality as recommended for document extraction.
    """
    doc = fitz.open(PDF_PATH)
    page = doc[page_num]

    # Render at 300 DPI for optimal OCR (Qwen3-VL best practice)
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


def extract_with_vlm_qwen(pages: List[int]) -> ExtractionResult:
    """Extract using Qwen3 VL 30B via Ollama.

    Best practices from Qwen3-VL documentation:
    - Temperature: 0.7 for document extraction (balanced consistency)
    - Top_p: 0.8, Top_k: 20
    - 300 DPI for optimal OCR
    - Structured prompts for consistent JSON output
    """
    start = time.time()
    issues = []

    # Convert pages to images at 300 DPI for optimal OCR
    images_base64 = []
    for page_num in pages:
        try:
            img_b64 = convert_pdf_page_to_image(page_num, dpi=300)
            images_base64.append(img_b64)
            print(f"      Converted page {page_num + 1} to image")
        except Exception as e:
            issues.append(f"Failed to convert page {page_num}: {e}")

    if not images_base64:
        return ExtractionResult(
            method="vlm_qwen3vl_30b",
            time_seconds=time.time() - start,
            article_number="1.3.3.3",
            title="",
            full_text="",
            subsections=[],
            numeric_values={},
            quality_score=0.0,
            issues=["No images could be converted"]
        )

    # Optimized prompt for Qwen3-VL document extraction
    # Based on best practices: be specific, request structured output
    extraction_prompt = """Extract all text from this page of the National Building Code of Canada.

Focus specifically on Article 1.3.3.3 "Application of Parts 9, 10 and 11" which defines when Part 9 applies.

IMPORTANT: Transcribe the EXACT text verbatim, preserving all numbers, units (m², storeys), and formatting.

Return a JSON object:
{
    "article_number": "1.3.3.3",
    "title": "Application of Parts 9, 10 and 11",
    "sentences": [
        {"number": 1, "text": "exact verbatim text of sentence 1"},
        {"number": 2, "text": "exact verbatim text of sentence 2"},
        {"number": 3, "text": "exact verbatim text of sentence 3"},
        {"number": 4, "text": "exact verbatim text of sentence 4"},
        {"number": 5, "text": "exact verbatim text of sentence 5"},
        {"number": 6, "text": "exact verbatim text of sentence 6"}
    ],
    "key_values": {
        "part_9_max_storeys": 3,
        "part_9_max_building_area_m2": 600,
        "part_10_1storey_no_sleeping_m2": 1200,
        "part_10_1storey_sleeping_m2": 600,
        "applicable_groups": ["B Division 4", "C", "D", "E", "F Divisions 2 and 3"]
    },
    "full_text": "complete verbatim text of the entire article 1.3.3.3"
}

Be extremely precise with all numeric values. Do not paraphrase - copy exact text."""

    try:
        # Call Ollama API with optimized Qwen3-VL parameters
        # Using /api/chat for better multimodal handling
        print("      Sending to Qwen3-VL (this may take 2-5 minutes)...")

        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "qwen3-vl:30b",
                "messages": [
                    {
                        "role": "user",
                        "content": extraction_prompt,
                        "images": images_base64
                    }
                ],
                "stream": False,
                "options": {
                    # Optimal parameters for document extraction (per Qwen3-VL docs)
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 20,
                    "num_predict": 8192,  # Allow longer responses for full extraction
                }
            },
            timeout=600  # 10 minutes for large model
        )

        if response.status_code != 200:
            issues.append(f"Ollama API error: {response.status_code}")
            return ExtractionResult(
                method="vlm_qwen3vl_30b",
                time_seconds=time.time() - start,
                article_number="1.3.3.3",
                title="",
                full_text="",
                subsections=[],
                numeric_values={},
                quality_score=0.0,
                issues=issues
            )

        result = response.json()
        # /api/chat returns response in message.content
        raw_response = result.get("message", {}).get("content", "")
        if not raw_response:
            # Fallback for /api/generate format
            raw_response = result.get("response", "")

        print(f"      Received response ({len(raw_response)} chars)")

        # Try to parse JSON from response
        try:
            # Find JSON in response
            json_match = re.search(r'\{[\s\S]*\}', raw_response)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                parsed = {"full_text": raw_response}
        except json.JSONDecodeError:
            parsed = {"full_text": raw_response}
            issues.append("Could not parse JSON response")

        article_text = parsed.get("full_text", raw_response)
        title = parsed.get("title", "Application of Parts 9, 10 and 11")

        # Extract subsections
        subsections = []
        if "sentences" in parsed:
            for s in parsed["sentences"]:
                subsections.append({
                    "sentence": s.get("number", 0),
                    "content": s.get("text", "")[:500]
                })

        # Extract numeric values from parsed JSON
        numeric_values = {}

        # Try key_values structure (new format)
        if "key_values" in parsed:
            kv = parsed["key_values"]
            if "part_9_max_storeys" in kv:
                numeric_values["max_storeys"] = kv["part_9_max_storeys"]
            if "part_9_max_building_area_m2" in kv:
                numeric_values["max_building_area_m2"] = kv["part_9_max_building_area_m2"]
            if "part_10_1storey_no_sleeping_m2" in kv:
                numeric_values["part_10_1storey_no_sleeping_m2"] = kv["part_10_1storey_no_sleeping_m2"]
            if "part_10_1storey_sleeping_m2" in kv:
                numeric_values["part_10_1storey_sleeping_m2"] = kv["part_10_1storey_sleeping_m2"]

        # Fallback to key_requirements structure (old format)
        elif "key_requirements" in parsed:
            kr = parsed["key_requirements"]
            if "part_9" in kr:
                if "max_storeys" in kr["part_9"]:
                    numeric_values["max_storeys"] = kr["part_9"]["max_storeys"]
                if "max_building_area_m2" in kr["part_9"]:
                    numeric_values["max_building_area_m2"] = kr["part_9"]["max_building_area_m2"]

        # Fallback extraction from text
        if not numeric_values:
            storey_match = re.search(r'(\d+)\s*storey', article_text, re.IGNORECASE)
            if storey_match:
                numeric_values["max_storeys"] = int(storey_match.group(1))

            area_matches = re.findall(r'(\d+)\s*m[²2]', article_text)
            if area_matches:
                numeric_values["building_areas_m2"] = [int(x) for x in area_matches]

        elapsed = time.time() - start
        quality = calculate_quality_score(article_text, numeric_values, subsections, "1.3.3.3")

        return ExtractionResult(
            method="vlm_qwen3vl_30b",
            time_seconds=round(elapsed, 3),
            article_number="1.3.3.3",
            title=title,
            full_text=article_text,
            subsections=subsections,
            numeric_values=numeric_values,
            quality_score=quality,
            issues=issues
        )

    except requests.exceptions.Timeout:
        issues.append("Ollama request timed out (300s)")
    except requests.exceptions.ConnectionError:
        issues.append("Could not connect to Ollama - is it running?")
    except Exception as e:
        issues.append(f"VLM extraction error: {str(e)}")

    return ExtractionResult(
        method="vlm_qwen3vl_30b",
        time_seconds=time.time() - start,
        article_number="1.3.3.3",
        title="",
        full_text="",
        subsections=[],
        numeric_values={},
        quality_score=0.0,
        issues=issues
    )


def calculate_quality_score(text: str, numeric_values: Dict, subsections: List, article_num: str) -> float:
    """Calculate quality score based on ground truth comparison."""
    if article_num not in GROUND_TRUTH:
        return 0.0

    gt = GROUND_TRUTH[article_num]
    score = 0.0
    max_score = 100.0

    # 1. Text completeness (30 points)
    if len(text) > 500:
        score += 15
    if len(text) > 1000:
        score += 10
    if len(text) > 1500:
        score += 5

    # 2. Key requirements found (30 points)
    requirements_found = 0
    for req in gt["key_requirements"]:
        # Normalize for comparison
        req_normalized = req.lower().replace("²", "2").replace(" ", "")
        text_normalized = text.lower().replace("²", "2").replace(" ", "")
        if req_normalized in text_normalized:
            requirements_found += 1

    req_score = (requirements_found / len(gt["key_requirements"])) * 30
    score += req_score

    # 3. Numeric values accuracy (25 points)
    gt_nums = gt["numeric_values"]
    nums_correct = 0
    nums_total = len(gt_nums)

    if "max_storeys" in numeric_values:
        if numeric_values["max_storeys"] == gt_nums["max_storeys"]:
            nums_correct += 1

    if "max_building_area_m2" in numeric_values:
        if numeric_values["max_building_area_m2"] == gt_nums["max_building_area_m2"]:
            nums_correct += 1
    elif "building_areas_m2" in numeric_values:
        if gt_nums["max_building_area_m2"] in numeric_values["building_areas_m2"]:
            nums_correct += 1

    # Check for Part 10 values
    if "building_areas_m2" in numeric_values:
        expected_areas = [600, 1200, 2400, 300]
        for exp in expected_areas:
            if exp in numeric_values["building_areas_m2"]:
                nums_correct += 0.5

    num_score = min(25, (nums_correct / max(nums_total, 1)) * 25)
    score += num_score

    # 4. Structure extraction (15 points)
    if len(subsections) >= 3:
        score += 10
    elif len(subsections) >= 1:
        score += 5

    # Check for proper sentence structure
    if subsections and all("sentence" in s for s in subsections):
        score += 5

    return round(min(score, max_score), 2)


def analyze_text_quality(text: str) -> Dict:
    """Analyze text quality metrics."""
    if not text:
        return {"word_count": 0, "spacing_issues": 0, "readability": 0}

    # Count words
    words = text.split()
    word_count = len(words)

    # Detect spacing issues (joined words)
    joined_pattern = re.compile(r'[a-z][A-Z]')
    spacing_issues = len(joined_pattern.findall(text))

    # Basic readability - average word length
    avg_word_len = sum(len(w) for w in words) / max(len(words), 1)

    # Detect structural elements
    has_article_numbers = bool(re.search(r'\d+\.\d+\.\d+\.\d+', text))
    has_sentences = bool(re.search(r'\d+\)\s', text))
    has_groups = bool(re.search(r'Group\s*[A-F]', text))

    return {
        "word_count": word_count,
        "char_count": len(text),
        "spacing_issues": spacing_issues,
        "avg_word_length": round(avg_word_len, 2),
        "has_article_structure": has_article_numbers,
        "has_sentence_structure": has_sentences,
        "has_group_references": has_groups,
    }


def run_comparison():
    """Run full comparison of extraction methods."""
    print("=" * 70)
    print("NBC PART 9 SCOPE EXTRACTION COMPARISON")
    print("Target: Article 1.3.3.3 - Application of Parts 9, 10 and 11")
    print("=" * 70)

    results = []

    # Pythonic methods
    print("\n[1/4] Extracting with pdfplumber...")
    result_pdfplumber = extract_with_pdfplumber(TARGET_PAGES)
    results.append(result_pdfplumber)
    print(f"      Done in {result_pdfplumber.time_seconds}s, quality: {result_pdfplumber.quality_score}")

    print("\n[2/4] Extracting with PyMuPDF (text mode)...")
    result_pymupdf = extract_with_pymupdf(TARGET_PAGES)
    results.append(result_pymupdf)
    print(f"      Done in {result_pymupdf.time_seconds}s, quality: {result_pymupdf.quality_score}")

    print("\n[3/4] Extracting with PyMuPDF (blocks mode)...")
    result_blocks = extract_with_pymupdf_blocks(TARGET_PAGES)
    results.append(result_blocks)
    print(f"      Done in {result_blocks.time_seconds}s, quality: {result_blocks.quality_score}")

    # VLM method
    print("\n[4/4] Extracting with VLM (Qwen3 VL 30B)...")
    print("      This may take 2-5 minutes...")
    result_vlm = extract_with_vlm_qwen(TARGET_PAGES)
    results.append(result_vlm)
    print(f"      Done in {result_vlm.time_seconds}s, quality: {result_vlm.quality_score}")

    # Analyze results
    print("\n" + "=" * 70)
    print("EXTRACTION COMPARISON RESULTS")
    print("=" * 70)

    comparison = {
        "timestamp": datetime.now().isoformat(),
        "target_article": "1.3.3.3",
        "target_pages": [p + 1 for p in TARGET_PAGES],
        "ground_truth": GROUND_TRUTH["1.3.3.3"],
        "results": [],
        "rankings": [],
    }

    for result in results:
        text_quality = analyze_text_quality(result.full_text)

        result_data = {
            "method": result.method,
            "time_seconds": result.time_seconds,
            "quality_score": result.quality_score,
            "text_metrics": text_quality,
            "subsections_found": len(result.subsections),
            "numeric_values_found": len(result.numeric_values),
            "issues": result.issues,
        }
        comparison["results"].append(result_data)

        print(f"\n{result.method.upper()}")
        print("-" * 40)
        print(f"  Time: {result.time_seconds}s")
        print(f"  Quality Score: {result.quality_score}/100")
        print(f"  Text Length: {text_quality['char_count']} chars, {text_quality['word_count']} words")
        print(f"  Spacing Issues: {text_quality['spacing_issues']}")
        print(f"  Subsections Found: {len(result.subsections)}")
        print(f"  Numeric Values: {result.numeric_values}")
        if result.issues:
            print(f"  Issues: {result.issues}")

    # Rank by quality score
    ranked = sorted(results, key=lambda x: x.quality_score, reverse=True)
    comparison["rankings"] = [
        {"rank": i+1, "method": r.method, "score": r.quality_score}
        for i, r in enumerate(ranked)
    ]

    print("\n" + "=" * 70)
    print("FINAL RANKINGS")
    print("=" * 70)
    for i, r in enumerate(ranked, 1):
        print(f"  #{i}: {r.method} (Score: {r.quality_score}, Time: {r.time_seconds}s)")

    winner = ranked[0]
    print(f"\n  WINNER: {winner.method.upper()}")
    print(f"  Best Quality Score: {winner.quality_score}/100")

    # Speed vs Quality analysis
    fastest = min(results, key=lambda x: x.time_seconds)
    print(f"\n  FASTEST: {fastest.method} ({fastest.time_seconds}s)")

    # Calculate speed-quality ratio
    for r in results:
        if r.time_seconds > 0:
            sqr = r.quality_score / r.time_seconds
            print(f"  {r.method}: Speed-Quality Ratio = {sqr:.2f}")

    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save comparison summary
    summary_path = OUTPUT_DIR / f"comparison_summary_{timestamp}.json"
    with open(summary_path, 'w') as f:
        json.dump(comparison, f, indent=2)
    print(f"\nSaved comparison summary: {summary_path}")

    # Save individual results with full text
    for result in results:
        result_path = OUTPUT_DIR / f"{result.method}_extraction_{timestamp}.json"
        with open(result_path, 'w') as f:
            json.dump(asdict(result), f, indent=2, default=str)

    print(f"Saved individual results to: {OUTPUT_DIR}")

    return comparison


if __name__ == "__main__":
    comparison = run_comparison()
