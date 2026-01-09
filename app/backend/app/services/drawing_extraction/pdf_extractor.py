"""
PDF Drawing Extractor Module

Extracts vector graphics, text, and images from PDF building drawings using PyMuPDF (fitz).
This is the primary component of the VLM-free drawing extraction pipeline.
"""

import fitz  # PyMuPDF
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class VectorType(Enum):
    """Types of vector elements that can be extracted from PDFs."""
    LINE = "line"
    RECTANGLE = "rect"
    QUAD = "quad"
    CURVE = "curve"
    CIRCLE = "circle"
    POLYGON = "polygon"
    PATH = "path"


@dataclass
class Point:
    """A 2D point with x and y coordinates."""
    x: float
    y: float

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

    @classmethod
    def from_tuple(cls, t: Tuple[float, float]) -> "Point":
        return cls(x=t[0], y=t[1])


@dataclass
class BoundingBox:
    """A bounding box defined by x0, y0 (top-left) and x1, y1 (bottom-right)."""
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return abs(self.x1 - self.x0)

    @property
    def height(self) -> float:
        return abs(self.y1 - self.y0)

    @property
    def center(self) -> Point:
        return Point(x=(self.x0 + self.x1) / 2, y=(self.y0 + self.y1) / 2)

    def to_tuple(self) -> Tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)

    @classmethod
    def from_tuple(cls, t: Tuple[float, float, float, float]) -> "BoundingBox":
        return cls(x0=t[0], y0=t[1], x1=t[2], y1=t[3])

    @classmethod
    def from_rect(cls, rect: fitz.Rect) -> "BoundingBox":
        return cls(x0=rect.x0, y0=rect.y0, x1=rect.x1, y1=rect.y1)


