"""
Permit Workflow API - Calgary Building Code Expert System.

This module provides endpoints for:
- Creating and managing Development Permit (DP) and Building Permit (BP) applications
- Submitting and tracking documents for review
- Tracking application status through the approval workflow
- Recording review comments and deficiencies
- SDAB appeal workflow tracking

All data is persisted to the database using SQLAlchemy models.
"""
import uuid as uuid_module
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc

from ..database import get_db
from ..models.permits import (
    PermitApplication, PermitDocument, PermitTimeline,
    PermitDeficiency, PermitReviewComment, SDABAppeal,
    PermitTypeEnum, ApplicationStatusEnum, DocumentStatusEnum,
    DeficiencyStatusEnum, DeficiencyPriorityEnum, AppealStatusEnum, AppealTypeEnum,
)
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
from ..services.document_service import document_service

router = APIRouter()


# --- Helper Functions ---

def _get_next_application_number(db: Session, permit_type: str) -> str:
    """Generate a unique application number."""
    year = datetime.now().year
    prefix = permit_type

    # Get the highest number for this type and year
    pattern = f"{prefix}{year}-%"
    last_app = db.query(PermitApplication).filter(
        PermitApplication.application_number.like(pattern)
    ).order_by(desc(PermitApplication.application_number)).first()

    if last_app and last_app.application_number:
        # Extract the number and increment
        try:
            last_num = int(last_app.application_number.split("-")[1])
            next_num = last_num + 1
        except (IndexError, ValueError):
            next_num = 1001
    else:
        next_num = 1001

    return f"{prefix}{year}-{next_num:05d}"


def _add_timeline_event(
    db: Session,
    application_id: uuid_module.UUID,
    event_type: str,
    description: str,
    status: Optional[str] = None,
    previous_status: Optional[str] = None,
    user: Optional[str] = None,
    notes: Optional[str] = None,
    related_entity_type: Optional[str] = None,
    related_entity_id: Optional[uuid_module.UUID] = None,
):
    """Add an event to the application timeline."""
    event = PermitTimeline(
        permit_application_id=application_id,
        event_type=event_type,
        description=description,
        status=status,
        previous_status=previous_status,
        user=user,
        notes=notes,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        timestamp=datetime.utcnow(),
    )
    db.add(event)


def _calculate_permit_fee(permit_type: str, estimated_value: Optional[float]) -> float:
    """Calculate estimated permit fee based on type and construction value."""
    if permit_type == PermitType.DEVELOPMENT_PERMIT.value:
        base_fee = 300.0
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

    elif permit_type == PermitType.BUILDING_PERMIT.value:
        base_fee = 150.0
        if estimated_value:
            return base_fee + (estimated_value / 1000) * 12
        return base_fee

    else:
        return 100.0


def _app_to_response(app: PermitApplication) -> PermitApplicationResponse:
    """Convert a PermitApplication model to response schema."""
    # Count documents and deficiencies
    docs_count = len(app.documents) if app.documents else 0
    deficiencies_count = len(app.deficiencies) if app.deficiencies else 0
    open_deficiencies = sum(1 for d in (app.deficiencies or []) if d.status == DeficiencyStatusEnum.OPEN.value)

    # Build contact info objects
    applicant = None
    if app.applicant_name:
        applicant = ContactInfo(
            name=app.applicant_name,
            email=app.applicant_email,
            phone=app.applicant_phone,
            company=app.applicant_company,
            address=app.applicant_address,
        )

    agent = None
    if app.agent_name:
        agent = ContactInfo(
            name=app.agent_name,
            email=app.agent_email,
            phone=app.agent_phone,
            company=app.agent_company,
        )

    contractor = None
    if app.contractor_name:
        contractor = ContactInfo(
            name=app.contractor_name,
            email=app.contractor_email,
            phone=app.contractor_phone,
            company=app.contractor_company,
        )

    return PermitApplicationResponse(
        id=app.id,
        application_number=app.application_number,
        permit_type=PermitType(app.permit_type),
        status=ApplicationStatus(app.status),
        project_name=app.project_name,
        description=app.description,
        address=app.address,
        parcel_id=app.parcel_id,
        legal_description=app.legal_description,
        project_type=app.project_type,
        estimated_value=float(app.estimated_value) if app.estimated_value else None,
        classification=app.classification,
        occupancy_group=app.occupancy_group,
        building_area_sqm=float(app.building_area_sqm) if app.building_area_sqm else None,
        building_height_storeys=app.building_height_storeys,
        dwelling_units=app.dwelling_units,
        proposed_use=app.proposed_use,
        relaxations_requested=app.relaxations_requested,
        applicant=applicant,
        agent=agent,
        contractor=contractor,
        created_at=app.created_at,
        updated_at=app.updated_at,
        submitted_at=app.submitted_at,
        assigned_reviewer=app.assigned_reviewer,
        review_started_at=app.review_started_at,
        decision_date=app.decision_date,
        decision_notes=app.decision_notes,
        conditions=app.conditions,
        application_fee=float(app.application_fee) if app.application_fee else None,
        permit_fee=float(app.permit_fee) if app.permit_fee else None,
        fees_paid=app.fees_paid or False,
        related_dp_id=app.related_dp_id,
        project_id=app.project_id,
        documents_count=docs_count,
        deficiencies_count=deficiencies_count,
        open_deficiencies_count=open_deficiencies,
    )


