"""
Unit tests for GUIDE mode API endpoints.
"""
import pytest
from uuid import uuid4


class TestGuideAnalyzeEndpoint:
    """Tests for the project analysis endpoint."""

    def test_analyze_project_basic(self, client, sample_zone, sample_parcel):
        """Test basic project analysis."""
        response = client.post(
            "/api/v1/guide/analyze",
            json={
                "address": "123 Test Street",
                "project_type": "new_construction",
                "occupancy_type": "residential",
                "building_height_storeys": 2,
                "footprint_area_sqm": 150,
                "dwelling_units": 1
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "classification" in data
        assert "permits_required" in data
        assert "key_requirements" in data
        assert "next_steps" in data

    def test_analyze_project_part_9_classification(self, client, sample_zone, sample_parcel):
        """Test Part 9 classification for small residential."""
        response = client.post(
            "/api/v1/guide/analyze",
            json={
                "address": "123 Test Street",
                "project_type": "new_construction",
                "occupancy_type": "residential",
                "building_height_storeys": 2,
                "footprint_area_sqm": 200,
                "building_area_sqm": 300,
                "dwelling_units": 1
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["classification"] == "PART_9"
        assert "Part 9" in data["classification_reason"]

    def test_analyze_project_part_3_exceeds_height(self, client, sample_zone, sample_parcel):
        """Test Part 3 classification when height exceeds 3 storeys."""
        response = client.post(
            "/api/v1/guide/analyze",
            json={
                "address": "123 Test Street",
                "project_type": "new_construction",
                "occupancy_type": "residential",
                "building_height_storeys": 5,
                "footprint_area_sqm": 400,
                "dwelling_units": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["classification"] == "PART_3"
        assert "storeys" in data["classification_reason"].lower()

    def test_analyze_project_part_3_exceeds_area(self, client, sample_zone, sample_parcel):
        """Test Part 3 classification when footprint exceeds 600 m²."""
        response = client.post(
            "/api/v1/guide/analyze",
            json={
                "address": "123 Test Street",
                "project_type": "new_construction",
                "occupancy_type": "residential",
                "building_height_storeys": 2,
                "footprint_area_sqm": 800,
                "dwelling_units": 4
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["classification"] == "PART_3"
        assert "m²" in data["classification_reason"]

    def test_analyze_project_part_3_high_hazard_occupancy(self, client, sample_zone, sample_parcel):
        """Test Part 3 classification for high hazard occupancy."""
        response = client.post(
            "/api/v1/guide/analyze",
            json={
                "address": "123 Test Street",
                "project_type": "new_construction",
                "occupancy_type": "assembly",
                "building_height_storeys": 1,
                "footprint_area_sqm": 200
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["classification"] == "PART_3"
        assert "occupancy" in data["classification_reason"].lower()

    def test_analyze_project_address_not_found(self, client):
        """Test analysis with unknown address adds warning."""
        response = client.post(
            "/api/v1/guide/analyze",
            json={
                "address": "999 Unknown Street XY",
                "project_type": "new_construction",
                "occupancy_type": "residential",
                "building_height_storeys": 2,
                "footprint_area_sqm": 150
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["warnings"]) > 0
        assert any("not found" in w.lower() for w in data["warnings"])

    def test_analyze_project_permits_included(self, client, sample_zone, sample_parcel):
        """Test that permits are included in response."""
        response = client.post(
            "/api/v1/guide/analyze",
            json={
                "address": "123 Test Street",
                "project_type": "new_construction",
                "occupancy_type": "residential",
                "building_height_storeys": 2,
                "footprint_area_sqm": 150
            }
        )
        assert response.status_code == 200
        data = response.json()
        permits = data["permits_required"]
        permit_types = [p["permit_type"] for p in permits]
        assert "development_permit" in permit_types
        assert "building_permit" in permit_types
        assert "electrical_permit" in permit_types

    def test_analyze_project_renovation(self, client, sample_zone, sample_parcel):
        """Test analysis for renovation project."""
        response = client.post(
            "/api/v1/guide/analyze",
            json={
                "address": "123 Test Street",
                "project_type": "renovation",
                "occupancy_type": "residential",
                "building_area_sqm": 30
            }
        )
        assert response.status_code == 200
        data = response.json()
        # Minor renovation may exempt development permit
        dp = next(p for p in data["permits_required"] if p["permit_type"] == "development_permit")
        assert dp["required"] is False

    def test_analyze_creates_project(self, client, sample_zone, sample_parcel, db_session):
        """Test that analysis creates a project record."""
        from app.models.projects import Project

        initial_count = db_session.query(Project).count()

        response = client.post(
            "/api/v1/guide/analyze",
            json={
                "address": "123 Test Street",
                "project_type": "new_construction",
                "occupancy_type": "residential",
                "building_height_storeys": 2,
                "footprint_area_sqm": 150
            }
        )
        assert response.status_code == 200

        final_count = db_session.query(Project).count()
        assert final_count == initial_count + 1


class TestGuideProjectEndpoints:
    """Tests for project management endpoints."""

    def test_list_projects_empty(self, client):
        """Test listing projects when empty."""
        response = client.get("/api/v1/guide/projects")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_projects_with_data(self, client, sample_project):
        """Test listing projects with data."""
        response = client.get("/api/v1/guide/projects")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["project_name"] == "Test Project"

    def test_list_projects_filter_by_status(self, client, db_session, sample_project):
        """Test filtering projects by status."""
        from app.models.projects import Project

        # Create another project with different status
        project2 = Project(
            project_name="In Review Project",
            address="456 Another St",
            classification="PART_9",
            status="in_review"
        )
        db_session.add(project2)
        db_session.commit()

        response = client.get("/api/v1/guide/projects?status=draft")
        assert response.status_code == 200
        data = response.json()
        assert all(p["status"] == "draft" for p in data)

    def test_list_projects_with_limit(self, client, sample_project):
        """Test project listing with limit."""
        response = client.get("/api/v1/guide/projects?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 1

    def test_get_project_by_id(self, client, sample_project):
        """Test getting a project by ID."""
        response = client.get(f"/api/v1/guide/projects/{sample_project.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["project_name"] == "Test Project"
        assert data["classification"] == "PART_9"

    def test_get_project_not_found(self, client):
        """Test getting a non-existent project."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/guide/projects/{fake_id}")
        assert response.status_code == 404


class TestGuideClassificationEndpoint:
    """Tests for the classification explanation endpoint."""

    def test_explain_classification(self, client):
        """Test the classification explanation endpoint."""
        response = client.get("/api/v1/guide/classification")
        assert response.status_code == 200
        data = response.json()
        assert "overview" in data
        assert "part_9" in data
        assert "part_3" in data
        assert "applies_to" in data["part_9"]
        assert "requirements" in data["part_3"]


class TestGuideHelperFunctions:
    """Tests for helper functions in guide module."""

    def test_classify_building_part_9_residential(self):
        """Test classification for typical Part 9 residential."""
        from app.api.guide import classify_building

        classification, reason = classify_building(
            building_height_storeys=2,
            footprint_area_sqm=200,
            building_area_sqm=350,
            occupancy_type="residential"
        )
        assert classification == "PART_9"

    def test_classify_building_part_3_height(self):
        """Test classification when exceeding height."""
        from app.api.guide import classify_building

        classification, reason = classify_building(
            building_height_storeys=4,
            footprint_area_sqm=200,
            building_area_sqm=600,
            occupancy_type="residential"
        )
        assert classification == "PART_3"
        assert "4 storeys" in reason

    def test_classify_building_part_3_area(self):
        """Test classification when exceeding area."""
        from app.api.guide import classify_building

        classification, reason = classify_building(
            building_height_storeys=2,
            footprint_area_sqm=700,
            building_area_sqm=1200,
            occupancy_type="commercial"
        )
        assert classification == "PART_3"
        assert "700" in reason

    def test_classify_building_part_3_both_limits(self):
        """Test classification when exceeding both height and area."""
        from app.api.guide import classify_building

        classification, reason = classify_building(
            building_height_storeys=5,
            footprint_area_sqm=800,
            building_area_sqm=2000,
            occupancy_type="residential"
        )
        assert classification == "PART_3"
        assert "storeys" in reason.lower() and "m²" in reason

    def test_classify_building_assembly_always_part_3(self):
        """Test that assembly occupancy is always Part 3."""
        from app.api.guide import classify_building

        classification, reason = classify_building(
            building_height_storeys=1,
            footprint_area_sqm=100,
            building_area_sqm=100,
            occupancy_type="assembly"
        )
        assert classification == "PART_3"

    def test_map_occupancy_type(self):
        """Test occupancy type mapping."""
        from app.api.guide import _map_occupancy_type

        assert _map_occupancy_type("residential") == "C"
        assert _map_occupancy_type("commercial") == "D"
        assert _map_occupancy_type("business") == "D"
        assert _map_occupancy_type("mercantile") == "E"
        assert _map_occupancy_type("industrial") == "F2"
        assert _map_occupancy_type("assembly") == "A2"
        assert _map_occupancy_type("unknown") == "D"  # Default

    def test_calculate_dp_fee(self):
        """Test development permit fee calculation."""
        from app.api.guide import _calculate_dp_fee

        # New construction: base + area * 2.5
        fee = _calculate_dp_fee(200, "new_construction")
        assert fee == 500 + (200 * 2.5)

        # Addition: base + area * 2.0
        fee = _calculate_dp_fee(100, "addition")
        assert fee == 500 + (100 * 2.0)

        # Renovation: base only
        fee = _calculate_dp_fee(100, "renovation")
        assert fee == 500

    def test_calculate_bp_fee(self):
        """Test building permit fee calculation."""
        from app.api.guide import _calculate_bp_fee

        # Part 9: base + area * 12
        fee = _calculate_bp_fee(200, "PART_9")
        assert fee == 200 + (200 * 12)

        # Part 3: base + area * 18
        fee = _calculate_bp_fee(200, "PART_3")
        assert fee == 200 + (200 * 18)
