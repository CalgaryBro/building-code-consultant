"""
Models for user authentication and authorization.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Index
)

from ..database import Base
from .codes import UUID  # Import cross-database UUID type


class User(Base):
    """
    User account for authentication.
    """
    __tablename__ = "users"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Profile
    full_name = Column(String(255), nullable=True)

    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Email verification
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)

    # Password reset
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_verification_token", "verification_token"),
        Index("idx_users_reset_token", "reset_token"),
    )
