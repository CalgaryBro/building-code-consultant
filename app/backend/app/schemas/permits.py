"""
Pydantic schemas for permit workflow management.

This module provides schemas for:
- Development Permit (DP) applications
- Building Permit (BP) applications
- Document submissions for review
- Application status tracking
- Review comments and deficiencies
- SDAB appeal workflow tracking
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, field_validator


# --- Enums ---

class PermitType(str, Enum):
    """Types of permits that can be applied for."""
    DEVELOPMENT_PERMIT = "DP"
    BUILDING_PERMIT = "BP"
    TRADE_PERMIT_ELECTRICAL = "TP_ELECTRICAL"
    TRADE_PERMIT_PLUMBING = "TP_PLUMBING"
    TRADE_PERMIT_GAS = "TP_GAS"
    TRADE_PERMIT_HVAC = "TP_HVAC"


class ApplicationStatus(str, Enum):
    """Status of a permit application."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    INFORMATION_REQUESTED = "information_requested"
    REVISION_REQUIRED = "revision_required"
    APPROVED = "approved"
    APPROVED_WITH_CONDITIONS = "approved_with_conditions"
    REFUSED = "refused"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    APPEALED = "appealed"


class DocumentStatus(str, Enum):
    """Status of a submitted document."""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REVISION_REQUIRED = "revision_required"


