#!/usr/bin/env python3
"""
Load all extracted JSON data into the database.

This script loads:
1. NBC Part 9 (32 sections with detailed requirements)
2. NECB-2020 (Energy Code)
3. NFC-AE-2023 (Fire Code)
4. NPC-2020 (Plumbing Code)
5. Land Use Bylaw zones
6. STANDATA bulletins
7. Permit guides and standards

Usage:
    python load_all_to_database.py [--force] [--verbose]
"""

import argparse
import json
import sys
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base, engine, SessionLocal
from app.models.codes import Code, Article, Requirement, RequirementCondition
from app.models.standata import Standata
from app.models.zones import Zone, ZoneRule

# Paths
BASE_DIR = Path("/Users/mohmmadhanafy/Building-code-consultant")
DATA_DIR = BASE_DIR / "data" / "codes"


def get_or_create_code(db, code_type: str, name: str, short_name: str,
                       version: str, jurisdiction: str, effective_date: date) -> Code:
    """Get existing code or create new one."""
    existing = db.query(Code).filter(
        Code.short_name == short_name,
        Code.version == version
    ).first()

    if existing:
        print(f"  Using existing code: {short_name} {version}")
        return existing

    code = Code(
        id=uuid.uuid4(),
        code_type=code_type,
        name=name,
        short_name=short_name,
        version=version,
        jurisdiction=jurisdiction,
        effective_date=effective_date,
        is_current=True
    )
    db.add(code)
    db.flush()
    print(f"  Created code: {short_name} {version}")
    return code


def load_nbc_part9(db, verbose: bool = False) -> int:
    """Load NBC Part 9 sections from structured JSON files."""
    print("\n" + "=" * 60)
    print("Loading NBC Part 9 Sections")
    print("=" * 60)

    # Create or get NBC code entry
    nbc_code = get_or_create_code(
        db,
        code_type="building",
        name="National Building Code of Canada - Alberta Edition",
        short_name="NBC(AE)",
        version="2023",
        jurisdiction="Alberta",
        effective_date=date(2024, 5, 1)
    )

    # Find all NBC section files
    section_files = sorted(DATA_DIR.glob("nbc_section_9.*_structured.json"))
    print(f"  Found {len(section_files)} section files")

    total_articles = 0
    total_requirements = 0

    for json_file in section_files:
        try:
            with open(json_file) as f:
                data = json.load(f)

            section = data.get("metadata", {}).get("section", "")
            section_title = data.get("metadata", {}).get("section_title", "")
            articles = data.get("articles", [])

            print(f"\n  Section {section}: {section_title}")
            print(f"    Articles: {len(articles)}")

            section_reqs = 0
            for article_data in articles:
                # Check if article already exists
                existing = db.query(Article).filter(
                    Article.code_id == nbc_code.id,
                    Article.article_number == article_data.get("article_number")
                ).first()

                if existing:
                    if verbose:
                        print(f"      Skipping existing: {article_data.get('article_number')}")
                    continue

                # Create article
                article = Article(
                    id=uuid.uuid4(),
                    code_id=nbc_code.id,
                    article_number=article_data.get("article_number", ""),
                    title=article_data.get("title", ""),
                    full_text=article_data.get("full_text", article_data.get("title", "")),
                    part_number=9,
                    section_number=int(section.split(".")[-1]) if "." in section else None,
                )
                db.add(article)
                db.flush()
                total_articles += 1

                # Create requirements
                for req_data in article_data.get("requirements", []):
                    # Handle non-numeric values
                    min_val = req_data.get("min_value")
                    max_val = req_data.get("max_value")
                    exact_val = req_data.get("exact_value")

                    # Convert non-numeric min/max to exact_value
                    if min_val is not None and not isinstance(min_val, (int, float)):
                        exact_val = str(min_val)
                        min_val = None
                    if max_val is not None and not isinstance(max_val, (int, float)):
                        if exact_val:
                            exact_val = f"{exact_val}, max: {max_val}"
                        else:
                            exact_val = str(max_val)
                        max_val = None

                    requirement = Requirement(
                        id=uuid.uuid4(),
                        article_id=article.id,
                        requirement_type=req_data.get("requirement_type", "prescriptive"),
                        element=req_data.get("element", req_data.get("id", "")),
                        description=req_data.get("description", ""),
                        min_value=min_val,
                        max_value=max_val,
                        exact_value=exact_val,
                        unit=req_data.get("unit"),
                        exact_quote=req_data.get("exact_quote", req_data.get("description", "")),
                        extraction_method="import",
                        extraction_confidence="HIGH",
                        source_document="NBC-AE-2023.pdf",
                        source_edition="2023",
                        is_verified=False
                    )
                    db.add(requirement)
                    section_reqs += 1
                    total_requirements += 1

            print(f"    Requirements: {section_reqs}")
            db.commit()

        except Exception as e:
            print(f"    Error loading {json_file.name}: {e}")
            db.rollback()

    print(f"\n  NBC Part 9 Total: {total_articles} articles, {total_requirements} requirements")
    return total_articles


