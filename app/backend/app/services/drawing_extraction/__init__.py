"""
Drawing Extraction Module

VLM-free pipeline for extracting and analyzing building drawings.
Provides PDF vector extraction, geometry analysis, and OCR processing.

Components:
- PDFDrawingExtractor: Extract vectors, text, and images from PDF drawings
- GeometryAnalyzer: Analyze room geometry, calculate areas, check setbacks
- DrawingOCR: Optical character recognition for dimensions and labels

Example:
    >>> from app.services.drawing_extraction import (
    ...     PDFDrawingExtractor,
    ...     GeometryAnalyzer,
    ...     DrawingOCR
    ... )
    >>>
    >>> # Extract from PDF
    >>> with PDFDrawingExtractor("floor_plan.pdf") as extractor:
    ...     result = extractor.extract_all(page_num=0)
    ...     image = extractor.render_to_image(page_num=0, dpi=200)
    >>>
    >>> # Analyze geometry
    >>> analyzer = GeometryAnalyzer(scale_factor=0.001)  # mm to m
    >>> rooms = analyzer.detect_rooms_from_vectors(result.vectors)
    >>> for room in rooms:
    ...     compliance = analyzer.check_minimum_room_size(room)
    ...     print(f"{room.name}: {room.area_m2:.2f} m^2 - {compliance['compliant']}")
    >>>
    >>> # OCR for dimensions
    >>> ocr = DrawingOCR(gpu=False)
    >>> dimensions = ocr.extract_dimensions(image)
    >>> for dim in dimensions:
    ...     print(f"{dim.value} {dim.unit}")
"""

# PDF Extraction
from .pdf_extractor import (
    PDFDrawingExtractor,
    VectorElement,
    VectorType,
    TextElement,
    ImageElement,
    Point,
    BoundingBox,
    PageMetadata,
    DrawingExtractionResult,
)

# Geometry Analysis
from .geometry_analyzer import (
    GeometryAnalyzer,
    Room,
    RoomType,
    Dimension,
    WallSegment,
    SetbackAnalysis,
)

# OCR Processing
from .ocr_processor import (
    DrawingOCR,
    OCRResult,
    TextType,
    ParsedDimension,
)

__all__ = [
    # PDF Extraction
    "PDFDrawingExtractor",
    "VectorElement",
    "VectorType",
    "TextElement",
    "ImageElement",
    "Point",
    "BoundingBox",
    "PageMetadata",
    "DrawingExtractionResult",
    # Geometry Analysis
    "GeometryAnalyzer",
    "Room",
    "RoomType",
    "Dimension",
    "WallSegment",
    "SetbackAnalysis",
    # OCR Processing
    "DrawingOCR",
    "OCRResult",
    "TextType",
    "ParsedDimension",
]

__version__ = "0.1.0"
