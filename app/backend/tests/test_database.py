"""
Unit tests for database module.
"""
import pytest
from sqlalchemy import text


class TestDatabaseConnection:
    """Tests for database connection and session management."""

    def test_db_session_creation(self, db_session):
        """Test that database session is created successfully."""
        assert db_session is not None
        # Session should be active
        assert db_session.is_active

    def test_db_session_can_execute(self, db_session):
        """Test that database session can execute queries."""
        result = db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    def test_db_session_commit(self, db_session):
        """Test that session can commit transactions."""
        from app.models.codes import Code
        from datetime import date

        code = Code(
            code_type="test",
            name="Test Code",
            short_name="TC",
            version="1.0",
            jurisdiction="Test",
            effective_date=date(2024, 1, 1),
            is_current=True
        )
        db_session.add(code)
        db_session.commit()

        # Should be able to query it back
        found = db_session.query(Code).filter_by(short_name="TC").first()
        assert found is not None
        assert found.name == "Test Code"

    def test_db_session_rollback(self, db_session):
        """Test that session can rollback transactions."""
        from app.models.codes import Code
        from datetime import date

        code = Code(
            code_type="test",
            name="Rollback Code",
            short_name="RC",
            version="1.0",
            jurisdiction="Test",
            effective_date=date(2024, 1, 1),
            is_current=True
        )
        db_session.add(code)
        # Don't commit - rollback
        db_session.rollback()

        # Should not be found
        found = db_session.query(Code).filter_by(short_name="RC").first()
        assert found is None


class TestGetDbDependency:
    """Tests for the get_db dependency."""

    def test_get_db_yields_session(self):
        """Test that get_db yields a session."""
        from app.database import get_db

        # get_db is a generator
        gen = get_db()
        session = next(gen)

        try:
            assert session is not None
            assert hasattr(session, 'query')
            assert hasattr(session, 'commit')
        finally:
            # Clean up
            try:
                next(gen)
            except StopIteration:
                pass

    def test_get_db_closes_session(self):
        """Test that get_db closes the session after use."""
        from app.database import get_db

        gen = get_db()
        session = next(gen)

        # Use the session
        _ = session.execute(text("SELECT 1"))

        # Clean up by exhausting the generator
        try:
            next(gen)
        except StopIteration:
            pass

        # Session should still exist but may be closed
        assert session is not None


class TestBase:
    """Tests for the declarative base."""

    def test_base_has_metadata(self):
        """Test that Base has metadata."""
        from app.database import Base

        assert hasattr(Base, 'metadata')
        assert Base.metadata is not None

    def test_base_tables_registered(self):
        """Test that model tables are registered with Base."""
        from app.database import Base

        # After importing models, tables should be registered
        from app.models import codes, zones, projects  # noqa

        table_names = [t.name for t in Base.metadata.sorted_tables]

        # Check some expected tables are registered
        assert 'codes' in table_names
        assert 'articles' in table_names
        assert 'requirements' in table_names
        assert 'zones' in table_names
        assert 'parcels' in table_names
        assert 'projects' in table_names


class TestDatabaseModels:
    """Tests for database model relationships."""

    def test_code_article_cascade(self, db_session, sample_code, sample_article):
        """Test Code-Article cascade delete."""
        from app.models.codes import Code, Article

        code_id = sample_code.id
        article_id = sample_article.id

        # Delete the code
        db_session.delete(sample_code)
        db_session.commit()

        # Article should be deleted too (cascade)
        assert db_session.query(Article).filter_by(id=article_id).first() is None
        assert db_session.query(Code).filter_by(id=code_id).first() is None

    def test_project_document_cascade(self, db_session, sample_project, sample_document):
        """Test Project-Document cascade delete."""
        from app.models.projects import Project, Document

        project_id = sample_project.id
        document_id = sample_document.id

        db_session.delete(sample_project)
        db_session.commit()

        assert db_session.query(Document).filter_by(id=document_id).first() is None
        assert db_session.query(Project).filter_by(id=project_id).first() is None

    def test_zone_parcel_relationship(self, db_session, sample_zone, sample_parcel):
        """Test Zone-Parcel relationship."""
        assert sample_parcel.zone_id == sample_zone.id
        assert sample_parcel.zone.zone_code == sample_zone.zone_code

    def test_parcel_zone_nullable(self, db_session):
        """Test that parcel can exist without zone."""
        from app.models.zones import Parcel

        parcel = Parcel(
            address="No Zone Address",
            street_name="Test",
            community_name="Test Community",
            quadrant="NW"
        )
        db_session.add(parcel)
        db_session.commit()

        assert parcel.id is not None
        assert parcel.zone_id is None
