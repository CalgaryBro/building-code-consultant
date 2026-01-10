"""
Fee Calculator Service for Calgary Building Code Expert System.

This service calculates accurate permit fees based on the
2026 Building & Trade Permit Fee Schedule (R2026-02).

Functions:
- calculate_dp_fee: Development Permit fee estimation
- calculate_bp_fee: Building Permit fee calculation
- calculate_trade_fees: Trade permit fees (electrical/plumbing/gas/HVAC)
- get_total_fees: Combined fee estimate for a project
"""
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

from ..schemas.fees import (
    # Enums
    BuildingType, ResidentialAlterationType, TradePermitType,
    ProjectType, ZoneCategory,
    # Request/Response schemas
    FeeBreakdown, FeeLineItem,
    BuildingPermitFeeRequest, BuildingPermitFeeResponse,
    TradePermitRequest, TradePermitFeeRequest, TradePermitFeeResponse, TradePermitFeeItem,
    DevelopmentPermitFeeRequest, DevelopmentPermitFeeResponse,
    ProjectFeeEstimateRequest, ProjectFeeEstimateResponse, FeeCategorySummary,
    LotGradingFeeRequest, LotGradingFeeResponse,
    InspectionFeeRequest, InspectionFeeResponse,
    ExtensionFeeRequest, ExtensionFeeResponse,
    FeeScheduleResponse, FeeScheduleCategory,
)


