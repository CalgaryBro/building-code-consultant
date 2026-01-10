#!/usr/bin/env python3
"""
Extract STANDATA bulletins from PDF files and load them into the database.

This script:
1. Scans the STANDATA directory for PDF files
2. Extracts text content using PyMuPDF (fitz)
3. Parses bulletin number, title, and content
4. Identifies NBC code references (pattern: "Article X.X.X.X" or "X.X.X.X")
5. Generates keywords from content
6. Saves to database

Usage:
    python -m app.scripts.extract_standata [--dry-run] [--force] [--verbose]

Options:
    --dry-run   Show what would be done without making changes
    --force     Delete existing data and reload
    --verbose   Enable verbose logging
"""

import argparse
import logging
import os
import re
import sys
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from sqlalchemy import select

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database import SessionLocal
from app.models.standata import Standata
from app.config import get_settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import fitz (PyMuPDF)
try:
    import fitz  # PyMuPDF
except ImportError:
    logger.error("PyMuPDF not installed. Please install with: pip install PyMuPDF")
    sys.exit(1)


# Regular expressions for parsing
BULLETIN_NUMBER_PATTERN = re.compile(r'(\d{2})-([A-Z]{2,3})-(\d{3})', re.IGNORECASE)
CODE_REFERENCE_PATTERN = re.compile(
    r'(?:Article\s+)?(\d{1,2}\.\d{1,2}\.\d{1,2}(?:\.\d{1,2})?)',
    re.IGNORECASE
)
DATE_PATTERNS = [
    re.compile(r'(?:Effective|Date)[:\s]+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})', re.IGNORECASE),
    re.compile(r'(\d{1,2}/\d{1,2}/\d{4})'),
    re.compile(r'([A-Z][a-z]+\s+\d{4})'),
]

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
}


def extract_text_from_pdf(pdf_path: Path) -> Tuple[str, str]:
    """
    Extract text from a PDF file using PyMuPDF.

    Returns:
        Tuple of (full_text, extraction_confidence)
    """
    try:
        doc = fitz.open(str(pdf_path))
        full_text = ""

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            full_text += text + "\n\n"

        doc.close()

        # Assess extraction confidence based on text quality
        if len(full_text.strip()) < 100:
            confidence = "LOW"
        elif len(full_text.strip()) < 500:
            confidence = "MEDIUM"
        else:
            confidence = "HIGH"

        return full_text.strip(), confidence

    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
        return "", "LOW"


def parse_bulletin_number(filename: str, text: str) -> Tuple[str, str]:
    """
    Parse bulletin number and category from filename or text.

    Returns:
        Tuple of (bulletin_number, category)
    """
    # Try filename first
    match = BULLETIN_NUMBER_PATTERN.search(filename)
    if match:
        year, category, number = match.groups()
        bulletin_number = f"{year}-{category.upper()}-{number}"
        return bulletin_number, category.upper()

    # Try text content
    match = BULLETIN_NUMBER_PATTERN.search(text)
    if match:
        year, category, number = match.groups()
        bulletin_number = f"{year}-{category.upper()}-{number}"
        return bulletin_number, category.upper()

    # Fallback - try to construct from filename
    basename = Path(filename).stem.upper()
    basename = basename.replace("_", "-").replace(" ", "-")

    # Check for category patterns
    for cat in ['BCI', 'BCB', 'FCB', 'PCB']:
        if cat in basename:
            return basename, cat

    return basename, "BCI"  # Default to BCI


def extract_title(text: str, bulletin_number: str) -> str:
    """
    Extract the title from the bulletin text.

    Usually found on the first page after the bulletin number.
    """
    lines = text.split('\n')

    # Look for a line that appears to be a title (short, capitalized)
    # Skip header lines and find substantive content
    for i, line in enumerate(lines[:30]):  # First 30 lines
        line = line.strip()

        # Skip empty lines, bulletin numbers, dates
        if not line or len(line) < 10:
            continue
        if bulletin_number in line:
            continue
        if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', line):
            continue
        if 'STANDATA' in line.upper() or 'ALBERTA' in line.upper():
            continue
        if line.upper() == line and len(line) < 100:
            # All caps title
            continue

        # Check if this looks like a title (mixed case, reasonable length)
        if 20 < len(line) < 200:
            # Clean up the title
            title = line.strip()
            # Remove trailing punctuation
            title = re.sub(r'[:\.]$', '', title)
            return title

    # Fallback - use first meaningful line
    for line in lines[:20]:
        line = line.strip()
        if len(line) > 20 and bulletin_number not in line:
            return line[:200]

    return f"STANDATA Bulletin {bulletin_number}"


