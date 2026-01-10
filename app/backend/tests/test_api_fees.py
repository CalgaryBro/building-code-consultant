"""
Unit tests for Fees API endpoints.

Tests the Calgary Building Code Expert System permit fee calculator endpoints.
Based on the 2026 Building & Trade Permit Fee Schedule (R2026-02).
"""
import pytest
from unittest.mock import patch, MagicMock


class TestFeeScheduleEndpoint:
    """Tests for GET /api/v1/fees/schedule endpoint."""

    def test_get_fee_schedule_returns_valid_data(self, client):
        """Test that fee schedule returns expected structure."""
        response = client.get("/api/v1/fees/schedule")
        assert response.status_code == 200
        data = response.json()

        # Verify required fields
        assert "version" in data
        assert data["version"] == "R2026-02"
        assert "effective_date" in data
        assert "categories" in data
        assert "safety_codes_council_info" in data
        assert "policies" in data

        # Verify categories structure
        assert len(data["categories"]) >= 3  # Building, Trade, Additional
        category_names = [cat["name"] for cat in data["categories"]]
        assert "Building Permits" in category_names
        assert "Trade Permits" in category_names
        assert "Additional Fees" in category_names

    def test_get_fee_schedule_safety_codes_council_info(self, client):
        """Test that SCC info is included in fee schedule."""
        response = client.get("/api/v1/fees/schedule")
        assert response.status_code == 200
        data = response.json()

        scc = data["safety_codes_council_info"]
        assert "rate" in scc
        assert scc["rate"] == 0.04
        assert "minimum" in scc
        assert scc["minimum"] == 4.50
        assert "maximum" in scc
        assert scc["maximum"] == 560.00


