#!/usr/bin/env python3
"""
Load NBC (National Building Code) structured JSON data into PostgreSQL database.

This script reads all nbc_section_*.json structured files and loads them into
the codes, articles, and requirements tables.

Usage:
    python -m app.scripts.load_nbc_data [--dry-run] [--force]

Options:
    --dry-run   Show what would be done without making changes
    --force     Delete existing data and reload (default is upsert)
"""

import argparse
import json
import logging
import sys
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from glob import glob
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database import SessionLocal, engine
from app.models.codes import Code, Article, Requirement, RequirementCondition
from app.config import get_settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_numeric_value(value: Any) -> Optional[Decimal]:
    """
    Parse a value to Decimal, handling various formats.
    Returns None if the value cannot be parsed or is null/None.
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None

    if isinstance(value, str):
        # Handle ratio strings like "1 in 50"
        if " in " in value.lower():
            return None  # Store these as exact_value strings

        # Handle percentage strings
        value = value.replace("%", "").strip()

        try:
            return Decimal(value)
        except (InvalidOperation, ValueError):
            return None

    return None


def get_or_create_code(db: Session, metadata: Dict[str, Any]) -> Code:
    """
    Get existing NBC code entry or create a new one.
    Returns the Code model instance.
    """
    short_name = metadata.get("short_name", "NBC(AE)")
    # Handle both "2023" and "NBC(AE) 2023" formats
    if " " in short_name:
        parts = short_name.split()
        short_name = parts[0]
        version = parts[-1] if len(parts) > 1 else "2023"
    else:
        version = metadata.get("version", "2023")

    # Look for existing code
    stmt = select(Code).where(
        and_(
            Code.short_name == short_name,
            Code.version == version
        )
    )
    existing_code = db.execute(stmt).scalar_one_or_none()

    if existing_code:
        logger.info(f"Using existing code: {existing_code.short_name} {existing_code.version}")
        return existing_code

    # Create new code entry
    new_code = Code(
        id=uuid.uuid4(),
        code_type="building",
        name=metadata.get("code", "National Building Code of Canada 2023 - Alberta Edition"),
        short_name=short_name,
        version=version,
        jurisdiction="Alberta",
        effective_date=date(2024, 5, 1),  # NBC(AE) 2023 effective date
        is_current=True,
        source_file=metadata.get("source_file"),
    )
    db.add(new_code)
    db.flush()  # Get the ID assigned
    logger.info(f"Created new code: {new_code.short_name} {new_code.version}")
    return new_code


def extract_section_number(section_str: str) -> int:
    """
    Extract section number from a section string like "9.8" or "9.36".
    Returns the subsection number (e.g., 8 from "9.8", 36 from "9.36").
    """
    if not section_str:
        return 0
    parts = section_str.split(".")
    if len(parts) >= 2:
        try:
            return int(parts[1])
        except ValueError:
            return 0
    return 0


def get_part_number(article_number: str) -> Optional[int]:
    """Extract part number from article number (e.g., 9 from 9.8.4.1)."""
    if article_number:
        parts = article_number.split(".")
        if parts:
            try:
                return int(parts[0])
            except ValueError:
                pass
    return None


def article_exists(db: Session, code_id: uuid.UUID, article_number: str) -> Optional[Article]:
    """Check if an article already exists and return it if found."""
    stmt = select(Article).where(
        and_(
            Article.code_id == code_id,
            Article.article_number == article_number
        )
    )
    return db.execute(stmt).scalar_one_or_none()


def create_or_update_article(
    db: Session,
    code: Code,
    article_data: Dict[str, Any],
    section_number: int,
    dry_run: bool = False
) -> Optional[Article]:
    """
    Create or update an article in the database.
    Returns the Article model instance or None if dry_run.
    """
    article_number = article_data.get("article_number", "")
    if not article_number:
        logger.warning("Skipping article with no article_number")
        return None

    title = article_data.get("title", "")
    full_text = article_data.get("full_text", "")

    # Use subsection as part of the title if no title
    if not title and article_data.get("subsection"):
        title = article_data.get("subsection")

    # Use description from first requirement if no full_text
    if not full_text and article_data.get("requirements"):
        first_req = article_data["requirements"][0]
        full_text = first_req.get("exact_quote", "") or first_req.get("description", "")

    if not full_text:
        full_text = f"Article {article_number}: {title}"

    if dry_run:
        logger.info(f"  [DRY RUN] Would create/update article: {article_number} - {title}")
        return None

    # Check for existing article
    existing = article_exists(db, code.id, article_number)

    if existing:
        # Update existing article
        existing.title = title
        existing.full_text = full_text
        existing.section_number = section_number
        existing.part_number = get_part_number(article_number)
        existing.updated_at = datetime.utcnow()
        logger.debug(f"  Updated article: {article_number}")
        return existing

    # Create new article
    article = Article(
        id=uuid.uuid4(),
        code_id=code.id,
        article_number=article_number,
        title=title,
        full_text=full_text,
        part_number=get_part_number(article_number),
        section_number=section_number,
    )
    db.add(article)
    db.flush()
    logger.debug(f"  Created article: {article_number}")
    return article


def requirement_exists(db: Session, article_id: uuid.UUID, element: str, exact_quote: str) -> Optional[Requirement]:
    """Check if a requirement already exists and return it if found."""
    stmt = select(Requirement).where(
        and_(
            Requirement.article_id == article_id,
            Requirement.element == element,
            Requirement.exact_quote == exact_quote
        )
    )
    return db.execute(stmt).scalar_one_or_none()


def create_or_update_requirement(
    db: Session,
    article: Article,
    req_data: Dict[str, Any],
    source_file: str,
    dry_run: bool = False
) -> Optional[Requirement]:
    """
    Create or update a requirement in the database.
    Returns the Requirement model instance or None if dry_run.
    """
    element = req_data.get("element", "unknown")
    exact_quote = req_data.get("exact_quote", "")

    if not exact_quote:
        exact_quote = req_data.get("description", f"Requirement for {element}")

    req_type = req_data.get("requirement_type", "dimensional")

    # Parse numeric values
    min_value = parse_numeric_value(req_data.get("min_value"))
    max_value = parse_numeric_value(req_data.get("max_value"))

    # Determine exact_value for non-numeric requirements
    exact_value = None
    if min_value is None and max_value is None:
        # Check for formula, ratio, or allowed_values
        if req_data.get("formula"):
            exact_value = req_data.get("formula")
        elif req_data.get("max_value") and isinstance(req_data.get("max_value"), str):
            exact_value = req_data.get("max_value")  # e.g., "1 in 50"
        elif req_data.get("allowed_values"):
            exact_value = str(req_data.get("allowed_values"))

    unit = req_data.get("unit", "")

    # Map applies_to to occupancy_groups where applicable
    applies_to = req_data.get("applies_to", [])
    occupancy_groups = None
    if applies_to:
        # Extract any standard occupancy group codes (A1, A2, B1, B2, C, D, E, F1, F2, F3)
        occupancy_codes = ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "C", "D", "E", "F1", "F2", "F3"]
        groups = [g for g in applies_to if g.upper() in occupancy_codes]
        if groups:
            occupancy_groups = groups

    if dry_run:
        logger.info(f"    [DRY RUN] Would create/update requirement: {element} ({req_type})")
        return None

    # Check for existing requirement
    existing = requirement_exists(db, article.id, element, exact_quote)

    if existing:
        # Update existing requirement
        existing.requirement_type = req_type
        existing.description = req_data.get("description")
        existing.min_value = min_value
        existing.max_value = max_value
        existing.exact_value = exact_value
        existing.unit = unit
        existing.occupancy_groups = occupancy_groups
        existing.is_mandatory = True
        existing.updated_at = datetime.utcnow()
        logger.debug(f"    Updated requirement: {element}")
        return existing

    # Create new requirement
    requirement = Requirement(
        id=uuid.uuid4(),
        article_id=article.id,
        requirement_type=req_type,
        element=element,
        description=req_data.get("description"),
        min_value=min_value,
        max_value=max_value,
        exact_value=exact_value,
        unit=unit,
        exact_quote=exact_quote,
        is_mandatory=True,
        applies_to_part_9=True,
        applies_to_part_3=False,
        occupancy_groups=occupancy_groups,
        extraction_method="import",
        extraction_confidence="HIGH",
        extraction_date=datetime.utcnow(),
        source_document=source_file,
        source_edition="NBC(AE) 2023",
        is_verified=False,
    )
    db.add(requirement)
    logger.debug(f"    Created requirement: {element}")
    return requirement


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def process_section_file(
    db: Session,
    file_path: Path,
    code: Code,
    dry_run: bool = False
) -> Tuple[int, int]:
    """
    Process a single section JSON file.
    Returns tuple of (articles_count, requirements_count).
    """
    data = load_json_file(file_path)

    metadata = data.get("metadata", {})
    section = metadata.get("section", "")
    section_title = metadata.get("section_title", "")
    section_number = extract_section_number(section)
    source_file = metadata.get("source_file", file_path.name)

    logger.info(f"Processing section {section}: {section_title}")

    articles = data.get("articles", [])
    articles_count = 0
    requirements_count = 0

    for article_data in articles:
        article = create_or_update_article(
            db, code, article_data, section_number, dry_run
        )
        if article:
            articles_count += 1

            # Process requirements for this article
            for req_data in article_data.get("requirements", []):
                req = create_or_update_requirement(
                    db, article, req_data, source_file, dry_run
                )
                if req:
                    requirements_count += 1

    return articles_count, requirements_count


def main():
    """Main entry point for the data loading script."""
    parser = argparse.ArgumentParser(
        description="Load NBC structured JSON data into PostgreSQL database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete existing NBC data and reload (WARNING: destructive)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose debug logging"
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    settings = get_settings()
    data_dir = Path(settings.data_dir) / "codes"

    # Find all structured JSON files
    json_files = sorted(
        glob(str(data_dir / "nbc_section_*_structured.json")),
        key=lambda x: float(Path(x).name.split("_")[2].replace("_structured.json", ""))
    )

    if not json_files:
        logger.error(f"No NBC section files found in {data_dir}")
        sys.exit(1)

    logger.info(f"Found {len(json_files)} NBC section files to process")

    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")

    # Create database session
    db = SessionLocal()

    try:
        # Get or create the NBC code entry
        # Use metadata from the first file
        first_file_data = load_json_file(Path(json_files[0]))
        metadata = first_file_data.get("metadata", {})
        code = get_or_create_code(db, metadata)

        if args.force and not args.dry_run:
            logger.warning("FORCE MODE - Deleting existing requirements and articles for this code")
            # Delete in order due to foreign key constraints
            db.query(RequirementCondition).filter(
                RequirementCondition.requirement_id.in_(
                    select(Requirement.id).where(
                        Requirement.article_id.in_(
                            select(Article.id).where(Article.code_id == code.id)
                        )
                    )
                )
            ).delete(synchronize_session=False)
            db.query(Requirement).filter(
                Requirement.article_id.in_(
                    select(Article.id).where(Article.code_id == code.id)
                )
            ).delete(synchronize_session=False)
            db.query(Article).filter(Article.code_id == code.id).delete()
            db.commit()
            logger.info("Existing data deleted")

        total_articles = 0
        total_requirements = 0

        for json_file in json_files:
            file_path = Path(json_file)
            articles, requirements = process_section_file(
                db, file_path, code, args.dry_run
            )
            total_articles += articles
            total_requirements += requirements

            if not args.dry_run:
                # Commit after each section file
                db.commit()

        logger.info("=" * 60)
        logger.info(f"Processing complete!")
        logger.info(f"  Total articles: {total_articles}")
        logger.info(f"  Total requirements: {total_requirements}")

        if args.dry_run:
            logger.info("(DRY RUN - no changes were made)")
        else:
            # Final commit
            db.commit()
            logger.info("All changes committed to database")

    except Exception as e:
        logger.error(f"Error during processing: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
