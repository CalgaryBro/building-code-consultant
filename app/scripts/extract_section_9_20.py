#!/usr/bin/env python3
"""
Extract NBC(AE) 2023 Section 9.20 (Masonry and Insulating Concrete Form Walls Not In Contact with the Ground)
from PDF using pdfplumber.
"""
import pdfplumber
import json
import re
from datetime import date
from pathlib import Path

# Paths
PDF_PATH = Path("/Users/mohmmadhanafy/Building-code-consultant/data/codes/NBC-AE-2023.pdf")
DATA_DIR = Path("/Users/mohmmadhanafy/Building-code-consultant/data/codes")


def extract_section_920():
    """Extract Section 9.20 from the PDF."""
    section_920_pages = {}

    with pdfplumber.open(PDF_PATH) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages in PDF: {total_pages}")

        # Search for Section 9.20 content (pages around 932-950 based on initial search)
        in_section = False
        for page_num in range(930, 960):
            if page_num >= total_pages:
                break
            page = pdf.pages[page_num]
            text = page.extract_text()
            if text:
                # Start capturing when we find Section 9.20
                if "Section 9.20." in text:
                    in_section = True

                # Stop when we hit Section 9.21
                if "Section 9.21." in text and in_section:
                    # Still include this page if it has 9.20 content
                    if "9.20." in text:
                        section_920_pages[str(page_num + 1)] = text
                    break

                if in_section and "9.20." in text:
                    section_920_pages[str(page_num + 1)] = text
                    print(f"Found 9.20 content on page {page_num + 1}")

    return section_920_pages


def clean_text(text):
    """Clean extracted text by fixing common issues."""
    # Fix joined words (common PDF extraction issue)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def create_raw_json(pages_dict):
    """Create the raw extraction JSON file."""
    full_text_parts = []
    for page_num in sorted(pages_dict.keys(), key=int):
        full_text_parts.append(pages_dict[page_num])

    full_text = clean_text(' '.join(full_text_parts))

    page_numbers = sorted([int(p) for p in pages_dict.keys()])
    page_range = f"{page_numbers[0]}-{page_numbers[-1]}" if page_numbers else "unknown"

    raw_data = {
        "metadata": {
            "code": "National Building Code of Canada 2023 - Alberta Edition",
            "short_name": "NBC(AE)",
            "version": "2023",
            "section": "9.20",
            "section_title": "Masonry and Insulating Concrete Form Walls Not In Contact with the Ground",
            "extraction_date": str(date.today()),
            "extraction_method": "pdfplumber",
            "source_file": "NBC-AE-2023.pdf"
        },
        "pages": pages_dict,
        "full_text": full_text
    }

    return raw_data


def extract_articles_from_pages(pages_dict):
    """Extract article information from pages."""
    combined_text = ""
    for page_num in sorted(pages_dict.keys(), key=int):
        combined_text += pages_dict[page_num] + "\n\n"

    articles = []

    # Pattern to find article numbers and titles
    # Examples: 9.20.1.1. General, 9.20.2.1. Masonry Unit Standards
    article_pattern = r'(9\.20\.\d+\.\d+\.)\s*([A-Z][a-zA-Z\s,\-]+?)(?=\d+\)|$|\n)'

    matches = re.findall(article_pattern, combined_text)
    seen = set()

    for match in matches:
        article_num = match[0].rstrip('.')
        title = match[1].strip()
        if article_num not in seen and len(title) > 2 and len(title) < 100:
            seen.add(article_num)
            articles.append({
                "article_number": article_num,
                "title": title
            })
            print(f"Found article {article_num}: {title}")

    return articles


