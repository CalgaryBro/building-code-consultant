# VLM-Free Drawing Extraction Pipeline

## Overview

This document outlines a **Vision Language Model (VLM)-free** approach for extracting and analyzing building drawings for permit compliance checking. Based on research documented in `drawing_extraction_libraries.md`, we can achieve reliable extraction using traditional CV/OCR methods.

## Architecture

```
PDF Drawing Input
       |
       v
+----------------+
|   PyMuPDF      | --> Extract vector graphics (lines, paths, shapes)
|                | --> Extract embedded text with positions
|                | --> Render pages to images for CV processing
+----------------+
       |
       v
+----------------+
|   OpenCV       | --> Edge detection (Canny)
|                | --> Line detection (Hough Transform)
|                | --> Contour detection for shapes
|                | --> Image preprocessing
+----------------+
       |
       v
+----------------+
|   EasyOCR      | --> Text recognition with positions
|                | --> Handles rotated text (90, 180, 270)
|                | --> Character allowlist for dimensions
+----------------+
       |
       v
+----------------+
|   YOLO/Custom  | --> Symbol detection (doors, windows, stairs)
|  (Optional)    | --> Fixture detection (plumbing, electrical)
|                | --> Annotation detection
+----------------+
       |
       v
+----------------+
|   Shapely      | --> Room polygon creation
|                | --> Area calculations
|                | --> Spatial queries (contains, intersects)
|                | --> Setback analysis (buffer operations)
+----------------+
       |
       v
+----------------+
|   NetworkX     | --> Room connectivity graph
|                | --> Egress path analysis
|                | --> Circulation analysis
+----------------+
       |
       v
+----------------+
|   pandas       | --> Schedule parsing (door, window, room)
|                | --> Data aggregation
|                | --> Code requirement comparison
+----------------+
       |
       v
+----------------+
| Rule-Based     | --> Compare extracted data vs NBC requirements
| Compliance     | --> Generate compliance report
| Checker        | --> Flag non-compliant items
+----------------+
```

## Implementation Modules

### 1. PDF Extraction Module (`drawing_extractor.py`)

```python
import pymupdf
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple

@dataclass
class VectorElement:
    type: str  # 'line', 'rect', 'curve'
    coords: List[Tuple[float, float]]
    width: float
    color: Tuple[float, ...]

@dataclass
class TextElement:
    text: str
    bbox: Tuple[float, float, float, float]
    font: str
    size: float

class PDFDrawingExtractor:
    def __init__(self, pdf_path: str):
        self.doc = pymupdf.open(pdf_path)

    def extract_vectors(self, page_num: int = 0) -> List[VectorElement]:
        """Extract all vector graphics from a page."""
        page = self.doc[page_num]
        drawings = page.get_drawings()
        vectors = []

        for path in drawings:
            for item in path['items']:
                if item[0] == 'l':  # line
                    vectors.append(VectorElement(
                        type='line',
                        coords=[tuple(item[1]), tuple(item[2])],
                        width=path.get('width', 1),
                        color=path.get('color', (0, 0, 0))
                    ))
                elif item[0] == 're':  # rectangle
                    rect = item[1]
                    vectors.append(VectorElement(
                        type='rect',
                        coords=[(rect.x0, rect.y0), (rect.x1, rect.y1)],
                        width=path.get('width', 1),
                        color=path.get('color', (0, 0, 0))
                    ))
        return vectors

    def extract_text(self, page_num: int = 0) -> List[TextElement]:
        """Extract embedded text with positions."""
        page = self.doc[page_num]
        text_dict = page.get_text("dict")
        texts = []

        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        texts.append(TextElement(
                            text=span['text'],
                            bbox=tuple(span['bbox']),
                            font=span.get('font', ''),
                            size=span.get('size', 0)
                        ))
        return texts

    def render_to_image(self, page_num: int = 0, dpi: int = 200) -> np.ndarray:
        """Render page to numpy array for CV processing."""
        page = self.doc[page_num]
        pix = page.get_pixmap(dpi=dpi)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )
        return img

    def close(self):
        self.doc.close()
```

