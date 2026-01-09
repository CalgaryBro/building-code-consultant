"""
Pydantic schemas for SDAB and DP issue checklists.

These schemas define the structure for serving checklist data to help users
understand common issues and risks in building permit applications.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# --- SDAB Issue Schemas ---

class SDABCitation(BaseModel):
    """Sample citation from SDAB decision history."""
    decision_number: str
    outcome: str
    year: str
    address: str
    key_reasoning: str
    property_type: str


class SDABTypicalOutcomes(BaseModel):
    """Typical outcomes for an SDAB issue type."""
    allowed: int = 0
    denied: int = 0
    allowed_in_part: int = 0
    withdrawn: int = 0
    struck: int = 0


class SDABIssueSummary(BaseModel):
    """Summary view of an SDAB issue type (for listing)."""
    issue_id: str
    issue_type: str
    display_name: str
    description: str
    frequency: int
    risk_level: str
    success_rate_percent: float


class SDABIssueDetail(BaseModel):
    """Detailed view of an SDAB issue type."""
    issue_id: str
    issue_type: str
    display_name: str
    description: str
    frequency: int
    risk_level: str
    success_rate_percent: float
    typical_outcomes: SDABTypicalOutcomes
    common_property_types: Dict[str, int]
    key_factors_for_approval: List[str]
    key_factors_for_denial: List[str]
    sample_citations: List[SDABCitation]
    recommendation: str


class SDABMetadata(BaseModel):
    """Metadata about the SDAB checklist."""
    generated_at: str
    source_file: str
    total_records_analyzed: int
    description: str
    note: str


class SDABSummaryStatistics(BaseModel):
    """Summary statistics from SDAB data."""
    total_cases: int
    overall_outcomes: Dict[str, int]
    appeals_of_refusals: Dict[str, Any]
    appeals_of_approvals: Dict[str, Any]


class SDABChecklistResponse(BaseModel):
    """Full SDAB checklist response."""
    metadata: SDABMetadata
    summary_statistics: SDABSummaryStatistics
    issues: List[SDABIssueSummary]


# --- DP Refusal Schemas ---

class DPSampleCitation(BaseModel):
    """Sample citation from DP refusal history."""
    permit_number: str
    description: str
    zone: str
    address: str
    applied_date: str
    community: str


class DPIssueSummary(BaseModel):
    """Summary view of a DP issue type (for listing)."""
    issue_id: str
    issue_category: str
    description: str
    frequency: int
    typical_deficiency: str


class DPIssueDetail(BaseModel):
    """Detailed view of a DP issue type."""
    issue_id: str
    issue_category: str
    description: str
    frequency: int
    common_zones_affected: List[str]
    typical_deficiency: str
    code_references: List[str]
    sample_citations: List[DPSampleCitation]
    prevention_tips: List[str]
    relaxation_success_rate: Optional[float] = None


class DPMetadata(BaseModel):
    """Metadata about the DP refusal checklist."""
    generated_date: str
    source_file: str
    total_permits_analyzed: int
    total_refused_permits: int
    refusal_rate: float
    data_coverage: str
    purpose: str


class DPSummary(BaseModel):
    """Summary information from DP data."""
    top_refusal_reasons: List[Dict[str, Any]]
    most_affected_zones: Dict[str, int]


class DPChecklistResponse(BaseModel):
    """Full DP refusal checklist response."""
    metadata: DPMetadata
    summary: DPSummary
    checklist_items: List[DPIssueSummary]


# --- Risk Assessment Schemas ---

class RiskIssue(BaseModel):
    """An issue relevant to a risk assessment."""
    source: str = Field(..., description="Source: 'sdab' or 'dp'")
    issue_id: str
    issue_type: str
    display_name: str
    description: str
    frequency: int
    risk_level: str
    success_rate_percent: Optional[float] = None
    key_factors_for_approval: Optional[List[str]] = None
    key_factors_for_denial: Optional[List[str]] = None
    prevention_tips: Optional[List[str]] = None
    recommendation: Optional[str] = None


class RiskAssessmentResponse(BaseModel):
    """Response for project-type risk assessment."""
    project_type: str
    project_type_description: str
    total_relevant_issues: int
    high_risk_issues: List[RiskIssue]
    medium_risk_issues: List[RiskIssue]
    moderate_risk_issues: List[RiskIssue]
    low_risk_issues: List[RiskIssue]
    general_guidance: Dict[str, Any]


# --- General Guidance Schema ---

class RiskLevelGuidance(BaseModel):
    """Guidance for a specific risk level."""
    HIGH: str
    MEDIUM: str
    MODERATE: str
    LOW: str


class AppealProcessNotes(BaseModel):
    """Notes about the appeal process."""
    timeline: str
    documentation: str
    representation: str
    neighbor_notification: str
    decision_timing: str


class GeneralGuidance(BaseModel):
    """General guidance from the SDAB checklist."""
    appeal_success_factors: List[str]
    common_denial_reasons: List[str]
    preparation_tips: List[str]
    appeal_process_notes: AppealProcessNotes
    year_over_year_trends: Dict[str, str]
    risk_level_guidance: RiskLevelGuidance