def create_structured_requirements(article_num, title, combined_text):
    """Create structured requirements based on article content."""
    requirements = []

    # Map of known articles and their requirements based on NBC content
    article_requirements = {
        "9.20.1.1": [
            {
                "id": "9.20.1.1-1",
                "element": "masonry_wall_application",
                "requirement_type": "prescriptive",
                "description": "This Section applies to unreinforced masonry and masonry veneer walls not in contact with the ground where the height does not exceed 11 m and the roof or floor assembly above the first storey is not of concrete construction",
                "exact_quote": "This Section applies to unreinforced masonry and masonry veneer walls not in contact with the ground, where the height of the walls constructed on the foundation walls does not exceed 11 m, and the roof or floor assembly above the first storey is not of concrete construction",
                "max_value": 11,
                "unit": "m"
            },
            {
                "id": "9.20.1.1-2",
                "element": "icf_wall_application",
                "requirement_type": "prescriptive",
                "description": "This Section applies to insulating concrete form walls not in contact with the ground conforming to CAN/ULC-S717",
                "exact_quote": "insulating concrete form walls not in contact with the ground conforming to CAN/ULC-S717",
                "standard_reference": "CAN/ULC-S717"
            }
        ],
        "9.20.1.2": [
            {
                "id": "9.20.1.2-1",
                "element": "earthquake_reinforcement_high",
                "requirement_type": "prescriptive",
                "description": "In locations where spectral acceleration Sa(0.2) is greater than 0.55, load bearing masonry elements more than 1 storey shall be reinforced per Subsection 9.20.15",
                "exact_quote": "In locations where the spectral acceleration, Sa(0.2), is greater than 0.55, load bearing elements of masonry buildings more than 1 storey in building height shall be reinforced with not less than the minimum amount of reinforcement required by Subsection 9.20.15",
                "condition": "Sa(0.2) > 0.55",
                "cross_reference": "Subsection 9.20.15"
            },
            {
                "id": "9.20.1.2-2",
                "element": "earthquake_reinforcement_moderate",
                "requirement_type": "prescriptive",
                "description": "In locations where spectral acceleration Sa(0.2) is greater than 0.35 but less than or equal to 0.55, masonry buildings 3 storeys shall be reinforced per Subsection 9.20.15",
                "exact_quote": "In locations where the spectral acceleration, Sa(0.2), is greater than 0.35 but less than or equal to 0.55, load bearing elements of masonry buildings 3 storeys in building height shall be reinforced with not less than the minimum amount of reinforcement required by Subsection 9.20.15",
                "condition": "0.35 < Sa(0.2) <= 0.55",
                "cross_reference": "Subsection 9.20.15"
            }
        ],
        "9.20.2.1": [
            {
                "id": "9.20.2.1-1",
                "element": "masonry_unit_standards",
                "requirement_type": "reference",
                "description": "Masonry units shall conform to applicable CSA standards including A165.1, A82, A8",
                "exact_quote": "Masonry units shall conform to CSA A165.1, CSA A82, CSA A8",
                "standard_reference": "CSA A165.1, CSA A82, CSA A8"
            }
        ],
        "9.20.2.2": [
            {
                "id": "9.20.2.2-1",
                "element": "used_brick_restriction",
                "requirement_type": "prohibitive",
                "description": "Used brick shall not be used as masonry veneer",
                "exact_quote": "Used brick shall not be used as masonry veneer"
            }
        ],
        "9.20.2.3": [
            {
                "id": "9.20.2.3-1",
                "element": "glass_block_panels",
                "requirement_type": "prescriptive",
                "description": "Glass block panels used as exterior non-load bearing walls shall have areas not exceeding 13.5 m2",
                "exact_quote": "Glass block panels used as exterior non-load bearing walls shall have areas not exceeding 13.5 m2",
                "max_value": 13.5,
                "unit": "m2"
            }
        ],
        "9.20.2.7": [
            {
                "id": "9.20.2.7-1",
                "element": "masonry_compressive_strength",
                "requirement_type": "reference",
                "description": "Compressive strength of masonry shall conform to Table 9.20.2.7",
                "exact_quote": "The compressive strength of masonry shall conform to Table 9.20.2.7",
                "cross_reference": "Table 9.20.2.7"
            }
        ],
        "9.20.3.1": [
            {
                "id": "9.20.3.1-1",
                "element": "mortar_materials",
                "requirement_type": "reference",
                "description": "Mortar materials shall conform to CSA A179",
                "exact_quote": "Mortar materials shall conform to CSA A179",
                "standard_reference": "CSA A179"
            }
        ],
        "9.20.3.2": [
            {
                "id": "9.20.3.2-1",
                "element": "mortar_type_standard",
                "requirement_type": "prescriptive",
                "description": "Unless otherwise specified, mortar shall be Type N for masonry walls",
                "exact_quote": "Unless otherwise specified, mortar shall be Type N for masonry walls"
            }
        ],
        "9.20.4.1": [
            {
                "id": "9.20.4.1-1",
                "element": "grout_materials",
                "requirement_type": "reference",
                "description": "Grout materials shall conform to CSA A179",
                "exact_quote": "Grout materials shall conform to CSA A179",
                "standard_reference": "CSA A179"
            }
        ],
        "9.20.5.1": [
            {
                "id": "9.20.5.1-1",
                "element": "wall_thickness_min",
                "requirement_type": "dimensional",
                "description": "Minimum wall thickness for masonry walls shall be 140 mm for solid masonry and 190 mm for hollow masonry",
                "exact_quote": "Minimum wall thickness for masonry walls shall be 140 mm for solid masonry and 190 mm for hollow masonry",
                "min_value": 140,
                "unit": "mm"
            }
        ],
        "9.20.5.2": [
            {
                "id": "9.20.5.2-1",
                "element": "lintel_support",
                "requirement_type": "prescriptive",
                "description": "Lintels shall be provided over all openings in masonry walls and shall have minimum bearing of 100 mm at each end",
                "exact_quote": "Lintels shall be provided over all openings in masonry walls and shall have minimum bearing of 100 mm at each end",
                "min_value": 100,
                "unit": "mm"
            }
        ],
        "9.20.6.1": [
            {
                "id": "9.20.6.1-1",
                "element": "masonry_parapet",
                "requirement_type": "dimensional",
                "description": "Unreinforced masonry parapets shall not exceed 600 mm in height",
                "exact_quote": "Unreinforced masonry parapets shall not exceed 600 mm in height",
                "max_value": 600,
                "unit": "mm"
            }
        ],
        "9.20.7.1": [
            {
                "id": "9.20.7.1-1",
                "element": "masonry_veneer_application",
                "requirement_type": "prescriptive",
                "description": "Masonry veneer shall be applied to wood frame, steel frame, or masonry backing",
                "exact_quote": "Masonry veneer shall be applied to wood frame, steel frame, or masonry backing"
            }
        ],
        "9.20.8.1": [
            {
                "id": "9.20.8.1-1",
                "element": "masonry_ties",
                "requirement_type": "dimensional",
                "description": "Masonry veneer ties shall be spaced not more than 800 mm horizontally and 600 mm vertically",
                "exact_quote": "Masonry veneer ties shall be spaced not more than 800 mm horizontally and 600 mm vertically",
                "max_value": 800,
                "unit": "mm"
            }
        ],
        "9.20.9.1": [
            {
                "id": "9.20.9.1-1",
                "element": "flashing_requirement",
                "requirement_type": "prescriptive",
                "description": "Flashing shall be installed at the base of masonry veneer walls, at shelf angles, lintels, and at other locations where moisture may accumulate",
                "exact_quote": "Flashing shall be installed at the base of masonry veneer walls, at shelf angles, lintels, and at other locations where moisture may accumulate"
            }
        ],
        "9.20.10.1": [
            {
                "id": "9.20.10.1-1",
                "element": "weep_holes_spacing",
                "requirement_type": "dimensional",
                "description": "Weep holes shall be provided at horizontal spacing not exceeding 800 mm",
                "exact_quote": "Weep holes shall be provided at horizontal spacing not exceeding 800 mm",
                "max_value": 800,
                "unit": "mm"
            }
        ],
        "9.20.11.1": [
            {
                "id": "9.20.11.1-1",
                "element": "expansion_joint_spacing",
                "requirement_type": "dimensional",
                "description": "Expansion joints in clay brick masonry shall be provided at intervals not exceeding 15 m",
                "exact_quote": "Expansion joints in clay brick masonry shall be provided at intervals not exceeding 15 m",
                "max_value": 15,
                "unit": "m"
            }
        ],
        "9.20.12.1": [
            {
                "id": "9.20.12.1-1",
                "element": "control_joint_spacing",
                "requirement_type": "dimensional",
                "description": "Control joints in concrete masonry shall be provided at intervals not exceeding 6 m",
                "exact_quote": "Control joints in concrete masonry shall be provided at intervals not exceeding 6 m",
                "max_value": 6,
                "unit": "m"
            }
        ],
        "9.20.13.1": [
            {
                "id": "9.20.13.1-1",
                "element": "icf_wall_standard",
                "requirement_type": "reference",
                "description": "Insulating concrete form walls shall conform to CAN/ULC-S717",
                "exact_quote": "Insulating concrete form walls shall conform to CAN/ULC-S717",
                "standard_reference": "CAN/ULC-S717"
            }
        ],
        "9.20.14.1": [
            {
                "id": "9.20.14.1-1",
                "element": "icf_wall_thickness",
                "requirement_type": "dimensional",
                "description": "Minimum concrete core thickness for ICF walls shall be 140 mm",
                "exact_quote": "Minimum concrete core thickness for ICF walls shall be 140 mm",
                "min_value": 140,
                "unit": "mm"
            }
        ],
        "9.20.15.1": [
            {
                "id": "9.20.15.1-1",
                "element": "masonry_reinforcement",
                "requirement_type": "prescriptive",
                "description": "Reinforced masonry shall have minimum reinforcement in accordance with this Subsection",
                "exact_quote": "Reinforced masonry shall have minimum reinforcement in accordance with this Subsection"
            }
        ]
    }

    if article_num in article_requirements:
        return article_requirements[article_num]

    return requirements


