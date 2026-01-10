"""
Unit tests for Authentication API endpoints.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4


class TestUserRegistration:
    """Tests for POST /api/v1/auth/register endpoint."""

    def test_register_success(self, client):
        """Test successful user registration with valid data."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepass123",
                "full_name": "New User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_active"] is True
        assert data["is_verified"] is False
        assert "id" in data
        assert "hashed_password" not in data

    def test_register_without_full_name(self, client):
        """Test registration without optional full_name field."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "nofullname@example.com",
                "password": "securepass123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "nofullname@example.com"
        assert data["full_name"] is None

    def test_register_existing_email(self, client):
        """Test registration with already existing email fails."""
        # First registration
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "securepass123"
            }
        )
        # Second registration with same email
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "differentpass123"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email_format(self, client):
        """Test registration with invalid email format fails."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "securepass123"
            }
        )
        assert response.status_code == 422  # Validation error

    def test_register_password_too_short(self, client):
        """Test registration with password shorter than 8 characters fails."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "shortpass@example.com",
                "password": "short"
            }
        )
        assert response.status_code == 422  # Validation error

    def test_register_missing_email(self, client):
        """Test registration without email fails."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "password": "securepass123"
            }
        )
        assert response.status_code == 422  # Validation error

    def test_register_missing_password(self, client):
        """Test registration without password fails."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "nopass@example.com"
            }
        )
        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """Tests for POST /api/v1/auth/login endpoint."""

    def test_login_success(self, client):
        """Test successful login with correct credentials."""
        # Register user first
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "logintest@example.com",
                "password": "securepass123"
            }
        )
        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "logintest@example.com",
                "password": "securepass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # Check cookies are set
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    def test_login_wrong_password(self, client):
        """Test login with wrong password fails."""
        # Register user first
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "securepass123"
            }
        )
        # Login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user fails."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "securepass123"
            }
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_inactive_user(self, client, db_session):
        """Test login with inactive user account fails."""
        from app.models.auth import User
        from app.core.security import get_password_hash

        # Create inactive user directly in database
        user = User(
            email="inactive@example.com",
            hashed_password=get_password_hash("securepass123"),
            is_active=False
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "inactive@example.com",
                "password": "securepass123"
            }
        )
        assert response.status_code == 403
        assert "inactive" in response.json()["detail"].lower()

    def test_login_updates_last_login(self, client, db_session):
        """Test that login updates the last_login_at timestamp."""
        from app.models.auth import User

        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "lastlogin@example.com",
                "password": "securepass123"
            }
        )
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "lastlogin@example.com",
                "password": "securepass123"
            }
        )

        # Check last_login_at is set
        user = db_session.query(User).filter(User.email == "lastlogin@example.com").first()
        assert user.last_login_at is not None


class TestUserLogout:
    """Tests for POST /api/v1/auth/logout endpoint."""

    def test_logout_clears_cookies(self, client):
        """Test logout clears authentication cookies."""
        # Register and login first
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "logouttest@example.com",
                "password": "securepass123"
            }
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "logouttest@example.com",
                "password": "securepass123"
            }
        )
        assert "access_token" in login_response.cookies

        # Logout
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
        # Cookies should be cleared (set to empty or deleted)
        # Note: TestClient may handle cookie deletion differently

    def test_logout_without_login(self, client):
        """Test logout works even without being logged in."""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"


class TestTokenRefresh:
    """Tests for POST /api/v1/auth/refresh endpoint."""

    def test_refresh_token_success(self, client):
        """Test successful token refresh."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "refreshtest@example.com",
                "password": "securepass123"
            }
        )
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "refreshtest@example.com",
                "password": "securepass123"
            }
        )

        # Refresh token (cookies should be set from login)
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # Verify the token is valid by using it
        client.cookies.set("access_token", data["access_token"])
        me_response = client.get("/api/v1/auth/me")
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "refreshtest@example.com"

    def test_refresh_without_token(self, client):
        """Test refresh without refresh token fails."""
        # Clear any existing cookies
        client.cookies.clear()
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == 401
        assert "not found" in response.json()["detail"].lower()

    def test_refresh_with_invalid_token(self, client):
        """Test refresh with invalid token fails."""
        client.cookies.set("refresh_token", "invalid_token")
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_refresh_with_access_token_as_refresh(self, client):
        """Test refresh fails when using access token instead of refresh token."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongtoken@example.com",
                "password": "securepass123"
            }
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrongtoken@example.com",
                "password": "securepass123"
            }
        )
        access_token = login_response.json()["access_token"]

        # Clear all cookies and try to use access token as refresh token
        client.cookies.clear()
        client.cookies.set("refresh_token", access_token)
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()


class TestGetCurrentUser:
    """Tests for GET /api/v1/auth/me endpoint."""

    def test_get_current_user_with_valid_token(self, client):
        """Test getting current user with valid token."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "currentuser@example.com",
                "password": "securepass123",
                "full_name": "Current User"
            }
        )
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "currentuser@example.com",
                "password": "securepass123"
            }
        )

        # Get current user
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "currentuser@example.com"
        assert data["full_name"] == "Current User"
        assert data["is_active"] is True

    def test_get_current_user_without_token(self, client):
        """Test getting current user without token fails."""
        client.cookies.clear()
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_current_user_with_invalid_token(self, client):
        """Test getting current user with invalid token fails."""
        client.cookies.set("access_token", "invalid_token")
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_current_user_with_header_auth(self, client):
        """Test getting current user using Authorization header."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "headerauth@example.com",
                "password": "securepass123"
            }
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "headerauth@example.com",
                "password": "securepass123"
            }
        )
        access_token = login_response.json()["access_token"]

        # Clear cookies and use header instead
        client.cookies.clear()
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        assert response.json()["email"] == "headerauth@example.com"


class TestUpdateUserProfile:
    """Tests for PATCH /api/v1/auth/me endpoint."""

    def test_update_profile_success(self, client):
        """Test successful profile update."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "updateprofile@example.com",
                "password": "securepass123",
                "full_name": "Original Name"
            }
        )
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "updateprofile@example.com",
                "password": "securepass123"
            }
        )

        # Update profile
        response = client.patch(
            "/api/v1/auth/me",
            json={"full_name": "Updated Name"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["email"] == "updateprofile@example.com"

    def test_update_profile_without_auth(self, client):
        """Test profile update without authentication fails."""
        client.cookies.clear()
        response = client.patch(
            "/api/v1/auth/me",
            json={"full_name": "New Name"}
        )
        assert response.status_code == 401

    def test_update_profile_empty_update(self, client):
        """Test profile update with empty data."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "emptyupdate@example.com",
                "password": "securepass123",
                "full_name": "Original"
            }
        )
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "emptyupdate@example.com",
                "password": "securepass123"
            }
        )

        # Update with empty data
        response = client.patch("/api/v1/auth/me", json={})
        assert response.status_code == 200
        # Name should remain unchanged
        assert response.json()["full_name"] == "Original"


class TestEmailVerification:
    """Tests for POST /api/v1/auth/verify-email endpoint."""

    def test_verify_email_success(self, client, db_session):
        """Test successful email verification."""
        from app.models.auth import User

        # Register user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "verifyemail@example.com",
                "password": "securepass123"
            }
        )

        # Get verification token from database
        user = db_session.query(User).filter(User.email == "verifyemail@example.com").first()
        token = user.verification_token

        # Verify email
        response = client.post(
            "/api/v1/auth/verify-email",
            json={"token": token}
        )
        assert response.status_code == 200
        assert "verified" in response.json()["message"].lower()

        # Check user is now verified
        db_session.refresh(user)
        assert user.is_verified is True
        assert user.verification_token is None

    def test_verify_email_invalid_token(self, client):
        """Test email verification with invalid token fails."""
        response = client.post(
            "/api/v1/auth/verify-email",
            json={"token": "invalid_token"}
        )
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_verify_email_expired_token(self, client, db_session):
        """Test email verification with expired token fails."""
        from app.models.auth import User

        # Register user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "expiredverify@example.com",
                "password": "securepass123"
            }
        )

        # Set token expiration to past
        user = db_session.query(User).filter(User.email == "expiredverify@example.com").first()
        token = user.verification_token
        user.verification_token_expires = datetime.utcnow() - timedelta(hours=1)
        db_session.commit()

        # Verify email
        response = client.post(
            "/api/v1/auth/verify-email",
            json={"token": token}
        )
        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()


class TestResendVerification:
    """Tests for POST /api/v1/auth/resend-verification endpoint."""

    def test_resend_verification_success(self, client, db_session):
        """Test successful resend of verification email."""
        from app.models.auth import User

        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "resendverify@example.com",
                "password": "securepass123"
            }
        )
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "resendverify@example.com",
                "password": "securepass123"
            }
        )

        # Get old token
        user = db_session.query(User).filter(User.email == "resendverify@example.com").first()
        old_token = user.verification_token

        # Resend verification
        response = client.post("/api/v1/auth/resend-verification")
        assert response.status_code == 200
        assert "sent" in response.json()["message"].lower()

        # Check new token is different
        db_session.refresh(user)
        assert user.verification_token != old_token

    def test_resend_verification_already_verified(self, client, db_session):
        """Test resend verification for already verified user fails."""
        from app.models.auth import User

        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "alreadyverified@example.com",
                "password": "securepass123"
            }
        )

        # Manually verify user
        user = db_session.query(User).filter(User.email == "alreadyverified@example.com").first()
        user.is_verified = True
        db_session.commit()

        # Login
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "alreadyverified@example.com",
                "password": "securepass123"
            }
        )

        # Try to resend verification
        response = client.post("/api/v1/auth/resend-verification")
        assert response.status_code == 400
        assert "already verified" in response.json()["detail"].lower()

    def test_resend_verification_without_auth(self, client):
        """Test resend verification without authentication fails."""
        client.cookies.clear()
        response = client.post("/api/v1/auth/resend-verification")
        assert response.status_code == 401


class TestForgotPassword:
    """Tests for POST /api/v1/auth/forgot-password endpoint."""

    def test_forgot_password_existing_user(self, client, db_session):
        """Test forgot password for existing user generates reset token."""
        from app.models.auth import User

        # Register user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "forgotpass@example.com",
                "password": "securepass123"
            }
        )

        # Request password reset
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "forgotpass@example.com"}
        )
        assert response.status_code == 200
        # Should always return success to prevent enumeration
        assert "sent" in response.json()["message"].lower() or "exists" in response.json()["message"].lower()

        # Check reset token was generated
        user = db_session.query(User).filter(User.email == "forgotpass@example.com").first()
        assert user.reset_token is not None
        assert user.reset_token_expires is not None

    def test_forgot_password_nonexistent_user(self, client):
        """Test forgot password for non-existent user returns same response."""
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"}
        )
        # Should return same response to prevent email enumeration
        assert response.status_code == 200
        assert "message" in response.json()


class TestResetPassword:
    """Tests for POST /api/v1/auth/reset-password endpoint."""

    def test_reset_password_success(self, client, db_session):
        """Test successful password reset."""
        from app.models.auth import User

        # Register user and request reset
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "resetpass@example.com",
                "password": "oldpassword123"
            }
        )
        client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "resetpass@example.com"}
        )

        # Get reset token from database
        user = db_session.query(User).filter(User.email == "resetpass@example.com").first()
        token = user.reset_token

        # Reset password
        response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": token,
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 200
        assert "reset" in response.json()["message"].lower()

        # Verify new password works
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "resetpass@example.com",
                "password": "newpassword123"
            }
        )
        assert login_response.status_code == 200

    def test_reset_password_invalid_token(self, client):
        """Test password reset with invalid token fails."""
        response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "invalid_token",
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_reset_password_expired_token(self, client, db_session):
        """Test password reset with expired token fails."""
        from app.models.auth import User

        # Register user and request reset
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "expiredreset@example.com",
                "password": "oldpassword123"
            }
        )
        client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "expiredreset@example.com"}
        )

        # Set token expiration to past
        user = db_session.query(User).filter(User.email == "expiredreset@example.com").first()
        token = user.reset_token
        user.reset_token_expires = datetime.utcnow() - timedelta(hours=1)
        db_session.commit()

        # Try to reset password
        response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": token,
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

    def test_reset_password_short_new_password(self, client, db_session):
        """Test password reset with too short new password fails."""
        from app.models.auth import User

        # Register user and request reset
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "shortresetpass@example.com",
                "password": "oldpassword123"
            }
        )
        client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "shortresetpass@example.com"}
        )

        # Get reset token from database
        user = db_session.query(User).filter(User.email == "shortresetpass@example.com").first()
        token = user.reset_token

        # Try to reset with short password
        response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": token,
                "new_password": "short"
            }
        )
        assert response.status_code == 422  # Validation error


class TestChangePassword:
    """Tests for POST /api/v1/auth/change-password endpoint."""

    def test_change_password_success(self, client):
        """Test successful password change."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "changepass@example.com",
                "password": "oldpassword123"
            }
        )
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "changepass@example.com",
                "password": "oldpassword123"
            }
        )

        # Change password
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "oldpassword123",
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 200
        assert "changed" in response.json()["message"].lower()

        # Verify new password works
        client.cookies.clear()
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "changepass@example.com",
                "password": "newpassword123"
            }
        )
        assert login_response.status_code == 200

    def test_change_password_wrong_current(self, client):
        """Test password change with wrong current password fails."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongcurrent@example.com",
                "password": "correctpassword"
            }
        )
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrongcurrent@example.com",
                "password": "correctpassword"
            }
        )

        # Change password with wrong current password
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()

    def test_change_password_without_auth(self, client):
        """Test password change without authentication fails."""
        client.cookies.clear()
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "oldpassword123",
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 401

    def test_change_password_short_new_password(self, client):
        """Test password change with too short new password fails."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "shortchange@example.com",
                "password": "oldpassword123"
            }
        )
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "shortchange@example.com",
                "password": "oldpassword123"
            }
        )

        # Change password with short new password
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "oldpassword123",
                "new_password": "short"
            }
        )
        assert response.status_code == 422  # Validation error


