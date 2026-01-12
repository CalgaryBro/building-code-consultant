"""
Models for user authentication and authorization.
"""
import uuid
from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Index, Enum as SQLEnum
)

from ..database import Base
from .codes import UUID  # Import cross-database UUID type


class UserRole(str, Enum):
    """User roles for access control."""
    USER = "user"          # Regular free user
    REVIEWER = "reviewer"  # Can review permit applications
    ADMIN = "admin"        # Full system access


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

    # Role
    role = Column(String(20), default=UserRole.USER.value)

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
