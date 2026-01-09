"""
Zones & Parcels API - Calgary zoning information and address lookup.

This module provides:
- Zone information lookup
- Address/parcel search
- Zoning compliance checks
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models.zones import Zone, ZoneRule, Parcel
from ..schemas.zones import (
    ZoneResponse, ZoneSummary, ZoneRuleResponse,
    ParcelResponse, ParcelSearchResult,
    AddressSearchQuery, ZoningCheckRequest, ZoningCheckResponse, ZoningCheckResult
)

router = APIRouter()


@router.get("/zones", response_model=List[ZoneSummary])
async def list_zones(
    category: Optional[str] = Query(None, description="Filter by category: residential, commercial, industrial, mixed"),
    db: Session = Depends(get_db)
):
    """
    List all zone designations.
    """
    query = db.query(Zone)

    if category:
        query = query.filter(Zone.category == category)

    return query.order_by(Zone.zone_code).all()


@router.get("/zones/{zone_code}", response_model=ZoneResponse)
async def get_zone(zone_code: str, db: Session = Depends(get_db)):
    """
    Get detailed information for a zone by its code (e.g., R-C1, M-CG).
    """
    zone = db.query(Zone).filter(
        func.upper(Zone.zone_code) == zone_code.upper()
    ).first()

    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_code}' not found")

    return zone


@router.get("/zones/{zone_code}/rules", response_model=List[ZoneRuleResponse])
async def get_zone_rules(
    zone_code: str,
    rule_type: Optional[str] = Query(None, description="Filter by rule type: setback_front, height, FAR, etc."),
    db: Session = Depends(get_db)
):
    """
    Get all rules for a specific zone.
    """
    zone = db.query(Zone).filter(
        func.upper(Zone.zone_code) == zone_code.upper()
    ).first()

    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_code}' not found")

    query = db.query(ZoneRule).filter(ZoneRule.zone_id == zone.id)

    if rule_type:
        query = query.filter(ZoneRule.rule_type == rule_type)

    return query.all()


@router.get("/parcels/search", response_model=List[ParcelSearchResult])
async def search_parcels(
    query: str = Query(..., min_length=3, description="Address or partial address to search"),
    community: Optional[str] = Query(None, description="Filter by community name"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Search for parcels by address.
    Returns matching parcels with their zoning information.
    """
    search_pattern = f"%{query}%"

    base_query = db.query(
        Parcel.id,
        Parcel.address,
        Parcel.community_name,
        Parcel.land_use_designation,
        Parcel.latitude,
        Parcel.longitude,
        Zone.zone_code,
        Zone.zone_name
    ).outerjoin(Zone, Parcel.zone_id == Zone.id)

    base_query = base_query.filter(Parcel.address.ilike(search_pattern))

    if community:
        base_query = base_query.filter(
            Parcel.community_name.ilike(f"%{community}%")
        )

    results = base_query.limit(limit).all()

    return [
        ParcelSearchResult(
            id=r.id,
            address=r.address,
            community_name=r.community_name,
            land_use_designation=r.land_use_designation,
            zone_code=r.zone_code,
            zone_name=r.zone_name,
            latitude=float(r.latitude) if r.latitude else None,
            longitude=float(r.longitude) if r.longitude else None
        )
        for r in results
    ]


@router.get("/parcels/{parcel_id}", response_model=ParcelResponse)
async def get_parcel(parcel_id: UUID, db: Session = Depends(get_db)):
    """
    Get detailed information for a specific parcel.
    """
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()

    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    return parcel


