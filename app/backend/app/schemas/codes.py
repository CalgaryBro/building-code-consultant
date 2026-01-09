"""
Pydantic schemas for building codes, articles, and requirements.
"""
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


# --- Code Schemas ---

class CodeBase(BaseModel):
    """Base schema for Code."""
    code_type: str
    name: str
    short_name: str
    version: str
    jurisdiction: str
    effective_date: date
    expiry_date: Optional[date] = None
    source_url: Optional[str] = None
    is_current: bool = True


class CodeCreate(CodeBase):
    """Schema for creating a Code."""
    source_file: Optional[str] = None


class CodeResponse(CodeBase):
    """Schema for Code response."""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# --- Article Schemas ---

class ArticleBase(BaseModel):
    """Base schema for Article."""
    article_number: str
    title: Optional[str] = None
    full_text: str
    part_number: Optional[int] = None
    division_number: Optional[int] = None
    section_number: Optional[int] = None
    page_number: Optional[int] = None


class ArticleCreate(ArticleBase):
    """Schema for creating an Article."""
    code_id: UUID
    parent_article_id: Optional[UUID] = None


class ArticleResponse(ArticleBase):
    """Schema for Article response."""
    id: UUID
    code_id: UUID
    parent_article_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArticleSearchResult(BaseModel):
    """Schema for article search results."""
    id: UUID
    article_number: str
    title: Optional[str]
    full_text: str
    code_short_name: str
    code_version: str
    relevance_score: Optional[float] = None
    highlight: Optional[str] = None

    class Config:
        from_attributes = True


# --- Requirement Schemas ---

class RequirementConditionResponse(BaseModel):
    """Schema for RequirementCondition response."""
    id: UUID
    field: str
    operator: str
    value_text: Optional[str] = None
    value_numeric: Optional[float] = None
    value_array: Optional[List[str]] = None
    unit: Optional[str] = None
    logic_with_next: Optional[str] = None
    condition_order: int

    class Config:
        from_attributes = True


class RequirementBase(BaseModel):
    """Base schema for Requirement."""
    requirement_type: str
    element: str
    description: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    exact_value: Optional[str] = None
    unit: Optional[str] = None
    exact_quote: str
    is_mandatory: bool = True
    applies_to_part_9: bool = True
    applies_to_part_3: bool = False
    occupancy_groups: Optional[List[str]] = None


class RequirementCreate(RequirementBase):
    """Schema for creating a Requirement."""
    article_id: UUID
    extraction_method: str = "manual"
    extraction_confidence: Optional[str] = None
    extraction_model: Optional[str] = None
    source_document: str
    source_page: Optional[int] = None
    source_edition: str


class RequirementResponse(RequirementBase):
    """Schema for Requirement response."""
    id: UUID
    article_id: UUID
    extraction_method: str
    extraction_confidence: Optional[str]
    is_verified: bool
    verified_by: Optional[str]
    verified_date: Optional[datetime]
    conditions: List[RequirementConditionResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


# --- Search Schemas ---

class CodeSearchQuery(BaseModel):
    """Schema for searching codes."""
    query: str = Field(..., min_length=2, max_length=500)
    code_types: Optional[List[str]] = None  # building, fire, zoning, etc.
    part_numbers: Optional[List[int]] = None  # 3, 9, etc.
    limit: int = Field(default=20, ge=1, le=100)
    use_semantic: bool = True  # Use vector similarity search


class CodeSearchResponse(BaseModel):
    """Schema for search response."""
    query: str
    total_results: int
    results: List[ArticleSearchResult]
    search_type: str  # "semantic", "fulltext", "hybrid"
