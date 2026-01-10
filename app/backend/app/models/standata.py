"""
Models for STANDATA bulletins - Alberta building code interpretations and bulletins.

STANDATA bulletins are official interpretations and guidelines published by
Alberta Municipal Affairs to clarify or supplement the building codes.

Types:
- BCI: Building Code Interpretations
- BCB: Building Code Bulletins
- FCB: Fire Code Bulletins
- PCB: Plumbing Code Bulletins
"""
import uuid
from datetime import datetime, date
from typing import Optional, List

from sqlalchemy import (
    Column, String, Text, Date, DateTime, Index
)

from ..database import Base
from .codes import UUID, StringArray


class StandataCategory(str):
    """STANDATA bulletin categories."""
    BCI = "BCI"  # Building Code Interpretations
    BCB = "BCB"  # Building Code Bulletins
    FCB = "FCB"  # Fire Code Bulletins
    PCB = "PCB"  # Plumbing Code Bulletins


class Standata(Base):
    """
    Represents a STANDATA bulletin from Alberta Municipal Affairs.

    These bulletins provide official interpretations and guidance for
    applying the Alberta Building Code, Fire Code, and Plumbing Code.
    """
    __tablename__ = "standata"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)

    # Bulletin identification
    bulletin_number = Column(String(50), nullable=False, unique=True, index=True)
    # e.g., "23-BCI-030", "23-BCB-001", "23-FCB-004"

    title = Column(String(500), nullable=False)
    # e.g., "Secondary Suites in Existing Buildings"

    category = Column(String(10), nullable=False, index=True)
    # BCI, BCB, FCB, or PCB

    effective_date = Column(Date, nullable=True)
    # When the bulletin became effective

    supersedes = Column(String(50), nullable=True)
    # Previous bulletin number this replaces, if any

    # Content
    summary = Column(Text, nullable=True)
    # Brief summary of the bulletin's purpose

    full_text = Column(Text, nullable=False)
    # Complete extracted text from the PDF

    # References
    code_references = Column(StringArray(), nullable=True)
    # List of NBC articles referenced (e.g., ["9.8.4.1", "9.10.9.6"])

    keywords = Column(StringArray(), nullable=True)
    # Keywords for search (e.g., ["secondary suite", "egress", "fire separation"])

    related_bulletins = Column(StringArray(), nullable=True)
    # Other related STANDATA bulletin numbers

    # File information
    pdf_path = Column(String(500), nullable=False)
    # Relative path to the PDF file

    pdf_filename = Column(String(255), nullable=False)
    # Original filename

    # Metadata
    extraction_date = Column(DateTime, default=datetime.utcnow)
    extraction_confidence = Column(String(20), nullable=True)
    # HIGH, MEDIUM, LOW - based on PDF text quality

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_standata_category", "category"),
        Index("idx_standata_effective_date", "effective_date"),
        Index("idx_standata_bulletin_number", "bulletin_number"),
    )

    def __repr__(self):
        return f"<Standata {self.bulletin_number}: {self.title[:50]}>"
