"""
Unit tests for database models.
"""
import pytest
from datetime import date, datetime
from uuid import uuid4
from decimal import Decimal

from app.models.codes import Code, Article, Requirement, RequirementCondition, CodeType, RequirementType
from app.models.zones import Zone, ZoneRule, Parcel
from app.models.projects import (
    Project, ComplianceCheck, Document, ExtractedData,
    ProjectStatus, BuildingClassification, OccupancyGroup, ComplianceStatus
)


class TestCodeModels:
    """Tests for code-related models."""

    def test_code_creation(self, db_session):
        """Test creating a Code instance."""
        code = Code(
            code_type="building",
            name="National Building Code",
            short_name="NBC",
            version="2023",
            jurisdiction="Canada",
            effective_date=date(2024, 1, 1),
            is_current=True,
        )
        db_session.add(code)
        db_session.commit()

        assert code.id is not None
        assert code.code_type == "building"
        assert code.short_name == "NBC"
        assert code.is_current is True
        assert code.created_at is not None

    def test_article_creation(self, db_session, sample_code):
        """Test creating an Article instance."""
        article = Article(
            code_id=sample_code.id,
            article_number="9.8.4.1",
            title="Stair Width",
            full_text="Test article text",
            part_number=9,
            division_number=8,
            section_number=4,
        )
        db_session.add(article)
        db_session.commit()

        assert article.id is not None
        assert article.article_number == "9.8.4.1"
        assert article.part_number == 9
        assert article.code_id == sample_code.id

    def test_article_code_relationship(self, db_session, sample_code, sample_article):
        """Test Article-Code relationship."""
        assert sample_article.code_id == sample_code.id
        assert sample_article.code.short_name == "NBC(AE)"

    def test_requirement_creation(self, db_session, sample_article):
        """Test creating a Requirement instance."""
        requirement = Requirement(
            article_id=sample_article.id,
            requirement_type="dimensional",
            element="stair_width",
            min_value=860,
            unit="mm",
            exact_quote="Test quote",
            extraction_method="manual",
            source_document="NBC 2023",
            source_edition="2023",
        )
        db_session.add(requirement)
        db_session.commit()

        assert requirement.id is not None
        assert requirement.min_value == 860
        assert requirement.is_mandatory is True  # Default
        assert requirement.is_verified is False  # Default

    def test_requirement_with_conditions(self, db_session, sample_requirement):
        """Test Requirement with RequirementConditions."""
        condition = RequirementCondition(
            requirement_id=sample_requirement.id,
            field="building_height",
            operator="<=",
            value_numeric=3,
            unit="storeys",
            logic_with_next="AND",
            condition_order=0,
        )
        db_session.add(condition)
        db_session.commit()

        assert condition.id is not None
        assert condition.requirement_id == sample_requirement.id
        assert len(sample_requirement.conditions) == 1

    def test_article_parent_child_relationship(self, db_session, sample_code):
        """Test Article parent-child relationship."""
        parent = Article(
            code_id=sample_code.id,
            article_number="9.8",
            title="Stairs",
            full_text="Section on stairs",
            part_number=9,
        )
        db_session.add(parent)
        db_session.commit()

        child = Article(
            code_id=sample_code.id,
            article_number="9.8.4",
            title="Stair Requirements",
            full_text="Subsection on stair requirements",
            part_number=9,
            parent_article_id=parent.id,
        )
        db_session.add(child)
        db_session.commit()

        assert child.parent_article_id == parent.id
        assert child.parent.title == "Stairs"
        assert len(parent.children) == 1


