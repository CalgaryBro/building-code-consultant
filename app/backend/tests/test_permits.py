"""
Unit tests for Permit Workflow API endpoints.

These tests cover:
- Creating permit applications (DP and BP)
- Document upload and review
- Application status tracking
- Review comments and deficiencies
- SDAB appeal workflow
"""
import pytest
from uuid import uuid4
from datetime import datetime


class TestPermitApplicationEndpoints:
    """Tests for permit application CRUD operations."""

    def test_create_development_permit_application(self, client):
        """Test creating a new Development Permit application."""
        response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "project_name": "New Single Family Home",
                "description": "Construction of a new single family dwelling",
                "address": "123 Test Street NW",
                "project_type": "new_construction",
                "estimated_value": 500000,
                "classification": "PART_9",
                "occupancy_group": "C",
                "building_area_sqm": 250,
                "building_height_storeys": 2,
                "dwelling_units": 1,
                "proposed_use": "Single Detached Dwelling",
                "applicant": {
                    "name": "John Smith",
                    "email": "john@example.com",
                    "phone": "403-555-0123"
                }
            }
        )
        assert response.status_code == 201
        data = response.json()

        assert data["permit_type"] == "DP"
        assert data["status"] == "draft"
        assert data["project_name"] == "New Single Family Home"
        assert data["address"] == "123 Test Street NW"
        assert data["application_number"] is not None
        assert data["application_number"].startswith("DP")
        assert data["permit_fee"] is not None
        assert data["id"] is not None

    def test_create_building_permit_application(self, client):
        """Test creating a new Building Permit application."""
        response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "BP",
                "project_name": "Commercial Renovation",
                "description": "Interior renovation of retail space",
                "address": "456 Business Ave SW",
                "project_type": "renovation",
                "estimated_value": 150000,
                "classification": "PART_9",
                "occupancy_group": "E",
                "building_area_sqm": 500,
                "applicant": {
                    "name": "Jane Doe",
                    "email": "jane@company.com"
                },
                "contractor": {
                    "name": "ABC Construction Ltd",
                    "company": "ABC Construction"
                }
            }
        )
        assert response.status_code == 201
        data = response.json()

        assert data["permit_type"] == "BP"
        assert data["status"] == "draft"
        assert data["application_number"].startswith("BP")

    def test_create_application_minimal_data(self, client):
        """Test creating an application with minimal required data."""
        response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "789 Minimal Street SE"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["address"] == "789 Minimal Street SE"
        assert data["status"] == "draft"

    def test_list_permit_applications(self, client):
        """Test listing permit applications with pagination."""
        # Create a few applications
        for i in range(3):
            client.post(
                "/api/v1/permits/applications",
                json={
                    "permit_type": "DP",
                    "address": f"{i+100} Test Ave NW",
                    "project_name": f"Test Project {i+1}"
                }
            )

        response = client.get("/api/v1/permits/applications")
        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "results" in data
        assert "page" in data
        assert "page_size" in data
        assert data["total"] >= 3

    def test_list_applications_filter_by_type(self, client):
        """Test filtering applications by permit type."""
        # Create one of each type
        client.post(
            "/api/v1/permits/applications",
            json={"permit_type": "DP", "address": "111 DP Street"}
        )
        client.post(
            "/api/v1/permits/applications",
            json={"permit_type": "BP", "address": "222 BP Street"}
        )

        response = client.get("/api/v1/permits/applications?permit_type=DP")
        assert response.status_code == 200
        data = response.json()

        for result in data["results"]:
            assert result["permit_type"] == "DP"

    def test_list_applications_filter_by_status(self, client):
        """Test filtering applications by status."""
        response = client.get("/api/v1/permits/applications?status=draft")
        assert response.status_code == 200
        data = response.json()

        for result in data["results"]:
            assert result["status"] == "draft"

    def test_get_permit_application(self, client):
        """Test getting a specific permit application."""
        # Create an application
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "333 Detail Street NE",
                "project_name": "Detail Test Project"
            }
        )
        app_id = create_response.json()["id"]

        # Get the application
        response = client.get(f"/api/v1/permits/applications/{app_id}")
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == app_id
        assert data["address"] == "333 Detail Street NE"
        assert data["documents_count"] == 0
        assert data["deficiencies_count"] == 0

    def test_get_application_not_found(self, client):
        """Test getting a non-existent application."""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/permits/applications/{fake_id}")
        assert response.status_code == 404

    def test_update_permit_application(self, client):
        """Test updating a permit application."""
        # Create an application
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "444 Update Street NW"
            }
        )
        app_id = create_response.json()["id"]

        # Update the application
        response = client.patch(
            f"/api/v1/permits/applications/{app_id}",
            json={
                "project_name": "Updated Project Name",
                "description": "Updated description",
                "estimated_value": 750000
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["project_name"] == "Updated Project Name"
        assert data["description"] == "Updated description"
        assert data["estimated_value"] == 750000


class TestApplicationSubmission:
    """Tests for application submission workflow."""

    def test_submit_application(self, client):
        """Test submitting a draft application."""
        # Create an application
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "555 Submit Street SE"
            }
        )
        app_id = create_response.json()["id"]

        # Submit the application
        response = client.post(f"/api/v1/permits/applications/{app_id}/submit")
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "submitted"
        assert data["submitted_at"] is not None

    def test_submit_already_submitted_application(self, client):
        """Test that submitting an already submitted application fails."""
        # Create and submit an application
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "666 Double Submit Street"
            }
        )
        app_id = create_response.json()["id"]
        client.post(f"/api/v1/permits/applications/{app_id}/submit")

        # Try to submit again
        response = client.post(f"/api/v1/permits/applications/{app_id}/submit")
        assert response.status_code == 400