def _doc_to_response(doc: PermitDocument) -> PermitDocumentResponse:
    """Convert a PermitDocument model to response schema."""
    return PermitDocumentResponse(
        id=doc.id,
        permit_application_id=doc.permit_application_id,
        document_type=doc.document_type,
        title=doc.title,
        description=doc.description,
        version=doc.version or 1,
        is_revision=doc.is_revision or False,
        replaces_document_id=doc.replaces_document_id,
        filename=doc.filename,
        file_path=doc.file_path,
        file_type=doc.file_type,
        file_size_bytes=doc.file_size_bytes,
        status=DocumentStatus(doc.status),
        uploaded_at=doc.uploaded_at,
        reviewed_at=doc.reviewed_at,
        reviewer=doc.reviewer,
        review_notes=doc.review_notes,
    )


def _comment_to_response(comment: PermitReviewComment) -> ReviewCommentResponse:
    """Convert a PermitReviewComment model to response schema."""
    return ReviewCommentResponse(
        id=comment.id,
        permit_application_id=comment.permit_application_id,
        category=comment.category,
        comment=comment.comment,
        code_reference=comment.code_reference,
        document_id=comment.document_id,
        page_number=comment.page_number,
        location_description=comment.location_description,
        requires_response=comment.requires_response or False,
        reviewer=comment.reviewer,
        created_at=comment.created_at,
        response=comment.response,
        responded_at=comment.responded_at,
        is_resolved=comment.is_resolved or False,
        resolved_at=comment.resolved_at,
    )


def _deficiency_to_response(deficiency: PermitDeficiency) -> DeficiencyResponse:
    """Convert a PermitDeficiency model to response schema."""
    return DeficiencyResponse(
        id=deficiency.id,
        permit_application_id=deficiency.permit_application_id,
        category=deficiency.category,
        title=deficiency.title,
        description=deficiency.description,
        priority=DeficiencyPriority(deficiency.priority),
        code_reference=deficiency.code_reference,
        required_action=deficiency.required_action,
        deadline_days=deficiency.deadline_days,
        document_id=deficiency.document_id,
        status=DeficiencyStatus(deficiency.status),
        created_at=deficiency.created_at,
        created_by=deficiency.created_by,
        deadline=deficiency.deadline,
        addressed_at=deficiency.addressed_at,
        addressed_notes=deficiency.addressed_notes,
        resolved_at=deficiency.resolved_at,
        resolved_by=deficiency.resolved_by,
        resolution_notes=deficiency.resolution_notes,
    )


