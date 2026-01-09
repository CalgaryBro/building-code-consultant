"""
Database connection and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from .config import get_settings

settings = get_settings()

# Create engine
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.
    Used with FastAPI's Depends().
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Called at application startup.
    """
    # Import all models to register them with Base
    from . import models  # noqa
    from sqlalchemy import text

    # Enable required PostgreSQL extensions (only for PostgreSQL)
    if "postgresql" in settings.database_url:
        with engine.connect() as conn:
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
                conn.commit()
            except Exception as e:
                print(f"Warning: Could not create extensions: {e}")

    Base.metadata.create_all(bind=engine)