class FeeCalculatorService:
    """
    Service for calculating Calgary building and trade permit fees.

    Based on the 2026 Building & Trade Permit Fee Schedule (R2026-02).
    """

    def __init__(self, fee_data_path: Optional[str] = None):
        """
        Initialize the fee calculator with fee schedule data.

        Args:
            fee_data_path: Path to the fee schedule JSON file.
                          If None, uses default location.
        """
        if fee_data_path is None:
            # Default path relative to this file
            base_dir = Path(__file__).parent.parent.parent
            fee_data_path = base_dir / "data" / "fees" / "permit_fees_2026.json"

        self.fee_data_path = Path(fee_data_path)
        self._fee_data: Optional[Dict[str, Any]] = None

    @property
    def fee_data(self) -> Dict[str, Any]:
        """Load and cache fee schedule data."""
        if self._fee_data is None:
            if not self.fee_data_path.exists():
                raise FileNotFoundError(
                    f"Fee schedule data not found at {self.fee_data_path}"
                )
            with open(self.fee_data_path, 'r') as f:
                self._fee_data = json.load(f)
        return self._fee_data

    def _calculate_scc_fee(self, permit_fee: float) -> float:
        """
        Calculate Safety Codes Council fee.

        4% of permit fee, minimum $4.50, maximum $560.
        """
        scc_info = self.fee_data.get("safety_codes_council_fee", {})
        rate = scc_info.get("rate", 0.04)
        minimum = scc_info.get("minimum", 4.50)
        maximum = scc_info.get("maximum", 560.00)

        scc_fee = permit_fee * rate
        return max(minimum, min(maximum, scc_fee))

    def _get_building_type_category(self, building_type: BuildingType) -> Tuple[str, str]:
        """
        Map building type enum to fee schedule category and subcategory.

        Returns:
            Tuple of (category, subcategory)
        """
        mapping = {
            BuildingType.COMMERCIAL: ("commercial", "new_building"),
            BuildingType.HOTEL: ("commercial", "new_hotel"),
            BuildingType.WAREHOUSE: ("commercial", "new_warehouse"),
            BuildingType.CARE_FACILITY: ("commercial", "new_care_facility"),
            BuildingType.MULTI_FAMILY_HIGH_RISE: ("commercial", "multi_family_high_rise"),
            BuildingType.MULTI_FAMILY_LOW_RISE: ("commercial", "multi_family_low_rise"),
            BuildingType.SINGLE_FAMILY: ("residential", "new_dwelling"),
            BuildingType.SEMI_DETACHED: ("residential", "new_dwelling"),
            BuildingType.DUPLEX: ("residential", "new_dwelling"),
            BuildingType.COMMERCIAL_ALTERATION: ("commercial", "alterations"),
            BuildingType.DEMOLITION: ("demolition", "standard"),
        }
        return mapping.get(building_type, ("commercial", "new_building"))

    def calculate_bp_fee(
        self,
        building_type: BuildingType,
        construction_value: Optional[float] = None,
        floor_area_sqm: Optional[float] = None,
        alteration_type: Optional[ResidentialAlterationType] = None,
        dwelling_units: Optional[int] = None,
        work_started_without_permit: bool = False,
    ) -> BuildingPermitFeeResponse:
        """
        Calculate Building Permit fees.

        Args:
            building_type: Type of building (residential, commercial, etc.)
            construction_value: Estimated construction value in CAD
            floor_area_sqm: Floor area in square metres (for demolition)
            alteration_type: Type of residential alteration (if applicable)
            dwelling_units: Number of dwelling units
            work_started_without_permit: If True, double fee applies

        Returns:
            BuildingPermitFeeResponse with fee breakdown
        """
        bp_data = self.fee_data.get("building_permits", {})
        line_items = []
        notes = []

        processing_fee = 0.0
        base_fee = 0.0

        # Handle residential alterations with flat fees
        if alteration_type:
            alt_data = bp_data.get("residential_alterations", {}).get(alteration_type.value, {})
            if alt_data:
                processing_fee = alt_data.get("processing_fee", 112.00)
                base_fee = alt_data.get("base_fee", 0.0)
                scc_fee = alt_data.get("scc_fee", self._calculate_scc_fee(base_fee))
                total = alt_data.get("total_fee", processing_fee + base_fee + scc_fee)

                line_items.append(FeeLineItem(
                    name="Processing Fee",
                    amount=processing_fee,
                    description="Permit processing fee"
                ))
                line_items.append(FeeLineItem(
                    name="Permit Base Fee",
                    amount=base_fee,
                    description=alt_data.get("description", "")
                ))
                line_items.append(FeeLineItem(
                    name="Safety Codes Council Fee",
                    amount=scc_fee,
                    description="4% of permit fee"
                ))

                # Apply double fee if work started without permit
                if work_started_without_permit:
                    total *= 2
                    notes.append("DOUBLE FEE APPLIED: Work started without permit")

                breakdown = FeeBreakdown(
                    processing_fee=processing_fee,
                    base_fee=base_fee,
                    safety_codes_council_fee=scc_fee,
                    subtotal=processing_fee + base_fee + scc_fee,
                    total=total,
                    line_items=line_items,
                    notes=notes,
                )

                return BuildingPermitFeeResponse(
                    building_type=building_type,
                    construction_value=construction_value,
                    floor_area_sqm=floor_area_sqm,
                    fee_breakdown=breakdown,
                    includes_trade_permits=False,
                    double_fee_applied=work_started_without_permit,
                )

        # Get fee schedule for building type
        category, subcategory = self._get_building_type_category(building_type)
        fee_schedule = bp_data.get(category, {}).get(subcategory, {})

        if not fee_schedule:
            # Fallback to commercial new building
            fee_schedule = bp_data.get("commercial", {}).get("new_building", {})

        processing_fee = fee_schedule.get("processing_fee", 112.00)

        # Calculate base fee based on calculation method
        fee_unit = fee_schedule.get("base_fee_unit", "per_1000_construction_value")
        fee_rate = fee_schedule.get("base_fee_rate", 10.14)

        if fee_unit == "per_1000_construction_value" and construction_value:
            base_fee = (construction_value / 1000) * fee_rate
            line_items.append(FeeLineItem(
                name="Permit Base Fee",
                amount=base_fee,
                calculation_basis=f"${fee_rate} per $1,000 of ${construction_value:,.2f} construction value"
            ))
        elif fee_unit == "per_square_metre" and floor_area_sqm:
            base_fee = floor_area_sqm * fee_rate
            line_items.append(FeeLineItem(
                name="Permit Base Fee",
                amount=base_fee,
                calculation_basis=f"${fee_rate} per sq.m. x {floor_area_sqm:,.2f} sq.m."
            ))
        else:
            # Use minimum if no value provided
            minimum_total = fee_schedule.get("minimum_total", 116.50)
            base_fee = minimum_total - processing_fee - 4.50  # Approximate
            notes.append("Minimum fee applied - provide construction value for accurate estimate")

        line_items.insert(0, FeeLineItem(
            name="Processing Fee",
            amount=processing_fee,
            description="Permit processing fee"
        ))

        # Calculate SCC fee
        scc_fee = self._calculate_scc_fee(processing_fee + base_fee)
        line_items.append(FeeLineItem(
            name="Safety Codes Council Fee",
            amount=scc_fee,
            description="4% of permit fee (min $4.50, max $560)"
        ))

        subtotal = processing_fee + base_fee + scc_fee
        total = subtotal

        # Check minimum
        minimum_total = fee_schedule.get("minimum_total", 116.50)
        if total < minimum_total:
            total = minimum_total
            notes.append(f"Minimum fee of ${minimum_total} applied")

        # Apply double fee if work started without permit
        if work_started_without_permit:
            total *= 2
            notes.append("DOUBLE FEE APPLIED: Work started without permit")

        # Check if trade permits are included (new residential)
        includes_trades = building_type in [
            BuildingType.SINGLE_FAMILY,
            BuildingType.SEMI_DETACHED,
            BuildingType.DUPLEX,
        ] and not alteration_type

        if includes_trades:
            notes.append("Trade permits (electrical, gas, mechanical, plumbing) are included in this Building Permit fee")

        breakdown = FeeBreakdown(
            processing_fee=processing_fee,
            base_fee=base_fee,
            safety_codes_council_fee=scc_fee,
            subtotal=subtotal,
            total=total,
            line_items=line_items,
            notes=notes,
        )

        return BuildingPermitFeeResponse(
            building_type=building_type,
            construction_value=construction_value,
            floor_area_sqm=floor_area_sqm,
            fee_breakdown=breakdown,
            includes_trade_permits=includes_trades,
            double_fee_applied=work_started_without_permit,
        )

    def calculate_trade_fees(
        self,
        trades: List[TradePermitRequest],
        work_started_without_permit: bool = False,
    ) -> TradePermitFeeResponse:
        """
        Calculate Trade Permit fees for electrical, plumbing, gas, HVAC.

        Args:
            trades: List of trade permits needed with their construction values
            work_started_without_permit: If True, double fee applies

        Returns:
            TradePermitFeeResponse with individual and combined fees
        """
        trade_data = self.fee_data.get("trade_permits", {})
        trade_items = []
        combined_total = 0.0

        for trade in trades:
            line_items = []
            notes = []

            if trade.is_homeowner:
                # Homeowner permit - flat fee
                fee_info = trade_data.get("homeowner", {})
                processing_fee = fee_info.get("processing_fee", 0.0)
                base_fee = fee_info.get("base_fee", 112.00)
                scc_fee = fee_info.get("scc_fee", 4.50)
                total = fee_info.get("total_fee", 116.50)

                line_items.append(FeeLineItem(
                    name="Homeowner Permit Fee",
                    amount=base_fee,
                    description="Flat fee for homeowner permits"
                ))
                line_items.append(FeeLineItem(
                    name="Safety Codes Council Fee",
                    amount=scc_fee,
                    description="4% of permit fee"
                ))

            elif trade.trade_type == TradePermitType.ANNUAL_ELECTRICAL:
                # Annual electrical permit - flat fee
                fee_info = trade_data.get("annual_electrical", {})
                processing_fee = fee_info.get("processing_fee", 0.0)
                base_fee = fee_info.get("base_fee", 156.00)
                scc_fee = fee_info.get("scc_fee", 6.24)
                total = fee_info.get("total_fee", 162.24)

                line_items.append(FeeLineItem(
                    name="Annual Electrical Permit Fee",
                    amount=base_fee,
                    description="Annual permit for electrical work"
                ))
                line_items.append(FeeLineItem(
                    name="Safety Codes Council Fee",
                    amount=scc_fee,
                    description="4% of permit fee"
                ))

            else:
                # Standard trade permit - based on construction value
                fee_info = trade_data.get("standard", {})
                processing_fee = fee_info.get("processing_fee", 112.00)
                fee_rate = fee_info.get("base_fee_rate", 9.79)

                if trade.construction_value and trade.construction_value > 0:
                    base_fee = (trade.construction_value / 1000) * fee_rate
                    line_items.append(FeeLineItem(
                        name="Processing Fee",
                        amount=processing_fee,
                        description="Permit processing fee"
                    ))
                    line_items.append(FeeLineItem(
                        name=f"{trade.trade_type.value.title()} Permit Base Fee",
                        amount=base_fee,
                        calculation_basis=f"${fee_rate} per $1,000 of ${trade.construction_value:,.2f}"
                    ))
                else:
                    # Minimum fee
                    base_fee = 0.0
                    total = fee_info.get("minimum_total", 116.50)
                    notes.append("Minimum fee applied - provide construction value for accurate estimate")
                    line_items.append(FeeLineItem(
                        name="Processing Fee",
                        amount=processing_fee,
                        description="Permit processing fee"
                    ))

                scc_fee = self._calculate_scc_fee(processing_fee + base_fee)
                line_items.append(FeeLineItem(
                    name="Safety Codes Council Fee",
                    amount=scc_fee,
                    description="4% of permit fee (min $4.50, max $560)"
                ))

                total = processing_fee + base_fee + scc_fee
                minimum_total = fee_info.get("minimum_total", 116.50)
                if total < minimum_total:
                    total = minimum_total
                    notes.append(f"Minimum fee of ${minimum_total} applied")

            # Apply double fee if applicable
            if work_started_without_permit:
                total *= 2
                notes.append("DOUBLE FEE APPLIED: Work started without permit")

            breakdown = FeeBreakdown(
                processing_fee=processing_fee,
                base_fee=base_fee,
                safety_codes_council_fee=scc_fee,
                subtotal=processing_fee + base_fee + scc_fee,
                total=total,
                line_items=line_items,
                notes=notes,
            )

            trade_items.append(TradePermitFeeItem(
                trade_type=trade.trade_type,
                construction_value=trade.construction_value,
                fee_breakdown=breakdown,
            ))

            combined_total += total

        return TradePermitFeeResponse(
            trade_permits=trade_items,
            combined_total=combined_total,
            double_fee_applied=work_started_without_permit,
        )

    def calculate_dp_fee(
        self,
        project_type: ProjectType,
        floor_area_sqm: Optional[float] = None,
        zone_category: Optional[ZoneCategory] = None,
        requires_relaxation: bool = False,
        is_discretionary: bool = False,
    ) -> DevelopmentPermitFeeResponse:
        """
        Estimate Development Permit fees.

        Note: Development Permit fees in Calgary vary significantly based on
        project complexity, location, and other factors. This provides an
        estimate based on typical scenarios.

        Args:
            project_type: Type of project (new construction, renovation, etc.)
            floor_area_sqm: Proposed floor area
            zone_category: Zoning category
            requires_relaxation: Whether zoning relaxations are needed
            is_discretionary: Whether this is a discretionary use

        Returns:
            DevelopmentPermitFeeResponse with estimated fees
        """
        line_items = []
        notes = [
            "Development Permit fees vary based on project complexity and review requirements.",
            "Contact the Planning Services Centre for an accurate quote.",
        ]

        # Base DP processing fee (estimate)
        processing_fee = 112.00  # Similar to BP processing fee

        # Base fee varies by project type and size
        # These are estimates based on typical DP applications
        base_fee = 0.0

        if project_type == ProjectType.NEW_CONSTRUCTION:
            if floor_area_sqm and floor_area_sqm > 0:
                # Estimate: roughly $1-2 per sq.m. for DP review
                base_fee = floor_area_sqm * 1.50
                line_items.append(FeeLineItem(
                    name="DP Base Fee (Estimated)",
                    amount=base_fee,
                    calculation_basis=f"~$1.50 per sq.m. x {floor_area_sqm:,.2f} sq.m."
                ))
            else:
                base_fee = 500.00  # Minimum estimate for new construction
                line_items.append(FeeLineItem(
                    name="DP Base Fee (Estimated)",
                    amount=base_fee,
                    description="Estimated minimum for new construction"
                ))

        elif project_type in [ProjectType.ADDITION, ProjectType.RENOVATION, ProjectType.ALTERATION]:
            base_fee = 300.00  # Estimate for alterations
            line_items.append(FeeLineItem(
                name="DP Base Fee (Estimated)",
                amount=base_fee,
                description="Estimated fee for alterations/additions"
            ))

        elif project_type == ProjectType.CHANGE_OF_USE:
            base_fee = 400.00  # Estimate for change of use
            line_items.append(FeeLineItem(
                name="DP Base Fee (Estimated)",
                amount=base_fee,
                description="Estimated fee for change of use"
            ))

        else:
            base_fee = 200.00
            line_items.append(FeeLineItem(
                name="DP Base Fee (Estimated)",
                amount=base_fee,
                description="Estimated minimum DP fee"
            ))

        line_items.insert(0, FeeLineItem(
            name="Processing Fee",
            amount=processing_fee,
            description="Application processing fee"
        ))

        # Additional fees for relaxations
        if requires_relaxation:
            relaxation_fee = 200.00  # Estimate
            base_fee += relaxation_fee
            line_items.append(FeeLineItem(
                name="Relaxation Review Fee (Estimated)",
                amount=relaxation_fee,
                description="Additional fee for zoning relaxation review"
            ))
            notes.append("Relaxation requests may require additional review time and fees.")

        # Additional fees for discretionary use
        if is_discretionary:
            discretionary_fee = 150.00  # Estimate
            base_fee += discretionary_fee
            line_items.append(FeeLineItem(
                name="Discretionary Use Fee (Estimated)",
                amount=discretionary_fee,
                description="Additional fee for discretionary use review"
            ))
            notes.append("Discretionary use applications require additional review.")

        # SCC fee
        scc_fee = self._calculate_scc_fee(processing_fee + base_fee)
        line_items.append(FeeLineItem(
            name="Safety Codes Council Fee",
            amount=scc_fee,
            description="4% of permit fee"
        ))

        total = processing_fee + base_fee + scc_fee

        breakdown = FeeBreakdown(
            processing_fee=processing_fee,
            base_fee=base_fee,
            safety_codes_council_fee=scc_fee,
            subtotal=total,
            total=total,
            line_items=line_items,
            notes=notes,
        )

        return DevelopmentPermitFeeResponse(
            project_type=project_type,
            floor_area_sqm=floor_area_sqm,
            zone_category=zone_category,
            fee_breakdown=breakdown,
            notes=notes,
        )

    def calculate_lot_grading_fee(
        self,
        building_type: BuildingType,
        dwelling_units: Optional[int] = None,
        ground_floor_units: Optional[int] = None,
        storeys: Optional[int] = None,
        lot_area_hectares: Optional[float] = None,
    ) -> LotGradingFeeResponse:
        """
        Calculate lot grading fees.

        Based on Lot Grading Bylaw 32M2004.
        """
        lot_grading = self.fee_data.get("additional_fees", {}).get("lot_grading", {})
        notes = []

        # Determine which fee category applies
        if building_type in [BuildingType.SINGLE_FAMILY, BuildingType.SEMI_DETACHED, BuildingType.DUPLEX]:
            # Small residential
            fee_info = lot_grading.get("small_residential", {})
            rate = fee_info.get("rate", 20.00)
            units = ground_floor_units or dwelling_units or 1
            total = rate * units
            fee_type = "Small Residential"
            calculation = f"${rate} x {units} ground floor unit(s)"

        elif building_type in [BuildingType.MULTI_FAMILY_LOW_RISE]:
            # Multi-family small (< 10 units or <= 3 storeys)
            if dwelling_units and dwelling_units >= 10 and storeys and storeys <= 3:
                fee_info = lot_grading.get("multi_family_small", {})
                base = fee_info.get("base_fee", 100.00)
                rate = fee_info.get("rate", 10.00)
                units = ground_floor_units or dwelling_units
                total = base + (rate * units)
                fee_type = "Multi-family (10+ units, up to 3 storeys)"
                calculation = f"${base} + ${rate} x {units} ground floor unit(s)"
            else:
                fee_info = lot_grading.get("small_residential", {})
                rate = fee_info.get("rate", 20.00)
                units = ground_floor_units or dwelling_units or 1
                total = rate * units
                fee_type = "Multi-family (< 10 units)"
                calculation = f"${rate} x {units} ground floor unit(s)"

        else:
            # Large commercial/industrial or high-rise multi-family
            fee_info = lot_grading.get("large_commercial_industrial", {})
            rate = fee_info.get("rate", 80.00)
            minimum = fee_info.get("minimum", 80.00)
            hectares = lot_area_hectares or 1.0
            total = max(minimum, rate * hectares)
            fee_type = "Commercial/Industrial/High-rise"
            calculation = f"${rate} x {hectares:.2f} hectare(s) (min ${minimum})"
            if not lot_area_hectares:
                notes.append("Provide lot area in hectares for accurate calculation")

        return LotGradingFeeResponse(
            fee_type=fee_type,
            total_fee=total,
            calculation_basis=calculation,
            notes=notes,
        )

    def calculate_inspection_fee(
        self,
        inspection_type: str,
        hours: Optional[float] = None,
    ) -> InspectionFeeResponse:
        """Calculate inspection fees."""
        inspection_data = self.fee_data.get("additional_fees", {}).get("inspections", {})
        line_items = []
        notes = []

        if inspection_type == "safety_inspection":
            fee_info = inspection_data.get("safety_inspection", {})
            base_fee = fee_info.get("base_fee", 5620.00)
            scc_fee = fee_info.get("scc_fee", 224.80)
            gst = fee_info.get("gst", 281.00)
            total = fee_info.get("total_fee", 6125.80)

            line_items = [
                FeeLineItem(name="Safety Inspection Fee", amount=base_fee),
                FeeLineItem(name="Safety Codes Council Fee", amount=scc_fee),
                FeeLineItem(name="GST", amount=gst),
            ]

        elif inspection_type == "weekend_holiday":
            fee_info = inspection_data.get("weekend_holiday", {})
            hourly_rate = fee_info.get("hourly_rate", 180.00)
            min_hours = fee_info.get("minimum_hours", 4)
            scc_hourly = fee_info.get("scc_fee_hourly", 9.00)

            actual_hours = max(hours or min_hours, min_hours)
            base_fee = hourly_rate * actual_hours
            scc_fee = scc_hourly * actual_hours
            total = base_fee + scc_fee

            line_items = [
                FeeLineItem(
                    name="Weekend/Holiday Inspection",
                    amount=base_fee,
                    calculation_basis=f"${hourly_rate}/hour x {actual_hours} hours"
                ),
                FeeLineItem(
                    name="Safety Codes Council Fee",
                    amount=scc_fee,
                    calculation_basis=f"${scc_hourly}/hour x {actual_hours} hours"
                ),
            ]
            if hours and hours < min_hours:
                notes.append(f"Minimum {min_hours} hours applies")
            gst = 0.0

        elif inspection_type == "re_inspection":
            fee_info = inspection_data.get("re_inspection", {})
            base_fee = fee_info.get("base_fee", 300.00)
            scc_fee = fee_info.get("scc_fee", 12.00)
            gst = fee_info.get("gst", 15.00)
            total = fee_info.get("total_fee", 327.00)

            line_items = [
                FeeLineItem(name="Re-inspection Fee", amount=base_fee),
                FeeLineItem(name="Safety Codes Council Fee", amount=scc_fee),
                FeeLineItem(name="GST", amount=gst),
            ]

        else:
            raise ValueError(f"Unknown inspection type: {inspection_type}")

        breakdown = FeeBreakdown(
            processing_fee=0.0,
            base_fee=base_fee,
            safety_codes_council_fee=scc_fee,
            gst=gst if 'gst' in locals() else 0.0,
            subtotal=total,
            total=total,
            line_items=line_items,
            notes=notes,
        )

        return InspectionFeeResponse(
            inspection_type=inspection_type,
            fee_breakdown=breakdown,
        )

    def calculate_extension_fee(
        self,
        original_permit_fee: float,
    ) -> ExtensionFeeResponse:
        """Calculate permit extension fee."""
        extension_data = self.fee_data.get("additional_fees", {}).get("extensions", {})

        processing_fee = extension_data.get("processing_fee", 112.00)
        rate = extension_data.get("base_fee_rate", 0.10)
        minimum = extension_data.get("base_fee_minimum", 112.00)
        maximum = extension_data.get("base_fee_maximum", 8852.00)

        base_fee = original_permit_fee * rate
        base_fee = max(minimum, min(maximum, base_fee))

        scc_fee = self._calculate_scc_fee(processing_fee + base_fee)
        total = processing_fee + base_fee + scc_fee

        minimum_total = extension_data.get("minimum_total", 116.50)
        if total < minimum_total:
            total = minimum_total

        line_items = [
            FeeLineItem(name="Processing Fee", amount=processing_fee),
            FeeLineItem(
                name="Extension Fee",
                amount=base_fee,
                calculation_basis=f"10% of ${original_permit_fee:,.2f} (min ${minimum}, max ${maximum})"
            ),
            FeeLineItem(name="Safety Codes Council Fee", amount=scc_fee),
        ]

        breakdown = FeeBreakdown(
            processing_fee=processing_fee,
            base_fee=base_fee,
            safety_codes_council_fee=scc_fee,
            subtotal=total,
            total=total,
            line_items=line_items,
        )

        return ExtensionFeeResponse(
            original_permit_fee=original_permit_fee,
            extension_fee=total,
            fee_breakdown=breakdown,
        )

    def get_total_fees(
        self,
        request: ProjectFeeEstimateRequest,
    ) -> ProjectFeeEstimateResponse:
        """
        Calculate combined fee estimate for a complete project.

        This is the main entry point for comprehensive fee estimation,
        combining DP, BP, trade permits, and additional fees.

        Args:
            request: Complete project fee estimate request

        Returns:
            ProjectFeeEstimateResponse with all fees broken down
        """
        fee_summaries = []
        warnings = []
        notes = [
            "This is an estimate based on the 2026 Fee Schedule (R2026-02).",
            "Actual fees may vary based on project specifics and review requirements.",
            "Contact the Planning Services Centre for official fee calculations.",
        ]

        total_estimate = 0.0
        dp_fees = None
        bp_fees = None
        trade_fees = None
        additional_fees = None

        # Development Permit fees
        if request.requires_development_permit:
            dp_response = self.calculate_dp_fee(
                project_type=request.project_type,
                floor_area_sqm=request.floor_area_sqm,
                zone_category=request.zone_category,
                requires_relaxation=request.requires_relaxation,
            )
            dp_fees = dp_response.fee_breakdown
            total_estimate += dp_fees.total

            fee_summaries.append(FeeCategorySummary(
                category="Development Permit",
                subtotal=dp_fees.total,
                items=dp_fees.line_items,
            ))

        # Building Permit fees
        if request.requires_building_permit:
            bp_response = self.calculate_bp_fee(
                building_type=request.building_type,
                construction_value=request.construction_value,
                floor_area_sqm=request.floor_area_sqm,
                alteration_type=request.alteration_type,
                dwelling_units=request.dwelling_units,
                work_started_without_permit=request.work_started_without_permit,
            )
            bp_fees = bp_response.fee_breakdown
            total_estimate += bp_fees.total

            fee_summaries.append(FeeCategorySummary(
                category="Building Permit",
                subtotal=bp_fees.total,
                items=bp_fees.line_items,
            ))

            if bp_response.includes_trade_permits:
                notes.append("Trade permits are included in the Building Permit fee for new residential dwellings.")

            if bp_response.double_fee_applied:
                warnings.append("DOUBLE FEE: Work started without permit - fees are doubled.")

        # Trade Permit fees (if not included in BP and requested)
        if request.trade_permits and not (bp_fees and request.building_type in [
            BuildingType.SINGLE_FAMILY, BuildingType.SEMI_DETACHED, BuildingType.DUPLEX
        ] and not request.alteration_type):
            trade_response = self.calculate_trade_fees(
                trades=request.trade_permits,
                work_started_without_permit=request.work_started_without_permit,
            )

            # Create combined breakdown for trade permits
            trade_line_items = []
            for trade_item in trade_response.trade_permits:
                trade_line_items.append(FeeLineItem(
                    name=f"{trade_item.trade_type.value.title()} Permit",
                    amount=trade_item.fee_breakdown.total,
                    description=f"Construction value: ${trade_item.construction_value:,.2f}" if trade_item.construction_value else None
                ))

            trade_fees = FeeBreakdown(
                processing_fee=sum(t.fee_breakdown.processing_fee for t in trade_response.trade_permits),
                base_fee=sum(t.fee_breakdown.base_fee for t in trade_response.trade_permits),
                safety_codes_council_fee=sum(t.fee_breakdown.safety_codes_council_fee for t in trade_response.trade_permits),
                subtotal=trade_response.combined_total,
                total=trade_response.combined_total,
                line_items=trade_line_items,
            )
            total_estimate += trade_response.combined_total

            fee_summaries.append(FeeCategorySummary(
                category="Trade Permits",
                subtotal=trade_response.combined_total,
                items=trade_line_items,
            ))

        # Additional fees (lot grading, water, etc.)
        additional_line_items = []
        additional_total = 0.0

        if request.include_lot_grading:
            lot_grading = self.calculate_lot_grading_fee(
                building_type=request.building_type,
                dwelling_units=request.dwelling_units,
                ground_floor_units=request.ground_floor_units,
                storeys=request.storeys,
                lot_area_hectares=request.lot_area_hectares,
            )
            additional_line_items.append(FeeLineItem(
                name="Lot Grading Fee",
                amount=lot_grading.total_fee,
                calculation_basis=lot_grading.calculation_basis,
            ))
            additional_total += lot_grading.total_fee

        # Water fee for residential
        if request.dwelling_units and request.building_type in [
            BuildingType.SINGLE_FAMILY, BuildingType.SEMI_DETACHED, BuildingType.DUPLEX,
            BuildingType.MULTI_FAMILY_LOW_RISE, BuildingType.MULTI_FAMILY_HIGH_RISE,
        ]:
            water_rate = self.fee_data.get("additional_fees", {}).get("other", {}).get("water_fee", {}).get("rate", 26.13)
            water_fee = water_rate * request.dwelling_units
            additional_line_items.append(FeeLineItem(
                name="Water Fee",
                amount=water_fee,
                calculation_basis=f"${water_rate} x {request.dwelling_units} dwelling unit(s)",
            ))
            additional_total += water_fee

        if additional_line_items:
            additional_fees = FeeBreakdown(
                subtotal=additional_total,
                total=additional_total,
                line_items=additional_line_items,
            )
            total_estimate += additional_total

            fee_summaries.append(FeeCategorySummary(
                category="Additional Fees",
                subtotal=additional_total,
                items=additional_line_items,
            ))

        # Warnings
        if request.work_started_without_permit:
            warnings.append("Work has started without a permit. Double fees apply.")

        if not request.construction_value:
            warnings.append("No construction value provided. Minimum fees may be applied.")

        return ProjectFeeEstimateResponse(
            project_name=request.project_name,
            project_type=request.project_type,
            building_type=request.building_type,
            development_permit_fees=dp_fees,
            building_permit_fees=bp_fees,
            trade_permit_fees=trade_fees,
            additional_fees=additional_fees,
            subtotal=total_estimate,
            total_estimate=total_estimate,
            fee_summary=fee_summaries,
            warnings=warnings,
            notes=notes,
            double_fee_applied=request.work_started_without_permit,
            fee_schedule_version=self.fee_data.get("version", "R2026-02"),
        )

    def get_fee_schedule(self) -> FeeScheduleResponse:
        """
        Get the complete fee schedule data.

        Returns:
            FeeScheduleResponse with all fee categories and policies
        """
        categories = []

        # Building Permits
        bp_items = []
        bp_data = self.fee_data.get("building_permits", {})
        for category, items in bp_data.items():
            for item_key, item_data in items.items():
                bp_items.append({
                    "category": category,
                    "type": item_key,
                    **item_data
                })
        categories.append(FeeScheduleCategory(
            name="Building Permits",
            description="Fees for building permit applications",
            items=bp_items,
        ))

        # Trade Permits
        trade_items = []
        trade_data = self.fee_data.get("trade_permits", {})
        for item_key, item_data in trade_data.items():
            trade_items.append({
                "type": item_key,
                **item_data
            })
        categories.append(FeeScheduleCategory(
            name="Trade Permits",
            description="Fees for electrical, gas, mechanical, and plumbing permits",
            items=trade_items,
        ))

        # Additional Fees
        additional_items = []
        additional_data = self.fee_data.get("additional_fees", {})
        for category, items in additional_data.items():
            if isinstance(items, dict):
                for item_key, item_data in items.items():
                    if isinstance(item_data, dict):
                        additional_items.append({
                            "category": category,
                            "type": item_key,
                            **item_data
                        })
                    else:
                        additional_items.append({
                            "category": category,
                            "type": item_key,
                            "value": item_data
                        })
        categories.append(FeeScheduleCategory(
            name="Additional Fees",
            description="Extensions, inspections, lot grading, and other fees",
            items=additional_items,
        ))

        return FeeScheduleResponse(
            version=self.fee_data.get("version", "R2026-02"),
            effective_date=self.fee_data.get("effective_date", "2026-01-01"),
            categories=categories,
            safety_codes_council_info=self.fee_data.get("safety_codes_council_fee", {}),
            policies=self.fee_data.get("policies", {}),
        )


# Singleton instance for easy import
fee_calculator = FeeCalculatorService()
