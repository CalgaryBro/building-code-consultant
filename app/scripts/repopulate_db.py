#!/usr/bin/env python3
"""
Database Repopulation Script for VLM-Extracted Building Codes

Loads VLM JSON files from data/codes/vlm/ and repopulates the database with:
1. Clean, properly-formatted article text
2. Generated embeddings (all-MiniLM-L6-v2, 384 dimensions)
3. Extraction tracking metadata

Usage:
    python repopulate_db.py --source data/codes/vlm/   # Load all VLM JSON files
    python repopulate_db.py --file nbc_ae_2023_part1_vlm.json  # Load specific file
    python repopulate_db.py --backup                   # Create backup first
    python repopulate_db.py --verify                   # Verify database counts
    python repopulate_db.py --dry-run                  # Show what would be done
"""

import argparse
import json
import logging
import re
import subprocess
import sys
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('repopulate_db.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = Path("/Users/mohmmadhanafy/Building-code-consultant")
VLM_OUTPUT_DIR = BASE_DIR / "data" / "codes" / "vlm"
BACKUP_DIR = BASE_DIR / "data" / "backups"

# Database URL (same as app config)
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/calgary_codes"

# Code type mapping based on code name
CODE_TYPE_MAP = {
    "NBC": "building",
    "NECB": "energy",
    "NFC": "fire",
    "NPC": "plumbing",
    "LUB": "zoning",
    "STANDATA": "standata",
}


def get_db_session():
    """Create a database session."""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session(), engine


def parse_article_number(article_num: str) -> Dict[str, Optional[int]]:
    """Parse article number into components (part, section, etc)."""
    result = {
        "part_number": None,
        "division_number": None,
        "section_number": None,
    }

    # Match patterns like 9.8.4.1, 1.3.3.3, etc.
    match = re.match(r'(\d+)\.(\d+)\.?(\d+)?\.?(\d+)?', article_num)
    if match:
        result["part_number"] = int(match.group(1))
        if match.group(2):
            result["section_number"] = int(match.group(2))

    return result


def get_code_type(code_name: str) -> str:
    """Determine code type from code name."""
    for prefix, code_type in CODE_TYPE_MAP.items():
        if prefix in code_name.upper():
            return code_type
    return "building"


def create_embedding_text(article: Dict) -> str:
    """Create optimized text for embedding generation."""
    article_num = article.get("article_number", "")
    title = article.get("title", "")
    full_text = article.get("full_text", "")

    # Combine article number, title, and text (truncate to 2000 chars)
    embedding_text = f"{article_num} {title}. {full_text}"
    return embedding_text[:2000]


def load_embedding_service():
    """Load the embedding service."""
    try:
        from app.services.embedding_service import get_embedding_service
        service = get_embedding_service()
        # Verify model is loaded
        if not service._ensure_model_loaded():
            logger.error("Failed to load embedding model")
            return None
        logger.info("Embedding service loaded successfully")
        return service
    except ImportError as e:
        logger.error(f"Cannot import embedding service: {e}")
        return None


def backup_database():
    """Create a PostgreSQL database backup."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"calgary_codes_backup_{timestamp}.sql"

    logger.info(f"Creating database backup: {backup_file}")

    try:
        result = subprocess.run([
            "pg_dump",
            "-h", "localhost",
            "-p", "5432",
            "-U", "postgres",
            "-d", "calgary_codes",
            "-f", str(backup_file),
        ], capture_output=True, text=True, env={"PGPASSWORD": "postgres"})

        if result.returncode == 0:
            logger.info(f"Backup created: {backup_file}")
            return backup_file
        else:
            logger.error(f"Backup failed: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"Backup error: {e}")
        return None


def add_extraction_columns(session, engine):
    """Add extraction tracking columns if they don't exist."""
    columns_to_add = [
        ("articles", "extraction_model", "VARCHAR(100)"),
        ("articles", "extraction_confidence", "VARCHAR(20)"),
        ("articles", "vlm_extracted", "BOOLEAN DEFAULT FALSE"),
        ("articles", "extraction_date", "TIMESTAMP"),
    ]

    for table, column, data_type in columns_to_add:
        try:
            session.execute(text(
                f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {data_type}"
            ))
            logger.info(f"Added column {table}.{column}")
        except Exception as e:
            logger.debug(f"Column {column} might already exist: {e}")

    session.commit()


def get_or_create_code(session, code_name: str, metadata: Dict) -> uuid.UUID:
    """Get existing code or create new one, return code ID."""
    from app.models.codes import Code

    # Parse version from code name (e.g., "NBC(AE) 2023" -> "2023")
    version_match = re.search(r'(\d{4})', code_name)
    version = version_match.group(1) if version_match else "2023"

    # Generate short name (e.g., "NBC(AE) 2023" -> "NBC(AE)")
    short_name = re.sub(r'\s*\d{4}\s*', '', code_name).strip()

    # Check if code exists
    existing = session.query(Code).filter(
        Code.short_name == short_name,
        Code.version == version
    ).first()

    if existing:
        logger.info(f"Using existing code: {short_name} {version} (ID: {existing.id})")
        return existing.id

    # Create new code
    code_type = get_code_type(code_name)
    new_code = Code(
        id=uuid.uuid4(),
        code_type=code_type,
        name=metadata.get("description", code_name),
        short_name=short_name,
        version=version,
        jurisdiction="Alberta",
        effective_date=date(2024, 5, 1),  # NBC(AE) 2023 effective date
        source_file=metadata.get("source_pdf", ""),
        is_current=True,
    )

    session.add(new_code)
    session.flush()

    logger.info(f"Created new code: {short_name} {version} (ID: {new_code.id})")
    return new_code.id


def clear_code_articles(session, code_id: uuid.UUID):
    """Clear existing articles for a code (for re-extraction)."""
    from app.models.codes import Article, Requirement, RequirementCondition

    # Get article IDs for this code
    article_ids = session.query(Article.id).filter(Article.code_id == code_id).all()
    article_ids = [a[0] for a in article_ids]

    if article_ids:
        # Delete conditions for requirements of these articles
        session.execute(text("""
            DELETE FROM requirement_conditions
            WHERE requirement_id IN (
                SELECT id FROM requirements WHERE article_id = ANY(:article_ids)
            )
        """), {"article_ids": article_ids})

        # Delete requirements for these articles
        session.execute(text("""
            DELETE FROM requirements WHERE article_id = ANY(:article_ids)
        """), {"article_ids": article_ids})

        # Delete articles
        session.execute(text("""
            DELETE FROM articles WHERE code_id = :code_id
        """), {"code_id": str(code_id)})

        session.commit()
        logger.info(f"Cleared {len(article_ids)} existing articles for code {code_id}")


def load_vlm_json(file_path: Path) -> Dict:
    """Load and validate a VLM extraction JSON file."""
    logger.info(f"Loading: {file_path}")

    with open(file_path, 'r') as f:
        data = json.load(f)

    # Validate structure
    if "articles" not in data:
        logger.warning(f"No 'articles' key in {file_path}")
        return None

    metadata = data.get("metadata", {})
    articles = data.get("articles", [])

    logger.info(f"  Code: {metadata.get('code_name', 'Unknown')}")
    logger.info(f"  Articles: {len(articles)}")
    logger.info(f"  Extraction model: {metadata.get('extraction_model', 'Unknown')}")

    return data


def insert_articles(session, code_id: uuid.UUID, articles: List[Dict],
                   metadata: Dict, embedding_service, dry_run: bool = False) -> int:
    """Insert articles into database with embeddings."""
    from app.models.codes import Article

    inserted = 0
    skipped = 0

    extraction_model = metadata.get("extraction_model", "qwen3-vl:30b")
    extraction_date = datetime.now()

    for i, article_data in enumerate(articles):
        article_num = article_data.get("article_number", "")
        title = article_data.get("title", "")
        full_text = article_data.get("full_text", "")

        # Skip empty articles
        if not article_num or not full_text:
            skipped += 1
            continue

        # Parse article number for part/section info
        parsed = parse_article_number(article_num)

        # Get page number
        pages = article_data.get("pages", [])
        page_number = pages[0] if pages else article_data.get("page_number")

        # Generate embedding
        embedding = None
        if embedding_service and not dry_run:
            embedding_text = create_embedding_text(article_data)
            embedding = embedding_service.embed_text(embedding_text)
            if embedding and (i + 1) % 50 == 0:
                logger.info(f"  Generated embeddings for {i + 1}/{len(articles)} articles")

        if dry_run:
            logger.info(f"  [DRY RUN] Would insert: {article_num} - {title[:50]}...")
            inserted += 1
            continue

        # Create article
        article = Article(
            id=uuid.uuid4(),
            code_id=code_id,
            article_number=article_num,
            title=title,
            full_text=full_text,
            part_number=parsed["part_number"],
            section_number=parsed["section_number"],
            page_number=page_number,
            embedding=embedding,
        )

        session.add(article)
        inserted += 1

        # Commit in batches
        if (i + 1) % 100 == 0:
            session.commit()
            logger.info(f"  Committed {i + 1}/{len(articles)} articles")

    # Final commit
    if not dry_run:
        session.commit()

    # Update extraction tracking columns using raw SQL (since they're dynamically added)
    if not dry_run:
        try:
            session.execute(text("""
                UPDATE articles
                SET extraction_model = :model,
                    extraction_confidence = 'HIGH',
                    vlm_extracted = TRUE,
                    extraction_date = :date
                WHERE code_id = :code_id
                AND extraction_model IS NULL
            """), {
                "model": extraction_model,
                "date": extraction_date,
                "code_id": str(code_id)
            })
            session.commit()
        except Exception as e:
            logger.warning(f"Could not update extraction tracking columns: {e}")

    logger.info(f"  Inserted: {inserted}, Skipped: {skipped}")
    return inserted


def update_search_vectors(session):
    """Update full-text search vectors for all articles."""
    logger.info("Updating full-text search vectors...")

    try:
        session.execute(text("""
            UPDATE articles
            SET search_vector = to_tsvector('english',
                coalesce(article_number, '') || ' ' ||
                coalesce(title, '') || ' ' ||
                coalesce(full_text, '')
            )
            WHERE search_vector IS NULL OR search_vector = ''::tsvector
        """))
        session.commit()
        logger.info("Search vectors updated")
    except Exception as e:
        logger.error(f"Failed to update search vectors: {e}")


def verify_database(session):
    """Verify database counts and data quality."""
    logger.info("\n" + "=" * 60)
    logger.info("DATABASE VERIFICATION")
    logger.info("=" * 60)

    # Count by code
    result = session.execute(text("""
        SELECT c.short_name, c.version, COUNT(a.id) as article_count,
               COUNT(a.embedding) as with_embedding,
               COUNT(a.search_vector) as with_search_vector
        FROM codes c
        LEFT JOIN articles a ON c.id = a.code_id
        GROUP BY c.id, c.short_name, c.version
        ORDER BY c.short_name
    """))

    print("\nCode Summary:")
    print("-" * 70)
    print(f"{'Code':<20} {'Version':<10} {'Articles':<12} {'Embeddings':<12} {'FTS':<10}")
    print("-" * 70)

    total_articles = 0
    total_embeddings = 0

    for row in result:
        print(f"{row[0]:<20} {row[1]:<10} {row[2]:<12} {row[3]:<12} {row[4]:<10}")
        total_articles += row[2]
        total_embeddings += row[3]

    print("-" * 70)
    print(f"{'TOTAL':<30} {total_articles:<12} {total_embeddings:<12}")

    # VLM extraction stats
    result = session.execute(text("""
        SELECT extraction_model, COUNT(*)
        FROM articles
        WHERE extraction_model IS NOT NULL
        GROUP BY extraction_model
    """))

    print("\n\nExtraction Methods:")
    print("-" * 40)
    for row in result:
        print(f"  {row[0]}: {row[1]} articles")

    # Sample articles
    result = session.execute(text("""
        SELECT article_number, title, LENGTH(full_text) as text_len
        FROM articles
        WHERE vlm_extracted = TRUE
        ORDER BY RANDOM()
        LIMIT 5
    """))

    print("\n\nSample VLM-Extracted Articles:")
    print("-" * 70)
    for row in result:
        print(f"  {row[0]}: {row[1][:40]}... ({row[2]} chars)")

    return total_articles, total_embeddings


def process_vlm_file(file_path: Path, session, embedding_service,
                    clear_existing: bool = False, dry_run: bool = False) -> Tuple[int, int]:
    """Process a single VLM JSON file."""
    data = load_vlm_json(file_path)
    if not data:
        return 0, 0

    metadata = data.get("metadata", {})
    articles = data.get("articles", [])
    code_name = metadata.get("code_name", "Unknown")

    # Get or create code
    code_id = get_or_create_code(session, code_name, metadata)

    # Clear existing articles if requested
    if clear_existing and not dry_run:
        clear_code_articles(session, code_id)

    # Insert articles
    inserted = insert_articles(session, code_id, articles, metadata,
                               embedding_service, dry_run)

    return len(articles), inserted


def main():
    parser = argparse.ArgumentParser(description="Repopulate database with VLM extractions")
    parser.add_argument("--source", type=Path, default=VLM_OUTPUT_DIR,
                       help="Directory containing VLM JSON files")
    parser.add_argument("--file", type=str,
                       help="Specific file to load (within source directory)")
    parser.add_argument("--backup", action="store_true",
                       help="Create database backup before loading")
    parser.add_argument("--clear", action="store_true",
                       help="Clear existing articles before loading")
    parser.add_argument("--verify", action="store_true",
                       help="Only verify database counts")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without making changes")
    parser.add_argument("--no-embeddings", action="store_true",
                       help="Skip embedding generation (faster for testing)")

    args = parser.parse_args()

    # Connect to database
    logger.info("Connecting to database...")
    session, engine = get_db_session()

    # Verify only mode
    if args.verify:
        verify_database(session)
        session.close()
        return

    # Create backup if requested
    if args.backup:
        backup_file = backup_database()
        if not backup_file:
            logger.warning("Backup failed, continuing anyway...")

    # Add extraction tracking columns
    logger.info("Ensuring extraction tracking columns exist...")
    add_extraction_columns(session, engine)

    # Load embedding service
    embedding_service = None
    if not args.no_embeddings and not args.dry_run:
        embedding_service = load_embedding_service()
        if not embedding_service:
            logger.warning("Embedding service not available, proceeding without embeddings")

    # Find files to process
    source_dir = args.source
    if args.file:
        files = [source_dir / args.file]
    else:
        files = sorted(source_dir.glob("*_vlm.json"))

    if not files:
        logger.error(f"No VLM JSON files found in {source_dir}")
        session.close()
        return

    logger.info(f"Found {len(files)} VLM JSON files to process")

    # Process each file
    total_found = 0
    total_inserted = 0

    for file_path in files:
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            continue

        found, inserted = process_vlm_file(
            file_path, session, embedding_service,
            clear_existing=args.clear, dry_run=args.dry_run
        )
        total_found += found
        total_inserted += inserted

    # Update search vectors
    if not args.dry_run and total_inserted > 0:
        update_search_vectors(session)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("REPOPULATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Files processed: {len(files)}")
    logger.info(f"Articles found: {total_found}")
    logger.info(f"Articles inserted: {total_inserted}")

    if not args.dry_run:
        verify_database(session)

    session.close()
    logger.info("Done!")


if __name__ == "__main__":
    main()
