"""
Rate limiting middleware for public API endpoints.

Tracks queries by IP address using PostgreSQL.
Limit: 5 queries per IP per day (resets at midnight UTC).
"""
from datetime import date, datetime
from typing import Tuple, Optional
from fastapi import Request, HTTPException
from sqlalchemy.orm import Session

from ..models.rate_limits import RateLimit

# Configuration
DAILY_QUERY_LIMIT = 5


class RateLimitExceeded(HTTPException):
    """Custom exception for rate limit exceeded."""
    def __init__(self, queries_remaining: int = 0, reset_time: str = "midnight UTC"):
        super().__init__(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Daily query limit ({DAILY_QUERY_LIMIT}) exceeded. Please register for unlimited access.",
                "queries_remaining": queries_remaining,
                "reset_time": reset_time,
                "upgrade_url": "/signup"
            }
        )


def get_client_ip(request: Request) -> str:
    """
    Extract the client IP address from the request.
    Handles X-Forwarded-For header for proxied requests.
    """
    # Check for X-Forwarded-For header (common in proxy setups)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain (original client)
        return forwarded_for.split(",")[0].strip()

    # Check for X-Real-IP header (used by some proxies like nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct client IP
    if request.client:
        return request.client.host

    # Ultimate fallback
    return "unknown"


def check_rate_limit(db: Session, ip_address: str) -> Tuple[bool, int]:
    """
    Check if an IP address has exceeded the daily rate limit.

    Args:
        db: Database session
        ip_address: The client's IP address

    Returns:
        Tuple of (allowed, queries_remaining)
        - allowed: True if the request should be permitted
        - queries_remaining: Number of queries left for today
    """
    today = date.today()

    # Find or create rate limit record for this IP
    rate_limit = db.query(RateLimit).filter(
        RateLimit.ip_address == ip_address,
        RateLimit.last_query_date == today
    ).first()

    if not rate_limit:
        # First query today - create new record
        rate_limit = RateLimit(
            ip_address=ip_address,
            query_count=0,
            last_query_date=today
        )
        db.add(rate_limit)
        db.flush()  # Get the ID without committing

    # Check if limit exceeded
    if rate_limit.query_count >= DAILY_QUERY_LIMIT:
        return False, 0

    # Increment counter
    rate_limit.query_count += 1
    rate_limit.updated_at = datetime.utcnow()
    db.commit()

    queries_remaining = DAILY_QUERY_LIMIT - rate_limit.query_count
    return True, queries_remaining


def get_rate_limit_status(db: Session, ip_address: str) -> Tuple[int, int]:
    """
    Get the current rate limit status for an IP without incrementing.

    Args:
        db: Database session
        ip_address: The client's IP address

    Returns:
        Tuple of (queries_used, queries_remaining)
    """
    today = date.today()

    rate_limit = db.query(RateLimit).filter(
        RateLimit.ip_address == ip_address,
        RateLimit.last_query_date == today
    ).first()

    if not rate_limit:
        return 0, DAILY_QUERY_LIMIT

    queries_used = rate_limit.query_count
    queries_remaining = max(0, DAILY_QUERY_LIMIT - queries_used)
    return queries_used, queries_remaining
