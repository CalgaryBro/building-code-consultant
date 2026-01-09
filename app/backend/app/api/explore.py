"""
EXPLORE Mode API - Search and browse building codes.

This mode allows users to:
- Search code articles using natural language (semantic search)
- Search using exact text (full-text search)
- Browse code structure (parts, divisions, sections)
- View specific articles and their requirements
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from ..database import get_db
from ..models.codes import Code, Article, Requirement
from ..schemas.codes import (
    CodeResponse, ArticleResponse, ArticleSearchResult,
    RequirementResponse, CodeSearchQuery, CodeSearchResponse
)

router = APIRouter()


@router.get("/codes", response_model=List[CodeResponse])
async def list_codes(
    code_type: Optional[str] = Query(None, description="Filter by code type: building, fire, zoning, etc."),
    current_only: bool = Query(True, description="Only return current (non-superseded) codes"),
    db: Session = Depends(get_db)
):
    """
    List all available codes/bylaws/standards.
    """
    query = db.query(Code)

    if code_type:
        query = query.filter(Code.code_type == code_type)
    if current_only:
        query = query.filter(Code.is_current == True)

    return query.order_by(Code.code_type, Code.effective_date.desc()).all()


@router.get("/codes/{code_id}", response_model=CodeResponse)
async def get_code(code_id: UUID, db: Session = Depends(get_db)):
    """
    Get details for a specific code.
    """
    code = db.query(Code).filter(Code.id == code_id).first()
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")
    return code


@router.get("/codes/{code_id}/articles", response_model=List[ArticleResponse])
async def list_articles(
    code_id: UUID,
    part_number: Optional[int] = Query(None, description="Filter by part number"),
    division_number: Optional[int] = Query(None, description="Filter by division number"),
    db: Session = Depends(get_db)
):
    """
    List articles for a specific code, optionally filtered by part/division.
    """
    query = db.query(Article).filter(Article.code_id == code_id)

    if part_number:
        query = query.filter(Article.part_number == part_number)
    if division_number:
        query = query.filter(Article.division_number == division_number)

    return query.order_by(Article.article_number).all()


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: UUID, db: Session = Depends(get_db)):
    """
    Get a specific article by ID.
    """
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.get("/articles/{article_id}/requirements", response_model=List[RequirementResponse])
async def get_article_requirements(article_id: UUID, db: Session = Depends(get_db)):
    """
    Get all requirements extracted from an article.
    """
    requirements = db.query(Requirement).filter(
        Requirement.article_id == article_id
    ).all()
    return requirements


@router.post("/search", response_model=CodeSearchResponse)
async def search_codes(query: CodeSearchQuery, db: Session = Depends(get_db)):
    """
    Search code articles using semantic search (vector similarity) or full-text search.

    This is the main search endpoint for EXPLORE mode. It supports:
    - Natural language queries (e.g., "stair width requirements for residential")
    - Exact phrase matching
    - Filtering by code type and part number
    """
    results = []
    search_type = "fulltext"  # Default to fulltext until embeddings are populated

    # Build base query
    base_query = db.query(
        Article.id,
        Article.article_number,
        Article.title,
        Article.full_text,
        Code.short_name.label("code_short_name"),
        Code.version.label("code_version")
    ).join(Code)

    # Apply filters
    if query.code_types:
        base_query = base_query.filter(Code.code_type.in_(query.code_types))
    if query.part_numbers:
        base_query = base_query.filter(Article.part_number.in_(query.part_numbers))

    # Try semantic search first if enabled and embeddings exist
    if query.use_semantic:
        # Check if we have embeddings
        has_embeddings = db.query(Article).filter(Article.embedding.isnot(None)).first()

        if has_embeddings:
            # TODO: Generate query embedding using sentence-transformers
            # For now, fall back to full-text search
            search_type = "semantic"
            pass

    # Full-text search using PostgreSQL tsvector
    if search_type == "fulltext":
        # Use plainto_tsquery for natural language queries
        search_query = func.plainto_tsquery('english', query.query)

        # Check if search_vector is populated, otherwise search full_text directly
        has_vectors = db.query(Article).filter(Article.search_vector.isnot(None)).first()

        if has_vectors:
            # Use the pre-computed search vector
            base_query = base_query.filter(
                Article.search_vector.op('@@')(search_query)
            ).order_by(
                func.ts_rank(Article.search_vector, search_query).desc()
            )
        else:
            # Fall back to ILIKE search
            search_pattern = f"%{query.query}%"
            base_query = base_query.filter(
                Article.full_text.ilike(search_pattern) |
                Article.title.ilike(search_pattern) |
                Article.article_number.ilike(search_pattern)
            )

    # Execute query with limit
    raw_results = base_query.limit(query.limit).all()

    # Transform to response format
    for row in raw_results:
        results.append(ArticleSearchResult(
            id=row.id,
            article_number=row.article_number,
            title=row.title,
            full_text=row.full_text[:500] + "..." if len(row.full_text) > 500 else row.full_text,
            code_short_name=row.code_short_name,
            code_version=row.code_version,
            relevance_score=None,  # TODO: Add when semantic search is implemented
            highlight=None  # TODO: Add highlighted snippets
        ))

    return CodeSearchResponse(
        query=query.query,
        total_results=len(results),
        results=results,
        search_type=search_type
    )


@router.get("/requirements", response_model=List[RequirementResponse])
async def search_requirements(
    element: Optional[str] = Query(None, description="Filter by element (e.g., stair_width, fire_rating)"),
    requirement_type: Optional[str] = Query(None, description="Filter by type: dimensional, material, procedural, performance"),
    occupancy_group: Optional[str] = Query(None, description="Filter by occupancy group: A1, A2, B1, C, D, E, F1, F2, F3"),
    part_9_only: bool = Query(False, description="Only return Part 9 requirements"),
    verified_only: bool = Query(False, description="Only return verified requirements"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Search for specific requirements across all codes.

    Useful for finding all requirements related to a specific building element
    (e.g., all stair width requirements, all fire rating requirements).
    """
    query = db.query(Requirement)

    if element:
        query = query.filter(Requirement.element.ilike(f"%{element}%"))
    if requirement_type:
        query = query.filter(Requirement.requirement_type == requirement_type)
    if occupancy_group:
        query = query.filter(Requirement.occupancy_groups.contains([occupancy_group]))
    if part_9_only:
        query = query.filter(Requirement.applies_to_part_9 == True)
    if verified_only:
        query = query.filter(Requirement.is_verified == True)

    return query.limit(limit).all()


@router.get("/browse/{code_type}")
async def browse_code_structure(
    code_type: str,
    db: Session = Depends(get_db)
):
    """
    Browse the hierarchical structure of a code type.
    Returns parts, divisions, and sections for navigation.
    """
    # Get the current code of this type
    code = db.query(Code).filter(
        Code.code_type == code_type,
        Code.is_current == True
    ).first()

    if not code:
        raise HTTPException(status_code=404, detail=f"No current {code_type} code found")

    # Get distinct parts
    parts = db.query(
        Article.part_number,
        func.min(Article.title).label("part_title"),
        func.count(Article.id).label("article_count")
    ).filter(
        Article.code_id == code.id,
        Article.part_number.isnot(None)
    ).group_by(Article.part_number).order_by(Article.part_number).all()

    structure = {
        "code": {
            "id": str(code.id),
            "name": code.name,
            "short_name": code.short_name,
            "version": code.version
        },
        "parts": [
            {
                "part_number": p.part_number,
                "title": p.part_title,
                "article_count": p.article_count
            }
            for p in parts
        ]
    }

    return structure
