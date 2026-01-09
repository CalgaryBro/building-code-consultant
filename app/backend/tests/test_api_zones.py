"""
Unit tests for Zones & Parcels API endpoints.
"""
import pytest
from uuid import uuid4


class TestZoneEndpoints:
    """Tests for zone-related endpoints."""

    def test_list_zones_empty(self, client):
        """Test listing zones when database is empty."""
        response = client.get("/api/v1/zones/zones")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_zones_with_data(self, client, sample_zone):
        """Test listing zones with data."""
        response = client.get("/api/v1/zones/zones")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["zone_code"] == "R-C1"

    def test_list_zones_filter_by_category(self, client, db_session, sample_zone):
        """Test filtering zones by category."""
        # Add commercial zone
        from app.models.zones import Zone
        commercial = Zone(
            zone_code="C-C1",
            zone_name="Commercial - Community 1",
            category="commercial",
        )
        db_session.add(commercial)
        db_session.commit()

        # Filter by residential
        response = client.get("/api/v1/zones/zones?category=residential")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "residential"

    def test_get_zone_by_code(self, client, sample_zone):
        """Test getting a zone by its code."""
        response = client.get("/api/v1/zones/zones/R-C1")
        assert response.status_code == 200
        data = response.json()
        assert data["zone_code"] == "R-C1"
        assert data["zone_name"] == "Residential - Contextual One Dwelling District"

    def test_get_zone_case_insensitive(self, client, sample_zone):
        """Test zone lookup is case insensitive."""
        response = client.get("/api/v1/zones/zones/r-c1")
        assert response.status_code == 200
        assert response.json()["zone_code"] == "R-C1"

    def test_get_zone_not_found(self, client):
        """Test getting a non-existent zone."""
        response = client.get("/api/v1/zones/zones/FAKE-ZONE")
        assert response.status_code == 404

    def test_get_zone_rules(self, client, db_session, sample_zone):
        """Test getting rules for a zone."""
        from app.models.zones import ZoneRule
        rule = ZoneRule(
            zone_id=sample_zone.id,
            rule_type="setback_front",
            min_value=6.0,
            unit="m",
        )
        db_session.add(rule)
        db_session.commit()

        response = client.get("/api/v1/zones/zones/R-C1/rules")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_get_zone_rules_filter_by_type(self, client, db_session, sample_zone):
        """Test filtering zone rules by type."""
        from app.models.zones import ZoneRule
        rule1 = ZoneRule(zone_id=sample_zone.id, rule_type="setback_front", min_value=6.0)
        rule2 = ZoneRule(zone_id=sample_zone.id, rule_type="height", max_value=10)
        db_session.add_all([rule1, rule2])
        db_session.commit()

        response = client.get("/api/v1/zones/zones/R-C1/rules?rule_type=height")
        assert response.status_code == 200
        data = response.json()
        assert all(r["rule_type"] == "height" for r in data)