def _appeal_to_response(appeal: SDABAppeal) -> SDABAppealResponse:
    """Convert an SDABAppeal model to response schema."""
    appellant = ContactInfo(
        name=appeal.appellant_name,
        email=appeal.appellant_email,
        phone=appeal.appellant_phone,
        company=appeal.appellant_company,
        address=appeal.appellant_address,
    )

    return SDABAppealResponse(
        id=appeal.id,
        appeal_number=appeal.appeal_number,
        permit_application_id=appeal.permit_application_id,
        appeal_type=AppealType(appeal.appeal_type),
        status=AppealStatus(appeal.status),
        grounds_for_appeal=appeal.grounds_for_appeal,
        requested_relief=appeal.requested_relief,
        supporting_arguments=appeal.supporting_arguments,
        appellant=appellant,
        filed_at=appeal.filed_at,
        deadline_to_file=appeal.deadline_to_file,
        hearing_date=appeal.hearing_date,
        hearing_location=appeal.hearing_location,
        hearing_notes=appeal.hearing_notes,
        decision_date=appeal.decision_date,
        decision=appeal.decision,
        decision_summary=appeal.decision_summary,
        conditions=appeal.conditions,
        original_decision=appeal.original_decision,
        original_decision_date=appeal.original_decision_date,
    )


# --- Permit Application Endpoints ---

