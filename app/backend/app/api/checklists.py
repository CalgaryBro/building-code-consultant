"""
Checklists API - SDAB and DP issue checklists for the Calgary Building Code Expert System.

This module provides:
- SDAB (Subdivision and Development Appeal Board) issue checklists with historical data
- DP (Development Permit) refusal checklists with common rejection reasons
- Risk assessment based on project type
"""
import json
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query

from ..schemas.checklists import (
    SDABIssueSummary, SDABIssueDetail, SDABChecklistResponse,
    SDABMetadata, SDABSummaryStatistics, SDABTypicalOutcomes, SDABCitation,
    DPIssueSummary, DPIssueDetail, DPChecklistResponse,
    DPMetadata, DPSummary, DPSampleCitation,
    RiskAssessmentResponse, RiskIssue, GeneralGuidance,
)

router = APIRouter()

# Data file paths
DATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "analysis"
SDAB_CHECKLIST_PATH = DATA_DIR / "sdab_issues_checklist.json"
DP_CHECKLIST_PATH = DATA_DIR / "dp_refusal_checklist.json"

# Cache for loaded data
_sdab_data_cache = None
_dp_data_cache = None


def _load_sdab_data() -> dict:
    """Load and cache SDAB checklist data."""
    global _sdab_data_cache
    if _sdab_data_cache is None:
        if not SDAB_CHECKLIST_PATH.exists():
            raise HTTPException(
                status_code=503,
                detail=f"SDAB checklist data file not found at {SDAB_CHECKLIST_PATH}"
            )
        with open(SDAB_CHECKLIST_PATH, "r") as f:
            _sdab_data_cache = json.load(f)
    return _sdab_data_cache


def _load_dp_data() -> dict:
    """Load and cache DP refusal checklist data."""
    global _dp_data_cache
    if _dp_data_cache is None:
        if not DP_CHECKLIST_PATH.exists():
            raise HTTPException(
                status_code=503,
                detail=f"DP checklist data file not found at {DP_CHECKLIST_PATH}"
            )
        with open(DP_CHECKLIST_PATH, "r") as f:
            _dp_data_cache = json.load(f)
    return _dp_data_cache


# --- Project Type Mappings ---

PROJECT_TYPE_MAPPINGS = {
    "single_residential": {
        "description": "Single residential property development (single detached dwelling)",
        "sdab_types": ["single_residential", "single_detached_dwelling", "accessory_residential_building",
                       "secondary_suite", "single_detached_dwelling_w/_accessory_residential_building"],
        "dp_categories": ["setback_violation", "height_violation", "accessory_building",
                         "secondary_suite", "coverage_violation", "driveway_access"]
    },
    "multi_residential": {
        "description": "Multi-residential development (apartments, condos, townhouses)",
        "sdab_types": ["multi_residential_development", "multi_residential", "rowhouse_building",
                       "semi_detached_dwelling"],
        "dp_categories": ["setback_violation", "height_violation", "parking_deficiency",
                         "coverage_violation", "other_violations"]
    },
    "commercial": {
        "description": "Commercial property development or change of use",
        "sdab_types": ["commercial", "retail_and_consumer_service", "sign", "mixed_use"],
        "dp_categories": ["signage_issues", "change_of_use", "parking_deficiency", "other_violations"]
    },
    "cannabis": {
        "description": "Cannabis retail establishment",
        "sdab_types": ["cannabis", "cannabis_store"],
        "dp_categories": ["change_of_use", "other_violations"]
    },
    "liquor_store": {
        "description": "Liquor store development",
        "sdab_types": ["liquor_store"],
        "dp_categories": ["change_of_use", "other_violations"]
    },
    "home_occupation": {
        "description": "Home-based business requiring development permit",
        "sdab_types": ["home_occupation"],
        "dp_categories": ["home_occupation", "parking_deficiency"]
    },
    "accessory_building": {
        "description": "Accessory building such as garage suite, laneway home, or garden suite",
        "sdab_types": ["accessory_residential_building", "single_detached_dwelling_w/_accessory_residential_building"],
        "dp_categories": ["accessory_building", "setback_violation", "height_violation", "secondary_suite"]
    },
    "child_care": {
        "description": "Child care or daycare facility",
        "sdab_types": ["child_care_service"],
        "dp_categories": ["change_of_use", "parking_deficiency", "other_violations"]
    },
    "subdivision": {
        "description": "Subdivision of land into smaller parcels",
        "sdab_types": ["subdivision"],
        "dp_categories": ["other_violations"]
    },
    "signage": {
        "description": "Commercial or advertising signage",
        "sdab_types": ["sign"],
        "dp_categories": ["signage_issues"]
    },
    "general": {
        "description": "General development project",
        "sdab_types": ["other"],
        "dp_categories": ["other_violations", "setback_violation", "height_violation"]
    }
}


def _categorize_risk_level(risk_level: str) -> int:
    """Convert risk level to numeric for sorting."""
    levels = {"HIGH": 0, "MEDIUM": 1, "MODERATE": 2, "LOW": 3}
    return levels.get(risk_level, 4)