def load_other_codes(db, verbose: bool = False) -> int:
    """Load NECB, NFC, NPC from structured JSON."""
    print("\n" + "=" * 60)
    print("Loading Other Building Codes")
    print("=" * 60)

    codes_to_load = [
        {
            "file": "necb_2020_structured.json",
            "code_type": "energy",
            "name": "National Energy Code of Canada for Buildings",
            "short_name": "NECB",
            "version": "2020",
            "jurisdiction": "Canada",
            "effective_date": date(2020, 1, 1)
        },
        {
            "file": "nfc_ae_2023_structured.json",
            "code_type": "fire",
            "name": "National Fire Code - Alberta Edition",
            "short_name": "NFC(AE)",
            "version": "2023",
            "jurisdiction": "Alberta",
            "effective_date": date(2024, 5, 1)
        },
        {
            "file": "npc_2020_structured.json",
            "code_type": "plumbing",
            "name": "National Plumbing Code of Canada",
            "short_name": "NPC",
            "version": "2020",
            "jurisdiction": "Canada",
            "effective_date": date(2020, 1, 1)
        },
    ]

    total_articles = 0

    for code_info in codes_to_load:
        json_path = DATA_DIR / code_info["file"]
        if not json_path.exists():
            print(f"  Skipping {code_info['short_name']}: file not found")
            continue

        try:
            with open(json_path) as f:
                data = json.load(f)

            code = get_or_create_code(
                db,
                code_type=code_info["code_type"],
                name=code_info["name"],
                short_name=code_info["short_name"],
                version=code_info["version"],
                jurisdiction=code_info["jurisdiction"],
                effective_date=code_info["effective_date"]
            )

            code_articles = 0
            for part_data in data.get("parts", []):
                part_num = part_data.get("part_number", 0)
                part_name = part_data.get("name", "")
                articles = part_data.get("articles", [])

                for article_num in articles:
                    # Check if already exists
                    existing = db.query(Article).filter(
                        Article.code_id == code.id,
                        Article.article_number == article_num
                    ).first()

                    if existing:
                        continue

                    article = Article(
                        id=uuid.uuid4(),
                        code_id=code.id,
                        article_number=article_num,
                        title=f"Part {part_num}: {part_name}",
                        full_text=f"Article {article_num} from {part_name}",
                        part_number=part_num,
                    )
                    db.add(article)
                    code_articles += 1
                    total_articles += 1

            db.commit()
            print(f"  {code_info['short_name']}: {code_articles} articles loaded")

        except Exception as e:
            print(f"  Error loading {code_info['short_name']}: {e}")
            db.rollback()

    return total_articles


def load_standata(db, verbose: bool = False) -> int:
    """Load STANDATA bulletins from JSON."""
    print("\n" + "=" * 60)
    print("Loading STANDATA Bulletins")
    print("=" * 60)

    json_path = DATA_DIR / "standata_bulletins.json"
    if not json_path.exists():
        print("  File not found: standata_bulletins.json")
        return 0

    with open(json_path) as f:
        data = json.load(f)

    bulletins = data.get("all_bulletins", [])
    print(f"  Found {len(bulletins)} bulletins")

    loaded = 0
    for bulletin_data in bulletins:
        try:
            bulletin_number = bulletin_data.get("bulletin_number", "")

            # Check if already exists
            existing = db.query(Standata).filter(
                Standata.bulletin_number == bulletin_number
            ).first()

            if existing:
                if verbose:
                    print(f"    Skipping existing: {bulletin_number}")
                continue

            standata = Standata(
                id=uuid.uuid4(),
                bulletin_number=bulletin_number,
                title=bulletin_data.get("title", "")[:500],
                category=bulletin_data.get("category", "BCI"),
                effective_date=None,  # Parse from string if available
                summary=bulletin_data.get("summary", ""),
                full_text=bulletin_data.get("full_text", ""),
                code_references=bulletin_data.get("code_references"),
                keywords=bulletin_data.get("keywords"),
                pdf_path=bulletin_data.get("pdf_filename", ""),
                pdf_filename=bulletin_data.get("pdf_filename", ""),
                extraction_confidence=bulletin_data.get("extraction_confidence", "HIGH"),
            )
            db.add(standata)
            loaded += 1

        except Exception as e:
            print(f"    Error loading bulletin {bulletin_data.get('bulletin_number')}: {e}")

    db.commit()
    print(f"  Loaded {loaded} bulletins")
    return loaded