class TestParcelEndpoints:
    """Tests for parcel-related endpoints."""

    def test_search_parcels_empty(self, client):
        """Test searching parcels with no results."""
        response = client.get("/api/v1/zones/parcels/search?query=nonexistent")
        assert response.status_code == 200
        assert response.json() == []

    def test_search_parcels_with_results(self, client, sample_parcel):
        """Test searching parcels with results."""
        response = client.get("/api/v1/zones/parcels/search?query=Test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert "Test" in data[0]["address"]

    def test_search_parcels_by_address(self, client, sample_parcel):
        """Test searching parcels by address."""
        response = client.get("/api/v1/zones/parcels/search?query=123")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_search_parcels_filter_by_community(self, client, sample_parcel):
        """Test filtering parcel search by community."""
        response = client.get("/api/v1/zones/parcels/search?query=Test&community=Test Community")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["community_name"] == "Test Community"

    def test_search_parcels_with_limit(self, client, sample_parcel):
        """Test parcel search with limit."""
        response = client.get("/api/v1/zones/parcels/search?query=Test&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 1

    def test_search_parcels_query_too_short(self, client):
        """Test parcel search with query too short."""
        response = client.get("/api/v1/zones/parcels/search?query=ab")
        assert response.status_code == 422

    def test_get_parcel_by_id(self, client, sample_parcel):
        """Test getting a parcel by ID."""
        response = client.get(f"/api/v1/zones/parcels/{sample_parcel.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["address"] == "123 Test Street NW"

    def test_get_parcel_not_found(self, client):
        """Test getting a non-existent parcel."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/zones/parcels/{fake_id}")
        assert response.status_code == 404


class TestZoningCheckEndpoints:
    """Tests for zoning compliance check endpoints."""

    def test_check_zoning_by_parcel_id(self, client, sample_parcel, sample_zone):
        """Test zoning check by parcel ID."""
        response = client.post(
            "/api/v1/zones/check-zoning",
            json={
                "parcel_id": str(sample_parcel.id),
                "building_height_m": 8.0,
                "building_storeys": 2,
                "front_setback_m": 6.5,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "checks" in data
        assert "overall_status" in data
        assert "zone" in data

    def test_check_zoning_by_address(self, client, sample_parcel, sample_zone):
        """Test zoning check by address."""
        response = client.post(
            "/api/v1/zones/check-zoning",
            json={
                "address": "123 Test Street",
                "building_height_m": 8.0,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["parcel"]["address"] == "123 Test Street NW"

    def test_check_zoning_height_pass(self, client, sample_parcel, sample_zone):
        """Test zoning check where height passes."""
        response = client.post(
            "/api/v1/zones/check-zoning",
            json={
                "parcel_id": str(sample_parcel.id),
                "building_height_m": 8.0,  # Zone max is 10m
            }
        )
        assert response.status_code == 200
        data = response.json()
        height_checks = [c for c in data["checks"] if "Height" in c["check_name"]]
        assert len(height_checks) > 0
        assert height_checks[0]["status"] == "pass"

    def test_check_zoning_height_fail(self, client, sample_parcel, sample_zone):
        """Test zoning check where height fails."""
        response = client.post(
            "/api/v1/zones/check-zoning",
            json={
                "parcel_id": str(sample_parcel.id),
                "building_height_m": 12.0,  # Zone max is 10m
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "fail"
        height_checks = [c for c in data["checks"] if "Height" in c["check_name"]]
        assert height_checks[0]["status"] == "fail"

    def test_check_zoning_setback_pass(self, client, sample_parcel, sample_zone):
        """Test zoning check where setback passes."""
        response = client.post(
            "/api/v1/zones/check-zoning",
            json={
                "parcel_id": str(sample_parcel.id),
                "front_setback_m": 7.0,  # Zone min is 6.0m
            }
        )
        assert response.status_code == 200
        data = response.json()
        setback_checks = [c for c in data["checks"] if "Setback" in c["check_name"]]
        assert len(setback_checks) > 0
        assert setback_checks[0]["status"] == "pass"

    def test_check_zoning_setback_fail(self, client, sample_parcel, sample_zone):
        """Test zoning check where setback fails."""
        response = client.post(
            "/api/v1/zones/check-zoning",
            json={
                "parcel_id": str(sample_parcel.id),
                "front_setback_m": 4.0,  # Zone min is 6.0m
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "fail"

    def test_check_zoning_no_parameters(self, client, sample_parcel):
        """Test zoning check with no parameters provided."""
        response = client.post(
            "/api/v1/zones/check-zoning",
            json={"parcel_id": str(sample_parcel.id)}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "needs_review"
        assert len(data["checks"]) == 0

    def test_check_zoning_parcel_not_found(self, client):
        """Test zoning check with non-existent parcel."""
        response = client.post(
            "/api/v1/zones/check-zoning",
            json={"parcel_id": str(uuid4())}
        )
        assert response.status_code == 404

    def test_check_zoning_address_not_found(self, client):
        """Test zoning check with address that doesn't match any parcel."""
        response = client.post(
            "/api/v1/zones/check-zoning",
            json={"address": "999 Nonexistent Street"}
        )
        assert response.status_code == 404


class TestCommunityEndpoints:
    """Tests for community endpoints."""

    def test_list_communities(self, client, sample_parcel):
        """Test listing communities."""
        response = client.get("/api/v1/zones/communities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["community_name"] == "Test Community"

    def test_list_communities_filter_by_quadrant(self, client, sample_parcel):
        """Test filtering communities by quadrant."""
        response = client.get("/api/v1/zones/communities?quadrant=NW")
        assert response.status_code == 200
        data = response.json()
        assert all(c["quadrant"] == "NW" for c in data)

    def test_list_communities_with_parcel_count(self, client, sample_parcel):
        """Test that communities include parcel count."""
        response = client.get("/api/v1/zones/communities")
        assert response.status_code == 200
        data = response.json()
        assert "parcel_count" in data[0]
        assert data[0]["parcel_count"] >= 1
