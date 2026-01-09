#!/usr/bin/env python3
"""
Import Calgary parcel and zoning data into the database.

This script imports:
1. Zone designations from land-use-designation-codes.json
2. Parcel addresses from parcel-addresses-*.json files

Usage:
    python import_calgary_data.py [--zones-only] [--parcels-only] [--batch-size 1000]
"""
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, Base
from app.models.zones import Zone, Parcel


# Data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "zoning"


def import_zones(db: Session) -> dict:
    """
    Import zone designations from land-use-designation-codes.json.
    Returns a mapping of zone_code -> zone_id for use when importing parcels.
    """
    zone_file = DATA_DIR / "land-use-designation-codes.json"

    if not zone_file.exists():
        print(f"Warning: Zone file not found at {zone_file}")
        return {}

    print(f"Loading zones from {zone_file}...")

    with open(zone_file, 'r') as f:
        zones_data = json.load(f)

    zone_map = {}
    imported = 0
    skipped = 0

    for zone_data in zones_data:
        zone_code = zone_data.get("lud_code", "").strip()
        if not zone_code:
            skipped += 1
            continue

        # Check if zone already exists
        existing = db.query(Zone).filter(Zone.zone_code == zone_code).first()
        if existing:
            zone_map[zone_code] = existing.id
            skipped += 1
            continue

        # Determine category from district
        district = zone_data.get("lud_district", "").upper()
        category_map = {
            "RESIDENTIAL": "residential",
            "COMMERCIAL": "commercial",
            "INDUSTRIAL": "industrial",
            "MIXED USE": "mixed",
            "DIRECT CONTROL": "direct_control",
            "SPECIAL PURPOSE": "special",
        }
        category = category_map.get(district, "other")

        # Create zone
        zone = Zone(
            zone_code=zone_code,
            zone_name=zone_data.get("lud_name", zone_code),
            category=category,
            district=district,
            description=zone_data.get("lud_description"),
            bylaw_url=zone_data.get("lud_url", {}).get("url") if isinstance(zone_data.get("lud_url"), dict) else None
        )

        db.add(zone)
        db.flush()  # Get the ID
        zone_map[zone_code] = zone.id
        imported += 1

    db.commit()
    print(f"Zones: {imported} imported, {skipped} skipped (already exist or invalid)")

    return zone_map


def import_parcels(db: Session, zone_map: dict, batch_size: int = 1000):
    """
    Import parcel addresses from parcel-addresses-*.json files.
    """
    parcel_files = sorted(DATA_DIR.glob("parcel-addresses-*.json"))

    if not parcel_files:
        print("Warning: No parcel files found")
        return

    total_imported = 0
    total_skipped = 0

    for parcel_file in parcel_files:
        print(f"\nProcessing {parcel_file.name}...")

        with open(parcel_file, 'r') as f:
            parcels_data = json.load(f)

        batch = []
        file_imported = 0
        file_skipped = 0

        for i, parcel_data in enumerate(parcels_data):
            address = parcel_data.get("address", "").strip()
            if not address:
                file_skipped += 1
                continue

            # Check for existing parcel by address (simplified - production would use source_id)
            # For bulk import, we'll skip this check and rely on constraints

            # Parse coordinates
            try:
                latitude = float(parcel_data.get("latitude")) if parcel_data.get("latitude") else None
                longitude = float(parcel_data.get("longitude")) if parcel_data.get("longitude") else None
            except (ValueError, TypeError):
                latitude = None
                longitude = None

            # Get zone ID if we have it
            land_use = parcel_data.get("land_use_designation", "").strip()
            zone_id = zone_map.get(land_use)

            # Create parcel
            parcel = Parcel(
                address=address,
                street_name=parcel_data.get("street_name"),
                street_type=parcel_data.get("street_type"),
                street_direction=parcel_data.get("street_quad"),
                house_number=parcel_data.get("house_number"),
                quadrant=parcel_data.get("street_quad"),
                land_use_designation=land_use or None,
                zone_id=zone_id,
                latitude=latitude,
                longitude=longitude,
                source_id=parcel_data.get(":@computed_region_4a3i_ccfj"),  # Use one of the computed regions as source ID
                source_updated=datetime.utcnow()
            )

            batch.append(parcel)

            # Commit in batches
            if len(batch) >= batch_size:
                try:
                    db.bulk_save_objects(batch)
                    db.commit()
                    file_imported += len(batch)
                except Exception as e:
                    print(f"  Error saving batch: {e}")
                    db.rollback()
                    file_skipped += len(batch)
                batch = []

                # Progress update
                if file_imported % 10000 == 0:
                    print(f"  {file_imported:,} parcels imported from {parcel_file.name}...")

        # Save remaining batch
        if batch:
            try:
                db.bulk_save_objects(batch)
                db.commit()
                file_imported += len(batch)
            except Exception as e:
                print(f"  Error saving final batch: {e}")
                db.rollback()
                file_skipped += len(batch)

        print(f"  {parcel_file.name}: {file_imported:,} imported, {file_skipped:,} skipped")
        total_imported += file_imported
        total_skipped += file_skipped

    print(f"\nTotal: {total_imported:,} parcels imported, {total_skipped:,} skipped")


def main():
    parser = argparse.ArgumentParser(description="Import Calgary parcel and zoning data")
    parser.add_argument("--zones-only", action="store_true", help="Only import zones")
    parser.add_argument("--parcels-only", action="store_true", help="Only import parcels")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for parcel import")
    args = parser.parse_args()

    print("Calgary Data Import Script")
    print("=" * 50)

    # Create tables if they don't exist
    print("Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        zone_map = {}

        if not args.parcels_only:
            zone_map = import_zones(db)

        if not args.zones_only:
            # If we skipped zones, load existing zone map
            if not zone_map:
                zones = db.query(Zone).all()
                zone_map = {z.zone_code: z.id for z in zones}
                print(f"Loaded {len(zone_map)} existing zones")

            import_parcels(db, zone_map, args.batch_size)

        print("\nImport complete!")

    except Exception as e:
        print(f"Error during import: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