class TestApplicationStatus:
    """Tests for application status transitions."""

    def test_status_update_submitted_to_under_review(self, client):
        """Test transitioning from submitted to under_review."""
        # Create and submit an application
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "777 Review Street NW"
            }
        )
        app_id = create_response.json()["id"]
        client.post(f"/api/v1/permits/applications/{app_id}/submit")

        # Update status to under_review
        response = client.post(
            f"/api/v1/permits/applications/{app_id}/status",
            json={
                "new_status": "under_review",
                "notes": "Assigned to reviewer John"
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "under_review"
        assert data["review_started_at"] is not None

    def test_status_update_approve_application(self, client):
        """Test approving an application."""
        # Create, submit, and set to under_review
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "888 Approve Street SE"
            }
        )
        app_id = create_response.json()["id"]
        client.post(f"/api/v1/permits/applications/{app_id}/submit")
        client.post(
            f"/api/v1/permits/applications/{app_id}/status",
            json={"new_status": "under_review"}
        )

        # Approve
        response = client.post(
            f"/api/v1/permits/applications/{app_id}/status",
            json={
                "new_status": "approved",
                "notes": "All requirements met"
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "approved"
        assert data["decision_date"] is not None
        assert data["decision_notes"] == "All requirements met"

    def test_status_update_refuse_application(self, client):
        """Test refusing an application."""
        # Create, submit, and set to under_review
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "999 Refuse Street NE"
            }
        )
        app_id = create_response.json()["id"]
        client.post(f"/api/v1/permits/applications/{app_id}/submit")
        client.post(
            f"/api/v1/permits/applications/{app_id}/status",
            json={"new_status": "under_review"}
        )

        # Refuse
        response = client.post(
            f"/api/v1/permits/applications/{app_id}/status",
            json={
                "new_status": "refused",
                "notes": "Setback violations cannot be relaxed"
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "refused"

    def test_invalid_status_transition(self, client):
        """Test that invalid status transitions are rejected."""
        # Create a draft application
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "000 Invalid Street"
            }
        )
        app_id = create_response.json()["id"]

        # Try to approve directly from draft (invalid)
        response = client.post(
            f"/api/v1/permits/applications/{app_id}/status",
            json={"new_status": "approved"}
        )
        assert response.status_code == 400

    def test_get_application_timeline(self, client):
        """Test getting the application timeline."""
        # Create and submit an application
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "111 Timeline Street"
            }
        )
        app_id = create_response.json()["id"]
        client.post(f"/api/v1/permits/applications/{app_id}/submit")

        # Get timeline
        response = client.get(f"/api/v1/permits/applications/{app_id}/timeline")
        assert response.status_code == 200
        data = response.json()

        assert data["permit_application_id"] == app_id
        assert data["current_status"] == "submitted"
        assert "events" in data
        assert len(data["events"]) >= 2  # Created + submitted


