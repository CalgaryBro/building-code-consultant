"""
Unit tests for EXPLORE mode API endpoints.
"""
import pytest
from uuid import uuid4


class TestExploreCodeEndpoints:
    """Tests for code-related endpoints."""

    def test_list_codes_empty(self, client):
        """Test listing codes when database is empty."""
        response = client.get("/api/v1/explore/codes")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_codes_with_data(self, client, sample_code):
        """Test listing codes with data."""
        response = client.get("/api/v1/explore/codes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["short_name"] == "NBC(AE)"
        assert data[0]["version"] == "2023"

    def test_list_codes_filter_by_type(self, client, db_session, sample_code):
        """Test filtering codes by type."""
        # Add another code of different type
        from app.models.codes import Code
        from datetime import date
        fire_code = Code(
            code_type="fire",
            name="Fire Code",
            short_name="NFC",
            version="2023",
            jurisdiction="Alberta",
            effective_date=date(2024, 1, 1),
            is_current=True,
        )
        db_session.add(fire_code)
        db_session.commit()

        # Filter by building type
        response = client.get("/api/v1/explore/codes?code_type=building")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["code_type"] == "building"

    def test_get_code_by_id(self, client, sample_code):
        """Test getting a specific code by ID."""
        response = client.get(f"/api/v1/explore/codes/{sample_code.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["short_name"] == "NBC(AE)"

    def test_get_code_not_found(self, client):
        """Test getting a non-existent code."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/explore/codes/{fake_id}")
        assert response.status_code == 404


class TestExploreArticleEndpoints:
    """Tests for article-related endpoints."""

    def test_list_articles_for_code(self, client, sample_code, sample_article):
        """Test listing articles for a code."""
        response = client.get(f"/api/v1/explore/codes/{sample_code.id}/articles")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["article_number"] == "9.8.4.1"

    def test_list_articles_filter_by_part(self, client, sample_code, sample_article):
        """Test filtering articles by part number."""
        response = client.get(f"/api/v1/explore/codes/{sample_code.id}/articles?part_number=9")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["part_number"] == 9

    def test_list_articles_filter_no_match(self, client, sample_code, sample_article):
        """Test filtering articles with no matches."""
        response = client.get(f"/api/v1/explore/codes/{sample_code.id}/articles?part_number=3")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_article_by_id(self, client, sample_article):
        """Test getting a specific article by ID."""
        response = client.get(f"/api/v1/explore/articles/{sample_article.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["article_number"] == "9.8.4.1"
        assert data["title"] == "Stair Width"

    def test_get_article_not_found(self, client):
        """Test getting a non-existent article."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/explore/articles/{fake_id}")
        assert response.status_code == 404

    def test_get_article_requirements(self, client, sample_article, sample_requirement):
        """Test getting requirements for an article."""
        response = client.get(f"/api/v1/explore/articles/{sample_article.id}/requirements")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["element"] == "stair_width"
        assert data[0]["min_value"] == 860


class TestExploreSearchEndpoints:
    """Tests for search endpoints."""

    def test_search_codes_empty_results(self, client):
        """Test searching with no results."""
        response = client.post(
            "/api/v1/explore/search",
            json={"query": "nonexistent term", "limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] == 0
        assert data["results"] == []

    def test_search_codes_with_results(self, client, sample_code, sample_article):
        """Test searching with results."""
        response = client.post(
            "/api/v1/explore/search",
            json={"query": "stair width", "limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] >= 1
        assert data["query"] == "stair width"

    def test_search_codes_by_article_number(self, client, sample_code, sample_article):
        """Test searching by article number."""
        response = client.post(
            "/api/v1/explore/search",
            json={"query": "9.8.4.1", "limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] >= 1

    def test_search_codes_with_limit(self, client, sample_code, sample_article):
        """Test search with limit parameter."""
        response = client.post(
            "/api/v1/explore/search",
            json={"query": "stair", "limit": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 1

    def test_search_requirements_by_element(self, client, sample_requirement):
        """Test searching requirements by element."""
        response = client.get("/api/v1/explore/requirements?element=stair")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert "stair" in data[0]["element"]

    def test_search_requirements_by_type(self, client, sample_requirement):
        """Test searching requirements by type."""
        response = client.get("/api/v1/explore/requirements?requirement_type=dimensional")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["requirement_type"] == "dimensional"

    def test_search_requirements_verified_only(self, client, sample_requirement):
        """Test searching only verified requirements."""
        response = client.get("/api/v1/explore/requirements?verified_only=true")
        assert response.status_code == 200
        data = response.json()
        assert all(r["is_verified"] for r in data)


class TestExploreBrowseEndpoints:
    """Tests for browse endpoints."""

    def test_browse_code_structure(self, client, sample_code, sample_article):
        """Test browsing code structure."""
        response = client.get("/api/v1/explore/browse/building")
        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert "parts" in data
        assert data["code"]["short_name"] == "NBC(AE)"

    def test_browse_code_structure_not_found(self, client):
        """Test browsing structure for non-existent code type."""
        response = client.get("/api/v1/explore/browse/nonexistent")
        assert response.status_code == 404


class TestExploreValidation:
    """Tests for input validation."""

    def test_search_query_too_short(self, client):
        """Test search with query too short."""
        response = client.post(
            "/api/v1/explore/search",
            json={"query": "a", "limit": 10}
        )
        assert response.status_code == 422  # Validation error

    def test_search_limit_validation(self, client):
        """Test search with invalid limit."""
        response = client.post(
            "/api/v1/explore/search",
            json={"query": "stair", "limit": 0}
        )
        assert response.status_code == 422

    def test_search_limit_too_high(self, client):
        """Test search with limit too high."""
        response = client.post(
            "/api/v1/explore/search",
            json={"query": "stair", "limit": 200}
        )
        assert response.status_code == 422
