"""
Document extraction service using VLM (Qwen-VL via Ollama).

This service extracts building parameters from architectural drawings
for use in compliance checking (REVIEW mode).
"""
import os
import base64
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class Confidence(str, Enum):
    """Confidence levels for extracted values."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NOT_FOUND = "NOT_FOUND"


@dataclass
class ExtractedValue:
    """A single extracted value from a document."""
    field_name: str
    value_raw: Optional[str]
    value_numeric: Optional[float]
    unit: Optional[str]
    confidence: Confidence
    location_description: Optional[str]
    notes: Optional[str]


class DocumentExtractionService:
    """
    Service for extracting building parameters from documents using VLM.

    Uses Qwen-VL via Ollama for image understanding and data extraction.
    """

    def __init__(self, ollama_host: str = "http://localhost:11434", model: str = "qwen2-vl:7b"):
        self.ollama_host = ollama_host
        self.model = model

    def _encode_image(self, file_path: str) -> str:
        """Encode an image file to base64."""
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _build_extraction_prompt(self, document_type: Optional[str]) -> str:
        """Build the extraction prompt based on document type."""
        base_prompt = """You are analyzing an architectural drawing. Extract all measurable building parameters you can find.

For each value you extract, provide:
1. The field name (use snake_case, e.g., stair_width, room_area)
2. The raw value as written on the drawing
3. The numeric value (if applicable)
4. The unit of measurement
5. Your confidence level: HIGH (clearly visible), MEDIUM (partially visible or inferred), LOW (uncertain)
6. Where on the drawing you found it

Format your response as JSON with this structure:
{
    "extracted_values": [
        {
            "field_name": "stair_width",
            "value_raw": "900mm",
            "value_numeric": 900,
            "unit": "mm",
            "confidence": "HIGH",
            "location": "Ground floor, main stairwell",
            "notes": null
        }
    ],
    "document_summary": "Brief description of what this drawing shows"
}

"""
        type_specific = {
            "floor_plan": """
Focus on extracting:
- Room dimensions (length x width)
- Door widths
- Corridor widths
- Stair widths and configurations
- Window dimensions
- Room labels and occupancy types
- Exit locations
- Total floor area
""",
            "site_plan": """
Focus on extracting:
- Property dimensions
- Building setbacks (front, side, rear)
- Building footprint dimensions
- Lot coverage
- Parking spaces count
- Driveway width
- Distance to property lines
""",
            "elevation": """
Focus on extracting:
- Building height (to peak and to midpoint of roof)
- Number of storeys
- Floor-to-floor heights
- Window and door sizes
- Grade levels
- Roof pitch
""",
            "section": """
Focus on extracting:
- Ceiling heights
- Floor thicknesses
- Foundation details
- Stair dimensions (rise, run, headroom)
- Room heights
"""
        }

        specific = type_specific.get(document_type, """
Extract any building-related dimensions, counts, or specifications you can identify.
""")

        return base_prompt + specific

    async def extract_from_image(
        self,
        file_path: str,
        document_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract building parameters from an image file.

        Args:
            file_path: Path to the image file
            document_type: Type of document (floor_plan, site_plan, elevation, section)

        Returns:
            Dictionary with extracted values and metadata
        """
        try:
            import ollama
        except ImportError:
            return {
                "success": False,
                "error": "ollama package not installed",
                "extracted_values": []
            }

        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "extracted_values": []
            }

        prompt = self._build_extraction_prompt(document_type)

        try:
            # Call Ollama with the image
            response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [file_path]
                }]
            )

            # Parse the response
            content = response['message']['content']

            # Try to extract JSON from the response
            import json
            import re

            # Look for JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    return {
                        "success": True,
                        "extracted_values": data.get("extracted_values", []),
                        "document_summary": data.get("document_summary"),
                        "raw_response": content
                    }
                except json.JSONDecodeError:
                    pass

            # If JSON parsing failed, return raw response
            return {
                "success": True,
                "extracted_values": [],
                "raw_response": content,
                "parse_error": "Could not parse JSON from response"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "extracted_values": []
            }

    async def extract_from_pdf(
        self,
        file_path: str,
        document_type: Optional[str] = None,
        pages: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Extract building parameters from a PDF file.

        Converts PDF pages to images and processes each page.

        Args:
            file_path: Path to the PDF file
            document_type: Type of document
            pages: Specific pages to process (1-indexed), or None for all

        Returns:
            Dictionary with extracted values from all pages
        """
        try:
            import pdfplumber
            from PIL import Image
            import tempfile
        except ImportError as e:
            return {
                "success": False,
                "error": f"Required package not installed: {e}",
                "extracted_values": []
            }

        all_extracted = []
        page_summaries = []

        try:
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                pages_to_process = pages if pages else list(range(1, total_pages + 1))

                for page_num in pages_to_process:
                    if page_num < 1 or page_num > total_pages:
                        continue

                    page = pdf.pages[page_num - 1]

                    # Convert page to image
                    img = page.to_image(resolution=150)

                    # Save to temp file
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                        img.save(tmp.name)
                        tmp_path = tmp.name

                    try:
                        # Extract from the page image
                        result = await self.extract_from_image(tmp_path, document_type)

                        if result.get("success"):
                            # Add page number to each extracted value
                            for value in result.get("extracted_values", []):
                                value["page_number"] = page_num
                                all_extracted.append(value)

                            if result.get("document_summary"):
                                page_summaries.append(f"Page {page_num}: {result['document_summary']}")
                    finally:
                        # Clean up temp file
                        os.unlink(tmp_path)

            return {
                "success": True,
                "total_pages": total_pages,
                "pages_processed": len(pages_to_process),
                "extracted_values": all_extracted,
                "page_summaries": page_summaries
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "extracted_values": []
            }


# Extraction field mappings for compliance checks
EXTRACTION_FIELDS = {
    "egress": [
        "stair_width",
        "corridor_width",
        "exit_door_width",
        "exit_count",
        "travel_distance",
        "dead_end_distance",
        "stair_rise",
        "stair_run",
        "handrail_height",
        "guard_height"
    ],
    "fire": [
        "fire_separation_rating",
        "sprinkler_coverage",
        "smoke_alarm_locations",
        "fire_alarm_type",
        "exit_sign_locations"
    ],
    "zoning": [
        "front_setback",
        "side_setback",
        "rear_setback",
        "building_height",
        "building_footprint_area",
        "lot_coverage",
        "parking_stall_count",
        "floor_area_ratio"
    ],
    "general": [
        "room_area",
        "ceiling_height",
        "window_area",
        "door_width",
        "dwelling_units",
        "storeys"
    ]
}
