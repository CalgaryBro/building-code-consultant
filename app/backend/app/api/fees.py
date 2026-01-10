"""
Fees API - Calgary Building and Trade Permit Fee Calculator.

This module provides API endpoints for:
- Estimating permit fees for projects
- Getting the current fee schedule
- Calculating specific fee types (building, trade, inspection, etc.)

Based on the 2026 Building & Trade Permit Fee Schedule (R2026-02).
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..schemas.fees import (
    # Enums
    BuildingType, ResidentialAlterationType, TradePermitType,
    ProjectType, ZoneCategory,
    # Request/Response schemas
    BuildingPermitFeeRequest, BuildingPermitFeeResponse,
    TradePermitRequest, TradePermitFeeRequest, TradePermitFeeResponse,
    DevelopmentPermitFeeRequest, DevelopmentPermitFeeResponse,
    ProjectFeeEstimateRequest, ProjectFeeEstimateResponse,
    LotGradingFeeRequest, LotGradingFeeResponse,
    InspectionFeeRequest, InspectionFeeResponse,
    ExtensionFeeRequest, ExtensionFeeResponse,
    FeeScheduleResponse,
)
from ..services.fee_calculator import fee_calculator

router = APIRouter()


# --- Main Fee Estimation Endpoint ---

@router.post("/estimate", response_model=ProjectFeeEstimateResponse)
async def estimate_project_fees(
    request: ProjectFeeEstimateRequest,
):
    """
    Get a complete fee estimate for a construction project.

    This endpoint calculates all applicable fees including:
    - Development Permit fees (if required)
    - Building Permit fees
    - Trade Permit fees (electrical, plumbing, gas, HVAC)
    - Additional fees (lot grading, water, etc.)

    **Important Notes:**
    - Fees are based on the 2026 Building & Trade Permit Fee Schedule (R2026-02)
    - Development Permit fee estimates are approximate and vary by project complexity
    - For new residential (single/semi-detached/duplex), trade permits are included in BP fee
    - If work has started without a permit, double fees apply

    **Example Request:**
    ```json
    {
        "project_name": "New Single Family Home",
        "project_type": "new_construction",
        "building_type": "single_family",
        "construction_value": 500000,
        "floor_area_sqm": 200,
        "dwelling_units": 1,
        "requires_development_permit": true,
        "requires_building_permit": true,
        "include_lot_grading": true
    }
    ```
    """
    try:
        return fee_calculator.get_total_fees(request)
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Fee schedule data not found. Please contact support."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating fees: {str(e)}"
        )


# --- Fee Schedule Endpoint ---

@router.get("/schedule", response_model=FeeScheduleResponse)
async def get_fee_schedule():
    """
    Get the current fee schedule.

    Returns the complete 2026 Building & Trade Permit Fee Schedule including:
    - Building permit fees
    - Trade permit fees
    - Additional fees (inspections, extensions, lot grading, etc.)
    - Fee policies (refunds, double fee rules, etc.)
    - Safety Codes Council fee information
    """
    try:
        return fee_calculator.get_fee_schedule()
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Fee schedule data not found. Please contact support."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading fee schedule: {str(e)}"
        )


# --- Building Permit Fee Endpoint ---

@router.post("/building-permit", response_model=BuildingPermitFeeResponse)
async def calculate_building_permit_fee(
    request: BuildingPermitFeeRequest,
):
    """
    Calculate Building Permit fees.

    **Fee Calculation:**
    - Commercial/Multi-family: $112 processing + $10.14 per $1,000 construction value
    - Residential new: $112 processing + $10.14 per $1,000 construction value (includes trade permits)
    - Demolition: $112 processing + $1.44 per square metre
    - Residential alterations: Flat fees based on type

    **Residential Alteration Types:**
    - `basement_garage_addition_small`: $333.84 total
    - `new_secondary_suite`: $403.52 total
    - `existing_secondary_suite`: $205.92 total
    - `new_backyard_suite`: $1,302.08 total
    - `minor_alterations`: $205.92 total (carport, deck, pool, etc.)
    - `addition_large`: $1,302.08 total (over 400 sq ft)

    **Example Request:**
    ```json
    {
        "building_type": "commercial",
        "construction_value": 1000000,
        "work_started_without_permit": false
    }
    ```
    """
    try:
        return fee_calculator.calculate_bp_fee(
            building_type=request.building_type,
            construction_value=request.construction_value,
            floor_area_sqm=request.floor_area_sqm,
            alteration_type=request.alteration_type,
            dwelling_units=request.dwelling_units,
            work_started_without_permit=request.work_started_without_permit,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating building permit fee: {str(e)}"
        )


# --- Trade Permit Fees Endpoint ---

@router.post("/trade-permits", response_model=TradePermitFeeResponse)
async def calculate_trade_permit_fees(
    request: TradePermitFeeRequest,
):
    """
    Calculate Trade Permit fees for electrical, plumbing, gas, and HVAC work.

    **Fee Calculation:**
    - Standard trade permit: $112 processing + $9.79 per $1,000 construction value
    - Homeowner permit: $116.50 flat fee
    - Annual electrical permit: $162.24 flat fee

    **Note:** For new single/semi-detached/duplex dwellings, trade permits are
    included in the Building Permit fee.

    **Example Request:**
    ```json
    {
        "trades": [
            {"trade_type": "electrical", "construction_value": 50000},
            {"trade_type": "plumbing", "construction_value": 30000}
        ],
        "work_started_without_permit": false
    }
    ```
    """
    try:
        return fee_calculator.calculate_trade_fees(
            trades=request.trades,
            work_started_without_permit=request.work_started_without_permit,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating trade permit fees: {str(e)}"
        )


# --- Development Permit Fee Endpoint ---

@router.post("/development-permit", response_model=DevelopmentPermitFeeResponse)
async def calculate_development_permit_fee(
    request: DevelopmentPermitFeeRequest,
):
    """
    Estimate Development Permit fees.

    **Important:** Development Permit fees vary significantly based on project
    complexity, location, and review requirements. This endpoint provides an
    estimate only. Contact the Planning Services Centre for accurate quotes.

    **Factors affecting DP fees:**
    - Project type (new construction, alteration, change of use)
    - Floor area
    - Zoning relaxations required
    - Discretionary vs. permitted use

    **Example Request:**
    ```json
    {
        "project_type": "new_construction",
        "floor_area_sqm": 500,
        "zone_category": "commercial",
        "requires_relaxation": false,
        "is_discretionary": false
    }
    ```
    """
    try:
        return fee_calculator.calculate_dp_fee(
            project_type=request.project_type,
            floor_area_sqm=request.floor_area_sqm,
            zone_category=request.zone_category,
            requires_relaxation=request.requires_relaxation,
            is_discretionary=request.is_discretionary,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating development permit fee: {str(e)}"
        )


# --- Lot Grading Fee Endpoint ---

@router.post("/lot-grading", response_model=LotGradingFeeResponse)
async def calculate_lot_grading_fee(
    request: LotGradingFeeRequest,
):
    """
    Calculate lot grading fees.

    Based on Lot Grading Bylaw 32M2004:
    - Single/semi-detached/duplex and small multi-family (<10 units): $20/ground floor unit
    - Multi-family (10+ units, up to 3 storeys): $100 + $10/ground floor unit
    - Large commercial/industrial/high-rise: $80/hectare (min $80)

    **Example Request:**
    ```json
    {
        "building_type": "single_family",
        "dwelling_units": 1,
        "ground_floor_units": 1
    }
    ```
    """
    try:
        return fee_calculator.calculate_lot_grading_fee(
            building_type=request.building_type,
            dwelling_units=request.dwelling_units,
            ground_floor_units=request.ground_floor_units,
            storeys=request.storeys,
            lot_area_hectares=request.lot_area_hectares,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating lot grading fee: {str(e)}"
        )


# --- Inspection Fee Endpoint ---

@router.post("/inspection", response_model=InspectionFeeResponse)
async def calculate_inspection_fee(
    request: InspectionFeeRequest,
):
    """
    Calculate inspection fees.

    **Inspection Types:**
    - `safety_inspection`: $6,125.80 total (includes GST)
    - `weekend_holiday`: $189/hour, minimum 4 hours ($756 min)
    - `re_inspection`: $327 total (includes GST)

    **Example Request:**
    ```json
    {
        "inspection_type": "re_inspection"
    }
    ```

    For weekend/holiday inspections:
    ```json
    {
        "inspection_type": "weekend_holiday",
        "hours": 6
    }
    ```
    """
    try:
        return fee_calculator.calculate_inspection_fee(
            inspection_type=request.inspection_type,
            hours=request.hours,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating inspection fee: {str(e)}"
        )


# --- Extension Fee Endpoint ---

@router.post("/extension", response_model=ExtensionFeeResponse)
async def calculate_extension_fee(
    request: ExtensionFeeRequest,
):
    """
    Calculate permit extension fees.

    Extension fee is 10% of the original permit fee:
    - Processing fee: $112
    - Base fee: 10% of original permit fee (min $112, max $8,852)
    - Safety Codes Council fee: 4% (min $4.50, max $560)

    **Example Request:**
    ```json
    {
        "original_permit_fee": 5000
    }
    ```
    """
    try:
        return fee_calculator.calculate_extension_fee(
            original_permit_fee=request.original_permit_fee,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating extension fee: {str(e)}"
        )


# --- Quick Estimate Endpoints ---

class QuickEstimateRequest(BaseModel):
    """Simplified request for quick fee estimates."""
    building_type: BuildingType
    construction_value: float = Field(..., ge=0, description="Construction value in CAD")


class QuickEstimateResponse(BaseModel):
    """Simplified response for quick fee estimates."""
    building_permit_fee: float
    trade_permit_fee: Optional[float] = None
    total_estimate: float
    notes: List[str]


@router.post("/quick-estimate", response_model=QuickEstimateResponse)
async def get_quick_estimate(
    request: QuickEstimateRequest,
):
    """
    Get a quick fee estimate based on building type and construction value.

    This is a simplified endpoint for quick estimates. For detailed breakdowns,
    use the `/estimate` endpoint.

    **Example Request:**
    ```json
    {
        "building_type": "commercial",
        "construction_value": 500000
    }
    ```
    """
    try:
        bp_response = fee_calculator.calculate_bp_fee(
            building_type=request.building_type,
            construction_value=request.construction_value,
        )

        notes = list(bp_response.fee_breakdown.notes)
        total = bp_response.fee_breakdown.total
        trade_fee = None

        # Add trade permit estimate for non-residential
        if not bp_response.includes_trade_permits and request.building_type not in [
            BuildingType.SINGLE_FAMILY, BuildingType.SEMI_DETACHED, BuildingType.DUPLEX
        ]:
            # Estimate trade permits as ~30% of construction value for combined trades
            estimated_trade_value = request.construction_value * 0.3
            trade_response = fee_calculator.calculate_trade_fees([
                TradePermitRequest(
                    trade_type=TradePermitType.ELECTRICAL,
                    construction_value=estimated_trade_value * 0.4,
                ),
                TradePermitRequest(
                    trade_type=TradePermitType.PLUMBING,
                    construction_value=estimated_trade_value * 0.3,
                ),
                TradePermitRequest(
                    trade_type=TradePermitType.HVAC,
                    construction_value=estimated_trade_value * 0.3,
                ),
            ])
            trade_fee = trade_response.combined_total
            total += trade_fee
            notes.append("Trade permit fees are estimated at 30% of construction value split between electrical (40%), plumbing (30%), and HVAC (30%).")
        else:
            notes.append("Trade permits are included in the Building Permit fee for new residential dwellings.")

        return QuickEstimateResponse(
            building_permit_fee=bp_response.fee_breakdown.total,
            trade_permit_fee=trade_fee,
            total_estimate=total,
            notes=notes,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating quick estimate: {str(e)}"
        )


# --- Fee Type Information Endpoints ---

@router.get("/building-types")
async def list_building_types():
    """
    List all available building types for fee calculation.

    Returns building types and their categories.
    """
    return {
        "residential": [
            {"value": "single_family", "label": "Single Family Home"},
            {"value": "semi_detached", "label": "Semi-detached Home"},
            {"value": "duplex", "label": "Duplex"},
        ],
        "multi_family": [
            {"value": "multi_family_low_rise", "label": "Multi-family Low Rise (Wood Frame)"},
            {"value": "multi_family_high_rise", "label": "Multi-family High Rise (Non-combustible)"},
        ],
        "commercial": [
            {"value": "commercial", "label": "Commercial Building"},
            {"value": "hotel", "label": "Hotel/Motel"},
            {"value": "warehouse", "label": "Warehouse/Storage"},
            {"value": "care_facility", "label": "Care Facility/Hospital"},
        ],
        "other": [
            {"value": "commercial_alteration", "label": "Commercial Alteration"},
            {"value": "demolition", "label": "Demolition"},
        ],
    }


@router.get("/alteration-types")
async def list_alteration_types():
    """
    List all residential alteration types and their flat fees.
    """
    return {
        "alterations": [
            {
                "value": "basement_garage_addition_small",
                "label": "Basement, Garage, or Addition under 400 sq ft",
                "total_fee": 333.84,
            },
            {
                "value": "new_secondary_suite",
                "label": "New Secondary Suite",
                "total_fee": 403.52,
            },
            {
                "value": "existing_secondary_suite",
                "label": "Existing Secondary Suite",
                "total_fee": 205.92,
            },
            {
                "value": "new_backyard_suite",
                "label": "New Backyard Suite",
                "total_fee": 1302.08,
            },
            {
                "value": "minor_alterations",
                "label": "Minor Alterations (carport, deck, pool, fireplace, etc.)",
                "total_fee": 205.92,
            },
            {
                "value": "addition_large",
                "label": "Addition over 400 sq ft",
                "total_fee": 1302.08,
            },
        ]
    }


@router.get("/trade-types")
async def list_trade_types():
    """
    List all trade permit types.
    """
    return {
        "standard": [
            {"value": "electrical", "label": "Electrical"},
            {"value": "plumbing", "label": "Plumbing"},
            {"value": "gas", "label": "Gas"},
            {"value": "hvac", "label": "HVAC/Mechanical"},
        ],
        "special": [
            {"value": "homeowner", "label": "Homeowner Permit", "flat_fee": 116.50},
            {"value": "annual_electrical", "label": "Annual Electrical Permit", "flat_fee": 162.24},
        ],
    }
