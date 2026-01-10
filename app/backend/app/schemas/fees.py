"""
Pydantic schemas for permit fee calculations.

This module provides schemas for:
- Fee estimation requests and responses
- Building permit fee calculations
- Trade permit fee calculations
- Development permit fee calculations
- Fee schedule data
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


# --- Enums ---

class BuildingType(str, Enum):
    """Types of buildings for fee calculation."""
    # Commercial
    COMMERCIAL = "commercial"
    HOTEL = "hotel"
    WAREHOUSE = "warehouse"
    CARE_FACILITY = "care_facility"

    # Multi-family
    MULTI_FAMILY_HIGH_RISE = "multi_family_high_rise"
    MULTI_FAMILY_LOW_RISE = "multi_family_low_rise"

    # Residential
    SINGLE_FAMILY = "single_family"
    SEMI_DETACHED = "semi_detached"
    DUPLEX = "duplex"

    # Alterations
    COMMERCIAL_ALTERATION = "commercial_alteration"
    DEMOLITION = "demolition"


class ResidentialAlterationType(str, Enum):
    """Types of residential alterations."""
    BASEMENT_GARAGE_ADDITION_SMALL = "basement_garage_addition_small"
    NEW_SECONDARY_SUITE = "new_secondary_suite"
    EXISTING_SECONDARY_SUITE = "existing_secondary_suite"
    NEW_BACKYARD_SUITE = "new_backyard_suite"
    MINOR_ALTERATIONS = "minor_alterations"
    ADDITION_LARGE = "addition_large"


class TradePermitType(str, Enum):
    """Types of trade permits."""
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    GAS = "gas"
    HVAC = "hvac"
    MECHANICAL = "mechanical"
    HOMEOWNER = "homeowner"
    ANNUAL_ELECTRICAL = "annual_electrical"


class ProjectType(str, Enum):
    """Types of construction projects."""
    NEW_CONSTRUCTION = "new_construction"
    ADDITION = "addition"
    RENOVATION = "renovation"
    ALTERATION = "alteration"
    DEMOLITION = "demolition"
    CHANGE_OF_USE = "change_of_use"


class ZoneCategory(str, Enum):
    """Zone categories for development permits."""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    MIXED_USE = "mixed_use"
    SPECIAL = "special"


# --- Fee Breakdown Schemas ---

class FeeLineItem(BaseModel):
    """A single line item in a fee breakdown."""
    name: str = Field(..., description="Name of the fee component")
    description: Optional[str] = Field(None, description="Description of what this fee covers")
    amount: float = Field(..., description="Amount in CAD")
    calculation_basis: Optional[str] = Field(None, description="How this fee was calculated")


class FeeBreakdown(BaseModel):
    """Detailed breakdown of fees."""
    processing_fee: float = Field(0.0, description="Permit processing fee")
    base_fee: float = Field(0.0, description="Base permit fee")
    safety_codes_council_fee: float = Field(0.0, description="Safety Codes Council fee (4%)")
    gst: float = Field(0.0, description="GST if applicable")
    subtotal: float = Field(0.0, description="Subtotal before any adjustments")
    total: float = Field(0.0, description="Total fee amount")
    line_items: List[FeeLineItem] = Field(default_factory=list, description="Detailed line items")
    notes: List[str] = Field(default_factory=list, description="Additional notes or warnings")


# --- Building Permit Fee Schemas ---

class BuildingPermitFeeRequest(BaseModel):
    """Request schema for building permit fee calculation."""
    building_type: BuildingType = Field(..., description="Type of building")
    construction_value: Optional[float] = Field(
        None,
        ge=0,
        description="Estimated construction value in CAD"
    )
    floor_area_sqm: Optional[float] = Field(
        None,
        ge=0,
        description="Floor area in square metres (for demolition)"
    )
    is_alteration: bool = Field(False, description="Is this an alteration to existing building?")
    alteration_type: Optional[ResidentialAlterationType] = Field(
        None,
        description="Type of residential alteration (if applicable)"
    )
    dwelling_units: Optional[int] = Field(
        None,
        ge=1,
        description="Number of dwelling units"
    )
    work_started_without_permit: bool = Field(
        False,
        description="Has work already started without a permit? (Double fee applies)"
    )


class BuildingPermitFeeResponse(BaseModel):
    """Response schema for building permit fee calculation."""
    building_type: BuildingType
    construction_value: Optional[float] = None
    floor_area_sqm: Optional[float] = None
    fee_breakdown: FeeBreakdown
    includes_trade_permits: bool = Field(
        False,
        description="Whether trade permits are included (for new residential)"
    )
    double_fee_applied: bool = Field(
        False,
        description="Whether double fee was applied for work started without permit"
    )
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


# --- Trade Permit Fee Schemas ---

class TradePermitRequest(BaseModel):
    """Single trade permit request."""
    trade_type: TradePermitType = Field(..., description="Type of trade permit")
    construction_value: Optional[float] = Field(
        None,
        ge=0,
        description="Construction value for this trade work"
    )
    is_homeowner: bool = Field(
        False,
        description="Is this a homeowner permit?"
    )


class TradePermitFeeRequest(BaseModel):
    """Request schema for trade permit fee calculation."""
    trades: List[TradePermitRequest] = Field(..., description="List of trade permits needed")
    work_started_without_permit: bool = Field(
        False,
        description="Has work already started without a permit?"
    )


class TradePermitFeeItem(BaseModel):
    """Fee calculation for a single trade permit."""
    trade_type: TradePermitType
    construction_value: Optional[float] = None
    fee_breakdown: FeeBreakdown


class TradePermitFeeResponse(BaseModel):
    """Response schema for trade permit fee calculation."""
    trade_permits: List[TradePermitFeeItem]
    combined_total: float
    double_fee_applied: bool = False
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


# --- Development Permit Fee Schemas ---

class DevelopmentPermitFeeRequest(BaseModel):
    """Request schema for development permit fee estimation."""
    project_type: ProjectType = Field(..., description="Type of project")
    floor_area_sqm: Optional[float] = Field(
        None,
        ge=0,
        description="Proposed floor area in square metres"
    )
    zone_category: Optional[ZoneCategory] = Field(
        None,
        description="Zoning category"
    )
    requires_relaxation: bool = Field(
        False,
        description="Does the project require zoning relaxations?"
    )
    is_discretionary: bool = Field(
        False,
        description="Is this a discretionary use application?"
    )


class DevelopmentPermitFeeResponse(BaseModel):
    """Response schema for development permit fee estimation."""
    project_type: ProjectType
    floor_area_sqm: Optional[float] = None
    zone_category: Optional[ZoneCategory] = None
    fee_breakdown: FeeBreakdown
    notes: List[str] = Field(
        default_factory=list,
        description="Notes about the estimate (DP fees vary by project complexity)"
    )
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


# --- Combined Fee Estimate Schemas ---

class ProjectFeeEstimateRequest(BaseModel):
    """Request schema for complete project fee estimate."""
    # Project basics
    project_name: Optional[str] = Field(None, description="Project name for reference")
    project_type: ProjectType = Field(..., description="Type of project")
    building_type: BuildingType = Field(..., description="Type of building")

    # Values and areas
    construction_value: Optional[float] = Field(
        None,
        ge=0,
        description="Total estimated construction value in CAD"
    )
    floor_area_sqm: Optional[float] = Field(
        None,
        ge=0,
        description="Total floor area in square metres"
    )
    dwelling_units: Optional[int] = Field(
        None,
        ge=1,
        description="Number of dwelling units"
    )

    # Permit requirements
    requires_development_permit: bool = Field(
        True,
        description="Does the project require a Development Permit?"
    )
    requires_building_permit: bool = Field(
        True,
        description="Does the project require a Building Permit?"
    )
    trade_permits: Optional[List[TradePermitRequest]] = Field(
        None,
        description="List of trade permits needed"
    )

    # Residential alterations
    alteration_type: Optional[ResidentialAlterationType] = Field(
        None,
        description="Type of residential alteration (if applicable)"
    )

    # Zone info
    zone_category: Optional[ZoneCategory] = Field(
        None,
        description="Zoning category"
    )
    requires_relaxation: bool = Field(
        False,
        description="Does the project require zoning relaxations?"
    )

    # Additional fees
    include_lot_grading: bool = Field(
        False,
        description="Include lot grading fees?"
    )
    lot_area_hectares: Optional[float] = Field(
        None,
        ge=0,
        description="Lot area in hectares (for lot grading calculation)"
    )
    ground_floor_units: Optional[int] = Field(
        None,
        ge=1,
        description="Number of ground floor units (for lot grading)"
    )
    storeys: Optional[int] = Field(
        None,
        ge=1,
        description="Number of storeys"
    )

    # Warnings
    work_started_without_permit: bool = Field(
        False,
        description="Has work already started without a permit?"
    )


class FeeCategorySummary(BaseModel):
    """Summary of fees in a category."""
    category: str
    subtotal: float
    items: List[FeeLineItem]


class ProjectFeeEstimateResponse(BaseModel):
    """Response schema for complete project fee estimate."""
    project_name: Optional[str] = None
    project_type: ProjectType
    building_type: BuildingType

    # Fee summaries by category
    development_permit_fees: Optional[FeeBreakdown] = None
    building_permit_fees: Optional[FeeBreakdown] = None
    trade_permit_fees: Optional[FeeBreakdown] = None
    additional_fees: Optional[FeeBreakdown] = None

    # Totals
    subtotal: float = Field(0.0, description="Subtotal of all fees")
    total_estimate: float = Field(0.0, description="Total estimated fees")

    # Fee breakdown by category
    fee_summary: List[FeeCategorySummary] = Field(
        default_factory=list,
        description="Summary of fees by category"
    )

    # Warnings and notes
    warnings: List[str] = Field(
        default_factory=list,
        description="Important warnings about the estimate"
    )
    notes: List[str] = Field(
        default_factory=list,
        description="Additional notes and disclaimers"
    )

    # Metadata
    double_fee_applied: bool = False
    estimated_at: datetime = Field(default_factory=datetime.utcnow)
    fee_schedule_version: str = Field("R2026-02", description="Fee schedule version used")


# --- Fee Schedule Schemas ---

class FeeScheduleCategory(BaseModel):
    """A category in the fee schedule."""
    name: str
    description: Optional[str] = None
    items: List[Dict[str, Any]]


class FeeScheduleResponse(BaseModel):
    """Response schema for fee schedule lookup."""
    version: str
    effective_date: str
    categories: List[FeeScheduleCategory]
    safety_codes_council_info: Dict[str, Any]
    policies: Dict[str, Any]


# --- Additional Fee Schemas ---

class LotGradingFeeRequest(BaseModel):
    """Request for lot grading fee calculation."""
    building_type: BuildingType
    dwelling_units: Optional[int] = Field(None, ge=1)
    ground_floor_units: Optional[int] = Field(None, ge=1)
    storeys: Optional[int] = Field(None, ge=1)
    lot_area_hectares: Optional[float] = Field(None, ge=0)


class LotGradingFeeResponse(BaseModel):
    """Response for lot grading fee calculation."""
    fee_type: str
    total_fee: float
    calculation_basis: str
    notes: List[str] = Field(default_factory=list)


class InspectionFeeRequest(BaseModel):
    """Request for inspection fee calculation."""
    inspection_type: str = Field(
        ...,
        description="safety_inspection, weekend_holiday, re_inspection"
    )
    hours: Optional[float] = Field(
        None,
        ge=0,
        description="Hours for weekend/holiday inspections"
    )


class InspectionFeeResponse(BaseModel):
    """Response for inspection fee calculation."""
    inspection_type: str
    fee_breakdown: FeeBreakdown


class ExtensionFeeRequest(BaseModel):
    """Request for permit extension fee calculation."""
    original_permit_fee: float = Field(..., ge=0)


class ExtensionFeeResponse(BaseModel):
    """Response for permit extension fee calculation."""
    original_permit_fee: float
    extension_fee: float
    fee_breakdown: FeeBreakdown
