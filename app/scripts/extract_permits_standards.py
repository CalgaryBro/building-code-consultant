#!/usr/bin/env python3
"""
Extract Permit Guides and Standards documents to structured JSON.

Documents:
- Permit Guides: Fee schedules, design guidelines, accessibility guides
- Standards: CSA accessibility, EMTC guide, NPC comparison
"""

import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    print("PyMuPDF not installed. Please install with: pip install PyMuPDF")
    sys.exit(1)

# Base paths
BASE_DIR = Path("/Users/mohmmadhanafy/Building-code-consultant")
PERMITS_DIR = BASE_DIR / "data" / "permits"
STANDARDS_DIR = BASE_DIR / "data" / "standards"
OUTPUT_DIR = BASE_DIR / "data" / "codes"


def extract_text_from_pdf(pdf_path: Path) -> tuple[str, int]:
    """Extract all text from a PDF file."""
    try:
        doc = fitz.open(str(pdf_path))
        full_text = ""
        num_pages = len(doc)

        for page_num in range(num_pages):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            full_text += f"\n--- Page {page_num + 1} ---\n{text}"

        doc.close()
        return full_text.strip(), num_pages
    except Exception as e:
        print(f"  Error: {e}")
        return "", 0


def extract_fee_schedule(text: str) -> List[Dict]:
    """Extract fee information from fee schedule document."""
    fees = []

    # Common fee patterns
    fee_patterns = [
        # Pattern: "Description ... $X,XXX.XX" or "$XXX"
        (r'([A-Za-z][A-Za-z\s\-/]+?)\s+\$\s*([\d,]+(?:\.\d{2})?)', 'fixed'),
        # Pattern: "$X.XX per square metre"
        (r'\$\s*([\d.]+)\s*(?:per|/)\s*(square\s*(?:metre|meter|m2|ft))', 'per_unit'),
        # Pattern: "minimum $XXX"
        (r'minimum\s+\$\s*([\d,]+(?:\.\d{2})?)', 'minimum'),
    ]

    for pattern, fee_type in fee_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches[:50]:  # Limit to avoid too many
            if fee_type == 'fixed':
                desc, amount = match
                if len(desc.strip()) > 3 and len(desc.strip()) < 100:
                    fees.append({
                        "description": desc.strip(),
                        "amount": amount.replace(',', ''),
                        "type": fee_type
                    })
            elif fee_type == 'per_unit':
                amount, unit = match
                fees.append({
                    "amount": amount,
                    "unit": unit,
                    "type": fee_type
                })

    return fees


def extract_sections(text: str) -> List[Dict]:
    """Extract document sections/chapters."""
    sections = []

    # Look for numbered sections or chapters
    section_patterns = [
        r'(?:Section|Chapter|Part)\s+(\d+)[:\s]+([A-Z][^\n]+)',
        r'^(\d+(?:\.\d+)?)\s+([A-Z][A-Z\s]+)$',
    ]

    for pattern in section_patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        for num, title in matches[:30]:
            title = title.strip()
            if len(title) > 3 and len(title) < 100:
                sections.append({
                    "number": num,
                    "title": title
                })

    return sections


def extract_requirements(text: str) -> List[Dict]:
    """Extract requirements/specifications from text."""
    requirements = []

    # Dimensional requirements
    dim_patterns = [
        (r'(?:minimum|min\.?)\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(mm|m|cm|inches?|feet|ft)', 'minimum'),
        (r'(?:maximum|max\.?)\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(mm|m|cm|inches?|feet|ft)', 'maximum'),
        (r'(?:at least|not less than)\s+(\d+(?:\.\d+)?)\s*(mm|m|cm|%)', 'minimum'),
        (r'(?:not (?:more|greater) than|shall not exceed)\s+(\d+(?:\.\d+)?)\s*(mm|m|cm|%)', 'maximum'),
    ]

    for pattern, req_type in dim_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for value, unit in matches[:30]:
            requirements.append({
                "type": req_type,
                "value": float(value),
                "unit": unit.lower()
            })

    return requirements


def extract_accessibility_requirements(text: str) -> List[Dict]:
    """Extract accessibility-specific requirements."""
    acc_reqs = []

    # Accessibility patterns
    patterns = [
        (r'(?:ramp|slope)\s+(?:gradient|slope)?\s*(?:of|:)?\s*(?:not (?:more|greater) than|maximum)?\s*1\s*(?::|in)\s*(\d+)', 'ramp_slope'),
        (r'(?:door|doorway)\s+(?:width|opening)\s+(?:of\s+)?(?:at least|minimum)?\s*(\d+)\s*(mm|m)', 'door_width'),
        (r'(?:corridor|hallway)\s+(?:width)?\s+(?:of\s+)?(?:at least|minimum)?\s*(\d+)\s*(mm|m)', 'corridor_width'),
        (r'(?:grab bar|handrail)\s+(?:height|diameter)?\s+(?:of\s+)?(\d+)\s*(?:to\s*(\d+))?\s*(mm|m)', 'grab_bar'),
        (r'(?:turning|maneuvering)\s+(?:space|radius|circle)\s+(?:of\s+)?(\d+)\s*(mm|m)', 'turning_space'),
        (r'(?:clear floor|floor)\s+space\s+(?:of\s+)?(\d+)\s*(?:x|by)\s*(\d+)\s*(mm|m)', 'clear_floor_space'),
    ]

    for pattern, req_type in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches[:20]:
            acc_reqs.append({
                "type": req_type,
                "values": [v for v in match if v],
            })

    return acc_reqs


