"""
Documents API - PDF Checklist and Report Generation for the Calgary Building Code Expert System.

This module provides endpoints for:
- Downloading Development Permit (DP) checklists as PDF
- Downloading Building Permit (BP) checklists as PDF
- Downloading compliance reports as PDF
- Generating document checklists for any permit type
"""
import uuid as uuid_module
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
import io

from ..database import get_db
from ..models.permits import PermitApplication
from ..models.projects import Project, ComplianceCheck
from ..schemas.permits import ApplicationStatus
from ..services.pdf_generator import pdf_generator

router = APIRouter()


def _get_permit_application(
    application_id: str,
    db: Session
) -> PermitApplication:
    """
    Get a permit application by ID.

    Args:
        application_id: UUID of the permit application.
        db: Database session.

    Returns:
        PermitApplication object.

    Raises:
        HTTPException: If application not found or invalid ID.
    """
    try:
        app_uuid = uuid_module.UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application ID format")

    app = db.query(PermitApplication).filter(PermitApplication.id == app_uuid).first()

    if not app:
        raise HTTPException(
            status_code=404,
            detail=f"Permit application {application_id} not found"
        )

    return app


def _get_project(
    project_id: str,
    db: Session
) -> Project:
    """
    Get a project by ID.

    Args:
        project_id: UUID of the project.
        db: Database session.

    Returns:
        Project object.

    Raises:
        HTTPException: If project not found or invalid ID.
    """
    try:
        proj_uuid = uuid_module.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID format")

    project = db.query(Project).filter(Project.id == proj_uuid).first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project {project_id} not found"
        )

    return project


def _application_to_project_data(app: PermitApplication) -> dict:
    """Convert a permit application to project data dictionary for PDF generation."""
    return {
        "project_name": app.project_name or f"Project at {app.address}",
        "address": app.address or "N/A",
        "application_number": app.application_number or "N/A",
        "parcel_id": str(app.parcel_id) if app.parcel_id else None,
        "project_type": app.project_type,
        "classification": app.classification,
        "occupancy_group": app.occupancy_group,
        "building_area_sqm": float(app.building_area_sqm) if app.building_area_sqm else None,
        "building_height_storeys": app.building_height_storeys,
        "proposed_use": app.proposed_use,
        "zone": None,  # Would need to be looked up from parcel data
        "relaxations": app.relaxations_requested if app.relaxations_requested else [],
    }


def _project_to_data(project: Project) -> dict:
    """Convert a project to data dictionary for PDF generation."""
    return {
        "project_name": project.project_name or f"Project at {project.address}",
        "address": project.address or "N/A",
        "application_number": f"PRJ-{str(project.id)[:8].upper()}",
        "parcel_id": str(project.parcel_id) if project.parcel_id else None,
        "project_type": project.project_type,
        "classification": project.classification,
        "occupancy_group": project.occupancy_group,
        "building_area_sqm": float(project.building_area_sqm) if project.building_area_sqm else None,
        "building_height_storeys": project.building_height_storeys,
    }


def _create_pdf_response(
    pdf_bytes: bytes,
    filename: str,
    inline: bool = False
) -> Response:
    """
    Create a Response object for PDF download.

    Args:
        pdf_bytes: PDF content as bytes.
        filename: Suggested filename for download.
        inline: If True, display in browser; if False, force download.

    Returns:
        Response object with PDF content.
    """
    disposition = "inline" if inline else "attachment"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{disposition}; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        }
    )


# --- Development Permit Checklist Endpoints ---

@router.get("/checklists/dp")
async def download_dp_checklist(
    project_id: Optional[str] = Query(
        None,
        description="Project ID to generate checklist for (from Projects)"
    ),
    application_id: Optional[str] = Query(
        None,
        description="Permit application ID to generate checklist for"
    ),
    address: Optional[str] = Query(
        None,
        description="Property address (if no project/application ID provided)"
    ),
    project_name: Optional[str] = Query(
        None,
        description="Project name (optional, for custom checklist)"
    ),
    inline: bool = Query(
        False,
        description="If true, display PDF in browser instead of downloading"
    ),
    db: Session = Depends(get_db)
):
    """
    Download a Development Permit checklist as PDF.

    Provide either:
    - `application_id`: ID of an existing permit application
    - `project_id`: ID of an existing project
    - `address`: Property address for a custom checklist

    The PDF includes:
    - Required documents checklist
    - Zoning considerations
    - Key requirements to verify
    - Next steps and contact information
    """
    project_data = {}

    if application_id:
        # Get from permit application
        app = _get_permit_application(application_id, db)
        project_data = _application_to_project_data(app)

    elif project_id:
        # Get from project
        project = _get_project(project_id, db)
        project_data = _project_to_data(project)

    elif address:
        # Create custom checklist
        project_data = {
            "project_name": project_name or f"Project at {address}",
            "address": address,
            "application_number": "Not submitted",
        }
    else:
        raise HTTPException(
            status_code=400,
            detail="Must provide either application_id, project_id, or address"
        )

    # Generate PDF
    pdf_bytes = pdf_generator.generate_dp_checklist(project_data)

    # Create filename
    safe_address = (project_data.get('address') or 'project').replace(' ', '_').replace(',', '')[:30]
    filename = f"DP_Checklist_{safe_address}.pdf"

    return _create_pdf_response(pdf_bytes, filename, inline)