def extract_summary(text: str, max_length: int = 500) -> str:
    """
    Extract a summary from the bulletin text.

    Usually the first paragraph after the title.
    """
    # Find the first substantive paragraph
    paragraphs = text.split('\n\n')

    for para in paragraphs:
        para = para.strip()

        # Skip short paragraphs, headers, etc.
        if len(para) < 50:
            continue
        if para.upper() == para:  # All caps
            continue

        # Found a good paragraph
        if len(para) > max_length:
            # Truncate at sentence boundary
            sentences = re.split(r'(?<=[.!?])\s+', para)
            summary = ""
            for sent in sentences:
                if len(summary) + len(sent) < max_length:
                    summary += sent + " "
                else:
                    break
            return summary.strip() + "..."

        return para

    # Fallback
    return text[:max_length].strip() + "..."


def extract_code_references(text: str) -> List[str]:
    """
    Extract NBC code article references from the text.

    Looks for patterns like:
    - Article 9.8.4.1
    - 9.10.9.6
    - Section 9.36
    """
    matches = CODE_REFERENCE_PATTERN.findall(text)

    # Deduplicate and sort
    unique_refs = list(set(matches))

    # Filter out likely false positives (e.g., version numbers, dates)
    valid_refs = []
    for ref in unique_refs:
        parts = ref.split('.')
        # Valid NBC references typically start with part number (1-11)
        if parts[0].isdigit() and 1 <= int(parts[0]) <= 11:
            valid_refs.append(ref)

    return sorted(valid_refs)


def extract_keywords(text: str) -> List[str]:
    """
    Extract relevant keywords from the text.
    """
    keywords = []

    for keyword, pattern in KEYWORD_PATTERNS.items():
        if pattern.search(text):
            keywords.append(keyword)

    return sorted(keywords)


def extract_effective_date(text: str) -> Optional[date]:
    """
    Try to extract the effective date from the bulletin.
    """
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            date_str = match.group(1)
            try:
                # Try various date formats
                for fmt in ['%B %d, %Y', '%B %d %Y', '%m/%d/%Y', '%B %Y']:
                    try:
                        parsed = datetime.strptime(date_str, fmt)
                        return parsed.date()
                    except ValueError:
                        continue
            except Exception:
                continue

    return None


def extract_supersedes(text: str) -> Optional[str]:
    """
    Check if this bulletin supersedes a previous one.
    """
    # Look for "supersedes" or "replaces" followed by a bulletin number
    patterns = [
        re.compile(r'(?:supersede[s]?|replace[s]?)\s+(\d{2}-[A-Z]{2,3}-\d{3})', re.IGNORECASE),
        re.compile(r'replac(?:es|ing)\s+(?:bulletin\s+)?(\d{2}-[A-Z]{2,3}-\d{3})', re.IGNORECASE),
    ]

    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match.group(1).upper()

    return None