def process_permit_guide(pdf_path: Path) -> Dict:
    """Process a permit guide PDF."""
    print(f"  Processing: {pdf_path.name}")

    text, num_pages = extract_text_from_pdf(pdf_path)
    if not text:
        return None

    # Determine document type
    filename_lower = pdf_path.name.lower()
    if 'fee' in filename_lower:
        doc_type = 'fee_schedule'
    elif 'access' in filename_lower:
        doc_type = 'accessibility_guide'
    elif 'design' in filename_lower:
        doc_type = 'design_guidelines'
    elif 'subdivision' in filename_lower:
        doc_type = 'subdivision_guidelines'
    else:
        doc_type = 'permit_guide'

    result = {
        "metadata": {
            "filename": pdf_path.name,
            "document_type": doc_type,
            "num_pages": num_pages,
            "extraction_date": str(date.today()),
        },
        "sections": extract_sections(text),
        "requirements": extract_requirements(text),
        "full_text": text[:50000],  # Limit size
    }

    # Add type-specific extractions
    if doc_type == 'fee_schedule':
        result["fees"] = extract_fee_schedule(text)
    elif doc_type == 'accessibility_guide':
        result["accessibility_requirements"] = extract_accessibility_requirements(text)

    return result


def process_standard(pdf_path: Path) -> Dict:
    """Process a standards document PDF."""
    print(f"  Processing: {pdf_path.name}")

    text, num_pages = extract_text_from_pdf(pdf_path)
    if not text:
        return None

    # Determine standard type
    filename_lower = pdf_path.name.lower()
    if 'csa' in filename_lower or 'b651' in filename_lower:
        doc_type = 'csa_accessibility'
    elif 'emtc' in filename_lower or '12-storey' in filename_lower:
        doc_type = 'mass_timber_guide'
    elif 'npc' in filename_lower or 'comparison' in filename_lower:
        doc_type = 'code_comparison'
    else:
        doc_type = 'standard'

    result = {
        "metadata": {
            "filename": pdf_path.name,
            "document_type": doc_type,
            "num_pages": num_pages,
            "extraction_date": str(date.today()),
        },
        "sections": extract_sections(text),
        "requirements": extract_requirements(text),
        "full_text": text[:50000],  # Limit size
    }

    if doc_type == 'csa_accessibility':
        result["accessibility_requirements"] = extract_accessibility_requirements(text)

    return result


def main():
    print("=" * 60)
    print("Permit Guides & Standards Extraction")
    print("=" * 60)

    all_documents = {
        "metadata": {
            "extraction_date": str(date.today()),
            "source": "Calgary Permit Guides and Referenced Standards"
        },
        "permit_guides": [],
        "standards": [],
        "summary": {}
    }

    # Process permit guides
    print("\n--- Permit Guides ---")
    permit_pdfs = list(PERMITS_DIR.glob("*.pdf"))
    print(f"Found {len(permit_pdfs)} PDF files")

    for pdf_path in sorted(permit_pdfs):
        result = process_permit_guide(pdf_path)
        if result:
            all_documents["permit_guides"].append(result)
            print(f"    Sections: {len(result.get('sections', []))}, Requirements: {len(result.get('requirements', []))}")

    # Process standards
    print("\n--- Standards ---")
    standards_pdfs = [f for f in STANDARDS_DIR.glob("*.pdf") if 'preview' not in f.name.lower()]
    print(f"Found {len(standards_pdfs)} PDF files (excluding previews)")

    for pdf_path in sorted(standards_pdfs):
        result = process_standard(pdf_path)
        if result:
            all_documents["standards"].append(result)
            print(f"    Sections: {len(result.get('sections', []))}, Requirements: {len(result.get('requirements', []))}")

    # Summary
    all_documents["summary"] = {
        "total_permit_guides": len(all_documents["permit_guides"]),
        "total_standards": len(all_documents["standards"]),
        "total_documents": len(all_documents["permit_guides"]) + len(all_documents["standards"])
    }

    # Save results
    output_path = OUTPUT_DIR / "permits_standards_extracted.json"
    with open(output_path, 'w') as f:
        json.dump(all_documents, f, indent=2, default=str)

    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"Permit Guides: {all_documents['summary']['total_permit_guides']}")
    print(f"Standards: {all_documents['summary']['total_standards']}")
    print(f"\nSaved: {output_path}")

    # Also save fee schedule separately for easy access
    for doc in all_documents["permit_guides"]:
        if doc["metadata"]["document_type"] == "fee_schedule":
            fee_output = OUTPUT_DIR / "fee_schedule_extracted.json"
            with open(fee_output, 'w') as f:
                json.dump(doc, f, indent=2)
            print(f"Fee Schedule: {fee_output}")
            break


if __name__ == "__main__":
    main()
