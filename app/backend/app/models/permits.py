"""
SQLAlchemy models for permit applications, documents, and timeline tracking.

This module provides database models for:
- PermitApplication: Main permit applications (DP, BP, Trade permits)
- PermitDocument: Documents uploaded to permit applications
- PermitTimeline: Status change history for permits
- PermitDeficiency: Deficiencies recorded during review
- PermitReviewComment: Review comments from reviewers
- SDABAppeal: SDAB appeal records
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime,
    Numeric, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship

from ..database import Base
from .codes import UUID, StringArray


# --- Enums ---

class PermitTypeEnum(str, PyEnum):
    """Types of permits that can be applied for."""
    DEVELOPMENT_PERMIT = "DP"
    BUILDING_PERMIT = "BP"
    TRADE_PERMIT_ELECTRICAL = "TP_ELECTRICAL"
    TRADE_PERMIT_PLUMBING = "TP_PLUMBING"
    TRADE_PERMIT_GAS = "TP_GAS"
    TRADE_PERMIT_HVAC = "TP_HVAC"


class ApplicationStatusEnum(str, PyEnum):
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


class DocumentStatusEnum(str, PyEnum):
    """Status of a submitted document."""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REVISION_REQUIRED = "revision_required"


class DeficiencyStatusEnum(str, PyEnum):
    """Status of a deficiency."""
    OPEN = "open"
    ADDRESSED = "addressed"
    RESOLVED = "resolved"
    WAIVED = "waived"


class DeficiencyPriorityEnum(str, PyEnum):
    """Priority level for deficiencies."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AppealStatusEnum(str, PyEnum):
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


class AppealTypeEnum(str, PyEnum):
    """Type of SDAB appeal."""
    APPEAL_OF_REFUSAL = "appeal_of_refusal"
    APPEAL_OF_APPROVAL = "appeal_of_approval"
    APPEAL_OF_CONDITIONS = "appeal_of_conditions"


# --- Models ---

class PermitApplication(Base):
    """
    A permit application (Development Permit, Building Permit, or Trade Permit).

    This is the central entity for the permit workflow, tracking the application
    from draft through submission, review, and final decision.
    """
    __tablename__ = "permit_applications"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    application_number = Column(String(50), unique=True, nullable=True)

    # Permit type and status
    permit_type = Column(String(20), nullable=False)  # DP, BP, TP_*
    status = Column(String(50), nullable=False, default="draft")

    # Basic project info
    project_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # Location
    address = Column(String(255), nullable=False)
    parcel_id = Column(UUID(), ForeignKey("parcels.id"), nullable=True)
    legal_description = Column(Text, nullable=True)

    # Project details
    project_type = Column(String(50), nullable=True)  # new_construction, addition, renovation, change_of_use, demolition
    estimated_value = Column(Numeric, nullable=True)

    # Building details (for BP applications)
    classification = Column(String(20), nullable=True)  # PART_9, PART_3
    occupancy_group = Column(String(10), nullable=True)
    building_area_sqm = Column(Numeric, nullable=True)
    building_height_storeys = Column(Integer, nullable=True)
    dwelling_units = Column(Integer, nullable=True)

    # DP specific
    proposed_use = Column(String(255), nullable=True)
    relaxations_requested = Column(StringArray(), nullable=True)

    # Contact information (stored as JSON-like strings)
    applicant_name = Column(String(255), nullable=True)
    applicant_email = Column(String(255), nullable=True)
    applicant_phone = Column(String(50), nullable=True)
    applicant_company = Column(String(255), nullable=True)
    applicant_address = Column(Text, nullable=True)

    agent_name = Column(String(255), nullable=True)
    agent_email = Column(String(255), nullable=True)
    agent_phone = Column(String(50), nullable=True)
    agent_company = Column(String(255), nullable=True)

    contractor_name = Column(String(255), nullable=True)
    contractor_email = Column(String(255), nullable=True)
    contractor_phone = Column(String(50), nullable=True)
    contractor_company = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)

    # Review info
    assigned_reviewer = Column(String(255), nullable=True)
    review_started_at = Column(DateTime, nullable=True)

    # Decision info
    decision_date = Column(DateTime, nullable=True)
    decision_notes = Column(Text, nullable=True)
    conditions = Column(StringArray(), nullable=True)

    # Fees
    application_fee = Column(Numeric, nullable=True, default=50.0)
    permit_fee = Column(Numeric, nullable=True)
    fees_paid = Column(Boolean, default=False)

    # Related entities
    related_dp_id = Column(UUID(), ForeignKey("permit_applications.id"), nullable=True)
    project_id = Column(UUID(), ForeignKey("projects.id"), nullable=True)

    # Relationships
    parcel = relationship("Parcel", foreign_keys=[parcel_id])
    project = relationship("Project", foreign_keys=[project_id])
    related_dp = relationship("PermitApplication", remote_side=[id], foreign_keys=[related_dp_id])
    documents = relationship("PermitDocument", back_populates="permit_application", cascade="all, delete-orphan")
    timeline_events = relationship("PermitTimeline", back_populates="permit_application", cascade="all, delete-orphan", order_by="PermitTimeline.timestamp.desc()")
    deficiencies = relationship("PermitDeficiency", back_populates="permit_application", cascade="all, delete-orphan")
    review_comments = relationship("PermitReviewComment", back_populates="permit_application", cascade="all, delete-orphan")
    appeals = relationship("SDABAppeal", back_populates="permit_application", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_permit_app_status", "status"),
        Index("idx_permit_app_type", "permit_type"),
        Index("idx_permit_app_address", "address"),
        Index("idx_permit_app_submitted", "submitted_at"),
        Index("idx_permit_app_reviewer", "assigned_reviewer"),
    )


