#!/usr/bin/env python3
"""
Extract STANDATA bulletins from PDF files to JSON format.

This script:
1. Scans the STANDATA directory for PDF files
2. Extracts text content using PyMuPDF (fitz)
3. Parses bulletin number, title, and content
4. Identifies NBC code references
5. Generates keywords from content
6. Saves to JSON files
"""

import json
import re
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

try:
    import fitz  # PyMuPDF
except ImportError:
    print("PyMuPDF not installed. Please install with: pip install PyMuPDF")
    sys.exit(1)

# Base paths
BASE_DIR = Path("/Users/mohmmadhanafy/Building-code-consultant")
STANDATA_DIR = BASE_DIR / "data" / "standata"
OUTPUT_DIR = BASE_DIR / "data" / "codes"

# Regular expressions for parsing
BULLETIN_NUMBER_PATTERN = re.compile(r'(\d{2})-([A-Z]{2,3})-(\d{3})', re.IGNORECASE)
CODE_REFERENCE_PATTERN = re.compile(
    r'(?:Article\s+)?(\d{1,2}\.\d{1,2}\.\d{1,2}(?:\.\d{1,2})?)',
    re.IGNORECASE
)

# Common keywords to extract
KEYWORD_PATTERNS = {
    'egress': re.compile(r'\begress\b', re.IGNORECASE),
    'fire separation': re.compile(r'fire\s+separation', re.IGNORECASE),
    'fire rating': re.compile(r'fire\s+rating', re.IGNORECASE),
    'sprinkler': re.compile(r'\bsprinkler[s]?\b', re.IGNORECASE),
    'smoke alarm': re.compile(r'smoke\s+alarm[s]?', re.IGNORECASE),
    'secondary suite': re.compile(r'secondary\s+suite[s]?', re.IGNORECASE),
    'stairway': re.compile(r'\bstair(?:way|s)?\b', re.IGNORECASE),
    'occupancy': re.compile(r'\boccupancy\b', re.IGNORECASE),
    'combustible': re.compile(r'\bcombustible\b', re.IGNORECASE),
    'energy efficiency': re.compile(r'energy\s+efficienc', re.IGNORECASE),
    'insulation': re.compile(r'\binsulation\b', re.IGNORECASE),
    'ventilation': re.compile(r'\bventilation\b', re.IGNORECASE),
    'radon': re.compile(r'\bradon\b', re.IGNORECASE),
    'roof truss': re.compile(r'roof\s+truss', re.IGNORECASE),
    'standpipe': re.compile(r'\bstandpipe\b', re.IGNORECASE),
    'plumbing': re.compile(r'\bplumbing\b', re.IGNORECASE),
    'drainage': re.compile(r'\bdrainage\b', re.IGNORECASE),
    'venting': re.compile(r'\bventing\b', re.IGNORECASE),
    'fixture': re.compile(r'\bfixture[s]?\b', re.IGNORECASE),
    'water supply': re.compile(r'water\s+supply', re.IGNORECASE),
    'smoke damper': re.compile(r'smoke\s+damper', re.IGNORECASE),
    'spray booth': re.compile(r'spray\s+booth', re.IGNORECASE),
    'antifreeze': re.compile(r'\bantifreeze\b', re.IGNORECASE),
    'HVAC': re.compile(r'\bHVAC\b', re.IGNORECASE),
    'SEER': re.compile(r'\bSEER\b', re.IGNORECASE),
}


def extract_text_from_pdf(pdf_path: Path) -> Tuple[str, str, int]:
    """Extract text from a PDF file using PyMuPDF."""
    try:
        doc = fitz.open(str(pdf_path))
        full_text = ""
        num_pages = len(doc)

        for page_num in range(num_pages):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            full_text += text + "\n\n"

        doc.close()

        # Assess extraction confidence
        if len(full_text.strip()) < 100:
            confidence = "LOW"
        elif len(full_text.strip()) < 500:
            confidence = "MEDIUM"
        else:
            confidence = "HIGH"

        return full_text.strip(), confidence, num_pages

    except Exception as e:
        print(f"  Error extracting text: {e}")
        return "", "LOW", 0


def parse_bulletin_number(filename: str, text: str) -> Tuple[str, str]:
    """Parse bulletin number and category from filename or text."""
    match = BULLETIN_NUMBER_PATTERN.search(filename)
    if match:
        year, category, number = match.groups()
        return f"{year}-{category.upper()}-{number}", category.upper()

    match = BULLETIN_NUMBER_PATTERN.search(text)
    if match:
        year, category, number = match.groups()
        return f"{year}-{category.upper()}-{number}", category.upper()

    basename = Path(filename).stem.upper().replace("_", "-").replace(" ", "-")
    for cat in ['BCI', 'BCB', 'FCB', 'PCB']:
        if cat in basename:
            return basename, cat

    return basename, "BCI"


def extract_title(text: str, bulletin_number: str) -> str:
    """Extract the title from the bulletin text."""
    lines = text.split('\n')

    for line in lines[:30]:
        line = line.strip()
        if not line or len(line) < 10:
            continue
        if bulletin_number in line:
            continue
        if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', line):
            continue
        if 'STANDATA' in line.upper() or 'ALBERTA' in line.upper():
            continue

        if 20 < len(line) < 200:
            return re.sub(r'[:\.]$', '', line).strip()

    for line in lines[:20]:
        line = line.strip()
        if len(line) > 20 and bulletin_number not in line:
            return line[:200]

    return f"STANDATA Bulletin {bulletin_number}"


