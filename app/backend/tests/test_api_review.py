"""
Unit tests for REVIEW mode API endpoints.
"""
import pytest
from uuid import uuid4
from io import BytesIO


class TestDocumentUploadEndpoints:
    """Tests for document upload endpoints."""

    def test_upload_document_pdf(self, client, sample_project):
        """Test uploading a PDF document."""
        # Create a fake PDF file
        pdf_content = b"%PDF-1.4 fake pdf content"
        files = {"file": ("test.pdf", BytesIO(pdf_content), "application/pdf")}
        data = {"document_type": "floor_plan"}

        response = client.post(
            f"/api/v1/review/projects/{sample_project.id}/documents",
            files=files,
            data=data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["document_type"] == "floor_plan"
        assert data["extraction_status"] == "pending"

    def test_upload_document_image(self, client, sample_project):
        """Test uploading an image document."""
        # Create a minimal PNG file (8x8 pixels)
        png_header = b'\x89PNG\r\n\x1a\n'
        png_content = png_header + b'\x00' * 100  # Simplified
        files = {"file": ("plan.png", BytesIO(png_content), "image/png")}

        response = client.post(
            f"/api/v1/review/projects/{sample_project.id}/documents",
            files=files
        )
        assert response.status_code == 200
        data = response.json()
        assert data["file_type"] == "image"

    def test_upload_document_invalid_type(self, client, sample_project):
        """Test uploading unsupported file type."""
        files = {"file": ("test.txt", BytesIO(b"text content"), "text/plain")}

        response = client.post(
            f"/api/v1/review/projects/{sample_project.id}/documents",
            files=files
        )
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"]

    def test_upload_document_project_not_found(self, client):
        """Test uploading to non-existent project."""
        fake_id = uuid4()
        files = {"file": ("test.pdf", BytesIO(b"%PDF-1.4"), "application/pdf")}

        response = client.post(
            f"/api/v1/review/projects/{fake_id}/documents",
            files=files
        )
        assert response.status_code == 404

    def test_list_documents_empty(self, client, sample_project):
        """Test listing documents when empty."""
        response = client.get(f"/api/v1/review/projects/{sample_project.id}/documents")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_documents_with_data(self, client, sample_project, sample_document):
        """Test listing documents with data."""
        response = client.get(f"/api/v1/review/projects/{sample_project.id}/documents")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["filename"] == "floor-plan.pdf"

    def test_list_documents_project_not_found(self, client):
        """Test listing documents for non-existent project."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/review/projects/{fake_id}/documents")
        assert response.status_code == 404


class TestExtractionEndpoints:
    """Tests for document extraction endpoints."""

    def test_extract_from_document(self, client, sample_document):
        """Test starting extraction from a document."""
        response = client.post(f"/api/v1/review/documents/{sample_document.id}/extract")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert "check_status_at" in data

    def test_extract_document_not_found(self, client):
        """Test extraction from non-existent document."""
        fake_id = uuid4()
        response = client.post(f"/api/v1/review/documents/{fake_id}/extract")
        assert response.status_code == 404

    def test_extract_already_processing(self, client, db_session, sample_document):
        """Test extraction when already processing."""
        sample_document.extraction_status = "processing"
        db_session.commit()

        response = client.post(f"/api/v1/review/documents/{sample_document.id}/extract")
        assert response.status_code == 400
        assert "already in progress" in response.json()["detail"]

    def test_get_extraction_status(self, client, sample_document):
        """Test getting extraction status."""
        response = client.get(f"/api/v1/review/documents/{sample_document.id}/extraction-status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["extracted_values_count"] >= 0

    def test_get_extraction_status_not_found(self, client):
        """Test getting status for non-existent document."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/review/documents/{fake_id}/extraction-status")
        assert response.status_code == 404


