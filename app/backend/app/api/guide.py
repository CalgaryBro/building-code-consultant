"""
GUIDE Mode API - Get permit requirements for your project.

This mode helps users understand:
- What permits are required for their project
- Which code classification applies (Part 9 vs Part 3)
- Key building code requirements
- Estimated fees and timelines
- Required documentation
"""
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.zones import Zone, Parcel
from ..models.projects import Project
from ..schemas.projects import (
    GuideProjectInput, GuideResponse, PermitRequirement,
    ProjectCreate, ProjectResponse
)
from ..schemas.zones import ZoningCheckRequest

router = APIRouter()


def classify_building(
    building_height_storeys: Optional[int],
    footprint_area_sqm: Optional[float],
    building_area_sqm: Optional[float],
    occupancy_type: str
) -> tuple[str, str]:
    """
    Determine if building falls under Part 9 or Part 3 of NBC.

    Part 9 applies to:
    - Buildings of 3 storeys or less in building height
    - Having a building area not exceeding 600 m²
    - Used for specific major occupancies (Group C, D, E, F2, F3)

    Returns (classification, reason)
    """
    # Default assumptions if not provided
    storeys = building_height_storeys or 1
    footprint = footprint_area_sqm or 0
    total_area = building_area_sqm or footprint

    # Part 9 occupancy groups
    part_9_occupancies = ["residential", "business", "mercantile", "low_hazard_industrial", "medium_hazard_industrial"]
    high_hazard_occupancies = ["assembly", "care", "detention", "high_hazard_industrial"]

    # Check occupancy type
    occupancy_lower = occupancy_type.lower()
    is_part_9_occupancy = occupancy_lower in part_9_occupancies or occupancy_lower == "commercial"

    # Check dimensional limits
    exceeds_height = storeys > 3
    exceeds_area = footprint > 600

    # Determine classification
    if occupancy_lower in high_hazard_occupancies:
        return ("PART_3", f"Occupancy type '{occupancy_type}' requires Part 3 design regardless of size")

    if exceeds_height and exceeds_area:
        return ("PART_3", f"Building exceeds Part 9 limits: {storeys} storeys (max 3) and {footprint} m² footprint (max 600 m²)")

    if exceeds_height:
        return ("PART_3", f"Building height of {storeys} storeys exceeds Part 9 limit of 3 storeys")

    if exceeds_area:
        return ("PART_3", f"Building footprint of {footprint} m² exceeds Part 9 limit of 600 m²")

    if is_part_9_occupancy:
        return ("PART_9", f"Building qualifies for Part 9: ≤3 storeys, ≤600 m² footprint, {occupancy_type} occupancy")

    return ("PART_3", f"Occupancy type '{occupancy_type}' typically requires Part 3 design")


def determine_permits_required(
    project_type: str,
    classification: str,
    occupancy_type: str,
    building_area_sqm: Optional[float],
    dwelling_units: Optional[int],
    zone: Optional[Zone]
) -> List[PermitRequirement]:
    """
    Determine which permits are required based on project parameters.
    """
    permits = []

    # Development Permit
    # Generally required unless project is exempt (e.g., single-family in established area)
    dp_required = True
    dp_notes = None

    if project_type == "renovation" and (building_area_sqm or 0) < 50:
        dp_required = False
        dp_notes = "Minor renovations under 50 m² typically exempt from development permit"
    elif project_type == "new_construction" and occupancy_type == "residential" and (dwelling_units or 0) <= 1:
        if zone and zone.category == "residential":
            dp_notes = "Single-family dwelling in residential zone - may qualify for deemed approval"

    permits.append(PermitRequirement(
        permit_type="development_permit",
        required=dp_required,
        description="Development Permit from City of Calgary Planning",
        estimated_fee=_calculate_dp_fee(building_area_sqm, project_type),
        typical_timeline_days=60 if dp_required else 0,
        documents_required=[
            "Site plan showing setbacks and lot coverage",
            "Building elevations",
            "Floor plans",
            "Landscaping plan (if applicable)"
        ] if dp_required else [],
        notes=dp_notes
    ))

    # Building Permit
    # Almost always required for new construction and major renovations
    bp_required = project_type in ["new_construction", "addition", "change_of_use"] or (building_area_sqm or 0) > 10

    permits.append(PermitRequirement(
        permit_type="building_permit",
        required=bp_required,
        description="Building Permit from City of Calgary Building Safety",
        estimated_fee=_calculate_bp_fee(building_area_sqm, classification),
        typical_timeline_days=30 if classification == "PART_9" else 60,
        documents_required=[
            "Stamped architectural drawings (Part 3) or prepared drawings (Part 9)",
            "Structural drawings and calculations",
            "HVAC design",
            "Energy compliance documentation (NECB)",
            "Site servicing plan",
            "Geotechnical report (if required)"
        ] if bp_required else [],
        notes=f"{classification} building - {'professional design required' if classification == 'PART_3' else 'design by qualified person acceptable'}"
    ))

    # Trade Permits
    permits.append(PermitRequirement(
        permit_type="electrical_permit",
        required=bp_required,
        description="Electrical Permit",
        estimated_fee=200 if (building_area_sqm or 0) < 200 else 500,
        typical_timeline_days=5,
        documents_required=["Electrical drawings", "Load calculations"],
        notes="Required for all new electrical work"
    ))

    permits.append(PermitRequirement(
        permit_type="plumbing_permit",
        required=bp_required,
        description="Plumbing Permit",
        estimated_fee=150 if (building_area_sqm or 0) < 200 else 400,
        typical_timeline_days=5,
        documents_required=["Plumbing layout", "Fixture count"],
        notes="Required for all new plumbing work"
    ))

    permits.append(PermitRequirement(
        permit_type="gas_permit",
        required=bp_required,
        description="Gas Permit",
        estimated_fee=100,
        typical_timeline_days=5,
        documents_required=["Gas piping layout", "Appliance specifications"],
        notes="Required if gas appliances are installed"
    ))

    return permits


