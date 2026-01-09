#!/usr/bin/env python3
"""
Import NBC(AE) 2023 building code requirements into the database.

This script:
1. Loads structured code data from JSON files
2. Creates or updates Code, Article, and Requirement records
3. Handles requirement conditions for complex rules

Usage:
    python import_nbc_codes.py [--verify] [--section SECTION]
"""
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.codes import Code, Article, Requirement, RequirementCondition


# Data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "codes"


def get_or_create_code(db: Session) -> Code:
    """Get or create the NBC(AE) 2023 code record."""
    code = db.query(Code).filter(
        Code.short_name == "NBC(AE)",
        Code.version == "2023"
    ).first()

    if not code:
        code = Code(
            id=uuid4(),
            code_type="building",
            name="National Building Code of Canada 2023 - Alberta Edition",
            short_name="NBC(AE)",
            version="2023",
            jurisdiction="Alberta",
            effective_date=date(2024, 5, 1),
            source_url="https://nrc.canada.ca/en/certifications-evaluations-standards/codes-canada/codes-canada-publications/national-building-code-2023-alberta-edition",
            source_file="NBC-AE-2023.pdf",
            is_current=True,
            created_at=datetime.utcnow()
        )
        db.add(code)
        db.commit()
        db.refresh(code)
        print(f"Created code record: {code.name}")
    else:
        print(f"Using existing code record: {code.name}")

    return code


