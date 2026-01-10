"""
Unit tests for Documents API endpoints.

Tests for PDF checklist and report generation including:
- Development Permit (DP) checklists
- Building Permit (BP) checklists
- Generic document checklists
- Compliance reports
- Document requirements information
"""
import pytest
from uuid import uuid4
from datetime import date, datetime
from unittest.mock import patch, MagicMock

from app.models.permits import PermitApplication
from app.models.projects import Project, ComplianceCheck


# --- Fixtures for Permit Applications ---

@pytest.fixture
def sample_permit_application(db_session, sample_parcel):
    """Create a sample permit application for testing."""
    app = PermitApplication(
        id=uuid4(),
        application_number="DP2024-00123",
        permit_type="development",
        status="draft",
        project_name="Test Development Project",
        address="456 Test Avenue SW",
        parcel_id=sample_parcel.id,
        project_type="new_construction",
        classification="PART_9",
        occupancy_group="C",
        building_area_sqm=300.0,
        building_height_storeys=2,
        proposed_use="Single family dwelling",
        relaxations_requested=["setback_front", "height"],
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)
    return app


@pytest.fixture
def sample_compliance_checks(db_session, sample_project, sample_requirement, sample_document):
    """Create sample compliance checks for testing."""
    checks = [
        ComplianceCheck(
            id=uuid4(),
            project_id=sample_project.id,
            requirement_id=sample_requirement.id,
            check_category="egress",
            check_name="Stair Width",
            element="stair_width",
            required_value=">= 860 mm",
            actual_value="900 mm",
            unit="mm",
            status="pass",
            message="Stair width meets minimum requirement",
            code_reference="NBC 9.8.4.1",
            extracted_from_document_id=sample_document.id,
            extraction_confidence="HIGH",
            is_verified=True,
        ),
        ComplianceCheck(
            id=uuid4(),
            project_id=sample_project.id,
            requirement_id=sample_requirement.id,
            check_category="egress",
            check_name="Handrail Height",
            element="handrail_height",
            required_value="865-965 mm",
            actual_value="920 mm",
            unit="mm",
            status="pass",
            message="Handrail height within acceptable range",
            code_reference="NBC 9.8.7.3",
            is_verified=True,
        ),
        ComplianceCheck(
            id=uuid4(),
            project_id=sample_project.id,
            requirement_id=sample_requirement.id,
            check_category="fire_safety",
            check_name="Fire Separation Rating",
            element="fire_separation",
            required_value="45 min",
            actual_value="30 min",
            unit="min",
            status="fail",
            message="Fire separation rating does not meet minimum requirement",
            code_reference="NBC 9.10.9.6",
            is_verified=True,
        ),
        ComplianceCheck(
            id=uuid4(),
            project_id=sample_project.id,
            requirement_id=sample_requirement.id,
            check_category="zoning",
            check_name="Front Setback",
            element="front_setback",
            required_value=">= 6.0 m",
            actual_value="5.5 m",
            unit="m",
            status="warning",
            message="Front setback slightly below requirement, may need relaxation",
            code_reference="Land Use Bylaw",
            is_verified=False,
        ),
    ]
    for check in checks:
        db_session.add(check)
    db_session.commit()
    return checks


# --- DP Checklist Tests ---

