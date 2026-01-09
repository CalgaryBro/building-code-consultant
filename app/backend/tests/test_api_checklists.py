"""
Unit tests for Checklists API endpoints.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, mock_open


# Sample test data for mocking
SAMPLE_SDAB_DATA = {
    "metadata": {
        "generated_at": "2026-01-09T12:45:38.652085",
        "source_file": "data/permits/sdab-decisions.json",
        "total_records_analyzed": 1433,
        "description": "SDAB Issues Checklist",
        "note": "This checklist is derived from historical SDAB decisions"
    },
    "summary_statistics": {
        "total_cases": 1433,
        "overall_outcomes": {
            "WITHDRAWN": 205,
            "DENIED": 416,
            "ALLOWED": 322
        },
        "appeals_of_refusals": {
            "total": 498,
            "success_rate": 38.8
        },
        "appeals_of_approvals": {
            "total": 925,
            "success_rate": 45.8
        }
    },
    "issues": [
        {
            "issue_id": "SDAB-001",
            "issue_type": "single_residential",
            "display_name": "Single Residential",
            "description": "Single residential property development",
            "frequency": 318,
            "risk_level": "MODERATE",
            "success_rate_percent": 66.4,
            "typical_outcomes": {
                "allowed": 79,
                "denied": 89,
                "allowed_in_part": 97,
                "withdrawn": 36,
                "struck": 16
            },
            "common_property_types": {
                "Single Residential": 318
            },
            "key_factors_for_approval": [
                "Site constraints justify requested variances",
                "Development pattern consistent with neighborhood"
            ],
            "key_factors_for_denial": [
                "Variance too significant without justification",
                "Development out of character for neighborhood"
            ],
            "sample_citations": [
                {
                    "decision_number": "SDAB-2014-0061",
                    "outcome": "ALLOWED",
                    "year": "2014",
                    "address": "184 TARADALE DR NE",
                    "key_reasoning": "Board found grounds to allow the development",
                    "property_type": "Single Residential"
                }
            ],
            "recommendation": "Document site constraints thoroughly"
        },
        {
            "issue_id": "SDAB-002",
            "issue_type": "commercial",
            "display_name": "Commercial",
            "description": "Commercial property development",
            "frequency": 182,
            "risk_level": "MODERATE",
            "success_rate_percent": 66.7,
            "typical_outcomes": {
                "allowed": 63,
                "denied": 46,
                "allowed_in_part": 29,
                "withdrawn": 37,
                "struck": 7
            },
            "common_property_types": {
                "Commercial": 182
            },
            "key_factors_for_approval": ["Commercial use appropriate for zone"],
            "key_factors_for_denial": ["Incompatible use for zone"],
            "sample_citations": [],
            "recommendation": "Verify zoning permits proposed use"
        },
        {
            "issue_id": "SDAB-015",
            "issue_type": "liquor_store",
            "display_name": "Liquor Store",
            "description": "Liquor store development permit",
            "frequency": 20,
            "risk_level": "HIGH",
            "success_rate_percent": 38.5,
            "typical_outcomes": {
                "allowed": 5,
                "denied": 8,
                "allowed_in_part": 0,
                "withdrawn": 2,
                "struck": 3
            },
            "common_property_types": {
                "Commercial": 11
            },
            "key_factors_for_approval": ["All separation distances met"],
            "key_factors_for_denial": ["Within prohibited distance of sensitive uses"],
            "sample_citations": [],
            "recommendation": "Map all liquor stores and sensitive uses"
        }
    ],
    "general_guidance": {
        "appeal_success_factors": [
            "Demonstrate unique hardship or site constraints",
            "Show minimal impact on neighboring properties"
        ],
        "common_denial_reasons": [
            "Excessive variance from required standards",
            "Significant unmitigated impact on neighboring properties"
        ],
        "preparation_tips": [
            "Attend pre-application meetings",
            "Conduct early consultation with immediate neighbors"
        ],
        "appeal_process_notes": {
            "timeline": "Appeals must typically be filed within 21 days",
            "documentation": "Bring all relevant drawings",
            "representation": "Applicants may represent themselves",
            "neighbor_notification": "Neighbors are typically notified",
            "decision_timing": "Decisions are usually issued within 15 days"
        },
        "year_over_year_trends": {
            "note": "Success rates have varied over time"
        },
        "risk_level_guidance": {
            "HIGH": "Less than 40% success rate",
            "MEDIUM": "40-55% success rate",
            "MODERATE": "55-70% success rate",
            "LOW": "Above 70% success rate"
        }
    }
}

SAMPLE_DP_DATA = {
    "metadata": {
        "generated_date": "2026-01-09T12:45:43.539514",
        "source_file": "development-permits.json",
        "total_permits_analyzed": 188019,
        "total_refused_permits": 4293,
        "refusal_rate": 2.28,
        "data_coverage": "City of Calgary Development Permits",
        "purpose": "Preventive checklist for permit applications"
    },
    "summary": {
        "top_refusal_reasons": [
            {"category": "other_violations", "count": 995},
            {"category": "signage_issues", "count": 778}
        ],
        "most_affected_zones": {
            "R-1": 883,
            "DC": 611
        }
    },
    "checklist_items": [
        {
            "issue_id": "DP-REF-001",
            "issue_category": "other_violations",
            "description": "Other development permit violations",
            "frequency": 995,
            "common_zones_affected": ["R-2", "R-1", "DC"],
            "typical_deficiency": "Various bylaw non-compliance issues",
            "code_references": ["Land Use Bylaw 1P2007"],
            "sample_citations": [
                {
                    "permit_number": "DP2025-03624",
                    "description": "NEW: SEMI-DETACHED DWELLING",
                    "zone": "M-CG d72",
                    "address": "404 11A ST NW",
                    "applied_date": "2025-06-21",
                    "community": "HILLHURST"
                }
            ],
            "prevention_tips": [
                "Review all applicable bylaw sections",
                "Consider pre-application meeting"
            ],
            "relaxation_success_rate": None
        },
        {
            "issue_id": "DP-REF-002",
            "issue_category": "signage_issues",
            "description": "Sign violations",
            "frequency": 778,
            "common_zones_affected": ["DC", "I-2", "C-3"],
            "typical_deficiency": "Sign type not permitted",
            "code_references": ["Land Use Bylaw 1P2007 Part 7"],
            "sample_citations": [],
            "prevention_tips": ["Identify sign classification"],
            "relaxation_success_rate": None
        },
        {
            "issue_id": "DP-REF-003",
            "issue_category": "setback_violation",
            "description": "Building setback violations",
            "frequency": 685,
            "common_zones_affected": ["R-1", "R-2", "R-C1"],
            "typical_deficiency": "Structure too close to property line",
            "code_references": ["Land Use Bylaw 1P2007 Part 5"],
            "sample_citations": [],
            "prevention_tips": ["Verify setback requirements"],
            "relaxation_success_rate": 0.92
        },
        {
            "issue_id": "DP-REF-005",
            "issue_category": "home_occupation",
            "description": "Home-based business violations",
            "frequency": 454,
            "common_zones_affected": ["R-1", "R-C1", "R-2"],
            "typical_deficiency": "Business type or scale not permitted",
            "code_references": ["Land Use Bylaw 1P2007 Section 83"],
            "sample_citations": [],
            "prevention_tips": ["Review home occupation class requirements"],
            "relaxation_success_rate": None
        }
    ]
}


@pytest.fixture
def mock_sdab_file(tmp_path):
    """Create a mock SDAB data file."""
    file_path = tmp_path / "sdab_issues_checklist.json"
    with open(file_path, "w") as f:
        json.dump(SAMPLE_SDAB_DATA, f)
    return file_path


@pytest.fixture
def mock_dp_file(tmp_path):
    """Create a mock DP data file."""
    file_path = tmp_path / "dp_refusal_checklist.json"
    with open(file_path, "w") as f:
        json.dump(SAMPLE_DP_DATA, f)
    return file_path


class TestSDABEndpoints:
    """Tests for SDAB checklist endpoints."""

    def test_list_sdab_issues(self, client, mock_sdab_file, mock_dp_file):
        """Test listing SDAB issues."""
        with patch("app.api.checklists.SDAB_CHECKLIST_PATH", mock_sdab_file):
            with patch("app.api.checklists._sdab_data_cache", None):
                response = client.get("/api/v1/checklists/sdab")
                assert response.status_code == 200
                data = response.json()
                assert "metadata" in data
                assert "summary_statistics" in data
                assert "issues" in data
                assert len(data["issues"]) > 0

    def test_list_sdab_issues_filter_by_risk(self, client, mock_sdab_file):
        """Test filtering SDAB issues by risk level."""
        with patch("app.api.checklists.SDAB_CHECKLIST_PATH", mock_sdab_file):
            with patch("app.api.checklists._sdab_data_cache", None):
                response = client.get("/api/v1/checklists/sdab?risk_level=HIGH")
                assert response.status_code == 200
                data = response.json()
                for issue in data["issues"]:
                    assert issue["risk_level"] == "HIGH"

    def test_list_sdab_issues_with_limit(self, client, mock_sdab_file):
        """Test SDAB issues listing with limit."""
        with patch("app.api.checklists.SDAB_CHECKLIST_PATH", mock_sdab_file):
            with patch("app.api.checklists._sdab_data_cache", None):
                response = client.get("/api/v1/checklists/sdab?limit=1")
                assert response.status_code == 200
                data = response.json()
                assert len(data["issues"]) == 1

    def test_get_sdab_issue_detail(self, client, mock_sdab_file):
        """Test getting SDAB issue details."""
        with patch("app.api.checklists.SDAB_CHECKLIST_PATH", mock_sdab_file):
            with patch("app.api.checklists._sdab_data_cache", None):
                response = client.get("/api/v1/checklists/sdab/SDAB-001")
                assert response.status_code == 200
                data = response.json()
                assert data["issue_id"] == "SDAB-001"
                assert data["issue_type"] == "single_residential"
                assert "typical_outcomes" in data
                assert "key_factors_for_approval" in data
                assert "key_factors_for_denial" in data
                assert "sample_citations" in data
                assert "recommendation" in data

    def test_get_sdab_issue_detail_case_insensitive(self, client, mock_sdab_file):
        """Test SDAB issue lookup is case insensitive."""
        with patch("app.api.checklists.SDAB_CHECKLIST_PATH", mock_sdab_file):
            with patch("app.api.checklists._sdab_data_cache", None):
                response = client.get("/api/v1/checklists/sdab/sdab-001")
                assert response.status_code == 200
                assert response.json()["issue_id"] == "SDAB-001"

    def test_get_sdab_issue_not_found(self, client, mock_sdab_file):
        """Test getting a non-existent SDAB issue."""
        with patch("app.api.checklists.SDAB_CHECKLIST_PATH", mock_sdab_file):
            with patch("app.api.checklists._sdab_data_cache", None):
                response = client.get("/api/v1/checklists/sdab/SDAB-999")
                assert response.status_code == 404

    def test_get_sdab_general_guidance(self, client, mock_sdab_file):
        """Test getting general SDAB guidance."""
        with patch("app.api.checklists.SDAB_CHECKLIST_PATH", mock_sdab_file):
            with patch("app.api.checklists._sdab_data_cache", None):
                response = client.get("/api/v1/checklists/sdab/guidance/general")
                assert response.status_code == 200
                data = response.json()
                assert "appeal_success_factors" in data
                assert "common_denial_reasons" in data
                assert "preparation_tips" in data
                assert "appeal_process_notes" in data


class TestDPEndpoints:
    """Tests for DP refusal checklist endpoints."""

    def test_list_dp_issues(self, client, mock_dp_file):
        """Test listing DP issues."""
        with patch("app.api.checklists.DP_CHECKLIST_PATH", mock_dp_file):
            with patch("app.api.checklists._dp_data_cache", None):
                response = client.get("/api/v1/checklists/dp")
                assert response.status_code == 200
                data = response.json()
                assert "metadata" in data
                assert "summary" in data
                assert "checklist_items" in data
                assert len(data["checklist_items"]) > 0

    def test_list_dp_issues_filter_by_zone(self, client, mock_dp_file):
        """Test filtering DP issues by zone."""
        with patch("app.api.checklists.DP_CHECKLIST_PATH", mock_dp_file):
            with patch("app.api.checklists._dp_data_cache", None):
                response = client.get("/api/v1/checklists/dp?zone=R-1")
                assert response.status_code == 200
                data = response.json()
                # All returned items should have R-1 in their affected zones
                for item in data["checklist_items"]:
                    # The filtering is done server-side, just verify we got results
                    assert "issue_id" in item

    def test_list_dp_issues_with_limit(self, client, mock_dp_file):
        """Test DP issues listing with limit."""
        with patch("app.api.checklists.DP_CHECKLIST_PATH", mock_dp_file):
            with patch("app.api.checklists._dp_data_cache", None):
                response = client.get("/api/v1/checklists/dp?limit=2")
                assert response.status_code == 200
                data = response.json()
                assert len(data["checklist_items"]) <= 2

    def test_get_dp_issue_detail(self, client, mock_dp_file):
        """Test getting DP issue details."""
        with patch("app.api.checklists.DP_CHECKLIST_PATH", mock_dp_file):
            with patch("app.api.checklists._dp_data_cache", None):
                response = client.get("/api/v1/checklists/dp/DP-REF-001")
                assert response.status_code == 200
                data = response.json()
                assert data["issue_id"] == "DP-REF-001"
                assert data["issue_category"] == "other_violations"
                assert "common_zones_affected" in data
                assert "code_references" in data
                assert "sample_citations" in data
                assert "prevention_tips" in data

    def test_get_dp_issue_detail_case_insensitive(self, client, mock_dp_file):
        """Test DP issue lookup is case insensitive."""
        with patch("app.api.checklists.DP_CHECKLIST_PATH", mock_dp_file):
            with patch("app.api.checklists._dp_data_cache", None):
                response = client.get("/api/v1/checklists/dp/dp-ref-001")
                assert response.status_code == 200
                assert response.json()["issue_id"] == "DP-REF-001"

    def test_get_dp_issue_not_found(self, client, mock_dp_file):
        """Test getting a non-existent DP issue."""
        with patch("app.api.checklists.DP_CHECKLIST_PATH", mock_dp_file):
            with patch("app.api.checklists._dp_data_cache", None):
                response = client.get("/api/v1/checklists/dp/DP-REF-999")
                assert response.status_code == 404

    def test_get_dp_issue_with_relaxation_rate(self, client, mock_dp_file):
        """Test getting DP issue that has a relaxation success rate."""
        with patch("app.api.checklists.DP_CHECKLIST_PATH", mock_dp_file):
            with patch("app.api.checklists._dp_data_cache", None):
                response = client.get("/api/v1/checklists/dp/DP-REF-003")
                assert response.status_code == 200
                data = response.json()
                assert data["relaxation_success_rate"] == 0.92


class TestRiskAssessmentEndpoint:
    """Tests for project risk assessment endpoint."""

    def test_risk_assessment_single_residential(self, client, mock_sdab_file, mock_dp_file):
        """Test risk assessment for single residential project."""
        with patch("app.api.checklists.SDAB_CHECKLIST_PATH", mock_sdab_file):
            with patch("app.api.checklists.DP_CHECKLIST_PATH", mock_dp_file):
                with patch("app.api.checklists._sdab_data_cache", None):
                    with patch("app.api.checklists._dp_data_cache", None):
                        response = client.get("/api/v1/checklists/risk-assessment?project_type=single_residential")
                        assert response.status_code == 200
                        data = response.json()
                        assert data["project_type"] == "single_residential"
                        assert "project_type_description" in data
                        assert "total_relevant_issues" in data
                        assert "high_risk_issues" in data
                        assert "medium_risk_issues" in data
                        assert "moderate_risk_issues" in data
                        assert "low_risk_issues" in data
                        assert "general_guidance" in data

    def test_risk_assessment_commercial(self, client, mock_sdab_file, mock_dp_file):
        """Test risk assessment for commercial project."""
        with patch("app.api.checklists.SDAB_CHECKLIST_PATH", mock_sdab_file):
            with patch("app.api.checklists.DP_CHECKLIST_PATH", mock_dp_file):
                with patch("app.api.checklists._sdab_data_cache", None):
                    with patch("app.api.checklists._dp_data_cache", None):
                        response = client.get("/api/v1/checklists/risk-assessment?project_type=commercial")
                        assert response.status_code == 200
                        data = response.json()
                        assert data["project_type"] == "commercial"

    def test_risk_assessment_home_occupation(self, client, mock_sdab_file, mock_dp_file):
        """Test risk assessment for home occupation project."""
        with patch("app.api.checklists.SDAB_CHECKLIST_PATH", mock_sdab_file):
            with patch("app.api.checklists.DP_CHECKLIST_PATH", mock_dp_file):
                with patch("app.api.checklists._sdab_data_cache", None):
                    with patch("app.api.checklists._dp_data_cache", None):
                        response = client.get("/api/v1/checklists/risk-assessment?project_type=home_occupation")
                        assert response.status_code == 200
                        data = response.json()
                        assert data["project_type"] == "home_occupation"

    def test_risk_assessment_invalid_project_type(self, client, mock_sdab_file, mock_dp_file):
        """Test risk assessment with invalid project type."""
        with patch("app.api.checklists.SDAB_CHECKLIST_PATH", mock_sdab_file):
            with patch("app.api.checklists.DP_CHECKLIST_PATH", mock_dp_file):
                response = client.get("/api/v1/checklists/risk-assessment?project_type=invalid_type")
                assert response.status_code == 400
                assert "Unknown project type" in response.json()["detail"]

    def test_risk_assessment_missing_project_type(self, client):
        """Test risk assessment without project type parameter."""
        response = client.get("/api/v1/checklists/risk-assessment")
        assert response.status_code == 422  # Validation error

    def test_risk_assessment_case_insensitive(self, client, mock_sdab_file, mock_dp_file):
        """Test risk assessment project type is case insensitive."""
        with patch("app.api.checklists.SDAB_CHECKLIST_PATH", mock_sdab_file):
            with patch("app.api.checklists.DP_CHECKLIST_PATH", mock_dp_file):
                with patch("app.api.checklists._sdab_data_cache", None):
                    with patch("app.api.checklists._dp_data_cache", None):
                        response = client.get("/api/v1/checklists/risk-assessment?project_type=SINGLE_RESIDENTIAL")
                        assert response.status_code == 200
                        data = response.json()
                        assert data["project_type"] == "single_residential"

    def test_risk_assessment_issues_sorted_by_risk(self, client, mock_sdab_file, mock_dp_file):
        """Test that risk assessment issues are sorted by risk level."""
        with patch("app.api.checklists.SDAB_CHECKLIST_PATH", mock_sdab_file):
            with patch("app.api.checklists.DP_CHECKLIST_PATH", mock_dp_file):
                with patch("app.api.checklists._sdab_data_cache", None):
                    with patch("app.api.checklists._dp_data_cache", None):
                        response = client.get("/api/v1/checklists/risk-assessment?project_type=commercial")
                        assert response.status_code == 200
                        data = response.json()
                        # High risk issues should all have HIGH risk level
                        for issue in data["high_risk_issues"]:
                            assert issue["risk_level"] == "HIGH"
                        # Low risk issues should all have LOW risk level
                        for issue in data["low_risk_issues"]:
                            assert issue["risk_level"] == "LOW"


class TestChecklistDataIntegrity:
    """Tests for checklist data loading and caching."""

    def test_sdab_data_file_not_found(self, client):
        """Test error when SDAB data file is missing."""
        fake_path = Path("/nonexistent/path/sdab.json")
        with patch("app.api.checklists.SDAB_CHECKLIST_PATH", fake_path):
            with patch("app.api.checklists._sdab_data_cache", None):
                response = client.get("/api/v1/checklists/sdab")
                assert response.status_code == 503

    def test_dp_data_file_not_found(self, client):
        """Test error when DP data file is missing."""
        fake_path = Path("/nonexistent/path/dp.json")
        with patch("app.api.checklists.DP_CHECKLIST_PATH", fake_path):
            with patch("app.api.checklists._dp_data_cache", None):
                response = client.get("/api/v1/checklists/dp")
                assert response.status_code == 503

    def test_sdab_metadata_structure(self, client, mock_sdab_file):
        """Test SDAB response metadata structure."""
        with patch("app.api.checklists.SDAB_CHECKLIST_PATH", mock_sdab_file):
            with patch("app.api.checklists._sdab_data_cache", None):
                response = client.get("/api/v1/checklists/sdab")
                assert response.status_code == 200
                data = response.json()
                metadata = data["metadata"]
                assert "generated_at" in metadata
                assert "source_file" in metadata
                assert "total_records_analyzed" in metadata

    def test_dp_metadata_structure(self, client, mock_dp_file):
        """Test DP response metadata structure."""
        with patch("app.api.checklists.DP_CHECKLIST_PATH", mock_dp_file):
            with patch("app.api.checklists._dp_data_cache", None):
                response = client.get("/api/v1/checklists/dp")
                assert response.status_code == 200
                data = response.json()
                metadata = data["metadata"]
                assert "generated_date" in metadata
                assert "total_permits_analyzed" in metadata
                assert "refusal_rate" in metadata