### 2. OCR Module (`drawing_ocr.py`)

```python
import easyocr
import cv2
import numpy as np
import re
from typing import List, Dict, Optional

class DrawingOCR:
    def __init__(self, gpu: bool = False):
        self.reader = easyocr.Reader(['en'], gpu=gpu)

        # Patterns for dimension extraction
        self.dimension_pattern = re.compile(
            r"(\d+(?:\.\d+)?)\s*(mm|m|cm|ft|in|'|\"|\"|′|″)?",
            re.IGNORECASE
        )

    def extract_text(self, image: np.ndarray,
                     rotation_info: List[int] = None) -> List[Dict]:
        """Extract text from image with positions."""
        if rotation_info is None:
            rotation_info = [0, 90, 180, 270]

        results = self.reader.readtext(
            image,
            rotation_info=rotation_info,
            paragraph=False
        )

        extracted = []
        for bbox, text, confidence in results:
            if confidence > 0.3:  # Low threshold to catch dimensions
                extracted.append({
                    'text': text,
                    'bbox': bbox,
                    'confidence': confidence,
                    'is_dimension': self._is_dimension(text)
                })
        return extracted

    def _is_dimension(self, text: str) -> bool:
        """Check if text looks like a dimension."""
        return bool(self.dimension_pattern.search(text))

    def parse_dimension(self, text: str) -> Optional[Dict]:
        """Parse a dimension string into value and unit."""
        match = self.dimension_pattern.search(text)
        if match:
            value = float(match.group(1))
            unit = match.group(2) or 'mm'  # default to mm

            # Normalize units
            unit_map = {
                "'": 'ft', '"': 'in', "′": 'ft', "″": 'in',
                'ft': 'ft', 'in': 'in', 'm': 'm',
                'mm': 'mm', 'cm': 'cm'
            }
            unit = unit_map.get(unit.lower(), unit)

            return {'value': value, 'unit': unit}
        return None
```

### 3. Geometry Analysis Module (`geometry_analyzer.py`)

```python
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
import networkx as nx
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Room:
    name: str
    polygon: Polygon
    area: float  # in m²
    doors: List[Point]
    windows: List[Point]

class GeometryAnalyzer:
    def __init__(self, scale_factor: float = 1.0):
        """
        Initialize with scale factor to convert drawing units to meters.
        e.g., if drawing is in mm, scale_factor = 0.001
        """
        self.scale_factor = scale_factor
        self.rooms: List[Room] = []
        self.connectivity_graph = nx.Graph()

    def create_room_from_vectors(self, vectors: List[Tuple]) -> Optional[Polygon]:
        """Create a room polygon from a list of line vectors."""
        if len(vectors) < 3:
            return None

        # Extract coordinates from connected lines
        coords = []
        for v in vectors:
            coords.extend(v)

        # Remove duplicates while preserving order
        seen = set()
        unique_coords = []
        for c in coords:
            if c not in seen:
                seen.add(c)
                unique_coords.append(c)

        if len(unique_coords) >= 3:
            try:
                poly = Polygon(unique_coords)
                if poly.is_valid:
                    return poly
            except:
                pass
        return None

    def calculate_area(self, polygon: Polygon) -> float:
        """Calculate area in square meters."""
        return polygon.area * (self.scale_factor ** 2)

    def check_minimum_room_size(self, room: Room, min_area: float = 9.29) -> bool:
        """
        Check if room meets minimum area requirement.
        Default 9.29 m² is NBC minimum for bedrooms.
        """
        return room.area >= min_area

    def analyze_setbacks(self, building: Polygon,
                         front_setback: float,
                         side_setback: float,
                         rear_setback: float,
                         lot: Polygon) -> Dict:
        """Analyze if building meets setback requirements."""
        # Create setback zones
        front_zone = lot.buffer(-front_setback * self.scale_factor)
        # Simplified - in reality need to identify sides

        violations = []
        if not front_zone.contains(building):
            violations.append('front_setback')

        return {
            'compliant': len(violations) == 0,
            'violations': violations
        }

    def build_connectivity_graph(self, rooms: List[Room]):
        """Build a graph of room connections (through doors)."""
        self.connectivity_graph.clear()

        for room in rooms:
            self.connectivity_graph.add_node(
                room.name,
                area=room.area,
                polygon=room.polygon
            )

        # Find connections through doors
        for i, room1 in enumerate(rooms):
            for room2 in rooms[i+1:]:
                # Check if rooms share a wall and have a door
                if room1.polygon.touches(room2.polygon):
                    for door in room1.doors:
                        if room2.polygon.distance(door) < 0.1:
                            self.connectivity_graph.add_edge(
                                room1.name,
                                room2.name,
                                type='door'
                            )

    def check_egress(self, start_room: str, exit_rooms: List[str]) -> Dict:
        """Check if there's a valid egress path from start to any exit."""
        if not self.connectivity_graph.has_node(start_room):
            return {'has_egress': False, 'reason': 'room_not_found'}

        for exit_room in exit_rooms:
            if self.connectivity_graph.has_node(exit_room):
                try:
                    path = nx.shortest_path(
                        self.connectivity_graph,
                        start_room,
                        exit_room
                    )
                    return {
                        'has_egress': True,
                        'path': path,
                        'path_length': len(path) - 1
                    }
                except nx.NetworkXNoPath:
                    continue

        return {'has_egress': False, 'reason': 'no_path_to_exit'}
```

