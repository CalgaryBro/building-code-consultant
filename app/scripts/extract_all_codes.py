#!/usr/bin/env python3
"""
Comprehensive Code Extraction Script

Extracts structured data from:
1. NECB-2020 (National Energy Code of Canada for Buildings)
2. NFC-AE-2023 (National Fire Code - Alberta Edition)
3. NPC-2020 (National Plumbing Code of Canada)
4. Land Use Bylaw 1P2007 (Calgary)

Usage:
    python extract_all_codes.py --code necb
    python extract_all_codes.py --code nfc
    python extract_all_codes.py --code npc
    python extract_all_codes.py --code bylaw
    python extract_all_codes.py --all
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pdfplumber

# Base paths
BASE_DIR = Path("/Users/mohmmadhanafy/Building-code-consultant")
CODES_DIR = BASE_DIR / "data" / "codes"
BYLAWS_DIR = BASE_DIR / "data" / "bylaws"
OUTPUT_DIR = BASE_DIR / "data" / "codes"

# Code configurations
CODE_CONFIGS = {
    "necb": {
        "pdf_path": CODES_DIR / "NECB-2020.pdf",
        "full_name": "National Energy Code of Canada for Buildings 2020",
        "short_name": "NECB 2020",
        "output_prefix": "necb_2020",
        "division_pattern": r"Division\s+([A-C])\.",
        "part_pattern": r"Part\s+(\d+)\.",
        "section_pattern": r"Section\s+(\d+\.\d+)\.",
        "article_pattern": r"(\d+\.\d+\.\d+\.\d+)",
    },
    "nfc": {
        "pdf_path": CODES_DIR / "NFC-AE-2023.pdf",
        "full_name": "National Fire Code - 2023 Alberta Edition",
        "short_name": "NFC(AE) 2023",
        "output_prefix": "nfc_ae_2023",
        "division_pattern": r"Division\s+([A-C])\.",
        "part_pattern": r"Part\s+(\d+)\.",
        "section_pattern": r"Section\s+(\d+\.\d+)\.",
        "article_pattern": r"(\d+\.\d+\.\d+\.\d+)",
    },
    "npc": {
        "pdf_path": CODES_DIR / "NPC-2020.pdf",
        "full_name": "National Plumbing Code of Canada 2020",
        "short_name": "NPC 2020",
        "output_prefix": "npc_2020",
        "division_pattern": r"Division\s+([A-C])\.",
        "part_pattern": r"Part\s+(\d+)\.",
        "section_pattern": r"Section\s+(\d+\.\d+)\.",
        "article_pattern": r"(\d+\.\d+\.\d+\.\d+)",
    },
    "bylaw": {
        "pdf_path": BYLAWS_DIR / "land-use-bylaw-1p2007-amended-2025-01-01.pdf",
        "full_name": "City of Calgary Land Use Bylaw 1P2007",
        "short_name": "LUB 1P2007",
        "output_prefix": "land_use_bylaw",
        "part_pattern": r"Part\s+(\d+)",
        "division_pattern": r"Division\s+(\d+)",
        "section_pattern": r"(\d+)\s+[A-Z]",
    },
}


def clean_text(text: str) -> str:
    """Clean extracted text by fixing common issues."""
    if not text:
        return ""
    # Fix joined words
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_toc(pdf, max_pages: int = 20) -> Dict[str, List[str]]:
    """Extract table of contents from first pages."""
    toc = {"divisions": [], "parts": [], "sections": []}

    for page_num in range(min(max_pages, len(pdf.pages))):
        text = pdf.pages[page_num].extract_text()
        if not text:
            continue

        # Look for Division headers
        divisions = re.findall(r"Division\s+([A-C])\s*[–-]\s*(.+?)(?:\n|\d)", text)
        for div_id, div_name in divisions:
            toc["divisions"].append({"id": div_id, "name": clean_text(div_name)})

        # Look for Part headers
        parts = re.findall(r"Part\s+(\d+)\s*[–-]\s*(.+?)(?:\n|\d)", text)
        for part_id, part_name in parts:
            toc["parts"].append({"id": part_id, "name": clean_text(part_name)})

    return toc


def extract_division_content(pdf, division_id: str, config: Dict) -> Dict:
    """Extract all content from a specific division."""
    division_content = {
        "division_id": division_id,
        "parts": [],
        "raw_text": ""
    }

    in_division = False
    current_text = []

    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text()
        if not text:
            continue

        # Check if we're entering this division
        if f"Division {division_id}" in text:
            in_division = True

        # Check if we've moved to next division
        next_div = chr(ord(division_id) + 1)
        if in_division and f"Division {next_div}" in text:
            break

        if in_division:
            current_text.append(text)

    division_content["raw_text"] = "\n\n".join(current_text)
    return division_content


def extract_part_content(pdf, part_num: int, config: Dict, start_page: int = 0) -> Tuple[Dict, int]:
    """Extract content from a specific Part, returning content and last page."""
    part_content = {
        "part_number": part_num,
        "sections": [],
        "articles": [],
        "raw_text": "",
        "pages": []
    }

    in_part = False
    current_text = []
    last_page = start_page

    for page_num in range(start_page, len(pdf.pages)):
        page = pdf.pages[page_num]
        text = page.extract_text()
        if not text:
            continue

        # Check if we're entering this part
        part_marker = f"Part {part_num}"
        if part_marker in text and not in_part:
            in_part = True
            part_content["pages"].append(page_num + 1)

        # Check if we've moved to next part
        next_part_marker = f"Part {part_num + 1}"
        if in_part and next_part_marker in text and page_num > start_page + 2:
            last_page = page_num
            break

        if in_part:
            current_text.append(text)
            last_page = page_num

    part_content["raw_text"] = "\n\n".join(current_text)

    # Extract articles from this part
    article_pattern = config.get("article_pattern", r"(\d+\.\d+\.\d+\.\d+)")
    articles = re.findall(article_pattern, part_content["raw_text"])
    part_content["articles"] = list(set(articles))

    return part_content, last_page


def extract_articles_with_context(text: str, article_pattern: str) -> List[Dict]:
    """Extract articles with their surrounding context."""
    articles = []
    pattern = re.compile(rf'({article_pattern})\.\s*([A-Z][^.]+?)\n(.*?)(?=\d+\.\d+\.\d+\.\d+\.|$)', re.DOTALL)

    for match in pattern.finditer(text):
        article_num = match.group(1)
        title = clean_text(match.group(2))
        content = clean_text(match.group(3))

        articles.append({
            "article_number": article_num,
            "title": title[:100] if title else "",
            "full_text": content[:2000] if content else "",
        })

    return articles


def extract_necb(config: Dict, verbose: bool = False) -> Dict:
    """Extract NECB 2020 (Energy Code)."""
    print("=" * 60)
    print("Extracting NECB 2020 - National Energy Code")
    print("=" * 60)

    result = {
        "metadata": {
            "code": config["full_name"],
            "short_name": config["short_name"],
            "extraction_date": str(date.today()),
            "extraction_method": "pdfplumber",
            "verification_status": "pending_professional_review"
        },
        "divisions": [],
        "parts": [],
        "summary": {}
    }

    with pdfplumber.open(config["pdf_path"]) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages: {total_pages}")

        # Extract TOC
        toc = extract_toc(pdf)
        result["metadata"]["toc"] = toc

        # NECB has 3 Divisions: A (Compliance), B (Acceptable Solutions), C (Administrative)
        # Division B contains the prescriptive requirements

        # Extract each major part
        parts_to_extract = [
            (3, "Building Envelope"),
            (4, "Lighting"),
            (5, "HVAC"),
            (6, "Service Water Heating"),
            (7, "Electrical Power"),
            (8, "Building Energy Performance")
        ]

        current_page = 0
        for part_num, part_name in parts_to_extract:
            print(f"\nExtracting Part {part_num}: {part_name}...")
            part_data, current_page = extract_part_content(pdf, part_num, config, current_page)
            part_data["name"] = part_name
            result["parts"].append(part_data)
            print(f"  Found {len(part_data['articles'])} articles")

        result["summary"] = {
            "total_parts": len(result["parts"]),
            "total_articles": sum(len(p["articles"]) for p in result["parts"])
        }

    return result


def extract_nfc(config: Dict, verbose: bool = False) -> Dict:
    """Extract NFC-AE 2023 (Fire Code)."""
    print("=" * 60)
    print("Extracting NFC-AE 2023 - National Fire Code")
    print("=" * 60)

    result = {
        "metadata": {
            "code": config["full_name"],
            "short_name": config["short_name"],
            "extraction_date": str(date.today()),
            "extraction_method": "pdfplumber",
            "verification_status": "pending_professional_review"
        },
        "divisions": [],
        "parts": [],
        "summary": {}
    }

    with pdfplumber.open(config["pdf_path"]) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages: {total_pages}")

        # NFC Parts of interest
        parts_to_extract = [
            (1, "General"),
            (2, "General Requirements"),
            (3, "Indoor and Outdoor Storage"),
            (4, "Flammable and Combustible Liquids"),
            (5, "Processes and Operations"),
            (6, "Petroleum and Natural Gas"),
            (7, "Fire Safety in Buildings"),
            (8, "Emergency Planning"),
        ]

        current_page = 0
        for part_num, part_name in parts_to_extract:
            print(f"\nExtracting Part {part_num}: {part_name}...")
            part_data, current_page = extract_part_content(pdf, part_num, config, current_page)
            part_data["name"] = part_name
            result["parts"].append(part_data)
            print(f"  Found {len(part_data['articles'])} articles")

        result["summary"] = {
            "total_parts": len(result["parts"]),
            "total_articles": sum(len(p["articles"]) for p in result["parts"])
        }

    return result


def extract_npc(config: Dict, verbose: bool = False) -> Dict:
    """Extract NPC 2020 (Plumbing Code)."""
    print("=" * 60)
    print("Extracting NPC 2020 - National Plumbing Code")
    print("=" * 60)

    result = {
        "metadata": {
            "code": config["full_name"],
            "short_name": config["short_name"],
            "extraction_date": str(date.today()),
            "extraction_method": "pdfplumber",
            "verification_status": "pending_professional_review"
        },
        "divisions": [],
        "parts": [],
        "summary": {}
    }

    with pdfplumber.open(config["pdf_path"]) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages: {total_pages}")

        # NPC Parts
        parts_to_extract = [
            (1, "General"),
            (2, "Plumbing Systems"),
            (3, "Connected Piping"),
            (4, "Materials and Equipment"),
            (5, "Drains"),
            (6, "Venting"),
            (7, "Fixtures"),
        ]

        current_page = 0
        for part_num, part_name in parts_to_extract:
            print(f"\nExtracting Part {part_num}: {part_name}...")
            part_data, current_page = extract_part_content(pdf, part_num, config, current_page)
            part_data["name"] = part_name
            result["parts"].append(part_data)
            print(f"  Found {len(part_data['articles'])} articles")

        result["summary"] = {
            "total_parts": len(result["parts"]),
            "total_articles": sum(len(p["articles"]) for p in result["parts"])
        }

    return result


def extract_bylaw_districts(pdf, start_page: int, end_page: int) -> List[Dict]:
    """Extract land use district information from bylaw."""
    districts = []

    # Common district patterns in Calgary LUB
    district_patterns = [
        (r"(R-C\d[A-Z]?)\s+", "Residential - Contextual"),
        (r"(R-G\w+)\s+", "Residential - Grade-Oriented"),
        (r"(R-CG)\s+", "Residential - Contextual Grade-Oriented"),
        (r"(M-C\d)\s+", "Multi-Residential - Contextual"),
        (r"(M-G\w+)\s+", "Multi-Residential - Grade-Oriented"),
        (r"(M-X\d)\s+", "Multi-Residential - Mixed"),
        (r"(C-C\d)\s+", "Commercial - Community"),
        (r"(C-N\d)\s+", "Commercial - Neighbourhood"),
        (r"(C-COR\d)\s+", "Commercial - Core"),
        (r"(I-G)\s+", "Industrial - General"),
        (r"(I-B)\s+", "Industrial - Business"),
        (r"(S-\w+)\s+", "Special Purpose"),
    ]

    for page_num in range(start_page, min(end_page, len(pdf.pages))):
        text = pdf.pages[page_num].extract_text()
        if not text:
            continue

        for pattern, category in district_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match not in [d["code"] for d in districts]:
                    districts.append({
                        "code": match,
                        "category": category,
                        "page": page_num + 1
                    })

    return districts


def extract_bylaw_rules(text: str, district_code: str) -> List[Dict]:
    """Extract rules for a specific land use district."""
    rules = []

    # Common rule patterns
    rule_patterns = [
        (r"maximum.*?height.*?(\d+(?:\.\d+)?)\s*m", "max_height_m"),
        (r"maximum.*?(?:building\s+)?height.*?(\d+)\s*storey", "max_storeys"),
        (r"minimum.*?front.*?setback.*?(\d+(?:\.\d+)?)\s*m", "min_front_setback_m"),
        (r"minimum.*?side.*?setback.*?(\d+(?:\.\d+)?)\s*m", "min_side_setback_m"),
        (r"minimum.*?rear.*?setback.*?(\d+(?:\.\d+)?)\s*m", "min_rear_setback_m"),
        (r"maximum.*?floor.*?area.*?ratio.*?(\d+(?:\.\d+)?)", "max_far"),
        (r"maximum.*?(?:lot|site).*?coverage.*?(\d+(?:\.\d+)?)\s*%", "max_coverage_pct"),
        (r"minimum.*?(?:lot|parcel).*?(?:area|size).*?(\d+(?:\.\d+)?)\s*m", "min_lot_area_m2"),
        (r"minimum.*?(?:lot|parcel).*?width.*?(\d+(?:\.\d+)?)\s*m", "min_lot_width_m"),
    ]

    for pattern, rule_type in rule_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            rules.append({
                "district": district_code,
                "rule_type": rule_type,
                "value": float(match),
            })

    return rules


def extract_bylaw(config: Dict, verbose: bool = False) -> Dict:
    """Extract Land Use Bylaw."""
    print("=" * 60)
    print("Extracting Land Use Bylaw 1P2007")
    print("=" * 60)

    result = {
        "metadata": {
            "code": config["full_name"],
            "short_name": config["short_name"],
            "jurisdiction": "City of Calgary",
            "extraction_date": str(date.today()),
            "extraction_method": "pdfplumber",
            "verification_status": "pending_professional_review"
        },
        "parts": [],
        "districts": [],
        "rules_summary": {},
        "summary": {}
    }

    with pdfplumber.open(config["pdf_path"]) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages: {total_pages}")

        # LUB Parts structure
        parts_info = [
            (1, "Administration", 1, 50),
            (2, "Interpretation", 50, 150),
            (3, "Land Use Districts and Maps", 150, 250),
            (4, "Rules for All Land Use Districts", 250, 400),
            (5, "Residential Districts", 400, 600),
            (6, "Commercial Districts", 600, 700),
            (7, "Industrial Districts", 700, 750),
            (8, "Special Purpose Districts", 750, 850),
            (9, "Overlay Districts", 850, 950),
        ]

        for part_num, part_name, start_page, end_page in parts_info:
            print(f"\nExtracting Part {part_num}: {part_name}...")

            part_data = {
                "part_number": part_num,
                "name": part_name,
                "pages": f"{start_page}-{min(end_page, total_pages)}",
                "raw_text": "",
                "sections": []
            }

            # Extract text from page range
            texts = []
            for page_num in range(start_page - 1, min(end_page, total_pages)):
                text = pdf.pages[page_num].extract_text()
                if text:
                    texts.append(text)

            part_data["raw_text"] = "\n\n".join(texts)

            # Extract districts from Parts 5-8
            if part_num in [5, 6, 7, 8]:
                districts = extract_bylaw_districts(pdf, start_page - 1, min(end_page, total_pages))
                part_data["districts"] = districts
                result["districts"].extend(districts)
                print(f"  Found {len(districts)} districts")

            result["parts"].append(part_data)

        result["summary"] = {
            "total_parts": len(result["parts"]),
            "total_districts": len(result["districts"]),
            "total_pages": total_pages
        }

    return result


def save_results(data: Dict, config: Dict, output_type: str = "structured"):
    """Save extraction results to JSON files."""
    output_path = OUTPUT_DIR / f"{config['output_prefix']}_{output_type}.json"

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

    print(f"\nSaved: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Extract building codes to structured JSON")
    parser.add_argument("--code", choices=["necb", "nfc", "npc", "bylaw"],
                       help="Code to extract")
    parser.add_argument("--all", action="store_true", help="Extract all codes")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if not args.code and not args.all:
        parser.print_help()
        sys.exit(1)

    codes_to_extract = []
    if args.all:
        codes_to_extract = ["necb", "nfc", "npc", "bylaw"]
    else:
        codes_to_extract = [args.code]

    for code in codes_to_extract:
        config = CODE_CONFIGS[code]

        if not config["pdf_path"].exists():
            print(f"ERROR: PDF not found: {config['pdf_path']}")
            continue

        if code == "necb":
            result = extract_necb(config, args.verbose)
        elif code == "nfc":
            result = extract_nfc(config, args.verbose)
        elif code == "npc":
            result = extract_npc(config, args.verbose)
        elif code == "bylaw":
            result = extract_bylaw(config, args.verbose)

        save_results(result, config)

        print("\n" + "=" * 60)
        print(f"EXTRACTION SUMMARY - {config['short_name']}")
        print("=" * 60)
        print(f"Code: {config['full_name']}")
        if "summary" in result:
            for key, value in result["summary"].items():
                print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