# --- SDAB Endpoints ---

@router.get("/sdab", response_model=SDABChecklistResponse)
async def list_sdab_issues(
    risk_level: Optional[str] = Query(
        None,
        description="Filter by risk level: HIGH, MEDIUM, MODERATE, LOW"
    ),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of issues to return")
):
    """
    List all SDAB issue types with risk levels.

    Returns a summary of all SDAB issue types analyzed from historical decisions,
    including frequency, success rates, and risk levels.
    """
    data = _load_sdab_data()

    issues = data.get("issues", [])

    # Filter by risk level if specified
    if risk_level:
        risk_level_upper = risk_level.upper()
        issues = [i for i in issues if i.get("risk_level") == risk_level_upper]

    # Sort by frequency (descending) and limit
    issues = sorted(issues, key=lambda x: x.get("frequency", 0), reverse=True)[:limit]

    # Convert to summary format
    issue_summaries = [
        SDABIssueSummary(
            issue_id=issue["issue_id"],
            issue_type=issue["issue_type"],
            display_name=issue["display_name"],
            description=issue["description"],
            frequency=issue["frequency"],
            risk_level=issue["risk_level"],
            success_rate_percent=issue["success_rate_percent"]
        )
        for issue in issues
    ]

    return SDABChecklistResponse(
        metadata=SDABMetadata(**data["metadata"]),
        summary_statistics=SDABSummaryStatistics(**data["summary_statistics"]),
        issues=issue_summaries
    )


@router.get("/sdab/{issue_id}", response_model=SDABIssueDetail)
async def get_sdab_issue_detail(issue_id: str):
    """
    Get detailed information for a specific SDAB issue type.

    Includes key factors for approval/denial, sample citations from historical
    decisions, and recommendations for success.
    """
    data = _load_sdab_data()

    # Find the issue by ID
    issue = None
    for i in data.get("issues", []):
        if i["issue_id"].upper() == issue_id.upper():
            issue = i
            break

    if not issue:
        raise HTTPException(
            status_code=404,
            detail=f"SDAB issue '{issue_id}' not found"
        )

    # Parse typical outcomes
    outcomes = issue.get("typical_outcomes", {})
    typical_outcomes = SDABTypicalOutcomes(
        allowed=outcomes.get("allowed", 0),
        denied=outcomes.get("denied", 0),
        allowed_in_part=outcomes.get("allowed_in_part", 0),
        withdrawn=outcomes.get("withdrawn", 0),
        struck=outcomes.get("struck", 0)
    )

    # Parse citations
    citations = [
        SDABCitation(**citation)
        for citation in issue.get("sample_citations", [])
    ]

    return SDABIssueDetail(
        issue_id=issue["issue_id"],
        issue_type=issue["issue_type"],
        display_name=issue["display_name"],
        description=issue["description"],
        frequency=issue["frequency"],
        risk_level=issue["risk_level"],
        success_rate_percent=issue["success_rate_percent"],
        typical_outcomes=typical_outcomes,
        common_property_types=issue.get("common_property_types", {}),
        key_factors_for_approval=issue.get("key_factors_for_approval", []),
        key_factors_for_denial=issue.get("key_factors_for_denial", []),
        sample_citations=citations,
        recommendation=issue.get("recommendation", "")
    )


@router.get("/sdab/guidance/general", response_model=GeneralGuidance)
async def get_sdab_general_guidance():
    """
    Get general guidance from SDAB historical analysis.

    Includes appeal success factors, common denial reasons, preparation tips,
    and year-over-year trend information.
    """
    data = _load_sdab_data()
    guidance = data.get("general_guidance", {})

    if not guidance:
        raise HTTPException(
            status_code=404,
            detail="General guidance not available"
        )

    return GeneralGuidance(**guidance)


# --- DP Refusal Endpoints ---

@router.get("/dp", response_model=DPChecklistResponse)
async def list_dp_issues(
    zone: Optional[str] = Query(
        None,
        description="Filter by affected zone (e.g., R-1, DC, C-3)"
    ),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of issues to return")
):
    """
    List all DP (Development Permit) refusal categories.

    Returns a summary of common reasons for development permit refusals,
    based on historical permit data analysis.
    """
    data = _load_dp_data()

    items = data.get("checklist_items", [])

    # Filter by zone if specified
    if zone:
        zone_upper = zone.upper()
        items = [
            item for item in items
            if any(zone_upper in z.upper() for z in item.get("common_zones_affected", []))
        ]

    # Sort by frequency (descending) and limit
    items = sorted(items, key=lambda x: x.get("frequency", 0), reverse=True)[:limit]

    # Convert to summary format
    item_summaries = [
        DPIssueSummary(
            issue_id=item["issue_id"],
            issue_category=item["issue_category"],
            description=item["description"],
            frequency=item["frequency"],
            typical_deficiency=item["typical_deficiency"]
        )
        for item in items
    ]

    return DPChecklistResponse(
        metadata=DPMetadata(**data["metadata"]),
        summary=DPSummary(**data["summary"]),
        checklist_items=item_summaries
    )