class PermitDocument(Base):
    """
    A document uploaded to a permit application.

    Documents can be site plans, floor plans, elevations, structural drawings,
    energy compliance docs, etc. Each document goes through a review process.
    """
    __tablename__ = "permit_documents"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    permit_application_id = Column(UUID(), ForeignKey("permit_applications.id"), nullable=False)

    # Document metadata
    document_type = Column(String(50), nullable=False)  # site_plan, floor_plan, elevation, etc.
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # Versioning
    version = Column(Integer, default=1)
    is_revision = Column(Boolean, default=False)
    replaces_document_id = Column(UUID(), ForeignKey("permit_documents.id"), nullable=True)

    # File info
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(100), nullable=True)  # MIME type
    file_size_bytes = Column(Integer, nullable=True)

    # Review status
    status = Column(String(50), nullable=False, default="pending")
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewer = Column(String(255), nullable=True)
    review_notes = Column(Text, nullable=True)

    # Verification
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(255), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verification_notes = Column(Text, nullable=True)

    # Relationships
    permit_application = relationship("PermitApplication", back_populates="documents")
    replaces_document = relationship("PermitDocument", remote_side=[id], foreign_keys=[replaces_document_id])

    __table_args__ = (
        Index("idx_permit_doc_app", "permit_application_id"),
        Index("idx_permit_doc_type", "document_type"),
        Index("idx_permit_doc_status", "status"),
    )


class PermitTimeline(Base):
    """
    Tracks status changes and significant events for a permit application.

    Provides a complete audit trail of all changes to the application status,
    document submissions, review comments, and other significant events.
    """
    __tablename__ = "permit_timeline"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    permit_application_id = Column(UUID(), ForeignKey("permit_applications.id"), nullable=False)

    # Event info
    event_type = Column(String(100), nullable=False)  # status_changed, document_uploaded, comment_added, etc.
    status = Column(String(50), nullable=True)  # New status if this was a status change
    previous_status = Column(String(50), nullable=True)  # Previous status if this was a status change
    description = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)

    # Who and when
    user = Column(String(255), nullable=True)  # Who triggered this event
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Optional reference to related entity
    related_entity_type = Column(String(50), nullable=True)  # document, deficiency, comment, appeal
    related_entity_id = Column(UUID(), nullable=True)

    # Relationships
    permit_application = relationship("PermitApplication", back_populates="timeline_events")

    __table_args__ = (
        Index("idx_timeline_app", "permit_application_id"),
        Index("idx_timeline_timestamp", "timestamp"),
        Index("idx_timeline_type", "event_type"),
    )