class TestZoneModels:
    """Tests for zone-related models."""

    def test_zone_creation(self, db_session):
        """Test creating a Zone instance."""
        zone = Zone(
            zone_code="R-C1",
            zone_name="Residential - Contextual One Dwelling",
            category="residential",
            max_height_m=10,
            max_storeys=2,
        )
        db_session.add(zone)
        db_session.commit()

        assert zone.id is not None
        assert zone.zone_code == "R-C1"
        assert zone.category == "residential"

    def test_zone_rule_creation(self, db_session, sample_zone):
        """Test creating a ZoneRule instance."""
        rule = ZoneRule(
            zone_id=sample_zone.id,
            rule_type="setback_front",
            description="Front setback requirement",
            min_value=6.0,
            unit="m",
            bylaw_reference="LUB 1P2007 Section 40",
        )
        db_session.add(rule)
        db_session.commit()

        assert rule.id is not None
        assert rule.zone_id == sample_zone.id
        assert rule.min_value == 6.0

    def test_zone_rules_relationship(self, db_session, sample_zone):
        """Test Zone-ZoneRule relationship."""
        rule1 = ZoneRule(zone_id=sample_zone.id, rule_type="height", max_value=10)
        rule2 = ZoneRule(zone_id=sample_zone.id, rule_type="FAR", max_value=0.65)
        db_session.add_all([rule1, rule2])
        db_session.commit()

        db_session.refresh(sample_zone)
        assert len(sample_zone.rules) == 2

    def test_parcel_creation(self, db_session, sample_zone):
        """Test creating a Parcel instance."""
        parcel = Parcel(
            address="456 Example Ave SW",
            street_name="Example",
            street_type="AVE",
            street_direction="SW",
            house_number="456",
            community_name="Beltline",
            quadrant="SW",
            zone_id=sample_zone.id,
            latitude=51.0400,
            longitude=-114.0700,
        )
        db_session.add(parcel)
        db_session.commit()

        assert parcel.id is not None
        assert parcel.address == "456 Example Ave SW"
        assert parcel.zone_id == sample_zone.id

    def test_parcel_zone_relationship(self, db_session, sample_parcel, sample_zone):
        """Test Parcel-Zone relationship."""
        assert sample_parcel.zone_id == sample_zone.id
        assert sample_parcel.zone.zone_code == "R-C1"


class TestProjectModels:
    """Tests for project-related models."""

    def test_project_creation(self, db_session, sample_parcel):
        """Test creating a Project instance."""
        project = Project(
            project_name="New House",
            address="123 Test St",
            parcel_id=sample_parcel.id,
            classification="PART_9",
            occupancy_group="C",
            building_height_storeys=2,
            status="draft",
        )
        db_session.add(project)
        db_session.commit()

        assert project.id is not None
        assert project.status == "draft"
        assert project.classification == "PART_9"

    def test_project_parcel_relationship(self, db_session, sample_project, sample_parcel):
        """Test Project-Parcel relationship."""
        assert sample_project.parcel_id == sample_parcel.id
        assert sample_project.parcel.address == "123 Test Street NW"

    def test_compliance_check_creation(self, db_session, sample_project):
        """Test creating a ComplianceCheck instance."""
        check = ComplianceCheck(
            project_id=sample_project.id,
            check_category="egress",
            check_name="Exit Width",
            required_value="≥ 900mm",
            actual_value="1000mm",
            status="pass",
        )
        db_session.add(check)
        db_session.commit()

        assert check.id is not None
        assert check.status == "pass"
        assert check.is_verified is False

    def test_document_creation(self, db_session, sample_project):
        """Test creating a Document instance."""
        doc = Document(
            project_id=sample_project.id,
            filename="site-plan.pdf",
            file_path="/uploads/site-plan.pdf",
            file_type="pdf",
            document_type="site_plan",
            extraction_status="pending",
        )
        db_session.add(doc)
        db_session.commit()

        assert doc.id is not None
        assert doc.extraction_status == "pending"

    def test_extracted_data_creation(self, db_session, sample_document):
        """Test creating an ExtractedData instance."""
        data = ExtractedData(
            document_id=sample_document.id,
            field_name="front_setback",
            field_category="dimension",
            value_raw="6.0m",
            value_numeric=6.0,
            unit="m",
            confidence="HIGH",
        )
        db_session.add(data)
        db_session.commit()

        assert data.id is not None
        assert data.confidence == "HIGH"
        assert data.is_verified is False

    def test_extracted_data_verification(self, db_session, sample_extracted_data):
        """Test verifying extracted data."""
        sample_extracted_data.is_verified = True
        sample_extracted_data.verified_value = "900"
        sample_extracted_data.verified_by = "Engineer"
        sample_extracted_data.verified_at = datetime.utcnow()
        db_session.commit()

        db_session.refresh(sample_extracted_data)
        assert sample_extracted_data.is_verified is True
        assert sample_extracted_data.verified_value == "900"

    def test_project_compliance_checks_relationship(self, db_session, sample_project, sample_compliance_check):
        """Test Project-ComplianceCheck relationship."""
        db_session.refresh(sample_project)
        assert len(sample_project.compliance_checks) == 1
        assert sample_project.compliance_checks[0].check_name == "Stair Width"

    def test_project_documents_relationship(self, db_session, sample_project, sample_document):
        """Test Project-Document relationship."""
        db_session.refresh(sample_project)
        assert len(sample_project.documents) == 1
        assert sample_project.documents[0].filename == "floor-plan.pdf"

    def test_document_extracted_data_relationship(self, db_session, sample_document, sample_extracted_data):
        """Test Document-ExtractedData relationship."""
        db_session.refresh(sample_document)
        assert len(sample_document.extracted_data) == 1
        assert sample_document.extracted_data[0].field_name == "stair_width"