def _calculate_dp_fee(area_sqm: Optional[float], project_type: str) -> float:
    """Calculate estimated development permit fee."""
    base_fee = 500
    area = area_sqm or 100

    if project_type == "new_construction":
        return base_fee + (area * 2.5)
    elif project_type == "addition":
        return base_fee + (area * 2.0)
    else:
        return base_fee


def _calculate_bp_fee(area_sqm: Optional[float], classification: str) -> float:
    """Calculate estimated building permit fee."""
    area = area_sqm or 100

    # Calgary uses approximately $12-15 per m² for Part 9, more for Part 3
    rate = 12 if classification == "PART_9" else 18
    base_fee = 200

    return base_fee + (area * rate)


@router.post("/analyze", response_model=GuideResponse)
async def analyze_project(
    project_input: GuideProjectInput,
    db: Session = Depends(get_db)
):
    """
    Analyze a proposed project and provide permit guidance.

    This is the main GUIDE mode endpoint. Provide project details and receive:
    - Building classification (Part 9 vs Part 3)
    - Zoning compliance status
    - Required permits with estimated fees
    - Key code requirements to consider
    - Next steps for the permit process
    """
    warnings = []

    # Find the parcel
    parcel = db.query(Parcel).filter(
        Parcel.address.ilike(f"%{project_input.address}%")
    ).first()

    if not parcel:
        warnings.append(f"Address '{project_input.address}' not found in Calgary parcel database. Zoning rules may not be accurate.")

    # Get zone information
    zone = None
    zoning_status = "unknown"

    if parcel and parcel.zone_id:
        zone = db.query(Zone).filter(Zone.id == parcel.zone_id).first()
        zoning_status = "pending_check"
    else:
        warnings.append("Could not determine zoning for this address. Manual verification required.")

    # Classify the building
    classification, classification_reason = classify_building(
        project_input.building_height_storeys,
        project_input.footprint_area_sqm,
        project_input.building_area_sqm,
        project_input.occupancy_type
    )

    # Determine required permits
    permits = determine_permits_required(
        project_input.project_type,
        classification,
        project_input.occupancy_type,
        project_input.building_area_sqm,
        project_input.dwelling_units,
        zone
    )

    # Build key requirements list
    key_requirements = []

    if classification == "PART_9":
        key_requirements.extend([
            "NBC(AE) 2023 Part 9 applies - residential and small buildings",
            "Maximum 3 storeys, 600 m² footprint",
            "Minimum ceiling height: 2.3 m (habitable rooms)",
            "Stairs: minimum 860 mm wide, maximum 200 mm rise, minimum 255 mm run",
            "Egress windows required in bedrooms",
            "Smoke alarms required on each floor and in bedrooms"
        ])
    else:
        key_requirements.extend([
            "NBC(AE) 2023 Part 3 applies - requires professional design",
            "Architect/Engineer stamped drawings required",
            "Sprinkler system likely required",
            "Fire separations based on occupancy classification",
            "Accessible design per NBC Section 3.8"
        ])

    if zone:
        key_requirements.append(f"Zone {zone.zone_code}: Max height {zone.max_height_m or 'TBD'} m, {zone.max_storeys or 'TBD'} storeys")
        if zone.min_front_setback_m:
            key_requirements.append(f"Front setback: minimum {zone.min_front_setback_m} m")

    # Build next steps
    next_steps = [
        "1. Confirm address and verify current zoning designation",
        "2. Prepare preliminary site plan showing setbacks and building footprint",
        f"3. {'Engage architect/engineer for Part 3 design' if classification == 'PART_3' else 'Prepare Part 9 compliant drawings'}",
        "4. Submit Development Permit application (if required)",
        "5. Wait for DP approval before submitting Building Permit",
        "6. Submit Building Permit with complete drawing package",
        "7. Schedule inspections during construction"
    ]

    # Create project record
    project = Project(
        project_name=f"Project at {project_input.address}",
        description=project_input.description,
        address=project_input.address,
        parcel_id=parcel.id if parcel else None,
        classification=classification,
        occupancy_group=_map_occupancy_type(project_input.occupancy_type),
        building_height_storeys=project_input.building_height_storeys,
        building_area_sqm=project_input.building_area_sqm,
        footprint_area_sqm=project_input.footprint_area_sqm,
        dwelling_units=project_input.dwelling_units,
        project_type=project_input.project_type,
        development_permit_required=any(p.permit_type == "development_permit" and p.required for p in permits),
        building_permit_required=any(p.permit_type == "building_permit" and p.required for p in permits),
        estimated_permit_fee=sum(p.estimated_fee or 0 for p in permits if p.required),
        status="draft"
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return GuideResponse(
        project=project,
        classification=classification,
        classification_reason=classification_reason,
        zoning_status=zoning_status,
        permits_required=permits,
        key_requirements=key_requirements,
        next_steps=next_steps,
        warnings=warnings
    )


def _map_occupancy_type(occupancy_type: str) -> str:
    """Map user-friendly occupancy type to NBC classification."""
    mapping = {
        "residential": "C",
        "commercial": "D",
        "business": "D",
        "mercantile": "E",
        "retail": "E",
        "industrial": "F2",
        "low_hazard_industrial": "F3",
        "medium_hazard_industrial": "F2",
        "high_hazard_industrial": "F1",
        "assembly": "A2",
        "care": "B2",
        "mixed": "D"  # Default to business for mixed use
    }
    return mapping.get(occupancy_type.lower(), "D")


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List all projects created through GUIDE mode.
    """
    query = db.query(Project)

    if status:
        query = query.filter(Project.status == status)

    return query.order_by(Project.created_at.desc()).limit(limit).all()


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID, db: Session = Depends(get_db)):
    """
    Get details for a specific project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.get("/classification")
async def explain_classification():
    """
    Explain the Part 9 vs Part 3 classification system.
    """
    return {
        "overview": "The National Building Code of Canada divides buildings into Part 9 (small buildings) and Part 3 (large/complex buildings).",
        "part_9": {
            "name": "Part 9 - Housing and Small Buildings",
            "applies_to": [
                "Buildings of 3 storeys or less in building height",
                "Buildings with footprint area ≤ 600 m²",
                "Occupancies: Residential (C), Business (D), Mercantile (E), Low/Medium Hazard Industrial (F2, F3)"
            ],
            "benefits": [
                "Prescriptive requirements - easier to follow",
                "Design can be prepared by qualified persons (not necessarily architects/engineers)",
                "Faster permit review",
                "Lower design costs"
            ]
        },
        "part_3": {
            "name": "Part 3 - Fire Protection, Occupant Safety, and Accessibility",
            "applies_to": [
                "Buildings over 3 storeys",
                "Buildings with footprint area > 600 m²",
                "High occupancy loads",
                "Assembly (A), Care (B), High Hazard Industrial (F1)"
            ],
            "requirements": [
                "Professional design by licensed architect and/or engineer",
                "Detailed fire safety analysis",
                "Sprinkler systems often required",
                "Accessible design requirements",
                "More complex egress design"
            ]
        }
    }