class TestDocumentEndpoints:
    """Tests for document upload and review."""

    def test_upload_document(self, client):
        """Test uploading a document to an application."""
        # Create an application
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "222 Document Street"
            }
        )
        app_id = create_response.json()["id"]

        # Upload a document
        response = client.post(
            f"/api/v1/permits/applications/{app_id}/documents",
            params={
                "document_type": "site_plan",
                "title": "Site Plan Drawing"
            },
            files={"file": ("site_plan.pdf", b"fake pdf content", "application/pdf")}
        )
        assert response.status_code == 201
        data = response.json()

        assert data["document_type"] == "site_plan"
        assert data["title"] == "Site Plan Drawing"
        assert data["filename"] == "site_plan.pdf"
        assert data["status"] == "pending"

    def test_list_application_documents(self, client):
        """Test listing documents for an application."""
        # Create application and upload documents
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "333 Documents Street"
            }
        )
        app_id = create_response.json()["id"]

        # Upload two documents
        client.post(
            f"/api/v1/permits/applications/{app_id}/documents",
            params={"document_type": "site_plan"},
            files={"file": ("site.pdf", b"content", "application/pdf")}
        )
        client.post(
            f"/api/v1/permits/applications/{app_id}/documents",
            params={"document_type": "floor_plan"},
            files={"file": ("floor.pdf", b"content", "application/pdf")}
        )

        # List documents
        response = client.get(f"/api/v1/permits/applications/{app_id}/documents")
        assert response.status_code == 200
        data = response.json()

        assert len(data) >= 2

    def test_review_document(self, client):
        """Test reviewing a document."""
        # Create application and upload document
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "444 Review Doc Street"
            }
        )
        app_id = create_response.json()["id"]

        upload_response = client.post(
            f"/api/v1/permits/applications/{app_id}/documents",
            params={"document_type": "elevation"},
            files={"file": ("elevation.pdf", b"content", "application/pdf")}
        )
        doc_id = upload_response.json()["id"]

        # Review the document
        response = client.patch(
            f"/api/v1/permits/documents/{doc_id}/review",
            json={
                "status": "accepted",
                "review_notes": "Document meets requirements",
                "reviewer": "Jane Reviewer"
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "accepted"
        assert data["reviewer"] == "Jane Reviewer"
        assert data["reviewed_at"] is not None


class TestReviewComments:
    """Tests for review comments."""

    def test_create_review_comment(self, client):
        """Test creating a review comment."""
        # Create an application
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "555 Comment Street"
            }
        )
        app_id = create_response.json()["id"]

        # Add a comment
        response = client.post(
            f"/api/v1/permits/applications/{app_id}/comments",
            params={"reviewer": "John Reviewer"},
            json={
                "category": "zoning",
                "comment": "Front setback appears to be less than required minimum",
                "code_reference": "LUB 1P2007 Sec 34",
                "requires_response": True
            }
        )
        assert response.status_code == 201
        data = response.json()

        assert data["category"] == "zoning"
        assert data["requires_response"] is True
        assert data["reviewer"] == "John Reviewer"

    def test_list_review_comments(self, client):
        """Test listing review comments."""
        # Create application and add comments
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "666 List Comments Street"
            }
        )
        app_id = create_response.json()["id"]

        client.post(
            f"/api/v1/permits/applications/{app_id}/comments",
            json={"category": "zoning", "comment": "Comment 1"}
        )
        client.post(
            f"/api/v1/permits/applications/{app_id}/comments",
            json={"category": "fire", "comment": "Comment 2"}
        )

        # List all comments
        response = client.get(f"/api/v1/permits/applications/{app_id}/comments")
        assert response.status_code == 200
        data = response.json()

        assert len(data) >= 2

    def test_filter_comments_by_category(self, client):
        """Test filtering comments by category."""
        # Create application and add comments
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "777 Filter Comments Street"
            }
        )
        app_id = create_response.json()["id"]

        client.post(
            f"/api/v1/permits/applications/{app_id}/comments",
            json={"category": "structural", "comment": "Structural comment"}
        )
        client.post(
            f"/api/v1/permits/applications/{app_id}/comments",
            json={"category": "fire", "comment": "Fire comment"}
        )

        # Filter by category
        response = client.get(
            f"/api/v1/permits/applications/{app_id}/comments?category=structural"
        )
        assert response.status_code == 200
        data = response.json()

        for comment in data:
            assert comment["category"] == "structural"