### 4. Compliance Checker Module (`compliance_checker.py`)

```python
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import json

class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    NEEDS_REVIEW = "needs_review"
    INSUFFICIENT_DATA = "insufficient_data"

@dataclass
class ComplianceResult:
    requirement_id: str
    article_number: str
    element: str
    status: ComplianceStatus
    extracted_value: Optional[float]
    required_value: Optional[float]
    unit: str
    message: str

class NBCComplianceChecker:
    def __init__(self, requirements_db_path: str = None):
        """
        Initialize with path to requirements database.
        Can load from JSON or connect to SQLite.
        """
        self.requirements = {}
        if requirements_db_path:
            self.load_requirements(requirements_db_path)

    def load_requirements(self, path: str):
        """Load requirements from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
            for article in data.get('articles', []):
                for req in article.get('requirements', []):
                    self.requirements[req['id']] = {
                        'article': article['article_number'],
                        **req
                    }

    def check_dimensional_requirement(
        self,
        extracted_value: float,
        extracted_unit: str,
        requirement_id: str
    ) -> ComplianceResult:
        """Check a dimensional value against a requirement."""
        req = self.requirements.get(requirement_id)
        if not req:
            return ComplianceResult(
                requirement_id=requirement_id,
                article_number='',
                element='',
                status=ComplianceStatus.INSUFFICIENT_DATA,
                extracted_value=extracted_value,
                required_value=None,
                unit=extracted_unit,
                message=f"Requirement {requirement_id} not found"
            )

        # Convert units if needed
        converted_value = self._convert_units(
            extracted_value,
            extracted_unit,
            req.get('unit', 'mm')
        )

        min_val = req.get('min_value')
        max_val = req.get('max_value')

        status = ComplianceStatus.COMPLIANT
        message = "Meets requirement"

        if min_val and converted_value < float(min_val):
            status = ComplianceStatus.NON_COMPLIANT
            message = f"Value {converted_value} below minimum {min_val}"
        elif max_val and converted_value > float(max_val):
            status = ComplianceStatus.NON_COMPLIANT
            message = f"Value {converted_value} exceeds maximum {max_val}"

        return ComplianceResult(
            requirement_id=requirement_id,
            article_number=req['article'],
            element=req.get('element', ''),
            status=status,
            extracted_value=converted_value,
            required_value=min_val or max_val,
            unit=req.get('unit', 'mm'),
            message=message
        )

    def _convert_units(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert between common building units."""
        # Convert everything to mm first
        to_mm = {
            'mm': 1, 'm': 1000, 'cm': 10,
            'ft': 304.8, 'in': 25.4,
            "'": 304.8, '"': 25.4
        }

        mm_value = value * to_mm.get(from_unit.lower(), 1)

        # Convert from mm to target
        from_mm = {k: 1/v for k, v in to_mm.items()}
        return mm_value * from_mm.get(to_unit.lower(), 1)

    def check_stair_requirements(self, extracted_data: Dict) -> List[ComplianceResult]:
        """Check all stair-related requirements."""
        results = []

        # Check stair width (NBC 9.8.4.1)
        if 'stair_width' in extracted_data:
            results.append(self.check_dimensional_requirement(
                extracted_data['stair_width'],
                extracted_data.get('stair_width_unit', 'mm'),
                '9.8.4.1-1'  # stair_width requirement ID
            ))

        # Check riser height (NBC 9.8.4.5)
        if 'riser_height' in extracted_data:
            results.append(self.check_dimensional_requirement(
                extracted_data['riser_height'],
                extracted_data.get('riser_height_unit', 'mm'),
                '9.8.4.5-1'
            ))

        # Check tread depth (NBC 9.8.4.5)
        if 'tread_depth' in extracted_data:
            results.append(self.check_dimensional_requirement(
                extracted_data['tread_depth'],
                extracted_data.get('tread_depth_unit', 'mm'),
                '9.8.4.5-2'
            ))

        return results
```

