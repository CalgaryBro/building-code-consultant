# Drawing Compliance Checking System

## Executive Summary

This document outlines the Calgary Building Code Expert System's approach to automated drawing compliance checking. The system performs **pre-screening and gap analysis** on architectural drawings against NBC 2023 Alberta Edition requirements.

**Key Positioning**: This is a code-compliance pre-screen tool, NOT a replacement for a licensed professional. The goal is to catch obvious violations, flag missing information, and provide clause references for verification.

---

## Table of Contents

1. [Code Requirements Context](#1-code-requirements-context)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [What's Already Built](#3-whats-already-built)
4. [What's Missing](#4-whats-missing)
5. [Recommended Implementation Plan](#5-recommended-implementation-plan)
6. [Technical Specifications](#6-technical-specifications)
7. [Limitations & Scope](#7-limitations--scope)

---

## 1. Code Requirements Context

### Applicable Codes (Alberta, Post May 1, 2024)

| Code | Version | Status |
|------|---------|--------|
| National Building Code | 2023 Alberta Edition | In force since May 1, 2024 |
| National Energy Code (NECB) | 2020 | In force since May 1, 2024 |
| National Fire Code | 2023 Alberta Edition | In force |
| National Plumbing Code | 2020 | In force |
| Calgary Land Use Bylaw | 1P2007 (amended) | Current |

### Part 9 vs Part 3 Distinction

| Criteria | Part 9 (Small Buildings) | Part 3 (Large Buildings) |
|----------|-------------------------|-------------------------|
| Height | ≤ 3 storeys | > 3 storeys |
| Building Area | ≤ 600 m² | > 600 m² |
| Major Occupancy | Residential, Business | Any |
| Complexity | Prescriptive rules | Performance-based |

**Note**: The system must determine Part 9 vs Part 3 applicability before applying specific rules.

---

## 2. System Architecture Overview

### Three-Server Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRODUCTION ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    VPS-2 ($8.76/mo)                                  │    │
│  │                    6 vCores, 12GB RAM                                │    │
│  │                                                                      │    │
│  │   ┌──────────────────────────────────────────────────────────┐      │    │
│  │   │  Drawing Analysis Pipeline                                │      │    │
│  │   │  ├── PDF Vector Extractor (PyMuPDF)                      │      │    │
│  │   │  ├── OCR Processor (EasyOCR)                             │      │    │
│  │   │  ├── Geometry Analyzer (Shapely)                         │      │    │
│  │   │  ├── Rule Engine (YAML-driven) ← TO BUILD                │      │    │
│  │   │  └── Report Generator ← TO BUILD                         │      │    │
│  │   └──────────────────────────────────────────────────────────┘      │    │
│  │                                                                      │    │
│  │   PostgreSQL + pgvector (3000+ code articles)                       │    │
│  │   LFM 2.5 (Chat Q&A)                                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                       │
│                                      │ HTTPS (for OCR fallback)              │
│                                      ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    ORACLE SERVER (FREE)                              │    │
│  │                    4 ARM64 Cores, 23GB RAM                           │    │
│  │                                                                      │    │
│  │   GOT-OCR2 (580M) ──→ For scanned drawings only                     │    │
│  │   Qwen2.5-7B ──→ Text structuring                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Drawing Processing Pipeline

```
PDF Upload
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Vector vs Scan Detection                                 │
│ ├── PyMuPDF: page.get_text() → count characters                 │
│ ├── If chars > 200 → Vector PDF (skip OCR)                      │
│ └── If chars < 200 → Scanned (needs OCR)                        │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Extract Drawing Elements                                 │
│ ├── PDFDrawingExtractor.extract_vectors() → walls, lines        │
│ ├── PDFDrawingExtractor.extract_text() → labels, dimensions     │
│ ├── PDFDrawingExtractor.find_dimension_lines() → measurements   │
│ └── [If scanned] DrawingOCR.extract_text() → OCR results        │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Build Drawing Facts Model                                │
│ ├── GeometryAnalyzer.detect_rooms_from_lines() → Room[]         │
│ ├── DrawingOCR.extract_dimensions() → ParsedDimension[]         │
│ ├── DrawingOCR.extract_room_labels() → room names               │
│ └── ScheduleExtractor.parse_door_schedule() → door data ← BUILD │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Rule Engine Checks ← TO BUILD                            │
│ ├── Load rules from YAML config                                 │
│ ├── For each rule: check(extracted_value, threshold)            │
│ ├── Output: PASS | FAIL | UNKNOWN                               │
│ └── Attach evidence: sheet#, bbox, extracted text               │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Generate Compliance Report ← TO BUILD                    │
│ ├── Compliance matrix by category                               │
│ ├── Evidence crops from PDF                                     │
│ ├── Code references (clause pointers)                           │
│ └── Recommendations for missing info                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. What's Already Built

### 3.1 PDF Vector Extractor

**File**: `app/backend/app/services/drawing_extraction/pdf_extractor.py`
**Lines**: 787
**Status**: ✅ Production Ready

```python
class PDFDrawingExtractor:
    """Extracts vector graphics, text, and images from PDF drawings."""

    # Key Methods:
    def extract_vectors(page) -> List[VectorElement]
        # Returns: lines, rectangles, curves, circles, polygons, paths

    def extract_text(page) -> List[TextElement]
        # Returns: text with position, font, size, rotation, color

    def extract_images(page) -> List[ImageElement]
        # Returns: embedded images with bounding boxes

    def find_dimension_lines(page) -> List[Dict]
        # Returns: dimension lines with associated text values

    def get_scale_from_text(page) -> Optional[str]
        # Parses: "1:100", "1/4\"=1'-0\"", "Scale: 1:50"

    def render_to_image(page, dpi=150) -> np.ndarray
        # Converts page to numpy array for CV/OCR processing
```

**Data Classes**:
```python
@dataclass
class VectorElement:
    type: VectorType  # LINE, RECTANGLE, CURVE, CIRCLE, POLYGON, PATH
    points: List[Tuple[float, float]]
    stroke_color: Optional[Tuple]
    fill_color: Optional[Tuple]
    stroke_width: float

@dataclass
class TextElement:
    text: str
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    font_name: str
    font_size: float
    rotation: float  # degrees
```

---

### 3.2 OCR Processor

**File**: `app/backend/app/services/drawing_extraction/ocr_processor.py`
**Lines**: 694
**Status**: ✅ Production Ready

```python
class DrawingOCR:
    """OCR processing for rasterized drawing areas using EasyOCR."""

    # Key Methods:
    def extract_text(image, min_confidence=0.3) -> List[OCRResult]
        # Extracts all text with bounding boxes and confidence

    def extract_dimensions(image) -> List[ParsedDimension]
        # Parses dimension values with unit conversion to mm

    def extract_room_labels(image) -> List[OCRResult]
        # Finds room labels: BEDROOM, BATHROOM, KITCHEN, etc.

    def classify_text_type(text) -> TextType
        # Returns: DIMENSION, ROOM_LABEL, SCALE, TITLE, ANNOTATION

    def detect_text_rotation(bbox) -> float
        # Calculates rotation angle from bounding box geometry
```

**Dimension Parsing Formats**:
```python
# Metric formats:
"1000mm", "1000 mm", "1.5m", "1.5 m", "150cm"

# Imperial formats:
"10'-6\"", "10' 6\"", "10ft 6in", "126\""

# Simple numbers (3-5 digits default to mm):
"1200" → 1200mm
```

**Room Label Patterns**:
```python
ROOM_PATTERNS = [
    "BEDROOM", "BATHROOM", "KITCHEN", "LIVING_ROOM",
    "DINING_ROOM", "HALLWAY", "CLOSET", "GARAGE",
    "BASEMENT", "UTILITY", "OFFICE", "STORAGE",
    "PORCH", "DECK", "PATIO", "BALCONY"
]
```

---

### 3.3 Geometry Analyzer

**File**: `app/backend/app/services/drawing_extraction/geometry_analyzer.py`
**Lines**: 781
**Status**: ✅ Production Ready

```python
class GeometryAnalyzer:
    """Analyzes building geometry from extracted vector graphics."""

    # Key Methods:
    def detect_rooms_from_lines(vectors) -> List[Room]
        # Uses Shapely polygonize to find enclosed areas

    def check_minimum_room_size(room, room_type) -> ComplianceResult
        # Validates against NBC minimum sizes

    def analyze_setbacks(building_polygon, lot_polygon, setbacks) -> SetbackAnalysis
        # Checks front/rear/side setback compliance

    def calculate_building_coverage(building, lot) -> float
        # Returns coverage ratio (building_area / lot_area)

    def extract_wall_segments(vectors) -> List[WallSegment]
        # Identifies parallel lines as wall thickness

    def calculate_room_dimensions(room) -> Tuple[float, float]
        # Returns min bounding rectangle (length, width)
```

**NBC Compliance Constants (Built-in)**:
```python
# Minimum Room Sizes (NBC Part 9)
MIN_ROOM_SIZES = {
    RoomType.BEDROOM: 9.29,      # m² (100 sq ft)
    RoomType.LIVING_ROOM: 13.0,  # m² (~140 sq ft)
    RoomType.KITCHEN: 4.65,      # m² (50 sq ft)
    RoomType.BATHROOM: 2.32,     # m² (25 sq ft)
}

# Minimum Dimensions
MIN_DIMENSIONS = {
    "room_width": 2.44,      # m (8 ft)
    "hallway_width": 0.86,   # m (~34 in)
    "door_width": 0.81,      # m (32 in clear)
    "stair_width": 0.86,     # m (34 in)
    "ceiling_height": 2.3,   # m (~7.5 ft)
}
```

---

### 3.4 Compliance Check Database Model

**File**: `app/backend/app/models/projects.py`
**Status**: ✅ Schema Complete

```python
class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"

    id: int
    project_id: int  # FK to projects
    document_id: Optional[int]  # FK to documents

    check_category: str  # zoning, egress, fire, structural, energy
    check_name: str      # Human-readable: "Exit Door Width"
    element: str         # Technical field: "exit_door_width"

    required_value: str  # Code requirement: "≥ 860mm"
    actual_value: str    # Extracted value: "810mm"
    status: str          # pass, fail, warning, needs_review

    code_reference: str  # "NBC 9.9.1.1.(1)"
    notes: Optional[str]
    is_verified: bool    # Manual verification flag
    verified_by: Optional[int]
    verified_at: Optional[datetime]
```

---

### 3.5 Document Service

**File**: `app/backend/app/services/document_service.py`
**Status**: ✅ Production Ready

```python
# Supported file types:
ALLOWED_TYPES = [
    "application/pdf",
    "image/png", "image/jpeg", "image/gif", "image/tiff", "image/bmp",
    "application/dwg", "application/dxf",  # CAD files
    "application/msword", "application/vnd.openxmlformats-officedocument"
]

# Maximum file size:
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Document categories:
DOCUMENT_CATEGORIES = [
    "floor_plan", "site_plan", "elevation", "section",
    "structural", "mechanical", "electrical", "plumbing",
    "energy_compliance", "survey", "title", "geotechnical",
    "drainage", "landscape", "parking", "signage",
    "fire_safety", "accessibility", "schedule", "other"
]
```

---

### 3.6 Oracle AI Services

**Location**: Oracle Server (129.153.97.27)
**Status**: ✅ Deployed and Running

| Service | Model | Port | Purpose |
|---------|-------|------|---------|
| GOT-OCR2 | 580M params | 8082 | Accurate document OCR |
| Qwen2.5-7B | 4.7GB | 11434 (Ollama) | Text structuring |

**GOT-OCR2 API Endpoints**:
```
GET  /health          → Service health check
GET  /model-info      → Model information
POST /ocr             → Raw text extraction from image
POST /structure       → Structure raw text into JSON
POST /extract         → Combined: OCR + structuring
POST /extract-file    → Upload file and extract
```

**Access Method**: SSH tunnel required (OCI firewall)
```bash
ssh -L 8082:localhost:8082 -i ~/Oracle_data/ssh-key-2025-05-12.key opc@129.153.97.27 -N &
```

---

## 4. What's Missing

### 4.1 Schedule Table Parser

**Priority**: HIGH
**Estimated Effort**: 4-6 hours

**Current State**: No dedicated schedule extraction. VLM can extract but no native parsing.

**Required Implementation**:
```python
class ScheduleExtractor:
    """Extract tabular data from door/window/stair schedules."""

    def detect_schedule_region(page) -> Optional[BoundingBox]:
        # Find "DOOR SCHEDULE", "WINDOW SCHEDULE" headers

    def parse_table_rows(region) -> List[Dict]:
        # Cluster text by Y (rows) then X (columns)
        # Infer headers from top row

    def parse_door_schedule(page) -> List[DoorScheduleEntry]:
        # Returns: mark, width, height, type, rating, hardware

    def parse_window_schedule(page) -> List[WindowScheduleEntry]:
        # Returns: mark, width, height, type, glazing, rating

    def parse_stair_schedule(page) -> List[StairScheduleEntry]:
        # Returns: id, width, rise, run, headroom, handrails
```

**Output Schema**:
```python
@dataclass
class DoorScheduleEntry:
    mark: str           # "D01", "101", "DR-1"
    width_mm: int       # Clear width
    height_mm: int      # Clear height
    type: str           # "HOLLOW METAL", "WOOD", "GLASS"
    fire_rating: str    # "20 MIN", "45 MIN", "1 HR", "NONE"
    hardware_set: str   # "HS-1", "HS-2"
    remarks: str        # Additional notes
```

---

### 4.2 YAML-Driven Rule Engine

**Priority**: HIGH
**Estimated Effort**: 6-8 hours

**Current State**: Hardcoded threshold checks in geometry_analyzer.py only.

**Required Implementation**:

**Rule Configuration File** (`rules/nbc_2023_ae_part9.yaml`):
```yaml
ruleset: "NBC_2023_AE_Part9"
version: "1.0"
effective_date: "2024-05-01"

profiles:
  residential:
    door_min_clear_mm: 860
    corridor_min_width_mm: 1100
    stair_min_width_mm: 900
    guard_min_height_mm: 1070
    handrail_min_mm: 865
    handrail_max_mm: 965

checks:
  - id: "EGRESS_001"
    name: "Exit Door Clear Width"
    category: "egress"
    input: "door_schedule[*].width_mm"
    condition: "value >= profiles.residential.door_min_clear_mm"
    code_ref: "NBC 9.9.1.1.(1)"
    severity: "high"
    message_fail: "Door {mark} width {value}mm < {threshold}mm minimum"

  - id: "EGRESS_002"
    name: "Stair Minimum Width"
    category: "egress"
    input: "stair_schedule[*].width_mm"
    condition: "value >= profiles.residential.stair_min_width_mm"
    code_ref: "NBC 9.8.2.1.(1)"
    severity: "high"

  - id: "EGRESS_003"
    name: "Corridor Minimum Width"
    category: "egress"
    input: "corridors[*].width_mm"
    condition: "value >= profiles.residential.corridor_min_width_mm"
    code_ref: "NBC 9.9.4.1.(1)"
    severity: "high"

  - id: "GUARD_001"
    name: "Guard Height"
    category: "egress"
    input: "guards[*].height_mm"
    condition: "value >= profiles.residential.guard_min_height_mm"
    code_ref: "NBC 9.8.8.1.(1)"
    severity: "high"

  - id: "HANDRAIL_001"
    name: "Handrail Height Range"
    category: "egress"
    input: "handrails[*].height_mm"
    condition: "value >= profiles.residential.handrail_min_mm AND value <= profiles.residential.handrail_max_mm"
    code_ref: "NBC 9.8.7.4.(1)"
    severity: "medium"
```

**Rule Engine Class**:
```python
class RuleEngine:
    def __init__(self, ruleset_path: str):
        self.rules = load_yaml(ruleset_path)

    def evaluate(self, drawing_facts: DrawingFacts) -> List[ComplianceResult]:
        results = []
        for rule in self.rules["checks"]:
            result = self._evaluate_rule(rule, drawing_facts)
            results.append(result)
        return results

    def _evaluate_rule(self, rule, facts) -> ComplianceResult:
        # Extract value from facts using input path
        # Evaluate condition
        # Return PASS, FAIL, or UNKNOWN with evidence
```

---

### 4.3 Report Generator

**Priority**: MEDIUM
**Estimated Effort**: 4-6 hours

**Required Output Format**:
```python
@dataclass
class ComplianceReport:
    project_id: str
    generated_at: datetime
    drawing_info: DrawingInfo

    summary: ReportSummary
    checks_by_category: Dict[str, List[CheckResult]]
    missing_information: List[str]
    recommendations: List[str]

@dataclass
class ReportSummary:
    total_checks: int
    passed: int
    failed: int
    unknown: int
    needs_review: int

@dataclass
class CheckResult:
    check_id: str
    check_name: str
    status: str  # PASS, FAIL, UNKNOWN

    # Evidence
    sheet_number: int
    element_id: str  # Door mark, room name, etc.
    extracted_value: str
    required_value: str

    # Location
    bbox: Tuple[float, float, float, float]
    evidence_crop: Optional[bytes]  # PNG image crop

    # Code reference
    code_ref: str
    code_text_pointer: str  # Link to code article in DB
```

**Report Formats**:
- JSON (API response)
- PDF (printable report with evidence crops)
- HTML (web display)

---

### 4.4 API Endpoint Integration

**Priority**: HIGH
**Estimated Effort**: 3-4 hours

**Current State**: `api/review.py` has document upload, but extraction pipeline not wired.

**Required Endpoints**:
```python
# Analyze uploaded drawing
POST /api/v1/projects/{project_id}/analyze
Request: { document_ids: [1, 2, 3] }
Response: { job_id: "abc123", status: "processing" }

# Get analysis results
GET /api/v1/projects/{project_id}/compliance
Response: ComplianceReport

# Get specific check details
GET /api/v1/projects/{project_id}/compliance/checks/{check_id}
Response: CheckResult with full evidence

# Re-run specific checks
POST /api/v1/projects/{project_id}/compliance/recheck
Request: { check_ids: ["EGRESS_001", "GUARD_001"] }

# Manual verification
PATCH /api/v1/projects/{project_id}/compliance/checks/{check_id}
Request: { is_verified: true, verified_notes: "Confirmed on site" }
```

---

### 4.5 Fire Safety Analysis

**Priority**: MEDIUM (Phase 2)
**Estimated Effort**: 8-12 hours

**Not Currently Built**:
- Fire separation detection
- Rated wall/door consistency checking
- Egress path analysis
- Occupant load calculations
- Travel distance calculations

**Would Require**:
- Fire rating extraction from schedules and notes
- Spatial path analysis for egress routes
- Occupant load tables from NBC

---

## 5. Recommended Implementation Plan

### Phase 1: Core Compliance MVP (1-2 weeks)

| Task | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| Schedule Table Parser | HIGH | 4-6h | None |
| YAML Rule Engine (5 rules) | HIGH | 6-8h | Schedule Parser |
| API Integration | HIGH | 3-4h | Rule Engine |
| Simple Report Generator | MEDIUM | 4-6h | API Integration |

**Deliverable**: Working system that can:
1. Accept a floor plan PDF
2. Extract door schedule
3. Run 5 compliance checks
4. Return Pass/Fail/Unknown with evidence

### Phase 2: Enhanced Extraction (2-3 weeks)

| Task | Priority | Effort |
|------|----------|--------|
| Window schedule parser | MEDIUM | 3-4h |
| Stair schedule parser | MEDIUM | 3-4h |
| General notes extraction | MEDIUM | 4-6h |
| Code summary sheet parser | MEDIUM | 4-6h |
| Expand to 20+ rules | HIGH | 8-12h |

### Phase 3: Advanced Analysis (4-6 weeks)

| Task | Priority | Effort |
|------|----------|--------|
| Fire rating consistency | MEDIUM | 8-12h |
| Egress path analysis | LOW | 12-16h |
| Occupant load calculations | LOW | 8-12h |
| PDF report generation | MEDIUM | 6-8h |

---

## 6. Technical Specifications

### Input Requirements

**Supported Drawing Types**:
- Floor plans (primary)
- Site plans
- Elevations
- Sections
- Schedules (door, window, stair)

**Supported File Formats**:
- PDF (vector or scanned)
- PNG, JPG, TIFF (scanned drawings)
- DWG, DXF (future: with conversion)

**Optimal Input**:
- Vector PDF from CAD/Revit export (fastest, most accurate)
- 300 DPI scanned drawings (if OCR needed)

### Processing Requirements

| Component | CPU | Memory | Notes |
|-----------|-----|--------|-------|
| PDF Extraction | Low | 500MB | PyMuPDF is fast |
| EasyOCR | Medium | 2GB | GPU optional |
| Geometry Analysis | Low | 500MB | Shapely is efficient |
| Rule Engine | Low | 100MB | YAML parsing |
| GOT-OCR2 (Oracle) | High | 3GB | ~3 min/page |

### Output Specifications

**Compliance Status Values**:
| Status | Meaning |
|--------|---------|
| PASS | Extracted value meets code requirement |
| FAIL | Extracted value does not meet code requirement |
| UNKNOWN | Cannot determine (missing input or not derivable) |
| NEEDS_REVIEW | Flagged for manual verification |

**Evidence Requirements**:
- Sheet number and drawing title
- Element identifier (door mark, room name)
- Bounding box coordinates
- Extracted text snippet
- Cropped image region (optional)

---

## 7. Limitations & Scope

### What This System CAN Do

✅ Extract dimensions and room sizes from vector PDFs
✅ Parse door/window schedules (with schedule parser)
✅ Check dimensional compliance (widths, heights, areas)
✅ Verify presence of required elements (guards, handrails)
✅ Flag missing information
✅ Provide code clause references
✅ Generate pre-screening reports

### What This System CANNOT Do

❌ **Prove full code compliance** - Only a licensed professional can certify
❌ **Calculate structural adequacy** - Requires engineering analysis
❌ **Verify fire ratings** - Requires assembly testing/listings
❌ **Calculate travel distances** - Requires path geometry (complex)
❌ **Determine occupant loads** - Requires use assumptions
❌ **Evaluate alternatives/exceptions** - Requires professional judgment

### Recommended Positioning

> "This tool performs automated pre-screening of architectural drawings against NBC 2023 Alberta Edition requirements. It identifies likely violations and missing compliance information. Results should be verified by a qualified professional before submission."

---

## 8. File Reference

### Existing Code (Production Ready)

| File | Lines | Description |
|------|-------|-------------|
| `services/drawing_extraction/pdf_extractor.py` | 787 | Vector/text extraction |
| `services/drawing_extraction/ocr_processor.py` | 694 | OCR and dimension parsing |
| `services/drawing_extraction/geometry_analyzer.py` | 781 | Geometry and room analysis |
| `models/projects.py` | 250+ | Compliance check models |
| `services/document_service.py` | 150+ | File upload handling |

### To Be Created

| File | Description |
|------|-------------|
| `services/drawing_extraction/schedule_extractor.py` | Door/window/stair schedule parsing |
| `services/compliance/rule_engine.py` | YAML-driven rule evaluation |
| `services/compliance/report_generator.py` | Compliance report generation |
| `rules/nbc_2023_ae_part9.yaml` | Part 9 compliance rules |
| `rules/nbc_2023_ae_part3.yaml` | Part 3 compliance rules |
| `api/compliance.py` | Compliance check API endpoints |

---

## 9. References

### NBC 2023 Alberta Edition Key Sections

| Section | Topic | Common Checks |
|---------|-------|---------------|
| 9.5 | Design Loads | Snow, wind, seismic values |
| 9.8 | Stairs, Ramps, Handrails | Width, rise, run, guard height |
| 9.9 | Means of Egress | Exit doors, corridors, travel distance |
| 9.10 | Fire Protection | Separations, ratings, smoke alarms |
| 9.32 | Ventilation | Bathroom/kitchen exhaust |
| 9.36 | Energy Efficiency | Insulation, windows |

### External Resources

- [NBC 2023 Alberta Edition](https://www.alberta.ca/national-building-code-alberta-edition)
- [NECB 2020](https://nrc.canada.ca/en/certifications-evaluations-standards/codes-canada/codes-canada-publications/national-energy-code-canada-buildings-2020)
- [Calgary Land Use Bylaw](https://www.calgary.ca/planning/land-use/land-use-bylaw-1p2007.html)

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-12 | Claude + User | Initial documentation |
| 2026-01-12 | Claude | Added deep codebase analysis findings |
| 2026-01-12 | Claude | Corrected "what's built" based on actual code |

---

*Document Version: 1.0*
*Last Updated: 2026-01-12*
