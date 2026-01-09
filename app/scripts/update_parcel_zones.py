#!/usr/bin/env python3
"""
Update parcels with zone information from property assessment data.

This script:
1. Loads property-zone mapping from Calgary's property assessment dataset
2. Updates parcels in the database with correct zone_id based on land_use_designation
3. Updates zone records with HEIGHT, FAR, and DENSITY from land use districts data

Usage:
    python update_parcel_zones.py [--batch-size 5000] [--update-zones]
"""
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, Base
from app.models.zones import Zone, Parcel


# Data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "zoning"


def load_property_zone_mapping() -> dict:
    """
    Load property-to-zone mapping from property assessment JSON.
    Returns: dict mapping address -> land_use_designation
    """
    mapping_file = DATA_DIR / "property-zone-mapping.json"

    if not mapping_file.exists():
        print(f"Error: Mapping file not found at {mapping_file}")
        return {}

    print(f"Loading property zone mapping from {mapping_file}...")

    with open(mapping_file, 'r') as f:
        data = json.load(f)

    # Create address -> zone mapping
    # Normalize addresses for matching
    mapping = {}
    for record in data:
        address = record.get('address', '').strip().upper()
        zone = record.get('land_use_designation', '').strip()
        if address and zone:
            mapping[address] = zone

    print(f"Loaded {len(mapping):,} address-to-zone mappings")
    return mapping


def load_zone_rules() -> dict:
    """
    Load zone rules (HEIGHT, FAR, DENSITY) from land use districts JSON.
    Returns: dict mapping zone_code -> {height, far, density}
    """
    districts_file = DATA_DIR / "land-use-districts.json"

    if not districts_file.exists():
        print(f"Warning: Land use districts file not found at {districts_file}")
        return {}

    print(f"Loading zone rules from {districts_file}...")

    with open(districts_file, 'r') as f:
        data = json.load(f)

    # Aggregate zone rules (some zones have multiple polygons with different rules)
    zone_rules = defaultdict(lambda: {'heights': [], 'fars': [], 'densities': []})

    for record in data:
        zone_code = record.get('lu_code', '').strip()
        if not zone_code:
            continue

        if record.get('height'):
            try:
                zone_rules[zone_code]['heights'].append(float(record['height']))
            except (ValueError, TypeError):
                pass

        if record.get('far'):
            try:
                zone_rules[zone_code]['fars'].append(float(record['far']))
            except (ValueError, TypeError):
                pass

        if record.get('density'):
            try:
                zone_rules[zone_code]['densities'].append(float(record['density']))
            except (ValueError, TypeError):
                pass

    # Calculate averages/max for each zone
    final_rules = {}
    for zone_code, rules in zone_rules.items():
        final_rules[zone_code] = {
            'max_height_m': max(rules['heights']) if rules['heights'] else None,
            'max_far': max(rules['fars']) if rules['fars'] else None,
            'max_density': max(rules['densities']) if rules['densities'] else None,
        }

    print(f"Loaded rules for {len(final_rules)} zones")
    return final_rules


def update_zones_with_rules(db: Session, zone_rules: dict):
    """Update zone records with HEIGHT, FAR, DENSITY from land use districts."""

    print("\nUpdating zones with rules from land use districts...")

    zones = db.query(Zone).all()
    updated = 0

    for zone in zones:
        rules = zone_rules.get(zone.zone_code)
        if rules:
            if rules['max_height_m'] and not zone.max_height_m:
                zone.max_height_m = rules['max_height_m']
            if rules['max_far'] and not zone.max_far:
                zone.max_far = rules['max_far']
            if rules['max_density']:
                # Store density if we have a field for it
                pass
            updated += 1

    db.commit()
    print(f"Updated {updated} zones with height/FAR rules")


def update_parcel_zones(db: Session, zone_mapping: dict, batch_size: int = 5000):
    """
    Update parcels with zone_id based on land_use_designation.
    """
    print("\nUpdating parcels with zone assignments...")

    # Get all zones as lookup
    zones = db.query(Zone).all()
    zone_lookup = {z.zone_code: z.id for z in zones}
    print(f"Loaded {len(zone_lookup)} zones from database")

    # Get total parcel count
    total_parcels = db.query(Parcel).count()
    print(f"Total parcels to process: {total_parcels:,}")

    # Process in batches
    offset = 0
    updated = 0
    no_match = 0
    zone_not_found = 0

    while offset < total_parcels:
        parcels = db.query(Parcel).offset(offset).limit(batch_size).all()

        for parcel in parcels:
            # Normalize address for matching
            address_normalized = parcel.address.strip().upper() if parcel.address else ""

            # Look up zone from mapping
            zone_code = zone_mapping.get(address_normalized)

            if zone_code:
                # Clean zone code (remove "(PRE 1P2007)" etc.)
                zone_code_clean = zone_code.split('(')[0].strip()

                zone_id = zone_lookup.get(zone_code_clean) or zone_lookup.get(zone_code)

                if zone_id:
                    parcel.zone_id = zone_id
                    parcel.land_use_designation = zone_code
                    updated += 1
                else:
                    zone_not_found += 1
            else:
                no_match += 1

        db.commit()
        offset += batch_size

        # Progress update
        if offset % 50000 == 0:
            print(f"  Processed {offset:,}/{total_parcels:,} parcels ({updated:,} updated)")

    print(f"\nParcel zone update complete:")
    print(f"  Updated: {updated:,}")
    print(f"  No address match: {no_match:,}")
    print(f"  Zone code not in database: {zone_not_found:,}")


def main():
    parser = argparse.ArgumentParser(description="Update parcels with zone information")
    parser.add_argument("--batch-size", type=int, default=5000, help="Batch size for updates")
    parser.add_argument("--update-zones", action="store_true", help="Also update zone rules")
    parser.add_argument("--zones-only", action="store_true", help="Only update zone rules, not parcels")
    args = parser.parse_args()

    print("Calgary Parcel Zone Update Script")
    print("=" * 50)

    db = SessionLocal()

    try:
        # Load zone rules if needed
        zone_rules = {}
        if args.update_zones or args.zones_only:
            zone_rules = load_zone_rules()
            if zone_rules:
                update_zones_with_rules(db, zone_rules)

        if not args.zones_only:
            # Load property-zone mapping
            zone_mapping = load_property_zone_mapping()

            if zone_mapping:
                update_parcel_zones(db, zone_mapping, args.batch_size)

        print("\nUpdate complete!")

    except Exception as e:
        print(f"Error during update: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
