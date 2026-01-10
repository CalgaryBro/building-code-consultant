"""
Address Autocomplete API - Fast address search for Calgary properties.

This module provides:
- Autocomplete endpoint for address search with pg_trgm optimization
- Returns address, community, and zone information
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, or_
from pydantic import BaseModel

from ..database import get_db
from ..models.zones import Parcel, Zone


router = APIRouter()


class AddressAutocompleteResult(BaseModel):
    """Schema for address autocomplete results."""
    address: str
    community: Optional[str] = None
    zone_code: Optional[str] = None
    parcel_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        from_attributes = True


@router.get("/autocomplete", response_model=List[AddressAutocompleteResult])
async def address_autocomplete(
    q: str = Query(..., min_length=2, max_length=200, description="Search query for address"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results to return"),
    db: Session = Depends(get_db)
):
    """
    Fast address autocomplete endpoint.

    Searches for addresses matching the query string (case-insensitive).
    Optimized for speed with trigram index support (pg_trgm).

    Returns address, community, zone_code, and parcel_id.
    """
    # Normalize query - remove extra spaces
    search_query = q.strip().upper()

    # Check if PostgreSQL with pg_trgm is available
    is_postgres = "postgresql" in str(db.bind.url)

    if is_postgres:
        # Use trigram similarity for PostgreSQL (requires pg_trgm extension)
        # This provides much better fuzzy matching
        try:
            # Try to use pg_trgm similarity search
            results = db.execute(
                text("""
                    SELECT
                        p.id,
                        p.address,
                        p.community_name,
                        p.land_use_designation,
                        z.zone_code,
                        p.latitude,
                        p.longitude,
                        similarity(UPPER(p.address), :query) as sim
                    FROM parcels p
                    LEFT JOIN zones z ON p.zone_id = z.id
                    WHERE UPPER(p.address) LIKE :pattern
                       OR similarity(UPPER(p.address), :query) > 0.1
                    ORDER BY
                        CASE WHEN UPPER(p.address) LIKE :start_pattern THEN 0 ELSE 1 END,
                        sim DESC,
                        p.address
                    LIMIT :limit
                """),
                {
                    "query": search_query,
                    "pattern": f"%{search_query}%",
                    "start_pattern": f"{search_query}%",
                    "limit": limit
                }
            ).fetchall()
        except Exception:
            # Fallback to ILIKE if pg_trgm is not available
            results = db.execute(
                text("""
                    SELECT
                        p.id,
                        p.address,
                        p.community_name,
                        p.land_use_designation,
                        z.zone_code,
                        p.latitude,
                        p.longitude,
                        0.0 as sim
                    FROM parcels p
                    LEFT JOIN zones z ON p.zone_id = z.id
                    WHERE UPPER(p.address) LIKE :pattern
                    ORDER BY
                        CASE WHEN UPPER(p.address) LIKE :start_pattern THEN 0 ELSE 1 END,
                        p.address
                    LIMIT :limit
                """),
                {
                    "pattern": f"%{search_query}%",
                    "start_pattern": f"{search_query}%",
                    "limit": limit
                }
            ).fetchall()
    else:
        # SQLite fallback with LIKE
        pattern = f"%{search_query}%"
        start_pattern = f"{search_query}%"

        results = db.query(
            Parcel.id,
            Parcel.address,
            Parcel.community_name,
            Parcel.land_use_designation,
            Zone.zone_code,
            Parcel.latitude,
            Parcel.longitude
        ).outerjoin(
            Zone, Parcel.zone_id == Zone.id
        ).filter(
            Parcel.address.ilike(pattern)
        ).order_by(
            # Prioritize addresses starting with the query
            Parcel.address.ilike(start_pattern).desc(),
            Parcel.address
        ).limit(limit).all()

    return [
        AddressAutocompleteResult(
            address=r[1] if hasattr(r, '__getitem__') else r.address,
            community=r[2] if hasattr(r, '__getitem__') else r.community_name,
            zone_code=r[4] if hasattr(r, '__getitem__') else (r.zone_code if hasattr(r, 'zone_code') else r[4]),
            parcel_id=str(r[0]) if hasattr(r, '__getitem__') else str(r.id),
            latitude=float(r[5]) if (hasattr(r, '__getitem__') and r[5]) else (float(r.latitude) if hasattr(r, 'latitude') and r.latitude else None),
            longitude=float(r[6]) if (hasattr(r, '__getitem__') and r[6]) else (float(r.longitude) if hasattr(r, 'longitude') and r.longitude else None)
        )
        for r in results
    ]


@router.get("/search", response_model=List[AddressAutocompleteResult])
async def search_addresses(
    query: str = Query(..., min_length=2, max_length=200, description="Search query for address"),
    community: Optional[str] = Query(None, description="Filter by community name"),
    zone: Optional[str] = Query(None, description="Filter by zone code"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results to return"),
    db: Session = Depends(get_db)
):
    """
    Advanced address search with optional filters.

    Supports filtering by community and zone code.
    """
    search_pattern = f"%{query.strip()}%"

    base_query = db.query(
        Parcel.id,
        Parcel.address,
        Parcel.community_name,
        Parcel.land_use_designation,
        Zone.zone_code,
        Parcel.latitude,
        Parcel.longitude
    ).outerjoin(
        Zone, Parcel.zone_id == Zone.id
    ).filter(
        Parcel.address.ilike(search_pattern)
    )

    if community:
        base_query = base_query.filter(
            Parcel.community_name.ilike(f"%{community}%")
        )

    if zone:
        base_query = base_query.filter(
            or_(
                Zone.zone_code.ilike(f"%{zone}%"),
                Parcel.land_use_designation.ilike(f"%{zone}%")
            )
        )

    results = base_query.order_by(Parcel.address).limit(limit).all()

    return [
        AddressAutocompleteResult(
            address=r.address,
            community=r.community_name,
            zone_code=r.zone_code or r.land_use_designation,
            parcel_id=str(r.id),
            latitude=float(r.latitude) if r.latitude else None,
            longitude=float(r.longitude) if r.longitude else None
        )
        for r in results
    ]
