"""
Unit tests for STANDATA API endpoints.

Tests for searching and browsing Alberta STANDATA bulletins including:
- BCI: Building Code Interpretations
- BCB: Building Code Bulletins
- FCB: Fire Code Bulletins
- PCB: Plumbing Code Bulletins
"""
import pytest
from datetime import date
from uuid import uuid4

from app.models.standata import Standata


@pytest.fixture
def sample_standata_bci(db_session):
    """Create a sample BCI bulletin for testing."""
    bulletin = Standata(
        id=uuid4(),
        bulletin_number="23-BCI-030",
        title="Secondary Suites in Existing Buildings",
        category="BCI",
        effective_date=date(2023, 6, 15),
        supersedes="22-BCI-030",
        summary="Guidance on applying building code requirements to secondary suites.",
        full_text="""
        This bulletin provides interpretation guidance for applying the Alberta Building Code
        to secondary suites in existing residential buildings. Key requirements include:
        - Minimum ceiling height of 2.0m in habitable rooms
        - Smoke alarms on each level
        - Fire separation between suite and principal dwelling
        - Egress requirements per NBC Article 9.8.4.1
        - Window egress per Article 9.9.10.1
        """,
        code_references=["9.8.4.1", "9.9.10.1", "9.10.9.6"],
        keywords=["secondary suite", "egress", "fire separation", "existing building"],
        related_bulletins=["23-BCB-001", "23-FCB-004"],
        pdf_path="/data/standata/23-BCI-030.pdf",
        pdf_filename="23-BCI-030.pdf",
        extraction_confidence="HIGH",
    )
    db_session.add(bulletin)
    db_session.commit()
    db_session.refresh(bulletin)
    return bulletin


@pytest.fixture
def sample_standata_bcb(db_session):
    """Create a sample BCB bulletin for testing."""
    bulletin = Standata(
        id=uuid4(),
        bulletin_number="23-BCB-001",
        title="Energy Efficiency Requirements Update",
        category="BCB",
        effective_date=date(2023, 5, 1),
        summary="Updates to energy efficiency requirements under NBC 9.36.",
        full_text="""
        This bulletin addresses updates to energy efficiency requirements under Section 9.36
        of the National Building Code (Alberta Edition). Topics covered include:
        - Insulation R-values for walls and roofs
        - Window and door efficiency ratings
        - Air barrier requirements
        - HVAC system efficiency
        """,
        code_references=["9.36.2.6", "9.36.3.1", "9.36.4.2"],
        keywords=["energy efficiency", "insulation", "air barrier", "HVAC"],
        pdf_path="/data/standata/23-BCB-001.pdf",
        pdf_filename="23-BCB-001.pdf",
        extraction_confidence="HIGH",
    )
    db_session.add(bulletin)
    db_session.commit()
    db_session.refresh(bulletin)
    return bulletin


@pytest.fixture
def sample_standata_fcb(db_session):
    """Create a sample FCB bulletin for testing."""
    bulletin = Standata(
        id=uuid4(),
        bulletin_number="23-FCB-004",
        title="Fire Alarm System Maintenance Requirements",
        category="FCB",
        effective_date=date(2023, 7, 1),
        summary="Requirements for fire alarm system testing and maintenance.",
        full_text="""
        This bulletin outlines the requirements for testing and maintaining fire alarm
        systems in accordance with the Alberta Fire Code. Key topics include:
        - Annual inspection requirements
        - Testing procedures for smoke detectors
        - Documentation and record-keeping
        - Qualified technician requirements
        """,
        code_references=["2.1.3.1", "2.1.3.5", "2.2.1.1"],
        keywords=["fire alarm", "maintenance", "inspection", "smoke detector"],
        pdf_path="/data/standata/23-FCB-004.pdf",
        pdf_filename="23-FCB-004.pdf",
        extraction_confidence="MEDIUM",
    )
    db_session.add(bulletin)
    db_session.commit()
    db_session.refresh(bulletin)
    return bulletin


