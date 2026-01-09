# Python Libraries for Reading Architectural/Engineering Drawings

## Research Report for Building Permit Review Automation

**Date:** January 2025
**Purpose:** Extract geometry, text, and classify symbols from building drawings

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [CAD File Libraries (DWG/DXF)](#cad-file-libraries-dwgdxf)
3. [PDF Vector Extraction Libraries](#pdf-vector-extraction-libraries)
4. [OCR and Computer Vision Libraries](#ocr-and-computer-vision-libraries)
5. [Deep Learning Object Detection](#deep-learning-object-detection)
6. [Semantic Interpretation Tools](#semantic-interpretation-tools)
7. [Vision Language Models (VLM) vs Traditional Approaches](#vision-language-models-vlm-vs-traditional-approaches)
8. [Recommended Stack for PDF Building Drawings](#recommended-stack-for-pdf-building-drawings)
9. [Open Source Floor Plan Recognition Projects](#open-source-floor-plan-recognition-projects)
10. [References](#references)

---

## Executive Summary

This report evaluates Python libraries for extracting and interpreting architectural/engineering drawings for building permit review automation. The primary use case is PDF building drawings, which may be either vector-based (CAD exports) or scanned images.

**Key Findings:**
- **Vector PDFs**: PyMuPDF offers the best balance of speed, features, and vector graphics extraction
- **Scanned PDFs**: A hybrid approach combining EasyOCR + OpenCV + VLM provides best results
- **Symbol Detection**: Custom-trained YOLO or Detectron2 models are required for architectural symbols
- **VLMs**: GPT-4V, Claude 3.5, and Gemini 2.5 Pro show strong potential for layout understanding but are slower and more expensive
- **Recommended Hybrid Approach**: Use traditional CV/OCR for speed, VLMs for semantic interpretation

---

## CAD File Libraries (DWG/DXF)

### 1. ezdxf

**Purpose:** Read, modify, and create DXF files (AutoCAD Drawing Exchange Format)

| Attribute | Details |
|-----------|---------|
| **Latest Version** | 1.4.3 (October 2025) |
| **License** | MIT |
| **Python Support** | 3.10, 3.11, 3.12, 3.13, 3.14 |
| **Installation** | `pip install ezdxf` |

**Pros for Building Drawings:**
- Excellent DXF format support (R12 through R2018)
- Read entities, layers, blocks, dimensions, polylines
- Preserves unknown DXF tags from third-party applications
- Drawing add-on for visualization (PNG, PDF, SVG output)
- Active development and good documentation
- Command-line tools for inspection and conversion

**Cons for Building Drawings:**
- DXF only (not DWG directly)
- Not a CAD kernel - no high-level construction features
- Requires ODA File Converter for DWG files

**DWG Support via ODA File Converter:**
```python
from ezdxf.addons import odafc

# Load a DWG file (requires ODA File Converter installed)
doc = odafc.readfile('building_plan.dwg')

# Export as DWG for specific AutoCAD version
odafc.export_dwg(doc, 'output_R2018.dwg', version='R2018')
```

**Basic Usage Example:**
```python
import ezdxf

# Load DXF file
doc = ezdxf.readfile("floor_plan.dxf")
msp = doc.modelspace()

# Iterate through all entities
for entity in msp:
    print(f"Type: {entity.dxftype()}")
    if entity.dxftype() == 'LINE':
        print(f"  Start: {entity.dxf.start}")
        print(f"  End: {entity.dxf.end}")
    elif entity.dxftype() == 'TEXT':
        print(f"  Text: {entity.dxf.text}")
        print(f"  Position: {entity.dxf.insert}")

# Access by layer
for entity in msp.query('*[layer=="WALLS"]'):
    print(entity.dxftype())

# Access blocks (symbols)
for block in doc.blocks:
    print(f"Block: {block.name}")
```

**Documentation:** https://ezdxf.readthedocs.io/

---

### 2. pythonOCC (pythonocc-core)

**Purpose:** Full OpenCASCADE 3D geometry kernel bindings for CAD/BIM/CAM

| Attribute | Details |
|-----------|---------|
| **Latest Version** | 7.9.0 (April 2025) |
| **License** | LGPL |
| **Python Support** | 3.9, 3.10, 3.11, 3.12 |
| **Installation** | `conda install -c conda-forge pythonocc-core=7.9.0` |

**Pros for Building Drawings:**
- Full access to ~1000 OpenCASCADE C++ classes
- Supports IGES, STEP, STL, PLY, OBJ, GLTF formats
- 3D visualization (tkinter, PyQt, PySide, web browsers, Jupyter)
- Industrial-grade geometry processing
- 400+ scientific citations

**Cons for Building Drawings:**
- Heavy dependency (OpenCASCADE)
- Conda installation required (no pip)
- Steep learning curve
- Overkill for 2D floor plan extraction
- Primarily for 3D CAD, not 2D drawings

**When to Use:**
- 3D BIM model processing
- Complex geometry operations (boolean, offsetting)
- IFC file processing (with IfcOpenShell)
- When precision geometry is required

**Documentation:** https://github.com/tpaviot/pythonocc-core

---

### 3. LibreDWG

**Purpose:** Free C library for reading/writing DWG files with Python bindings

| Attribute | Details |
|-----------|---------|
| **Latest Version** | 0.13.3 |
| **License** | GPLv3+ |
| **DWG Support** | r1.2 through r2018 (~99% coverage) |
| **Installation** | Build from source with SWIG |

**Pros for Building Drawings:**
- Direct DWG reading (no conversion needed)
- Best free DWG support available
- Supports all major DWG versions
- GNU Project - well maintained

**Cons for Building Drawings:**
- GPLv3 license (viral copyleft)
- Requires building from source
- Python bindings via SWIG (less Pythonic)
- Documentation primarily for C API
- Some entity types still under development

**Note:** For most projects, using ezdxf + ODA File Converter is easier than LibreDWG.

**Resources:**
- https://github.com/LibreDWG/libredwg
- https://www.gnu.org/software/libredwg/

---

### 4. ODA File Converter

**Purpose:** Convert between DWG, DXF, and DXB formats

| Attribute | Details |
|-----------|---------|
| **Provider** | Open Design Alliance |
| **License** | Free for personal use |
| **Platforms** | Windows, Linux, macOS |
| **Python Integration** | Via ezdxf.addons.odafc or subprocess |

**Best Practice:** Use ODA File Converter to convert DWG to DXF, then process with ezdxf.

**Download:** https://www.opendesign.com/guestfiles/oda_file_converter

---

## PDF Vector Extraction Libraries

### 1. PyMuPDF (fitz)

**Purpose:** High-performance PDF data extraction, analysis, and manipulation

| Attribute | Details |
|-----------|---------|
| **Latest Version** | 1.26.7 (December 2025) |
| **License** | AGPL / Commercial |
| **Python Support** | >= 3.10 |
| **Installation** | `pip install PyMuPDF` |

**Pros for Building Drawings:**
- **Excellent vector graphics extraction** via `page.get_drawings()`
- Fast performance (one of the fastest PDF libraries)
- Extracts text with position information
- Renders pages to images for CV processing
- Creates vector graphics on PDF pages
- Active development by Artifex

**Cons for Building Drawings:**
- AGPL license (copyleft) or commercial license required
- Vector extraction returns paths, not semantic objects
- Complex drawings may have thousands of path elements

**Vector Graphics Extraction:**
```python
import pymupdf  # or: import fitz

doc = pymupdf.open("floor_plan.pdf")
page = doc[0]

# Extract all vector drawings (line art)
drawings = page.get_drawings()

for path in drawings:
    print(f"Path items: {len(path['items'])}")
    print(f"Fill color: {path['fill']}")
    print(f"Stroke color: {path['color']}")
    print(f"Line width: {path['width']}")

    for item in path['items']:
        if item[0] == 'l':  # line
            start, end = item[1], item[2]
            print(f"  Line: {start} -> {end}")
        elif item[0] == 're':  # rectangle
            rect = item[1]
            print(f"  Rectangle: {rect}")
        elif item[0] == 'c':  # cubic bezier
            print(f"  Curve: {item[1:]}")

# Extract text with positions
text_dict = page.get_text("dict")
for block in text_dict["blocks"]:
    if block["type"] == 0:  # text block
        for line in block["lines"]:
            for span in line["spans"]:
                print(f"Text: '{span['text']}' at {span['bbox']}")
```

**Render to Image for CV:**
```python
# Render page to image at 300 DPI
pix = page.get_pixmap(dpi=300)
pix.save("page_image.png")

# Convert to numpy array for OpenCV
import numpy as np
img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
    pix.height, pix.width, pix.n
)
```

**Documentation:** https://pymupdf.readthedocs.io/

---

### 2. pdfplumber

**Purpose:** Extract text, tables, and detailed object information from PDFs

| Attribute | Details |
|-----------|---------|
| **Latest Version** | Current (2025) |
| **License** | MIT |
| **Python Support** | 3.8+ |
| **Installation** | `pip install pdfplumber` |

**Pros for Building Drawings:**
- Excellent table extraction
- Access to chars, lines, rectangles, curves
- Visual debugging tools
- Region-based extraction (crop areas)
- MIT license (permissive)

**Cons for Building Drawings:**
- Slower than PyMuPDF
- Works best on machine-generated PDFs (not scanned)
- Table detection may struggle with complex drawing layouts
- Less capable for pure vector graphics extraction

**Usage Example:**
```python
import pdfplumber

with pdfplumber.open("floor_plan.pdf") as pdf:
    page = pdf.pages[0]

    # Extract all objects
    chars = page.chars  # text characters with positions
    lines = page.lines  # line segments
    rects = page.rects  # rectangles
    curves = page.curves  # bezier curves

    # Extract lines (walls, etc.)
    for line in lines:
        print(f"Line: ({line['x0']}, {line['top']}) -> ({line['x1']}, {line['bottom']})")
        print(f"  Width: {line['linewidth']}, Color: {line.get('stroking_color')}")

    # Region-based extraction
    title_block = page.crop((0, 0, 200, 100))  # x0, top, x1, bottom
    title_text = title_block.extract_text()

    # Visual debugging
    im = page.to_image(resolution=150)
    im.draw_lines(lines)
    im.save("debug_lines.png")
```

**Documentation:** https://github.com/jsvine/pdfplumber

---

### 3. pikepdf

**Purpose:** Low-level PDF manipulation powered by QPDF

| Attribute | Details |
|-----------|---------|
| **Latest Version** | 10.2.0 (December 2025) |
| **License** | MPL-2.0 |
| **Python Support** | >= 3.10 |
| **Installation** | `pip install pikepdf` |

**Pros for Building Drawings:**
- Low-level access to PDF internals
- Repair damaged PDFs
- Merge/split operations
- Metadata editing
- Password-protected PDF support

**Cons for Building Drawings:**
- Requires knowledge of PDF specification
- No built-in text extraction (use with PyMuPDF)
- Cannot render PDFs to images
- Not designed for content extraction

**Best Use Case:** Pre-processing PDFs before extraction (repair, decrypt, merge).

**Documentation:** https://pikepdf.readthedocs.io/

---

## OCR and Computer Vision Libraries

### 1. OpenCV (cv2)

**Purpose:** Computer vision operations for image processing

| Attribute | Details |
|-----------|---------|
| **Latest Version** | 4.x (2025) |
| **License** | Apache 2.0 |
| **Installation** | `pip install opencv-python` |

**Pros for Building Drawings:**
- Industry standard for image processing
- Hough Line Transform for line detection
- Contour detection for shapes
- Template matching for symbols
- Image preprocessing (threshold, denoise, morphology)

**Cons for Building Drawings:**
- No semantic understanding
- Requires significant parameter tuning
- Symbol detection requires templates or ML

**Line Detection Example:**
```python
import cv2
import numpy as np

# Load image
img = cv2.imread('floor_plan.png')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Edge detection
edges = cv2.Canny(gray, 50, 150, apertureSize=3)

# Probabilistic Hough Line Transform
lines = cv2.HoughLinesP(
    edges,
    rho=1,
    theta=np.pi/180,
    threshold=100,
    minLineLength=50,
    maxLineGap=10
)

# Draw detected lines
for line in lines:
    x1, y1, x2, y2 = line[0]
    cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

# Contour detection for rooms
contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
```

**Documentation:** https://docs.opencv.org/

---

### 2. pytesseract

**Purpose:** Python wrapper for Google's Tesseract OCR engine

| Attribute | Details |
|-----------|---------|
| **License** | Apache 2.0 |
| **Installation** | `pip install pytesseract` + Tesseract binary |

**Pros for Building Drawings:**
- Free and open source
- Good for printed text
- Multiple language support
- Position information available

**Cons for Building Drawings:**
- ~80% accuracy on real-world documents
- Struggles with engineering drawing fonts
- Poor on rotated text without preprocessing
- Requires good image preprocessing

**Usage Example:**
```python
import pytesseract
from PIL import Image
import cv2

# Preprocess image
img = cv2.imread('drawing.png')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

# Extract text with bounding boxes
data = pytesseract.image_to_data(thresh, output_type=pytesseract.Output.DICT)

for i, text in enumerate(data['text']):
    if text.strip():
        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
        conf = data['conf'][i]
        print(f"Text: '{text}' at ({x}, {y}) confidence: {conf}%")
```

---

### 3. EasyOCR

**Purpose:** Ready-to-use OCR with deep learning backend

| Attribute | Details |
|-----------|---------|
| **License** | Apache 2.0 |
| **Languages** | 80+ supported |
| **Installation** | `pip install easyocr` |

**Pros for Building Drawings:**
- Better accuracy than Tesseract on complex layouts
- Handles rotated text (rotation_info parameter)
- GPU acceleration support
- Scene text recognition capability
- Character allowlist for specific use cases

**Cons for Building Drawings:**
- Slower than Tesseract
- Larger model download
- May require GPU for production use

**Usage Example:**
```python
import easyocr

# Initialize reader (downloads models on first run)
reader = easyocr.Reader(['en'], gpu=True)

# Detect and recognize text
results = reader.readtext(
    'floor_plan.png',
    rotation_info=[90, 180, 270],  # Try rotations
    paragraph=False
)

for bbox, text, confidence in results:
    if confidence > 0.5:  # Filter low confidence
        print(f"Text: '{text}' confidence: {confidence:.2f}")
        print(f"  Bounding box: {bbox}")
```

**Documentation:** https://github.com/JaidedAI/EasyOCR

---

### 4. LayoutParser

**Purpose:** Deep learning-based document layout analysis

| Attribute | Details |
|-----------|---------|
| **License** | Apache 2.0 |
| **Installation** | `pip install layoutparser` |

**Pros for Building Drawings:**
- Pre-trained models for document layout detection
- Detectron2 backend
- OCR integration (Tesseract, Google Cloud Vision)
- Visual debugging tools

**Cons for Building Drawings:**
- Pre-trained models are for documents, not drawings
- Would require custom training for architectural symbols
- Heavy dependencies (Detectron2)

**Note:** For architectural drawings, you would need to train custom models on annotated drawing datasets.

**Documentation:** https://layout-parser.github.io/

---

## Deep Learning Object Detection

### 1. YOLO (Ultralytics)

**Purpose:** Real-time object detection

| Attribute | Details |
|-----------|---------|
| **Latest Version** | YOLOv12 (February 2025) |
| **License** | AGPL-3.0 |
| **Installation** | `pip install ultralytics` |

**Pros for Building Drawings:**
- Fast inference (real-time capable)
- Easy to train on custom datasets
- Active development
- Good documentation

**Cons for Building Drawings:**
- Requires custom dataset of annotated symbols
- AGPL license for commercial use
- May struggle with very small symbols

**Custom Training for Architectural Symbols:**
```python
from ultralytics import YOLO

# Load pretrained model
model = YOLO('yolov8n.pt')

# Train on custom architectural symbol dataset
model.train(
    data='architectural_symbols.yaml',  # Custom dataset config
    epochs=100,
    imgsz=640
)

# Inference on floor plan
results = model('floor_plan.png')

for result in results:
    for box in result.boxes:
        class_id = int(box.cls)
        class_name = model.names[class_id]
        confidence = float(box.conf)
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        print(f"Detected: {class_name} ({confidence:.2f}) at ({x1}, {y1}, {x2}, {y2})")
```

**Documentation:** https://docs.ultralytics.com/

---

### 2. Detectron2

**Purpose:** Facebook AI's object detection and segmentation platform

| Attribute | Details |
|-----------|---------|
| **License** | Apache 2.0 |
| **Installation** | See GitHub for platform-specific instructions |

**Pros for Building Drawings:**
- State-of-the-art accuracy
- Instance segmentation (useful for rooms)
- Panoptic segmentation
- Rotated bounding boxes (useful for angled text)
- Research-grade flexibility

**Cons for Building Drawings:**
- Complex setup
- Requires custom training
- Heavier than YOLO
- Slower inference

**Documentation:** https://github.com/facebookresearch/detectron2

---

## Semantic Interpretation Tools

### 1. NetworkX

**Purpose:** Graph creation and analysis

| Attribute | Details |
|-----------|---------|
| **Latest Version** | 3.5 (May 2025) |
| **License** | BSD |
| **Installation** | `pip install networkx` |

**Use Cases for Building Drawings:**
- Model room connectivity graphs
- Analyze circulation paths
- Find shortest paths (egress analysis)
- Community detection (zone identification)

**Example - Building Connectivity Graph:**
```python
import networkx as nx

# Create graph of rooms and their connections
G = nx.Graph()

# Add rooms as nodes with attributes
G.add_node("Living Room", area=25.5, type="habitable")
G.add_node("Kitchen", area=12.0, type="habitable")
G.add_node("Hallway", area=8.0, type="circulation")
G.add_node("Bedroom 1", area=15.0, type="habitable")

# Add connections (doors/openings)
G.add_edge("Living Room", "Hallway", door_width=0.9)
G.add_edge("Kitchen", "Living Room", opening_width=1.2)
G.add_edge("Hallway", "Bedroom 1", door_width=0.8)

# Analyze connectivity
print(f"Is connected: {nx.is_connected(G)}")
print(f"Shortest path Living->Bedroom: {nx.shortest_path(G, 'Living Room', 'Bedroom 1')}")
```

**Documentation:** https://networkx.org/

---

### 2. Shapely

**Purpose:** Geometric operations and spatial analysis

| Attribute | Details |
|-----------|---------|
| **Latest Version** | 2.1.2 |
| **License** | BSD |
| **Installation** | `pip install shapely` |

**Use Cases for Building Drawings:**
- Room polygon operations
- Area calculations
- Spatial queries (contains, intersects, within)
- Buffer operations (setback analysis)
- Polygon simplification

**Example - Room Analysis:**
```python
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union

# Define room polygons from extracted coordinates
living_room = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])
kitchen = Polygon([(5, 0), (8, 0), (8, 3), (5, 3)])

# Calculate areas
print(f"Living room area: {living_room.area} sq m")
print(f"Kitchen area: {kitchen.area} sq m")

# Check if rooms share a wall
print(f"Rooms touch: {living_room.touches(kitchen)}")

# Create building footprint
building = unary_union([living_room, kitchen])
print(f"Total building area: {building.area} sq m")

# Buffer for setback analysis
setback = building.buffer(3)  # 3 meter setback

# Check if point is inside room
smoke_detector = Point(2.5, 2.5)
print(f"Detector in living room: {living_room.contains(smoke_detector)}")
```

**Documentation:** https://shapely.readthedocs.io/

---

### 3. pandas

**Purpose:** Data analysis and manipulation

| Attribute | Details |
|-----------|---------|
| **License** | BSD |
| **Installation** | `pip install pandas` |

**Use Cases for Building Drawings:**
- Parse drawing schedules (door, window, room schedules)
- Aggregate extracted data
- Compare against code requirements
- Generate reports

**Example - Room Schedule:**
```python
import pandas as pd

# Create room schedule from extracted data
room_data = [
    {"name": "Living Room", "area": 25.5, "ceiling_height": 2.7, "windows": 2},
    {"name": "Bedroom 1", "area": 15.0, "ceiling_height": 2.7, "windows": 1},
    {"name": "Kitchen", "area": 12.0, "ceiling_height": 2.7, "windows": 1},
]

df = pd.DataFrame(room_data)

# Calculate volume
df['volume'] = df['area'] * df['ceiling_height']

# Check minimum area requirements
MIN_BEDROOM_AREA = 9.29  # sq m per code
df['meets_min_area'] = df.apply(
    lambda row: row['area'] >= MIN_BEDROOM_AREA if 'Bedroom' in row['name'] else True,
    axis=1
)

print(df)
```

---

## Vision Language Models (VLM) vs Traditional Approaches

### Comparison Summary

| Aspect | Traditional CV/OCR | Vision Language Models |
|--------|-------------------|----------------------|
| **Speed** | Fast (ms to seconds) | Slow (seconds to minutes) |
| **Cost** | Free/cheap | API costs or GPU costs |
| **Accuracy (text)** | 80-95% on clean docs | 90-99% with context |
| **Layout Understanding** | Limited | Excellent |
| **Symbol Recognition** | Requires training | Zero-shot capable |
| **Semantic Understanding** | None | Strong |
| **Scalability** | Excellent | Limited by cost/speed |
| **Offline Operation** | Yes | Depends on model |

### When to Use VLMs

**Best for:**
- Understanding drawing context and intent
- Interpreting annotations and notes
- Handling non-standard layouts
- Zero-shot symbol identification
- Answering questions about drawings
- Validation and quality checks

**VLM Capabilities for Floor Plans:**
- Identify furniture, doors, windows, stairs
- Understand room types from context
- Read and interpret legends
- Analyze spatial relationships
- Check accessibility compliance

### When to Use Traditional CV/OCR

**Best for:**
- High-volume batch processing
- Precise geometric extraction
- Cost-sensitive applications
- Real-time processing
- Structured data extraction (schedules, tables)

### Recommended Hybrid Approach

```
PDF Drawing Input
       |
       v
[PyMuPDF] --> Vector extraction (lines, paths, shapes)
       |
       v
[PyMuPDF] --> Render to image
       |
       +--> [EasyOCR] --> Text extraction with positions
       |
       +--> [YOLO/Custom] --> Symbol detection
       |
       v
[Shapely + NetworkX] --> Spatial analysis, room detection
       |
       v
[VLM (GPT-4V/Claude)] --> Semantic validation & interpretation
       |
       v
Structured Output (JSON)
```

### VLM API Examples

**GPT-4 Vision:**
```python
import openai
import base64

def analyze_floor_plan(image_path: str, question: str) -> str:
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    response = openai.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_data}"}
                    }
                ]
            }
        ],
        max_tokens=1000
    )
    return response.choices[0].message.content

# Example usage
result = analyze_floor_plan(
    "floor_plan.png",
    "Identify all rooms in this floor plan and list their approximate areas. "
    "Also identify the locations of doors and windows."
)
```

**Claude 3.5 Sonnet:**
```python
import anthropic
import base64

def analyze_with_claude(image_path: str, prompt: str) -> str:
    client = anthropic.Anthropic()

    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode()

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data
                        }
                    },
                    {"type": "text", "text": prompt}
                ]
            }
        ]
    )
    return message.content[0].text
```

---

## Recommended Stack for PDF Building Drawings

### Primary Use Case: PDF Building Drawings for Permit Review

**Tier 1: Essential Libraries**

| Library | Purpose | Priority |
|---------|---------|----------|
| PyMuPDF | PDF parsing, vector extraction, rendering | Critical |
| OpenCV | Image preprocessing | Critical |
| EasyOCR | Text recognition | Critical |
| Shapely | Geometric operations | High |
| pandas | Data organization | High |

**Tier 2: Symbol Detection (requires training)**

| Library | Purpose | Priority |
|---------|---------|----------|
| Ultralytics YOLO | Fast symbol detection | High |
| OR Detectron2 | Advanced segmentation | Medium |

**Tier 3: Semantic Understanding**

| Library | Purpose | Priority |
|---------|---------|----------|
| NetworkX | Connectivity analysis | Medium |
| GPT-4V/Claude API | Semantic validation | Medium |

### Installation Commands

```bash
# Core extraction stack
pip install PyMuPDF pdfplumber opencv-python easyocr

# Geometry and analysis
pip install shapely networkx pandas numpy

# Deep learning (optional, for symbol detection)
pip install ultralytics torch torchvision

# VLM integration (optional)
pip install openai anthropic
```

### Sample Processing Pipeline

```python
"""
Building Drawing Processing Pipeline
"""
import pymupdf
import cv2
import easyocr
import numpy as np
from shapely.geometry import Polygon, box
import pandas as pd

class DrawingProcessor:
    def __init__(self):
        self.ocr_reader = easyocr.Reader(['en'], gpu=False)

    def process_pdf(self, pdf_path: str) -> dict:
        """Process a PDF drawing and extract structured data."""
        doc = pymupdf.open(pdf_path)
        results = []

        for page_num, page in enumerate(doc):
            page_data = {
                'page': page_num + 1,
                'vectors': self._extract_vectors(page),
                'text': self._extract_text(page),
                'ocr_text': self._ocr_page(page)
            }
            results.append(page_data)

        doc.close()
        return {'pages': results}

    def _extract_vectors(self, page) -> list:
        """Extract vector graphics (lines, rectangles, curves)."""
        drawings = page.get_drawings()
        vectors = []

        for path in drawings:
            for item in path['items']:
                if item[0] == 'l':  # line
                    vectors.append({
                        'type': 'line',
                        'start': list(item[1]),
                        'end': list(item[2]),
                        'width': path.get('width', 1)
                    })
                elif item[0] == 're':  # rectangle
                    vectors.append({
                        'type': 'rect',
                        'bbox': list(item[1]),
                        'fill': path.get('fill'),
                        'stroke': path.get('color')
                    })

        return vectors

    def _extract_text(self, page) -> list:
        """Extract embedded text with positions."""
        text_dict = page.get_text("dict")
        text_items = []

        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text_items.append({
                            'text': span['text'],
                            'bbox': list(span['bbox']),
                            'font': span.get('font', ''),
                            'size': span.get('size', 0)
                        })

        return text_items

    def _ocr_page(self, page, dpi=200) -> list:
        """OCR the page for any text not in the PDF structure."""
        pix = page.get_pixmap(dpi=dpi)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )

        if pix.n == 4:  # RGBA
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)

        results = self.ocr_reader.readtext(img)

        return [
            {'text': text, 'bbox': bbox, 'confidence': conf}
            for bbox, text, conf in results
            if conf > 0.5
        ]


# Usage
processor = DrawingProcessor()
data = processor.process_pdf("floor_plan.pdf")
```

---

## Open Source Floor Plan Recognition Projects

### 1. TF2DeepFloorplan
- **GitHub:** https://github.com/zcemycl/TF2DeepFloorplan
- **Purpose:** Room segmentation and boundary detection
- **Framework:** TensorFlow 2
- **Features:** Multi-task network, room-boundary-guided attention

### 2. DeepFloorplan (Original)
- **GitHub:** https://github.com/zlzeng/DeepFloorplan
- **Paper:** ICCV 2019
- **Purpose:** Room type and boundary recognition

### 3. FloorPlanParser
- **GitHub:** https://github.com/TINY-KE/FloorPlanParser
- **Purpose:** Vectorization of floor plan elements
- **Output:** Structured JSON of detected elements

### 4. Object Detection in Floor Plan Images
- **GitHub:** https://github.com/dwnsingh/Object-Detection-in-Floor-Plan-Images
- **Models:** YOLO and Faster RCNN
- **Objects:** Furniture, fixtures

### 5. AFPlan (Architectural Floor Plan)
- **GitHub:** https://github.com/cansik/architectural-floor-plan
- **Purpose:** Fast room detection
- **Focus:** Non-standardized floor plans

---

## References

### CAD Libraries
- [ezdxf Documentation](https://ezdxf.readthedocs.io/)
- [ezdxf PyPI](https://pypi.org/project/ezdxf/)
- [pythonOCC GitHub](https://github.com/tpaviot/pythonocc-core)
- [LibreDWG GNU Project](https://www.gnu.org/software/libredwg/)
- [ODA File Converter](https://www.opendesign.com/guestfiles/oda_file_converter)

### PDF Libraries
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- [PyMuPDF Vector Graphics Blog](https://artifex.com/blog/extracting-and-creating-vector-graphics-in-a-pdf-using-python-pymupdf)
- [pdfplumber GitHub](https://github.com/jsvine/pdfplumber)
- [pikepdf Documentation](https://pikepdf.readthedocs.io/)

### OCR/CV Libraries
- [OpenCV Hough Lines Tutorial](https://docs.opencv.org/3.4/d9/db0/tutorial_hough_lines.html)
- [EasyOCR GitHub](https://github.com/JaidedAI/EasyOCR)
- [pytesseract PyPI](https://pypi.org/project/pytesseract/)
- [LayoutParser](https://layout-parser.github.io/)

### Deep Learning Object Detection
- [Ultralytics YOLO Docs](https://docs.ultralytics.com/)
- [Detectron2 GitHub](https://github.com/facebookresearch/detectron2)
- [Best Object Detection Models 2025](https://blog.roboflow.com/best-object-detection-models/)

### Semantic Tools
- [NetworkX Documentation](https://networkx.org/)
- [Shapely Documentation](https://shapely.readthedocs.io/)

### VLM Research
- [OCR vs VLM Comparison](https://www.f22labs.com/blogs/ocr-vs-vlm-vision-language-models-key-comparison/)
- [VLM for Engineering Design](https://link.springer.com/article/10.1007/s10462-025-11290-y)
- [Vision LLMs for Floor Plans (ACM 2025)](https://dl.acm.org/doi/10.1145/3704268.3748681)
- [GPT-4 Vision Guide](https://www.datacamp.com/tutorial/gpt-4-vision-comprehensive-guide)

### Floor Plan Recognition
- [TF2DeepFloorplan](https://github.com/zcemycl/TF2DeepFloorplan)
- [Deep Floor Plan Recognition (ICCV 2019)](https://openaccess.thecvf.com/content_ICCV_2019/papers/Zeng_Deep_Floor_Plan_Recognition_Using_a_Multi-Task_Network_With_Room-Boundary-Guided_ICCV_2019_paper.pdf)
- [Residential Floor Plan Recognition (CVPR 2021)](https://openaccess.thecvf.com/content/CVPR2021/papers/Lv_Residential_Floor_Plan_Recognition_and_Reconstruction_CVPR_2021_paper.pdf)

---

*Report generated January 2025 for Building Permit Review Automation project*