def load_zones(db, verbose: bool = False) -> int:
    """Load Land Use Bylaw zones."""
    print("\n" + "=" * 60)
    print("Loading Land Use Bylaw Zones")
    print("=" * 60)

    json_path = DATA_DIR / "land_use_bylaw_structured.json"
    if not json_path.exists():
        print("  File not found: land_use_bylaw_structured.json")
        return 0

    with open(json_path) as f:
        data = json.load(f)

    # Create LUB code entry
    lub_code = get_or_create_code(
        db,
        code_type="zoning",
        name="City of Calgary Land Use Bylaw",
        short_name="LUB",
        version="1P2007",
        jurisdiction="Calgary",
        effective_date=date(2025, 1, 1)
    )

    districts = data.get("districts", [])
    print(f"  Found {len(districts)} districts")

    # Track loaded zones to avoid duplicates
    loaded_codes = set()

    loaded = 0
    for district in districts:
        try:
            zone_code = district.get("code", "")

            # Skip if already loaded in this batch
            if zone_code in loaded_codes:
                continue
            loaded_codes.add(zone_code)

            # Check if already exists in database
            existing = db.query(Zone).filter(
                Zone.zone_code == zone_code
            ).first()

            if existing:
                if verbose:
                    print(f"    Skipping existing: {zone_code}")
                continue

            # Determine category from zone code
            if zone_code.startswith("R-"):
                category = "residential"
            elif zone_code.startswith("M-"):
                category = "multi_residential"
            elif zone_code.startswith("C-"):
                category = "commercial"
            elif zone_code.startswith("I-"):
                category = "industrial"
            elif zone_code.startswith("S-"):
                category = "special"
            else:
                category = "other"

            zone = Zone(
                id=uuid.uuid4(),
                code_id=lub_code.id,
                zone_code=zone_code,
                zone_name=district.get("category", zone_code),
                category=category,
            )
            db.add(zone)
            loaded += 1

        except Exception as e:
            print(f"    Error loading zone {district.get('code')}: {e}")

    db.commit()
    print(f"  Loaded {loaded} zones")
    return loaded


def load_permits_standards(db, verbose: bool = False) -> int:
    """Load permit guides and standards as reference documents."""
    print("\n" + "=" * 60)
    print("Loading Permit Guides & Standards")
    print("=" * 60)

    json_path = DATA_DIR / "permits_standards_extracted.json"
    if not json_path.exists():
        print("  File not found: permits_standards_extracted.json")
        return 0

    with open(json_path) as f:
        data = json.load(f)

    # Create a reference code for guides
    guides_code = get_or_create_code(
        db,
        code_type="standata",  # Using standata type for reference docs
        name="Calgary Permit Guides and Design Standards",
        short_name="GUIDES",
        version="2024",
        jurisdiction="Calgary",
        effective_date=date(2024, 1, 1)
    )

    loaded = 0

    # Load permit guides as articles
    for guide in data.get("permit_guides", []):
        try:
            filename = guide.get("metadata", {}).get("filename", "")
            doc_type = guide.get("metadata", {}).get("document_type", "guide")

            # Check if already exists
            existing = db.query(Article).filter(
                Article.code_id == guides_code.id,
                Article.article_number == filename
            ).first()

            if existing:
                continue

            article = Article(
                id=uuid.uuid4(),
                code_id=guides_code.id,
                article_number=filename,
                title=doc_type.replace("_", " ").title(),
                full_text=guide.get("full_text", "")[:50000],
            )
            db.add(article)
            loaded += 1

        except Exception as e:
            print(f"    Error loading guide: {e}")

    # Load standards as articles
    for standard in data.get("standards", []):
        try:
            filename = standard.get("metadata", {}).get("filename", "")
            doc_type = standard.get("metadata", {}).get("document_type", "standard")

            # Check if already exists
            existing = db.query(Article).filter(
                Article.code_id == guides_code.id,
                Article.article_number == filename
            ).first()

            if existing:
                continue

            article = Article(
                id=uuid.uuid4(),
                code_id=guides_code.id,
                article_number=filename,
                title=doc_type.replace("_", " ").title(),
                full_text=standard.get("full_text", "")[:50000],
            )
            db.add(article)
            loaded += 1

        except Exception as e:
            print(f"    Error loading standard: {e}")

    db.commit()
    print(f"  Loaded {loaded} reference documents")
    return loaded


