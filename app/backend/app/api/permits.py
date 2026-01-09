"""
Permit Workflow API - Calgary Building Code Expert System.

This module provides endpoints for:
- Creating and managing Development Permit (DP) and Building Permit (BP) applications
- Submitting and tracking documents for review
- Tracking application status through the approval workflow
- Recording review comments and deficiencies
- SDAB appeal workflow tracking

Note: Authentication is not implemented in this module - it will be handled separately.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from ..database import get_db
from ..schemas.permits import (
    # Enums
    PermitType, ApplicationStatus, DocumentStatus, DeficiencyStatus,
    DeficiencyPriority, AppealStatus, AppealType,
    # Permit Application
    PermitApplicationCreate, PermitApplicationUpdate, PermitApplicationResponse,
    PermitApplicationSummary,
    # Documents
    PermitDocumentUpload, PermitDocumentResponse, DocumentReviewUpdate,
    # Review
    ReviewCommentCreate, ReviewCommentResponse,
    DeficiencyCreate, DeficiencyResponse, DeficiencyUpdate,
    # Appeals
    SDABAppealCreate, SDABAppealUpdate, SDABAppealResponse,
    # Status
    StatusUpdateCreate, ApplicationTimeline, TimelineEvent,
    # Search
    PermitSearchFilters, PermitSearchResponse,
    # Statistics
    PermitStatistics,
    # Other
    ContactInfo,
)

router = APIRouter()

# --- In-Memory Storage ---
# Note: In production, these would be database tables.
# For now, we use in-memory storage to demonstrate the API.

_permit_applications: Dict[str, Dict[str, Any]] = {}
_permit_documents: Dict[str, Dict[str, Any]] = {}
_review_comments: Dict[str, Dict[str, Any]] = {}
_deficiencies: Dict[str, Dict[str, Any]] = {}
_sdab_appeals: Dict[str, Dict[str, Any]] = {}
_timeline_events: Dict[str, List[Dict[str, Any]]] = {}

# Application counter for generating application numbers
_application_counter = {"DP": 1000, "BP": 1000}


def _generate_application_number(permit_type: PermitType) -> str:
    """Generate a unique application number."""
    prefix = permit_type.value
    year = datetime.now().year
    _application_counter[prefix] = _application_counter.get(prefix, 1000) + 1
    return f"{prefix}{year}-{_application_counter[prefix]:05d}"


def _add_timeline_event(
    application_id: str,
    event_type: str,
    description: str,
    user: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Add an event to the application timeline."""
    if application_id not in _timeline_events:
        _timeline_events[application_id] = []

    _timeline_events[application_id].append({
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "description": description,
        "user": user,
        "details": details
    })


def _calculate_permit_fee(permit_type: PermitType, estimated_value: Optional[float]) -> float:
    """Calculate estimated permit fee based on type and construction value."""
    if permit_type == PermitType.DEVELOPMENT_PERMIT:
        # Base DP fee
        base_fee = 300.0
        # Additional fees based on project value
        if estimated_value:
            if estimated_value < 100000:
                return base_fee
            elif estimated_value < 500000:
                return base_fee + 200.0
            elif estimated_value < 1000000:
                return base_fee + 500.0
            else:
                return base_fee + 1000.0
        return base_fee

    elif permit_type == PermitType.BUILDING_PERMIT:
        # BP fee is typically based on construction value
        base_fee = 150.0
        if estimated_value:
            # $12 per $1000 of construction value (typical rate)
            return base_fee + (estimated_value / 1000) * 12
        return base_fee

    else:
        # Trade permits
        return 100.0


# --- Permit Application Endpoints ---