@router.post("/applications", response_model=PermitApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_permit_application(
    application: PermitApplicationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new permit application (Development Permit or Building Permit).

    The application starts in 'draft' status and can be edited before submission.
    """
    # Generate application number
    app_number = _get_next_application_number(db, application.permit_type.value)

    # Calculate estimated fee
    permit_fee = _calculate_permit_fee(
        application.permit_type.value,
        application.estimated_value
    )

    # Create application record
    app = PermitApplication(
        application_number=app_number,
        permit_type=application.permit_type.value,
        status=ApplicationStatus.DRAFT.value,
        project_name=application.project_name,
        description=application.description,
        address=application.address,
        parcel_id=application.parcel_id,
        legal_description=application.legal_description,
        project_type=application.project_type,
        estimated_value=application.estimated_value,
        classification=application.classification,
        occupancy_group=application.occupancy_group,
        building_area_sqm=application.building_area_sqm,
        building_height_storeys=application.building_height_storeys,
        dwelling_units=application.dwelling_units,
        proposed_use=application.proposed_use,
        relaxations_requested=application.relaxations_requested,
        application_fee=50.0,
        permit_fee=permit_fee,
    )

    # Set contact info
    if application.applicant:
        app.applicant_name = application.applicant.name
        app.applicant_email = application.applicant.email
        app.applicant_phone = application.applicant.phone
        app.applicant_company = application.applicant.company
        app.applicant_address = application.applicant.address

    if application.agent:
        app.agent_name = application.agent.name
        app.agent_email = application.agent.email
        app.agent_phone = application.agent.phone
        app.agent_company = application.agent.company

    if application.contractor:
        app.contractor_name = application.contractor.name
        app.contractor_email = application.contractor.email
        app.contractor_phone = application.contractor.phone
        app.contractor_company = application.contractor.company

    db.add(app)
    db.flush()  # Get the ID

    # Add timeline event
    _add_timeline_event(
        db,
        app.id,
        "application_created",
        f"Permit application {app_number} created",
        status=ApplicationStatus.DRAFT.value,
    )

    db.commit()
    db.refresh(app)

    return _app_to_response(app)


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
    query = db.query(PermitApplication)

    # Apply filters
    if permit_type:
        query = query.filter(PermitApplication.permit_type == permit_type.value)
    if status:
        query = query.filter(PermitApplication.status == status.value)
    if address:
        query = query.filter(PermitApplication.address.ilike(f"%{address}%"))

    # Get total count
    total = query.count()

    # Sort and paginate
    query = query.order_by(desc(PermitApplication.created_at))
    offset = (page - 1) * page_size
    applications = query.offset(offset).limit(page_size).all()

    # Convert to summaries
    summaries = [
        PermitApplicationSummary(
            id=app.id,
            application_number=app.application_number,
            permit_type=PermitType(app.permit_type),
            project_name=app.project_name,
            address=app.address,
            status=ApplicationStatus(app.status),
            submitted_at=app.submitted_at,
            created_at=app.created_at,
        )
        for app in applications
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

    return _app_to_response(app)


@router.patch("/applications/{application_id}", response_model=PermitApplicationResponse)
async def update_permit_application(
    application_id: str,
    update: PermitApplicationUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a permit application.

    Only applications in 'draft' or 'information_requested' status can be fully edited.
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

    current_status = app.status
    editable_statuses = [
        ApplicationStatus.DRAFT.value,
        ApplicationStatus.INFORMATION_REQUESTED.value,
        ApplicationStatus.REVISION_REQUIRED.value
    ]

    update_dict = update.model_dump(exclude_unset=True)

    if current_status not in editable_statuses:
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
            app.applicant_name = value.get("name") if isinstance(value, dict) else value.name
            app.applicant_email = value.get("email") if isinstance(value, dict) else value.email
            app.applicant_phone = value.get("phone") if isinstance(value, dict) else value.phone
            app.applicant_company = value.get("company") if isinstance(value, dict) else value.company
            app.applicant_address = value.get("address") if isinstance(value, dict) else value.address
        elif field == "agent" and value:
            app.agent_name = value.get("name") if isinstance(value, dict) else value.name
            app.agent_email = value.get("email") if isinstance(value, dict) else value.email
            app.agent_phone = value.get("phone") if isinstance(value, dict) else value.phone
            app.agent_company = value.get("company") if isinstance(value, dict) else value.company
        elif field == "contractor" and value:
            app.contractor_name = value.get("name") if isinstance(value, dict) else value.name
            app.contractor_email = value.get("email") if isinstance(value, dict) else value.email
            app.contractor_phone = value.get("phone") if isinstance(value, dict) else value.phone
            app.contractor_company = value.get("company") if isinstance(value, dict) else value.company
        elif field == "status" and value:
            new_status = value.value if hasattr(value, "value") else value
            if new_status != current_status:
                _add_timeline_event(
                    db,
                    app.id,
                    "status_changed",
                    f"Status changed to {new_status}",
                    status=new_status,
                    previous_status=current_status,
                )
            app.status = new_status
        elif hasattr(app, field):
            setattr(app, field, value)

    app.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(app)

    return _app_to_response(app)


@router.post("/applications/{application_id}/submit", response_model=PermitApplicationResponse)
async def submit_permit_application(
    application_id: str,
    db: Session = Depends(get_db)
):
    """
    Submit a permit application for review.

    Changes status from 'draft' to 'submitted'.
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

    if app.status != ApplicationStatus.DRAFT.value:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit application in {app.status} status. Must be 'draft'."
        )

    # Check for documents
    doc_count = len(app.documents) if app.documents else 0
    warnings = []
    if doc_count == 0:
        warnings.append("No documents have been uploaded. Consider uploading required documents.")

    # Update status
    now = datetime.utcnow()
    previous_status = app.status
    app.status = ApplicationStatus.SUBMITTED.value
    app.submitted_at = now
    app.updated_at = now

    _add_timeline_event(
        db,
        app.id,
        "application_submitted",
        f"Application {app.application_number} submitted for review",
        status=ApplicationStatus.SUBMITTED.value,
        previous_status=previous_status,
        notes="; ".join(warnings) if warnings else None,
    )

    db.commit()
    db.refresh(app)

    return _app_to_response(app)


@router.post("/applications/{application_id}/status", response_model=PermitApplicationResponse)
async def update_application_status(
    application_id: str,
    status_update: StatusUpdateCreate,
    db: Session = Depends(get_db)
):
    """
    Update the status of a permit application.
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

    old_status = app.status
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
    app.status = new_status
    app.updated_at = now

    # Handle specific status changes
    if new_status == ApplicationStatus.UNDER_REVIEW.value:
        app.review_started_at = now
    elif new_status in [ApplicationStatus.APPROVED.value, ApplicationStatus.APPROVED_WITH_CONDITIONS.value, ApplicationStatus.REFUSED.value]:
        app.decision_date = now
        app.decision_notes = status_update.notes

    _add_timeline_event(
        db,
        app.id,
        "status_changed",
        f"Status changed from {old_status} to {new_status}",
        status=new_status,
        previous_status=old_status,
        notes=status_update.notes,
    )

    db.commit()
    db.refresh(app)

    return _app_to_response(app)


@router.get("/applications/{application_id}/timeline", response_model=ApplicationTimeline)
async def get_application_timeline(
    application_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the complete timeline of events for a permit application.
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

    # Get timeline events
    events = db.query(PermitTimeline).filter(
        PermitTimeline.permit_application_id == app_uuid
    ).order_by(desc(PermitTimeline.timestamp)).all()

    # Calculate days in review
    days_in_review = None
    if app.submitted_at:
        if app.status in [ApplicationStatus.APPROVED.value, ApplicationStatus.REFUSED.value]:
            if app.decision_date:
                days_in_review = (app.decision_date - app.submitted_at).days
        else:
            days_in_review = (datetime.utcnow() - app.submitted_at).days

    # Convert events to schema format
    timeline_events = [
        TimelineEvent(
            timestamp=e.timestamp,
            event_type=e.event_type,
            description=e.description,
            user=e.user,
            details={"notes": e.notes} if e.notes else None,
        )
        for e in events
    ]

    return ApplicationTimeline(
        permit_application_id=app.id,
        events=timeline_events,
        current_status=ApplicationStatus(app.status),
        days_in_review=days_in_review,
        estimated_completion_date=None,
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

    # Generate document ID
    doc_id = uuid_module.uuid4()

    # Save the file
    relative_path, absolute_path, file_size = await document_service.save_file(
        file,
        application_id,
        str(doc_id)
    )

    # Create document record
    doc = PermitDocument(
        id=doc_id,
        permit_application_id=app_uuid,
        document_type=document_type,
        title=title or file.filename,
        description=description,
        filename=file.filename,
        file_path=relative_path,
        file_type=file.content_type,
        file_size_bytes=file_size,
        status=DocumentStatus.PENDING.value,
    )

    db.add(doc)

    _add_timeline_event(
        db,
        app_uuid,
        "document_uploaded",
        f"Document uploaded: {file.filename}",
        related_entity_type="document",
        related_entity_id=doc_id,
        notes=f"Document type: {document_type}",
    )

    db.commit()
    db.refresh(doc)

    return _doc_to_response(doc)


@router.get("/applications/{application_id}/documents", response_model=List[PermitDocumentResponse])
async def list_application_documents(
    application_id: str,
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    status: Optional[DocumentStatus] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """
    List all documents for a permit application.
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

    query = db.query(PermitDocument).filter(
        PermitDocument.permit_application_id == app_uuid
    )

    if document_type:
        query = query.filter(PermitDocument.document_type == document_type)
    if status:
        query = query.filter(PermitDocument.status == status.value)

    docs = query.order_by(desc(PermitDocument.uploaded_at)).all()

    return [_doc_to_response(d) for d in docs]


@router.delete("/applications/{application_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    application_id: str,
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a document from a permit application.
    """
    try:
        app_uuid = uuid_module.UUID(application_id)
        doc_uuid = uuid_module.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    doc = db.query(PermitDocument).filter(
        PermitDocument.id == doc_uuid,
        PermitDocument.permit_application_id == app_uuid
    ).first()

    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found for application {application_id}"
        )

    # Delete the file
    if doc.file_path:
        document_service.delete_file(doc.file_path)

    # Add timeline event
    _add_timeline_event(
        db,
        app_uuid,
        "document_deleted",
        f"Document deleted: {doc.filename}",
        related_entity_type="document",
        related_entity_id=doc_uuid,
    )

    db.delete(doc)
    db.commit()


@router.patch("/documents/{document_id}/review", response_model=PermitDocumentResponse)
async def review_document(
    document_id: str,
    review: DocumentReviewUpdate,
    db: Session = Depends(get_db)
):
    """
    Update the review status of a document.
    """
    try:
        doc_uuid = uuid_module.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")

    doc = db.query(PermitDocument).filter(PermitDocument.id == doc_uuid).first()

    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found"
        )

    doc.status = review.status.value
    doc.review_notes = review.review_notes
    doc.reviewer = review.reviewer
    doc.reviewed_at = datetime.utcnow()

    _add_timeline_event(
        db,
        doc.permit_application_id,
        "document_reviewed",
        f"Document reviewed: {doc.filename} - {review.status.value}",
        user=review.reviewer,
        related_entity_type="document",
        related_entity_id=doc_uuid,
    )

    db.commit()
    db.refresh(doc)

    return _doc_to_response(doc)


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

    comment_record = PermitReviewComment(
        permit_application_id=app_uuid,
        category=comment.category,
        comment=comment.comment,
        code_reference=comment.code_reference,
        document_id=comment.document_id,
        page_number=comment.page_number,
        location_description=comment.location_description,
        requires_response=comment.requires_response,
        reviewer=reviewer,
    )

    db.add(comment_record)
    db.flush()

    _add_timeline_event(
        db,
        app_uuid,
        "comment_added",
        f"Review comment added: {comment.category}",
        user=reviewer,
        related_entity_type="comment",
        related_entity_id=comment_record.id,
        notes=f"Requires response: {comment.requires_response}",
    )

    db.commit()
    db.refresh(comment_record)

    return _comment_to_response(comment_record)


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

    query = db.query(PermitReviewComment).filter(
        PermitReviewComment.permit_application_id == app_uuid
    )

    if category:
        query = query.filter(PermitReviewComment.category == category)
    if unresolved_only:
        query = query.filter(PermitReviewComment.is_resolved == False)

    comments = query.order_by(desc(PermitReviewComment.created_at)).all()

    return [_comment_to_response(c) for c in comments]


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

    now = datetime.utcnow()
    deadline = None
    if deficiency.deadline_days:
        deadline = now + timedelta(days=deficiency.deadline_days)

    deficiency_record = PermitDeficiency(
        permit_application_id=app_uuid,
        category=deficiency.category,
        title=deficiency.title,
        description=deficiency.description,
        priority=deficiency.priority.value,
        code_reference=deficiency.code_reference,
        required_action=deficiency.required_action,
        deadline_days=deficiency.deadline_days,
        deadline=deadline,
        document_id=deficiency.document_id,
        created_by=created_by,
    )

    db.add(deficiency_record)
    db.flush()

    _add_timeline_event(
        db,
        app_uuid,
        "deficiency_created",
        f"Deficiency recorded: {deficiency.title}",
        user=created_by,
        related_entity_type="deficiency",
        related_entity_id=deficiency_record.id,
        notes=f"Priority: {deficiency.priority.value}, Category: {deficiency.category}",
    )

    db.commit()
    db.refresh(deficiency_record)

    return _deficiency_to_response(deficiency_record)


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

    query = db.query(PermitDeficiency).filter(
        PermitDeficiency.permit_application_id == app_uuid
    )

    if status:
        query = query.filter(PermitDeficiency.status == status.value)
    if priority:
        query = query.filter(PermitDeficiency.priority == priority.value)

    deficiencies = query.order_by(PermitDeficiency.priority, PermitDeficiency.created_at).all()

    return [_deficiency_to_response(d) for d in deficiencies]


@router.patch("/deficiencies/{deficiency_id}", response_model=DeficiencyResponse)
async def update_deficiency(
    deficiency_id: str,
    update: DeficiencyUpdate,
    updated_by: Optional[str] = Query(None, description="Name of person updating"),
    db: Session = Depends(get_db)
):
    """
    Update a deficiency status or add resolution notes.
    """
    try:
        def_uuid = uuid_module.UUID(deficiency_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid deficiency ID format")

    deficiency = db.query(PermitDeficiency).filter(PermitDeficiency.id == def_uuid).first()

    if not deficiency:
        raise HTTPException(
            status_code=404,
            detail=f"Deficiency {deficiency_id} not found"
        )

    now = datetime.utcnow()
    old_status = deficiency.status

    if update.status:
        deficiency.status = update.status.value

        if update.status == DeficiencyStatus.ADDRESSED:
            deficiency.addressed_at = now
            deficiency.addressed_notes = update.addressed_notes
        elif update.status == DeficiencyStatus.RESOLVED:
            deficiency.resolved_at = now
            deficiency.resolved_by = updated_by
            deficiency.resolution_notes = update.resolution_notes
        elif update.status == DeficiencyStatus.WAIVED:
            deficiency.resolved_at = now
            deficiency.resolved_by = updated_by
            deficiency.resolution_notes = update.resolution_notes or "Requirement waived"

        _add_timeline_event(
            db,
            deficiency.permit_application_id,
            "deficiency_updated",
            f"Deficiency status changed: {old_status} -> {update.status.value}",
            user=updated_by,
            related_entity_type="deficiency",
            related_entity_id=def_uuid,
        )

    db.commit()
    db.refresh(deficiency)

    return _deficiency_to_response(deficiency)


# --- SDAB Appeal Endpoints ---

@router.post("/appeals", response_model=SDABAppealResponse, status_code=status.HTTP_201_CREATED)
async def file_sdab_appeal(
    appeal: SDABAppealCreate,
    db: Session = Depends(get_db)
):
    """
    File an SDAB appeal for a refused permit application.
    """
    app = db.query(PermitApplication).filter(
        PermitApplication.id == appeal.permit_application_id
    ).first()

    if not app:
        raise HTTPException(
            status_code=404,
            detail=f"Permit application {appeal.permit_application_id} not found"
        )

    # Verify application status allows appeal
    if appeal.appeal_type == AppealType.APPEAL_OF_REFUSAL:
        if app.status != ApplicationStatus.REFUSED.value:
            raise HTTPException(
                status_code=400,
                detail="Can only appeal refused applications"
            )
    elif appeal.appeal_type == AppealType.APPEAL_OF_APPROVAL:
        if app.status not in [ApplicationStatus.APPROVED.value, ApplicationStatus.APPROVED_WITH_CONDITIONS.value]:
            raise HTTPException(
                status_code=400,
                detail="Can only appeal approved applications"
            )

    now = datetime.utcnow()

    # Calculate filing deadline (21 days from decision)
    deadline = None
    if app.decision_date:
        deadline = app.decision_date + timedelta(days=21)

    # Generate appeal number
    year = now.year
    count = db.query(func.count(SDABAppeal.id)).scalar() or 0
    appeal_number = f"SDAB-{year}-{count + 1:04d}"

    appeal_record = SDABAppeal(
        appeal_number=appeal_number,
        permit_application_id=appeal.permit_application_id,
        appeal_type=appeal.appeal_type.value,
        status=AppealStatus.FILED.value,
        grounds_for_appeal=appeal.grounds_for_appeal,
        requested_relief=appeal.requested_relief,
        supporting_arguments=appeal.supporting_arguments,
        appellant_name=appeal.appellant.name,
        appellant_email=appeal.appellant.email,
        appellant_phone=appeal.appellant.phone,
        appellant_company=appeal.appellant.company,
        appellant_address=appeal.appellant.address,
        deadline_to_file=deadline,
        original_decision=app.status,
        original_decision_date=app.decision_date,
    )

    db.add(appeal_record)
    db.flush()

    # Update application status
    previous_status = app.status
    app.status = ApplicationStatus.APPEALED.value
    app.updated_at = now

    _add_timeline_event(
        db,
        app.id,
        "appeal_filed",
        f"SDAB appeal filed: {appeal_number}",
        status=ApplicationStatus.APPEALED.value,
        previous_status=previous_status,
        related_entity_type="appeal",
        related_entity_id=appeal_record.id,
        notes=f"Grounds: {appeal.grounds_for_appeal[:100]}..." if len(appeal.grounds_for_appeal) > 100 else appeal.grounds_for_appeal,
    )

    db.commit()
    db.refresh(appeal_record)

    return _appeal_to_response(appeal_record)


@router.get("/appeals/{appeal_id}", response_model=SDABAppealResponse)
async def get_sdab_appeal(
    appeal_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about an SDAB appeal.
    """
    try:
        appeal_uuid = uuid_module.UUID(appeal_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid appeal ID format")

    appeal = db.query(SDABAppeal).filter(SDABAppeal.id == appeal_uuid).first()

    if not appeal:
        raise HTTPException(
            status_code=404,
            detail=f"SDAB appeal {appeal_id} not found"
        )

    return _appeal_to_response(appeal)


@router.get("/applications/{application_id}/appeals", response_model=List[SDABAppealResponse])
async def list_application_appeals(
    application_id: str,
    db: Session = Depends(get_db)
):
    """
    List all SDAB appeals for a permit application.
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

    appeals = db.query(SDABAppeal).filter(
        SDABAppeal.permit_application_id == app_uuid
    ).order_by(desc(SDABAppeal.filed_at)).all()

    return [_appeal_to_response(a) for a in appeals]


@router.patch("/appeals/{appeal_id}", response_model=SDABAppealResponse)
async def update_sdab_appeal(
    appeal_id: str,
    update: SDABAppealUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an SDAB appeal.
    """
    try:
        appeal_uuid = uuid_module.UUID(appeal_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid appeal ID format")

    appeal = db.query(SDABAppeal).filter(SDABAppeal.id == appeal_uuid).first()

    if not appeal:
        raise HTTPException(
            status_code=404,
            detail=f"SDAB appeal {appeal_id} not found"
        )

    now = datetime.utcnow()
    update_dict = update.model_dump(exclude_unset=True)

    for field, value in update_dict.items():
        if field == "status" and value:
            new_status = value.value if hasattr(value, "value") else value
            appeal.status = new_status

            if new_status in [AppealStatus.ALLOWED.value, AppealStatus.DENIED.value, AppealStatus.ALLOWED_IN_PART.value]:
                appeal.decision_date = now
                appeal.decision = new_status

                # Update original application based on appeal outcome
                app = db.query(PermitApplication).filter(
                    PermitApplication.id == appeal.permit_application_id
                ).first()
                if app:
                    if new_status == AppealStatus.ALLOWED.value:
                        app.status = ApplicationStatus.APPROVED.value
                    elif new_status == AppealStatus.DENIED.value:
                        app.status = ApplicationStatus.REFUSED.value
                    app.updated_at = now
        elif hasattr(appeal, field):
            setattr(appeal, field, value)

    db.commit()
    db.refresh(appeal)

    return _appeal_to_response(appeal)


# --- Statistics Endpoint ---

@router.get("/statistics", response_model=PermitStatistics)
async def get_permit_statistics(
    db: Session = Depends(get_db)
):
    """
    Get statistics about permit applications.
    """
    total = db.query(func.count(PermitApplication.id)).scalar() or 0

    # Count by type
    type_counts = db.query(
        PermitApplication.permit_type,
        func.count(PermitApplication.id)
    ).group_by(PermitApplication.permit_type).all()
    by_type = {t: c for t, c in type_counts}

    # Count by status
    status_counts = db.query(
        PermitApplication.status,
        func.count(PermitApplication.id)
    ).group_by(PermitApplication.status).all()
    by_status = {s: c for s, c in status_counts}

    # Calculate average review days
    completed_apps = db.query(PermitApplication).filter(
        PermitApplication.submitted_at.isnot(None),
        PermitApplication.decision_date.isnot(None)
    ).all()

    review_days = []
    for app in completed_apps:
        if app.submitted_at and app.decision_date:
            days = (app.decision_date - app.submitted_at).days
            review_days.append(days)

    avg_review_days = sum(review_days) / len(review_days) if review_days else None

    # Calculate approval rate
    decided = db.query(func.count(PermitApplication.id)).filter(
        PermitApplication.status.in_([
            ApplicationStatus.APPROVED.value,
            ApplicationStatus.APPROVED_WITH_CONDITIONS.value,
            ApplicationStatus.REFUSED.value
        ])
    ).scalar() or 0

    approved = db.query(func.count(PermitApplication.id)).filter(
        PermitApplication.status.in_([
            ApplicationStatus.APPROVED.value,
            ApplicationStatus.APPROVED_WITH_CONDITIONS.value
        ])
    ).scalar() or 0

    approval_rate = (approved / decided * 100) if decided > 0 else None

    # Common deficiencies
    deficiency_counts = db.query(
        PermitDeficiency.category,
        func.count(PermitDeficiency.id)
    ).group_by(PermitDeficiency.category).order_by(desc(func.count(PermitDeficiency.id))).limit(10).all()

    common_deficiencies = [
        {"category": cat, "count": count}
        for cat, count in deficiency_counts
    ]

    return PermitStatistics(
        total_applications=total,
        by_type=by_type,
        by_status=by_status,
        average_review_days=avg_review_days,
        approval_rate=approval_rate,
        common_deficiencies=common_deficiencies
    )


# --- Document Types Endpoint ---

@router.get("/document-types")
async def get_document_types():
    """
    Get the list of valid document types and their descriptions.
    """
    return document_service.get_document_types()


@router.get("/upload-constraints")
async def get_upload_constraints():
    """
    Get file upload constraints.
    """
    return {
        "allowed_extensions": document_service.get_allowed_file_types(),
        "max_file_size_bytes": document_service.get_max_file_size(),
        "max_file_size_mb": document_service.get_max_file_size() / (1024 * 1024),
    }
