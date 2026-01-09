"""
Pydantic schemas for projects, compliance checks, and documents.
"""
from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID
from pydantic import BaseModel, Field


# --- Project Schemas ---

class ProjectBase(BaseModel):
    """Base schema for Project."""
    project_name: Optional[str] = None
    description: Optional[str] = None
    address: str
    classification: Optional[str] = None  # PART_9, PART_3
    occupancy_group: Optional[str] = None  # C, D, E, F2, F3, etc.
    construction_type: Optional[str] = None  # combustible, noncombustible, heavy_timber
    building_height_storeys: Optional[int] = None
    building_height_m: Optional[float] = None
    building_area_sqm: Optional[float] = None
    footprint_area_sqm: Optional[float] = None
    dwelling_units: Optional[int] = None
    project_type: Optional[str] = None  # new_construction, addition, renovation, change_of_use


class ProjectCreate(ProjectBase):
    """Schema for creating a Project."""
    parcel_id: Optional[UUID] = None


class ProjectUpdate(BaseModel):
    """Schema for updating a Project."""
    project_name: Optional[str] = None
    description: Optional[str] = None
    classification: Optional[str] = None
    occupancy_group: Optional[str] = None
    construction_type: Optional[str] = None
    building_height_storeys: Optional[int] = None
    building_height_m: Optional[float] = None
    building_area_sqm: Optional[float] = None
    footprint_area_sqm: Optional[float] = None
    dwelling_units: Optional[int] = None
    project_type: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(ProjectBase):
    """Schema for Project response."""
    id: UUID
    parcel_id: Optional[UUID] = None
    development_permit_required: Optional[bool] = None
    building_permit_required: Optional[bool] = None
    estimated_permit_fee: Optional[float] = None
    status: str
    overall_compliance: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectSummary(BaseModel):
    """Brief project info for lists."""
    id: UUID
    project_name: Optional[str]
    address: str
    status: str
    overall_compliance: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Compliance Check Schemas ---

class ComplianceCheckResponse(BaseModel):
    """Schema for ComplianceCheck response."""
    id: UUID
    project_id: UUID
    requirement_id: Optional[UUID] = None
    check_category: str  # zoning, egress, fire, structural, energy
    check_name: str
    element: Optional[str] = None
    required_value: Optional[str] = None
    actual_value: Optional[str] = None
    unit: Optional[str] = None
    status: str  # pass, fail, warning, needs_review
    message: Optional[str] = None
    code_reference: Optional[str] = None
    extraction_confidence: Optional[str] = None
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ComplianceCheckCreate(BaseModel):
    """Schema for creating a ComplianceCheck."""
    requirement_id: Optional[UUID] = None
    check_category: str
    check_name: str
    element: Optional[str] = None
    required_value: Optional[str] = None
    actual_value: Optional[str] = None
    unit: Optional[str] = None
    status: str
    message: Optional[str] = None
    code_reference: Optional[str] = None
    extracted_from_document_id: Optional[UUID] = None
    extraction_confidence: Optional[str] = None


# --- Document Schemas ---

class DocumentUpload(BaseModel):
    """Schema for document upload metadata."""
    document_type: Optional[str] = None  # floor_plan, site_plan, elevation, section, schedule


class DocumentResponse(BaseModel):
    """Schema for Document response."""
    id: UUID
    project_id: UUID
    filename: str
    file_path: str
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    document_type: Optional[str] = None
    extraction_status: str
    extraction_started_at: Optional[datetime] = None
    extraction_completed_at: Optional[datetime] = None
    extraction_error: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Extracted Data Schemas ---

class ExtractedDataResponse(BaseModel):
    """Schema for ExtractedData response."""
    id: UUID
    document_id: UUID
    field_name: str
    field_category: Optional[str] = None
    value_raw: Optional[str] = None
    value_numeric: Optional[float] = None
    unit: Optional[str] = None
    page_number: Optional[int] = None
    location_description: Optional[str] = None
    confidence: str  # HIGH, MEDIUM, LOW, NOT_FOUND
    extraction_notes: Optional[str] = None
    is_verified: bool
    verified_value: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExtractedDataVerification(BaseModel):
    """Schema for verifying extracted data."""
    verified_value: str
    verified_by: str
    verification_notes: Optional[str] = None


# --- Guide Mode Schemas ---

class GuideProjectInput(BaseModel):
    """Input for GUIDE mode - describes the proposed project."""
    address: str
    project_type: str = Field(..., description="new_construction, addition, renovation, change_of_use")
    occupancy_type: str = Field(..., description="residential, commercial, industrial, mixed")
    building_height_storeys: Optional[int] = None
    building_area_sqm: Optional[float] = None
    footprint_area_sqm: Optional[float] = None
    dwelling_units: Optional[int] = None
    description: Optional[str] = None


class PermitRequirement(BaseModel):
    """A single permit or approval requirement."""
    permit_type: str  # development_permit, building_permit, trade_permit, etc.
    required: bool
    description: str
    estimated_fee: Optional[float] = None
    typical_timeline_days: Optional[int] = None
    documents_required: List[str] = []
    notes: Optional[str] = None


class GuideResponse(BaseModel):
    """Response for GUIDE mode."""
    project: ProjectResponse
    classification: str  # PART_9 or PART_3
    classification_reason: str
    zoning_status: str  # compliant, relaxation_required, redesignation_required
    permits_required: List[PermitRequirement]
    key_requirements: List[str]
    next_steps: List[str]
    warnings: List[str] = []


# --- Review Mode Schemas ---

class ReviewRequest(BaseModel):
    """Request to start a document review."""
    project_id: UUID
    document_ids: List[UUID]
    check_categories: Optional[List[str]] = None  # zoning, egress, fire, etc.


class ReviewProgress(BaseModel):
    """Progress update during document review."""
    status: str  # processing, complete, failed
    current_document: Optional[str] = None
    documents_processed: int
    total_documents: int
    checks_completed: int
    issues_found: int


class ReviewSummary(BaseModel):
    """Summary of review results."""
    project_id: UUID
    overall_status: str  # pass, fail, needs_review
    total_checks: int
    passed: int
    failed: int
    warnings: int
    needs_review: int
    critical_issues: List[ComplianceCheckResponse]
    all_checks: List[ComplianceCheckResponse]
    recommendations: List[str]