def main():
    parser = argparse.ArgumentParser(description="Load all extracted data into database")
    parser.add_argument("--force", action="store_true", help="Force reload (delete existing data)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--only", choices=["nbc", "codes", "standata", "zones", "guides"],
                       help="Only load specific data type")
    args = parser.parse_args()

    print("=" * 60)
    print("Database Loader - All Extracted JSON")
    print("=" * 60)

    # Initialize database
    print("\nInitializing database...")
    try:
        Base.metadata.create_all(bind=engine)
        print("  Tables created/verified")
    except Exception as e:
        print(f"  Error creating tables: {e}")
        return 1

    db = SessionLocal()

    try:
        if args.force:
            print("\n  WARNING: Force mode - clearing existing data...")
            # Import Parcel model for deletion
            from app.models.zones import Parcel
            from app.models.projects import Project

            # Delete in correct order for foreign key constraints
            try:
                db.query(RequirementCondition).delete()
                db.query(Requirement).delete()
                db.query(Article).delete()
                db.query(Standata).delete()
                db.query(Project).delete()
                db.query(Parcel).delete()
                db.query(ZoneRule).delete()
                db.query(Zone).delete()
                db.query(Code).delete()
                db.commit()
                print("  Existing data cleared")
            except Exception as e:
                print(f"  Warning during cleanup: {e}")
                db.rollback()
                # Try with raw SQL for more control
                db.execute(text("TRUNCATE requirement_conditions, requirements, articles, standata, projects, parcels, zone_rules, zones, codes CASCADE"))
                db.commit()
                print("  Existing data cleared (via TRUNCATE CASCADE)")

        totals = {
            "nbc_articles": 0,
            "other_articles": 0,
            "standata": 0,
            "zones": 0,
            "guides": 0
        }

        if args.only is None or args.only == "nbc":
            totals["nbc_articles"] = load_nbc_part9(db, args.verbose)

        if args.only is None or args.only == "codes":
            totals["other_articles"] = load_other_codes(db, args.verbose)

        if args.only is None or args.only == "standata":
            totals["standata"] = load_standata(db, args.verbose)

        if args.only is None or args.only == "zones":
            totals["zones"] = load_zones(db, args.verbose)

        if args.only is None or args.only == "guides":
            totals["guides"] = load_permits_standards(db, args.verbose)

        # Final summary
        print("\n" + "=" * 60)
        print("LOADING COMPLETE")
        print("=" * 60)
        print(f"  NBC Part 9 Articles: {totals['nbc_articles']}")
        print(f"  Other Code Articles: {totals['other_articles']}")
        print(f"  STANDATA Bulletins: {totals['standata']}")
        print(f"  Land Use Zones: {totals['zones']}")
        print(f"  Reference Guides: {totals['guides']}")
        print(f"\n  TOTAL ITEMS LOADED: {sum(totals.values())}")

        # Show database counts
        print("\n  Database Status:")
        print(f"    Codes: {db.query(Code).count()}")
        print(f"    Articles: {db.query(Article).count()}")
        print(f"    Requirements: {db.query(Requirement).count()}")
        print(f"    STANDATA: {db.query(Standata).count()}")
        print(f"    Zones: {db.query(Zone).count()}")

    except Exception as e:
        print(f"\nError during loading: {e}")
        db.rollback()
        raise
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