# --- Building Permit Checklist Endpoints ---

@router.get("/checklists/bp")
async def download_bp_checklist(
    project_id: Optional[str] = Query(
        None,
        description="Project ID to generate checklist for (from Projects)"
    ),
    application_id: Optional[str] = Query(
        None,
        description="Permit application ID to generate checklist for"
    ),
    address: Optional[str] = Query(
        None,
        description="Property address (if no project/application ID provided)"
    ),
    project_name: Optional[str] = Query(
        None,
        description="Project name (optional)"
    ),
    classification: Optional[str] = Query(
        None,
        description="Building classification: PART_9 or PART_3"
    ),
    occupancy_group: Optional[str] = Query(
        None,
        description="Occupancy group (e.g., C, D, E, F2)"
    ),
    inline: bool = Query(
        False,
        description="If true, display PDF in browser instead of downloading"
    ),
    db: Session = Depends(get_db)
):
    """
    Download a Building Permit checklist as PDF.

    Provide either:
    - `application_id`: ID of an existing permit application
    - `project_id`: ID of an existing project
    - `address`: Property address for a custom checklist

    The PDF includes:
    - Building classification information
    - Required documents checklist (varies by classification)
    - Building code compliance checklist
    - Inspection requirements
    - Contact information
    """
    project_data = {}

    if application_id:
        # Get from permit application
        app = _get_permit_application(application_id, db)
        project_data = _application_to_project_data(app)

    elif project_id:
        # Get from project
        project = _get_project(project_id, db)
        project_data = _project_to_data(project)

    elif address:
        # Create custom checklist
        project_data = {
            "project_name": project_name or f"Project at {address}",
            "address": address,
            "application_number": "Not submitted",
            "classification": classification,
            "occupancy_group": occupancy_group,
        }
    else:
        raise HTTPException(
            status_code=400,
            detail="Must provide either application_id, project_id, or address"
        )

    # Override classification/occupancy if provided
    if classification:
        project_data['classification'] = classification
    if occupancy_group:
        project_data['occupancy_group'] = occupancy_group

    # Generate PDF
    pdf_bytes = pdf_generator.generate_bp_checklist(project_data)

    # Create filename
    safe_address = (project_data.get('address') or 'project').replace(' ', '_').replace(',', '')[:30]
    filename = f"BP_Checklist_{safe_address}.pdf"

    return _create_pdf_response(pdf_bytes, filename, inline)


# --- Generic Document Checklist Endpoint ---

@router.get("/checklists/{permit_type}")
async def download_document_checklist(
    permit_type: str,
    project_id: Optional[str] = Query(None, description="Project ID"),
    application_id: Optional[str] = Query(None, description="Permit application ID"),
    address: Optional[str] = Query(None, description="Property address"),
    project_name: Optional[str] = Query(None, description="Project name"),
    inline: bool = Query(False, description="Display in browser"),
    db: Session = Depends(get_db)
):
    """
    Download a document checklist for the specified permit type.

    Supported permit types:
    - `dp` or `development`: Development Permit
    - `bp` or `building`: Building Permit
    - Other types will generate a generic checklist

    The PDF includes relevant document requirements for the permit type.
    """
    # Validate permit type
    valid_types = ['dp', 'development', 'development_permit',
                   'bp', 'building', 'building_permit',
                   'trade', 'electrical', 'plumbing', 'hvac', 'gas']

    permit_type_lower = permit_type.lower()

    project_data = {}

    if application_id:
        app = _get_permit_application(application_id, db)
        project_data = _application_to_project_data(app)
    elif project_id:
        project = _get_project(project_id, db)
        project_data = _project_to_data(project)
    elif address:
        project_data = {
            "project_name": project_name or f"Project at {address}",
            "address": address,
            "application_number": "Not submitted",
        }
    else:
        raise HTTPException(
            status_code=400,
            detail="Must provide either application_id, project_id, or address"
        )

    # Generate PDF
    pdf_bytes = pdf_generator.generate_document_checklist(permit_type, project_data)

    # Create filename
    safe_address = (project_data.get('address') or 'project').replace(' ', '_').replace(',', '')[:30]
    filename = f"{permit_type.upper()}_Checklist_{safe_address}.pdf"

    return _create_pdf_response(pdf_bytes, filename, inline)


# --- Compliance Report Endpoints ---

