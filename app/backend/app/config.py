"""
Configuration settings for Calgary Building Code Expert System.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from functools import lru_cache
from typing import List, Union


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application
    app_name: str = "Calgary Building Code Expert"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/calgary_codes"
    database_echo: bool = False

    # Paths
    data_dir: str = "/Users/mohmmadhanafy/Building-code-consultant/data"

    # Ollama VLM
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2-vl:7b"  # or qwen3-vl when available

    # API
    api_prefix: str = "/api/v1"
    cors_origins: Union[List[str], str] = ["http://localhost:3000", "http://localhost:5173"]

    # Code versions (effective dates)
    nbc_version: str = "NBC(AE) 2023"
    nbc_effective_date: str = "2024-05-01"
    bylaw_version: str = "1P2007-21P2024"
    bylaw_effective_date: str = "2025-01-01"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