def parse_numeric_value(value):
    """Parse a numeric value from various formats."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        # Handle ratio strings like "1 in 50"
        if " in " in value:
            parts = value.split(" in ")
            try:
                return Decimal(str(float(parts[0]) / float(parts[1])))
            except (ValueError, ZeroDivisionError):
                return None
        try:
            return Decimal(value)
        except:
            return None
    return None


def import_section(db: Session, code: Code, json_file: Path, verify_only: bool = False):
    """Import a single section from a structured JSON file."""

    if not json_file.exists():
        print(f"Error: File not found: {json_file}")
        return

    print(f"\nImporting from: {json_file.name}")

    with open(json_file, 'r') as f:
        data = json.load(f)

    metadata = data.get('metadata', {})
    articles_data = data.get('articles', [])

    print(f"  Section: {metadata.get('section')} - {metadata.get('section_title')}")
    print(f"  Articles: {len(articles_data)}")

    if verify_only:
        # Just print summary for verification
        for article_data in articles_data:
            reqs = article_data.get('requirements', [])
            print(f"    {article_data.get('article_number')}: {article_data.get('title')} ({len(reqs)} requirements)")
        return

    articles_created = 0
    requirements_created = 0

    for article_data in articles_data:
        article_number = article_data.get('article_number')

        # Check if article exists
        existing_article = db.query(Article).filter(
            Article.code_id == code.id,
            Article.article_number == article_number
        ).first()

        if existing_article:
            article = existing_article
            print(f"    Updating article: {article_number}")
        else:
            # Parse article number components
            parts = article_number.split('.')
            part_num = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else None
            div_num = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            sec_num = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None

            article = Article(
                id=uuid4(),
                code_id=code.id,
                article_number=article_number,
                title=article_data.get('title'),
                full_text=article_data.get('full_text', ''),
                part_number=part_num,
                division_number=div_num,
                section_number=sec_num,
                page_number=int(metadata.get('pages', '0').split('-')[0]) if metadata.get('pages') else None,
                created_at=datetime.utcnow()
            )
            db.add(article)
            db.flush()  # Get the ID
            articles_created += 1
            print(f"    Created article: {article_number}")

        # Import requirements for this article
        for req_data in article_data.get('requirements', []):
            req_id = req_data.get('id', str(uuid4()))

            # Check for existing requirement by element and article
            existing_req = db.query(Requirement).filter(
                Requirement.article_id == article.id,
                Requirement.element == req_data.get('element'),
                Requirement.exact_quote == req_data.get('exact_quote')
            ).first()

            if existing_req:
                continue  # Skip duplicate

            # Determine occupancy groups from applies_to
            applies_to = req_data.get('applies_to', [])
            occupancy_groups = None
            if 'residential' in applies_to:
                occupancy_groups = ['C']
            elif 'non_residential' in applies_to:
                occupancy_groups = ['A1', 'A2', 'B1', 'B2', 'D', 'E', 'F1', 'F2', 'F3']

            # Parse min/max values
            min_val = parse_numeric_value(req_data.get('min_value'))
            max_val = parse_numeric_value(req_data.get('max_value'))

            # Handle ratio values
            if 'ratio' in req_data:
                if min_val is None:
                    min_val = parse_numeric_value(req_data.get('ratio'))
                if max_val is None and 'max_value' in req_data:
                    max_val = parse_numeric_value(req_data.get('ratio'))

            requirement = Requirement(
                id=uuid4(),
                article_id=article.id,
                requirement_type=req_data.get('requirement_type', 'dimensional'),
                element=req_data.get('element'),
                description=req_data.get('description'),
                min_value=min_val,
                max_value=max_val,
                exact_value=req_data.get('formula') or (str(req_data.get('allowed_values')) if req_data.get('allowed_values') else None),
                unit=req_data.get('unit'),
                exact_quote=req_data.get('exact_quote'),
                is_mandatory=True,
                applies_to_part_9=True,
                applies_to_part_3=False,
                occupancy_groups=occupancy_groups,
                extraction_method="pdfplumber_structured",
                extraction_confidence="HIGH",
                extraction_date=datetime.utcnow(),
                extraction_model="claude-opus-4-5-20251101",
                source_document=f"{code.short_name} {code.version}",
                source_page=int(metadata.get('pages', '0').split('-')[0]) if metadata.get('pages') else None,
                source_edition=code.version,
                is_verified=False,
                created_at=datetime.utcnow()
            )
            db.add(requirement)
            requirements_created += 1

            # Handle conditions if present
            condition = req_data.get('condition')
            if condition:
                req_condition = RequirementCondition(
                    id=uuid4(),
                    requirement_id=requirement.id,
                    field="condition",
                    operator="=",
                    value_text=condition,
                    condition_order=0,
                    created_at=datetime.utcnow()
                )
                db.add(req_condition)

            # Handle exceptions as conditions
            exceptions = req_data.get('exceptions', [])
            for i, exc in enumerate(exceptions):
                exc_condition = RequirementCondition(
                    id=uuid4(),
                    requirement_id=requirement.id,
                    field="exception",
                    operator="NOT_IN",
                    value_text=exc,
                    condition_order=i + 1,
                    created_at=datetime.utcnow()
                )
                db.add(exc_condition)

    db.commit()
    print(f"  Created {articles_created} articles and {requirements_created} requirements")


def main():
    parser = argparse.ArgumentParser(description="Import NBC building code requirements")
    parser.add_argument("--verify", action="store_true", help="Verify data without importing")
    parser.add_argument("--section", type=str, help="Import specific section (e.g., '9.8')")
    args = parser.parse_args()

    print("NBC(AE) 2023 Code Import Script")
    print("=" * 50)

    db = SessionLocal()

    try:
        # Get or create the code record
        code = get_or_create_code(db)

        # Find structured JSON files
        if args.section:
            json_files = list(DATA_DIR.glob(f"nbc_section_{args.section}_structured.json"))
        else:
            json_files = list(DATA_DIR.glob("nbc_section_*_structured.json"))

        if not json_files:
            print(f"No structured JSON files found in {DATA_DIR}")
            return

        print(f"Found {len(json_files)} section file(s)")

        for json_file in sorted(json_files):
            import_section(db, code, json_file, verify_only=args.verify)

        # Print summary
        total_articles = db.query(Article).filter(Article.code_id == code.id).count()
        total_requirements = db.query(Requirement).join(Article).filter(Article.code_id == code.id).count()

        print(f"\n{'Verification' if args.verify else 'Import'} complete!")
        print(f"  Total articles in database: {total_articles}")
        print(f"  Total requirements in database: {total_requirements}")

    except Exception as e:
        print(f"Error during import: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