@dataclass
class VectorElement:
    """
    Represents a vector graphic element extracted from a PDF.

    Attributes:
        type: The type of vector element (line, rectangle, curve, etc.)
        coords: List of coordinate points defining the element
        width: Line/stroke width
        color: Stroke color as RGB tuple (0-1 range)
        fill_color: Fill color as RGB tuple (0-1 range), None if not filled
        bbox: Bounding box of the element
        layer: Optional layer name if available
    """
    type: VectorType
    coords: List[Tuple[float, float]]
    width: float = 1.0
    color: Tuple[float, ...] = (0.0, 0.0, 0.0)
    fill_color: Optional[Tuple[float, ...]] = None
    bbox: Optional[BoundingBox] = None
    layer: Optional[str] = None
    closed: bool = False

    @property
    def length(self) -> float:
        """Calculate the length of the vector element."""
        if self.type == VectorType.LINE and len(self.coords) >= 2:
            p1, p2 = self.coords[0], self.coords[1]
            return ((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)**0.5
        return 0.0


@dataclass
class TextElement:
    """
    Represents a text element extracted from a PDF.

    Attributes:
        text: The text content
        bbox: Bounding box of the text
        font: Font name
        size: Font size in points
        color: Text color as RGB tuple
        flags: Font flags (bold, italic, etc.)
        rotation: Text rotation angle in degrees
    """
    text: str
    bbox: BoundingBox
    font: str = ""
    size: float = 12.0
    color: Tuple[float, ...] = (0.0, 0.0, 0.0)
    flags: int = 0
    rotation: float = 0.0

    @property
    def is_bold(self) -> bool:
        return bool(self.flags & 2**4)

    @property
    def is_italic(self) -> bool:
        return bool(self.flags & 2**1)


@dataclass
class ImageElement:
    """
    Represents an embedded image in a PDF.

    Attributes:
        bbox: Bounding box of the image on the page
        width: Image width in pixels
        height: Image height in pixels
        xref: PDF internal reference number
        image_data: Raw image bytes (if extracted)
    """
    bbox: BoundingBox
    width: int
    height: int
    xref: int
    image_data: Optional[bytes] = None


@dataclass
class PageMetadata:
    """Metadata about a PDF page."""
    page_number: int
    width: float
    height: float
    rotation: int = 0
    media_box: Optional[BoundingBox] = None
    crop_box: Optional[BoundingBox] = None


@dataclass
class DrawingExtractionResult:
    """
    Complete extraction result for a PDF page.

    Attributes:
        page_metadata: Page dimensions and metadata
        vectors: List of extracted vector elements
        texts: List of extracted text elements
        images: List of embedded images
        annotations: List of PDF annotations
    """
    page_metadata: PageMetadata
    vectors: List[VectorElement] = field(default_factory=list)
    texts: List[TextElement] = field(default_factory=list)
    images: List[ImageElement] = field(default_factory=list)
    annotations: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def total_elements(self) -> int:
        return len(self.vectors) + len(self.texts) + len(self.images)


class PDFDrawingExtractor:
    """
    Extracts vector graphics, text, and images from PDF building drawings.

    Uses PyMuPDF (fitz) for extraction, providing access to:
    - Vector paths (lines, rectangles, curves, polygons)
    - Embedded text with font and position information
    - Embedded images and their locations
    - Page metadata and structure

    Example:
        >>> extractor = PDFDrawingExtractor("floor_plan.pdf")
        >>> result = extractor.extract_all(page_num=0)
        >>> print(f"Found {len(result.vectors)} vector elements")
        >>> extractor.close()
    """

    def __init__(self, pdf_path: str):
        """
        Initialize the extractor with a PDF file.

        Args:
            pdf_path: Path to the PDF file to extract from

        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            fitz.FileDataError: If the file is not a valid PDF
        """
        self.pdf_path = pdf_path
        self.doc: fitz.Document = fitz.open(pdf_path)
        self._scale_factor: float = 1.0

    @property
    def page_count(self) -> int:
        """Return the number of pages in the PDF."""
        return len(self.doc)

    @property
    def metadata(self) -> Dict[str, Any]:
        """Return PDF metadata (title, author, etc.)."""
        return dict(self.doc.metadata) if self.doc.metadata else {}

    def get_page_metadata(self, page_num: int = 0) -> PageMetadata:
        """
        Get metadata for a specific page.

        Args:
            page_num: Page number (0-indexed)

        Returns:
            PageMetadata object with page dimensions and properties
        """
        self._validate_page_num(page_num)
        page = self.doc[page_num]

        return PageMetadata(
            page_number=page_num,
            width=page.rect.width,
            height=page.rect.height,
            rotation=page.rotation,
            media_box=BoundingBox.from_rect(page.mediabox) if page.mediabox else None,
            crop_box=BoundingBox.from_rect(page.cropbox) if page.cropbox else None
        )

    def extract_vectors(self, page_num: int = 0) -> List[VectorElement]:
        """
        Extract all vector graphics from a page.

        This includes lines, rectangles, curves, and other path elements
        commonly found in architectural drawings.

        Args:
            page_num: Page number (0-indexed)

        Returns:
            List of VectorElement objects
        """
        self._validate_page_num(page_num)
        page = self.doc[page_num]
        drawings = page.get_drawings()
        vectors: List[VectorElement] = []

        for path in drawings:
            path_vectors = self._process_drawing_path(path)
            vectors.extend(path_vectors)

        logger.debug(f"Extracted {len(vectors)} vector elements from page {page_num}")
        return vectors

    def _process_drawing_path(self, path: Dict[str, Any]) -> List[VectorElement]:
        """
        Process a single drawing path and extract vector elements.

        Args:
            path: Drawing path dictionary from PyMuPDF

        Returns:
            List of VectorElement objects from this path
        """
        vectors: List[VectorElement] = []

        # Extract common properties
        stroke_width = path.get("width", 1.0) or 1.0
        stroke_color = self._normalize_color(path.get("color"))
        fill_color = self._normalize_color(path.get("fill"))
        rect = path.get("rect")
        path_bbox = BoundingBox.from_tuple(rect) if rect else None
        closePath = path.get("closePath", False)

        items = path.get("items", [])
        path_coords: List[Tuple[float, float]] = []

        for item in items:
            if not item:
                continue

            op = item[0]  # Operation type

            if op == "l":  # Line
                p1 = (item[1].x, item[1].y)
                p2 = (item[2].x, item[2].y)
                vectors.append(VectorElement(
                    type=VectorType.LINE,
                    coords=[p1, p2],
                    width=stroke_width,
                    color=stroke_color,
                    fill_color=fill_color,
                    bbox=self._calculate_line_bbox(p1, p2)
                ))
                path_coords.extend([p1, p2])

            elif op == "re":  # Rectangle
                rect = item[1]
                coords = [
                    (rect.x0, rect.y0),
                    (rect.x1, rect.y0),
                    (rect.x1, rect.y1),
                    (rect.x0, rect.y1)
                ]
                vectors.append(VectorElement(
                    type=VectorType.RECTANGLE,
                    coords=coords,
                    width=stroke_width,
                    color=stroke_color,
                    fill_color=fill_color,
                    bbox=BoundingBox(rect.x0, rect.y0, rect.x1, rect.y1),
                    closed=True
                ))
                path_coords.extend(coords)

            elif op == "qu":  # Quad (4-point shape)
                quad = item[1]
                coords = [
                    (quad.ul.x, quad.ul.y),
                    (quad.ur.x, quad.ur.y),
                    (quad.lr.x, quad.lr.y),
                    (quad.ll.x, quad.ll.y)
                ]
                vectors.append(VectorElement(
                    type=VectorType.QUAD,
                    coords=coords,
                    width=stroke_width,
                    color=stroke_color,
                    fill_color=fill_color,
                    closed=True
                ))
                path_coords.extend(coords)

            elif op == "c":  # Bezier curve
                # Cubic Bezier: start, control1, control2, end
                coords = [
                    (item[1].x, item[1].y),  # Start
                    (item[2].x, item[2].y),  # Control 1
                    (item[3].x, item[3].y),  # Control 2
                    (item[4].x, item[4].y)   # End
                ]
                vectors.append(VectorElement(
                    type=VectorType.CURVE,
                    coords=coords,
                    width=stroke_width,
                    color=stroke_color,
                    fill_color=fill_color
                ))
                path_coords.extend(coords)

        return vectors

    def _normalize_color(self, color: Any) -> Tuple[float, ...]:
        """
        Normalize color to RGB tuple in 0-1 range.

        Args:
            color: Color value (could be None, tuple, or single value)

        Returns:
            RGB tuple (r, g, b) with values 0-1
        """
        if color is None:
            return (0.0, 0.0, 0.0)
        if isinstance(color, (tuple, list)):
            if len(color) == 1:
                # Grayscale
                return (color[0], color[0], color[0])
            elif len(color) >= 3:
                return (float(color[0]), float(color[1]), float(color[2]))
        elif isinstance(color, (int, float)):
            return (float(color), float(color), float(color))
        return (0.0, 0.0, 0.0)

    def _calculate_line_bbox(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> BoundingBox:
        """Calculate bounding box for a line segment."""
        return BoundingBox(
            x0=min(p1[0], p2[0]),
            y0=min(p1[1], p2[1]),
            x1=max(p1[0], p2[0]),
            y1=max(p1[1], p2[1])
        )

    def extract_text(self, page_num: int = 0) -> List[TextElement]:
        """
        Extract embedded text with position, font, and size information.

        This extracts text that is embedded in the PDF as text objects,
        not text that appears in images (use OCR for that).

        Args:
            page_num: Page number (0-indexed)

        Returns:
            List of TextElement objects
        """
        self._validate_page_num(page_num)
        page = self.doc[page_num]
        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        texts: List[TextElement] = []

        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:  # Type 0 is text, type 1 is image
                continue

            for line in block.get("lines", []):
                # Get line direction for rotation detection
                line_dir = line.get("dir", (1, 0))
                rotation = self._calculate_rotation(line_dir)

                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue

                    bbox_tuple = span.get("bbox", (0, 0, 0, 0))
                    texts.append(TextElement(
                        text=text,
                        bbox=BoundingBox.from_tuple(bbox_tuple),
                        font=span.get("font", ""),
                        size=span.get("size", 12.0),
                        color=self._normalize_color(span.get("color")),
                        flags=span.get("flags", 0),
                        rotation=rotation
                    ))

        logger.debug(f"Extracted {len(texts)} text elements from page {page_num}")
        return texts

    def _calculate_rotation(self, direction: Tuple[float, float]) -> float:
        """
        Calculate rotation angle from direction vector.

        Args:
            direction: (cos, sin) direction tuple from PyMuPDF

        Returns:
            Rotation angle in degrees (0, 90, 180, 270 typically)
        """
        import math
        cos_val, sin_val = direction
        angle = math.degrees(math.atan2(sin_val, cos_val))
        # Normalize to 0-360
        return angle % 360

    def extract_images(self, page_num: int = 0, include_data: bool = False) -> List[ImageElement]:
        """
        Extract information about embedded images on a page.

        Args:
            page_num: Page number (0-indexed)
            include_data: If True, include raw image bytes

        Returns:
            List of ImageElement objects
        """
        self._validate_page_num(page_num)
        page = self.doc[page_num]
        images: List[ImageElement] = []

        image_list = page.get_images(full=True)

        for img_info in image_list:
            xref = img_info[0]

            # Get image rect on page
            img_rects = page.get_image_rects(xref)
            if not img_rects:
                continue

            img_rect = img_rects[0]

            image_data = None
            if include_data:
                try:
                    base_image = self.doc.extract_image(xref)
                    image_data = base_image.get("image")
                except Exception as e:
                    logger.warning(f"Failed to extract image data for xref {xref}: {e}")

            images.append(ImageElement(
                bbox=BoundingBox.from_rect(img_rect),
                width=img_info[2],
                height=img_info[3],
                xref=xref,
                image_data=image_data
            ))

        logger.debug(f"Extracted {len(images)} images from page {page_num}")
        return images

    def extract_annotations(self, page_num: int = 0) -> List[Dict[str, Any]]:
        """
        Extract PDF annotations (comments, highlights, links, etc.).

        Args:
            page_num: Page number (0-indexed)

        Returns:
            List of annotation dictionaries
        """
        self._validate_page_num(page_num)
        page = self.doc[page_num]
        annotations: List[Dict[str, Any]] = []

        for annot in page.annots():
            annot_info = {
                "type": annot.type[1],  # Type name
                "rect": BoundingBox.from_rect(annot.rect).to_tuple(),
                "content": annot.info.get("content", ""),
                "title": annot.info.get("title", ""),
                "subject": annot.info.get("subject", ""),
            }
            annotations.append(annot_info)

        return annotations

    def extract_all(self, page_num: int = 0, include_image_data: bool = False) -> DrawingExtractionResult:
        """
        Extract all elements from a page (vectors, text, images, annotations).

        This is the main method for comprehensive extraction.

        Args:
            page_num: Page number (0-indexed)
            include_image_data: If True, include raw image bytes

        Returns:
            DrawingExtractionResult containing all extracted elements
        """
        return DrawingExtractionResult(
            page_metadata=self.get_page_metadata(page_num),
            vectors=self.extract_vectors(page_num),
            texts=self.extract_text(page_num),
            images=self.extract_images(page_num, include_data=include_image_data),
            annotations=self.extract_annotations(page_num)
        )

    def render_to_image(
        self,
        page_num: int = 0,
        dpi: int = 200,
        alpha: bool = False
    ) -> np.ndarray:
        """
        Render a page to a numpy array image for CV/OCR processing.

        Args:
            page_num: Page number (0-indexed)
            dpi: Resolution in dots per inch (default 200)
            alpha: Include alpha channel (default False for RGB)

        Returns:
            numpy array of shape (height, width, channels)
            Channels is 3 for RGB, 4 if alpha=True
        """
        self._validate_page_num(page_num)
        page = self.doc[page_num]

        # Calculate zoom factor from DPI
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)

        pix = page.get_pixmap(matrix=mat, alpha=alpha)

        # Convert to numpy array
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )

        return img.copy()  # Return a copy to avoid memory issues

    def render_to_pil(self, page_num: int = 0, dpi: int = 200):
        """
        Render a page to a PIL Image object.

        Args:
            page_num: Page number (0-indexed)
            dpi: Resolution in dots per inch

        Returns:
            PIL.Image object
        """
        try:
            from PIL import Image
        except ImportError:
            raise ImportError("PIL/Pillow is required for render_to_pil()")

        img_array = self.render_to_image(page_num, dpi, alpha=False)
        return Image.fromarray(img_array)

    def save_page_image(
        self,
        page_num: int = 0,
        output_path: str = "page.png",
        dpi: int = 200
    ) -> str:
        """
        Save a page as an image file.

        Args:
            page_num: Page number (0-indexed)
            output_path: Output file path
            dpi: Resolution in dots per inch

        Returns:
            The output path
        """
        self._validate_page_num(page_num)
        page = self.doc[page_num]

        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        pix.save(output_path)

        logger.info(f"Saved page {page_num} to {output_path}")
        return output_path

    def extract_all_pages(self, include_image_data: bool = False) -> List[DrawingExtractionResult]:
        """
        Extract elements from all pages in the PDF.

        Args:
            include_image_data: If True, include raw image bytes

        Returns:
            List of DrawingExtractionResult objects, one per page
        """
        results = []
        for page_num in range(self.page_count):
            results.append(self.extract_all(page_num, include_image_data))
        return results

    def get_scale_from_text(self, page_num: int = 0) -> Optional[float]:
        """
        Attempt to detect drawing scale from text annotations.

        Looks for common scale notations like "1:100", "Scale: 1/4" = 1'-0""

        Args:
            page_num: Page number to search

        Returns:
            Scale factor if found, None otherwise
        """
        import re

        texts = self.extract_text(page_num)

        # Common scale patterns
        patterns = [
            r"1\s*:\s*(\d+)",           # 1:100
            r"scale\s*[:=]?\s*1\s*:\s*(\d+)",  # Scale: 1:100
            r"(\d+)\s*mm\s*=\s*1\s*m",  # 10mm = 1m
        ]

        for text_elem in texts:
            text = text_elem.text.lower()
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        scale_value = float(match.group(1))
                        return 1.0 / scale_value
                    except (ValueError, IndexError):
                        continue

        return None

    def find_dimension_lines(self, page_num: int = 0) -> List[Dict[str, Any]]:
        """
        Find potential dimension lines and their associated text.

        Dimension lines typically have:
        - Horizontal or vertical orientation
        - Small tick marks at ends
        - Text nearby indicating measurement

        Args:
            page_num: Page number to search

        Returns:
            List of potential dimension annotations
        """
        vectors = self.extract_vectors(page_num)
        texts = self.extract_text(page_num)

        dimension_lines: List[Dict[str, Any]] = []

        # Filter for horizontal and vertical lines
        for vec in vectors:
            if vec.type != VectorType.LINE:
                continue

            if len(vec.coords) < 2:
                continue

            p1, p2 = vec.coords[0], vec.coords[1]

            # Check if roughly horizontal or vertical
            dx = abs(p2[0] - p1[0])
            dy = abs(p2[1] - p1[1])

            is_horizontal = dy < 5 and dx > 20
            is_vertical = dx < 5 and dy > 20

            if not (is_horizontal or is_vertical):
                continue

            # Look for nearby text that looks like a dimension
            line_center = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)

            for text in texts:
                # Check if text is near the line
                text_center = text.bbox.center
                dist = ((text_center.x - line_center[0])**2 +
                       (text_center.y - line_center[1])**2)**0.5

                if dist < 50:  # Within 50 units
                    # Check if text looks like a dimension
                    import re
                    if re.search(r'\d+', text.text):
                        dimension_lines.append({
                            "line": vec,
                            "text": text,
                            "orientation": "horizontal" if is_horizontal else "vertical",
                            "length": vec.length
                        })
                        break

        return dimension_lines

    def _validate_page_num(self, page_num: int) -> None:
        """Validate that page number is within range."""
        if page_num < 0 or page_num >= self.page_count:
            raise ValueError(
                f"Page number {page_num} out of range. "
                f"PDF has {self.page_count} pages (0-indexed)."
            )

    def close(self) -> None:
        """Close the PDF document and release resources."""
        if self.doc:
            self.doc.close()
            logger.debug(f"Closed PDF: {self.pdf_path}")

    def __enter__(self) -> "PDFDrawingExtractor":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def __del__(self) -> None:
        """Destructor to ensure document is closed."""
        try:
            self.close()
        except Exception:
            pass