@router.get("/dp/{issue_id}", response_model=DPIssueDetail)
async def get_dp_issue_detail(issue_id: str):
    """
    Get detailed information for a specific DP refusal category.

    Includes code references, sample citations, and prevention tips.
    """
    data = _load_dp_data()

    # Find the issue by ID
    issue = None
    for item in data.get("checklist_items", []):
        if item["issue_id"].upper() == issue_id.upper():
            issue = item
            break

    if not issue:
        raise HTTPException(
            status_code=404,
            detail=f"DP issue '{issue_id}' not found"
        )

    # Parse citations
    citations = [
        DPSampleCitation(**citation)
        for citation in issue.get("sample_citations", [])
    ]

    return DPIssueDetail(
        issue_id=issue["issue_id"],
        issue_category=issue["issue_category"],
        description=issue["description"],
        frequency=issue["frequency"],
        common_zones_affected=issue.get("common_zones_affected", []),
        typical_deficiency=issue["typical_deficiency"],
        code_references=issue.get("code_references", []),
        sample_citations=citations,
        prevention_tips=issue.get("prevention_tips", []),
        relaxation_success_rate=issue.get("relaxation_success_rate")
    )


# --- Risk Assessment Endpoint ---

@router.get("/risk-assessment", response_model=RiskAssessmentResponse)
async def get_risk_assessment(
    project_type: str = Query(
        ...,
        description="Project type: single_residential, multi_residential, commercial, cannabis, "
                    "liquor_store, home_occupation, accessory_building, child_care, subdivision, "
                    "signage, general"
    )
):
    """
    Get relevant issues for a specific project type.

    Provides a risk assessment based on historical SDAB decisions and DP refusals
    relevant to the specified project type. Issues are categorized by risk level.
    """
    project_type_lower = project_type.lower()

    if project_type_lower not in PROJECT_TYPE_MAPPINGS:
        available = ", ".join(sorted(PROJECT_TYPE_MAPPINGS.keys()))
        raise HTTPException(
            status_code=400,
            detail=f"Unknown project type '{project_type}'. Available types: {available}"
        )

    mapping = PROJECT_TYPE_MAPPINGS[project_type_lower]
    sdab_data = _load_sdab_data()
    dp_data = _load_dp_data()

    # Collect relevant SDAB issues
    relevant_issues: List[RiskIssue] = []

    for issue in sdab_data.get("issues", []):
        if issue["issue_type"] in mapping["sdab_types"]:
            relevant_issues.append(RiskIssue(
                source="sdab",
                issue_id=issue["issue_id"],
                issue_type=issue["issue_type"],
                display_name=issue["display_name"],
                description=issue["description"],
                frequency=issue["frequency"],
                risk_level=issue["risk_level"],
                success_rate_percent=issue["success_rate_percent"],
                key_factors_for_approval=issue.get("key_factors_for_approval"),
                key_factors_for_denial=issue.get("key_factors_for_denial"),
                recommendation=issue.get("recommendation")
            ))

    # Collect relevant DP issues and assign risk levels based on frequency
    for item in dp_data.get("checklist_items", []):
        if item["issue_category"] in mapping["dp_categories"]:
            # Assign risk level based on frequency
            freq = item["frequency"]
            if freq >= 400:
                risk_level = "HIGH"
            elif freq >= 200:
                risk_level = "MEDIUM"
            elif freq >= 100:
                risk_level = "MODERATE"
            else:
                risk_level = "LOW"

            relevant_issues.append(RiskIssue(
                source="dp",
                issue_id=item["issue_id"],
                issue_type=item["issue_category"],
                display_name=item["issue_category"].replace("_", " ").title(),
                description=item["description"],
                frequency=item["frequency"],
                risk_level=risk_level,
                prevention_tips=item.get("prevention_tips")
            ))

    # Sort by risk level and frequency
    relevant_issues.sort(key=lambda x: (_categorize_risk_level(x.risk_level), -x.frequency))

    # Categorize by risk level
    high_risk = [i for i in relevant_issues if i.risk_level == "HIGH"]
    medium_risk = [i for i in relevant_issues if i.risk_level == "MEDIUM"]
    moderate_risk = [i for i in relevant_issues if i.risk_level == "MODERATE"]
    low_risk = [i for i in relevant_issues if i.risk_level == "LOW"]

    # Get general guidance
    general_guidance = sdab_data.get("general_guidance", {})

    return RiskAssessmentResponse(
        project_type=project_type_lower,
        project_type_description=mapping["description"],
        total_relevant_issues=len(relevant_issues),
        high_risk_issues=high_risk,
        medium_risk_issues=medium_risk,
        moderate_risk_issues=moderate_risk,
        low_risk_issues=low_risk,
        general_guidance=general_guidance
    )