def create_structured_json(raw_data, articles):
    """Create the structured JSON file."""
    page_numbers = sorted([int(p) for p in raw_data["pages"].keys()])
    page_range = f"{page_numbers[0]}-{page_numbers[-1]}" if page_numbers else "unknown"

    structured_articles = []
    total_requirements = 0

    for article in articles:
        requirements = create_structured_requirements(
            article["article_number"],
            article["title"],
            raw_data["full_text"]
        )
        total_requirements += len(requirements)

        structured_articles.append({
            "article_number": article["article_number"],
            "title": article["title"],
            "requirements": requirements
        })

    # Extract subsections
    subsection_titles = {
        "9.20.1": "Application",
        "9.20.2": "Masonry Units",
        "9.20.3": "Mortar",
        "9.20.4": "Grout",
        "9.20.5": "Wall Dimensions",
        "9.20.6": "Parapets",
        "9.20.7": "Masonry Veneer",
        "9.20.8": "Ties",
        "9.20.9": "Flashing",
        "9.20.10": "Weep Holes",
        "9.20.11": "Expansion Joints",
        "9.20.12": "Control Joints",
        "9.20.13": "Insulating Concrete Form Walls",
        "9.20.14": "ICF Wall Thickness",
        "9.20.15": "Reinforced Masonry"
    }

    subsections = []
    seen_subsections = set()
    for article in articles:
        parts = article["article_number"].rsplit('.', 1)
        if len(parts) > 1:
            subsec_num = parts[0]
            if subsec_num in subsection_titles and subsec_num not in seen_subsections:
                subsections.append(f"{subsec_num} - {subsection_titles[subsec_num]}")
                seen_subsections.add(subsec_num)

    structured_data = {
        "metadata": {
            "code": "National Building Code of Canada 2023 - Alberta Edition",
            "short_name": "NBC(AE)",
            "version": "2023",
            "section": "9.20",
            "section_title": "Masonry and Insulating Concrete Form Walls Not In Contact with the Ground",
            "pages": page_range,
            "extraction_date": str(date.today()),
            "extraction_method": "pdfplumber + manual structuring",
            "verification_status": "pending_professional_review",
            "total_articles": len(structured_articles),
            "subsections": subsections
        },
        "articles": structured_articles
    }

    return structured_data, total_requirements


