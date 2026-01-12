"""
Pydantic schemas for authentication.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, EmailStr, Field


# --- User Role Enum ---

class UserRole(str, Enum):
    """User roles for access control."""
    USER = "user"
    REVIEWER = "reviewer"
    ADMIN = "admin"


# --- User Schemas ---

class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for User response (public info)."""
    id: UUID
    email: str
    full_name: Optional[str] = None
    role: str = "user"
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = None


class AdminUserUpdate(BaseModel):
    """Schema for admin updating user (including role and status)."""
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class AdminUserCreate(BaseModel):
    """Schema for admin creating a user."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_verified: bool = True  # Admin-created users are pre-verified


class UserListResponse(BaseModel):
    """Schema for paginated user list."""
    total: int
    page: int
    page_size: int
    users: List[UserResponse]


# --- Token Schemas ---

class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    """Schema for login response with user data."""
    user: UserResponse
    message: str = "Login successful"


class TokenData(BaseModel):
    """Schema for decoded token data."""
    user_id: Optional[str] = None
    email: Optional[str] = None
    exp: Optional[int] = None


# --- Password Reset Schemas ---

class PasswordResetRequest(BaseModel):
    """Schema for password reset request (forgot password)."""
    email: EmailStr


class PasswordReset(BaseModel):
    """Schema for actually resetting password with token."""
    token: str
    new_password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class PasswordChange(BaseModel):
    """Schema for changing password (when logged in)."""
    current_password: str
    new_password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


# --- Email Verification Schemas ---

class EmailVerificationRequest(BaseModel):
    """Schema for email verification."""
    token: str


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    detail: Optional[str] = None
