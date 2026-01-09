"""
Models for Calgary zoning, zone rules, and parcels.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime,
    Numeric, ForeignKey, Index
)
from sqlalchemy.orm import relationship

from ..database import Base
from .codes import UUID  # Import cross-database UUID type


class Zone(Base):
    """
    Represents a Calgary Land Use Bylaw zone designation.
    Examples: R-C1, R-C2, M-CG, C-COR1, I-G
    """
    __tablename__ = "zones"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    code_id = Column(UUID(), ForeignKey("codes.id"), nullable=True)  # Link to Land Use Bylaw

    zone_code = Column(String(20), nullable=False, unique=True)  # e.g., "R-C1", "M-CG"
    zone_name = Column(String(255), nullable=False)  # Full name
    category = Column(String(50), nullable=False)  # residential, commercial, industrial, mixed, direct_control
    district = Column(String(100), nullable=True)  # e.g., "RESIDENTIAL", "COMMERCIAL"
    description = Column(Text, nullable=True)
    bylaw_url = Column(Text, nullable=True)  # Link to LUB section

    # Common rules stored directly for quick access
    max_height_m = Column(Numeric, nullable=True)
    max_storeys = Column(Integer, nullable=True)
    max_far = Column(Numeric, nullable=True)  # Floor Area Ratio
    min_front_setback_m = Column(Numeric, nullable=True)
    min_side_setback_m = Column(Numeric, nullable=True)
    min_rear_setback_m = Column(Numeric, nullable=True)
    min_parking_stalls = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rules = relationship("ZoneRule", back_populates="zone", cascade="all, delete-orphan")
    parcels = relationship("Parcel", back_populates="zone")

    __table_args__ = (
        Index("idx_zones_code", "zone_code"),
        Index("idx_zones_category", "category"),
    )


class ZoneRule(Base):
    """
    Detailed rules for a zone that may have conditions.
    Examples: setback rules that vary by lot width, height rules with bonusing.
    """
    __tablename__ = "zone_rules"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    zone_id = Column(UUID(), ForeignKey("zones.id"), nullable=False)

    rule_type = Column(String(50), nullable=False)  # setback_front, setback_side, height, FAR, parking, use
    description = Column(Text, nullable=True)
    min_value = Column(Numeric, nullable=True)
    max_value = Column(Numeric, nullable=True)
    unit = Column(String(20), nullable=True)  # m, storeys, stalls, ratio
    calculation_formula = Column(Text, nullable=True)  # e.g., "0.25 * lot_depth" for rear setback
    conditions = Column(Text, nullable=True)  # Additional conditions as JSON string
    exceptions = Column(Text, nullable=True)
    bylaw_reference = Column(String(100), nullable=True)  # Section reference in LUB

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    zone = relationship("Zone", back_populates="rules")

    __table_args__ = (
        Index("idx_zone_rules_zone_type", "zone_id", "rule_type"),
    )


class Parcel(Base):
    """
    Represents a land parcel in Calgary with address and zoning information.
    Data from Open Calgary API.
    """
    __tablename__ = "parcels"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)

    # Address information
    address = Column(String(255), nullable=False)
    street_name = Column(String(100), nullable=True)
    street_type = Column(String(20), nullable=True)  # ST, AVE, DR, etc.
    street_direction = Column(String(5), nullable=True)  # N, S, E, W, NE, NW, SE, SW
    house_number = Column(String(20), nullable=True)
    unit_number = Column(String(20), nullable=True)

    # Location
    community_name = Column(String(100), nullable=True)
    community_code = Column(String(10), nullable=True)
    quadrant = Column(String(5), nullable=True)  # NE, NW, SE, SW
    postal_code = Column(String(10), nullable=True)

    # Zoning
    zone_id = Column(UUID(), ForeignKey("zones.id"), nullable=True)
    land_use_designation = Column(String(50), nullable=True)  # The zone code as stored in source data

    # Parcel details
    legal_description = Column(String(255), nullable=True)
    roll_number = Column(String(50), nullable=True)  # City's internal ID
    area_sqm = Column(Numeric, nullable=True)
    frontage_m = Column(Numeric, nullable=True)
    depth_m = Column(Numeric, nullable=True)

    # Geometry (stored as text for SQLite compatibility, PostGIS for PostgreSQL)
    latitude = Column(Numeric, nullable=True)
    longitude = Column(Numeric, nullable=True)
    geometry = Column(Text, nullable=True)  # WKT format for cross-database compatibility

    # Source tracking
    source_id = Column(String(50), nullable=True)  # ID from Open Calgary
    source_updated = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    zone = relationship("Zone", back_populates="parcels")
    projects = relationship("Project", back_populates="parcel")

    __table_args__ = (
        Index("idx_parcels_address", "address"),
        Index("idx_parcels_community", "community_name"),
        Index("idx_parcels_zone", "zone_id"),
    )
