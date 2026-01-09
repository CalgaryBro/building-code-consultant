"""
Tests for the Drawing Extraction Module

Tests the VLM-free drawing extraction pipeline including:
- PDF vector extraction
- Geometry analysis
- OCR processing
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Import the modules
from app.services.drawing_extraction import (
    PDFDrawingExtractor,
    VectorElement,
    VectorType,
    TextElement,
    BoundingBox,
    Point,
    PageMetadata,
    DrawingExtractionResult,
    GeometryAnalyzer,
    Room,
    RoomType,
    SetbackAnalysis,
    DrawingOCR,
    OCRResult,
    TextType,
    ParsedDimension,
)


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def sample_pdf_path():
    """Create a simple test PDF for testing."""
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")

    # Create a temporary PDF with some content
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        doc = fitz.open()
        page = doc.new_page(width=612, height=792)  # Letter size

        # Add some rectangles (simulating walls)
        rect1 = fitz.Rect(100, 100, 300, 200)
        rect2 = fitz.Rect(300, 100, 500, 200)
        page.draw_rect(rect1, color=(0, 0, 0), width=2)
        page.draw_rect(rect2, color=(0, 0, 0), width=2)

        # Add some lines
        page.draw_line((100, 100), (100, 300), color=(0, 0, 0), width=1)
        page.draw_line((100, 300), (300, 300), color=(0, 0, 0), width=1)

        # Add text
        text_point = fitz.Point(150, 150)
        page.insert_text(text_point, "BEDROOM 1", fontsize=12)
        text_point2 = fitz.Point(350, 150)
        page.insert_text(text_point2, "3000mm", fontsize=10)

        doc.save(f.name)
        doc.close()
        yield f.name

    # Cleanup
    os.unlink(f.name)


@pytest.fixture
def sample_image():
    """Create a simple test image for OCR testing."""
    # Create a white image with some basic shapes
    img = np.ones((200, 400, 3), dtype=np.uint8) * 255
    return img


@pytest.fixture
def geometry_analyzer():
    """Create a GeometryAnalyzer instance."""
    return GeometryAnalyzer(scale_factor=0.001, unit="mm")


# ==============================================================================
# PDFDrawingExtractor Tests
# ==============================================================================

class TestPDFDrawingExtractor:
    """Tests for the PDFDrawingExtractor class."""

    def test_open_pdf(self, sample_pdf_path):
        """Test opening a PDF file."""
        extractor = PDFDrawingExtractor(sample_pdf_path)
        assert extractor.page_count >= 1
        extractor.close()

    def test_context_manager(self, sample_pdf_path):
        """Test using extractor as context manager."""
        with PDFDrawingExtractor(sample_pdf_path) as extractor:
            assert extractor.page_count >= 1

    def test_get_page_metadata(self, sample_pdf_path):
        """Test getting page metadata."""
        with PDFDrawingExtractor(sample_pdf_path) as extractor:
            metadata = extractor.get_page_metadata(0)
            assert isinstance(metadata, PageMetadata)
            assert metadata.page_number == 0
            assert metadata.width > 0
            assert metadata.height > 0

    def test_extract_vectors(self, sample_pdf_path):
        """Test extracting vectors from a page."""
        with PDFDrawingExtractor(sample_pdf_path) as extractor:
            vectors = extractor.extract_vectors(0)
            assert isinstance(vectors, list)
            # Should have some vectors from the rectangles and lines we drew
            assert len(vectors) > 0
            for vec in vectors:
                assert isinstance(vec, VectorElement)
                assert vec.type in VectorType

    def test_extract_text(self, sample_pdf_path):
        """Test extracting text from a page."""
        with PDFDrawingExtractor(sample_pdf_path) as extractor:
            texts = extractor.extract_text(0)
            assert isinstance(texts, list)
            # Should find the text we inserted
            text_contents = [t.text for t in texts]
            assert any("BEDROOM" in t or "3000" in t for t in text_contents)

    def test_extract_all(self, sample_pdf_path):
        """Test extracting all elements from a page."""
        with PDFDrawingExtractor(sample_pdf_path) as extractor:
            result = extractor.extract_all(0)
            assert isinstance(result, DrawingExtractionResult)
            assert result.page_metadata is not None
            assert isinstance(result.vectors, list)
            assert isinstance(result.texts, list)

    def test_render_to_image(self, sample_pdf_path):
        """Test rendering a page to image."""
        with PDFDrawingExtractor(sample_pdf_path) as extractor:
            img = extractor.render_to_image(0, dpi=100)
            assert isinstance(img, np.ndarray)
            assert len(img.shape) == 3  # Height, Width, Channels
            assert img.shape[2] == 3  # RGB

    def test_invalid_page_number(self, sample_pdf_path):
        """Test handling invalid page numbers."""
        with PDFDrawingExtractor(sample_pdf_path) as extractor:
            with pytest.raises(ValueError):
                extractor.extract_vectors(999)

    def test_file_not_found(self):
        """Test handling non-existent files."""
        with pytest.raises(Exception):  # FileNotFoundError or fitz error
            PDFDrawingExtractor("nonexistent_file.pdf")


class TestVectorElement:
    """Tests for VectorElement dataclass."""

    def test_line_length(self):
        """Test calculating line length."""
        vec = VectorElement(
            type=VectorType.LINE,
            coords=[(0, 0), (3, 4)],
            width=1.0,
            color=(0, 0, 0)
        )
        assert vec.length == 5.0  # 3-4-5 triangle

    def test_rectangle_coords(self):
        """Test rectangle coordinates."""
        vec = VectorElement(
            type=VectorType.RECTANGLE,
            coords=[(0, 0), (100, 0), (100, 50), (0, 50)],
            width=1.0,
            color=(0, 0, 0),
            closed=True
        )
        assert len(vec.coords) == 4
        assert vec.closed is True


class TestBoundingBox:
    """Tests for BoundingBox dataclass."""

    def test_width_height(self):
        """Test width and height calculation."""
        bbox = BoundingBox(x0=10, y0=20, x1=110, y1=70)
        assert bbox.width == 100
        assert bbox.height == 50

    def test_center(self):
        """Test center point calculation."""
        bbox = BoundingBox(x0=0, y0=0, x1=100, y1=100)
        center = bbox.center
        assert center.x == 50
        assert center.y == 50


# ==============================================================================
# GeometryAnalyzer Tests
# ==============================================================================

class TestGeometryAnalyzer:
    """Tests for the GeometryAnalyzer class."""

    def test_initialization(self, geometry_analyzer):
        """Test analyzer initialization."""
        assert geometry_analyzer.scale_factor == 0.001
        assert geometry_analyzer.unit == "mm"

    def test_create_polygon_from_coords(self, geometry_analyzer):
        """Test creating polygon from coordinates."""
        coords = [(0, 0), (1000, 0), (1000, 1000), (0, 1000)]
        polygon = geometry_analyzer.create_polygon_from_coords(coords)
        assert polygon is not None
        assert polygon.is_valid
        assert polygon.area == 1000000  # 1000 x 1000

    def test_calculate_area_m2(self, geometry_analyzer):
        """Test area calculation in square meters."""
        from shapely.geometry import Polygon
        # 3000mm x 4000mm room
        poly = Polygon([(0, 0), (3000, 0), (3000, 4000), (0, 4000)])
        area_m2 = geometry_analyzer.calculate_area_m2(poly)
        assert abs(area_m2 - 12.0) < 0.01  # 12 square meters

    def test_check_minimum_room_size_compliant(self, geometry_analyzer):
        """Test room size compliance check for compliant room."""
        from shapely.geometry import Polygon
        # 3500mm x 3500mm = 12.25 m^2 (above bedroom minimum)
        poly = Polygon([(0, 0), (3500, 0), (3500, 3500), (0, 3500)])
        room = Room(
            name="Test Bedroom",
            polygon=poly,
            area_drawing_units=poly.area,
            area_m2=geometry_analyzer.calculate_area_m2(poly),
            room_type=RoomType.BEDROOM
        )
        result = geometry_analyzer.check_minimum_room_size(room)
        assert result["compliant"] is True

    def test_check_minimum_room_size_non_compliant(self, geometry_analyzer):
        """Test room size compliance check for non-compliant room."""
        from shapely.geometry import Polygon
        # 2000mm x 2000mm = 4 m^2 (below bedroom minimum of 9.29)
        poly = Polygon([(0, 0), (2000, 0), (2000, 2000), (0, 2000)])
        room = Room(
            name="Small Room",
            polygon=poly,
            area_drawing_units=poly.area,
            area_m2=geometry_analyzer.calculate_area_m2(poly),
            room_type=RoomType.BEDROOM
        )
        result = geometry_analyzer.check_minimum_room_size(room)
        assert result["compliant"] is False

    def test_detect_rooms_from_lines(self, geometry_analyzer):
        """Test room detection from line segments."""
        # Create a simple square room from 4 lines
        lines = [
            ((0, 0), (4000, 0)),      # Top
            ((4000, 0), (4000, 4000)),  # Right
            ((4000, 4000), (0, 4000)),  # Bottom
            ((0, 4000), (0, 0))       # Left
        ]
        rooms = geometry_analyzer.detect_rooms_from_lines(lines, min_area=1000)
        assert len(rooms) >= 1
        # The detected room should have reasonable area
        assert rooms[0].area_drawing_units > 0

    def test_calculate_room_dimensions(self, geometry_analyzer):
        """Test room dimension calculation."""
        from shapely.geometry import Polygon
        # 3000mm x 4000mm room
        poly = Polygon([(0, 0), (3000, 0), (3000, 4000), (0, 4000)])
        room = Room(
            name="Test Room",
            polygon=poly,
            area_drawing_units=poly.area,
            area_m2=geometry_analyzer.calculate_area_m2(poly)
        )
        dims = geometry_analyzer.calculate_room_dimensions(room)
        assert abs(dims["width_m"] - 3.0) < 0.01
        assert abs(dims["length_m"] - 4.0) < 0.01

    def test_export_to_geojson(self, geometry_analyzer):
        """Test GeoJSON export."""
        from shapely.geometry import Polygon
        poly = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000)])
        room = Room(
            name="Room 1",
            polygon=poly,
            area_drawing_units=poly.area,
            area_m2=1.0,
            room_type=RoomType.BEDROOM
        )
        geometry_analyzer.rooms = [room]
        geojson = geometry_analyzer.export_to_geojson()
        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) == 1
        assert geojson["features"][0]["properties"]["name"] == "Room 1"


class TestSetbackAnalysis:
    """Tests for setback analysis."""

    def test_compliant_setbacks(self):
        """Test building within setbacks."""
        from shapely.geometry import Polygon
        analyzer = GeometryAnalyzer(scale_factor=1.0)  # 1:1 for meters

        lot = Polygon([(0, 0), (30, 0), (30, 40), (0, 40)])
        building = Polygon([(7, 10), (23, 10), (23, 30), (7, 30)])

        result = analyzer.analyze_setbacks(
            building=building,
            lot=lot,
            front_setback=6.0,
            rear_setback=6.0,
            side_setback=3.0
        )
        # Building should be compliant with these setbacks
        assert isinstance(result, SetbackAnalysis)


# ==============================================================================
# DrawingOCR Tests
# ==============================================================================

class TestDrawingOCR:
    """Tests for the DrawingOCR class."""

    def test_initialization(self):
        """Test OCR initialization (without actually loading model)."""
        ocr = DrawingOCR(gpu=False)
        assert ocr.languages == ['en']
        assert ocr.gpu is False

    def test_parse_dimension_mm(self):
        """Test parsing mm dimension."""
        ocr = DrawingOCR()
        result = ocr.parse_dimension("3000mm")
        assert result is not None
        assert result.value == 3000
        assert result.unit == "mm"

    def test_parse_dimension_m(self):
        """Test parsing meter dimension."""
        ocr = DrawingOCR()
        result = ocr.parse_dimension("3.5m")
        assert result is not None
        assert result.value == 3.5
        assert result.unit == "m"

    def test_parse_dimension_imperial(self):
        """Test parsing imperial dimension."""
        ocr = DrawingOCR()
        result = ocr.parse_dimension("10'-6\"")
        assert result is not None
        # Should parse feet and inches
        assert result.value == 126  # 10*12 + 6 inches

    def test_parse_dimension_no_unit(self):
        """Test parsing dimension without explicit unit."""
        ocr = DrawingOCR()
        result = ocr.parse_dimension("3500")
        assert result is not None
        assert result.value == 3500
        assert result.unit == "mm"  # Default to mm

    def test_parsed_dimension_to_mm(self):
        """Test conversion to mm."""
        dim = ParsedDimension(value=1.0, unit="m", raw_text="1m")
        assert dim.value_in_mm == 1000.0

        dim2 = ParsedDimension(value=12.0, unit="in", raw_text="12in")
        assert abs(dim2.value_in_mm - 304.8) < 0.1

    def test_classify_room_label(self):
        """Test room label classification."""
        ocr = DrawingOCR()
        assert ocr._is_room_label("BEDROOM 1") is True
        assert ocr._is_room_label("BATHROOM") is True
        assert ocr._is_room_label("KITCHEN") is True
        assert ocr._is_room_label("random text") is False

    def test_ocr_result_center(self):
        """Test OCRResult center calculation."""
        result = OCRResult(
            text="test",
            bbox=[(0, 0), (100, 0), (100, 50), (0, 50)],
            confidence=0.9
        )
        center = result.center
        assert center == (50, 25)

    @pytest.mark.skipif(
        not os.environ.get("RUN_OCR_TESTS"),
        reason="Full OCR tests require EasyOCR (set RUN_OCR_TESTS=1)"
    )
    def test_extract_text_from_image(self, sample_image):
        """Test actual text extraction (requires EasyOCR)."""
        ocr = DrawingOCR(gpu=False)
        results = ocr.extract_text(sample_image, min_confidence=0.1)
        assert isinstance(results, list)


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_pdf_to_geometry_pipeline(self, sample_pdf_path):
        """Test extracting PDF vectors and analyzing geometry."""
        with PDFDrawingExtractor(sample_pdf_path) as extractor:
            result = extractor.extract_all(0)

        analyzer = GeometryAnalyzer(scale_factor=0.001)

        # Try to detect rooms from extracted vectors
        rooms = analyzer.detect_rooms_from_vectors(result.vectors, min_area=100)
        # We may or may not detect rooms depending on how the PDF was created
        assert isinstance(rooms, list)

    def test_text_extraction_and_classification(self, sample_pdf_path):
        """Test extracting and classifying text."""
        with PDFDrawingExtractor(sample_pdf_path) as extractor:
            texts = extractor.extract_text(0)

        ocr = DrawingOCR()

        # Check if any text is classified as dimension or room label
        for text in texts:
            text_type, parsed = ocr._classify_text(text.text)
            assert text_type in TextType
            if text_type == TextType.DIMENSION:
                assert parsed is not None


# ==============================================================================
# Run tests
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
