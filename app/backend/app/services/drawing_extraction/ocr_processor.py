"""
OCR Processor Module

Performs optical character recognition on rasterized areas of building drawings
using EasyOCR. Specializes in extracting dimensions, room labels, and annotations.
"""

import re
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logger.warning("EasyOCR not available. Install with: pip install easyocr")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not available. Install with: pip install opencv-python")


class TextType(Enum):
    """Types of text that can be identified in drawings."""
    UNKNOWN = "unknown"
    DIMENSION = "dimension"
    ROOM_LABEL = "room_label"
    ANNOTATION = "annotation"
    SCALE = "scale"
    TITLE = "title"
    REFERENCE = "reference"
    ELEVATION = "elevation"


@dataclass
class OCRResult:
    """
    Represents a single OCR detection result.

    Attributes:
        text: Recognized text string
        bbox: Bounding box as list of 4 corner points [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
        confidence: Confidence score (0-1)
        text_type: Classified type of text
        parsed_value: Parsed value if applicable (e.g., dimension value)
        rotation: Detected text rotation in degrees
    """
    text: str
    bbox: List[Tuple[float, float]]
    confidence: float
    text_type: TextType = TextType.UNKNOWN
    parsed_value: Optional[Dict[str, Any]] = None
    rotation: float = 0.0

    @property
    def center(self) -> Tuple[float, float]:
        """Calculate center point of bounding box."""
        if not self.bbox or len(self.bbox) < 4:
            return (0, 0)
        xs = [p[0] for p in self.bbox]
        ys = [p[1] for p in self.bbox]
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    @property
    def width(self) -> float:
        """Calculate width of bounding box."""
        if not self.bbox or len(self.bbox) < 2:
            return 0
        return abs(self.bbox[1][0] - self.bbox[0][0])

    @property
    def height(self) -> float:
        """Calculate height of bounding box."""
        if not self.bbox or len(self.bbox) < 4:
            return 0
        return abs(self.bbox[3][1] - self.bbox[0][1])


@dataclass
class ParsedDimension:
    """Parsed dimension value with unit."""
    value: float
    unit: str
    raw_text: str
    value_in_mm: float = 0.0

    def __post_init__(self):
        """Convert value to mm for standardization."""
        self.value_in_mm = self._to_mm()

    def _to_mm(self) -> float:
        """Convert dimension to millimeters."""
        unit_to_mm = {
            "mm": 1.0,
            "cm": 10.0,
            "m": 1000.0,
            "in": 25.4,
            "ft": 304.8,
            "'": 304.8,
            '"': 25.4,
        }
        return self.value * unit_to_mm.get(self.unit.lower(), 1.0)