class PermitDeficiency(Base):
    """
    A deficiency recorded during permit review.

    Deficiencies are formal issues that must be addressed before the application
    can be approved. They have priority levels and deadlines.
    """
    __tablename__ = "permit_deficiencies"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    permit_application_id = Column(UUID(), ForeignKey("permit_applications.id"), nullable=False)

    # Deficiency details
    category = Column(String(100), nullable=False)  # zoning, structural, fire, egress, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, default="medium")  # critical, high, medium, low

    # Code reference
    code_reference = Column(String(255), nullable=True)
    required_action = Column(Text, nullable=False)

    # Timeline
    deadline_days = Column(Integer, nullable=True)
    deadline = Column(DateTime, nullable=True)

    # Related document
    document_id = Column(UUID(), ForeignKey("permit_documents.id"), nullable=True)

    # Status tracking
    status = Column(String(50), nullable=False, default="open")  # open, addressed, resolved, waived
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255), nullable=True)

    # Resolution
    addressed_at = Column(DateTime, nullable=True)
    addressed_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(255), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Relationships
    permit_application = relationship("PermitApplication", back_populates="deficiencies")
    document = relationship("PermitDocument", foreign_keys=[document_id])

    __table_args__ = (
        Index("idx_deficiency_app", "permit_application_id"),
        Index("idx_deficiency_status", "status"),
        Index("idx_deficiency_priority", "priority"),
    )


class PermitReviewComment(Base):
    """
    A review comment from a permit reviewer.

    Comments can be general or linked to specific documents and pages.
    They may require a response from the applicant.
    """
    __tablename__ = "permit_review_comments"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    permit_application_id = Column(UUID(), ForeignKey("permit_applications.id"), nullable=False)

    # Comment details
    category = Column(String(100), nullable=False)  # zoning, structural, fire, egress, etc.
    comment = Column(Text, nullable=False)
    code_reference = Column(String(255), nullable=True)

    # Related document
    document_id = Column(UUID(), ForeignKey("permit_documents.id"), nullable=True)
    page_number = Column(Integer, nullable=True)
    location_description = Column(Text, nullable=True)

    # Reviewer info
    reviewer = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    requires_response = Column(Boolean, default=False)

    # Response
    response = Column(Text, nullable=True)
    responded_at = Column(DateTime, nullable=True)

    # Resolution
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    permit_application = relationship("PermitApplication", back_populates="review_comments")
    document = relationship("PermitDocument", foreign_keys=[document_id])

    __table_args__ = (
        Index("idx_comment_app", "permit_application_id"),
        Index("idx_comment_category", "category"),
        Index("idx_comment_resolved", "is_resolved"),
    )


class SDABAppeal(Base):
    """
    An SDAB (Subdivision and Development Appeal Board) appeal.

    Appeals can be filed against refused applications (by applicant),
    approved applications (by third parties), or specific conditions.
    """
    __tablename__ = "sdab_appeals"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    appeal_number = Column(String(50), unique=True, nullable=True)
    permit_application_id = Column(UUID(), ForeignKey("permit_applications.id"), nullable=False)

    # Appeal type and status
    appeal_type = Column(String(50), nullable=False)  # appeal_of_refusal, appeal_of_approval, appeal_of_conditions
    status = Column(String(50), nullable=False, default="draft")

    # Appeal details
    grounds_for_appeal = Column(Text, nullable=False)
    requested_relief = Column(Text, nullable=False)
    supporting_arguments = Column(StringArray(), nullable=True)

    # Appellant info
    appellant_name = Column(String(255), nullable=False)
    appellant_email = Column(String(255), nullable=True)
    appellant_phone = Column(String(50), nullable=True)
    appellant_company = Column(String(255), nullable=True)
    appellant_address = Column(Text, nullable=True)

    # Filing info
    filed_at = Column(DateTime, default=datetime.utcnow)
    deadline_to_file = Column(DateTime, nullable=True)

    # Hearing info
    hearing_date = Column(DateTime, nullable=True)
    hearing_location = Column(String(255), nullable=True)
    hearing_notes = Column(Text, nullable=True)

    # Decision
    decision_date = Column(DateTime, nullable=True)
    decision = Column(String(50), nullable=True)  # allowed, denied, allowed_in_part, struck
    decision_summary = Column(Text, nullable=True)
    conditions = Column(StringArray(), nullable=True)

    # Original decision reference
    original_decision = Column(String(50), nullable=True)
    original_decision_date = Column(DateTime, nullable=True)

    # Relationships
    permit_application = relationship("PermitApplication", back_populates="appeals")

    __table_args__ = (
        Index("idx_appeal_app", "permit_application_id"),
        Index("idx_appeal_status", "status"),
        Index("idx_appeal_type", "appeal_type"),
    )
