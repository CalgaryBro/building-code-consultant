"""
Pydantic schemas for API request/response validation.
"""
from .codes import (
    CodeBase, CodeCreate, CodeResponse,
    ArticleBase, ArticleCreate, ArticleResponse, ArticleSearchResult,
    RequirementBase, RequirementCreate, RequirementResponse,
)
from .zones import (
    ZoneBase, ZoneCreate, ZoneResponse,
    ZoneRuleResponse,
    ParcelBase, ParcelCreate, ParcelResponse, ParcelSearchResult,
)
from .projects import (
    ProjectBase, ProjectCreate, ProjectUpdate, ProjectResponse,
    ComplianceCheckResponse,
    DocumentUpload, DocumentResponse,
    ExtractedDataResponse,
)
from .checklists import (
    SDABIssueSummary, SDABIssueDetail, SDABChecklistResponse,
    DPIssueSummary, DPIssueDetail, DPChecklistResponse,
    RiskAssessmentResponse, RiskIssue, GeneralGuidance,
)
from .permits import (
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
    StatusUpdateCreate, ApplicationTimeline,
    # Search
    PermitSearchFilters, PermitSearchResponse,
    # Statistics
    PermitStatistics,
)
from .fees import (
    # Enums
    BuildingType, ResidentialAlterationType, TradePermitType,
    ProjectType, ZoneCategory,
    # Fee Breakdown
    FeeLineItem, FeeBreakdown,
    # Building Permit
    BuildingPermitFeeRequest, BuildingPermitFeeResponse,
    # Trade Permits
    TradePermitRequest, TradePermitFeeRequest, TradePermitFeeResponse, TradePermitFeeItem,
    # Development Permit
    DevelopmentPermitFeeRequest, DevelopmentPermitFeeResponse,
    # Project Estimate
    ProjectFeeEstimateRequest, ProjectFeeEstimateResponse, FeeCategorySummary,
    # Additional Fees
    LotGradingFeeRequest, LotGradingFeeResponse,
    InspectionFeeRequest, InspectionFeeResponse,
    ExtensionFeeRequest, ExtensionFeeResponse,
    # Fee Schedule
    FeeScheduleResponse, FeeScheduleCategory,
)
from .standata import (
    StandataCategory,
    StandataBase, StandataCreate, StandataResponse, StandataSummary,
    StandataSearchResult, StandataSearchQuery, StandataSearchResponse,
    StandataByCodeResponse, StandataStats,
)