@pytest.fixture
def sample_standata_pcb(db_session):
    """Create a sample PCB bulletin for testing."""
    bulletin = Standata(
        id=uuid4(),
        bulletin_number="23-PCB-002",
        title="Backflow Prevention Device Requirements",
        category="PCB",
        effective_date=date(2023, 4, 15),
        summary="Requirements for backflow prevention devices in plumbing systems.",
        full_text="""
        This bulletin provides guidance on backflow prevention device requirements under
        the Alberta Plumbing Code. Coverage includes:
        - Types of backflow preventers
        - Installation requirements
        - Testing and maintenance schedules
        - Cross-connection control
        """,
        code_references=["2.6.2.1", "2.6.2.6"],
        keywords=["backflow", "plumbing", "cross-connection", "water supply"],
        pdf_path="/data/standata/23-PCB-002.pdf",
        pdf_filename="23-PCB-002.pdf",
        extraction_confidence="HIGH",
    )
    db_session.add(bulletin)
    db_session.commit()
    db_session.refresh(bulletin)
    return bulletin


class TestListStandata:
    """Tests for listing STANDATA bulletins endpoint."""

    def test_list_standata_empty(self, client):
        """Test listing bulletins when database is empty."""
        response = client.get("/api/v1/standata/")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_standata_with_data(self, client, sample_standata_bci):
        """Test listing bulletins returns data."""
        response = client.get("/api/v1/standata/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["bulletin_number"] == "23-BCI-030"
        assert data[0]["title"] == "Secondary Suites in Existing Buildings"
        assert data[0]["category"] == "BCI"

    def test_list_standata_multiple_bulletins(
        self, client, sample_standata_bci, sample_standata_bcb, sample_standata_fcb
    ):
        """Test listing multiple bulletins."""
        response = client.get("/api/v1/standata/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_standata_filter_by_category(
        self, client, sample_standata_bci, sample_standata_bcb, sample_standata_fcb
    ):
        """Test filtering bulletins by category."""
        response = client.get("/api/v1/standata/?category=BCI")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "BCI"
        assert data[0]["bulletin_number"] == "23-BCI-030"

    def test_list_standata_filter_category_case_insensitive(
        self, client, sample_standata_bci
    ):
        """Test category filter is case insensitive."""
        response = client.get("/api/v1/standata/?category=bci")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "BCI"

    def test_list_standata_with_limit(
        self, client, sample_standata_bci, sample_standata_bcb, sample_standata_fcb
    ):
        """Test listing bulletins with limit."""
        response = client.get("/api/v1/standata/?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_standata_with_offset(
        self, client, sample_standata_bci, sample_standata_bcb, sample_standata_fcb
    ):
        """Test listing bulletins with offset."""
        response = client.get("/api/v1/standata/?limit=10&offset=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_standata_includes_summary_fields(self, client, sample_standata_bci):
        """Test that list response includes summary fields."""
        response = client.get("/api/v1/standata/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        bulletin = data[0]
        assert "id" in bulletin
        assert "bulletin_number" in bulletin
        assert "title" in bulletin
        assert "category" in bulletin
        assert "effective_date" in bulletin
        assert "summary" in bulletin
        assert "code_references" in bulletin


class TestStandataStats:
    """Tests for STANDATA statistics endpoint."""

    def test_stats_empty_database(self, client):
        """Test stats with empty database."""
        response = client.get("/api/v1/standata/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_bulletins"] == 0
        assert data["by_category"] == {}
        assert data["total_code_references"] == 0

    def test_stats_with_data(
        self, client, sample_standata_bci, sample_standata_bcb, sample_standata_fcb
    ):
        """Test stats returns counts by category."""
        response = client.get("/api/v1/standata/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_bulletins"] == 3
        assert data["by_category"]["BCI"] == 1
        assert data["by_category"]["BCB"] == 1
        assert data["by_category"]["FCB"] == 1
        assert data["total_code_references"] > 0

    def test_stats_includes_latest_date(self, client, sample_standata_bci, sample_standata_fcb):
        """Test stats includes latest effective date."""
        response = client.get("/api/v1/standata/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["latest_effective_date"] is not None
        # FCB has the latest date (2023-07-01)
        assert data["latest_effective_date"] == "2023-07-01"

    def test_stats_counts_unique_code_references(self, client, sample_standata_bci):
        """Test stats counts unique code references correctly."""
        response = client.get("/api/v1/standata/stats")
        assert response.status_code == 200
        data = response.json()
        # sample_standata_bci has 3 code references
        assert data["total_code_references"] == 3


class TestStandataCategories:
    """Tests for STANDATA categories endpoint."""

    def test_list_categories(self, client):
        """Test categories endpoint returns all categories."""
        response = client.get("/api/v1/standata/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        categories = data["categories"]
        assert len(categories) == 4

        # Verify all expected categories are present
        category_codes = [cat["code"] for cat in categories]
        assert "BCI" in category_codes
        assert "BCB" in category_codes
        assert "FCB" in category_codes
        assert "PCB" in category_codes

    def test_categories_have_descriptions(self, client):
        """Test each category has name and description."""
        response = client.get("/api/v1/standata/categories")
        assert response.status_code == 200
        data = response.json()
        for category in data["categories"]:
            assert "code" in category
            assert "name" in category
            assert "description" in category
            assert len(category["name"]) > 0
            assert len(category["description"]) > 0


class TestSearchStandata:
    """Tests for STANDATA search endpoint."""

    def test_search_no_results(self, client, sample_standata_bci):
        """Test search returns empty when no matches."""
        response = client.get("/api/v1/standata/search?q=nonexistent_term_xyz")
        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] == 0
        assert data["results"] == []
        assert data["query"] == "nonexistent_term_xyz"

    def test_search_by_title(self, client, sample_standata_bci):
        """Test search returns results matching title."""
        response = client.get("/api/v1/standata/search?q=Secondary+Suites")
        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] == 1
        assert data["results"][0]["bulletin_number"] == "23-BCI-030"
        assert data["results"][0]["match_type"] == "title"

    def test_search_by_bulletin_number(self, client, sample_standata_bci):
        """Test search returns results matching bulletin number."""
        response = client.get("/api/v1/standata/search?q=23-BCI-030")
        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] == 1
        assert data["results"][0]["bulletin_number"] == "23-BCI-030"
        assert data["results"][0]["match_type"] == "bulletin_number"

    def test_search_by_summary(self, client, sample_standata_bci):
        """Test search returns results matching summary."""
        response = client.get("/api/v1/standata/search?q=secondary+suites")
        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] >= 1
        # Could match title or summary

    def test_search_by_full_text(self, client, sample_standata_bci):
        """Test search returns results matching full text."""
        response = client.get("/api/v1/standata/search?q=ceiling+height")
        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] == 1
        assert data["results"][0]["bulletin_number"] == "23-BCI-030"

    def test_search_relevance_snippet(self, client, sample_standata_bci):
        """Test search results include relevance snippet."""
        response = client.get("/api/v1/standata/search?q=egress")
        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] >= 1
        assert data["results"][0]["relevance_snippet"] is not None

    def test_search_filter_by_categories(
        self, client, sample_standata_bci, sample_standata_bcb
    ):
        """Test search filter by categories."""
        # Both bulletins contain "requirements" in their text
        response = client.get("/api/v1/standata/search?q=requirements&categories=BCI")
        assert response.status_code == 200
        data = response.json()
        for result in data["results"]:
            assert result["category"] == "BCI"

    def test_search_filter_multiple_categories(
        self, client, sample_standata_bci, sample_standata_bcb, sample_standata_fcb
    ):
        """Test search filter by multiple categories."""
        response = client.get("/api/v1/standata/search?q=requirements&categories=BCI,BCB")
        assert response.status_code == 200
        data = response.json()
        for result in data["results"]:
            assert result["category"] in ["BCI", "BCB"]

    def test_search_with_limit(
        self, client, sample_standata_bci, sample_standata_bcb, sample_standata_fcb
    ):
        """Test search respects limit parameter."""
        response = client.get("/api/v1/standata/search?q=requirements&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 1

    def test_search_query_too_short(self, client):
        """Test search rejects query too short."""
        response = client.get("/api/v1/standata/search?q=a")
        assert response.status_code == 422  # Validation error

    def test_search_case_insensitive(self, client, sample_standata_bci):
        """Test search is case insensitive."""
        response_lower = client.get("/api/v1/standata/search?q=secondary")
        response_upper = client.get("/api/v1/standata/search?q=SECONDARY")
        assert response_lower.status_code == 200
        assert response_upper.status_code == 200
        assert response_lower.json()["total_results"] == response_upper.json()["total_results"]


class TestGetBulletinsByCode:
    """Tests for finding bulletins by NBC article reference."""

    def test_by_code_no_results(self, client, sample_standata_bci):
        """Test by-code returns empty when no matches."""
        response = client.get("/api/v1/standata/by-code/99.99.99.99")
        assert response.status_code == 200
        data = response.json()
        assert data["code_reference"] == "99.99.99.99"
        assert data["total_results"] == 0
        assert data["bulletins"] == []

    def test_by_code_returns_matching_bulletins(self, client, sample_standata_bci):
        """Test by-code returns bulletins referencing that article."""
        response = client.get("/api/v1/standata/by-code/9.8.4.1")
        assert response.status_code == 200
        data = response.json()
        assert data["code_reference"] == "9.8.4.1"
        assert data["total_results"] >= 1
        assert data["bulletins"][0]["bulletin_number"] == "23-BCI-030"

    def test_by_code_multiple_results(
        self, client, db_session, sample_standata_bci
    ):
        """Test by-code returns multiple bulletins if they reference same article."""
        # Add another bulletin referencing the same code
        another_bulletin = Standata(
            id=uuid4(),
            bulletin_number="22-BCI-015",
            title="Egress Requirements for Small Buildings",
            category="BCI",
            effective_date=date(2022, 3, 1),
            full_text="This bulletin covers egress per Article 9.8.4.1 for small buildings.",
            code_references=["9.8.4.1", "9.8.4.2"],
            pdf_path="/data/standata/22-BCI-015.pdf",
            pdf_filename="22-BCI-015.pdf",
        )
        db_session.add(another_bulletin)
        db_session.commit()

        response = client.get("/api/v1/standata/by-code/9.8.4.1")
        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] == 2

    def test_by_code_response_structure(self, client, sample_standata_bci):
        """Test by-code response has correct structure."""
        response = client.get("/api/v1/standata/by-code/9.8.4.1")
        assert response.status_code == 200
        data = response.json()
        assert "code_reference" in data
        assert "total_results" in data
        assert "bulletins" in data
        if data["total_results"] > 0:
            bulletin = data["bulletins"][0]
            assert "id" in bulletin
            assert "bulletin_number" in bulletin
            assert "title" in bulletin
            assert "category" in bulletin