class TestBuildingPermitFeeEndpoint:
    """Tests for POST /api/v1/fees/building-permit endpoint."""

    def test_building_permit_fee_commercial(self, client):
        """Test building permit fee calculation for commercial building."""
        response = client.post(
            "/api/v1/fees/building-permit",
            json={
                "building_type": "commercial",
                "construction_value": 1000000,
                "work_started_without_permit": False
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["building_type"] == "commercial"
        assert data["construction_value"] == 1000000
        assert "fee_breakdown" in data
        assert data["includes_trade_permits"] is False
        assert data["double_fee_applied"] is False

        # Verify fee calculation
        # $112 processing + $10.14 per $1,000 * 1000 = $112 + $10,140 = $10,252 + SCC
        breakdown = data["fee_breakdown"]
        assert breakdown["processing_fee"] == 112.00
        assert breakdown["base_fee"] == 10140.00  # 10.14 * 1000
        # SCC is 4% of ($112 + $10,140) = $410.08
        assert abs(breakdown["safety_codes_council_fee"] - 410.08) < 0.01
        assert breakdown["total"] > 10000

    def test_building_permit_fee_residential(self, client):
        """Test building permit fee calculation for residential (single family)."""
        response = client.post(
            "/api/v1/fees/building-permit",
            json={
                "building_type": "single_family",
                "construction_value": 500000,
                "work_started_without_permit": False
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["building_type"] == "single_family"
        assert data["includes_trade_permits"] is True  # Trade included for new residential

        # Verify fee calculation
        breakdown = data["fee_breakdown"]
        assert breakdown["processing_fee"] == 112.00
        # $10.14 per $1,000 * 500 = $5,070
        assert breakdown["base_fee"] == 5070.00
        assert "Trade permits" in " ".join(breakdown["notes"])

    def test_building_permit_fee_residential_alteration(self, client):
        """Test building permit fee for residential alteration (flat fee)."""
        response = client.post(
            "/api/v1/fees/building-permit",
            json={
                "building_type": "single_family",
                "alteration_type": "new_secondary_suite",
                "work_started_without_permit": False
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Flat fee for new secondary suite: $403.52
        breakdown = data["fee_breakdown"]
        assert breakdown["total"] == 403.52
        assert breakdown["processing_fee"] == 112.00
        assert breakdown["base_fee"] == 276.00
        assert breakdown["safety_codes_council_fee"] == 15.52

    def test_building_permit_fee_demolition(self, client):
        """Test building permit fee for demolition (per square metre)."""
        response = client.post(
            "/api/v1/fees/building-permit",
            json={
                "building_type": "demolition",
                "floor_area_sqm": 500.0,
                "work_started_without_permit": False
            }
        )
        assert response.status_code == 200
        data = response.json()

        # $112 processing + $1.44 per sq.m. * 500 = $112 + $720 = $832 + SCC
        breakdown = data["fee_breakdown"]
        assert breakdown["processing_fee"] == 112.00
        assert breakdown["base_fee"] == 720.00  # 1.44 * 500

    def test_building_permit_fee_double_fee_applied(self, client):
        """Test that double fee is applied when work started without permit."""
        response = client.post(
            "/api/v1/fees/building-permit",
            json={
                "building_type": "commercial",
                "construction_value": 100000,
                "work_started_without_permit": True
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["double_fee_applied"] is True
        breakdown = data["fee_breakdown"]

        # Verify double fee note
        assert any("DOUBLE FEE" in note for note in breakdown["notes"])

        # Calculate expected: normal fee doubled
        # Processing $112 + Base $1,014 ($10.14 * 100) + SCC (4% of $1,126 = $45.04)
        # Total = $1,171.04, doubled = $2,342.08
        # But need to verify actual logic

    def test_building_permit_fee_minimum_applied(self, client):
        """Test that minimum fee is applied for small construction values."""
        response = client.post(
            "/api/v1/fees/building-permit",
            json={
                "building_type": "commercial",
                "construction_value": 1000,  # Very low value
                "work_started_without_permit": False
            }
        )
        assert response.status_code == 200
        data = response.json()

        breakdown = data["fee_breakdown"]
        # Minimum total is $116.50
        assert breakdown["total"] >= 116.50

    def test_building_permit_fee_all_alteration_types(self, client):
        """Test all residential alteration types return correct flat fees."""
        alteration_fees = {
            "basement_garage_addition_small": 333.84,
            "new_secondary_suite": 403.52,
            "existing_secondary_suite": 205.92,
            "new_backyard_suite": 1302.08,
            "minor_alterations": 205.92,
            "addition_large": 1302.08,
        }

        for alteration_type, expected_fee in alteration_fees.items():
            response = client.post(
                "/api/v1/fees/building-permit",
                json={
                    "building_type": "single_family",
                    "alteration_type": alteration_type,
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["fee_breakdown"]["total"] == expected_fee, f"Failed for {alteration_type}"


class TestTradePermitFeesEndpoint:
    """Tests for POST /api/v1/fees/trade-permits endpoint."""

    def test_trade_permit_fee_electrical(self, client):
        """Test electrical trade permit fee calculation."""
        response = client.post(
            "/api/v1/fees/trade-permits",
            json={
                "trades": [
                    {"trade_type": "electrical", "construction_value": 50000}
                ],
                "work_started_without_permit": False
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert len(data["trade_permits"]) == 1
        assert data["trade_permits"][0]["trade_type"] == "electrical"
        assert data["double_fee_applied"] is False

        # $112 processing + $9.79 per $1,000 * 50 = $112 + $489.50 + SCC
        breakdown = data["trade_permits"][0]["fee_breakdown"]
        assert breakdown["processing_fee"] == 112.00
        assert abs(breakdown["base_fee"] - 489.50) < 0.01  # 9.79 * 50

    def test_trade_permit_fee_plumbing(self, client):
        """Test plumbing trade permit fee calculation."""
        response = client.post(
            "/api/v1/fees/trade-permits",
            json={
                "trades": [
                    {"trade_type": "plumbing", "construction_value": 30000}
                ],
                "work_started_without_permit": False
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["trade_permits"][0]["trade_type"] == "plumbing"
        # $9.79 per $1,000 * 30 = $293.70
        assert data["trade_permits"][0]["fee_breakdown"]["base_fee"] == 293.70

    def test_trade_permit_fee_gas(self, client):
        """Test gas trade permit fee calculation."""
        response = client.post(
            "/api/v1/fees/trade-permits",
            json={
                "trades": [
                    {"trade_type": "gas", "construction_value": 20000}
                ],
                "work_started_without_permit": False
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["trade_permits"][0]["trade_type"] == "gas"
        # $9.79 per $1,000 * 20 = $195.80
        assert abs(data["trade_permits"][0]["fee_breakdown"]["base_fee"] - 195.80) < 0.01

    def test_trade_permit_fee_multiple_trades(self, client):
        """Test multiple trade permits in single request."""
        response = client.post(
            "/api/v1/fees/trade-permits",
            json={
                "trades": [
                    {"trade_type": "electrical", "construction_value": 40000},
                    {"trade_type": "plumbing", "construction_value": 25000},
                    {"trade_type": "gas", "construction_value": 15000}
                ],
                "work_started_without_permit": False
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert len(data["trade_permits"]) == 3
        assert data["combined_total"] > 0

        # Verify combined total is sum of individual fees
        individual_totals = sum(t["fee_breakdown"]["total"] for t in data["trade_permits"])
        assert abs(data["combined_total"] - individual_totals) < 0.01

    def test_trade_permit_fee_homeowner(self, client):
        """Test homeowner permit flat fee."""
        response = client.post(
            "/api/v1/fees/trade-permits",
            json={
                "trades": [
                    {"trade_type": "electrical", "is_homeowner": True}
                ],
                "work_started_without_permit": False
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Homeowner permit flat fee: $116.50
        assert data["trade_permits"][0]["fee_breakdown"]["total"] == 116.50

    def test_trade_permit_fee_annual_electrical(self, client):
        """Test annual electrical permit flat fee."""
        response = client.post(
            "/api/v1/fees/trade-permits",
            json={
                "trades": [
                    {"trade_type": "annual_electrical"}
                ],
                "work_started_without_permit": False
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Annual electrical permit flat fee: $162.24
        assert data["trade_permits"][0]["fee_breakdown"]["total"] == 162.24


class TestDevelopmentPermitFeeEndpoint:
    """Tests for POST /api/v1/fees/development-permit endpoint."""

    def test_development_permit_fee_new_construction(self, client):
        """Test DP fee for new construction."""
        response = client.post(
            "/api/v1/fees/development-permit",
            json={
                "project_type": "new_construction",
                "floor_area_sqm": 500,
                "zone_category": "commercial",
                "requires_relaxation": False,
                "is_discretionary": False
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["project_type"] == "new_construction"
        assert data["floor_area_sqm"] == 500
        assert data["zone_category"] == "commercial"
        assert "fee_breakdown" in data
        assert len(data["notes"]) > 0  # Should have notes about DP being estimate

    def test_development_permit_fee_with_relaxation(self, client):
        """Test DP fee with zoning relaxation."""
        response = client.post(
            "/api/v1/fees/development-permit",
            json={
                "project_type": "new_construction",
                "floor_area_sqm": 300,
                "requires_relaxation": True,
                "is_discretionary": False
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Should include relaxation note
        assert any("relaxation" in note.lower() for note in data["notes"])

    def test_development_permit_fee_discretionary(self, client):
        """Test DP fee for discretionary use."""
        response = client.post(
            "/api/v1/fees/development-permit",
            json={
                "project_type": "change_of_use",
                "is_discretionary": True
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Should include discretionary note
        assert any("discretionary" in note.lower() for note in data["notes"])


class TestLotGradingFeeEndpoint:
    """Tests for POST /api/v1/fees/lot-grading endpoint."""

    def test_lot_grading_fee_single_family(self, client):
        """Test lot grading fee for single family dwelling."""
        response = client.post(
            "/api/v1/fees/lot-grading",
            json={
                "building_type": "single_family",
                "dwelling_units": 1,
                "ground_floor_units": 1
            }
        )
        assert response.status_code == 200
        data = response.json()

        # $20 per ground floor unit * 1 = $20
        assert data["total_fee"] == 20.00
        assert data["fee_type"] == "Small Residential"

    def test_lot_grading_fee_duplex(self, client):
        """Test lot grading fee for duplex."""
        response = client.post(
            "/api/v1/fees/lot-grading",
            json={
                "building_type": "duplex",
                "dwelling_units": 2,
                "ground_floor_units": 2
            }
        )
        assert response.status_code == 200
        data = response.json()

        # $20 per ground floor unit * 2 = $40
        assert data["total_fee"] == 40.00

    def test_lot_grading_fee_commercial(self, client):
        """Test lot grading fee for commercial building."""
        response = client.post(
            "/api/v1/fees/lot-grading",
            json={
                "building_type": "commercial",
                "lot_area_hectares": 2.5
            }
        )
        assert response.status_code == 200
        data = response.json()

        # $80 per hectare * 2.5 = $200
        assert data["total_fee"] == 200.00
        assert data["fee_type"] == "Commercial/Industrial/High-rise"

    def test_lot_grading_fee_minimum(self, client):
        """Test lot grading fee minimum for commercial."""
        response = client.post(
            "/api/v1/fees/lot-grading",
            json={
                "building_type": "commercial",
                "lot_area_hectares": 0.5  # Would be $40 but min is $80
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Minimum is $80
        assert data["total_fee"] == 80.00


class TestInspectionFeeEndpoint:
    """Tests for POST /api/v1/fees/inspection endpoint."""

    def test_inspection_fee_re_inspection(self, client):
        """Test re-inspection fee."""
        response = client.post(
            "/api/v1/fees/inspection",
            json={"inspection_type": "re_inspection"}
        )
        assert response.status_code == 200
        data = response.json()

        assert data["inspection_type"] == "re_inspection"
        # $300 base + $12 SCC + $15 GST = $327
        assert data["fee_breakdown"]["total"] == 327.00

    def test_inspection_fee_safety_inspection(self, client):
        """Test safety inspection fee."""
        response = client.post(
            "/api/v1/fees/inspection",
            json={"inspection_type": "safety_inspection"}
        )
        assert response.status_code == 200
        data = response.json()

        assert data["inspection_type"] == "safety_inspection"
        # $5,620 base + $224.80 SCC + $281 GST = $6,125.80
        assert data["fee_breakdown"]["total"] == 6125.80

    def test_inspection_fee_weekend_holiday(self, client):
        """Test weekend/holiday inspection fee."""
        response = client.post(
            "/api/v1/fees/inspection",
            json={
                "inspection_type": "weekend_holiday",
                "hours": 6
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["inspection_type"] == "weekend_holiday"
        # $180/hour * 6 = $1,080 + $9/hour SCC * 6 = $54, total $1,134
        assert data["fee_breakdown"]["base_fee"] == 1080.00
        assert data["fee_breakdown"]["safety_codes_council_fee"] == 54.00
        assert data["fee_breakdown"]["total"] == 1134.00

    def test_inspection_fee_weekend_minimum_hours(self, client):
        """Test weekend inspection fee with less than minimum hours."""
        response = client.post(
            "/api/v1/fees/inspection",
            json={
                "inspection_type": "weekend_holiday",
                "hours": 2  # Below minimum of 4
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Should use minimum 4 hours
        # $180 * 4 = $720 + $9 * 4 = $36, total $756
        assert data["fee_breakdown"]["total"] == 756.00
        assert any("minimum" in note.lower() for note in data["fee_breakdown"]["notes"])

    def test_inspection_fee_invalid_type(self, client):
        """Test invalid inspection type returns error."""
        response = client.post(
            "/api/v1/fees/inspection",
            json={"inspection_type": "invalid_type"}
        )
        assert response.status_code == 400


class TestExtensionFeeEndpoint:
    """Tests for POST /api/v1/fees/extension endpoint."""

    def test_extension_fee_calculation(self, client):
        """Test extension fee is 10% of original permit fee."""
        response = client.post(
            "/api/v1/fees/extension",
            json={"original_permit_fee": 5000}
        )
        assert response.status_code == 200
        data = response.json()

        assert data["original_permit_fee"] == 5000
        # $112 processing + 10% of $5000 = $500 + SCC
        breakdown = data["fee_breakdown"]
        assert breakdown["processing_fee"] == 112.00
        assert breakdown["base_fee"] == 500.00

    def test_extension_fee_minimum(self, client):
        """Test extension fee minimum."""
        response = client.post(
            "/api/v1/fees/extension",
            json={"original_permit_fee": 500}  # 10% = $50, below min of $112
        )
        assert response.status_code == 200
        data = response.json()

        # Minimum base fee is $112
        assert data["fee_breakdown"]["base_fee"] == 112.00

    def test_extension_fee_maximum(self, client):
        """Test extension fee maximum."""
        response = client.post(
            "/api/v1/fees/extension",
            json={"original_permit_fee": 100000}  # 10% = $10,000, above max
        )
        assert response.status_code == 200
        data = response.json()

        # Maximum base fee is $8,852
        assert data["fee_breakdown"]["base_fee"] == 8852.00


class TestQuickEstimateEndpoint:
    """Tests for POST /api/v1/fees/quick-estimate endpoint."""

    def test_quick_estimate_commercial(self, client):
        """Test quick estimate for commercial building."""
        response = client.post(
            "/api/v1/fees/quick-estimate",
            json={
                "building_type": "commercial",
                "construction_value": 500000
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert "building_permit_fee" in data
        assert "total_estimate" in data
        assert "notes" in data
        assert data["building_permit_fee"] > 0
        assert data["total_estimate"] >= data["building_permit_fee"]

        # Commercial should have trade permit estimate
        assert data["trade_permit_fee"] is not None

    def test_quick_estimate_residential(self, client):
        """Test quick estimate for residential building."""
        response = client.post(
            "/api/v1/fees/quick-estimate",
            json={
                "building_type": "single_family",
                "construction_value": 400000
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["building_permit_fee"] > 0
        # Trade permits included in BP for residential
        assert any("included" in note.lower() for note in data["notes"])

    def test_quick_estimate_correct_total(self, client):
        """Test quick estimate total is sum of components."""
        response = client.post(
            "/api/v1/fees/quick-estimate",
            json={
                "building_type": "commercial",
                "construction_value": 1000000
            }
        )
        assert response.status_code == 200
        data = response.json()

        expected_total = data["building_permit_fee"]
        if data["trade_permit_fee"]:
            expected_total += data["trade_permit_fee"]

        assert abs(data["total_estimate"] - expected_total) < 0.01


class TestCompleteProjectEstimateEndpoint:
    """Tests for POST /api/v1/fees/estimate endpoint."""

    def test_complete_estimate_new_construction(self, client):
        """Test complete project estimate for new commercial construction."""
        response = client.post(
            "/api/v1/fees/estimate",
            json={
                "project_name": "New Office Building",
                "project_type": "new_construction",
                "building_type": "commercial",
                "construction_value": 2000000,
                "floor_area_sqm": 1000,
                "requires_development_permit": True,
                "requires_building_permit": True,
                "include_lot_grading": True,
                "lot_area_hectares": 0.5,
                "work_started_without_permit": False
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert data["project_name"] == "New Office Building"
        assert data["project_type"] == "new_construction"
        assert data["building_type"] == "commercial"
        assert "development_permit_fees" in data
        assert "building_permit_fees" in data
        assert "additional_fees" in data
        assert "total_estimate" in data
        assert "fee_summary" in data

        # DP and BP should have fees
        assert data["development_permit_fees"] is not None
        assert data["building_permit_fees"] is not None
        assert data["total_estimate"] > 0

    def test_complete_estimate_with_trade_permits(self, client):
        """Test complete estimate with explicit trade permits."""
        response = client.post(
            "/api/v1/fees/estimate",
            json={
                "project_type": "renovation",
                "building_type": "commercial_alteration",
                "construction_value": 500000,
                "requires_development_permit": False,
                "requires_building_permit": True,
                "trade_permits": [
                    {"trade_type": "electrical", "construction_value": 100000},
                    {"trade_type": "plumbing", "construction_value": 50000}
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["trade_permit_fees"] is not None
        assert data["total_estimate"] > 0

    def test_complete_estimate_residential_trades_included(self, client):
        """Test that trade permits are included for new residential."""
        response = client.post(
            "/api/v1/fees/estimate",
            json={
                "project_type": "new_construction",
                "building_type": "single_family",
                "construction_value": 600000,
                "dwelling_units": 1,
                "requires_development_permit": True,
                "requires_building_permit": True
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Trade permits should be included in BP fee for new residential
        assert any("included" in note.lower() for note in data["notes"])

    def test_complete_estimate_double_fee_warning(self, client):
        """Test that double fee warning is included when work started."""
        response = client.post(
            "/api/v1/fees/estimate",
            json={
                "project_type": "new_construction",
                "building_type": "commercial",
                "construction_value": 500000,
                "requires_building_permit": True,
                "work_started_without_permit": True
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["double_fee_applied"] is True
        assert any("double" in warning.lower() for warning in data["warnings"])

    def test_complete_estimate_with_lot_grading(self, client):
        """Test complete estimate includes lot grading fees."""
        response = client.post(
            "/api/v1/fees/estimate",
            json={
                "project_type": "new_construction",
                "building_type": "single_family",
                "construction_value": 500000,
                "dwelling_units": 1,
                "ground_floor_units": 1,
                "requires_development_permit": True,
                "requires_building_permit": True,
                "include_lot_grading": True
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["additional_fees"] is not None
        # Should include lot grading
        lot_grading_items = [
            item for item in data["additional_fees"]["line_items"]
            if "lot grading" in item["name"].lower()
        ]
        assert len(lot_grading_items) > 0

    def test_complete_estimate_fee_schedule_version(self, client):
        """Test that fee schedule version is included."""
        response = client.post(
            "/api/v1/fees/estimate",
            json={
                "project_type": "new_construction",
                "building_type": "commercial",
                "construction_value": 100000,
                "requires_building_permit": True
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["fee_schedule_version"] == "R2026-02"


class TestBuildingTypesEndpoint:
    """Tests for GET /api/v1/fees/building-types endpoint."""

    def test_list_building_types(self, client):
        """Test listing available building types."""
        response = client.get("/api/v1/fees/building-types")
        assert response.status_code == 200
        data = response.json()

        # Verify categories
        assert "residential" in data
        assert "multi_family" in data
        assert "commercial" in data
        assert "other" in data

        # Verify residential types
        residential_values = [t["value"] for t in data["residential"]]
        assert "single_family" in residential_values
        assert "semi_detached" in residential_values
        assert "duplex" in residential_values

    def test_building_types_have_labels(self, client):
        """Test that all building types have labels."""
        response = client.get("/api/v1/fees/building-types")
        assert response.status_code == 200
        data = response.json()

        for category in data.values():
            for building_type in category:
                assert "value" in building_type
                assert "label" in building_type
                assert len(building_type["label"]) > 0


class TestAlterationTypesEndpoint:
    """Tests for GET /api/v1/fees/alteration-types endpoint."""

    def test_list_alteration_types(self, client):
        """Test listing residential alteration types."""
        response = client.get("/api/v1/fees/alteration-types")
        assert response.status_code == 200
        data = response.json()

        assert "alterations" in data
        alterations = data["alterations"]
        assert len(alterations) >= 6

    def test_alteration_types_have_fees(self, client):
        """Test that alteration types include total fees."""
        response = client.get("/api/v1/fees/alteration-types")
        assert response.status_code == 200
        data = response.json()

        for alteration in data["alterations"]:
            assert "value" in alteration
            assert "label" in alteration
            assert "total_fee" in alteration
            assert alteration["total_fee"] > 0

    def test_alteration_type_specific_fees(self, client):
        """Test specific alteration type fees match schedule."""
        response = client.get("/api/v1/fees/alteration-types")
        assert response.status_code == 200
        data = response.json()

        fee_map = {alt["value"]: alt["total_fee"] for alt in data["alterations"]}

        assert fee_map["basement_garage_addition_small"] == 333.84
        assert fee_map["new_secondary_suite"] == 403.52
        assert fee_map["existing_secondary_suite"] == 205.92
        assert fee_map["new_backyard_suite"] == 1302.08
        assert fee_map["minor_alterations"] == 205.92
        assert fee_map["addition_large"] == 1302.08


class TestTradeTypesEndpoint:
    """Tests for GET /api/v1/fees/trade-types endpoint."""

    def test_list_trade_types(self, client):
        """Test listing trade permit types."""
        response = client.get("/api/v1/fees/trade-types")
        assert response.status_code == 200
        data = response.json()

        assert "standard" in data
        assert "special" in data

        # Verify standard trades
        standard_values = [t["value"] for t in data["standard"]]
        assert "electrical" in standard_values
        assert "plumbing" in standard_values
        assert "gas" in standard_values
        assert "hvac" in standard_values

    def test_special_trade_types_have_flat_fees(self, client):
        """Test that special trade types include flat fees."""
        response = client.get("/api/v1/fees/trade-types")
        assert response.status_code == 200
        data = response.json()

        for special in data["special"]:
            assert "flat_fee" in special
            assert special["flat_fee"] > 0

    def test_special_trade_type_fees(self, client):
        """Test specific special trade type fees."""
        response = client.get("/api/v1/fees/trade-types")
        assert response.status_code == 200
        data = response.json()

        fee_map = {t["value"]: t["flat_fee"] for t in data["special"]}

        assert fee_map["homeowner"] == 116.50
        assert fee_map["annual_electrical"] == 162.24


class TestErrorHandling:
    """Tests for API error handling."""

    def test_building_permit_invalid_building_type(self, client):
        """Test error for invalid building type."""
        response = client.post(
            "/api/v1/fees/building-permit",
            json={
                "building_type": "invalid_type",
                "construction_value": 100000
            }
        )
        assert response.status_code == 422  # Validation error

    def test_missing_required_field(self, client):
        """Test error for missing required field."""
        response = client.post(
            "/api/v1/fees/building-permit",
            json={}  # Missing building_type
        )
        assert response.status_code == 422

    def test_negative_construction_value(self, client):
        """Test error for negative construction value."""
        response = client.post(
            "/api/v1/fees/building-permit",
            json={
                "building_type": "commercial",
                "construction_value": -1000
            }
        )
        assert response.status_code == 422

    def test_trade_permit_empty_trades_list(self, client):
        """Test trade permit with empty trades list."""
        response = client.post(
            "/api/v1/fees/trade-permits",
            json={
                "trades": [],
                "work_started_without_permit": False
            }
        )
        # Should work but return 0 total
        assert response.status_code == 200
        data = response.json()
        assert data["combined_total"] == 0

    def test_extension_fee_zero_permit_fee(self, client):
        """Test extension fee with zero original permit fee."""
        response = client.post(
            "/api/v1/fees/extension",
            json={"original_permit_fee": 0}
        )
        assert response.status_code == 200
        data = response.json()
        # Should apply minimum
        assert data["fee_breakdown"]["total"] >= 116.50


class TestFeeCalculationAccuracy:
    """Tests to verify fee calculation accuracy against fee schedule."""

    def test_scc_fee_minimum(self, client):
        """Test that SCC fee respects $4.50 minimum."""
        response = client.post(
            "/api/v1/fees/trade-permits",
            json={
                "trades": [
                    {"trade_type": "electrical", "is_homeowner": True}
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Homeowner permit has $4.50 SCC
        assert data["trade_permits"][0]["fee_breakdown"]["safety_codes_council_fee"] == 4.50

    def test_scc_fee_maximum(self, client):
        """Test that SCC fee respects $560 maximum."""
        response = client.post(
            "/api/v1/fees/building-permit",
            json={
                "building_type": "commercial",
                "construction_value": 5000000  # Very high value
            }
        )
        assert response.status_code == 200
        data = response.json()

        # SCC should be capped at $560
        assert data["fee_breakdown"]["safety_codes_council_fee"] == 560.00

    def test_processing_fee_consistency(self, client):
        """Test that processing fee is consistently $112."""
        building_types = ["commercial", "hotel", "warehouse", "single_family"]

        for bt in building_types:
            response = client.post(
                "/api/v1/fees/building-permit",
                json={
                    "building_type": bt,
                    "construction_value": 500000
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["fee_breakdown"]["processing_fee"] == 112.00

    def test_trade_permit_rate(self, client):
        """Test trade permit rate of $9.79 per $1,000."""
        response = client.post(
            "/api/v1/fees/trade-permits",
            json={
                "trades": [
                    {"trade_type": "electrical", "construction_value": 100000}
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()

        # $9.79 per $1,000 * 100 = $979
        assert abs(data["trade_permits"][0]["fee_breakdown"]["base_fee"] - 979.00) < 0.01

    def test_building_permit_rate(self, client):
        """Test building permit rate of $10.14 per $1,000."""
        response = client.post(
            "/api/v1/fees/building-permit",
            json={
                "building_type": "commercial",
                "construction_value": 100000
            }
        )
        assert response.status_code == 200
        data = response.json()

        # $10.14 per $1,000 * 100 = $1,014
        assert data["fee_breakdown"]["base_fee"] == 1014.00