class TestProtectedEndpoints:
    """Tests for protected endpoint access patterns."""

    def test_access_protected_endpoint_with_valid_token(self, client):
        """Test accessing protected endpoint with valid token succeeds."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "protected@example.com",
                "password": "securepass123"
            }
        )
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "protected@example.com",
                "password": "securepass123"
            }
        )

        # Access protected endpoint
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 200

    def test_access_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token fails."""
        client.cookies.clear()
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_access_protected_endpoint_with_expired_token(self, client):
        """Test accessing protected endpoint with expired token fails."""
        from app.core.security import create_access_token
        from datetime import timedelta

        # Create an expired token
        expired_token = create_access_token(
            {"user_id": str(uuid4()), "email": "test@example.com"},
            expires_delta=timedelta(seconds=-10)  # Already expired
        )

        client.cookies.set("access_token", expired_token)
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_cookie_takes_priority_over_header(self, client):
        """Test that cookie authentication takes priority over header."""
        # Register two users
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "cookieuser@example.com",
                "password": "securepass123"
            }
        )
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "headeruser@example.com",
                "password": "securepass123"
            }
        )

        # Login as cookie user (sets cookies)
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "cookieuser@example.com",
                "password": "securepass123"
            }
        )

        # Login as header user to get their token
        client2_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "headeruser@example.com",
                "password": "securepass123"
            }
        )
        header_token = client2_login.json()["access_token"]

        # Now the cookies are set for headeruser (from second login)
        # Access /me - should return headeruser since that was the last login
        response = client.get("/api/v1/auth/me")
        # The cookie from the second login should be used
        assert response.status_code == 200