class TestExtractedDataEndpoints:
    """Tests for extracted data endpoints."""

    def test_get_extracted_data(self, client, sample_document, sample_extracted_data):
        """Test getting extracted data for a document."""
        response = client.get(f"/api/v1/review/documents/{sample_document.id}/extracted")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["field_name"] == "stair_width"

    def test_get_extracted_data_verified_only(self, client, db_session, sample_document, sample_extracted_data):
        """Test filtering to verified data only."""
        # First get all - should include unverified
        response = client.get(f"/api/v1/review/documents/{sample_document.id}/extracted")
        all_data = response.json()

        # Verify some data
        sample_extracted_data.is_verified = True
        db_session.commit()

        # Get verified only
        response = client.get(f"/api/v1/review/documents/{sample_document.id}/extracted?verified_only=true")
        verified_data = response.json()
        assert all(d["is_verified"] for d in verified_data)

    def test_verify_extracted_data(self, client, sample_extracted_data):
        """Test verifying extracted data."""
        response = client.put(
            f"/api/v1/review/extracted/{sample_extracted_data.id}/verify",
            json={
                "verified_value": "920",
                "verified_by": "Test Engineer",
                "verification_notes": "Measured on site"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_verified"] is True
        assert data["verified_value"] == "920"
        assert data["verified_by"] == "Test Engineer"

    def test_verify_extracted_not_found(self, client):
        """Test verifying non-existent extracted data."""
        fake_id = uuid4()
        response = client.put(
            f"/api/v1/review/extracted/{fake_id}/verify",
            json={
                "verified_value": "900",
                "verified_by": "Test"
            }
        )
        assert response.status_code == 404


class TestComplianceCheckEndpoints:
    """Tests for compliance check endpoints."""

    def test_run_compliance_checks(self, client, sample_project, sample_document, sample_extracted_data, sample_requirement, db_session):
        """Test running compliance checks."""
        # Verify the extracted data first
        sample_extracted_data.is_verified = True
        sample_extracted_data.verified_value = "900"
        db_session.commit()

        response = client.post(f"/api/v1/review/projects/{sample_project.id}/run-checks")
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "total_checks" in data
        assert "passed" in data
        assert "failed" in data

    def test_run_compliance_checks_no_extracted_data(self, client, sample_project):
        """Test running checks with no extracted data."""
        response = client.post(f"/api/v1/review/projects/{sample_project.id}/run-checks")
        assert response.status_code == 200
        data = response.json()
        assert data["total_checks"] == 0
        assert any("No extracted data" in r for r in data["recommendations"])

    def test_run_compliance_checks_project_not_found(self, client):
        """Test running checks for non-existent project."""
        fake_id = uuid4()
        response = client.post(f"/api/v1/review/projects/{fake_id}/run-checks")
        assert response.status_code == 404

    def test_run_compliance_checks_with_categories(self, client, sample_project):
        """Test running checks filtered by category."""
        response = client.post(
            f"/api/v1/review/projects/{sample_project.id}/run-checks?check_categories=egress&check_categories=fire"
        )
        assert response.status_code == 200

    def test_run_compliance_checks_use_unverified(self, client, sample_project, sample_document, sample_extracted_data, sample_requirement):
        """Test running checks with unverified data."""
        response = client.post(
            f"/api/v1/review/projects/{sample_project.id}/run-checks?use_unverified=true"
        )
        assert response.status_code == 200
        data = response.json()
        # Results should be marked as needs_review for unverified data
        if data["total_checks"] > 0:
            assert data["needs_review"] > 0

    def test_get_project_checks(self, client, sample_project, sample_compliance_check):
        """Test getting compliance checks for a project."""
        response = client.get(f"/api/v1/review/projects/{sample_project.id}/checks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["check_name"] == "Stair Width"

    def test_get_project_checks_filter_by_category(self, client, sample_project, sample_compliance_check):
        """Test filtering checks by category."""
        response = client.get(f"/api/v1/review/projects/{sample_project.id}/checks?category=egress")
        assert response.status_code == 200
        data = response.json()
        assert all(c["check_category"] == "egress" for c in data)

    def test_get_project_checks_filter_by_status(self, client, sample_project, sample_compliance_check):
        """Test filtering checks by status."""
        response = client.get(f"/api/v1/review/projects/{sample_project.id}/checks?status=pass")
        assert response.status_code == 200
        data = response.json()
        assert all(c["status"] == "pass" for c in data)


class TestReviewHelperFunctions:
    """Tests for helper functions in review module."""

    def test_element_to_category_egress(self):
        """Test element to category mapping for egress."""
        from app.api.review import _element_to_category

        assert _element_to_category("stair_width") == "egress"
        assert _element_to_category("exit_width") == "egress"
        assert _element_to_category("corridor_width") == "egress"
        assert _element_to_category("travel_distance") == "egress"

    def test_element_to_category_fire(self):
        """Test element to category mapping for fire."""
        from app.api.review import _element_to_category

        assert _element_to_category("fire_rating") == "fire"
        assert _element_to_category("fire_separation") == "fire"
        assert _element_to_category("sprinkler") == "fire"

    def test_element_to_category_zoning(self):
        """Test element to category mapping for zoning."""
        from app.api.review import _element_to_category

        assert _element_to_category("front_setback") == "zoning"
        assert _element_to_category("building_height") == "zoning"
        assert _element_to_category("parking_count") == "zoning"

    def test_element_to_category_accessibility(self):
        """Test element to category mapping for accessibility."""
        from app.api.review import _element_to_category

        assert _element_to_category("accessible_route") == "accessibility"
        assert _element_to_category("barrier_free_path") == "accessibility"

    def test_element_to_category_general(self):
        """Test element to category mapping for unknown."""
        from app.api.review import _element_to_category

        assert _element_to_category("random_element") == "general"

    def test_format_requirement_value_min_only(self):
        """Test formatting requirement with min value only."""
        from app.api.review import _format_requirement_value

        class MockReq:
            min_value = 860
            max_value = None
            exact_value = None
            unit = "mm"

        result = _format_requirement_value(MockReq())
        assert "≥ 860" in result
        assert "mm" in result

    def test_format_requirement_value_max_only(self):
        """Test formatting requirement with max value only."""
        from app.api.review import _format_requirement_value

        class MockReq:
            min_value = None
            max_value = 10
            exact_value = None
            unit = "m"

        result = _format_requirement_value(MockReq())
        assert "≤ 10" in result
        assert "m" in result

    def test_format_requirement_value_range(self):
        """Test formatting requirement with range."""
        from app.api.review import _format_requirement_value

        class MockReq:
            min_value = 5
            max_value = 10
            exact_value = None
            unit = "m"

        result = _format_requirement_value(MockReq())
        assert "5" in result
        assert "10" in result

    def test_format_requirement_value_exact(self):
        """Test formatting requirement with exact value."""
        from app.api.review import _format_requirement_value

        class MockReq:
            min_value = None
            max_value = None
            exact_value = "Class A"
            unit = None

        result = _format_requirement_value(MockReq())
        assert "Class A" in result

    def test_get_extraction_prompts_floor_plan(self):
        """Test extraction prompts for floor plan."""
        from app.api.review import _get_extraction_prompts

        prompts = _get_extraction_prompts("floor_plan")
        assert "Room dimensions" in prompts["full_prompt"]
        assert "Stair widths" in prompts["full_prompt"]

    def test_get_extraction_prompts_site_plan(self):
        """Test extraction prompts for site plan."""
        from app.api.review import _get_extraction_prompts

        prompts = _get_extraction_prompts("site_plan")
        assert "setbacks" in prompts["full_prompt"].lower()
        assert "lot" in prompts["full_prompt"].lower()

    def test_get_extraction_prompts_elevation(self):
        """Test extraction prompts for elevation."""
        from app.api.review import _get_extraction_prompts

        prompts = _get_extraction_prompts("elevation")
        assert "height" in prompts["full_prompt"].lower()
        assert "storeys" in prompts["full_prompt"].lower()

    def test_get_extraction_prompts_default(self):
        """Test extraction prompts for unknown type."""
        from app.api.review import _get_extraction_prompts

        prompts = _get_extraction_prompts(None)
        assert "building-related" in prompts["full_prompt"].lower()
