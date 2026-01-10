"""
Pytest fixtures for Calgary Building Code Expert System tests.
"""
import os
import pytest
from datetime import date, datetime
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Set test environment before importing app modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["DATABASE_ECHO"] = "false"

from app.database import Base, get_db
from app.main import app
from app.models.codes import Code, Article, Requirement, RequirementCondition
from app.models.zones import Zone, ZoneRule, Parcel
from app.models.projects import Project, ComplianceCheck, Document, ExtractedData
from app.models.auth import User  # Import User model for auth tests
from app.models.permits import PermitApplication  # Import PermitApplication for permit tests
from app.models.standata import Standata  # Import Standata for standata tests


# Create test database
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_code(db_session):
    """Create a sample code for testing."""
    code = Code(
        id=uuid4(),
        code_type="building",
        name="National Building Code (Alberta Edition)",
        short_name="NBC(AE)",
        version="2023",
        jurisdiction="Alberta",
        effective_date=date(2024, 5, 1),
        source_url="https://nrc.canada.ca/en/certifications-evaluations-standards/codes-canada",
        is_current=True,
    )
    db_session.add(code)
    db_session.commit()
    db_session.refresh(code)
    return code


@pytest.fixture
def sample_article(db_session, sample_code):
    """Create a sample article for testing."""
    article = Article(
        id=uuid4(),
        code_id=sample_code.id,
        article_number="9.8.4.1",
        title="Stair Width",
        full_text="Except as permitted in Sentences (2) to (4), the width of a stair shall be not less than 860 mm between the wall or guard on each side.",
        part_number=9,
        division_number=8,
        section_number=4,
        page_number=450,
    )
    db_session.add(article)
    db_session.commit()
    db_session.refresh(article)
    return article


@pytest.fixture
def sample_requirement(db_session, sample_article):
    """Create a sample requirement for testing."""
    requirement = Requirement(
        id=uuid4(),
        article_id=sample_article.id,
        requirement_type="dimensional",
        element="stair_width",
        description="Minimum stair width requirement",
        min_value=860,
        unit="mm",
        exact_quote="the width of a stair shall be not less than 860 mm",
        is_mandatory=True,
        applies_to_part_9=True,
        applies_to_part_3=False,
        occupancy_groups=["C", "D", "E"],
        extraction_method="manual",
        extraction_confidence="HIGH",
        source_document="NBC(AE) 2023",
        source_page=450,
        source_edition="2023",
        is_verified=True,
        verified_by="Test User",
        verified_date=datetime.utcnow(),
    )
    db_session.add(requirement)
    db_session.commit()
    db_session.refresh(requirement)
    return requirement


@pytest.fixture
def sample_zone(db_session):
    """Create a sample zone for testing."""
    zone = Zone(
        id=uuid4(),
        zone_code="R-C1",
        zone_name="Residential - Contextual One Dwelling District",
        category="residential",
        district="RESIDENTIAL",
        description="Single detached dwellings in established neighbourhoods",
        max_height_m=10,
        max_storeys=2,
        min_front_setback_m=6.0,
        min_side_setback_m=1.2,
        min_rear_setback_m=7.5,
    )
    db_session.add(zone)
    db_session.commit()
    db_session.refresh(zone)
    return zone


@pytest.fixture
def sample_parcel(db_session, sample_zone):
    """Create a sample parcel for testing."""
    parcel = Parcel(
        id=uuid4(),
        address="123 Test Street NW",
        street_name="Test",
        street_type="ST",
        street_direction="NW",
        house_number="123",
        community_name="Test Community",
        quadrant="NW",
        zone_id=sample_zone.id,
        land_use_designation="R-C1",
        latitude=51.0447,
        longitude=-114.0719,
    )
    db_session.add(parcel)
    db_session.commit()
    db_session.refresh(parcel)
    return parcel


@pytest.fixture
def sample_project(db_session, sample_parcel):
    """Create a sample project for testing."""
    project = Project(
        id=uuid4(),
        project_name="Test Project",
        description="A test project for unit testing",
        address="123 Test Street NW",
        parcel_id=sample_parcel.id,
        classification="PART_9",
        occupancy_group="C",
        construction_type="combustible",
        building_height_storeys=2,
        building_height_m=7.0,
        building_area_sqm=250,
        footprint_area_sqm=150,
        dwelling_units=1,
        project_type="new_construction",
        development_permit_required=True,
        building_permit_required=True,
        estimated_permit_fee=5500,
        status="draft",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def sample_document(db_session, sample_project):
    """Create a sample document for testing."""
    document = Document(
        id=uuid4(),
        project_id=sample_project.id,
        filename="floor-plan.pdf",
        file_path="/uploads/floor-plan.pdf",
        file_type="pdf",
        file_size_bytes=2500000,
        document_type="floor_plan",
        extraction_status="pending",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document


@pytest.fixture
def sample_extracted_data(db_session, sample_document):
    """Create sample extracted data for testing."""
    extracted = ExtractedData(
        id=uuid4(),
        document_id=sample_document.id,
        field_name="stair_width",
        field_category="dimension",
        value_raw="900mm",
        value_numeric=900,
        unit="mm",
        page_number=1,
        location_description="Main stairwell, ground floor",
        confidence="HIGH",
        is_verified=False,
    )
    db_session.add(extracted)
    db_session.commit()
    db_session.refresh(extracted)
    return extracted


@pytest.fixture
def sample_compliance_check(db_session, sample_project, sample_requirement, sample_document):
    """Create a sample compliance check for testing."""
    check = ComplianceCheck(
        id=uuid4(),
        project_id=sample_project.id,
        requirement_id=sample_requirement.id,
        check_category="egress",
        check_name="Stair Width",
        element="stair_width",
        required_value="≥ 860 mm",
        actual_value="900 mm",
        unit="mm",
        status="pass",
        message="Stair width meets minimum requirement",
        code_reference="NBC 9.8.4.1",
        extracted_from_document_id=sample_document.id,
        extraction_confidence="HIGH",
        is_verified=True,
    )
    db_session.add(check)
    db_session.commit()
    db_session.refresh(check)
    return check


@pytest.fixture
def sample_permit_application(db_session, sample_parcel):
    """Create a sample permit application for testing."""
    permit_app = PermitApplication(
        id=uuid4(),
        application_number="DP2024-00123",
        permit_type="development",
        status="draft",
        project_name="Test Development Project",
        address="456 Test Avenue SW",
        parcel_id=sample_parcel.id,
        project_type="new_construction",
        classification="PART_9",
        occupancy_group="C",
        building_area_sqm=300.0,
        building_height_storeys=2,
        proposed_use="Single family dwelling",
        relaxations_requested=["setback_front", "height"],
        applicant_name="Test Applicant",
        applicant_email="test@example.com",
    )
    db_session.add(permit_app)
    db_session.commit()
    db_session.refresh(permit_app)
    return permit_app