class TestDeficiencies:
    """Tests for deficiency management."""

    def test_create_deficiency(self, client):
        """Test creating a deficiency."""
        # Create an application
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "888 Deficiency Street"
            }
        )
        app_id = create_response.json()["id"]

        # Create a deficiency
        response = client.post(
            f"/api/v1/permits/applications/{app_id}/deficiencies",
            params={"created_by": "Inspector Smith"},
            json={
                "category": "zoning",
                "title": "Front Setback Violation",
                "description": "Building extends 1.5m into required front setback",
                "priority": "high",
                "code_reference": "LUB 1P2007 Section 40",
                "required_action": "Submit revised site plan showing compliant setback or apply for relaxation",
                "deadline_days": 14
            }
        )
        assert response.status_code == 201
        data = response.json()

        assert data["title"] == "Front Setback Violation"
        assert data["priority"] == "high"
        assert data["status"] == "open"
        assert data["deadline"] is not None

    def test_list_deficiencies(self, client):
        """Test listing deficiencies."""
        # Create application and deficiencies
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "999 List Deficiency Street"
            }
        )
        app_id = create_response.json()["id"]

        client.post(
            f"/api/v1/permits/applications/{app_id}/deficiencies",
            json={
                "category": "zoning",
                "title": "Deficiency 1",
                "description": "Description 1",
                "priority": "critical",
                "required_action": "Fix it"
            }
        )
        client.post(
            f"/api/v1/permits/applications/{app_id}/deficiencies",
            json={
                "category": "fire",
                "title": "Deficiency 2",
                "description": "Description 2",
                "priority": "low",
                "required_action": "Fix it"
            }
        )

        # List deficiencies
        response = client.get(f"/api/v1/permits/applications/{app_id}/deficiencies")
        assert response.status_code == 200
        data = response.json()

        assert len(data) >= 2
        # Should be sorted by priority (critical first)
        if len(data) >= 2:
            assert data[0]["priority"] == "critical"

    def test_update_deficiency_status(self, client):
        """Test updating deficiency status."""
        # Create application and deficiency
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "111 Update Deficiency Street"
            }
        )
        app_id = create_response.json()["id"]

        def_response = client.post(
            f"/api/v1/permits/applications/{app_id}/deficiencies",
            json={
                "category": "structural",
                "title": "Test Deficiency",
                "description": "Test description",
                "priority": "medium",
                "required_action": "Fix it"
            }
        )
        def_id = def_response.json()["id"]

        # Update to addressed
        response = client.patch(
            f"/api/v1/permits/deficiencies/{def_id}",
            params={"updated_by": "Applicant"},
            json={
                "status": "addressed",
                "addressed_notes": "Submitted revised drawings"
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "addressed"
        assert data["addressed_at"] is not None

    def test_resolve_deficiency(self, client):
        """Test resolving a deficiency."""
        # Create and address a deficiency
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "222 Resolve Deficiency Street"
            }
        )
        app_id = create_response.json()["id"]

        def_response = client.post(
            f"/api/v1/permits/applications/{app_id}/deficiencies",
            json={
                "category": "energy",
                "title": "Energy Compliance",
                "description": "Missing energy calculations",
                "priority": "medium",
                "required_action": "Submit NECB compliance report"
            }
        )
        def_id = def_response.json()["id"]

        # Resolve
        response = client.patch(
            f"/api/v1/permits/deficiencies/{def_id}",
            params={"updated_by": "Reviewer Jane"},
            json={
                "status": "resolved",
                "resolution_notes": "Energy calculations verified and approved"
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "resolved"
        assert data["resolved_by"] == "Reviewer Jane"


class TestSDABAppeals:
    """Tests for SDAB appeal workflow."""

    def test_file_sdab_appeal(self, client):
        """Test filing an SDAB appeal."""
        # Create, submit, review, and refuse an application
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "333 Appeal Street NW"
            }
        )
        app_id = create_response.json()["id"]

        client.post(f"/api/v1/permits/applications/{app_id}/submit")
        client.post(
            f"/api/v1/permits/applications/{app_id}/status",
            json={"new_status": "under_review"}
        )
        client.post(
            f"/api/v1/permits/applications/{app_id}/status",
            json={"new_status": "refused", "notes": "Height exceeds maximum"}
        )

        # File appeal
        response = client.post(
            "/api/v1/permits/appeals",
            json={
                "permit_application_id": app_id,
                "appeal_type": "appeal_of_refusal",
                "grounds_for_appeal": "The proposed height is consistent with neighboring properties",
                "requested_relief": "Approval of the development permit as submitted",
                "supporting_arguments": [
                    "Adjacent property at 335 Appeal Street has similar height",
                    "No shadow impact on neighboring properties"
                ],
                "appellant": {
                    "name": "Property Owner",
                    "email": "owner@example.com",
                    "phone": "403-555-1234"
                }
            }
        )
        assert response.status_code == 201
        data = response.json()

        assert data["appeal_type"] == "appeal_of_refusal"
        assert data["status"] == "filed"
        assert data["appeal_number"] is not None
        assert data["original_decision"] == "refused"

    def test_cannot_appeal_non_refused_application(self, client):
        """Test that only refused applications can be appealed (for refusal appeals)."""
        # Create a draft application
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "444 No Appeal Street"
            }
        )
        app_id = create_response.json()["id"]

        # Try to file appeal on draft
        response = client.post(
            "/api/v1/permits/appeals",
            json={
                "permit_application_id": app_id,
                "appeal_type": "appeal_of_refusal",
                "grounds_for_appeal": "Test grounds",
                "requested_relief": "Test relief",
                "appellant": {"name": "Test Person"}
            }
        )
        assert response.status_code == 400

    def test_get_sdab_appeal(self, client):
        """Test getting appeal details."""
        # Create refused application and appeal
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "555 Get Appeal Street"
            }
        )
        app_id = create_response.json()["id"]

        client.post(f"/api/v1/permits/applications/{app_id}/submit")
        client.post(
            f"/api/v1/permits/applications/{app_id}/status",
            json={"new_status": "under_review"}
        )
        client.post(
            f"/api/v1/permits/applications/{app_id}/status",
            json={"new_status": "refused"}
        )

        appeal_response = client.post(
            "/api/v1/permits/appeals",
            json={
                "permit_application_id": app_id,
                "appeal_type": "appeal_of_refusal",
                "grounds_for_appeal": "Test grounds",
                "requested_relief": "Test relief",
                "appellant": {"name": "Test Person"}
            }
        )
        appeal_id = appeal_response.json()["id"]

        # Get appeal
        response = client.get(f"/api/v1/permits/appeals/{appeal_id}")
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == appeal_id
        assert data["permit_application_id"] == app_id

    def test_update_appeal_decision(self, client):
        """Test updating appeal with decision."""
        # Create refused application and appeal
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "666 Decision Street"
            }
        )
        app_id = create_response.json()["id"]

        client.post(f"/api/v1/permits/applications/{app_id}/submit")
        client.post(
            f"/api/v1/permits/applications/{app_id}/status",
            json={"new_status": "under_review"}
        )
        client.post(
            f"/api/v1/permits/applications/{app_id}/status",
            json={"new_status": "refused"}
        )

        appeal_response = client.post(
            "/api/v1/permits/appeals",
            json={
                "permit_application_id": app_id,
                "appeal_type": "appeal_of_refusal",
                "grounds_for_appeal": "Test grounds",
                "requested_relief": "Test relief",
                "appellant": {"name": "Test Person"}
            }
        )
        appeal_id = appeal_response.json()["id"]

        # Update with allowed decision
        response = client.patch(
            f"/api/v1/permits/appeals/{appeal_id}",
            json={
                "status": "allowed",
                "hearing_notes": "Board found merit in the appeal"
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "allowed"
        assert data["decision_date"] is not None


class TestStatistics:
    """Tests for permit statistics."""

    def test_get_permit_statistics(self, client):
        """Test getting permit statistics."""
        # Create a few applications first
        client.post(
            "/api/v1/permits/applications",
            json={"permit_type": "DP", "address": "Stats Street 1"}
        )
        client.post(
            "/api/v1/permits/applications",
            json={"permit_type": "BP", "address": "Stats Street 2"}
        )

        response = client.get("/api/v1/permits/statistics")
        assert response.status_code == 200
        data = response.json()

        assert "total_applications" in data
        assert "by_type" in data
        assert "by_status" in data
        assert "common_deficiencies" in data


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_create_application_missing_required_field(self, client):
        """Test creating application without required address."""
        response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP"
                # Missing address
            }
        )
        assert response.status_code == 422  # Validation error

    def test_create_application_invalid_permit_type(self, client):
        """Test creating application with invalid permit type."""
        response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "INVALID",
                "address": "123 Test Street"
            }
        )
        assert response.status_code == 422

    def test_update_non_editable_application(self, client):
        """Test that approved applications cannot be edited."""
        # Create, submit, review, and approve an application
        create_response = client.post(
            "/api/v1/permits/applications",
            json={
                "permit_type": "DP",
                "address": "777 Locked Street"
            }
        )
        app_id = create_response.json()["id"]

        client.post(f"/api/v1/permits/applications/{app_id}/submit")
        client.post(
            f"/api/v1/permits/applications/{app_id}/status",
            json={"new_status": "under_review"}
        )
        client.post(
            f"/api/v1/permits/applications/{app_id}/status",
            json={"new_status": "approved"}
        )

        # Try to update
        response = client.patch(
            f"/api/v1/permits/applications/{app_id}",
            json={"project_name": "Cannot Change This"}
        )
        assert response.status_code == 400

    def test_document_not_found(self, client):
        """Test reviewing a non-existent document."""
        fake_id = str(uuid4())
        response = client.patch(
            f"/api/v1/permits/documents/{fake_id}/review",
            json={"status": "accepted"}
        )
        assert response.status_code == 404

    def test_deficiency_not_found(self, client):
        """Test updating a non-existent deficiency."""
        fake_id = str(uuid4())
        response = client.patch(
            f"/api/v1/permits/deficiencies/{fake_id}",
            json={"status": "resolved"}
        )
        assert response.status_code == 404

    def test_appeal_not_found(self, client):
        """Test getting a non-existent appeal."""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/permits/appeals/{fake_id}")
        assert response.status_code == 404
