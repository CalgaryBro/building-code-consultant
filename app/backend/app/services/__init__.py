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

# DSSP calculation services
from .dssp import (
    # IDF Curves
    IDFCurveService,
    idf_service,
    # Stormwater
    StormwaterCalculator,
    stormwater_calculator,
    CatchmentData,
    # Sanitary
    SanitaryCalculator,
    sanitary_calculator,
    SanitaryLoadData,
    # Water
    WaterCalculator,
    water_calculator,
    WaterLoadData,
)

# Quantity Survey services
from .quantity_survey import (
    CostDataService,
    EstimatorService,
    BOQGeneratorService,
    get_cost_service,
    get_estimator_service,
    get_boq_service,
    EstimateResult,
    BOQResult,
)
