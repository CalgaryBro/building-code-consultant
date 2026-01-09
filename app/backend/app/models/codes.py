"""
Models for building codes, articles, and requirements.
"""
import uuid
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, Integer, Boolean, Date, DateTime,
    Numeric, ForeignKey, Enum, Index, CheckConstraint, TypeDecorator
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, ARRAY, TSVECTOR
from sqlalchemy.types import CHAR
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from ..database import Base


# Custom UUID type that works with both PostgreSQL and SQLite
class UUID(TypeDecorator):
    """Platform-independent UUID type."""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            else:
                return str(uuid.UUID(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


# Custom Array type for cross-database compatibility
class StringArray(TypeDecorator):
    """Array type that works with both PostgreSQL and SQLite."""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(ARRAY(String))
        else:
            return dialect.type_descriptor(Text)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        # For SQLite, store as JSON string
        import json
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        # For SQLite, parse JSON string
        import json
        if isinstance(value, list):
            return value
        return json.loads(value)


# Optional Vector type
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # Fallback for when pgvector is not available
    class Vector(TypeDecorator):
        impl = Text
        cache_ok = True

        def __init__(self, dim=None, *args, **kwargs):
            self.dim = dim
            super().__init__(*args, **kwargs)

        def process_bind_param(self, value, dialect):
            if value is None:
                return value
            import json
            return json.dumps(value)

        def process_result_value(self, value, dialect):
            if value is None:
                return value
            import json
            return json.loads(value)


class CodeType(str, PyEnum):
    """Types of codes/standards."""
    BUILDING = "building"
    FIRE = "fire"
    ENERGY = "energy"
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    ZONING = "zoning"
    STANDATA = "standata"


class RequirementType(str, PyEnum):
    """Types of requirements."""
    DIMENSIONAL = "dimensional"
    MATERIAL = "material"
    PROCEDURAL = "procedural"
    PERFORMANCE = "performance"


class ConfidenceLevel(str, PyEnum):
    """Confidence levels for extracted data."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NOT_FOUND = "NOT_FOUND"
    CRITICAL = "CRITICAL"


class Code(Base):
    """
    Represents a building code, bylaw, or standard.
    Examples: NBC(AE) 2023, Land Use Bylaw 1P2007, STANDATA 23-BCB-001
    """
    __tablename__ = "codes"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    code_type = Column(String(50), nullable=False)  # building, fire, energy, zoning, standata
    name = Column(String(255), nullable=False)  # e.g., "National Building Code"
    short_name = Column(String(50), nullable=False)  # e.g., "NBC(AE)"
    version = Column(String(50), nullable=False)  # e.g., "2023"
    jurisdiction = Column(String(100), nullable=False)  # e.g., "Alberta", "Calgary"
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)  # When superseded
    source_url = Column(Text, nullable=True)
    source_file = Column(String(255), nullable=True)  # Local file path
    is_current = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    articles = relationship("Article", back_populates="code", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_codes_type_current", "code_type", "is_current"),
    )


class Article(Base):
    """
    Represents a code article/section.
    Examples: 9.8.4.1 (Stair Width), 9.10.9 (Fire Separations)
    """
    __tablename__ = "articles"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    code_id = Column(UUID(), ForeignKey("codes.id"), nullable=False)
    article_number = Column(String(50), nullable=False)  # e.g., "9.8.4.1"
    title = Column(String(255), nullable=True)
    full_text = Column(Text, nullable=False)  # Exact code language
    parent_article_id = Column(UUID(), ForeignKey("articles.id"), nullable=True)
    part_number = Column(Integer, nullable=True)  # e.g., 9 for Part 9
    division_number = Column(Integer, nullable=True)
    section_number = Column(Integer, nullable=True)
    page_number = Column(Integer, nullable=True)

    # Full-text search vector (Text for SQLite, TSVECTOR for PostgreSQL)
    search_vector = Column(Text, nullable=True)

    # Vector embedding for semantic search (1536 dimensions for OpenAI, 384 for sentence-transformers)
    embedding = Column(Vector(384), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    code = relationship("Code", back_populates="articles")
    requirements = relationship("Requirement", back_populates="article", cascade="all, delete-orphan")
    parent = relationship("Article", remote_side=[id], backref="children")

    __table_args__ = (
        Index("idx_articles_code_number", "code_id", "article_number"),
        Index("idx_articles_search", "search_vector", postgresql_using="gin", postgresql_ops={"search_vector": "gin_trgm_ops"}),
    )


class Requirement(Base):
    """
    A specific, checkable requirement extracted from a code article.
    Examples: stair_width >= 860mm, fire_rating = 45min
    """
    __tablename__ = "requirements"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(), ForeignKey("articles.id"), nullable=False)

    # What this requirement is about
    requirement_type = Column(String(50), nullable=False)  # dimensional, material, procedural, performance
    element = Column(String(100), nullable=False)  # e.g., "stair_width", "fire_rating"
    description = Column(Text, nullable=True)

    # The actual requirement values
    min_value = Column(Numeric, nullable=True)
    max_value = Column(Numeric, nullable=True)
    exact_value = Column(String(255), nullable=True)  # For non-numeric requirements
    unit = Column(String(20), nullable=True)  # mm, m, minutes, storeys, m²

    # The exact quote from the code
    exact_quote = Column(Text, nullable=False)

    # When this requirement applies (conditions are in separate table)
    is_mandatory = Column(Boolean, default=True)
    applies_to_part_9 = Column(Boolean, default=True)
    applies_to_part_3 = Column(Boolean, default=False)
    occupancy_groups = Column(StringArray(), nullable=True)  # A1, A2, B1, B2, C, D, E, F1, F2, F3

    # Extraction tracking
    extraction_method = Column(String(50), nullable=False, default="manual")  # llm_assisted, manual, import
    extraction_confidence = Column(String(20), nullable=True)  # HIGH, MEDIUM, LOW
    extraction_date = Column(DateTime, default=datetime.utcnow)
    extraction_model = Column(String(100), nullable=True)  # qwen3-vl:8b, gpt-4, etc.

    # Source traceability
    source_document = Column(String(255), nullable=False)
    source_page = Column(Integer, nullable=True)
    source_edition = Column(String(50), nullable=False)

    # Verification (required before production use)
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(100), nullable=True)
    verifier_designation = Column(String(100), nullable=True)  # Architect, Engineer, Code Consultant
    verified_date = Column(DateTime, nullable=True)
    verification_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    article = relationship("Article", back_populates="requirements")
    conditions = relationship("RequirementCondition", back_populates="requirement", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_requirements_element", "element"),
        Index("idx_requirements_verified", "is_verified"),
        Index("idx_requirements_type", "requirement_type"),
    )


class RequirementCondition(Base):
    """
    Conditions under which a requirement applies.
    Allows for complex conditional logic (e.g., "if building height <= 3 storeys AND occupancy = C").
    """
    __tablename__ = "requirement_conditions"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(UUID(), ForeignKey("requirements.id"), nullable=False)

    # The condition
    field = Column(String(100), nullable=False)  # e.g., "building_height", "occupancy_group"
    operator = Column(String(20), nullable=False)  # =, !=, <, <=, >, >=, IN, NOT_IN, BETWEEN
    value_text = Column(String(255), nullable=True)  # For string comparisons
    value_numeric = Column(Numeric, nullable=True)  # For numeric comparisons
    value_array = Column(StringArray(), nullable=True)  # For IN/NOT_IN operators
    unit = Column(String(20), nullable=True)

    # How this condition combines with the next
    logic_with_next = Column(String(10), nullable=True)  # AND, OR, null if last condition
    condition_order = Column(Integer, default=0)  # Order in the condition chain

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    requirement = relationship("Requirement", back_populates="conditions")

    __table_args__ = (
        Index("idx_conditions_requirement", "requirement_id", "condition_order"),
    )