class TestEnums:
    """Tests for enum types."""

    def test_code_type_enum(self):
        """Test CodeType enum values."""
        assert CodeType.BUILDING.value == "building"
        assert CodeType.FIRE.value == "fire"
        assert CodeType.ZONING.value == "zoning"

    def test_requirement_type_enum(self):
        """Test RequirementType enum values."""
        assert RequirementType.DIMENSIONAL.value == "dimensional"
        assert RequirementType.MATERIAL.value == "material"

    def test_project_status_enum(self):
        """Test ProjectStatus enum values."""
        assert ProjectStatus.DRAFT.value == "draft"
        assert ProjectStatus.IN_REVIEW.value == "in_review"
        assert ProjectStatus.COMPLETE.value == "complete"

    def test_compliance_status_enum(self):
        """Test ComplianceStatus enum values."""
        assert ComplianceStatus.PASS.value == "pass"
        assert ComplianceStatus.FAIL.value == "fail"
        assert ComplianceStatus.WARNING.value == "warning"

    def test_occupancy_group_enum(self):
        """Test OccupancyGroup enum values."""
        assert OccupancyGroup.C.value == "C"
        assert OccupancyGroup.D.value == "D"
        assert OccupancyGroup.F2.value == "F2"


class TestCascadeDeletes:
    """Tests for cascade delete behavior."""

    def test_code_delete_cascades_to_articles(self, db_session, sample_code, sample_article):
        """Test that deleting a Code cascades to Articles."""
        code_id = sample_code.id
        article_id = sample_article.id

        db_session.delete(sample_code)
        db_session.commit()

        assert db_session.query(Code).filter_by(id=code_id).first() is None
        assert db_session.query(Article).filter_by(id=article_id).first() is None

    def test_project_delete_cascades_to_documents(self, db_session, sample_project, sample_document):
        """Test that deleting a Project cascades to Documents."""
        project_id = sample_project.id
        document_id = sample_document.id

        db_session.delete(sample_project)
        db_session.commit()

        assert db_session.query(Project).filter_by(id=project_id).first() is None
        assert db_session.query(Document).filter_by(id=document_id).first() is None

    def test_document_delete_cascades_to_extracted_data(self, db_session, sample_document, sample_extracted_data):
        """Test that deleting a Document cascades to ExtractedData."""
        document_id = sample_document.id
        extracted_id = sample_extracted_data.id

        db_session.delete(sample_document)
        db_session.commit()

        assert db_session.query(Document).filter_by(id=document_id).first() is None
        assert db_session.query(ExtractedData).filter_by(id=extracted_id).first() is None