@router.post("/check-zoning", response_model=ZoningCheckResponse)
async def check_zoning_compliance(
    request: ZoningCheckRequest,
    db: Session = Depends(get_db)
):
    """
    Check if proposed building parameters comply with zoning rules.

    Provide either parcel_id or address to identify the location.
    Then provide proposed building parameters to check against zone rules.
    """
    # Find the parcel
    parcel = None
    if request.parcel_id:
        parcel = db.query(Parcel).filter(Parcel.id == request.parcel_id).first()
    elif request.address:
        parcel = db.query(Parcel).filter(
            Parcel.address.ilike(f"%{request.address}%")
        ).first()

    if not parcel:
        raise HTTPException(
            status_code=404,
            detail="Parcel not found. Please provide a valid parcel_id or searchable address."
        )

    # Get the zone
    if not parcel.zone_id:
        raise HTTPException(
            status_code=400,
            detail=f"No zone designation found for parcel at {parcel.address}"
        )

    zone = db.query(Zone).filter(Zone.id == parcel.zone_id).first()
    if not zone:
        raise HTTPException(status_code=500, detail="Zone data inconsistency")

    # Perform compliance checks
    checks = []
    failed_count = 0
    warning_count = 0

    # Height check (metres)
    if request.building_height_m is not None and zone.max_height_m:
        status = "pass" if request.building_height_m <= float(zone.max_height_m) else "fail"
        if status == "fail":
            failed_count += 1
        checks.append(ZoningCheckResult(
            check_name="Building Height (metres)",
            rule_type="height",
            required_value=f"≤ {zone.max_height_m} m",
            proposed_value=f"{request.building_height_m} m",
            status=status,
            message=f"Maximum height is {zone.max_height_m} m" if status == "fail" else None,
            bylaw_reference=f"LUB 1P2007 - Zone {zone.zone_code}"
        ))

    # Height check (storeys)
    if request.building_storeys is not None and zone.max_storeys:
        status = "pass" if request.building_storeys <= zone.max_storeys else "fail"
        if status == "fail":
            failed_count += 1
        checks.append(ZoningCheckResult(
            check_name="Building Height (storeys)",
            rule_type="height",
            required_value=f"≤ {zone.max_storeys} storeys",
            proposed_value=f"{request.building_storeys} storeys",
            status=status,
            message=f"Maximum is {zone.max_storeys} storeys" if status == "fail" else None,
            bylaw_reference=f"LUB 1P2007 - Zone {zone.zone_code}"
        ))

    # Front setback check
    if request.front_setback_m is not None and zone.min_front_setback_m:
        status = "pass" if request.front_setback_m >= float(zone.min_front_setback_m) else "fail"
        if status == "fail":
            failed_count += 1
        checks.append(ZoningCheckResult(
            check_name="Front Setback",
            rule_type="setback_front",
            required_value=f"≥ {zone.min_front_setback_m} m",
            proposed_value=f"{request.front_setback_m} m",
            status=status,
            message=f"Minimum front setback is {zone.min_front_setback_m} m" if status == "fail" else None,
            bylaw_reference=f"LUB 1P2007 - Zone {zone.zone_code}"
        ))

    # Side setback check
    if request.side_setback_m is not None and zone.min_side_setback_m:
        status = "pass" if request.side_setback_m >= float(zone.min_side_setback_m) else "fail"
        if status == "fail":
            failed_count += 1
        checks.append(ZoningCheckResult(
            check_name="Side Setback",
            rule_type="setback_side",
            required_value=f"≥ {zone.min_side_setback_m} m",
            proposed_value=f"{request.side_setback_m} m",
            status=status,
            message=f"Minimum side setback is {zone.min_side_setback_m} m" if status == "fail" else None,
            bylaw_reference=f"LUB 1P2007 - Zone {zone.zone_code}"
        ))

    # Rear setback check
    if request.rear_setback_m is not None and zone.min_rear_setback_m:
        status = "pass" if request.rear_setback_m >= float(zone.min_rear_setback_m) else "fail"
        if status == "fail":
            failed_count += 1
        checks.append(ZoningCheckResult(
            check_name="Rear Setback",
            rule_type="setback_rear",
            required_value=f"≥ {zone.min_rear_setback_m} m",
            proposed_value=f"{request.rear_setback_m} m",
            status=status,
            message=f"Minimum rear setback is {zone.min_rear_setback_m} m" if status == "fail" else None,
            bylaw_reference=f"LUB 1P2007 - Zone {zone.zone_code}"
        ))

    # FAR check
    if request.floor_area_ratio is not None and zone.max_far:
        status = "pass" if request.floor_area_ratio <= float(zone.max_far) else "fail"
        if status == "fail":
            failed_count += 1
        checks.append(ZoningCheckResult(
            check_name="Floor Area Ratio",
            rule_type="FAR",
            required_value=f"≤ {zone.max_far}",
            proposed_value=f"{request.floor_area_ratio}",
            status=status,
            message=f"Maximum FAR is {zone.max_far}" if status == "fail" else None,
            bylaw_reference=f"LUB 1P2007 - Zone {zone.zone_code}"
        ))

    # Parking check
    if request.parking_stalls is not None and zone.min_parking_stalls:
        status = "pass" if request.parking_stalls >= zone.min_parking_stalls else "fail"
        if status == "fail":
            failed_count += 1
        checks.append(ZoningCheckResult(
            check_name="Parking Stalls",
            rule_type="parking",
            required_value=f"≥ {zone.min_parking_stalls} stalls",
            proposed_value=f"{request.parking_stalls} stalls",
            status=status,
            message=f"Minimum {zone.min_parking_stalls} parking stalls required" if status == "fail" else None,
            bylaw_reference=f"LUB 1P2007 - Zone {zone.zone_code}"
        ))

    # Determine overall status
    if failed_count > 0:
        overall_status = "fail"
        summary = f"{failed_count} zoning violation(s) found. A relaxation or variance may be required."
    elif warning_count > 0:
        overall_status = "warning"
        summary = f"Zoning compliant with {warning_count} warning(s). Review recommended."
    elif len(checks) == 0:
        overall_status = "needs_review"
        summary = "No parameters provided to check. Please provide building dimensions and setbacks."
    else:
        overall_status = "pass"
        summary = f"All {len(checks)} zoning checks passed for zone {zone.zone_code}."

    return ZoningCheckResponse(
        parcel=parcel,
        zone=zone,
        checks=checks,
        overall_status=overall_status,
        summary=summary
    )


@router.get("/communities", response_model=List[dict])
async def list_communities(
    quadrant: Optional[str] = Query(None, description="Filter by quadrant: NE, NW, SE, SW"),
    db: Session = Depends(get_db)
):
    """
    List all Calgary communities with parcel counts.
    """
    query = db.query(
        Parcel.community_name,
        Parcel.community_code,
        Parcel.quadrant,
        func.count(Parcel.id).label("parcel_count")
    ).filter(
        Parcel.community_name.isnot(None)
    )

    if quadrant:
        query = query.filter(Parcel.quadrant == quadrant.upper())

    results = query.group_by(
        Parcel.community_name,
        Parcel.community_code,
        Parcel.quadrant
    ).order_by(Parcel.community_name).all()

    return [
        {
            "community_name": r.community_name,
            "community_code": r.community_code,
            "quadrant": r.quadrant,
            "parcel_count": r.parcel_count
        }
        for r in results
    ]
