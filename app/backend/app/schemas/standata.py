"""
Pydantic schemas for STANDATA bulletins API.
"""
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class StandataCategory(str, Enum):
    """STANDATA bulletin categories."""
    BCI = "BCI"  # Building Code Interpretations
    BCB = "BCB"  # Building Code Bulletins
    FCB = "FCB"  # Fire Code Bulletins
    PCB = "PCB"  # Plumbing Code Bulletins


# --- Base Schemas ---

class StandataBase(BaseModel):
    """Base schema for STANDATA bulletins."""
    bulletin_number: str = Field(..., description="Bulletin number (e.g., 23-BCI-030)")
    title: str = Field(..., description="Bulletin title")
    category: StandataCategory = Field(..., description="Category: BCI, BCB, FCB, or PCB")
    effective_date: Optional[date] = Field(None, description="Effective date of the bulletin")
    supersedes: Optional[str] = Field(None, description="Previous bulletin this replaces")
    summary: Optional[str] = Field(None, description="Brief summary")
    code_references: Optional[List[str]] = Field(None, description="NBC articles referenced")
    keywords: Optional[List[str]] = Field(None, description="Search keywords")


class StandataCreate(StandataBase):
    """Schema for creating a STANDATA bulletin."""
    full_text: str = Field(..., description="Full extracted text from PDF")
    pdf_path: str = Field(..., description="Path to PDF file")
    pdf_filename: str = Field(..., description="Original PDF filename")
    related_bulletins: Optional[List[str]] = None
    extraction_confidence: Optional[str] = None


class StandataResponse(StandataBase):
    """Schema for STANDATA bulletin response."""
    id: UUID
    full_text: str
    pdf_path: str
    pdf_filename: str
    related_bulletins: Optional[List[str]] = None
    extraction_confidence: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StandataSummary(BaseModel):
    """Summary schema for listing STANDATA bulletins."""
    id: UUID
    bulletin_number: str
    title: str
    category: StandataCategory
    effective_date: Optional[date] = None
    summary: Optional[str] = None
    code_references: Optional[List[str]] = None

    class Config:
        from_attributes = True


class StandataSearchResult(BaseModel):
    """Schema for STANDATA search results."""
    id: UUID
    bulletin_number: str
    title: str
    category: StandataCategory
    effective_date: Optional[date] = None
    summary: Optional[str] = None
    code_references: Optional[List[str]] = None
    relevance_snippet: Optional[str] = Field(None, description="Relevant text snippet from search")
    match_type: Optional[str] = Field(None, description="Where the match was found: title, summary, full_text, code_reference")

    class Config:
        from_attributes = True


# --- Search Schemas ---

class StandataSearchQuery(BaseModel):
    """Schema for searching STANDATA bulletins."""
    query: str = Field(..., min_length=2, max_length=500, description="Search query text")
    categories: Optional[List[StandataCategory]] = Field(None, description="Filter by categories")
    code_reference: Optional[str] = Field(None, description="Filter by code article reference (e.g., 9.8.4.1)")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results to return")


class StandataSearchResponse(BaseModel):
    """Schema for search response."""
    query: str
    total_results: int
    results: List[StandataSearchResult]


class StandataByCodeResponse(BaseModel):
    """Schema for bulletins by code reference response."""
    code_reference: str
    total_results: int
    bulletins: List[StandataSummary]


# --- Statistics Schema ---

class StandataStats(BaseModel):
    """Schema for STANDATA statistics."""
    total_bulletins: int
    by_category: dict[str, int]
    latest_effective_date: Optional[date] = None
    total_code_references: int