class TestGetBulletinByNumber:
    """Tests for getting a specific bulletin by number."""

    def test_get_bulletin_by_number(self, client, sample_standata_bci):
        """Test getting a bulletin by its number."""
        response = client.get("/api/v1/standata/23-BCI-030")
        assert response.status_code == 200
        data = response.json()
        assert data["bulletin_number"] == "23-BCI-030"
        assert data["title"] == "Secondary Suites in Existing Buildings"
        assert data["category"] == "BCI"

    def test_get_bulletin_full_response(self, client, sample_standata_bci):
        """Test bulletin response includes all fields."""
        response = client.get("/api/v1/standata/23-BCI-030")
        assert response.status_code == 200
        data = response.json()
        # Check all expected fields
        assert "id" in data
        assert "bulletin_number" in data
        assert "title" in data
        assert "category" in data
        assert "effective_date" in data
        assert "supersedes" in data
        assert "summary" in data
        assert "full_text" in data
        assert "code_references" in data
        assert "keywords" in data
        assert "related_bulletins" in data
        assert "pdf_path" in data
        assert "pdf_filename" in data
        assert "extraction_confidence" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_bulletin_case_insensitive(self, client, sample_standata_bci):
        """Test bulletin lookup is case insensitive."""
        response = client.get("/api/v1/standata/23-bci-030")
        assert response.status_code == 200
        data = response.json()
        assert data["bulletin_number"] == "23-BCI-030"

    def test_get_bulletin_not_found(self, client):
        """Test getting a non-existent bulletin returns 404."""
        response = client.get("/api/v1/standata/99-BCI-999")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_bulletin_not_found_message(self, client):
        """Test 404 message includes the bulletin number."""
        response = client.get("/api/v1/standata/FAKE-BULLETIN-123")
        assert response.status_code == 404
        data = response.json()
        assert "FAKE-BULLETIN-123" in data["detail"]

    def test_get_bulletin_code_references(self, client, sample_standata_bci):
        """Test bulletin includes code references list."""
        response = client.get("/api/v1/standata/23-BCI-030")
        assert response.status_code == 200
        data = response.json()
        assert data["code_references"] is not None
        assert "9.8.4.1" in data["code_references"]
        assert "9.9.10.1" in data["code_references"]
        assert "9.10.9.6" in data["code_references"]

    def test_get_bulletin_keywords(self, client, sample_standata_bci):
        """Test bulletin includes keywords list."""
        response = client.get("/api/v1/standata/23-BCI-030")
        assert response.status_code == 200
        data = response.json()
        assert data["keywords"] is not None
        assert "secondary suite" in data["keywords"]
        assert "egress" in data["keywords"]


