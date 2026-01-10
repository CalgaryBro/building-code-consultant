"""
Rate limiting model for tracking API usage by IP address.
"""
import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Integer, Date, DateTime, Index

from ..database import Base
from .codes import UUID


class RateLimit(Base):
    """
    Tracks API query counts per IP address for rate limiting public endpoints.
    Resets daily at midnight UTC.
    """
    __tablename__ = "rate_limits"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    ip_address = Column(String(45), nullable=False)  # IPv6 can be up to 45 chars
    query_count = Column(Integer, default=0, nullable=False)
    last_query_date = Column(Date, nullable=False, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_rate_limits_ip_date", "ip_address", "last_query_date", unique=True),
    )
