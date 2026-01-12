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
from ..models.standata import Standata
from ..schemas.codes import (
    CodeResponse, ArticleResponse, ArticleSearchResult,
    RequirementResponse, CodeSearchQuery, CodeSearchResponse
)
from ..schemas.standata import StandataSummary, StandataByCodeResponse

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

    # Handle browse mode - if query is "*" or "**", just return filtered results
    is_browse_mode = query.query.strip() in ('*', '**', 'browse', 'all')

    if is_browse_mode:
        search_type = "browse"
        # Just use the filters, order by article number
        base_query = base_query.order_by(Article.article_number)

    # Try semantic search first if enabled and embeddings exist
    elif query.use_semantic:
        # Check if we have embeddings
        has_embeddings = db.query(Article).filter(Article.embedding.isnot(None)).first()

        if has_embeddings:
            # TODO: Generate query embedding using sentence-transformers
            # For now, fall back to full-text search
            search_type = "semantic"
            pass

    # Full-text search using PostgreSQL tsvector (only if not in browse mode)
    if search_type == "fulltext" and not is_browse_mode:
        # Check if search_vector is populated
        has_vectors = db.query(Article).filter(Article.search_vector.isnot(None)).first()

        if has_vectors:
            # Build OR-based tsquery for better natural language support
            # Convert "ceiling height bedrooms" to "ceiling | height | bedrooms"
            words = query.query.strip().split()
            # Filter out common stop words and short words
            stop_words = {'what', 'is', 'the', 'a', 'an', 'are', 'for', 'to', 'of', 'in', 'on', 'at', 'and', 'or', 'between'}
            search_terms = [w for w in words if len(w) >= 3 and w.lower() not in stop_words]

            if search_terms:
                # Join with OR operator for more forgiving search
                or_query = ' | '.join(search_terms)
                search_query = func.to_tsquery('english', or_query)

                # Use the pre-computed search vector
                base_query = base_query.filter(
                    Article.search_vector.op('@@')(search_query)
                ).order_by(
                    func.ts_rank(Article.search_vector, search_query).desc()
                )
        else:
            # Fall back to ILIKE search with individual words (OR logic)
            words = query.query.split()
            if words:
                from sqlalchemy import or_
                conditions = []
                for word in words:
                    if len(word) >= 3:  # Skip very short words
                        pattern = f"%{word}%"
                        conditions.append(Article.full_text.ilike(pattern))
                        conditions.append(Article.title.ilike(pattern))
                        conditions.append(Article.article_number.ilike(pattern))
                if conditions:
                    base_query = base_query.filter(or_(*conditions))

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


@router.get("/articles/{article_number}/related-standata", response_model=StandataByCodeResponse)
async def get_related_standata(
    article_number: str,
    db: Session = Depends(get_db)
):
    """
    Get STANDATA bulletins related to a specific code article.

    This endpoint searches for STANDATA bulletins that reference the given
    article number in their code_references field. Useful for showing
    official interpretations when viewing a code article.

    Args:
        article_number: The article number to search for (e.g., "9.10.9.6", "9.8.4.1")

    Returns:
        List of STANDATA bulletins that reference this article
    """
    # Query standata bulletins where code_references contains the article number
    # PostgreSQL ARRAY contains operator: @> or ANY()
    bulletins = db.query(Standata).filter(
        Standata.code_references.any(article_number)
    ).order_by(Standata.effective_date.desc()).all()

    # Also check for partial matches (e.g., "9.10" matches "9.10.9.6")
    if not bulletins:
        # Try prefix match for broader searches
        article_prefix = '.'.join(article_number.split('.')[:3])  # e.g., "9.10.9"
        bulletins = db.query(Standata).filter(
            func.array_to_string(Standata.code_references, ',').ilike(f"%{article_prefix}%")
        ).order_by(Standata.effective_date.desc()).limit(10).all()

    return StandataByCodeResponse(
        code_reference=article_number,
        total_results=len(bulletins),
        bulletins=[
            StandataSummary(
                id=b.id,
                bulletin_number=b.bulletin_number,
                title=b.title,
                category=b.category,
                effective_date=b.effective_date,
                summary=b.summary,
                code_references=b.code_references
            )
            for b in bulletins
        ]
    )


@router.get("/standata", response_model=list[StandataSummary])
async def list_standata(
    category: Optional[str] = Query(None, description="Filter by category: BCI, BCB, FCB, PCB"),
    search: Optional[str] = Query(None, description="Search in title, summary, keywords"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    List all STANDATA bulletins with optional filtering.

    Returns a summary list of bulletins for browsing.
    """
    query = db.query(Standata)

    if category:
        query = query.filter(Standata.category == category.upper())

    if search:
        from sqlalchemy import or_
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Standata.title.ilike(pattern),
                Standata.summary.ilike(pattern),
                func.array_to_string(Standata.keywords, ',').ilike(pattern),
                Standata.bulletin_number.ilike(pattern)
            )
        )

    bulletins = query.order_by(Standata.effective_date.desc()).limit(limit).all()

    return [
        StandataSummary(
            id=b.id,
            bulletin_number=b.bulletin_number,
            title=b.title,
            category=b.category,
            effective_date=b.effective_date,
            summary=b.summary,
            code_references=b.code_references
        )
        for b in bulletins
    ]


@router.get("/standata/{bulletin_number}")
async def get_standata_bulletin(
    bulletin_number: str,
    db: Session = Depends(get_db)
):
    """
    Get full details of a specific STANDATA bulletin.
    """
    bulletin = db.query(Standata).filter(
        Standata.bulletin_number == bulletin_number
    ).first()

    if not bulletin:
        raise HTTPException(status_code=404, detail=f"Bulletin '{bulletin_number}' not found")

    return {
        "id": str(bulletin.id),
        "bulletin_number": bulletin.bulletin_number,
        "title": bulletin.title,
        "category": bulletin.category,
        "effective_date": bulletin.effective_date.isoformat() if bulletin.effective_date else None,
        "supersedes": bulletin.supersedes,
        "summary": bulletin.summary,
        "full_text": bulletin.full_text,
        "code_references": bulletin.code_references or [],
        "keywords": bulletin.keywords or [],
        "related_bulletins": bulletin.related_bulletins or [],
        "pdf_filename": bulletin.pdf_filename,
        "extraction_confidence": bulletin.extraction_confidence
    }
