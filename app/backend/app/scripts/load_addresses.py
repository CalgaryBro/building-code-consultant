#!/usr/bin/env python3
"""
Load Calgary address data from JSON files into PostgreSQL database.

This script reads parcel-addresses-*.json files and loads them into
the parcels table for the address autocomplete feature.

Usage:
    python -m app.scripts.load_addresses [--dry-run] [--force] [--batch-size 1000]

Options:
    --dry-run      Show what would be done without making changes
    --force        Delete existing parcel data and reload
    --batch-size   Number of records to commit per batch (default: 1000)
"""

import argparse
import json
import logging
import sys
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
from glob import glob
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database import SessionLocal, engine
from app.models.zones import Parcel
from app.config import get_settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_decimal(value: Any) -> Optional[Decimal]:
    """Parse a value to Decimal, handling various formats."""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def parse_address_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a JSON address record into a format suitable for the Parcel model.
    """
    # Extract address components
    address = record.get("address", "").strip()
    if not address:
        return None

    # Parse latitude/longitude
    latitude = parse_decimal(record.get("latitude"))
    longitude = parse_decimal(record.get("longitude"))

    # Get street components
    street_name = record.get("street_name", "").strip() if record.get("street_name") else None
    street_type = record.get("street_type", "").strip() if record.get("street_type") else None
    street_quad = record.get("street_quad", "").strip() if record.get("street_quad") else None
    house_number = record.get("house_number", "").strip() if record.get("house_number") else None

    # Extract unit number if present (addresses like "#2402 111 TARAWOOD LN NE")
    unit_number = None
    if address.startswith("#"):
        parts = address.split(" ", 1)
        if len(parts) > 1:
            unit_number = parts[0].replace("#", "")

    return {
        "address": address,
        "street_name": street_name,
        "street_type": street_type,
        "street_direction": street_quad,  # street_quad maps to quadrant/direction
        "house_number": house_number,
        "unit_number": unit_number,
        "quadrant": street_quad,
        "latitude": latitude,
        "longitude": longitude,
        "source_id": None,  # No source ID in this data
        "source_updated": datetime.utcnow(),
    }


def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load and parse a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_address_exists(db: Session, address: str) -> bool:
    """Check if an address already exists in the database."""
    result = db.execute(
        text("SELECT 1 FROM parcels WHERE address = :address LIMIT 1"),
        {"address": address}
    ).fetchone()
    return result is not None


def create_trigram_index(db: Session) -> None:
    """
    Create trigram index on address column for faster autocomplete.
    Requires pg_trgm extension.
    """
    try:
        # First ensure extension exists
        db.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        db.commit()

        # Create GIN trigram index for fast similarity searches
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_parcels_address_trgm
            ON parcels USING gin (UPPER(address) gin_trgm_ops)
        """))
        db.commit()

        # Also create a B-tree index for exact prefix matching
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_parcels_address_upper
            ON parcels (UPPER(address))
        """))
        db.commit()

        logger.info("Trigram indexes created successfully")
    except Exception as e:
        logger.warning(f"Could not create trigram indexes (may not be PostgreSQL): {e}")
        db.rollback()


def process_address_file(
    db: Session,
    file_path: Path,
    batch_size: int = 1000,
    dry_run: bool = False,
    skip_existing: bool = True
) -> int:
    """
    Process a single address JSON file.
    Returns the number of addresses loaded.
    """
    logger.info(f"Loading {file_path.name}...")

    data = load_json_file(file_path)
    total_records = len(data)
    loaded_count = 0
    skipped_count = 0
    error_count = 0

    batch = []

    for i, record in enumerate(data):
        parsed = parse_address_record(record)

        if not parsed:
            error_count += 1
            continue

        if skip_existing and not dry_run:
            if check_address_exists(db, parsed["address"]):
                skipped_count += 1
                continue

        if dry_run:
            loaded_count += 1
            continue

        # Create parcel record
        parcel = Parcel(
            id=uuid.uuid4(),
            address=parsed["address"],
            street_name=parsed["street_name"],
            street_type=parsed["street_type"],
            street_direction=parsed["street_direction"],
            house_number=parsed["house_number"],
            unit_number=parsed["unit_number"],
            quadrant=parsed["quadrant"],
            latitude=parsed["latitude"],
            longitude=parsed["longitude"],
            source_updated=parsed["source_updated"],
        )
        batch.append(parcel)
        loaded_count += 1

        # Commit in batches
        if len(batch) >= batch_size:
            db.bulk_save_objects(batch)
            db.commit()
            logger.info(f"  Committed batch: {loaded_count}/{total_records} records")
            batch = []

    # Commit remaining records
    if batch and not dry_run:
        db.bulk_save_objects(batch)
        db.commit()

    logger.info(f"  Completed: {loaded_count} loaded, {skipped_count} skipped, {error_count} errors")
    return loaded_count


def main():
    """Main entry point for the address loading script."""
    parser = argparse.ArgumentParser(
        description="Load Calgary address data into PostgreSQL database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete existing parcel data and reload (WARNING: destructive)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of records to commit per batch (default: 1000)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose debug logging"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Process only a specific file (by number, e.g., 1 for parcel-addresses-1.json)"
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    settings = get_settings()
    data_dir = Path(settings.data_dir) / "zoning"

    # Find all address JSON files
    if args.file:
        json_files = [str(data_dir / f"parcel-addresses-{args.file}.json")]
        if not Path(json_files[0]).exists():
            logger.error(f"File not found: {json_files[0]}")
            sys.exit(1)
    else:
        json_files = sorted(
            glob(str(data_dir / "parcel-addresses-*.json")),
            key=lambda x: int(Path(x).stem.split("-")[-1])
        )

    if not json_files:
        logger.error(f"No parcel address files found in {data_dir}")
        sys.exit(1)

    logger.info(f"Found {len(json_files)} address files to process")

    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")

    # Create database session
    db = SessionLocal()

    try:
        if args.force and not args.dry_run:
            logger.warning("FORCE MODE - Deleting existing parcel data")
            db.query(Parcel).delete()
            db.commit()
            logger.info("Existing parcel data deleted")

        total_loaded = 0

        for json_file in json_files:
            file_path = Path(json_file)
            loaded = process_address_file(
                db,
                file_path,
                batch_size=args.batch_size,
                dry_run=args.dry_run,
                skip_existing=not args.force
            )
            total_loaded += loaded

        # Create trigram index for fast autocomplete
        if not args.dry_run and total_loaded > 0:
            create_trigram_index(db)

        logger.info("=" * 60)
        logger.info(f"Processing complete!")
        logger.info(f"  Total addresses loaded: {total_loaded}")

        if args.dry_run:
            logger.info("(DRY RUN - no changes were made)")

        # Show database statistics
        if not args.dry_run:
            count = db.execute(text("SELECT COUNT(*) FROM parcels")).scalar()
            logger.info(f"  Total parcels in database: {count}")

    except Exception as e:
        logger.error(f"Error during processing: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