## Installation

```bash
# Core extraction stack
pip install PyMuPDF pdfplumber opencv-python easyocr

# Geometry and analysis
pip install shapely networkx pandas numpy

# Optional: Deep learning for symbol detection
pip install ultralytics torch torchvision
```

## Usage Example

```python
from drawing_extractor import PDFDrawingExtractor
from drawing_ocr import DrawingOCR
from geometry_analyzer import GeometryAnalyzer
from compliance_checker import NBCComplianceChecker

# Initialize components
extractor = PDFDrawingExtractor("floor_plan.pdf")
ocr = DrawingOCR(gpu=False)
analyzer = GeometryAnalyzer(scale_factor=0.001)  # mm to m
checker = NBCComplianceChecker("requirements.json")

# Extract data
vectors = extractor.extract_vectors(page_num=0)
embedded_text = extractor.extract_text(page_num=0)
image = extractor.render_to_image(page_num=0, dpi=200)
ocr_text = ocr.extract_text(image)

# Find dimensions
dimensions = [t for t in ocr_text if t['is_dimension']]
for dim in dimensions:
    parsed = ocr.parse_dimension(dim['text'])
    print(f"Found dimension: {parsed}")

# Check compliance
extracted = {
    'stair_width': 900,
    'stair_width_unit': 'mm',
    'riser_height': 180,
    'riser_height_unit': 'mm'
}

results = checker.check_stair_requirements(extracted)
for r in results:
    print(f"{r.element}: {r.status.value} - {r.message}")

extractor.close()
```

## Advantages over VLM Approach

| Aspect | VLM-Free | VLM |
|--------|----------|-----|
| Speed | Fast (ms-seconds) | Slow (seconds-minutes) |
| Cost | Free/cheap | API costs |
| Offline | Yes | Requires internet |
| Scalability | Excellent | Limited |
| Deterministic | Yes | Variable |
| Explainable | Fully | Black box |

## When to Consider VLMs

VLMs may still be useful for:
1. Initial data annotation for training symbol detection models
2. Edge cases requiring human-like reasoning
3. Natural language explanations of compliance issues
4. Understanding non-standard drawings

However, for production permit review, the VLM-free approach provides:
- Faster processing
- Lower costs
- More consistent results
- Full auditability

---

*Document created January 2026 for Building Code Expert System*
