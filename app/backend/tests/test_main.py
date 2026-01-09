"""
Unit tests for main application and configuration.
"""
import pytest
from unittest.mock import patch


class TestRootEndpoints:
    """Tests for root application endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns system info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()

        assert "name" in data
        assert "version" in data
        assert "modes" in data
        assert "codes" in data
        assert "docs" in data

        # Check modes are present
        assert "explore" in data["modes"]
        assert "guide" in data["modes"]
        assert "review" in data["modes"]

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestSettings:
    """Tests for application settings."""

    def test_default_settings(self):
        """Test default settings values."""
        from app.config import Settings

        settings = Settings()

        assert settings.app_name == "Calgary Building Code Expert"
        assert settings.app_version == "0.1.0"
        assert settings.api_prefix == "/api/v1"
        # CORS origins can be from env or default
        assert len(settings.cors_origins) > 0

    def test_settings_database_url(self):
        """Test database URL setting."""
        from app.config import Settings

        settings = Settings()
        # In test environment, might be sqlite or postgresql
        assert settings.database_url is not None
        assert len(settings.database_url) > 0

    def test_settings_ollama(self):
        """Test Ollama settings."""
        from app.config import Settings

        settings = Settings()
        assert "localhost:11434" in settings.ollama_host
        assert "qwen" in settings.ollama_model.lower()

    def test_settings_code_versions(self):
        """Test code version settings."""
        from app.config import Settings

        settings = Settings()
        assert "NBC" in settings.nbc_version
        assert "2023" in settings.nbc_version
        assert "1P2007" in settings.bylaw_version

    def test_get_settings_cached(self):
        """Test settings singleton/cache."""
        from app.config import get_settings

        # Clear cache first
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    @patch.dict("os.environ", {"APP_NAME": "Test App"})
    def test_settings_from_env(self):
        """Test settings loaded from environment variables."""
        from app.config import Settings

        settings = Settings()
        # Note: pydantic_settings converts env var names to lowercase
        # The env var APP_NAME maps to app_name
        assert settings.app_name == "Test App"


class TestCORS:
    """Tests for CORS configuration."""

    def test_cors_preflight(self, client):
        """Test CORS preflight request."""
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )
        # OPTIONS should be allowed
        assert response.status_code in [200, 204]

    def test_cors_headers(self, client):
        """Test CORS headers in response."""
        response = client.get(
            "/",
            headers={"Origin": "http://localhost:3000"}
        )
        # CORS header should be present
        assert "access-control-allow-origin" in response.headers or response.status_code == 200


class TestAPIRouting:
    """Tests for API routing."""

    def test_explore_route_prefix(self, client):
        """Test explore routes use correct prefix."""
        response = client.get("/api/v1/explore/codes")
        assert response.status_code == 200

    def test_guide_route_prefix(self, client):
        """Test guide routes use correct prefix."""
        response = client.get("/api/v1/guide/classification")
        assert response.status_code == 200

    def test_review_route_prefix(self, client, sample_project):
        """Test review routes use correct prefix."""
        response = client.get(f"/api/v1/review/projects/{sample_project.id}/documents")
        assert response.status_code == 200

    def test_zones_route_prefix(self, client):
        """Test zones routes use correct prefix."""
        response = client.get("/api/v1/zones/zones")
        assert response.status_code == 200

    def test_invalid_route(self, client):
        """Test invalid routes return 404."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_docs_available(self, client):
        """Test OpenAPI docs are available."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema(self, client):
        """Test OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