def process_pdf_file(pdf_path: Path, standata_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Process a single PDF file and extract all relevant data.

    Returns a dictionary with extracted data or None if extraction failed.
    """
    logger.info(f"Processing: {pdf_path.name}")

    # Extract text
    full_text, confidence = extract_text_from_pdf(pdf_path)
    if not full_text:
        logger.warning(f"  No text extracted from {pdf_path.name}")
        return None

    # Parse bulletin info
    bulletin_number, category = parse_bulletin_number(pdf_path.name, full_text)
    logger.info(f"  Bulletin: {bulletin_number} ({category})")

    # Extract fields
    title = extract_title(full_text, bulletin_number)
    summary = extract_summary(full_text)
    code_refs = extract_code_references(full_text)
    keywords = extract_keywords(full_text)
    effective_date = extract_effective_date(full_text)
    supersedes = extract_supersedes(full_text)

    # Calculate relative path from standata directory
    rel_path = pdf_path.relative_to(standata_dir)

    return {
        'bulletin_number': bulletin_number,
        'title': title,
        'category': category,
        'effective_date': effective_date,
        'supersedes': supersedes,
        'summary': summary,
        'full_text': full_text,
        'code_references': code_refs if code_refs else None,
        'keywords': keywords if keywords else None,
        'related_bulletins': None,
        'pdf_path': str(rel_path),
        'pdf_filename': pdf_path.name,
        'extraction_confidence': confidence,
    }


def find_pdf_files(standata_dir: Path) -> List[Path]:
    """
    Find all PDF files in the STANDATA directory and subdirectories.
    """
    pdf_files = []

    # Main directory
    pdf_files.extend(standata_dir.glob("*.pdf"))

    # Subdirectories (fire, plumbing, etc.)
    for subdir in standata_dir.iterdir():
        if subdir.is_dir():
            pdf_files.extend(subdir.glob("*.pdf"))

    return sorted(pdf_files)


def save_to_database(data: Dict[str, Any], db, dry_run: bool = False) -> bool:
    """
    Save extracted data to the database.

    Returns True if saved successfully.
    """
    if dry_run:
        logger.info(f"  [DRY RUN] Would save: {data['bulletin_number']}")
        return True

    # Check if already exists
    existing = db.query(Standata).filter(
        Standata.bulletin_number == data['bulletin_number']
    ).first()

    if existing:
        # Update existing record
        for key, value in data.items():
            if key not in ['id', 'created_at']:
                setattr(existing, key, value)
        existing.updated_at = datetime.utcnow()
        logger.info(f"  Updated: {data['bulletin_number']}")
    else:
        # Create new record
        standata = Standata(
            id=uuid.uuid4(),
            **data
        )
        db.add(standata)
        logger.info(f"  Created: {data['bulletin_number']}")

    return True


def main():
    """Main entry point for the extraction script."""
    parser = argparse.ArgumentParser(
        description="Extract STANDATA bulletins from PDF files and load into database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete existing STANDATA data and reload (WARNING: destructive)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose debug logging"
    )
    parser.add_argument(
        "--single",
        type=str,
        help="Process a single PDF file (full path)"
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    settings = get_settings()
    standata_dir = Path(settings.data_dir) / "standata"

    if not standata_dir.exists():
        logger.error(f"STANDATA directory not found: {standata_dir}")
        sys.exit(1)

    # Find PDF files
    if args.single:
        pdf_files = [Path(args.single)]
    else:
        pdf_files = find_pdf_files(standata_dir)

    if not pdf_files:
        logger.error(f"No PDF files found in {standata_dir}")
        sys.exit(1)

    logger.info(f"Found {len(pdf_files)} PDF files to process")

    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")

    # Create database session
    db = SessionLocal()

    try:
        if args.force and not args.dry_run:
            logger.warning("FORCE MODE - Deleting existing STANDATA data")
            db.query(Standata).delete()
            db.commit()
            logger.info("Existing STANDATA data deleted")

        success_count = 0
        error_count = 0

        for pdf_path in pdf_files:
            try:
                data = process_pdf_file(pdf_path, standata_dir)
                if data:
                    if save_to_database(data, db, args.dry_run):
                        success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"Error processing {pdf_path.name}: {e}")
                error_count += 1

            # Commit periodically
            if not args.dry_run and success_count % 10 == 0:
                db.commit()

        # Final commit
        if not args.dry_run:
            db.commit()

        logger.info("=" * 60)
        logger.info(f"Processing complete!")
        logger.info(f"  Successful: {success_count}")
        logger.info(f"  Errors: {error_count}")

        if args.dry_run:
            logger.info("(DRY RUN - no changes were made)")
        else:
            logger.info("All changes committed to database")

    except Exception as e:
        logger.error(f"Error during processing: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