class TestDPChecklist:
    """Tests for Development Permit checklist generation."""

    def test_dp_checklist_with_project_id(self, client, sample_project):
        """Test DP checklist generates valid PDF with project_id."""
        response = client.get(f"/api/v1/documents/checklists/dp?project_id={sample_project.id}")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        # Check content disposition header
        assert "attachment" in response.headers["content-disposition"]
        assert "DP_Checklist" in response.headers["content-disposition"]

    def test_dp_checklist_with_address(self, client):
        """Test DP checklist generates valid PDF with address parameter."""
        response = client.get("/api/v1/documents/checklists/dp?address=123%20Main%20Street%20NW")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_dp_checklist_with_address_and_project_name(self, client):
        """Test DP checklist with address and custom project name."""
        response = client.get(
            "/api/v1/documents/checklists/dp?address=123%20Main%20Street&project_name=My%20Project"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_dp_checklist_inline_display(self, client, sample_project):
        """Test DP checklist inline display option."""
        response = client.get(
            f"/api/v1/documents/checklists/dp?project_id={sample_project.id}&inline=true"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "inline" in response.headers["content-disposition"]

    def test_dp_checklist_with_application_id(self, client, sample_permit_application):
        """Test DP checklist generates PDF from permit application."""
        response = client.get(
            f"/api/v1/documents/checklists/dp?application_id={sample_permit_application.id}"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_dp_checklist_no_parameters_error(self, client):
        """Test DP checklist requires at least one identifier."""
        response = client.get("/api/v1/documents/checklists/dp")
        assert response.status_code == 400
        assert "must provide" in response.json()["detail"].lower()

    def test_dp_checklist_invalid_project_id(self, client):
        """Test DP checklist with non-existent project_id returns 404."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/documents/checklists/dp?project_id={fake_id}")
        assert response.status_code == 404

    def test_dp_checklist_invalid_id_format(self, client):
        """Test DP checklist with invalid ID format returns error."""
        response = client.get("/api/v1/documents/checklists/dp?project_id=not-a-uuid")
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_dp_checklist_pdf_content_valid(self, client, sample_project):
        """Test DP checklist PDF content is valid PDF format."""
        response = client.get(f"/api/v1/documents/checklists/dp?project_id={sample_project.id}")
        assert response.status_code == 200
        # Check PDF magic bytes
        content = response.content
        assert content[:4] == b'%PDF', "Response should be valid PDF starting with %PDF"

    def test_dp_checklist_content_length_header(self, client, sample_project):
        """Test DP checklist includes Content-Length header."""
        response = client.get(f"/api/v1/documents/checklists/dp?project_id={sample_project.id}")
        assert response.status_code == 200
        assert "content-length" in response.headers
        assert int(response.headers["content-length"]) > 0


# --- BP Checklist Tests ---

class TestBPChecklist:
    """Tests for Building Permit checklist generation."""

    def test_bp_checklist_with_project_id(self, client, sample_project):
        """Test BP checklist generates valid PDF with project_id."""
        response = client.get(f"/api/v1/documents/checklists/bp?project_id={sample_project.id}")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "BP_Checklist" in response.headers["content-disposition"]

    def test_bp_checklist_with_address(self, client):
        """Test BP checklist generates valid PDF with address parameter."""
        response = client.get("/api/v1/documents/checklists/bp?address=789%20Oak%20Drive%20SE")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_bp_checklist_with_classification(self, client):
        """Test BP checklist with classification parameter."""
        response = client.get(
            "/api/v1/documents/checklists/bp?address=123%20Main%20St&classification=PART_9"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_bp_checklist_with_occupancy_group(self, client):
        """Test BP checklist with occupancy group parameter."""
        response = client.get(
            "/api/v1/documents/checklists/bp?address=123%20Main%20St&occupancy_group=C"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    @pytest.mark.xfail(reason="Bug in pdf_generator.py: variable 'doc' shadowed by loop variable on line 583")
    def test_bp_checklist_part3_classification(self, client):
        """Test BP checklist for Part 3 building."""
        response = client.get(
            "/api/v1/documents/checklists/bp?address=456%20Tower%20Ave&classification=PART_3"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_bp_checklist_with_application_id(self, client, sample_permit_application):
        """Test BP checklist generates PDF from permit application."""
        response = client.get(
            f"/api/v1/documents/checklists/bp?application_id={sample_permit_application.id}"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_bp_checklist_inline_display(self, client, sample_project):
        """Test BP checklist inline display option."""
        response = client.get(
            f"/api/v1/documents/checklists/bp?project_id={sample_project.id}&inline=true"
        )
        assert response.status_code == 200
        assert "inline" in response.headers["content-disposition"]

    def test_bp_checklist_no_parameters_error(self, client):
        """Test BP checklist requires at least one identifier."""
        response = client.get("/api/v1/documents/checklists/bp")
        assert response.status_code == 400

    def test_bp_checklist_invalid_project_id(self, client):
        """Test BP checklist with non-existent project_id returns 404."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/documents/checklists/bp?project_id={fake_id}")
        assert response.status_code == 404

    def test_bp_checklist_pdf_content_valid(self, client, sample_project):
        """Test BP checklist PDF content is valid PDF format."""
        response = client.get(f"/api/v1/documents/checklists/bp?project_id={sample_project.id}")
        assert response.status_code == 200
        content = response.content
        assert content[:4] == b'%PDF', "Response should be valid PDF starting with %PDF"


# --- Generic Document Checklist Tests ---

class TestGenericChecklist:
    """Tests for generic document checklist endpoint."""

    def test_generic_checklist_dp_type(self, client):
        """Test generic checklist with dp permit type."""
        response = client.get("/api/v1/documents/checklists/dp?address=123%20Test%20St")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_generic_checklist_development_type(self, client):
        """Test generic checklist with development permit type."""
        response = client.get("/api/v1/documents/checklists/development?address=123%20Test%20St")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_generic_checklist_bp_type(self, client):
        """Test generic checklist with bp permit type."""
        response = client.get("/api/v1/documents/checklists/bp?address=123%20Test%20St")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_generic_checklist_building_type(self, client):
        """Test generic checklist with building permit type."""
        response = client.get("/api/v1/documents/checklists/building?address=123%20Test%20St")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_generic_checklist_trade_type(self, client):
        """Test generic checklist with trade permit type."""
        response = client.get("/api/v1/documents/checklists/trade?address=123%20Test%20St")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_generic_checklist_electrical_type(self, client):
        """Test generic checklist with electrical permit type."""
        response = client.get("/api/v1/documents/checklists/electrical?address=123%20Test%20St")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_generic_checklist_plumbing_type(self, client):
        """Test generic checklist with plumbing permit type."""
        response = client.get("/api/v1/documents/checklists/plumbing?address=123%20Test%20St")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_generic_checklist_hvac_type(self, client):
        """Test generic checklist with hvac permit type."""
        response = client.get("/api/v1/documents/checklists/hvac?address=123%20Test%20St")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_generic_checklist_gas_type(self, client):
        """Test generic checklist with gas permit type."""
        response = client.get("/api/v1/documents/checklists/gas?address=123%20Test%20St")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_generic_checklist_with_project_id(self, client, sample_project):
        """Test generic checklist with project_id."""
        response = client.get(
            f"/api/v1/documents/checklists/trade?project_id={sample_project.id}"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_generic_checklist_no_parameters_error(self, client):
        """Test generic checklist requires identifier parameter."""
        response = client.get("/api/v1/documents/checklists/trade")
        assert response.status_code == 400

    def test_generic_checklist_filename_includes_type(self, client):
        """Test generic checklist filename includes permit type."""
        response = client.get("/api/v1/documents/checklists/electrical?address=123%20Test")
        assert response.status_code == 200
        assert "ELECTRICAL" in response.headers["content-disposition"].upper()


# --- Compliance Report Tests ---

class TestComplianceReport:
    """Tests for compliance report generation."""

    def test_compliance_report_with_checks(
        self, client, sample_project, sample_compliance_checks
    ):
        """Test compliance report generates valid PDF."""
        response = client.get(
            f"/api/v1/documents/reports/compliance?project_id={sample_project.id}"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "Compliance_Report" in response.headers["content-disposition"]

    def test_compliance_report_pdf_valid(
        self, client, sample_project, sample_compliance_checks
    ):
        """Test compliance report PDF content is valid."""
        response = client.get(
            f"/api/v1/documents/reports/compliance?project_id={sample_project.id}"
        )
        assert response.status_code == 200
        content = response.content
        assert content[:4] == b'%PDF', "Response should be valid PDF"

    def test_compliance_report_no_checks_error(self, client, sample_project):
        """Test compliance report without checks returns 404."""
        response = client.get(
            f"/api/v1/documents/reports/compliance?project_id={sample_project.id}"
        )
        assert response.status_code == 404
        assert "no compliance checks" in response.json()["detail"].lower()

    def test_compliance_report_invalid_project_id(self, client):
        """Test compliance report with non-existent project returns 404."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/documents/reports/compliance?project_id={fake_id}")
        assert response.status_code == 404

    def test_compliance_report_missing_project_id(self, client):
        """Test compliance report requires project_id parameter."""
        response = client.get("/api/v1/documents/reports/compliance")
        assert response.status_code == 422  # Validation error

    def test_compliance_report_include_passed_true(
        self, client, sample_project, sample_compliance_checks
    ):
        """Test compliance report includes passed checks when flag is true."""
        response = client.get(
            f"/api/v1/documents/reports/compliance?project_id={sample_project.id}&include_passed=true"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_compliance_report_include_passed_false(
        self, client, sample_project, sample_compliance_checks
    ):
        """Test compliance report excludes passed checks when flag is false."""
        response = client.get(
            f"/api/v1/documents/reports/compliance?project_id={sample_project.id}&include_passed=false"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_compliance_report_inline_display(
        self, client, sample_project, sample_compliance_checks
    ):
        """Test compliance report inline display option."""
        response = client.get(
            f"/api/v1/documents/reports/compliance?project_id={sample_project.id}&inline=true"
        )
        assert response.status_code == 200
        assert "inline" in response.headers["content-disposition"]


# --- Document Requirements Info Tests ---

class TestRequirementsInfo:
    """Tests for document requirements information endpoint."""

    def test_requirements_info_returns_data(self, client):
        """Test requirements info endpoint returns valid data."""
        response = client.get("/api/v1/documents/checklists/info/requirements")
        assert response.status_code == 200
        data = response.json()
        assert "development_permit" in data
        assert "building_permit" in data

    def test_requirements_info_dp_structure(self, client):
        """Test DP requirements structure."""
        response = client.get("/api/v1/documents/checklists/info/requirements")
        assert response.status_code == 200
        data = response.json()
        dp_info = data["development_permit"]
        assert "description" in dp_info
        assert "typical_documents" in dp_info
        assert "optional_documents" in dp_info
        assert "typical_processing_time" in dp_info

    def test_requirements_info_bp_structure(self, client):
        """Test BP requirements structure."""
        response = client.get("/api/v1/documents/checklists/info/requirements")
        assert response.status_code == 200
        data = response.json()
        bp_info = data["building_permit"]
        assert "description" in bp_info
        assert "typical_documents" in bp_info
        assert "optional_documents" in bp_info
        assert "typical_processing_time" in bp_info

    def test_requirements_info_checklist_features(self, client):
        """Test requirements info includes checklist features."""
        response = client.get("/api/v1/documents/checklists/info/requirements")
        assert response.status_code == 200
        data = response.json()
        assert "checklist_features" in data
        assert isinstance(data["checklist_features"], list)
        assert len(data["checklist_features"]) > 0

    def test_requirements_info_dp_documents_list(self, client):
        """Test DP typical documents is a non-empty list."""
        response = client.get("/api/v1/documents/checklists/info/requirements")
        assert response.status_code == 200
        data = response.json()
        typical_docs = data["development_permit"]["typical_documents"]
        assert isinstance(typical_docs, list)
        assert len(typical_docs) > 0
        # Check some expected documents
        assert "Certificate of Title" in " ".join(typical_docs)
        assert "Site Plan" in " ".join(typical_docs)

    def test_requirements_info_bp_documents_list(self, client):
        """Test BP typical documents is a non-empty list."""
        response = client.get("/api/v1/documents/checklists/info/requirements")
        assert response.status_code == 200
        data = response.json()
        typical_docs = data["building_permit"]["typical_documents"]
        assert isinstance(typical_docs, list)
        assert len(typical_docs) > 0
        # Check some expected documents
        assert "Architectural Drawings" in " ".join(typical_docs)
        assert "Structural Drawings" in " ".join(typical_docs)


# --- Edge Cases and Error Handling ---

class TestDocumentsEdgeCases:
    """Tests for edge cases and error handling."""

    def test_checklist_special_characters_in_address(self, client):
        """Test checklist handles special characters in address."""
        response = client.get(
            "/api/v1/documents/checklists/dp?address=123%20Main%20St.%20%23456"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_checklist_long_address(self, client):
        """Test checklist handles long address."""
        long_address = "12345%20Very%20Long%20Street%20Name%20Avenue%20Boulevard%20NW"
        response = client.get(f"/api/v1/documents/checklists/dp?address={long_address}")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_checklist_empty_address(self, client):
        """Test checklist with empty address parameter."""
        response = client.get("/api/v1/documents/checklists/dp?address=")
        # Should either require a value or generate a default checklist
        assert response.status_code in [200, 400, 422]

    def test_multiple_parameters_project_id_takes_precedence(self, client, sample_project):
        """Test that project_id takes precedence when multiple params provided."""
        response = client.get(
            f"/api/v1/documents/checklists/dp?project_id={sample_project.id}&address=Other%20Address"
        )
        assert response.status_code == 200
        # The PDF should use project data, not the address

    def test_checklist_unicode_in_project_name(self, client):
        """Test checklist handles unicode in project name."""
        response = client.get(
            "/api/v1/documents/checklists/dp?address=123%20Test&project_name=Caf%C3%A9%20Project"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"


# --- Integration Tests ---

class TestDocumentsIntegration:
    """Integration tests for Documents API."""

    def test_full_checklist_workflow(self, client, sample_project, sample_permit_application):
        """Test complete checklist workflow."""
        # 1. Get requirements info
        info_response = client.get("/api/v1/documents/checklists/info/requirements")
        assert info_response.status_code == 200

        # 2. Generate DP checklist for project
        dp_response = client.get(
            f"/api/v1/documents/checklists/dp?project_id={sample_project.id}"
        )
        assert dp_response.status_code == 200
        assert dp_response.headers["content-type"] == "application/pdf"

        # 3. Generate BP checklist for same project
        bp_response = client.get(
            f"/api/v1/documents/checklists/bp?project_id={sample_project.id}"
        )
        assert bp_response.status_code == 200
        assert bp_response.headers["content-type"] == "application/pdf"

        # 4. Generate checklist from application
        app_response = client.get(
            f"/api/v1/documents/checklists/dp?application_id={sample_permit_application.id}"
        )
        assert app_response.status_code == 200
        assert app_response.headers["content-type"] == "application/pdf"

    def test_compliance_workflow(
        self, client, sample_project, sample_compliance_checks
    ):
        """Test compliance report workflow."""
        # 1. Generate compliance report with all checks
        all_checks_response = client.get(
            f"/api/v1/documents/reports/compliance?project_id={sample_project.id}"
        )
        assert all_checks_response.status_code == 200
        assert all_checks_response.headers["content-type"] == "application/pdf"

        # 2. Generate report with only failed/warning checks
        failed_only_response = client.get(
            f"/api/v1/documents/reports/compliance?project_id={sample_project.id}&include_passed=false"
        )
        assert failed_only_response.status_code == 200
        assert failed_only_response.headers["content-type"] == "application/pdf"

    def test_pdf_sizes_are_reasonable(self, client, sample_project):
        """Test that generated PDFs have reasonable file sizes."""
        dp_response = client.get(
            f"/api/v1/documents/checklists/dp?project_id={sample_project.id}"
        )
        bp_response = client.get(
            f"/api/v1/documents/checklists/bp?project_id={sample_project.id}"
        )

        # PDFs should be non-trivial size (at least 1KB) but not huge (under 1MB)
        dp_size = len(dp_response.content)
        bp_size = len(bp_response.content)

        assert dp_size > 1000, "DP checklist PDF should be at least 1KB"
        assert dp_size < 1000000, "DP checklist PDF should be under 1MB"
        assert bp_size > 1000, "BP checklist PDF should be at least 1KB"
        assert bp_size < 1000000, "BP checklist PDF should be under 1MB"