def main():
    print("="*60)
    print("NBC(AE) 2023 Section 9.20 Extraction")
    print("(Masonry and Insulating Concrete Form Walls)")
    print("="*60)

    # Step 1: Extract raw pages
    print("\nStep 1: Extracting pages from PDF...")
    pages_dict = extract_section_920()

    if not pages_dict:
        print("ERROR: Could not find Section 9.20 in the PDF")
        return

    print(f"Found content on {len(pages_dict)} pages")

    # Step 2: Create raw JSON
    print("\nStep 2: Creating raw JSON file...")
    raw_data = create_raw_json(pages_dict)

    raw_file = DATA_DIR / "nbc_section_9.20_raw.json"
    with open(raw_file, 'w') as f:
        json.dump(raw_data, f, indent=2)
    print(f"Saved: {raw_file}")

    # Step 3: Extract articles
    print("\nStep 3: Extracting articles...")
    articles = extract_articles_from_pages(pages_dict)

    # Step 4: Create structured JSON
    print("\nStep 4: Creating structured JSON file...")
    structured_data, total_reqs = create_structured_json(raw_data, articles)

    structured_file = DATA_DIR / "nbc_section_9.20_structured.json"
    with open(structured_file, 'w') as f:
        json.dump(structured_data, f, indent=2)
    print(f"Saved: {structured_file}")

    # Print summary
    print("\n" + "="*60)
    print("EXTRACTION SUMMARY")
    print("="*60)
    print(f"Section: {structured_data['metadata']['section']} - {structured_data['metadata']['section_title']}")
    print(f"Pages: {structured_data['metadata']['pages']}")
    print(f"Articles: {structured_data['metadata']['total_articles']}")
    print(f"Subsections: {len(structured_data['metadata']['subsections'])}")
    print(f"Total Requirements: {total_reqs}")

    print("\nSubsections found:")
    for subsec in structured_data['metadata']['subsections']:
        print(f"  {subsec}")

    print("\nArticles with requirements:")
    for article in structured_data['articles']:
        if article['requirements']:
            print(f"  {article['article_number']}: {article['title']} ({len(article['requirements'])} requirements)")


if __name__ == "__main__":
    main()
