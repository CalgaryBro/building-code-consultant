"""
Unit tests for Addresses API endpoints.
"""
import pytest
from uuid import uuid4


class TestAddressAutocomplete:
    """Tests for the address autocomplete endpoint."""

    def test_autocomplete_returns_results_for_valid_query(self, client, sample_parcel):
        """Test autocomplete returns results for a valid query."""
        response = client.get("/api/v1/addresses/autocomplete?q=Test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert "Test" in data[0]["address"]
        assert data[0]["community"] == "Test Community"
        assert data[0]["zone_code"] == "R-C1"
        assert data[0]["parcel_id"] is not None

    def test_autocomplete_returns_results_by_house_number(self, client, sample_parcel):
        """Test autocomplete returns results when searching by house number."""
        response = client.get("/api/v1/addresses/autocomplete?q=123")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert "123" in data[0]["address"]

    def test_autocomplete_respects_limit_parameter(self, client, db_session, sample_zone):
        """Test autocomplete respects the limit parameter."""
        from app.models.zones import Parcel

        # Create multiple parcels
        for i in range(15):
            parcel = Parcel(
                address=f"{100 + i} Main Street NW",
                street_name="Main",
                street_type="ST",
                street_direction="NW",
                house_number=str(100 + i),
                community_name="Downtown",
                quadrant="NW",
                zone_id=sample_zone.id,
            )
            db_session.add(parcel)
        db_session.commit()

        # Test with limit=5
        response = client.get("/api/v1/addresses/autocomplete?q=Main&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

        # Test with limit=10 (default)
        response = client.get("/api/v1/addresses/autocomplete?q=Main")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10

        # Test with limit=20
        response = client.get("/api/v1/addresses/autocomplete?q=Main&limit=20")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 15  # Only 15 parcels exist

    def test_autocomplete_with_empty_query_validation_error(self, client):
        """Test autocomplete with empty query returns validation error."""
        response = client.get("/api/v1/addresses/autocomplete?q=")
        assert response.status_code == 422  # Validation error

    def test_autocomplete_with_single_char_validation_error(self, client):
        """Test autocomplete with single character returns validation error (min_length=2)."""
        response = client.get("/api/v1/addresses/autocomplete?q=a")
        assert response.status_code == 422

    def test_autocomplete_returns_empty_for_no_matches(self, client):
        """Test autocomplete returns empty list for query with no matches."""
        response = client.get("/api/v1/addresses/autocomplete?q=ZZNONEXISTENT")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_autocomplete_case_insensitive(self, client, sample_parcel):
        """Test autocomplete is case insensitive."""
        # Lowercase
        response_lower = client.get("/api/v1/addresses/autocomplete?q=test")
        assert response_lower.status_code == 200
        data_lower = response_lower.json()

        # Uppercase
        response_upper = client.get("/api/v1/addresses/autocomplete?q=TEST")
        assert response_upper.status_code == 200
        data_upper = response_upper.json()

        # Both should return the same result
        assert len(data_lower) == len(data_upper)
        if len(data_lower) > 0:
            assert data_lower[0]["address"] == data_upper[0]["address"]

    def test_autocomplete_includes_coordinates(self, client, sample_parcel):
        """Test autocomplete includes latitude and longitude."""
        response = client.get("/api/v1/addresses/autocomplete?q=Test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["latitude"] is not None
        assert data[0]["longitude"] is not None
        assert abs(data[0]["latitude"] - 51.0447) < 0.01
        assert abs(data[0]["longitude"] - (-114.0719)) < 0.01

    def test_autocomplete_max_limit_validation(self, client, sample_parcel):
        """Test autocomplete validates maximum limit (50)."""
        response = client.get("/api/v1/addresses/autocomplete?q=Test&limit=100")
        assert response.status_code == 422  # Exceeds max limit of 50


class TestAddressSearch:
    """Tests for the advanced address search endpoint."""

    def test_search_returns_results(self, client, sample_parcel):
        """Test search returns results for valid query."""
        response = client.get("/api/v1/addresses/search?query=Test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert "Test" in data[0]["address"]

    def test_search_with_community_filter(self, client, db_session, sample_zone):
        """Test search with community filter."""
        from app.models.zones import Parcel

        # Create parcels in different communities
        parcel1 = Parcel(
            address="100 Community A Street NW",
            street_name="Community A",
            community_name="Community A",
            quadrant="NW",
            zone_id=sample_zone.id,
        )
        parcel2 = Parcel(
            address="200 Community B Street NW",
            street_name="Community B",
            community_name="Community B",
            quadrant="NW",
            zone_id=sample_zone.id,
        )
        db_session.add_all([parcel1, parcel2])
        db_session.commit()

        # Search with community filter
        response = client.get("/api/v1/addresses/search?query=Street&community=Community A")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all("Community A" in p["community"] for p in data)

    def test_search_with_zone_filter(self, client, db_session):
        """Test search with zone filter."""
        from app.models.zones import Zone, Parcel

        # Create zones
        zone_rc1 = Zone(
            zone_code="R-C1",
            zone_name="Residential - Contextual One",
            category="residential",
        )
        zone_cc1 = Zone(
            zone_code="C-C1",
            zone_name="Commercial - Community 1",
            category="commercial",
        )
        db_session.add_all([zone_rc1, zone_cc1])
        db_session.flush()

        # Create parcels
        parcel_res = Parcel(
            address="100 Residential Street NW",
            street_name="Residential",
            community_name="Test",
            zone_id=zone_rc1.id,
            land_use_designation="R-C1",
        )
        parcel_com = Parcel(
            address="200 Commercial Street NW",
            street_name="Commercial",
            community_name="Test",
            zone_id=zone_cc1.id,
            land_use_designation="C-C1",
        )
        db_session.add_all([parcel_res, parcel_com])
        db_session.commit()

        # Search with zone filter for R-C1
        response = client.get("/api/v1/addresses/search?query=Street&zone=R-C1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(p["zone_code"] == "R-C1" for p in data)

        # Search with zone filter for C-C1
        response = client.get("/api/v1/addresses/search?query=Street&zone=C-C1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(p["zone_code"] == "C-C1" for p in data)

    def test_search_with_combined_filters(self, client, db_session):
        """Test search with both community and zone filters."""
        from app.models.zones import Zone, Parcel

        zone = Zone(
            zone_code="R-C2",
            zone_name="Residential - Contextual Two",
            category="residential",
        )
        db_session.add(zone)
        db_session.flush()

        parcel = Parcel(
            address="123 Combined Filter Street NW",
            street_name="Combined Filter",
            community_name="Beltline",
            zone_id=zone.id,
            land_use_designation="R-C2",
        )
        db_session.add(parcel)
        db_session.commit()

        response = client.get(
            "/api/v1/addresses/search?query=Combined&community=Beltline&zone=R-C2"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["community"] == "Beltline"
        assert data[0]["zone_code"] == "R-C2"

    def test_search_with_no_matches(self, client):
        """Test search returns empty for no matches."""
        response = client.get("/api/v1/addresses/search?query=NONEXISTENTADDRESS")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_search_respects_limit(self, client, db_session, sample_zone):
        """Test search respects limit parameter."""
        from app.models.zones import Parcel

        # Create multiple parcels
        for i in range(25):
            parcel = Parcel(
                address=f"{200 + i} Search Test Ave NW",
                street_name="Search Test",
                community_name="Downtown",
                zone_id=sample_zone.id,
            )
            db_session.add(parcel)
        db_session.commit()

        # Default limit is 20
        response = client.get("/api/v1/addresses/search?query=Search Test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 20

        # Custom limit
        response = client.get("/api/v1/addresses/search?query=Search Test&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_search_query_validation(self, client):
        """Test search validates query parameter."""
        # Query too short
        response = client.get("/api/v1/addresses/search?query=a")
        assert response.status_code == 422

        # Missing query
        response = client.get("/api/v1/addresses/search")
        assert response.status_code == 422

    def test_search_partial_zone_match(self, client, db_session):
        """Test search with partial zone code match."""
        from app.models.zones import Zone, Parcel

        zone = Zone(
            zone_code="M-CG",
            zone_name="Multi-Residential - Contextual Grade",
            category="residential",
        )
        db_session.add(zone)
        db_session.flush()

        parcel = Parcel(
            address="500 Multi Res Street NW",
            street_name="Multi Res",
            community_name="Mission",
            zone_id=zone.id,
            land_use_designation="M-CG",
        )
        db_session.add(parcel)
        db_session.commit()

        # Partial zone match (just "M-")
        response = client.get("/api/v1/addresses/search?query=Multi&zone=M-")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_search_partial_community_match(self, client, sample_parcel):
        """Test search with partial community name match."""
        response = client.get("/api/v1/addresses/search?query=Test&community=Test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert "Test" in data[0]["community"]