def extract_summary(text: str, max_length: int = 500) -> str:
    """Extract a summary from the bulletin text."""
    paragraphs = text.split('\n\n')

    for para in paragraphs:
        para = para.strip()
        if len(para) < 50 or para.upper() == para:
            continue

        if len(para) > max_length:
            sentences = re.split(r'(?<=[.!?])\s+', para)
            summary = ""
            for sent in sentences:
                if len(summary) + len(sent) < max_length:
                    summary += sent + " "
                else:
                    break
            return summary.strip() + "..."

        return para

    return text[:max_length].strip() + "..."


def extract_code_references(text: str) -> List[str]:
    """Extract NBC code article references from the text."""
    matches = CODE_REFERENCE_PATTERN.findall(text)
    unique_refs = list(set(matches))

    valid_refs = []
    for ref in unique_refs:
        parts = ref.split('.')
        if parts[0].isdigit() and 1 <= int(parts[0]) <= 11:
            valid_refs.append(ref)

    return sorted(valid_refs)


def extract_keywords(text: str) -> List[str]:
    """Extract relevant keywords from the text."""
    keywords = []
    for keyword, pattern in KEYWORD_PATTERNS.items():
        if pattern.search(text):
            keywords.append(keyword)
    return sorted(keywords)


def extract_effective_date(text: str) -> Optional[str]:
    """Try to extract the effective date from the bulletin."""
    patterns = [
        re.compile(r'(?:Effective|Date)[:\s]+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})', re.IGNORECASE),
        re.compile(r'(\d{1,2}/\d{1,2}/\d{4})'),
        re.compile(r'([A-Z][a-z]+\s+\d{4})'),
    ]

    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match.group(1)

    return None


def find_pdf_files(standata_dir: Path) -> List[Path]:
    """Find all PDF files in the STANDATA directory and subdirectories."""
    pdf_files = list(standata_dir.glob("*.pdf"))
    for subdir in standata_dir.iterdir():
        if subdir.is_dir():
            pdf_files.extend(subdir.glob("*.pdf"))
    return sorted(pdf_files)


def process_pdf_file(pdf_path: Path) -> Optional[Dict[str, Any]]:
    """Process a single PDF file and extract all relevant data."""
    print(f"  Processing: {pdf_path.name}")

    full_text, confidence, num_pages = extract_text_from_pdf(pdf_path)
    if not full_text:
        print(f"    No text extracted")
        return None

    bulletin_number, category = parse_bulletin_number(pdf_path.name, full_text)
    title = extract_title(full_text, bulletin_number)
    summary = extract_summary(full_text)
    code_refs = extract_code_references(full_text)
    keywords = extract_keywords(full_text)
    effective_date = extract_effective_date(full_text)

    # Determine subdirectory
    rel_path = pdf_path.relative_to(STANDATA_DIR)
    subdir = str(rel_path.parent) if rel_path.parent != Path('.') else None

    return {
        'bulletin_number': bulletin_number,
        'title': title,
        'category': category,
        'subcategory': subdir,
        'effective_date': effective_date,
        'summary': summary,
        'full_text': full_text,
        'code_references': code_refs,
        'keywords': keywords,
        'pdf_filename': pdf_path.name,
        'num_pages': num_pages,
        'extraction_confidence': confidence,
    }


def main():
    print("=" * 60)
    print("STANDATA Bulletin Extraction")
    print("=" * 60)

    if not STANDATA_DIR.exists():
        print(f"ERROR: STANDATA directory not found: {STANDATA_DIR}")
        sys.exit(1)

    pdf_files = find_pdf_files(STANDATA_DIR)
    print(f"\nFound {len(pdf_files)} PDF files")

    all_bulletins = {
        "metadata": {
            "source": "Alberta STANDATA Bulletins",
            "extraction_date": str(date.today()),
            "extraction_method": "PyMuPDF",
            "total_bulletins": 0
        },
        "categories": {
            "BCI": {"name": "Building Code Interpretations", "bulletins": []},
            "BCB": {"name": "Building Code Bulletins", "bulletins": []},
            "FCB": {"name": "Fire Code Bulletins", "bulletins": []},
            "PCB": {"name": "Plumbing Code Bulletins", "bulletins": []},
        },
        "all_bulletins": []
    }

    success_count = 0
    error_count = 0

    for pdf_path in pdf_files:
        try:
            data = process_pdf_file(pdf_path)
            if data:
                all_bulletins["all_bulletins"].append(data)
                category = data["category"]
                if category in all_bulletins["categories"]:
                    all_bulletins["categories"][category]["bulletins"].append({
                        "bulletin_number": data["bulletin_number"],
                        "title": data["title"],
                        "keywords": data["keywords"],
                        "code_references": data["code_references"],
                    })
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            print(f"    Error: {e}")
            error_count += 1

    all_bulletins["metadata"]["total_bulletins"] = success_count

    # Save results
    output_path = OUTPUT_DIR / "standata_bulletins.json"
    with open(output_path, 'w') as f:
        json.dump(all_bulletins, f, indent=2)

    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"Successful: {success_count}")
    print(f"Errors: {error_count}")
    print(f"\nBy Category:")
    for cat_id, cat_data in all_bulletins["categories"].items():
        count = len(cat_data["bulletins"])
        if count > 0:
            print(f"  {cat_id} ({cat_data['name']}): {count}")

    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()
