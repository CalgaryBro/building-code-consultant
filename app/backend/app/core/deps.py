"""
FastAPI dependencies for authentication.
"""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.auth import User
from .security import decode_token


def get_token_from_cookie(request: Request) -> Optional[str]:
    """
    Extract the access token from httpOnly cookie.

    Args:
        request: The FastAPI request object

    Returns:
        The access token or None
    """
    return request.cookies.get("access_token")


def get_token_from_header(request: Request) -> Optional[str]:
    """
    Extract the access token from Authorization header.

    Args:
        request: The FastAPI request object

    Returns:
        The access token or None
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


def get_token(request: Request) -> Optional[str]:
    """
    Get access token from cookie or header (cookie takes priority).

    Args:
        request: The FastAPI request object

    Returns:
        The access token or None
    """
    token = get_token_from_cookie(request)
    if not token:
        token = get_token_from_header(request)
    return token


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.

    This dependency can be used in any endpoint that requires authentication.

    Args:
        request: The FastAPI request object
        db: Database session

    Returns:
        The authenticated User object

    Raises:
        HTTPException: If token is missing, invalid, or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = get_token(request)
    if not token:
        raise credentials_exception

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    # Check token type
    if payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("user_id")
    if user_id is None:
        raise credentials_exception

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current user and verify they are active.

    Use this dependency when you need to ensure the user account is not deactivated.

    Args:
        current_user: The authenticated user from get_current_user

    Returns:
        The active User object

    Raises:
        HTTPException: If user account is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get the current user and verify their email is verified.

    Use this dependency for endpoints that require email verification.

    Args:
        current_user: The active user from get_current_active_user

    Returns:
        The verified User object

    Raises:
        HTTPException: If user email is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address not verified"
        )
    return current_user


async def get_optional_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current user if authenticated, otherwise return None.

    Use this dependency for endpoints that work differently for
    authenticated vs anonymous users.

    Args:
        request: The FastAPI request object
        db: Database session

    Returns:
        The User object if authenticated, None otherwise
    """
    token = get_token(request)
    if not token:
        return None

    payload = decode_token(token)
    if payload is None:
        return None

    if payload.get("type") != "access":
        return None

    user_id = payload.get("user_id")
    if user_id is None:
        return None

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        return None

    return db.query(User).filter(User.id == user_uuid).first()