class DeficiencyPriority(str, Enum):
    """Priority level for deficiencies."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DeficiencyStatus(str, Enum):
    """Status of a deficiency."""
    OPEN = "open"
    ADDRESSED = "addressed"
    RESOLVED = "resolved"
    WAIVED = "waived"


class AppealStatus(str, Enum):
    """Status of an SDAB appeal."""
    DRAFT = "draft"
    FILED = "filed"
    SCHEDULED = "scheduled"
    HEARING_COMPLETED = "hearing_completed"
    ALLOWED = "allowed"
    DENIED = "denied"
    ALLOWED_IN_PART = "allowed_in_part"
    WITHDRAWN = "withdrawn"
    STRUCK = "struck"


class AppealType(str, Enum):
    """Type of SDAB appeal."""
    APPEAL_OF_REFUSAL = "appeal_of_refusal"
    APPEAL_OF_APPROVAL = "appeal_of_approval"  # By third party
    APPEAL_OF_CONDITIONS = "appeal_of_conditions"


# --- Base Schemas ---

class ContactInfo(BaseModel):
    """Contact information for applicants, agents, etc."""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None


class TimelineEvent(BaseModel):
    """A single event in the permit timeline."""
    timestamp: datetime
    event_type: str
    description: str
    user: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# --- Permit Application Schemas ---

class PermitApplicationBase(BaseModel):
    """Base schema for permit applications."""
    permit_type: PermitType
    project_name: Optional[str] = None
    description: Optional[str] = None

    # Location
    address: str
    parcel_id: Optional[UUID] = None
    legal_description: Optional[str] = None

    # Project details
    project_type: Optional[str] = Field(
        None,
        description="new_construction, addition, renovation, change_of_use, demolition"
    )
    estimated_value: Optional[float] = Field(
        None,
        description="Estimated construction value in CAD"
    )

    # Building details (for BP applications)
    classification: Optional[str] = Field(
        None,
        description="PART_9 or PART_3"
    )
    occupancy_group: Optional[str] = None
    building_area_sqm: Optional[float] = None
    building_height_storeys: Optional[int] = None
    dwelling_units: Optional[int] = None

    # DP specific
    proposed_use: Optional[str] = None
    relaxations_requested: Optional[List[str]] = None

    # Contacts
    applicant: Optional[ContactInfo] = None
    agent: Optional[ContactInfo] = None
    contractor: Optional[ContactInfo] = None


class PermitApplicationCreate(PermitApplicationBase):
    """Schema for creating a new permit application."""
    pass


class PermitApplicationUpdate(BaseModel):
    """Schema for updating a permit application."""
    project_name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[str] = None
    estimated_value: Optional[float] = None
    classification: Optional[str] = None
    occupancy_group: Optional[str] = None
    building_area_sqm: Optional[float] = None
    building_height_storeys: Optional[int] = None
    dwelling_units: Optional[int] = None
    proposed_use: Optional[str] = None
    relaxations_requested: Optional[List[str]] = None
    applicant: Optional[ContactInfo] = None
    agent: Optional[ContactInfo] = None
    contractor: Optional[ContactInfo] = None
    status: Optional[ApplicationStatus] = None


class PermitApplicationResponse(PermitApplicationBase):
    """Schema for permit application response."""
    id: UUID
    application_number: Optional[str] = None
    status: ApplicationStatus

    # Dates
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None

    # Review info
    assigned_reviewer: Optional[str] = None
    review_started_at: Optional[datetime] = None

    # Decision info
    decision_date: Optional[datetime] = None
    decision_notes: Optional[str] = None
    conditions: Optional[List[str]] = None

    # Fees
    application_fee: Optional[float] = None
    permit_fee: Optional[float] = None
    fees_paid: bool = False

    # Linked entities
    related_dp_id: Optional[UUID] = Field(
        None,
        description="For BP applications, the associated DP if applicable"
    )
    project_id: Optional[UUID] = None

    # Statistics
    documents_count: int = 0
    deficiencies_count: int = 0
    open_deficiencies_count: int = 0

    class Config:
        from_attributes = True


class PermitApplicationSummary(BaseModel):
    """Brief summary of a permit application for listings."""
    id: UUID
    application_number: Optional[str] = None
    permit_type: PermitType
    project_name: Optional[str] = None
    address: str
    status: ApplicationStatus
    submitted_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Document Submission Schemas ---

class PermitDocumentBase(BaseModel):
    """Base schema for permit documents."""
    document_type: str = Field(
        ...,
        description="site_plan, floor_plan, elevation, section, structural, mechanical, electrical, energy_compliance, survey, title, other"
    )
    title: Optional[str] = None
    description: Optional[str] = None
    version: int = 1
    is_revision: bool = False
    replaces_document_id: Optional[UUID] = None


class PermitDocumentUpload(PermitDocumentBase):
    """Schema for uploading a document to a permit application."""
    pass


class PermitDocumentResponse(PermitDocumentBase):
    """Schema for permit document response."""
    id: UUID
    permit_application_id: UUID
    filename: str
    file_path: str
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    status: DocumentStatus
    uploaded_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewer: Optional[str] = None
    review_notes: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentReviewUpdate(BaseModel):
    """Schema for updating document review status."""
    status: DocumentStatus
    review_notes: Optional[str] = None
    reviewer: Optional[str] = None


# --- Review Comments and Deficiencies ---

class ReviewCommentCreate(BaseModel):
    """Schema for creating a review comment."""
    category: str = Field(
        ...,
        description="zoning, structural, fire, egress, mechanical, electrical, energy, general"
    )
    comment: str
    code_reference: Optional[str] = None
    document_id: Optional[UUID] = Field(
        None,
        description="If comment relates to a specific document"
    )
    page_number: Optional[int] = None
    location_description: Optional[str] = None
    requires_response: bool = False


class ReviewCommentResponse(ReviewCommentCreate):
    """Schema for review comment response."""
    id: UUID
    permit_application_id: UUID
    reviewer: Optional[str] = None
    created_at: datetime
    response: Optional[str] = None
    responded_at: Optional[datetime] = None
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeficiencyCreate(BaseModel):
    """Schema for creating a deficiency notice."""
    category: str = Field(
        ...,
        description="zoning, structural, fire, egress, mechanical, electrical, energy, documentation"
    )
    title: str
    description: str
    priority: DeficiencyPriority = DeficiencyPriority.MEDIUM
    code_reference: Optional[str] = None
    required_action: str = Field(
        ...,
        description="What the applicant needs to do to address this deficiency"
    )
    deadline_days: Optional[int] = Field(
        None,
        description="Number of days from notification to address"
    )
    document_id: Optional[UUID] = None


class DeficiencyResponse(DeficiencyCreate):
    """Schema for deficiency response."""
    id: UUID
    permit_application_id: UUID
    status: DeficiencyStatus
    created_at: datetime
    created_by: Optional[str] = None
    deadline: Optional[datetime] = None

    # Resolution tracking
    addressed_at: Optional[datetime] = None
    addressed_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None

    class Config:
        from_attributes = True


class DeficiencyUpdate(BaseModel):
    """Schema for updating a deficiency."""
    status: Optional[DeficiencyStatus] = None
    addressed_notes: Optional[str] = None
    resolution_notes: Optional[str] = None


# --- SDAB Appeal Schemas ---

class SDABAppealBase(BaseModel):
    """Base schema for SDAB appeals."""
    appeal_type: AppealType
    grounds_for_appeal: str = Field(
        ...,
        description="Detailed grounds for the appeal"
    )
    requested_relief: str = Field(
        ...,
        description="What the appellant is asking the Board to grant"
    )
    supporting_arguments: Optional[List[str]] = None
    appellant: ContactInfo


class SDABAppealCreate(SDABAppealBase):
    """Schema for filing an SDAB appeal."""
    permit_application_id: UUID


class SDABAppealUpdate(BaseModel):
    """Schema for updating an SDAB appeal."""
    grounds_for_appeal: Optional[str] = None
    requested_relief: Optional[str] = None
    supporting_arguments: Optional[List[str]] = None
    status: Optional[AppealStatus] = None
    hearing_notes: Optional[str] = None


class SDABAppealResponse(SDABAppealBase):
    """Schema for SDAB appeal response."""
    id: UUID
    appeal_number: Optional[str] = None
    permit_application_id: UUID
    status: AppealStatus

    # Dates
    filed_at: datetime
    deadline_to_file: Optional[datetime] = None

    # Hearing info
    hearing_date: Optional[datetime] = None
    hearing_location: Optional[str] = None
    hearing_notes: Optional[str] = None

    # Decision
    decision_date: Optional[datetime] = None
    decision: Optional[str] = None
    decision_summary: Optional[str] = None
    conditions: Optional[List[str]] = None

    # Linked permit info
    original_decision: Optional[str] = None
    original_decision_date: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Status Tracking Schemas ---

class StatusUpdateCreate(BaseModel):
    """Schema for creating a status update."""
    new_status: ApplicationStatus
    notes: Optional[str] = None
    notify_applicant: bool = True


class ApplicationTimeline(BaseModel):
    """Full timeline of a permit application."""
    permit_application_id: UUID
    events: List[TimelineEvent]
    current_status: ApplicationStatus
    days_in_review: Optional[int] = None
    estimated_completion_date: Optional[datetime] = None


# --- Batch Operations ---

class BatchStatusUpdate(BaseModel):
    """Schema for batch status updates."""
    application_ids: List[UUID]
    new_status: ApplicationStatus
    notes: Optional[str] = None


class BatchDocumentReview(BaseModel):
    """Schema for batch document reviews."""
    document_ids: List[UUID]
    status: DocumentStatus
    review_notes: Optional[str] = None


# --- Search and Filter Schemas ---

class PermitSearchFilters(BaseModel):
    """Filters for searching permit applications."""
    permit_type: Optional[PermitType] = None
    status: Optional[ApplicationStatus] = None
    address: Optional[str] = None
    applicant_name: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    has_deficiencies: Optional[bool] = None
    assigned_reviewer: Optional[str] = None


class PermitSearchResponse(BaseModel):
    """Response for permit search."""
    total: int
    page: int
    page_size: int
    results: List[PermitApplicationSummary]


# --- Statistics and Reports ---

class PermitStatistics(BaseModel):
    """Statistics about permit applications."""
    total_applications: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    average_review_days: Optional[float] = None
    approval_rate: Optional[float] = None
    common_deficiencies: List[Dict[str, Any]]


class ReviewerWorkload(BaseModel):
    """Workload statistics for a reviewer."""
    reviewer: str
    active_applications: int
    pending_review: int
    completed_this_month: int
    average_review_days: Optional[float] = None