@router.get("/reports/compliance")
async def download_compliance_report(
    project_id: str = Query(..., description="Project ID to generate report for"),
    include_passed: bool = Query(
        True,
        description="Include passed checks in the report"
    ),
    inline: bool = Query(
        False,
        description="If true, display PDF in browser instead of downloading"
    ),
    db: Session = Depends(get_db)
):
    """
    Download a compliance check results report as PDF.

    The report includes:
    - Summary of all compliance checks (pass/fail/warning counts)
    - Detailed results grouped by category
    - Required actions for failed items
    - Recommendations and next steps

    Requires a project with compliance checks to have been run.
    """
    # Get project
    project = _get_project(project_id, db)
    project_data = _project_to_data(project)

    # Get compliance checks for this project
    query = db.query(ComplianceCheck).filter(
        ComplianceCheck.project_id == project.id
    )

    if not include_passed:
        query = query.filter(ComplianceCheck.status != 'pass')

    checks = query.order_by(
        ComplianceCheck.check_category,
        ComplianceCheck.check_name
    ).all()

    if not checks:
        raise HTTPException(
            status_code=404,
            detail=f"No compliance checks found for project {project_id}. "
                   "Please run compliance checks first using the REVIEW mode."
        )

    # Convert checks to dictionary format
    checks_data = []
    for check in checks:
        checks_data.append({
            "check_category": check.check_category,
            "check_name": check.check_name,
            "status": check.status,
            "required_value": check.required_value,
            "actual_value": check.actual_value,
            "code_reference": check.code_reference,
            "message": check.message,
        })

    # Generate PDF
    pdf_bytes = pdf_generator.generate_compliance_report(
        project_id=project_id,
        checks=checks_data,
        project_data=project_data
    )

    # Create filename
    safe_address = (project_data.get('address') or 'project').replace(' ', '_').replace(',', '')[:30]
    filename = f"Compliance_Report_{safe_address}.pdf"

    return _create_pdf_response(pdf_bytes, filename, inline)


@router.post("/reports/compliance/custom")
async def generate_custom_compliance_report(
    project_id: str = Query(..., description="Project ID for the report header"),
    checks: List[dict] = None,
    inline: bool = Query(False, description="Display in browser"),
    db: Session = Depends(get_db)
):
    """
    Generate a custom compliance report with provided check data.

    This endpoint allows generating a compliance report with custom check results,
    useful for previewing results before they are saved to the database.

    Request body should contain a list of checks, each with:
    - check_category: Category (zoning, egress, fire, etc.)
    - check_name: Name of the check
    - status: Result (pass, fail, warning, needs_review)
    - required_value: Required value (optional)
    - actual_value: Actual value found (optional)
    - code_reference: Code reference (optional)
    - message: Additional notes (optional)
    """
    # Get project data for header
    project = _get_project(project_id, db)
    project_data = _project_to_data(project)

    if not checks:
        raise HTTPException(
            status_code=400,
            detail="No checks provided. Include a list of checks in the request body."
        )

    # Generate PDF
    pdf_bytes = pdf_generator.generate_compliance_report(
        project_id=project_id,
        checks=checks,
        project_data=project_data
    )

    # Create filename
    filename = f"Compliance_Report_Custom_{project_id[:8]}.pdf"

    return _create_pdf_response(pdf_bytes, filename, inline)


# --- Information Endpoints ---

@router.get("/checklists/info/requirements")
async def get_checklist_requirements():
    """
    Get information about typical document requirements for different permit types.

    Returns a summary of commonly required documents for:
    - Development Permits (DP)
    - Building Permits (BP)
    """
    return {
        "development_permit": {
            "description": "Development Permit (DP) - Required for most land use changes",
            "typical_documents": [
                "Completed Application Form",
                "Certificate of Title (< 30 days old)",
                "Real Property Report / Survey",
                "Site Plan",
                "Floor Plans",
                "Building Elevations",
            ],
            "optional_documents": [
                "Roof Plan",
                "Landscape Plan",
                "Parking Layout",
                "Signage Details",
                "Traffic Impact Assessment",
                "Environmental Site Assessment",
            ],
            "typical_processing_time": "4-8 weeks for straightforward applications",
        },
        "building_permit": {
            "description": "Building Permit (BP) - Required before construction begins",
            "typical_documents": [
                "Approved Development Permit (if applicable)",
                "Completed Application Form",
                "Site Plan",
                "Architectural Drawings",
                "Structural Drawings",
                "Energy Compliance Documentation",
            ],
            "optional_documents": [
                "Structural Engineer's Seal",
                "Mechanical Drawings",
                "Plumbing Drawings",
                "Electrical Drawings",
                "Fire Safety Plan",
                "Geotechnical Report",
                "Truss Engineering",
                "Sprinkler System Drawings",
            ],
            "typical_processing_time": "2-4 weeks for Part 9 buildings, 4-8 weeks for Part 3",
        },
        "checklist_features": [
            "Checkbox format for tracking document preparation",
            "Indicates required vs. optional documents",
            "Includes relevant code requirements",
            "Provides next steps and contact information",
        ],
    }
