"""
Authentication API endpoints.

Handles user registration, login, logout, email verification,
and password reset functionality.
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..config import get_settings
from ..models.auth import User
from ..schemas.auth import (
    UserCreate, UserLogin, UserResponse, UserUpdate,
    TokenResponse, LoginResponse, PasswordResetRequest, PasswordReset,
    PasswordChange, EmailVerificationRequest, MessageResponse
)
from ..core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, decode_token,
    generate_verification_token, generate_reset_token
)
from ..core.deps import get_current_user, get_current_active_user

settings = get_settings()
router = APIRouter()


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set httpOnly cookies for authentication tokens."""
    # Access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60
    )
    # Refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear authentication cookies."""
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(
    response: Response,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.

    A verification email will be sent to complete registration.
    The account will be created but marked as unverified until
    the email is confirmed.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create verification token
    verification_token = generate_verification_token()
    verification_expires = datetime.utcnow() + timedelta(hours=24)

    # Create user
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        is_active=True,
        is_verified=False,
        verification_token=verification_token,
        verification_token_expires=verification_expires
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Create tokens for auto-login after registration
    token_data = {
        "user_id": str(user.id),
        "email": user.email
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Set cookies
    set_auth_cookies(response, access_token, refresh_token)

    # TODO: Send verification email with token
    # In production, integrate with email service (SendGrid, SES, etc.)
    # For now, the token can be verified via the verify-email endpoint

    return LoginResponse(user=UserResponse.model_validate(user), message="Registration successful")


@router.post("/login", response_model=LoginResponse)
async def login(
    response: Response,
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens along with user data.

    Tokens are set as httpOnly cookies for security.
    The user object is returned in the response body for the frontend.
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Create tokens
    token_data = {
        "user_id": str(user.id),
        "email": user.email
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    # Set cookies
    set_auth_cookies(response, access_token, refresh_token)

    return LoginResponse(user=UserResponse.model_validate(user))


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response):
    """
    Logout the current user by clearing authentication cookies.
    """
    clear_auth_cookies(response)
    return MessageResponse(message="Successfully logged out")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Refresh the access token using the refresh token.

    The refresh token must be provided via httpOnly cookie.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )

    # Decode refresh token
    payload = decode_token(refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Verify token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    # Get user
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new tokens
    token_data = {
        "user_id": str(user.id),
        "email": user.email
    }
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    # Set new cookies
    set_auth_cookies(response, new_access_token, new_refresh_token)

    return TokenResponse(access_token=new_access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the current authenticated user's profile.
    """
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's profile.
    """
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return current_user


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    verification: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verify user's email address using the verification token.

    The token is sent to the user's email upon registration.
    """
    user = db.query(User).filter(
        User.verification_token == verification.token
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )

    # Check if token expired
    if user.verification_token_expires and user.verification_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired"
        )

    # Mark user as verified
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    user.updated_at = datetime.utcnow()
    db.commit()

    return MessageResponse(message="Email successfully verified")


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification_email(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Resend the email verification token.

    User must be logged in but can request a new verification email
    if they haven't verified yet.
    """
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )

    # Generate new verification token
    current_user.verification_token = generate_verification_token()
    current_user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
    current_user.updated_at = datetime.utcnow()
    db.commit()

    # TODO: Send verification email
    # In production, integrate with email service

    return MessageResponse(
        message="Verification email sent",
        detail="Please check your email for the verification link"
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request a password reset email.

    If the email exists in the system, a reset token will be generated
    and sent to that email address.

    Note: Always returns success to prevent email enumeration.
    """
    user = db.query(User).filter(User.email == request_data.email).first()

    if user:
        # Generate reset token
        user.reset_token = generate_reset_token()
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        user.updated_at = datetime.utcnow()
        db.commit()

        # TODO: Send password reset email
        # In production, integrate with email service

    # Always return success to prevent email enumeration
    return MessageResponse(
        message="If the email exists, a password reset link has been sent",
        detail="Please check your email for the reset link"
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """
    Reset password using the reset token.

    The token is sent to the user's email via the forgot-password endpoint.
    """
    user = db.query(User).filter(
        User.reset_token == reset_data.token
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )

    # Check if token expired
    if user.reset_token_expires and user.reset_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )

    # Update password
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    user.updated_at = datetime.utcnow()
    db.commit()

    return MessageResponse(message="Password successfully reset")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change password for the currently logged in user.

    Requires the current password for verification.
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()

    return MessageResponse(message="Password successfully changed")