@router.post("/applications", response_model=PermitApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_permit_application(
    application: PermitApplicationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new permit application (Development Permit or Building Permit).

    The application starts in 'draft' status and can be edited before submission.

    For Building Permits, if a Development Permit is required, the DP should be
    approved or in progress before the BP application is submitted.
    """
    app_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # Generate application number
    app_number = _generate_application_number(application.permit_type)

    # Calculate estimated fee
    permit_fee = _calculate_permit_fee(
        application.permit_type,
        application.estimated_value
    )

    # Create application record
    app_data = {
        "id": app_id,
        "application_number": app_number,
        "permit_type": application.permit_type.value,
        "status": ApplicationStatus.DRAFT.value,

        # Basic info
        "project_name": application.project_name,
        "description": application.description,
        "address": application.address,
        "parcel_id": str(application.parcel_id) if application.parcel_id else None,
        "legal_description": application.legal_description,

        # Project details
        "project_type": application.project_type,
        "estimated_value": application.estimated_value,
        "classification": application.classification,
        "occupancy_group": application.occupancy_group,
        "building_area_sqm": application.building_area_sqm,
        "building_height_storeys": application.building_height_storeys,
        "dwelling_units": application.dwelling_units,

        # DP specific
        "proposed_use": application.proposed_use,
        "relaxations_requested": application.relaxations_requested,

        # Contacts (stored as dicts)
        "applicant": application.applicant.model_dump() if application.applicant else None,
        "agent": application.agent.model_dump() if application.agent else None,
        "contractor": application.contractor.model_dump() if application.contractor else None,

        # Timestamps
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "submitted_at": None,

        # Review info
        "assigned_reviewer": None,
        "review_started_at": None,

        # Decision
        "decision_date": None,
        "decision_notes": None,
        "conditions": None,

        # Fees
        "application_fee": 50.0,  # Base application fee
        "permit_fee": permit_fee,
        "fees_paid": False,

        # Related entities
        "related_dp_id": None,
        "project_id": None,

        # Statistics (computed)
        "documents_count": 0,
        "deficiencies_count": 0,
        "open_deficiencies_count": 0,
    }

    _permit_applications[app_id] = app_data

    # Add timeline event
    _add_timeline_event(
        app_id,
        "application_created",
        f"Permit application {app_number} created",
        details={"permit_type": application.permit_type.value}
    )

    return _format_application_response(app_data)


@router.get("/applications", response_model=PermitSearchResponse)
async def list_permit_applications(
    permit_type: Optional[PermitType] = Query(None, description="Filter by permit type"),
    status: Optional[ApplicationStatus] = Query(None, description="Filter by status"),
    address: Optional[str] = Query(None, description="Filter by address (partial match)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    List permit applications with optional filtering.

    Returns paginated results with summary information for each application.
    """
    # Filter applications
    results = []
    for app_id, app_data in _permit_applications.items():
        # Apply filters
        if permit_type and app_data["permit_type"] != permit_type.value:
            continue
        if status and app_data["status"] != status.value:
            continue
        if address and address.lower() not in app_data["address"].lower():
            continue

        results.append(app_data)

    # Sort by created_at descending
    results.sort(key=lambda x: x["created_at"], reverse=True)

    # Paginate
    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    page_results = results[start:end]

    # Convert to summary format
    summaries = [
        PermitApplicationSummary(
            id=uuid.UUID(app["id"]),
            application_number=app["application_number"],
            permit_type=PermitType(app["permit_type"]),
            project_name=app["project_name"],
            address=app["address"],
            status=ApplicationStatus(app["status"]),
            submitted_at=datetime.fromisoformat(app["submitted_at"]) if app["submitted_at"] else None,
            created_at=datetime.fromisoformat(app["created_at"]),
        )
        for app in page_results
    ]

    return PermitSearchResponse(
        total=total,
        page=page,
        page_size=page_size,
        results=summaries
    )


@router.get("/applications/{application_id}", response_model=PermitApplicationResponse)
async def get_permit_application(
    application_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific permit application.

    Includes all application details, current status, assigned reviewer,
    and document/deficiency counts.
    """
    if application_id not in _permit_applications:
        raise HTTPException(
            status_code=404,
            detail=f"Permit application {application_id} not found"
        )

    app_data = _permit_applications[application_id]

    # Update computed fields
    app_data["documents_count"] = len([
        d for d in _permit_documents.values()
        if d["permit_application_id"] == application_id
    ])
    app_data["deficiencies_count"] = len([
        d for d in _deficiencies.values()
        if d["permit_application_id"] == application_id
    ])
    app_data["open_deficiencies_count"] = len([
        d for d in _deficiencies.values()
        if d["permit_application_id"] == application_id and d["status"] == DeficiencyStatus.OPEN.value
    ])

    return _format_application_response(app_data)


@router.patch("/applications/{application_id}", response_model=PermitApplicationResponse)
async def update_permit_application(
    application_id: str,
    update: PermitApplicationUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a permit application.

    Only applications in 'draft' or 'information_requested' status can be fully edited.
    Other applications can only have limited fields updated.
    """
    if application_id not in _permit_applications:
        raise HTTPException(
            status_code=404,
            detail=f"Permit application {application_id} not found"
        )

    app_data = _permit_applications[application_id]
    current_status = app_data["status"]

    # Check if editable
    editable_statuses = [
        ApplicationStatus.DRAFT.value,
        ApplicationStatus.INFORMATION_REQUESTED.value,
        ApplicationStatus.REVISION_REQUIRED.value
    ]

    update_dict = update.model_dump(exclude_unset=True)

    if current_status not in editable_statuses:
        # Only allow status updates for non-editable applications
        allowed_fields = {"status"}
        for field in update_dict:
            if field not in allowed_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot modify {field} for application in {current_status} status"
                )

    # Apply updates
    for field, value in update_dict.items():
        if field == "applicant" and value:
            app_data["applicant"] = value if isinstance(value, dict) else value.model_dump()
        elif field == "agent" and value:
            app_data["agent"] = value if isinstance(value, dict) else value.model_dump()
        elif field == "contractor" and value:
            app_data["contractor"] = value if isinstance(value, dict) else value.model_dump()
        elif field == "status" and value:
            app_data["status"] = value.value if hasattr(value, "value") else value
        else:
            app_data[field] = value

    app_data["updated_at"] = datetime.utcnow().isoformat()

    # Add timeline event for significant changes
    if "status" in update_dict:
        _add_timeline_event(
            application_id,
            "status_changed",
            f"Status changed to {app_data['status']}",
            details={"previous_status": current_status, "new_status": app_data["status"]}
        )

    return _format_application_response(app_data)


@router.post("/applications/{application_id}/submit", response_model=PermitApplicationResponse)
async def submit_permit_application(
    application_id: str,
    db: Session = Depends(get_db)
):
    """
    Submit a permit application for review.

    Changes status from 'draft' to 'submitted'. The application will then
    be assigned to a reviewer and enter the 'under_review' status.

    Prerequisites:
    - Application must be in 'draft' status
    - Required documents should be uploaded (warning issued if missing)
    """
    if application_id not in _permit_applications:
        raise HTTPException(
            status_code=404,
            detail=f"Permit application {application_id} not found"
        )

    app_data = _permit_applications[application_id]

    if app_data["status"] != ApplicationStatus.DRAFT.value:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit application in {app_data['status']} status. Must be 'draft'."
        )

    # Check for required documents (basic check)
    doc_count = len([
        d for d in _permit_documents.values()
        if d["permit_application_id"] == application_id
    ])

    warnings = []
    if doc_count == 0:
        warnings.append("No documents have been uploaded. Consider uploading required documents.")

    # Update status
    now = datetime.utcnow()
    app_data["status"] = ApplicationStatus.SUBMITTED.value
    app_data["submitted_at"] = now.isoformat()
    app_data["updated_at"] = now.isoformat()

    _add_timeline_event(
        application_id,
        "application_submitted",
        f"Application {app_data['application_number']} submitted for review",
        details={"warnings": warnings} if warnings else None
    )

    return _format_application_response(app_data)


@router.post("/applications/{application_id}/status", response_model=PermitApplicationResponse)
async def update_application_status(
    application_id: str,
    status_update: StatusUpdateCreate,
    db: Session = Depends(get_db)
):
    """
    Update the status of a permit application.

    Valid status transitions:
    - submitted -> under_review (when assigned to reviewer)
    - under_review -> information_requested, revision_required, approved, refused
    - information_requested/revision_required -> under_review (when resubmitted)
    - approved -> expired (if permit not obtained within time limit)
    - refused -> appealed (if SDAB appeal is filed)
    """
    if application_id not in _permit_applications:
        raise HTTPException(
            status_code=404,
            detail=f"Permit application {application_id} not found"
        )

    app_data = _permit_applications[application_id]
    old_status = app_data["status"]
    new_status = status_update.new_status.value

    # Validate status transition
    valid_transitions = {
        ApplicationStatus.DRAFT.value: [ApplicationStatus.SUBMITTED.value, ApplicationStatus.WITHDRAWN.value],
        ApplicationStatus.SUBMITTED.value: [ApplicationStatus.UNDER_REVIEW.value, ApplicationStatus.WITHDRAWN.value],
        ApplicationStatus.UNDER_REVIEW.value: [
            ApplicationStatus.INFORMATION_REQUESTED.value,
            ApplicationStatus.REVISION_REQUIRED.value,
            ApplicationStatus.APPROVED.value,
            ApplicationStatus.APPROVED_WITH_CONDITIONS.value,
            ApplicationStatus.REFUSED.value,
            ApplicationStatus.WITHDRAWN.value
        ],
        ApplicationStatus.INFORMATION_REQUESTED.value: [ApplicationStatus.UNDER_REVIEW.value, ApplicationStatus.WITHDRAWN.value],
        ApplicationStatus.REVISION_REQUIRED.value: [ApplicationStatus.UNDER_REVIEW.value, ApplicationStatus.WITHDRAWN.value],
        ApplicationStatus.APPROVED.value: [ApplicationStatus.EXPIRED.value],
        ApplicationStatus.APPROVED_WITH_CONDITIONS.value: [ApplicationStatus.EXPIRED.value],
        ApplicationStatus.REFUSED.value: [ApplicationStatus.APPEALED.value],
        ApplicationStatus.APPEALED.value: [ApplicationStatus.APPROVED.value, ApplicationStatus.REFUSED.value],
    }

    allowed = valid_transitions.get(old_status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {old_status} to {new_status}. Allowed: {allowed}"
        )

    now = datetime.utcnow()
    app_data["status"] = new_status
    app_data["updated_at"] = now.isoformat()

    # Handle specific status changes
    if new_status == ApplicationStatus.UNDER_REVIEW.value:
        app_data["review_started_at"] = now.isoformat()
    elif new_status in [ApplicationStatus.APPROVED.value, ApplicationStatus.APPROVED_WITH_CONDITIONS.value, ApplicationStatus.REFUSED.value]:
        app_data["decision_date"] = now.isoformat()
        app_data["decision_notes"] = status_update.notes

    _add_timeline_event(
        application_id,
        "status_changed",
        f"Status changed from {old_status} to {new_status}",
        details={"notes": status_update.notes} if status_update.notes else None
    )

    return _format_application_response(app_data)


@router.get("/applications/{application_id}/timeline", response_model=ApplicationTimeline)
async def get_application_timeline(
    application_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the complete timeline of events for a permit application.

    Includes all status changes, document uploads, review comments,
    and other significant events.
    """
    if application_id not in _permit_applications:
        raise HTTPException(
            status_code=404,
            detail=f"Permit application {application_id} not found"
        )

    app_data = _permit_applications[application_id]
    events = _timeline_events.get(application_id, [])

    # Calculate days in review
    days_in_review = None
    if app_data.get("submitted_at"):
        submitted = datetime.fromisoformat(app_data["submitted_at"])
        if app_data["status"] in [ApplicationStatus.APPROVED.value, ApplicationStatus.REFUSED.value]:
            if app_data.get("decision_date"):
                decision = datetime.fromisoformat(app_data["decision_date"])
                days_in_review = (decision - submitted).days
        else:
            days_in_review = (datetime.utcnow() - submitted).days

    # Convert events to schema format
    timeline_events = [
        TimelineEvent(
            timestamp=datetime.fromisoformat(e["timestamp"]),
            event_type=e["event_type"],
            description=e["description"],
            user=e.get("user"),
            details=e.get("details")
        )
        for e in events
    ]

    return ApplicationTimeline(
        permit_application_id=uuid.UUID(application_id),
        events=timeline_events,
        current_status=ApplicationStatus(app_data["status"]),
        days_in_review=days_in_review,
        estimated_completion_date=None  # Would be calculated based on historical data
    )


# --- Document Endpoints ---

@router.post("/applications/{application_id}/documents", response_model=PermitDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    application_id: str,
    document_type: str = Query(..., description="Document type: site_plan, floor_plan, elevation, etc."),
    title: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document to a permit application.

    Supported document types:
    - site_plan: Site plan showing property boundaries, setbacks, structures
    - floor_plan: Floor plans for each level
    - elevation: Building elevations (front, rear, sides)
    - section: Building sections
    - structural: Structural drawings and calculations
    - mechanical: Mechanical/HVAC drawings
    - electrical: Electrical drawings
    - energy_compliance: Energy compliance documentation
    - survey: Survey or real property report
    - title: Certificate of title
    - other: Other supporting documents
    """
    if application_id not in _permit_applications:
        raise HTTPException(
            status_code=404,
            detail=f"Permit application {application_id} not found"
        )

    doc_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # In production, file would be saved to storage
    file_path = f"/uploads/permits/{application_id}/{doc_id}_{file.filename}"

    doc_data = {
        "id": doc_id,
        "permit_application_id": application_id,
        "document_type": document_type,
        "title": title or file.filename,
        "description": description,
        "version": 1,
        "is_revision": False,
        "replaces_document_id": None,
        "filename": file.filename,
        "file_path": file_path,
        "file_type": file.content_type,
        "file_size_bytes": 0,  # Would be calculated from actual file
        "status": DocumentStatus.PENDING.value,
        "uploaded_at": now.isoformat(),
        "reviewed_at": None,
        "reviewer": None,
        "review_notes": None,
    }

    _permit_documents[doc_id] = doc_data

    _add_timeline_event(
        application_id,
        "document_uploaded",
        f"Document uploaded: {file.filename}",
        details={"document_type": document_type, "document_id": doc_id}
    )

    return _format_document_response(doc_data)


@router.get("/applications/{application_id}/documents", response_model=List[PermitDocumentResponse])
async def list_application_documents(
    application_id: str,
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    status: Optional[DocumentStatus] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """
    List all documents for a permit application.

    Optionally filter by document type or review status.
    """
    if application_id not in _permit_applications:
        raise HTTPException(
            status_code=404,
            detail=f"Permit application {application_id} not found"
        )

    docs = []
    for doc_id, doc_data in _permit_documents.items():
        if doc_data["permit_application_id"] != application_id:
            continue
        if document_type and doc_data["document_type"] != document_type:
            continue
        if status and doc_data["status"] != status.value:
            continue
        docs.append(doc_data)

    # Sort by uploaded_at descending
    docs.sort(key=lambda x: x["uploaded_at"], reverse=True)

    return [_format_document_response(d) for d in docs]


@router.patch("/documents/{document_id}/review", response_model=PermitDocumentResponse)
async def review_document(
    document_id: str,
    review: DocumentReviewUpdate,
    db: Session = Depends(get_db)
):
    """
    Update the review status of a document.

    Reviewers use this to accept, reject, or request revisions for documents.
    """
    if document_id not in _permit_documents:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found"
        )

    doc_data = _permit_documents[document_id]
    now = datetime.utcnow()

    doc_data["status"] = review.status.value
    doc_data["review_notes"] = review.review_notes
    doc_data["reviewer"] = review.reviewer
    doc_data["reviewed_at"] = now.isoformat()

    _add_timeline_event(
        doc_data["permit_application_id"],
        "document_reviewed",
        f"Document reviewed: {doc_data['filename']} - {review.status.value}",
        user=review.reviewer,
        details={"document_id": document_id, "status": review.status.value}
    )

    return _format_document_response(doc_data)


# --- Review Comments Endpoints ---

@router.post("/applications/{application_id}/comments", response_model=ReviewCommentResponse, status_code=status.HTTP_201_CREATED)
async def create_review_comment(
    application_id: str,
    comment: ReviewCommentCreate,
    reviewer: Optional[str] = Query(None, description="Name of the reviewer"),
    db: Session = Depends(get_db)
):
    """
    Add a review comment to a permit application.

    Review comments can be general or linked to specific documents and pages.
    Comments can optionally require a response from the applicant.
    """
    if application_id not in _permit_applications:
        raise HTTPException(
            status_code=404,
            detail=f"Permit application {application_id} not found"
        )

    comment_id = str(uuid.uuid4())
    now = datetime.utcnow()

    comment_data = {
        "id": comment_id,
        "permit_application_id": application_id,
        "category": comment.category,
        "comment": comment.comment,
        "code_reference": comment.code_reference,
        "document_id": str(comment.document_id) if comment.document_id else None,
        "page_number": comment.page_number,
        "location_description": comment.location_description,
        "requires_response": comment.requires_response,
        "reviewer": reviewer,
        "created_at": now.isoformat(),
        "response": None,
        "responded_at": None,
        "is_resolved": False,
        "resolved_at": None,
    }

    _review_comments[comment_id] = comment_data

    _add_timeline_event(
        application_id,
        "comment_added",
        f"Review comment added: {comment.category}",
        user=reviewer,
        details={"comment_id": comment_id, "requires_response": comment.requires_response}
    )

    return _format_comment_response(comment_data)


@router.get("/applications/{application_id}/comments", response_model=List[ReviewCommentResponse])
async def list_review_comments(
    application_id: str,
    category: Optional[str] = Query(None, description="Filter by category"),
    unresolved_only: bool = Query(False, description="Show only unresolved comments"),
    db: Session = Depends(get_db)
):
    """
    List all review comments for a permit application.
    """
    if application_id not in _permit_applications:
        raise HTTPException(
            status_code=404,
            detail=f"Permit application {application_id} not found"
        )

    comments = []
    for comment_id, comment_data in _review_comments.items():
        if comment_data["permit_application_id"] != application_id:
            continue
        if category and comment_data["category"] != category:
            continue
        if unresolved_only and comment_data["is_resolved"]:
            continue
        comments.append(comment_data)

    comments.sort(key=lambda x: x["created_at"], reverse=True)

    return [_format_comment_response(c) for c in comments]


# --- Deficiency Endpoints ---

@router.post("/applications/{application_id}/deficiencies", response_model=DeficiencyResponse, status_code=status.HTTP_201_CREATED)
async def create_deficiency(
    application_id: str,
    deficiency: DeficiencyCreate,
    created_by: Optional[str] = Query(None, description="Name of the person creating the deficiency"),
    db: Session = Depends(get_db)
):
    """
    Record a deficiency in a permit application.

    Deficiencies are formal issues that must be addressed before the application
    can be approved. They are more serious than review comments.

    Priority levels:
    - critical: Must be addressed immediately, blocks approval
    - high: Must be addressed before approval
    - medium: Should be addressed, may be approved with conditions
    - low: Minor issue, informational
    """
    if application_id not in _permit_applications:
        raise HTTPException(
            status_code=404,
            detail=f"Permit application {application_id} not found"
        )

    deficiency_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # Calculate deadline if specified
    deadline = None
    if deficiency.deadline_days:
        deadline = (now + timedelta(days=deficiency.deadline_days)).isoformat()

    deficiency_data = {
        "id": deficiency_id,
        "permit_application_id": application_id,
        "category": deficiency.category,
        "title": deficiency.title,
        "description": deficiency.description,
        "priority": deficiency.priority.value,
        "code_reference": deficiency.code_reference,
        "required_action": deficiency.required_action,
        "deadline_days": deficiency.deadline_days,
        "document_id": str(deficiency.document_id) if deficiency.document_id else None,
        "status": DeficiencyStatus.OPEN.value,
        "created_at": now.isoformat(),
        "created_by": created_by,
        "deadline": deadline,
        "addressed_at": None,
        "addressed_notes": None,
        "resolved_at": None,
        "resolved_by": None,
        "resolution_notes": None,
    }

    _deficiencies[deficiency_id] = deficiency_data

    _add_timeline_event(
        application_id,
        "deficiency_created",
        f"Deficiency recorded: {deficiency.title}",
        user=created_by,
        details={
            "deficiency_id": deficiency_id,
            "priority": deficiency.priority.value,
            "category": deficiency.category
        }
    )

    return _format_deficiency_response(deficiency_data)


@router.get("/applications/{application_id}/deficiencies", response_model=List[DeficiencyResponse])
async def list_deficiencies(
    application_id: str,
    status: Optional[DeficiencyStatus] = Query(None, description="Filter by status"),
    priority: Optional[DeficiencyPriority] = Query(None, description="Filter by priority"),
    db: Session = Depends(get_db)
):
    """
    List all deficiencies for a permit application.
    """
    if application_id not in _permit_applications:
        raise HTTPException(
            status_code=404,
            detail=f"Permit application {application_id} not found"
        )

    deficiencies = []
    for def_id, def_data in _deficiencies.items():
        if def_data["permit_application_id"] != application_id:
            continue
        if status and def_data["status"] != status.value:
            continue
        if priority and def_data["priority"] != priority.value:
            continue
        deficiencies.append(def_data)

    # Sort by priority (critical first) then created_at
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    deficiencies.sort(key=lambda x: (priority_order.get(x["priority"], 4), x["created_at"]))

    return [_format_deficiency_response(d) for d in deficiencies]


@router.patch("/deficiencies/{deficiency_id}", response_model=DeficiencyResponse)
async def update_deficiency(
    deficiency_id: str,
    update: DeficiencyUpdate,
    updated_by: Optional[str] = Query(None, description="Name of person updating"),
    db: Session = Depends(get_db)
):
    """
    Update a deficiency status or add resolution notes.

    Status transitions:
    - open -> addressed (applicant has responded)
    - addressed -> resolved (reviewer confirms resolution)
    - open -> waived (reviewer waives the requirement)
    """
    if deficiency_id not in _deficiencies:
        raise HTTPException(
            status_code=404,
            detail=f"Deficiency {deficiency_id} not found"
        )

    def_data = _deficiencies[deficiency_id]
    now = datetime.utcnow()

    if update.status:
        old_status = def_data["status"]
        def_data["status"] = update.status.value

        if update.status == DeficiencyStatus.ADDRESSED:
            def_data["addressed_at"] = now.isoformat()
            def_data["addressed_notes"] = update.addressed_notes
        elif update.status == DeficiencyStatus.RESOLVED:
            def_data["resolved_at"] = now.isoformat()
            def_data["resolved_by"] = updated_by
            def_data["resolution_notes"] = update.resolution_notes
        elif update.status == DeficiencyStatus.WAIVED:
            def_data["resolved_at"] = now.isoformat()
            def_data["resolved_by"] = updated_by
            def_data["resolution_notes"] = update.resolution_notes or "Requirement waived"

        _add_timeline_event(
            def_data["permit_application_id"],
            "deficiency_updated",
            f"Deficiency status changed: {old_status} -> {update.status.value}",
            user=updated_by,
            details={"deficiency_id": deficiency_id}
        )

    return _format_deficiency_response(def_data)


# --- SDAB Appeal Endpoints ---

@router.post("/appeals", response_model=SDABAppealResponse, status_code=status.HTTP_201_CREATED)
async def file_sdab_appeal(
    appeal: SDABAppealCreate,
    db: Session = Depends(get_db)
):
    """
    File an SDAB appeal for a refused permit application.

    SDAB appeals must typically be filed within 21 days of the decision.

    Appeal types:
    - appeal_of_refusal: Applicant appeals a refused application
    - appeal_of_approval: Third party appeals an approved application
    - appeal_of_conditions: Appeal specific conditions of approval
    """
    app_id = str(appeal.permit_application_id)

    if app_id not in _permit_applications:
        raise HTTPException(
            status_code=404,
            detail=f"Permit application {app_id} not found"
        )

    app_data = _permit_applications[app_id]

    # Verify application status allows appeal
    if appeal.appeal_type == AppealType.APPEAL_OF_REFUSAL:
        if app_data["status"] != ApplicationStatus.REFUSED.value:
            raise HTTPException(
                status_code=400,
                detail="Can only appeal refused applications"
            )
    elif appeal.appeal_type == AppealType.APPEAL_OF_APPROVAL:
        if app_data["status"] not in [ApplicationStatus.APPROVED.value, ApplicationStatus.APPROVED_WITH_CONDITIONS.value]:
            raise HTTPException(
                status_code=400,
                detail="Can only appeal approved applications"
            )

    appeal_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # Calculate filing deadline (21 days from decision)
    deadline = None
    if app_data.get("decision_date"):
        decision_date = datetime.fromisoformat(app_data["decision_date"])
        deadline = (decision_date + timedelta(days=21)).isoformat()

    appeal_data = {
        "id": appeal_id,
        "appeal_number": f"SDAB-{now.year}-{len(_sdab_appeals) + 1:04d}",
        "permit_application_id": app_id,
        "appeal_type": appeal.appeal_type.value,
        "status": AppealStatus.FILED.value,
        "grounds_for_appeal": appeal.grounds_for_appeal,
        "requested_relief": appeal.requested_relief,
        "supporting_arguments": appeal.supporting_arguments,
        "appellant": appeal.appellant.model_dump(),
        "filed_at": now.isoformat(),
        "deadline_to_file": deadline,
        "hearing_date": None,
        "hearing_location": None,
        "hearing_notes": None,
        "decision_date": None,
        "decision": None,
        "decision_summary": None,
        "conditions": None,
        "original_decision": app_data["status"],
        "original_decision_date": app_data.get("decision_date"),
    }

    _sdab_appeals[appeal_id] = appeal_data

    # Update application status
    app_data["status"] = ApplicationStatus.APPEALED.value
    app_data["updated_at"] = now.isoformat()

    _add_timeline_event(
        app_id,
        "appeal_filed",
        f"SDAB appeal filed: {appeal_data['appeal_number']}",
        details={
            "appeal_id": appeal_id,
            "appeal_type": appeal.appeal_type.value,
            "grounds": appeal.grounds_for_appeal[:100] + "..." if len(appeal.grounds_for_appeal) > 100 else appeal.grounds_for_appeal
        }
    )

    return _format_appeal_response(appeal_data)


@router.get("/appeals/{appeal_id}", response_model=SDABAppealResponse)
async def get_sdab_appeal(
    appeal_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about an SDAB appeal.
    """
    if appeal_id not in _sdab_appeals:
        raise HTTPException(
            status_code=404,
            detail=f"SDAB appeal {appeal_id} not found"
        )

    return _format_appeal_response(_sdab_appeals[appeal_id])


@router.get("/applications/{application_id}/appeals", response_model=List[SDABAppealResponse])
async def list_application_appeals(
    application_id: str,
    db: Session = Depends(get_db)
):
    """
    List all SDAB appeals for a permit application.
    """
    if application_id not in _permit_applications:
        raise HTTPException(
            status_code=404,
            detail=f"Permit application {application_id} not found"
        )

    appeals = [
        _format_appeal_response(a)
        for a in _sdab_appeals.values()
        if a["permit_application_id"] == application_id
    ]

    return appeals


@router.patch("/appeals/{appeal_id}", response_model=SDABAppealResponse)
async def update_sdab_appeal(
    appeal_id: str,
    update: SDABAppealUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an SDAB appeal.

    Status transitions:
    - filed -> scheduled (hearing date set)
    - scheduled -> hearing_completed
    - hearing_completed -> allowed, denied, allowed_in_part, struck
    - Any status -> withdrawn
    """
    if appeal_id not in _sdab_appeals:
        raise HTTPException(
            status_code=404,
            detail=f"SDAB appeal {appeal_id} not found"
        )

    appeal_data = _sdab_appeals[appeal_id]
    now = datetime.utcnow()

    update_dict = update.model_dump(exclude_unset=True)

    for field, value in update_dict.items():
        if field == "status" and value:
            old_status = appeal_data["status"]
            new_status = value.value if hasattr(value, "value") else value
            appeal_data["status"] = new_status

            # Handle status-specific updates
            if new_status in [AppealStatus.ALLOWED.value, AppealStatus.DENIED.value,
                             AppealStatus.ALLOWED_IN_PART.value]:
                appeal_data["decision_date"] = now.isoformat()
                appeal_data["decision"] = new_status

                # Update original application based on appeal outcome
                app_id = appeal_data["permit_application_id"]
                if app_id in _permit_applications:
                    if new_status == AppealStatus.ALLOWED.value:
                        _permit_applications[app_id]["status"] = ApplicationStatus.APPROVED.value
                    elif new_status == AppealStatus.DENIED.value:
                        _permit_applications[app_id]["status"] = ApplicationStatus.REFUSED.value
                    # ALLOWED_IN_PART might need manual handling
                    _permit_applications[app_id]["updated_at"] = now.isoformat()
        else:
            appeal_data[field] = value

    return _format_appeal_response(appeal_data)


# --- Statistics Endpoint ---

@router.get("/statistics", response_model=PermitStatistics)
async def get_permit_statistics(
    db: Session = Depends(get_db)
):
    """
    Get statistics about permit applications.

    Includes counts by type and status, average review times,
    approval rates, and common deficiency categories.
    """
    total = len(_permit_applications)

    # Count by type
    by_type = {}
    for app in _permit_applications.values():
        permit_type = app["permit_type"]
        by_type[permit_type] = by_type.get(permit_type, 0) + 1

    # Count by status
    by_status = {}
    for app in _permit_applications.values():
        status = app["status"]
        by_status[status] = by_status.get(status, 0) + 1

    # Calculate average review days for completed applications
    review_days = []
    for app in _permit_applications.values():
        if app.get("submitted_at") and app.get("decision_date"):
            submitted = datetime.fromisoformat(app["submitted_at"])
            decision = datetime.fromisoformat(app["decision_date"])
            review_days.append((decision - submitted).days)

    avg_review_days = sum(review_days) / len(review_days) if review_days else None

    # Calculate approval rate
    decided = len([a for a in _permit_applications.values()
                   if a["status"] in [ApplicationStatus.APPROVED.value,
                                      ApplicationStatus.APPROVED_WITH_CONDITIONS.value,
                                      ApplicationStatus.REFUSED.value]])
    approved = len([a for a in _permit_applications.values()
                    if a["status"] in [ApplicationStatus.APPROVED.value,
                                       ApplicationStatus.APPROVED_WITH_CONDITIONS.value]])
    approval_rate = (approved / decided * 100) if decided > 0 else None

    # Common deficiencies
    deficiency_counts = {}
    for d in _deficiencies.values():
        cat = d["category"]
        deficiency_counts[cat] = deficiency_counts.get(cat, 0) + 1

    common_deficiencies = [
        {"category": cat, "count": count}
        for cat, count in sorted(deficiency_counts.items(), key=lambda x: -x[1])[:10]
    ]

    return PermitStatistics(
        total_applications=total,
        by_type=by_type,
        by_status=by_status,
        average_review_days=avg_review_days,
        approval_rate=approval_rate,
        common_deficiencies=common_deficiencies
    )


# --- Helper Functions ---

def _format_application_response(app_data: Dict[str, Any]) -> PermitApplicationResponse:
    """Convert application data dict to response schema."""
    return PermitApplicationResponse(
        id=uuid.UUID(app_data["id"]),
        application_number=app_data.get("application_number"),
        permit_type=PermitType(app_data["permit_type"]),
        status=ApplicationStatus(app_data["status"]),
        project_name=app_data.get("project_name"),
        description=app_data.get("description"),
        address=app_data["address"],
        parcel_id=uuid.UUID(app_data["parcel_id"]) if app_data.get("parcel_id") else None,
        legal_description=app_data.get("legal_description"),
        project_type=app_data.get("project_type"),
        estimated_value=app_data.get("estimated_value"),
        classification=app_data.get("classification"),
        occupancy_group=app_data.get("occupancy_group"),
        building_area_sqm=app_data.get("building_area_sqm"),
        building_height_storeys=app_data.get("building_height_storeys"),
        dwelling_units=app_data.get("dwelling_units"),
        proposed_use=app_data.get("proposed_use"),
        relaxations_requested=app_data.get("relaxations_requested"),
        applicant=ContactInfo(**app_data["applicant"]) if app_data.get("applicant") else None,
        agent=ContactInfo(**app_data["agent"]) if app_data.get("agent") else None,
        contractor=ContactInfo(**app_data["contractor"]) if app_data.get("contractor") else None,
        created_at=datetime.fromisoformat(app_data["created_at"]),
        updated_at=datetime.fromisoformat(app_data["updated_at"]),
        submitted_at=datetime.fromisoformat(app_data["submitted_at"]) if app_data.get("submitted_at") else None,
        assigned_reviewer=app_data.get("assigned_reviewer"),
        review_started_at=datetime.fromisoformat(app_data["review_started_at"]) if app_data.get("review_started_at") else None,
        decision_date=datetime.fromisoformat(app_data["decision_date"]) if app_data.get("decision_date") else None,
        decision_notes=app_data.get("decision_notes"),
        conditions=app_data.get("conditions"),
        application_fee=app_data.get("application_fee"),
        permit_fee=app_data.get("permit_fee"),
        fees_paid=app_data.get("fees_paid", False),
        related_dp_id=uuid.UUID(app_data["related_dp_id"]) if app_data.get("related_dp_id") else None,
        project_id=uuid.UUID(app_data["project_id"]) if app_data.get("project_id") else None,
        documents_count=app_data.get("documents_count", 0),
        deficiencies_count=app_data.get("deficiencies_count", 0),
        open_deficiencies_count=app_data.get("open_deficiencies_count", 0),
    )


def _format_document_response(doc_data: Dict[str, Any]) -> PermitDocumentResponse:
    """Convert document data dict to response schema."""
    return PermitDocumentResponse(
        id=uuid.UUID(doc_data["id"]),
        permit_application_id=uuid.UUID(doc_data["permit_application_id"]),
        document_type=doc_data["document_type"],
        title=doc_data.get("title"),
        description=doc_data.get("description"),
        version=doc_data.get("version", 1),
        is_revision=doc_data.get("is_revision", False),
        replaces_document_id=uuid.UUID(doc_data["replaces_document_id"]) if doc_data.get("replaces_document_id") else None,
        filename=doc_data["filename"],
        file_path=doc_data["file_path"],
        file_type=doc_data.get("file_type"),
        file_size_bytes=doc_data.get("file_size_bytes"),
        status=DocumentStatus(doc_data["status"]),
        uploaded_at=datetime.fromisoformat(doc_data["uploaded_at"]),
        reviewed_at=datetime.fromisoformat(doc_data["reviewed_at"]) if doc_data.get("reviewed_at") else None,
        reviewer=doc_data.get("reviewer"),
        review_notes=doc_data.get("review_notes"),
    )


def _format_comment_response(comment_data: Dict[str, Any]) -> ReviewCommentResponse:
    """Convert comment data dict to response schema."""
    return ReviewCommentResponse(
        id=uuid.UUID(comment_data["id"]),
        permit_application_id=uuid.UUID(comment_data["permit_application_id"]),
        category=comment_data["category"],
        comment=comment_data["comment"],
        code_reference=comment_data.get("code_reference"),
        document_id=uuid.UUID(comment_data["document_id"]) if comment_data.get("document_id") else None,
        page_number=comment_data.get("page_number"),
        location_description=comment_data.get("location_description"),
        requires_response=comment_data.get("requires_response", False),
        reviewer=comment_data.get("reviewer"),
        created_at=datetime.fromisoformat(comment_data["created_at"]),
        response=comment_data.get("response"),
        responded_at=datetime.fromisoformat(comment_data["responded_at"]) if comment_data.get("responded_at") else None,
        is_resolved=comment_data.get("is_resolved", False),
        resolved_at=datetime.fromisoformat(comment_data["resolved_at"]) if comment_data.get("resolved_at") else None,
    )


def _format_deficiency_response(def_data: Dict[str, Any]) -> DeficiencyResponse:
    """Convert deficiency data dict to response schema."""
    return DeficiencyResponse(
        id=uuid.UUID(def_data["id"]),
        permit_application_id=uuid.UUID(def_data["permit_application_id"]),
        category=def_data["category"],
        title=def_data["title"],
        description=def_data["description"],
        priority=DeficiencyPriority(def_data["priority"]),
        code_reference=def_data.get("code_reference"),
        required_action=def_data["required_action"],
        deadline_days=def_data.get("deadline_days"),
        document_id=uuid.UUID(def_data["document_id"]) if def_data.get("document_id") else None,
        status=DeficiencyStatus(def_data["status"]),
        created_at=datetime.fromisoformat(def_data["created_at"]),
        created_by=def_data.get("created_by"),
        deadline=datetime.fromisoformat(def_data["deadline"]) if def_data.get("deadline") else None,
        addressed_at=datetime.fromisoformat(def_data["addressed_at"]) if def_data.get("addressed_at") else None,
        addressed_notes=def_data.get("addressed_notes"),
        resolved_at=datetime.fromisoformat(def_data["resolved_at"]) if def_data.get("resolved_at") else None,
        resolved_by=def_data.get("resolved_by"),
        resolution_notes=def_data.get("resolution_notes"),
    )


def _format_appeal_response(appeal_data: Dict[str, Any]) -> SDABAppealResponse:
    """Convert appeal data dict to response schema."""
    return SDABAppealResponse(
        id=uuid.UUID(appeal_data["id"]),
        appeal_number=appeal_data.get("appeal_number"),
        permit_application_id=uuid.UUID(appeal_data["permit_application_id"]),
        appeal_type=AppealType(appeal_data["appeal_type"]),
        status=AppealStatus(appeal_data["status"]),
        grounds_for_appeal=appeal_data["grounds_for_appeal"],
        requested_relief=appeal_data["requested_relief"],
        supporting_arguments=appeal_data.get("supporting_arguments"),
        appellant=ContactInfo(**appeal_data["appellant"]),
        filed_at=datetime.fromisoformat(appeal_data["filed_at"]),
        deadline_to_file=datetime.fromisoformat(appeal_data["deadline_to_file"]) if appeal_data.get("deadline_to_file") else None,
        hearing_date=datetime.fromisoformat(appeal_data["hearing_date"]) if appeal_data.get("hearing_date") else None,
        hearing_location=appeal_data.get("hearing_location"),
        hearing_notes=appeal_data.get("hearing_notes"),
        decision_date=datetime.fromisoformat(appeal_data["decision_date"]) if appeal_data.get("decision_date") else None,
        decision=appeal_data.get("decision"),
        decision_summary=appeal_data.get("decision_summary"),
        conditions=appeal_data.get("conditions"),
        original_decision=appeal_data.get("original_decision"),
        original_decision_date=datetime.fromisoformat(appeal_data["original_decision_date"]) if appeal_data.get("original_decision_date") else None,
    )
