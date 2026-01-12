"""
Public API endpoints - Rate-limited access for unauthenticated users.

This module provides a limited version of the Explore functionality
for users who haven't registered yet, encouraging sign-up.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models.codes import Code, Article
from ..schemas.codes import ArticleSearchResult, CodeSearchQuery, CodeSearchResponse
from ..middleware.rate_limit import (
    check_rate_limit, get_client_ip, get_rate_limit_status,
    RateLimitExceeded, DAILY_QUERY_LIMIT
)

router = APIRouter()


# Maximum results for public endpoint (limited preview)
PUBLIC_RESULT_LIMIT = 2


@router.get("/rate-limit-status")
async def get_public_rate_limit_status(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Check the current rate limit status for the requesting IP.
    Does not count against the limit.
    """
    ip_address = get_client_ip(request)
    queries_used, queries_remaining = get_rate_limit_status(db, ip_address)

    return {
        "ip_address": ip_address[:10] + "..." if len(ip_address) > 10 else ip_address,
        "queries_used": queries_used,
        "queries_remaining": queries_remaining,
        "daily_limit": DAILY_QUERY_LIMIT,
        "resets_at": "midnight UTC"
    }


@router.post("/explore", response_model=CodeSearchResponse)
async def public_explore_search(
    request: Request,
    query: CodeSearchQuery,
    db: Session = Depends(get_db)
):
    """
    Rate-limited public search endpoint for code exploration.

    This endpoint provides a preview of the Explore functionality:
    - Limited to 5 queries per day per IP address
    - Returns only the first 2 results
    - Encourages users to register for full access

    Returns:
        - X-Queries-Remaining header with remaining queries
        - Search results (limited to 2)
        - 429 error when limit exceeded
    """
    ip_address = get_client_ip(request)

    # Check rate limit
    allowed, queries_remaining = check_rate_limit(db, ip_address)

    if not allowed:
        raise RateLimitExceeded(queries_remaining=0)

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

    search_type = "fulltext"

    # Check if search_vector is populated
    has_vectors = db.query(Article).filter(Article.search_vector.isnot(None)).first()

    if has_vectors:
        # Use the pre-computed search vector
        search_query_obj = func.plainto_tsquery('english', query.query)
        base_query = base_query.filter(
            Article.search_vector.op('@@')(search_query_obj)
        ).order_by(
            func.ts_rank(Article.search_vector, search_query_obj).desc()
        )
    else:
        # Fall back to ILIKE search with individual words (OR logic)
        # This allows "egress window requirements" to match articles containing any of these words
        from sqlalchemy import or_
        words = query.query.strip().split()
        # Filter out common stop words and short words
        stop_words = {'what', 'is', 'the', 'a', 'an', 'are', 'for', 'to', 'of', 'in', 'on', 'at', 'and', 'or', 'between', 'how', 'why', 'when', 'where'}
        search_terms = [w.strip('?.,!') for w in words if len(w) >= 3 and w.lower() not in stop_words]

        if search_terms:
            conditions = []
            for word in search_terms:
                pattern = f"%{word}%"
                conditions.append(Article.full_text.ilike(pattern))
                conditions.append(Article.title.ilike(pattern))
                conditions.append(Article.article_number.ilike(pattern))
            base_query = base_query.filter(or_(*conditions))
        else:
            # Fallback to full query if no valid terms
            search_pattern = f"%{query.query}%"
            base_query = base_query.filter(
                Article.full_text.ilike(search_pattern) |
                Article.title.ilike(search_pattern) |
                Article.article_number.ilike(search_pattern)
            )

    # Execute query with PUBLIC limit (only 2 results for free users)
    raw_results = base_query.limit(PUBLIC_RESULT_LIMIT).all()

    # Count total results available (for showing "X more results with signup")
    count_query = db.query(func.count(Article.id)).join(Code)
    if query.code_types:
        count_query = count_query.filter(Code.code_type.in_(query.code_types))
    if query.part_numbers:
        count_query = count_query.filter(Article.part_number.in_(query.part_numbers))

    if has_vectors:
        search_query_obj = func.plainto_tsquery('english', query.query)
        count_query = count_query.filter(
            Article.search_vector.op('@@')(search_query_obj)
        )
    else:
        # Same word-splitting logic as above for consistent counts
        from sqlalchemy import or_
        words = query.query.strip().split()
        stop_words = {'what', 'is', 'the', 'a', 'an', 'are', 'for', 'to', 'of', 'in', 'on', 'at', 'and', 'or', 'between', 'how', 'why', 'when', 'where'}
        search_terms = [w.strip('?.,!') for w in words if len(w) >= 3 and w.lower() not in stop_words]

        if search_terms:
            conditions = []
            for word in search_terms:
                pattern = f"%{word}%"
                conditions.append(Article.full_text.ilike(pattern))
                conditions.append(Article.title.ilike(pattern))
                conditions.append(Article.article_number.ilike(pattern))
            count_query = count_query.filter(or_(*conditions))
        else:
            search_pattern = f"%{query.query}%"
            count_query = count_query.filter(
                Article.full_text.ilike(search_pattern) |
                Article.title.ilike(search_pattern) |
                Article.article_number.ilike(search_pattern)
            )

    total_available = count_query.scalar() or 0

    # Transform to response format
    results = []
    for row in raw_results:
        # Truncate full_text for preview
        preview_text = row.full_text[:300] + "..." if len(row.full_text) > 300 else row.full_text
        results.append(ArticleSearchResult(
            id=str(row.id),  # Convert UUID to string for JSON serialization
            article_number=row.article_number,
            title=row.title,
            full_text=preview_text,
            code_short_name=row.code_short_name,
            code_version=row.code_version,
            relevance_score=None,
            highlight=None
        ))

    # Create response with custom headers
    response_data = CodeSearchResponse(
        query=query.query,
        total_results=total_available,
        results=results,
        search_type=search_type
    )

    # Return response with rate limit headers
    response = JSONResponse(
        content={
            **response_data.model_dump(mode='json'),  # mode='json' converts UUIDs to strings
            "is_limited": True,
            "results_shown": len(results),
            "total_available": total_available,
            "upgrade_message": f"Sign up free to see all {total_available} results and get unlimited searches."
            if total_available > PUBLIC_RESULT_LIMIT else None
        },
        headers={
            "X-Queries-Remaining": str(queries_remaining),
            "X-Daily-Limit": str(DAILY_QUERY_LIMIT),
            "X-Rate-Limited": "true"
        }
    )

    return response


@router.get("/sample-questions")
async def get_sample_questions():
    """
    Get sample questions that users can try with the public explore feature.
    """
    return {
        "questions": [
            {
                "question": "What is the minimum ceiling height for bedrooms?",
                "category": "dimensional",
                "code_type": "building"
            },
            {
                "question": "What are the egress window requirements?",
                "category": "safety",
                "code_type": "building"
            },
            {
                "question": "What is the maximum building height for R-C1 zone?",
                "category": "zoning",
                "code_type": "zoning"
            },
            {
                "question": "What fire separation is required for a garage?",
                "category": "fire_safety",
                "code_type": "building"
            },
            {
                "question": "What are secondary suite requirements?",
                "category": "permits",
                "code_type": "building"
            }
        ],
        "cta": {
            "message": "Want unlimited searches? Sign up for free!",
            "url": "/signup",
            "benefits": [
                "Unlimited code searches",
                "Save your projects",
                "Access to Guide mode",
                "Document review tools",
                "Export to PDF"
            ]
        }
    }
