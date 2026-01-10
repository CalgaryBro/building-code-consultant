"""
STANDATA API - Search and browse Alberta STANDATA bulletins.

STANDATA bulletins provide official interpretations and guidance for
applying the Alberta Building Code, Fire Code, and Plumbing Code.

Types:
- BCI: Building Code Interpretations
- BCB: Building Code Bulletins
- FCB: Fire Code Bulletins
- PCB: Plumbing Code Bulletins
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from ..database import get_db
from ..models.standata import Standata
from ..schemas.standata import (
    StandataResponse, StandataSummary, StandataSearchResult,
    StandataSearchQuery, StandataSearchResponse, StandataByCodeResponse,
    StandataStats, StandataCategory
)

router = APIRouter()


@router.get("/", response_model=List[StandataSummary])
async def list_standata(
    category: Optional[str] = Query(None, description="Filter by category: BCI, BCB, FCB, PCB"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """
    List all STANDATA bulletins.

    Returns a summary list of bulletins, optionally filtered by category.
    Results are sorted by bulletin number descending (newest first).
    """
    query = db.query(Standata)

    if category:
        query = query.filter(Standata.category == category.upper())

    total = query.count()

    bulletins = query.order_by(Standata.bulletin_number.desc())\
        .offset(offset)\
        .limit(limit)\
        .all()

    return bulletins


@router.get("/stats", response_model=StandataStats)
async def get_standata_stats(db: Session = Depends(get_db)):
    """
    Get statistics about STANDATA bulletins in the database.
    """
    total = db.query(Standata).count()

    # Count by category
    category_counts = db.query(
        Standata.category,
        func.count(Standata.id)
    ).group_by(Standata.category).all()

    by_category = {cat: count for cat, count in category_counts}

    # Latest effective date
    latest = db.query(func.max(Standata.effective_date)).scalar()

    # Count unique code references
    # This is an approximation since code_references is stored as array
    all_refs = db.query(Standata.code_references).filter(
        Standata.code_references.isnot(None)
    ).all()

    unique_refs = set()
    for refs_tuple in all_refs:
        if refs_tuple[0]:
            unique_refs.update(refs_tuple[0])

    return StandataStats(
        total_bulletins=total,
        by_category=by_category,
        latest_effective_date=latest,
        total_code_references=len(unique_refs)
    )


@router.get("/categories")
async def list_categories():
    """
    List available STANDATA categories with descriptions.
    """
    return {
        "categories": [
            {
                "code": "BCI",
                "name": "Building Code Interpretations",
                "description": "Official interpretations of specific building code provisions"
            },
            {
                "code": "BCB",
                "name": "Building Code Bulletins",
                "description": "Technical guidance and clarifications for building code requirements"
            },
            {
                "code": "FCB",
                "name": "Fire Code Bulletins",
                "description": "Interpretations and guidance for fire code requirements"
            },
            {
                "code": "PCB",
                "name": "Plumbing Code Bulletins",
                "description": "Interpretations and guidance for plumbing code requirements"
            }
        ]
    }


@router.get("/search", response_model=StandataSearchResponse)
async def search_standata(
    q: str = Query(..., min_length=2, description="Search query"),
    categories: Optional[str] = Query(None, description="Comma-separated categories to filter: BCI,BCB,FCB,PCB"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    db: Session = Depends(get_db)
):
    """
    Full-text search across STANDATA bulletins.

    Searches in:
    - Bulletin number
    - Title
    - Summary
    - Full text content
    - Code references
    - Keywords

    Returns results with relevance snippets showing where the match occurred.
    """
    results = []
    search_pattern = f"%{q}%"

    query = db.query(Standata)

    # Apply category filter if provided
    if categories:
        cat_list = [c.strip().upper() for c in categories.split(",")]
        query = query.filter(Standata.category.in_(cat_list))

    # Search across multiple fields
    query = query.filter(
        or_(
            Standata.bulletin_number.ilike(search_pattern),
            Standata.title.ilike(search_pattern),
            Standata.summary.ilike(search_pattern),
            Standata.full_text.ilike(search_pattern),
        )
    )

    bulletins = query.limit(limit).all()

    # Build results with snippets
    for bulletin in bulletins:
        # Determine match type and create snippet
        match_type = "full_text"
        snippet = None

        if q.lower() in bulletin.bulletin_number.lower():
            match_type = "bulletin_number"
            snippet = f"Bulletin: {bulletin.bulletin_number}"
        elif q.lower() in bulletin.title.lower():
            match_type = "title"
            snippet = bulletin.title
        elif bulletin.summary and q.lower() in bulletin.summary.lower():
            match_type = "summary"
            snippet = bulletin.summary[:200] + "..." if len(bulletin.summary) > 200 else bulletin.summary
        else:
            # Find snippet in full text
            q_lower = q.lower()
            full_text_lower = bulletin.full_text.lower()
            pos = full_text_lower.find(q_lower)
            if pos >= 0:
                start = max(0, pos - 50)
                end = min(len(bulletin.full_text), pos + len(q) + 150)
                snippet = ("..." if start > 0 else "") + bulletin.full_text[start:end] + ("..." if end < len(bulletin.full_text) else "")

        results.append(StandataSearchResult(
            id=bulletin.id,
            bulletin_number=bulletin.bulletin_number,
            title=bulletin.title,
            category=bulletin.category,
            effective_date=bulletin.effective_date,
            summary=bulletin.summary,
            code_references=bulletin.code_references,
            relevance_snippet=snippet,
            match_type=match_type
        ))

    return StandataSearchResponse(
        query=q,
        total_results=len(results),
        results=results
    )


@router.get("/by-code/{code_reference}", response_model=StandataByCodeResponse)
async def get_bulletins_by_code(
    code_reference: str,
    db: Session = Depends(get_db)
):
    """
    Find STANDATA bulletins that reference a specific NBC article.

    Args:
        code_reference: NBC article number (e.g., "9.8.4.1", "9.10.9.6")

    Returns all bulletins that contain this code reference.
    """
    # Search for bulletins containing this code reference
    # Search in full text as code_references is stored as array and
    # also appears in the full text content
    bulletins = db.query(Standata).filter(
        Standata.full_text.ilike(f"%{code_reference}%")
    ).order_by(Standata.bulletin_number.desc()).all()

    return StandataByCodeResponse(
        code_reference=code_reference,
        total_results=len(bulletins),
        bulletins=[StandataSummary(
            id=b.id,
            bulletin_number=b.bulletin_number,
            title=b.title,
            category=b.category,
            effective_date=b.effective_date,
            summary=b.summary,
            code_references=b.code_references
        ) for b in bulletins]
    )


@router.get("/{bulletin_number}", response_model=StandataResponse)
async def get_standata_bulletin(
    bulletin_number: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific STANDATA bulletin by its bulletin number.

    Args:
        bulletin_number: The bulletin number (e.g., "23-BCI-030", "23-BCB-001")
    """
    # Try exact match first
    bulletin = db.query(Standata).filter(
        Standata.bulletin_number == bulletin_number.upper()
    ).first()

    # Try case-insensitive match
    if not bulletin:
        bulletin = db.query(Standata).filter(
            Standata.bulletin_number.ilike(bulletin_number)
        ).first()

    if not bulletin:
        raise HTTPException(
            status_code=404,
            detail=f"STANDATA bulletin {bulletin_number} not found"
        )

    return bulletin


@router.get("/id/{bulletin_id}", response_model=StandataResponse)
async def get_standata_by_id(
    bulletin_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific STANDATA bulletin by its UUID.
    """
    bulletin = db.query(Standata).filter(Standata.id == bulletin_id).first()

    if not bulletin:
        raise HTTPException(
            status_code=404,
            detail=f"STANDATA bulletin with ID {bulletin_id} not found"
        )

    return bulletin
