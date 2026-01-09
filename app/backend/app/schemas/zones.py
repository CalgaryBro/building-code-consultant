"""
Pydantic schemas for zones, zone rules, and parcels.
"""
from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field


# --- Zone Schemas ---

class ZoneRuleResponse(BaseModel):
    """Schema for ZoneRule response."""
    id: UUID
    rule_type: str
    description: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: Optional[str] = None
    calculation_formula: Optional[str] = None
    conditions: Optional[dict] = None
    exceptions: Optional[str] = None
    bylaw_reference: Optional[str] = None

    class Config:
        from_attributes = True


class ZoneBase(BaseModel):
    """Base schema for Zone."""
    zone_code: str
    zone_name: str
    category: str  # residential, commercial, industrial, mixed, direct_control
    district: Optional[str] = None
    description: Optional[str] = None
    bylaw_url: Optional[str] = None
    max_height_m: Optional[float] = None
    max_storeys: Optional[int] = None
    max_far: Optional[float] = None
    min_front_setback_m: Optional[float] = None
    min_side_setback_m: Optional[float] = None
    min_rear_setback_m: Optional[float] = None
    min_parking_stalls: Optional[int] = None


class ZoneCreate(ZoneBase):
    """Schema for creating a Zone."""
    code_id: Optional[UUID] = None


class ZoneResponse(ZoneBase):
    """Schema for Zone response."""
    id: UUID
    rules: List[ZoneRuleResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ZoneSummary(BaseModel):
    """Brief zone info for lists."""
    id: UUID
    zone_code: str
    zone_name: str
    category: str

    class Config:
        from_attributes = True


# --- Parcel Schemas ---

class ParcelBase(BaseModel):
    """Base schema for Parcel."""
    address: str
    street_name: Optional[str] = None
    street_type: Optional[str] = None
    street_direction: Optional[str] = None
    house_number: Optional[str] = None
    unit_number: Optional[str] = None
    community_name: Optional[str] = None
    community_code: Optional[str] = None
    quadrant: Optional[str] = None
    postal_code: Optional[str] = None
    land_use_designation: Optional[str] = None
    legal_description: Optional[str] = None
    roll_number: Optional[str] = None
    area_sqm: Optional[float] = None
    frontage_m: Optional[float] = None
    depth_m: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ParcelCreate(ParcelBase):
    """Schema for creating a Parcel."""
    zone_id: Optional[UUID] = None
    source_id: Optional[str] = None
    source_updated: Optional[datetime] = None


class ParcelResponse(ParcelBase):
    """Schema for Parcel response."""
    id: UUID
    zone_id: Optional[UUID] = None
    zone: Optional[ZoneSummary] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ParcelSearchResult(BaseModel):
    """Schema for parcel search results."""
    id: UUID
    address: str
    community_name: Optional[str]
    land_use_designation: Optional[str]
    zone_code: Optional[str] = None
    zone_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        from_attributes = True


# --- Search Schemas ---

class AddressSearchQuery(BaseModel):
    """Schema for address search."""
    query: str = Field(..., min_length=3, max_length=200)
    community: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=50)


class ZoningCheckRequest(BaseModel):
    """Schema for checking zoning compliance."""
    parcel_id: Optional[UUID] = None
    address: Optional[str] = None
    # Proposed building parameters
    building_height_m: Optional[float] = None
    building_storeys: Optional[int] = None
    building_area_sqm: Optional[float] = None
    floor_area_ratio: Optional[float] = None
    front_setback_m: Optional[float] = None
    side_setback_m: Optional[float] = None
    rear_setback_m: Optional[float] = None
    parking_stalls: Optional[int] = None


class ZoningCheckResult(BaseModel):
    """Schema for zoning compliance result."""
    check_name: str
    rule_type: str
    required_value: Optional[str] = None
    proposed_value: Optional[str] = None
    status: str  # pass, fail, warning, needs_review
    message: Optional[str] = None
    bylaw_reference: Optional[str] = None


class ZoningCheckResponse(BaseModel):
    """Schema for full zoning check response."""
    parcel: ParcelResponse
    zone: ZoneResponse
    checks: List[ZoningCheckResult]
    overall_status: str  # pass, fail, needs_review
    summary: str
