"""
REVIEW Mode API - Check drawings for code compliance.

This mode allows users to:
- Upload architectural drawings (PDF, images)
- Extract building parameters using VLM (Qwen-VL)
- Run compliance checks against applicable codes
- Get detailed compliance reports
- Verify and correct extracted values
"""
import os
import uuid
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.projects import Project, Document, ExtractedData, ComplianceCheck
from ..models.codes import Requirement
from ..schemas.projects import (
    DocumentUpload, DocumentResponse,
    ExtractedDataResponse, ExtractedDataVerification,
    ComplianceCheckResponse, ComplianceCheckCreate,
    ReviewRequest, ReviewProgress, ReviewSummary
)
from ..config import get_settings

settings = get_settings()
router = APIRouter()

# Upload directory
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/projects/{project_id}/documents", response_model=DocumentResponse)
async def upload_document(
    project_id: UUID,
    document_type: Optional[str] = Form(None, description="floor_plan, site_plan, elevation, section, schedule"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a drawing or document for a project.

    Supported formats:
    - PDF (architectural drawings)
    - PNG, JPG (scanned plans or screenshots)

    After upload, use /extract endpoint to extract building parameters.
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate file type
    allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not supported. Allowed: PDF, PNG, JPG"
        )

    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{project_id}_{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Save file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Determine file type category
    if file.content_type == "application/pdf":
        file_type = "pdf"
    else:
        file_type = "image"

    # Create document record
    document = Document(
        project_id=project_id,
        filename=file.filename,
        file_path=file_path,
        file_type=file_type,
        file_size_bytes=len(content),
        document_type=document_type,
        extraction_status="pending"
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


@router.get("/projects/{project_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """
    List all documents uploaded for a project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return db.query(Document).filter(Document.project_id == project_id).all()


@router.post("/documents/{document_id}/extract")
async def extract_from_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start extraction of building parameters from a document using VLM.

    This endpoint triggers an async extraction process using Qwen-VL via Ollama.
    The extraction identifies:
    - Dimensions (room sizes, stair widths, door widths)
    - Counts (rooms, exits, stairs, fixtures)
    - Labels (room names, occupancy types)
    - Areas (floor areas, lot coverage)

    All extracted values require human verification before use in compliance checks.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.extraction_status == "processing":
        raise HTTPException(status_code=400, detail="Extraction already in progress")

    # Update status
    document.extraction_status = "processing"
    document.extraction_started_at = datetime.utcnow()
    db.commit()

    # Queue extraction task
    background_tasks.add_task(
        _run_extraction,
        document_id=document_id,
        file_path=document.file_path,
        document_type=document.document_type
    )

    return {
        "message": "Extraction started",
        "document_id": str(document_id),
        "status": "processing",
        "check_status_at": f"/api/v1/review/documents/{document_id}/extraction-status"
    }


async def _run_extraction(document_id: UUID, file_path: str, document_type: Optional[str]):
    """
    Background task to run VLM extraction.

    This function calls Ollama with Qwen-VL to analyze the document.
    """
    from ..database import SessionLocal

    db = SessionLocal()

    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return

        # Determine what to look for based on document type
        extraction_prompts = _get_extraction_prompts(document_type)

        # TODO: Call Ollama with Qwen-VL
        # For now, create placeholder extracted data

        # This is where we would call:
        # import ollama
        # response = ollama.chat(
        #     model=settings.ollama_model,
        #     messages=[{
        #         'role': 'user',
        #         'content': extraction_prompts['full_prompt'],
        #         'images': [file_path] if file_type == 'image' else []
        #     }]
        # )

        # Create sample extracted data entries (placeholder)
        sample_fields = [
            ("stair_width", "dimension", "860", 860, "mm", "LOW"),
            ("exit_count", "count", "2", 2, None, "MEDIUM"),
            ("floor_area", "area", "450", 450, "m²", "LOW"),
        ]

        for field_name, category, raw, numeric, unit, confidence in sample_fields:
            extracted = ExtractedData(
                document_id=document_id,
                field_name=field_name,
                field_category=category,
                value_raw=raw,
                value_numeric=numeric,
                unit=unit,
                confidence=confidence,
                extraction_notes="Placeholder - VLM extraction not yet implemented",
                is_verified=False
            )
            db.add(extracted)

        document.extraction_status = "complete"
        document.extraction_completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.extraction_status = "failed"
            document.extraction_error = str(e)
            db.commit()
    finally:
        db.close()


def _get_extraction_prompts(document_type: Optional[str]) -> dict:
    """
    Get extraction prompts based on document type.
    """
    base_prompt = """Analyze this architectural drawing and extract the following information.
For each value found, indicate your confidence level (HIGH, MEDIUM, LOW).

"""

    if document_type == "floor_plan":
        specific = """Focus on:
- Room dimensions (length x width)
- Door widths
- Stair widths and configurations
- Corridor widths
- Exit door locations
- Room labels and uses
"""
    elif document_type == "site_plan":
        specific = """Focus on:
- Building setbacks (front, side, rear)
- Lot dimensions
- Building footprint area
- Lot coverage percentage
- Parking stall counts
- Driveway width
"""
    elif document_type == "elevation":
        specific = """Focus on:
- Building height (to peak, to midpoint of roof)
- Number of storeys
- Window sizes
- Grade levels
"""
    else:
        specific = """Extract any building-related dimensions, counts, or specifications you can identify.
"""

    return {
        "full_prompt": base_prompt + specific,
        "document_type": document_type
    }


@router.get("/documents/{document_id}/extraction-status")
async def get_extraction_status(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Check the status of document extraction.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    extracted_count = db.query(ExtractedData).filter(
        ExtractedData.document_id == document_id
    ).count()

    return {
        "document_id": str(document_id),
        "status": document.extraction_status,
        "started_at": document.extraction_started_at,
        "completed_at": document.extraction_completed_at,
        "error": document.extraction_error,
        "extracted_values_count": extracted_count
    }


@router.get("/documents/{document_id}/extracted", response_model=List[ExtractedDataResponse])
async def get_extracted_data(
    document_id: UUID,
    verified_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get all extracted data from a document.
    """
    query = db.query(ExtractedData).filter(ExtractedData.document_id == document_id)

    if verified_only:
        query = query.filter(ExtractedData.is_verified == True)

    return query.all()


@router.put("/extracted/{extracted_id}/verify", response_model=ExtractedDataResponse)
async def verify_extracted_data(
    extracted_id: UUID,
    verification: ExtractedDataVerification,
    db: Session = Depends(get_db)
):
    """
    Verify or correct an extracted value.

    IMPORTANT: All life-safety critical values (egress widths, fire ratings, etc.)
    MUST be verified by a qualified professional before being used in compliance checks.
    """
    extracted = db.query(ExtractedData).filter(ExtractedData.id == extracted_id).first()
    if not extracted:
        raise HTTPException(status_code=404, detail="Extracted data not found")

    extracted.is_verified = True
    extracted.verified_value = verification.verified_value
    extracted.verified_by = verification.verified_by
    extracted.verified_at = datetime.utcnow()
    extracted.verification_notes = verification.verification_notes

    db.commit()
    db.refresh(extracted)

    return extracted


@router.post("/projects/{project_id}/run-checks", response_model=ReviewSummary)
async def run_compliance_checks(
    project_id: UUID,
    check_categories: Optional[List[str]] = None,
    use_unverified: bool = False,
    db: Session = Depends(get_db)
):
    """
    Run compliance checks on a project using extracted values.

    By default, only verified values are used. Set use_unverified=True to include
    unverified values (results will be marked as needing review).

    Check categories:
    - zoning: Setbacks, height, FAR, parking
    - egress: Exit widths, travel distances, stair requirements
    - fire: Fire separations, sprinkler requirements
    - accessibility: Accessible routes, washrooms
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get all extracted data for project's documents
    documents = db.query(Document).filter(Document.project_id == project_id).all()
    doc_ids = [d.id for d in documents]

    extracted_query = db.query(ExtractedData).filter(ExtractedData.document_id.in_(doc_ids))
    if not use_unverified:
        extracted_query = extracted_query.filter(ExtractedData.is_verified == True)

    extracted_data = {e.field_name: e for e in extracted_query.all()}

    # Get applicable requirements
    requirements_query = db.query(Requirement)

    if project.classification == "PART_9":
        requirements_query = requirements_query.filter(Requirement.applies_to_part_9 == True)
    else:
        requirements_query = requirements_query.filter(Requirement.applies_to_part_3 == True)

    if project.occupancy_group:
        requirements_query = requirements_query.filter(
            Requirement.occupancy_groups.contains([project.occupancy_group])
        )

    requirements = requirements_query.all()

    # Run checks
    checks = []
    passed = 0
    failed = 0
    warnings = 0
    needs_review = 0

    for req in requirements:
        # Skip if we don't have the extracted value
        if req.element not in extracted_data:
            continue

        # Skip if not in requested categories
        if check_categories:
            # Map element to category
            category = _element_to_category(req.element)
            if category not in check_categories:
                continue

        extracted = extracted_data[req.element]

        # Perform the check
        check_result = _perform_check(req, extracted)

        check = ComplianceCheck(
            project_id=project_id,
            requirement_id=req.id,
            check_category=_element_to_category(req.element),
            check_name=req.description or req.element,
            element=req.element,
            required_value=_format_requirement_value(req),
            actual_value=extracted.verified_value if extracted.is_verified else extracted.value_raw,
            unit=req.unit,
            status=check_result["status"],
            message=check_result["message"],
            code_reference=f"{req.article.code.short_name} {req.article.article_number}" if req.article else None,
            extracted_from_document_id=extracted.document_id,
            extraction_confidence=extracted.confidence,
            is_verified=extracted.is_verified
        )

        db.add(check)
        checks.append(check)

        # Count results
        if check_result["status"] == "pass":
            passed += 1
        elif check_result["status"] == "fail":
            failed += 1
        elif check_result["status"] == "warning":
            warnings += 1
        else:
            needs_review += 1

    # Update project overall compliance
    if failed > 0:
        project.overall_compliance = "fail"
    elif needs_review > 0:
        project.overall_compliance = "needs_review"
    elif warnings > 0:
        project.overall_compliance = "warning"
    else:
        project.overall_compliance = "pass"

    db.commit()

    # Build recommendations
    recommendations = []
    if failed > 0:
        recommendations.append(f"{failed} compliance issue(s) must be addressed before permit approval")
    if needs_review > 0:
        recommendations.append(f"{needs_review} check(s) require verification of extracted values")
    if not extracted_data:
        recommendations.append("No extracted data available. Upload drawings and run extraction first.")

    return ReviewSummary(
        project_id=project_id,
        overall_status=project.overall_compliance or "needs_review",
        total_checks=len(checks),
        passed=passed,
        failed=failed,
        warnings=warnings,
        needs_review=needs_review,
        critical_issues=[c for c in checks if c.status == "fail"],
        all_checks=checks,
        recommendations=recommendations
    )


def _element_to_category(element: str) -> str:
    """Map element names to check categories."""
    egress_elements = ["stair_width", "exit_width", "corridor_width", "door_width", "exit_count", "travel_distance"]
    fire_elements = ["fire_rating", "fire_separation", "sprinkler", "smoke_alarm"]
    zoning_elements = ["setback", "height", "far", "parking", "lot_coverage"]
    accessibility_elements = ["accessible", "barrier_free", "ramp", "elevator"]

    element_lower = element.lower()

    for e in egress_elements:
        if e in element_lower:
            return "egress"
    for e in fire_elements:
        if e in element_lower:
            return "fire"
    for e in zoning_elements:
        if e in element_lower:
            return "zoning"
    for e in accessibility_elements:
        if e in element_lower:
            return "accessibility"

    return "general"


def _format_requirement_value(req: Requirement) -> str:
    """Format requirement value for display."""
    if req.min_value and req.max_value:
        return f"{req.min_value} - {req.max_value} {req.unit or ''}"
    elif req.min_value:
        return f"≥ {req.min_value} {req.unit or ''}"
    elif req.max_value:
        return f"≤ {req.max_value} {req.unit or ''}"
    elif req.exact_value:
        return f"{req.exact_value} {req.unit or ''}"
    return "See code"


def _perform_check(req: Requirement, extracted: ExtractedData) -> dict:
    """
    Perform a single compliance check.
    Returns {"status": str, "message": str}
    """
    # Get the value to check
    if extracted.is_verified and extracted.verified_value:
        try:
            value = float(extracted.verified_value)
        except ValueError:
            value = None
            text_value = extracted.verified_value
    else:
        value = float(extracted.value_numeric) if extracted.value_numeric else None
        text_value = extracted.value_raw

    # If value wasn't verified, mark as needs_review
    if not extracted.is_verified:
        return {
            "status": "needs_review",
            "message": f"Extracted value '{extracted.value_raw}' requires verification before compliance determination"
        }

    # Numeric comparisons
    if value is not None:
        if req.min_value and value < float(req.min_value):
            return {
                "status": "fail",
                "message": f"Value {value} {req.unit or ''} is below minimum {req.min_value} {req.unit or ''}"
            }
        if req.max_value and value > float(req.max_value):
            return {
                "status": "fail",
                "message": f"Value {value} {req.unit or ''} exceeds maximum {req.max_value} {req.unit or ''}"
            }
        return {
            "status": "pass",
            "message": f"Value {value} {req.unit or ''} meets requirement"
        }

    # Exact value comparison
    if req.exact_value and text_value:
        if text_value.lower() == req.exact_value.lower():
            return {"status": "pass", "message": "Value matches requirement"}
        else:
            return {"status": "fail", "message": f"Expected '{req.exact_value}', found '{text_value}'"}

    return {
        "status": "needs_review",
        "message": "Could not perform automated check. Manual review required."
    }


@router.get("/projects/{project_id}/checks", response_model=List[ComplianceCheckResponse])
async def get_project_checks(
    project_id: UUID,
    category: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all compliance checks for a project.
    """
    query = db.query(ComplianceCheck).filter(ComplianceCheck.project_id == project_id)

    if category:
        query = query.filter(ComplianceCheck.check_category == category)
    if status:
        query = query.filter(ComplianceCheck.status == status)

    return query.all()
