"""
Business logic services for Calgary Building Code Expert System.
"""
from .embedding import EmbeddingService
from .extraction import DocumentExtractionService

# Drawing extraction services (VLM-free pipeline)
from .drawing_extraction import (
    PDFDrawingExtractor,
    GeometryAnalyzer,
    DrawingOCR,
)

# Document upload service for permits
from .document_service import DocumentService, document_service

# Fee calculator service
from .fee_calculator import FeeCalculatorService, fee_calculator
