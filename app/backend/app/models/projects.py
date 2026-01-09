"""
Models for user projects, compliance checks, and document extraction.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime,
    Numeric, ForeignKey, Index, Enum
)
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from ..database import Base
from .codes import UUID  # Import cross-database UUID type


class ProjectStatus(str, PyEnum):
    """Project workflow status."""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    COMPLETE = "complete"
    ARCHIVED = "archived"


class BuildingClassification(str, PyEnum):
    """NBC building classification."""
    PART_9 = "PART_9"  # Small buildings
    PART_3 = "PART_3"  # Large/complex buildings


class OccupancyGroup(str, PyEnum):
    """Major occupancy classifications."""
    A1 = "A1"  # Assembly - fixed seats
    A2 = "A2"  # Assembly - no fixed seats
    A3 = "A3"  # Assembly - arena
    A4 = "A4"  # Assembly - open air
    B1 = "B1"  # Care - detention
    B2 = "B2"  # Care - treatment
    B3 = "B3"  # Care - assisted
    C = "C"    # Residential
    D = "D"    # Business/personal services
    E = "E"    # Mercantile
    F1 = "F1"  # Industrial - high hazard
    F2 = "F2"  # Industrial - medium hazard
    F3 = "F3"  # Industrial - low hazard


class ComplianceStatus(str, PyEnum):
    """Compliance check result."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NEEDS_REVIEW = "needs_review"
    NOT_APPLICABLE = "not_applicable"


class Project(Base):
    """
    A user's building project being checked for compliance.
    """
    __tablename__ = "projects"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)

    # Basic info
    project_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # Location
    address = Column(String(255), nullable=False)
    parcel_id = Column(UUID(), ForeignKey("parcels.id"), nullable=True)

    # Building classification
    classification = Column(String(20), nullable=True)  # PART_9, PART_3
    occupancy_group = Column(String(10), nullable=True)  # C, D, E, F2, F3, etc.
    construction_type = Column(String(50), nullable=True)  # combustible, noncombustible, heavy_timber

    # Building parameters
    building_height_storeys = Column(Integer, nullable=True)
    building_height_m = Column(Numeric, nullable=True)
    building_area_sqm = Column(Numeric, nullable=True)  # Total gross area
    footprint_area_sqm = Column(Numeric, nullable=True)  # Ground floor
    dwelling_units = Column(Integer, nullable=True)

    # Project type
    project_type = Column(String(50), nullable=True)  # new_construction, addition, renovation, change_of_use

    # Permit tracking
    development_permit_required = Column(Boolean, nullable=True)
    building_permit_required = Column(Boolean, nullable=True)
    estimated_permit_fee = Column(Numeric, nullable=True)

    # Status
    status = Column(String(50), default="draft")
    overall_compliance = Column(String(50), nullable=True)  # pass, fail, needs_review

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    parcel = relationship("Parcel", back_populates="projects")
    compliance_checks = relationship("ComplianceCheck", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_projects_status", "status"),
        Index("idx_projects_address", "address"),
    )


class ComplianceCheck(Base):
    """
    A single compliance check against a code requirement.
    """
    __tablename__ = "compliance_checks"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(), ForeignKey("projects.id"), nullable=False)
    requirement_id = Column(UUID(), ForeignKey("requirements.id"), nullable=True)

    # What was checked
    check_category = Column(String(100), nullable=False)  # zoning, egress, fire, structural, energy
    check_name = Column(String(255), nullable=False)  # e.g., "Stair Width", "Front Setback"
    element = Column(String(100), nullable=True)  # e.g., "stair_width", "setback_front"

    # The check
    required_value = Column(String(255), nullable=True)  # What the code requires
    actual_value = Column(String(255), nullable=True)  # What the project has
    unit = Column(String(20), nullable=True)

    # Result
    status = Column(String(50), nullable=False)  # pass, fail, warning, needs_review
    message = Column(Text, nullable=True)  # Human-readable explanation
    code_reference = Column(String(100), nullable=True)  # e.g., "NBC 9.8.4.1"

    # If value was extracted from drawing
    extracted_from_document_id = Column(UUID(), ForeignKey("documents.id"), nullable=True)
    extraction_confidence = Column(String(20), nullable=True)

    # Verification
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="compliance_checks")
    requirement = relationship("Requirement")
    source_document = relationship("Document")

    __table_args__ = (
        Index("idx_checks_project_status", "project_id", "status"),
        Index("idx_checks_category", "check_category"),
    )


class Document(Base):
    """
    An uploaded document (drawing, plan, etc.) for a project.
    """
    __tablename__ = "documents"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(), ForeignKey("projects.id"), nullable=False)

    # File info
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=True)  # pdf, dwg, image
    file_size_bytes = Column(Integer, nullable=True)

    # Document type
    document_type = Column(String(50), nullable=True)  # floor_plan, site_plan, elevation, section, schedule

    # Extraction status
    extraction_status = Column(String(50), default="pending")  # pending, processing, complete, failed
    extraction_started_at = Column(DateTime, nullable=True)
    extraction_completed_at = Column(DateTime, nullable=True)
    extraction_error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="documents")
    extracted_data = relationship("ExtractedData", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_documents_project", "project_id"),
        Index("idx_documents_status", "extraction_status"),
    )


class ExtractedData(Base):
    """
    Data extracted from a document by the VLM.
    All extracted values require human verification before use in compliance checks.
    """
    __tablename__ = "extracted_data"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(), ForeignKey("documents.id"), nullable=False)

    # What was extracted
    field_name = Column(String(100), nullable=False)  # e.g., "stair_width", "room_area"
    field_category = Column(String(50), nullable=True)  # dimension, count, label, area

    # The extracted value
    value_raw = Column(String(255), nullable=True)  # Exactly as extracted
    value_numeric = Column(Numeric, nullable=True)  # Parsed numeric value
    unit = Column(String(20), nullable=True)

    # Location in document
    page_number = Column(Integer, nullable=True)
    location_description = Column(Text, nullable=True)  # e.g., "Ground floor, east stairwell"

    # Confidence
    confidence = Column(String(20), nullable=False)  # HIGH, MEDIUM, LOW, NOT_FOUND
    extraction_notes = Column(Text, nullable=True)  # Any warnings or notes from VLM

    # Verification (REQUIRED for life-safety values)
    is_verified = Column(Boolean, default=False)
    verified_value = Column(String(255), nullable=True)  # The confirmed correct value
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verification_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="extracted_data")

    __table_args__ = (
        Index("idx_extracted_document_field", "document_id", "field_name"),
        Index("idx_extracted_verified", "is_verified"),
    )