class DrawingOCR:
    """
    Performs OCR on building drawing images.

    Uses EasyOCR for text recognition, with special handling for:
    - Rotated text (common in drawings)
    - Dimension strings with units
    - Room labels and annotations
    - Scale notations

    Example:
        >>> ocr = DrawingOCR(gpu=False)
        >>> results = ocr.extract_text(image)
        >>> dimensions = ocr.extract_dimensions(image)
        >>> for dim in dimensions:
        ...     print(f"{dim.value} {dim.unit}")
    """

    # Common room name patterns
    ROOM_PATTERNS = [
        r"(?i)(bed\s*room|bedroom|br)\s*\d*",
        r"(?i)(bath\s*room|bathroom|wc|toilet)\s*\d*",
        r"(?i)(living\s*room|living|lr)",
        r"(?i)(dining\s*room|dining|dr)",
        r"(?i)(kitchen|kit|kitch)",
        r"(?i)(garage|gar)",
        r"(?i)(closet|clo|storage|stor)",
        r"(?i)(hall|hallway|corridor)",
        r"(?i)(entry|foyer|vestibule)",
        r"(?i)(basement|bsmt)",
        r"(?i)(office|study|den)",
        r"(?i)(utility|mechanical|mech)",
        r"(?i)(laundry|laund)",
        r"(?i)(porch|deck|patio|balcony)",
    ]

    # Dimension patterns - handles various formats
    DIMENSION_PATTERNS = [
        # Standard metric: 1000, 1000mm, 1000 mm, 1.5m, 1.5 m
        r"(\d+(?:\.\d+)?)\s*(mm|m|cm)?",
        # Imperial: 10'-6", 10' 6", 10'6", 10ft 6in
        r"(\d+)['′]\s*[-]?\s*(\d+)?[\"″]?",
        r"(\d+)\s*(?:ft|feet)[\s-]*(\d+)?\s*(?:in|inch|inches)?",
        # Simple number that looks like dimension
        r"^\s*(\d{3,5})\s*$",  # 3-5 digit numbers often are mm dimensions
    ]

    # Scale notation patterns
    SCALE_PATTERNS = [
        r"(?i)scale\s*[:=]?\s*1\s*[:/-]\s*(\d+)",
        r"1\s*[:/-]\s*(\d+)",
        r"(?i)(\d+)\s*mm\s*=\s*1\s*m",
    ]

    def __init__(
        self,
        languages: List[str] = None,
        gpu: bool = False,
        model_storage_directory: Optional[str] = None
    ):
        """
        Initialize the OCR processor.

        Args:
            languages: List of language codes (default ['en'])
            gpu: Whether to use GPU acceleration
            model_storage_directory: Custom directory for model storage
        """
        self.languages = languages or ['en']
        self.gpu = gpu
        self._reader = None

        if not EASYOCR_AVAILABLE:
            logger.warning("EasyOCR not installed. OCR functionality will be limited.")

        self._model_storage = model_storage_directory

        # Compile regex patterns
        self._dimension_patterns = [re.compile(p) for p in self.DIMENSION_PATTERNS]
        self._room_patterns = [re.compile(p) for p in self.ROOM_PATTERNS]
        self._scale_patterns = [re.compile(p) for p in self.SCALE_PATTERNS]

    @property
    def reader(self):
        """Lazy initialization of EasyOCR reader."""
        if self._reader is None:
            if not EASYOCR_AVAILABLE:
                raise ImportError(
                    "EasyOCR is required for OCR functionality. "
                    "Install with: pip install easyocr"
                )
            kwargs = {
                'lang_list': self.languages,
                'gpu': self.gpu
            }
            if self._model_storage:
                kwargs['model_storage_directory'] = self._model_storage

            logger.info(f"Initializing EasyOCR reader (gpu={self.gpu})")
            self._reader = easyocr.Reader(**kwargs)
        return self._reader

    def extract_text(
        self,
        image: np.ndarray,
        min_confidence: float = 0.3,
        rotation_info: Optional[List[int]] = None,
        allowlist: Optional[str] = None
    ) -> List[OCRResult]:
        """
        Extract all text from an image.

        Args:
            image: Input image as numpy array (RGB or grayscale)
            min_confidence: Minimum confidence threshold (0-1)
            rotation_info: List of rotation angles to try [0, 90, 180, 270]
            allowlist: String of allowed characters (e.g., "0123456789.-'" for dimensions)

        Returns:
            List of OCRResult objects
        """
        if not EASYOCR_AVAILABLE:
            logger.warning("EasyOCR not available, returning empty results")
            return []

        # Default rotation handling for drawings
        if rotation_info is None:
            rotation_info = [0, 90, 180, 270]

        # Build kwargs for readtext
        kwargs = {
            'rotation_info': rotation_info,
            'paragraph': False,
        }
        if allowlist:
            kwargs['allowlist'] = allowlist

        try:
            raw_results = self.reader.readtext(image, **kwargs)
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return []

        results = []
        for bbox, text, confidence in raw_results:
            if confidence < min_confidence:
                continue

            # Convert bbox to list of tuples
            bbox_tuples = [tuple(point) for point in bbox]

            # Classify text type
            text_type, parsed = self._classify_text(text)

            results.append(OCRResult(
                text=text.strip(),
                bbox=bbox_tuples,
                confidence=confidence,
                text_type=text_type,
                parsed_value=parsed,
                rotation=self._estimate_rotation(bbox_tuples)
            ))

        logger.debug(f"Extracted {len(results)} text elements")
        return results

    def extract_dimensions(
        self,
        image: np.ndarray,
        min_confidence: float = 0.4
    ) -> List[ParsedDimension]:
        """
        Extract dimension values from an image.

        Optimized for dimension text extraction with character filtering.

        Args:
            image: Input image as numpy array
            min_confidence: Minimum confidence threshold

        Returns:
            List of ParsedDimension objects
        """
        # Use allowlist for dimension characters
        dimension_chars = "0123456789.-'\"′″/,xX mMcCfFtTiInN"

        results = self.extract_text(
            image,
            min_confidence=min_confidence,
            allowlist=dimension_chars
        )

        dimensions = []
        for result in results:
            if result.text_type == TextType.DIMENSION and result.parsed_value:
                dim = ParsedDimension(
                    value=result.parsed_value.get('value', 0),
                    unit=result.parsed_value.get('unit', 'mm'),
                    raw_text=result.text
                )
                dimensions.append(dim)
            else:
                # Try to parse as dimension anyway
                parsed = self.parse_dimension(result.text)
                if parsed:
                    dimensions.append(parsed)

        return dimensions

    def extract_room_labels(
        self,
        image: np.ndarray,
        min_confidence: float = 0.5
    ) -> List[OCRResult]:
        """
        Extract room labels from an image.

        Args:
            image: Input image as numpy array
            min_confidence: Minimum confidence threshold

        Returns:
            List of OCRResult objects that are room labels
        """
        results = self.extract_text(image, min_confidence=min_confidence)

        room_labels = []
        for result in results:
            if result.text_type == TextType.ROOM_LABEL:
                room_labels.append(result)
            else:
                # Check against room patterns
                if self._is_room_label(result.text):
                    result.text_type = TextType.ROOM_LABEL
                    room_labels.append(result)

        return room_labels

    def _classify_text(self, text: str) -> Tuple[TextType, Optional[Dict[str, Any]]]:
        """
        Classify text type and parse if applicable.

        Args:
            text: Text string to classify

        Returns:
            Tuple of (TextType, parsed_value dict or None)
        """
        text_clean = text.strip()

        # Check for dimension
        for pattern in self._dimension_patterns:
            match = pattern.search(text_clean)
            if match:
                parsed = self._parse_dimension_match(text_clean, match)
                if parsed:
                    return TextType.DIMENSION, parsed

        # Check for room label
        if self._is_room_label(text_clean):
            return TextType.ROOM_LABEL, {"room_name": text_clean}

        # Check for scale notation
        for pattern in self._scale_patterns:
            match = pattern.search(text_clean)
            if match:
                try:
                    scale_value = int(match.group(1))
                    return TextType.SCALE, {"scale": f"1:{scale_value}"}
                except (ValueError, IndexError):
                    pass

        # Check for elevation reference
        if re.search(r"(?i)(elev|elevation|el\.?)\s*[:=]?\s*[\d.+-]+", text_clean):
            return TextType.ELEVATION, None

        return TextType.UNKNOWN, None

    def _parse_dimension_match(
        self,
        text: str,
        match: re.Match
    ) -> Optional[Dict[str, Any]]:
        """Parse a dimension from regex match."""
        try:
            groups = match.groups()

            # Handle imperial feet-inches format
            if "'" in text or "ft" in text.lower():
                feet = float(groups[0]) if groups[0] else 0
                inches = float(groups[1]) if len(groups) > 1 and groups[1] else 0
                return {
                    "value": feet * 12 + inches,
                    "unit": "in",
                    "feet": feet,
                    "inches": inches
                }

            # Standard metric/simple format
            value = float(groups[0])
            unit = groups[1] if len(groups) > 1 and groups[1] else "mm"

            # Default large numbers to mm
            if not unit and value >= 100:
                unit = "mm"
            elif not unit:
                unit = "mm"

            return {"value": value, "unit": unit.lower()}

        except (ValueError, IndexError) as e:
            logger.debug(f"Failed to parse dimension '{text}': {e}")
            return None

    def parse_dimension(self, text: str) -> Optional[ParsedDimension]:
        """
        Parse a dimension string into value and unit.

        Handles various formats:
        - 1000mm, 1000 mm, 1000
        - 1.5m, 1.5 m
        - 10'-6", 10' 6", 10ft 6in

        Args:
            text: Dimension string to parse

        Returns:
            ParsedDimension object or None if parsing fails
        """
        text = text.strip()

        # Try each pattern
        for pattern in self._dimension_patterns:
            match = pattern.search(text)
            if match:
                parsed = self._parse_dimension_match(text, match)
                if parsed:
                    return ParsedDimension(
                        value=parsed.get("value", 0),
                        unit=parsed.get("unit", "mm"),
                        raw_text=text
                    )

        return None

    def _is_room_label(self, text: str) -> bool:
        """Check if text matches a room label pattern."""
        for pattern in self._room_patterns:
            if pattern.search(text):
                return True
        return False

    def _estimate_rotation(self, bbox: List[Tuple[float, float]]) -> float:
        """
        Estimate text rotation from bounding box.

        Args:
            bbox: Bounding box as 4 corner points

        Returns:
            Rotation angle in degrees
        """
        if len(bbox) < 2:
            return 0.0

        # Calculate angle from first edge
        dx = bbox[1][0] - bbox[0][0]
        dy = bbox[1][1] - bbox[0][1]

        import math
        angle = math.degrees(math.atan2(dy, dx))

        # Normalize to nearest 90 degrees for typical drawing text
        normalized = round(angle / 90) * 90
        return normalized % 360

    def preprocess_image(
        self,
        image: np.ndarray,
        threshold: bool = True,
        denoise: bool = True,
        deskew: bool = False
    ) -> np.ndarray:
        """
        Preprocess image for better OCR results.

        Args:
            image: Input image as numpy array
            threshold: Apply adaptive thresholding
            denoise: Apply denoising
            deskew: Attempt to deskew image

        Returns:
            Preprocessed image
        """
        if not CV2_AVAILABLE:
            logger.warning("OpenCV not available for preprocessing")
            return image

        result = image.copy()

        # Convert to grayscale if needed
        if len(result.shape) == 3:
            result = cv2.cvtColor(result, cv2.COLOR_RGB2GRAY)

        # Denoise
        if denoise:
            result = cv2.fastNlMeansDenoising(result, None, 10, 7, 21)

        # Threshold
        if threshold:
            result = cv2.adaptiveThreshold(
                result, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11, 2
            )

        # Deskew
        if deskew:
            result = self._deskew_image(result)

        return result

    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Deskew an image based on detected lines."""
        if not CV2_AVAILABLE:
            return image

        # Detect lines using Hough transform
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(
            edges, 1, np.pi/180, 100,
            minLineLength=100, maxLineGap=10
        )

        if lines is None:
            return image

        # Calculate average angle
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            # Only consider nearly horizontal lines
            if abs(angle) < 10 or abs(angle - 180) < 10:
                angles.append(angle)

        if not angles:
            return image

        median_angle = np.median(angles)

        # Rotate image
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )

        return rotated

    def extract_from_region(
        self,
        image: np.ndarray,
        x: int,
        y: int,
        width: int,
        height: int,
        **kwargs
    ) -> List[OCRResult]:
        """
        Extract text from a specific region of the image.

        Args:
            image: Full image
            x: Left coordinate of region
            y: Top coordinate of region
            width: Width of region
            height: Height of region
            **kwargs: Additional arguments passed to extract_text

        Returns:
            List of OCRResult objects with coordinates adjusted to full image
        """
        # Extract region
        region = image[y:y+height, x:x+width]

        # Run OCR on region
        results = self.extract_text(region, **kwargs)

        # Adjust coordinates back to full image
        for result in results:
            result.bbox = [
                (point[0] + x, point[1] + y)
                for point in result.bbox
            ]

        return results

    def batch_extract(
        self,
        images: List[np.ndarray],
        **kwargs
    ) -> List[List[OCRResult]]:
        """
        Extract text from multiple images.

        Args:
            images: List of images
            **kwargs: Arguments passed to extract_text

        Returns:
            List of OCRResult lists, one per image
        """
        all_results = []
        for i, image in enumerate(images):
            logger.debug(f"Processing image {i+1}/{len(images)}")
            results = self.extract_text(image, **kwargs)
            all_results.append(results)
        return all_results

    def find_scale_notation(self, image: np.ndarray) -> Optional[str]:
        """
        Find and extract scale notation from an image.

        Args:
            image: Input image

        Returns:
            Scale string (e.g., "1:100") or None
        """
        results = self.extract_text(image, min_confidence=0.5)

        for result in results:
            if result.text_type == TextType.SCALE:
                return result.parsed_value.get("scale")

        # Try harder with full text search
        for result in results:
            for pattern in self._scale_patterns:
                match = pattern.search(result.text)
                if match:
                    try:
                        return f"1:{match.group(1)}"
                    except IndexError:
                        pass

        return None

    def get_text_near_point(
        self,
        results: List[OCRResult],
        point: Tuple[float, float],
        max_distance: float = 50.0
    ) -> List[OCRResult]:
        """
        Find OCR results near a specific point.

        Useful for finding labels near detected features.

        Args:
            results: List of OCRResult objects to search
            point: (x, y) coordinate
            max_distance: Maximum distance from point

        Returns:
            List of nearby OCRResult objects
        """
        nearby = []
        for result in results:
            center = result.center
            distance = ((center[0] - point[0])**2 + (center[1] - point[1])**2)**0.5
            if distance <= max_distance:
                nearby.append(result)
        return nearby