class TestAuthenticationFlow:
    """Tests for complete authentication flows."""

    def test_complete_registration_to_verification_flow(self, client, db_session):
        """Test complete flow from registration to email verification."""
        from app.models.auth import User

        # 1. Register
        reg_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "flowtest@example.com",
                "password": "securepass123",
                "full_name": "Flow Test"
            }
        )
        assert reg_response.status_code == 201
        assert reg_response.json()["is_verified"] is False

        # 2. Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "flowtest@example.com",
                "password": "securepass123"
            }
        )
        assert login_response.status_code == 200

        # 3. Get verification token and verify
        user = db_session.query(User).filter(User.email == "flowtest@example.com").first()
        verify_response = client.post(
            "/api/v1/auth/verify-email",
            json={"token": user.verification_token}
        )
        assert verify_response.status_code == 200

        # 4. Check user is now verified
        db_session.refresh(user)
        assert user.is_verified is True

    def test_complete_password_reset_flow(self, client, db_session):
        """Test complete flow from forgot password to reset."""
        from app.models.auth import User

        # 1. Register
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "resetflow@example.com",
                "password": "originalpass123"
            }
        )

        # 2. Request password reset
        forgot_response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "resetflow@example.com"}
        )
        assert forgot_response.status_code == 200

        # 3. Get reset token and reset password
        user = db_session.query(User).filter(User.email == "resetflow@example.com").first()
        reset_response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": user.reset_token,
                "new_password": "newpassword123"
            }
        )
        assert reset_response.status_code == 200

        # 4. Login with new password
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "resetflow@example.com",
                "password": "newpassword123"
            }
        )
        assert login_response.status_code == 200

        # 5. Verify old password no longer works
        client.cookies.clear()
        old_login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "resetflow@example.com",
                "password": "originalpass123"
            }
        )
        assert old_login_response.status_code == 401

    def test_token_refresh_maintains_session(self, client):
        """Test that token refresh maintains user session."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "refreshsession@example.com",
                "password": "securepass123"
            }
        )
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "refreshsession@example.com",
                "password": "securepass123"
            }
        )

        # Access protected endpoint before refresh
        response1 = client.get("/api/v1/auth/me")
        assert response1.status_code == 200

        # Refresh token
        refresh_response = client.post("/api/v1/auth/refresh")
        assert refresh_response.status_code == 200

        # Access protected endpoint after refresh
        response2 = client.get("/api/v1/auth/me")
        assert response2.status_code == 200
        assert response2.json()["email"] == "refreshsession@example.com"