class TestGetBulletinById:
    """Tests for getting a bulletin by UUID."""

    def test_get_bulletin_by_id(self, client, sample_standata_bci):
        """Test getting a bulletin by its UUID."""
        # First get the bulletin to obtain its ID
        list_response = client.get("/api/v1/standata/")
        assert list_response.status_code == 200
        bulletin_id = list_response.json()[0]["id"]

        # Now get by ID
        response = client.get(f"/api/v1/standata/id/{bulletin_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["bulletin_number"] == "23-BCI-030"

    def test_get_bulletin_by_id_not_found(self, client):
        """Test getting a non-existent bulletin by ID returns 404."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/standata/id/{fake_id}")
        assert response.status_code == 404

    def test_get_bulletin_by_invalid_id(self, client):
        """Test getting a bulletin with invalid ID format."""
        response = client.get("/api/v1/standata/id/not-a-valid-uuid")
        assert response.status_code == 422  # Validation error


class TestStandataIntegration:
    """Integration tests for STANDATA API."""

    def test_full_workflow(
        self, client, sample_standata_bci, sample_standata_bcb,
        sample_standata_fcb, sample_standata_pcb
    ):
        """Test a full workflow of listing, searching, and retrieving bulletins."""
        # 1. Get stats to see overview
        stats_response = client.get("/api/v1/standata/stats")
        assert stats_response.status_code == 200
        assert stats_response.json()["total_bulletins"] == 4

        # 2. List categories
        categories_response = client.get("/api/v1/standata/categories")
        assert categories_response.status_code == 200

        # 3. List all bulletins
        list_response = client.get("/api/v1/standata/")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 4

        # 4. Filter by category
        bci_response = client.get("/api/v1/standata/?category=BCI")
        assert bci_response.status_code == 200
        assert len(bci_response.json()) == 1

        # 5. Search for specific content
        search_response = client.get("/api/v1/standata/search?q=fire")
        assert search_response.status_code == 200

        # 6. Look up by code reference
        code_response = client.get("/api/v1/standata/by-code/9.8.4.1")
        assert code_response.status_code == 200

        # 7. Get specific bulletin details
        detail_response = client.get("/api/v1/standata/23-BCI-030")
        assert detail_response.status_code == 200
        assert "full_text" in detail_response.json()

    def test_all_categories_represented(
        self, client, sample_standata_bci, sample_standata_bcb,
        sample_standata_fcb, sample_standata_pcb
    ):
        """Test all four STANDATA categories are properly handled."""
        stats_response = client.get("/api/v1/standata/stats")
        assert stats_response.status_code == 200
        by_category = stats_response.json()["by_category"]
        assert by_category.get("BCI", 0) == 1
        assert by_category.get("BCB", 0) == 1
        assert by_category.get("FCB", 0) == 1
        assert by_category.get("PCB", 0) == 1
